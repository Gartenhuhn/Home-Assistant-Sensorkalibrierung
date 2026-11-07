"""Ablaufsteuerung der Kalibrierung.

Ein Lauf wird vollständig im Home-Assistant-Speicher gehalten und übersteht
damit Neustarts. Offsets werden nie zurückgesetzt: Gemessen wird mit den
bestehenden Offsets, die Korrektur kommt obendrauf.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from datetime import datetime, timedelta
from itertools import pairwise
import logging
from typing import Any
from uuid import uuid4

from homeassistant.components import persistent_notification
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import (
    Event,
    EventStateChangedData,
    EventStateReportedData,
    HomeAssistant,
    callback,
)
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.event import (
    async_track_state_change_event,
    async_track_state_report_event,
    async_track_time_interval,
)
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from . import analysis
from .const import (
    ACTIVE_PHASES,
    APPLY_MAX_ATTEMPTS,
    BATTERY_WARN_PERCENT,
    CONF_MAX_HUMIDITY,
    CONF_MAX_PRESSURE,
    CONF_MAX_TEMPERATURE,
    CONF_MEASURE_HOURS,
    CONF_NOTIFY_TARGETS,
    CONF_SETTLE_MAX_HOURS,
    CONF_VERIFY_HOURS,
    DEFAULT_MEASURE_HOURS,
    DEFAULT_SETTLE_MAX_HOURS,
    DEFAULT_VERIFY_HOURS,
    DOMAIN,
    GRID_SECONDS,
    MAX_GAP_SECONDS,
    MAX_HOLD_SECONDS,
    MAX_SAMPLES_PER_ENTITY,
    MIN_COVERAGE,
    MIN_WINDOW_POINTS,
    MODE_QUICK,
    MODE_STANDARD,
    MODES,
    NEW_DEVICE_DAYS,
    PHASE_APPLYING,
    PHASE_CANCELLED,
    PHASE_DONE,
    PHASE_FAILED,
    PHASE_IDLE,
    PHASE_MEASURING,
    PHASE_PREPARING,
    PHASE_SETTLING,
    PHASE_STEP,
    PHASE_VERIFYING,
    PREPARE_TIMEOUT_SECONDS,
    QUANTITIES,
    QUICK_MEASURE_HOURS,
    QUICK_SETTLE_MAX_HOURS,
    QUICK_SETTLE_MIN_HOURS,
    QUICK_VERIFY_HOURS,
    SETTLE_MIN_SECONDS,
    SETTLE_WINDOW_SECONDS,
    SILENT_SECONDS,
    STATUS_COMPARE,
    STATUS_NO_DATA,
    STATUS_OK,
    STATUS_OUTLIER,
    STATUS_REFERENCE,
    STATUS_UNSTABLE,
    TICK_SECONDS,
    VERIFY_WAIT_SECONDS,
    Quantity,
)
from .discovery import Candidate, battery_level, find_candidates, z2m_ieee
from .z2m import Z2MBridge, Z2MError

_LOGGER = logging.getLogger(__name__)

STORAGE_VERSION = 1
OFFSET_EPSILON = 0.005
OFFSET_MISSING = "missing"
OFFSET_DIFFERS = "differs"
TITLE = "Sensor-Kalibrierung"


class CalibrationManager:
    """Steuert genau einen Kalibrierlauf."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        bridge: Z2MBridge,
        listeners: set[Callable[[], None]],
    ) -> None:
        """Initialisiert den Manager."""
        self.hass = hass
        self.entry = entry
        self.bridge = bridge
        self._listeners = listeners
        self._store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, DOMAIN)
        self._lock = asyncio.Lock()
        self._selection: list[str] | None = None
        self._references: list[str] = []
        self._mode = MODE_STANDARD
        self._run: dict[str, Any] | None = None
        self._last: dict[str, Any] | None = None
        self._backup: dict[str, Any] | None = None
        self._calibrations: dict[str, dict[str, Any]] = {}
        self._live: dict[str, dict[str, float]] = {}
        self._unsubscribe: list[Callable[[], None]] = []
        bridge.on_update = self._notify

    # Lebenszyklus

    async def async_setup(self) -> None:
        """Lädt den Speicher und setzt einen laufenden Durchgang fort."""
        data = await self._store.async_load() or {}
        self._selection = data.get("selection")
        references = data.get("references")
        if references is None and data.get("reference"):
            references = [data["reference"]]
        self._references = list(references or [])
        self._mode = data.get("mode") if data.get("mode") in MODES else MODE_STANDARD
        self._run = data.get("run")
        self._last = data.get("last")
        self._backup = data.get("backup")
        self._calibrations = self._migrate_calibrations(
            data.get("calibrations") or {}, self._last
        )
        if self._backup and "calibrations" in self._backup:
            self._backup["calibrations"] = self._migrate_calibrations(
                self._backup["calibrations"] or {}, None
            )
        if self._run:
            _migrate_run(self._run)
            self._attach(self._run)
            self._refresh_live(self._run)

    async def async_unload(self) -> None:
        """Beendet Listener und schreibt den Stand sofort."""
        self._detach()
        await self._store.async_save(self._data())

    def _data(self) -> dict[str, Any]:
        """Erzeugt die zu speichernden Daten."""
        return {
            "selection": self._selection,
            "references": self._references,
            "mode": self._mode,
            "run": self._run,
            "last": self._last,
            "backup": self._backup,
            "calibrations": self._calibrations,
        }

    def _migrate_calibrations(
        self, raw: dict[str, Any], last: dict[str, Any] | None
    ) -> dict[str, dict[str, Any]]:
        """Stellt Version 1.0 (Zeitstempel je Geräte-ID) auf Offsets je IEEE um."""
        offsets: dict[str, dict[str, float]] = {}
        if last and last.get("result") and not last.get("rolled_back"):
            for key, data in last["result"].items():
                for member_id, item in data["sensors"].items():
                    if item.get("applied"):
                        option = QUANTITIES[key].calibration_option
                        offsets.setdefault(member_id, {})[option] = item["new_offset"]
        devices = dr.async_get(self.hass)
        result: dict[str, dict[str, Any]] = {}
        for member_id, value in raw.items():
            if isinstance(value, dict):
                result[member_id] = value
                continue
            device = devices.async_get(member_id)
            key = z2m_ieee(device) or member_id
            result[key] = {
                "at": float(value),
                "name": (device.name_by_user or device.name) if device else member_id,
                "offsets": offsets.get(member_id, {}),
            }
        return result

    def _attach(self, run: dict[str, Any]) -> None:
        """Startet Messwert-Listener und Takt."""
        self._detach()
        entity_ids = [
            entity_id
            for member in run["members"].values()
            for entity_id in member["entities"].values()
        ]
        self._unsubscribe = [
            async_track_state_change_event(self.hass, entity_ids, self._on_state),
            async_track_state_report_event(self.hass, entity_ids, self._on_report),
            async_track_time_interval(
                self.hass, self._async_tick, timedelta(seconds=TICK_SECONDS)
            ),
        ]

    def _detach(self) -> None:
        """Beendet Messwert-Listener und Takt."""
        for unsubscribe in self._unsubscribe:
            unsubscribe()
        self._unsubscribe = []

    @callback
    def _notify(self) -> None:
        """Informiert Kachel und Statussensor."""
        for listener in list(self._listeners):
            listener()

    # Öffentliche Aktionen

    def candidates(self) -> list[Candidate]:
        """Liefert die aktuelle Auswahlliste."""
        return find_candidates(self.hass, self.bridge)

    def _selected_ids(self, candidates: list[Candidate]) -> list[str]:
        """Liefert die Auswahl, ohne Eintrag gilt die Vorbelegung."""
        known = {item.member_id for item in candidates}
        if self._selection is not None:
            return [item for item in self._selection if item in known]
        return [item.member_id for item in candidates if item.selected_by_default]

    async def async_set_selection(
        self,
        members: list[str],
        references: list[str] | None = None,
        mode: str | None = None,
    ) -> None:
        """Speichert Auswahl, Referenzgruppe und Art der Kalibrierung."""
        if self._run:
            raise HomeAssistantError("Während eines Laufs ist die Auswahl gesperrt")
        self._selection = members
        if references is not None:
            self._references = [item for item in references if item in members]
        else:
            self._references = [item for item in self._references if item in members]
        if mode is not None:
            if mode not in MODES:
                raise HomeAssistantError(f"Unbekannte Art: {mode}")
            self._mode = mode
        await self._store.async_save(self._data())
        self._notify()

    async def async_start(self) -> None:
        """Startet einen neuen Lauf."""
        async with self._lock:
            if self._run:
                raise HomeAssistantError("Es läuft bereits eine Kalibrierung")
            candidates = self.candidates()
            selected = set(self._selected_ids(candidates))
            members = [item for item in candidates if item.member_id in selected]
            references = [item for item in self._references if item in selected]
            if len(members) < 2:
                raise HomeAssistantError("Wähle mindestens zwei Sensoren aus")
            if not any(
                item.correctable and item.member_id not in references
                for item in members
            ):
                raise HomeAssistantError(
                    "Keiner der gewählten Sensoren lässt sich korrigieren"
                    if not references
                    else "Neben der Referenz fehlt ein Sensor, der korrigiert wird"
                )
            if not self.bridge.ready:
                raise HomeAssistantError("Zigbee2MQTT ist noch nicht erreichbar")
            run = self._new_run(members, references)
            backup, changed = await self._prepare_devices(run)
            run["prepared_at"] = self._now()
            self._seed_samples(run, changed)
            self._backup = backup
            self._last = None
            self._run = run
            self._live = {}
            self._attach(run)
            await self._store.async_save(self._data())
        self._notify()

    async def async_cancel(self) -> None:
        """Bricht einen Lauf ab, Offsets bleiben unverändert."""
        async with self._lock:
            if not self._run:
                raise HomeAssistantError("Es läuft keine Kalibrierung")
            await self._finish(
                self._run, PHASE_CANCELLED, "Die Kalibrierung wurde abgebrochen."
            )

    async def async_dismiss(self) -> None:
        """Schließt die Ergebnisansicht, das Ergebnis bleibt abrufbar."""
        if self._last:
            self._last["dismissed"] = True
            await self._store.async_save(self._data())
            self._notify()

    async def async_rollback(self) -> None:
        """Stellt die Optionen von vor dem letzten Lauf wieder her."""
        async with self._lock:
            if self._run:
                raise HomeAssistantError("Zuerst den laufenden Durchgang abbrechen")
            if not self._backup:
                raise HomeAssistantError("Es gibt nichts wiederherzustellen")
            failed = []
            for ieee, item in self._backup["devices"].items():
                try:
                    await self.bridge.async_set_options(ieee, dict(item["options"]))
                except Z2MError as err:
                    _LOGGER.warning("Rückgängig für %s fehlgeschlagen: %s", ieee, err)
                    failed.append(item["name"])
            if failed:
                raise HomeAssistantError(
                    "Nicht wiederhergestellt: " + ", ".join(failed)
                )
            self._calibrations = self._backup.get("calibrations") or {}
            self._backup = None
            if self._last:
                self._last["rolled_back"] = True
            await self._store.async_save(self._data())
        self._notify()

    async def async_restore_offsets(self, members: list[str] | None = None) -> None:
        """Schreibt gespeicherte Offsets erneut, etwa nach einem Zurücksetzen."""
        async with self._lock:
            if self._run:
                raise HomeAssistantError("Während eines Laufs nicht möglich")
            candidates = [
                item
                for item in self.candidates()
                if members is None or item.member_id in members
            ]
            todo = [
                item
                for item in candidates
                if item.ieee
                and (members is not None or self._offset_state(item))
                and self._calibrations.get(item.key, {}).get("offsets")
            ]
            if not todo:
                raise HomeAssistantError("Für diese Sensoren ist nichts gespeichert")
            failed = []
            for item in todo:
                options = self._restore_options(item)
                try:
                    await self.bridge.async_set_options(item.ieee, options)
                except Z2MError as err:
                    _LOGGER.warning("Wiederherstellen für %s: %s", item.name, err)
                    failed.append(item.name)
            if failed:
                raise HomeAssistantError(
                    "Nicht wiederhergestellt: " + ", ".join(failed)
                )
        self._notify()

    def _restore_options(self, item: Candidate) -> dict[str, Any]:
        """Offsets und Nachkommastellen für ein Gerät."""
        options = dict(self._calibrations[item.key]["offsets"])
        for quantity in QUANTITIES.values():
            if (
                quantity.calibration_option in options
                and item.ieee
                and self.bridge.supports(item.ieee, quantity.precision_option)
            ):
                options[quantity.precision_option] = quantity.precision
        return options

    async def async_adopt_offset(self, member_id: str, key: str) -> None:
        """Übernimmt den Offset eines Ausreißers aus dem letzten Lauf."""
        async with self._lock:
            last = self._last
            if self._run:
                raise HomeAssistantError("Während eines Laufs nicht möglich")
            if not last or last.get("rolled_back") or not self._backup:
                raise HomeAssistantError("Das letzte Ergebnis ist nicht mehr aktiv")
            data = (last.get("result") or {}).get(key)
            item = (data or {}).get("sensors", {}).get(member_id)
            if not item or item["status"] != STATUS_OUTLIER or item["applied"]:
                raise HomeAssistantError("Dieser Wert kann nicht übernommen werden")
            info = self._member_info(last, member_id)
            ieee = info["ieee"]
            if not ieee or ieee not in self._backup["devices"]:
                raise HomeAssistantError("Für diesen Sensor fehlt die Sicherung")
            option = QUANTITIES[key].calibration_option
            try:
                await self.bridge.async_set_options(
                    ieee, {option: item["new_offset"]}
                )
            except Z2MError as err:
                raise HomeAssistantError(f"Zigbee2MQTT: {err}") from err
            item["applied"] = True
            item["manual"] = True
            self._record_calibration(
                info["key"], info["name"], {option: item["new_offset"]}
            )
            await self._store.async_save(self._data())
        self._notify()

    def _member_info(self, last: dict[str, Any], member_id: str) -> dict[str, Any]:
        """Name und IEEE eines Sensors aus dem letzten Lauf."""
        info = (last.get("members") or {}).get(member_id)
        if info:
            return info
        device = dr.async_get(self.hass).async_get(member_id)
        ieee = z2m_ieee(device)
        return {
            "name": (last.get("names") or {}).get(member_id, member_id),
            "ieee": ieee,
            "key": ieee or member_id,
        }

    def _record_calibration(
        self, key: str, name: str, offsets: dict[str, float]
    ) -> None:
        """Merkt sich Zeitpunkt und Offsets eines Geräts."""
        previous = self._calibrations.get(key, {}).get("offsets", {})
        self._calibrations[key] = {
            "at": self._now(),
            "name": name,
            "offsets": previous | offsets,
        }

    # Ablauf

    def _now(self) -> float:
        """Aktuelle Zeit als Zeitstempel."""
        return dt_util.utcnow().timestamp()

    def _option(self, key: str, default: Any) -> Any:
        """Liest eine Einstellung."""
        return self.entry.options.get(key, default)

    def _timings(self, mode: str) -> dict[str, float]:
        """Zeiten je Art der Kalibrierung in Sekunden."""
        if mode == MODE_QUICK:
            return {
                "settle_min_seconds": QUICK_SETTLE_MIN_HOURS * 3600,
                "settle_window_seconds": SETTLE_WINDOW_SECONDS // 2,
                "settle_max_seconds": QUICK_SETTLE_MAX_HOURS * 3600,
                "measure_seconds": QUICK_MEASURE_HOURS * 3600,
                "verify_seconds": QUICK_VERIFY_HOURS * 3600,
            }
        return {
            "settle_min_seconds": SETTLE_MIN_SECONDS,
            "settle_window_seconds": SETTLE_WINDOW_SECONDS,
            "settle_max_seconds": 3600
            * self._option(CONF_SETTLE_MAX_HOURS, DEFAULT_SETTLE_MAX_HOURS),
            "measure_seconds": 3600
            * self._option(CONF_MEASURE_HOURS, DEFAULT_MEASURE_HOURS),
            "verify_seconds": 3600
            * self._option(CONF_VERIFY_HOURS, DEFAULT_VERIFY_HOURS),
        }

    def _new_run(
        self, members: list[Candidate], references: list[str]
    ) -> dict[str, Any]:
        """Legt die Daten eines Laufs an."""
        now = self._now()
        limits = {
            "temperature": self._option(
                CONF_MAX_TEMPERATURE, QUANTITIES["temperature"].max_offset
            ),
            "humidity": self._option(
                CONF_MAX_HUMIDITY, QUANTITIES["humidity"].max_offset
            ),
            "pressure": self._option(
                CONF_MAX_PRESSURE, QUANTITIES["pressure"].max_offset
            ),
        }
        warnings = []
        data = {}
        for item in members:
            data[item.member_id] = {
                "id": item.member_id,
                "key": item.key,
                "name": item.name,
                "entities": dict(item.entities),
                "correctable": [] if item.member_id in references else list(
                    item.correctable
                ),
                "precision": list(item.correctable),
                "ieee": item.ieee,
                "battery_entity": item.battery_entity,
                "active": True,
            }
            level = battery_level(self.hass, item.battery_entity)
            if level is not None and level <= BATTERY_WARN_PERCENT:
                warnings.append(
                    f"{item.name}: Batterie {level:.0f} %, die Werte können driften."
                )
        return {
            "id": uuid4().hex,
            "mode": self._mode,
            "phase": PHASE_PREPARING,
            "started_at": now,
            "phase_started_at": now,
            "prepared_at": now,
            "members": data,
            "references": [item for item in references if item in data],
            "samples": {},
            "restored": {},
            "warnings": warnings,
            "unstable": [],
            "silent": [],
            "silent_notified": [],
            "limits": limits,
            "apply_attempts": 0,
        } | self._timings(self._mode)

    def _seed_samples(self, run: dict[str, Any], changed: set[str]) -> None:
        """Übernimmt aktuelle Werte, die schon genau genug sind."""
        for member in run["members"].values():
            for entity_id in member["entities"].values():
                state = self.hass.states.get(entity_id)
                if entity_id in changed or state is None:
                    continue
                try:
                    value = float(state.state)
                except ValueError:
                    continue
                run["samples"][entity_id] = [[run["prepared_at"], value]]

    async def _prepare_devices(
        self, run: dict[str, Any]
    ) -> tuple[dict[str, Any], set[str]]:
        """Sichert Optionen und stellt die Nachkommastellen ein."""
        backup: dict[str, Any] = {
            "created_at": self._now(),
            "devices": {},
            "calibrations": dict(self._calibrations),
        }
        changed: set[str] = set()
        for member in run["members"].values():
            ieee = member["ieee"]
            precision = member.get("precision", member["correctable"])
            if not ieee or not precision:
                continue
            current = self.bridge.device_options(ieee)
            quantities = [QUANTITIES[key] for key in precision]
            keys = [item.calibration_option for item in quantities] + [
                item.precision_option for item in quantities
            ]
            wanted = {
                item.precision_option: item.precision
                for item in quantities
                if self.bridge.supports(ieee, item.precision_option)
                and self.bridge.effective_precision(ieee, item) < item.precision
            }
            try:
                if wanted:
                    await self.bridge.async_set_options(ieee, wanted)
                    changed.update(
                        member["entities"][item.key]
                        for item in quantities
                        if item.precision_option in wanted
                    )
            except Z2MError as err:
                _LOGGER.warning("Optionen für %s: %s", member["name"], err)
                member["correctable"] = []
                run["warnings"].append(
                    f"{member['name']}: Zigbee2MQTT reagiert nicht, "
                    "der Sensor wird nur verglichen."
                )
                continue
            backup["devices"][ieee] = {
                "name": member["name"],
                "options": {key: current.get(key) for key in keys},
            }
        if not backup["devices"]:
            raise HomeAssistantError("Zigbee2MQTT hat keine Änderung bestätigt")
        return backup, changed

    def _sample_value(self, run: dict[str, Any], entity_id: str, state: Any) -> float | None:
        """Prüft einen Messwert auf Plausibilität."""
        if state is None or state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            return None
        quantity = self._quantity_of(run, entity_id)
        try:
            value = float(state.state)
        except ValueError:
            return None
        if quantity and quantity.minimum <= value <= quantity.maximum:
            return value
        return None

    def _add_sample(self, run: dict[str, Any], entity_id: str, value: float) -> None:
        """Hängt einen Messwert an, gleiche Werte verlängern nur das Plateau."""
        series = run["samples"].setdefault(entity_id, [])
        now = self._now()
        if (
            len(series) >= 2
            and series[-1][1] == value == series[-2][1]
            and now - series[-2][0] < GRID_SECONDS
        ):
            series[-1][0] = now
        else:
            series.append([now, value])
            del series[:-MAX_SAMPLES_PER_ENTITY]
        self._notify()

    @callback
    def _on_state(self, event: Event[EventStateChangedData]) -> None:
        """Nimmt eine geänderte Sensormeldung auf.

        Ein Wechsel aus unbekannt oder nicht verfügbar ist meist ein
        wiederhergestellter oder von Zigbee2MQTT erneut gesendeter Wert nach
        einem Neustart. Er zählt erst, wenn sich der Wert wirklich ändert.
        """
        run = self._run
        if run is None:
            return
        entity_id = event.data["entity_id"]
        value = self._sample_value(run, entity_id, event.data["new_state"])
        if value is None:
            return
        old_state = event.data["old_state"]
        restored = run.setdefault("restored", {})
        if old_state is None or old_state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            restored[entity_id] = value
            return
        if restored.get(entity_id) == value:
            return
        restored.pop(entity_id, None)
        self._add_sample(run, entity_id, value)

    @callback
    def _on_report(self, event: Event[EventStateReportedData]) -> None:
        """Nimmt eine Meldung mit unverändertem Wert auf."""
        run = self._run
        if run is None:
            return
        entity_id = event.data["entity_id"]
        value = self._sample_value(run, entity_id, event.data["new_state"])
        if value is None or entity_id in run.get("restored", {}):
            return
        self._add_sample(run, entity_id, value)

    @staticmethod
    def _quantity_of(run: dict[str, Any], entity_id: str) -> Quantity | None:
        """Findet die Messgröße zu einer Entität."""
        for member in run["members"].values():
            for key, item in member["entities"].items():
                if item == entity_id:
                    return QUANTITIES[key]
        return None

    async def _async_tick(self, _now: datetime | None = None) -> None:
        """Prüft regelmäßig, ob die nächste Phase beginnen kann."""
        if self._lock.locked():
            return
        async with self._lock:
            await self._advance()

    async def _advance(self) -> None:
        """Führt alle jetzt möglichen Phasenwechsel aus."""
        handlers = {
            PHASE_PREPARING: self._step_preparing,
            PHASE_SETTLING: self._step_settling,
            PHASE_MEASURING: self._step_measuring,
            PHASE_APPLYING: self._step_applying,
            PHASE_VERIFYING: self._step_verifying,
        }
        while (run := self._run) is not None:
            phase = run["phase"]
            await handlers[phase](run)
            if self._run is None or self._run["phase"] == phase:
                break
        if self._run is not None:
            self._refresh_live(self._run)
            self._store.async_delay_save(self._data, 1)
        self._notify()

    async def _set_phase(self, run: dict[str, Any], phase: str) -> None:
        """Wechselt die Phase und speichert sofort."""
        _LOGGER.debug("Phase %s -> %s", run["phase"], phase)
        run["phase"] = phase
        run["phase_started_at"] = self._now()
        await self._store.async_save(self._data())

    def _series(
        self, run: dict[str, Any], key: str, since: float | None = None
    ) -> dict[str, list[list[float]]]:
        """Liefert die Messreihen einer Größe je Sensor."""
        result = {}
        for member in run["members"].values():
            entity_id = member["entities"].get(key)
            if not member["active"] or not entity_id:
                continue
            series = run["samples"].get(entity_id, [])
            if since is not None:
                series = [point for point in series if point[0] >= since]
            if series:
                result[member["id"]] = series
        return result

    def _reference_ids(self, run: dict[str, Any], key: str) -> list[str]:
        """Aktive Referenzsensoren, die diese Größe messen."""
        return [
            member_id
            for member_id in run.get("references", [])
            if (member := run["members"].get(member_id))
            and member["active"]
            and key in member["entities"]
        ]

    def _group_ids(self, run: dict[str, Any], key: str) -> list[str]:
        """Sensoren, die korrigiert werden."""
        return [
            member["id"]
            for member in run["members"].values()
            if member["active"] and key in member["correctable"]
        ]

    def _active(self, run: dict[str, Any]) -> list[dict[str, Any]]:
        """Liefert die aktiven Sensoren."""
        return [item for item in run["members"].values() if item["active"]]

    def _last_seen(self, run: dict[str, Any], member: dict[str, Any]) -> float | None:
        """Zeitpunkt der letzten Meldung eines Geräts."""
        times = [
            series[-1][0]
            for entity_id in member["entities"].values()
            if (series := run["samples"].get(entity_id))
        ]
        return max(times) if times else None

    def _silent_members(self, run: dict[str, Any]) -> list[str]:
        """Aktive Sensoren, die sich zu lange nicht gemeldet haben."""
        now = self._now()
        return [
            member["id"]
            for member in self._active(run)
            if (seen := self._last_seen(run, member)) is not None
            and now - seen > SILENT_SECONDS
        ]

    async def _fail(self, run: dict[str, Any], message: str) -> None:
        """Beendet einen Lauf mit Fehler, ohne Offsets zu verändern."""
        await self._finish(run, PHASE_FAILED, message)

    async def _step_preparing(self, run: dict[str, Any]) -> None:
        """Wartet auf die erste Meldung jedes Sensors."""
        since = run["prepared_at"]
        missing = {}
        for member in self._active(run):
            gaps = [
                key
                for key, entity_id in member["entities"].items()
                if not run["samples"].get(entity_id)
            ]
            if gaps:
                missing[member["id"]] = gaps
        if missing and self._now() - since < PREPARE_TIMEOUT_SECONDS:
            return
        for member_id, gaps in missing.items():
            member = run["members"][member_id]
            for key in gaps:
                member["entities"].pop(key)
                if key in member["correctable"]:
                    member["correctable"].remove(key)
            if not member["entities"]:
                member["active"] = False
                run["warnings"].append(
                    f"{member['name']}: keine Meldung erhalten, Sensor ausgelassen."
                )
        if len(self._active(run)) < 2:
            await self._fail(run, "Es melden sich zu wenige Sensoren.")
            return
        await self._set_phase(run, PHASE_SETTLING)

    async def _step_settling(self, run: dict[str, Any]) -> None:
        """Wartet, bis die Abstände zwischen den Sensoren stabil sind."""
        now = self._now()
        elapsed = now - run["phase_started_at"]
        unstable: set[str] = set()
        for key, quantity in QUANTITIES.items():
            series = self._series(run, key)
            if len(series) < 2:
                continue
            unstable.update(
                analysis.unstable_sensors(
                    series,
                    now,
                    group_ids=self._group_ids(run, key),
                    reference_ids=self._reference_ids(run, key),
                    tolerance=quantity.tolerance,
                    window=run["settle_window_seconds"],
                    step=GRID_SECONDS,
                    max_hold=MAX_HOLD_SECONDS,
                    min_points=MIN_WINDOW_POINTS,
                )
            )
        relevant = {
            member["id"]
            for member in self._active(run)
            if member["correctable"] or member["id"] in run.get("references", [])
        }
        silent = set(self._silent_members(run)) & relevant
        unstable = (unstable | silent) & relevant
        run["unstable"] = sorted(unstable)
        run["silent"] = sorted(silent)
        await self._report_silent(run, silent)
        ready = elapsed >= run["settle_min_seconds"] and not unstable
        if ready or elapsed >= run["settle_max_seconds"]:
            if unstable:
                names = ", ".join(run["members"][item]["name"] for item in unstable)
                run["warnings"].append(
                    f"Noch nicht stabil nach maximaler Wartezeit: {names}."
                )
            run["measure_start"] = now
            run["measure_end"] = now + run["measure_seconds"]
            await self._set_phase(run, PHASE_MEASURING)

    async def _report_silent(self, run: dict[str, Any], silent: set[str]) -> None:
        """Meldet einmal je Lauf, wenn ein Sensor verstummt."""
        notified = run.setdefault("silent_notified", [])
        new = sorted(item for item in silent if item not in notified)
        if not new:
            return
        notified.extend(new)
        names = ", ".join(run["members"][item]["name"] for item in new)
        minutes = SILENT_SECONDS // 60
        await self._send(
            f"{names}: seit über {minutes} Minuten keine Meldung. Prüfe die "
            "Zigbee-Verbindung, zum Beispiel mit einem kurzen Druck auf die Taste. "
            "Die Kalibrierung wartet so lange.",
            f"{DOMAIN}_silent",
        )

    async def _step_measuring(self, run: dict[str, Any]) -> None:
        """Wertet nach Ablauf der Messzeit aus."""
        if self._now() < run["measure_end"]:
            return
        run["result"] = self._evaluate(run)
        await self._set_phase(run, PHASE_APPLYING)

    def _old_offset(self, member: dict[str, Any], key: str) -> float:
        """Liefert den Offset von vor dem Lauf."""
        options = (self._backup or {}).get("devices", {}).get(member["ieee"], {})
        value = options.get("options", {}).get(QUANTITIES[key].calibration_option)
        return float(value or 0)

    def _max_gap(self, series: list[list[float]], start: float, end: float) -> float:
        """Längste Zeit ohne Meldung im Fenster."""
        before = [point[0] for point in series if point[0] < start]
        times = ([before[-1]] if before else [start]) + [
            point[0] for point in series if start <= point[0] <= end
        ]
        times.append(end)
        return max(b - a for a, b in pairwise(times))

    def _evaluate(self, run: dict[str, Any]) -> dict[str, Any]:
        """Berechnet Abweichungen und neue Offsets je Messgröße."""
        result: dict[str, Any] = {}
        start, end = run["measure_start"], run["measure_end"]
        for key, quantity in QUANTITIES.items():
            series = self._series(run, key)
            if not series:
                continue
            silent = {
                member_id
                for member_id, points in series.items()
                if self._max_gap(points, start, end) > MAX_GAP_SECONDS
            }
            usable_series = {
                member_id: points
                for member_id, points in series.items()
                if member_id not in silent
            }
            references = [
                item for item in self._reference_ids(run, key) if item not in silent
            ]
            stats = analysis.analyse_window(
                usable_series,
                start,
                end,
                group_ids=self._group_ids(run, key),
                reference_ids=references,
                step=GRID_SECONDS,
                max_hold=MAX_HOLD_SECONDS,
                min_points=MIN_WINDOW_POINTS,
                min_coverage=MIN_COVERAGE,
            )
            sensors: dict[str, Any] = {}
            for member in self._active(run):
                if key not in member["entities"]:
                    continue
                if member["id"] in silent:
                    run["warnings"].append(
                        f"{member['name']}: {quantity.label} hat beim Messen zu "
                        "selten gemeldet, nicht korrigiert."
                    )
                sensors[member["id"]] = self._rate_sensor(
                    run, member, key, quantity, stats.get(member["id"]), references
                )
            usable = [
                item["deviation"]
                for item in sensors.values()
                if item["status"] in (STATUS_OK, STATUS_REFERENCE)
            ]
            result[key] = {
                "label": quantity.label,
                "unit": quantity.unit,
                "references": references,
                "sensors": sensors,
                "spread_before": _round(analysis.spread(usable)),
                "spread_after": None,
            }
        return result

    def _rate_sensor(
        self,
        run: dict[str, Any],
        member: dict[str, Any],
        key: str,
        quantity: Quantity,
        stats: analysis.WindowStats | None,
        references: list[str],
    ) -> dict[str, Any]:
        """Bewertet einen Sensor für eine Messgröße."""
        item: dict[str, Any] = {
            "deviation": None,
            "after": None,
            "correction": None,
            "old_offset": None,
            "new_offset": None,
            "status": STATUS_NO_DATA,
            "applied": False,
        }
        if member["id"] in references:
            item["deviation"] = round(stats.deviation, 2) if stats else 0.0
            item["status"] = STATUS_REFERENCE
            return item
        state = self.hass.states.get(member["entities"][key])
        if stats is None or state is None or state.state == STATE_UNAVAILABLE:
            return item
        item["deviation"] = round(stats.deviation, 2)
        if key not in member["correctable"]:
            item["status"] = STATUS_COMPARE
            return item
        old = self._old_offset(member, key)
        correction = -stats.deviation
        item["old_offset"] = round(old, 2)
        item["correction"] = round(correction, 2)
        item["new_offset"] = round(old + correction, 2)
        if abs(stats.drift) > 2 * quantity.tolerance:
            item["status"] = STATUS_UNSTABLE
            run["warnings"].append(
                f"{member['name']}: {quantity.label} driftet noch, nicht korrigiert."
            )
        elif abs(correction) > run["limits"][key]:
            item["status"] = STATUS_OUTLIER
            run["warnings"].append(
                f"{member['name']}: {quantity.label} weicht um "
                f"{stats.deviation:+.2f} {quantity.unit} ab, nicht korrigiert."
            )
        else:
            item["status"] = STATUS_OK
        return item

    async def _step_applying(self, run: dict[str, Any]) -> None:
        """Schreibt die Offsets, wiederholt das bei Fehlern."""
        pending: dict[str, dict[str, Any]] = {}
        for key, data in run["result"].items():
            for member_id, item in data["sensors"].items():
                if item["status"] == STATUS_OK and not item["applied"]:
                    option = QUANTITIES[key].calibration_option
                    pending.setdefault(member_id, {})[option] = item["new_offset"]
        for member_id, options in pending.items():
            member = run["members"][member_id]
            try:
                await self.bridge.async_set_options(member["ieee"], options)
            except Z2MError as err:
                _LOGGER.warning("Offset für %s: %s", member["name"], err)
                continue
            for data in run["result"].values():
                item = data["sensors"].get(member_id)
                if item and item["status"] == STATUS_OK:
                    item["applied"] = True
            self._record_calibration(
                member.get("key") or member["ieee"] or member_id,
                member["name"],
                options,
            )
        run["apply_attempts"] += 1
        await self._store.async_save(self._data())
        remaining = [
            member_id
            for data in run["result"].values()
            for member_id, item in data["sensors"].items()
            if item["status"] == STATUS_OK and not item["applied"]
        ]
        if remaining and run["apply_attempts"] < APPLY_MAX_ATTEMPTS:
            return
        for member_id in sorted(set(remaining)):
            run["warnings"].append(
                f"{run['members'][member_id]['name']}: Offset konnte nicht "
                "geschrieben werden."
            )
        applied = [
            item
            for data in run["result"].values()
            for item in data["sensors"].values()
            if item["applied"]
        ]
        if not applied:
            await self._finish(
                run,
                PHASE_DONE,
                "Es wurde kein Offset gesetzt. Die Hinweise nennen den Grund.",
            )
            return
        run["applied_at"] = self._now()
        await self._set_phase(run, PHASE_VERIFYING)

    def _reported_since_apply(self, run: dict[str, Any]) -> bool:
        """Prüft, ob alle korrigierten Sensoren neu gemeldet haben."""
        for key, data in run["result"].items():
            for member_id, item in data["sensors"].items():
                if not item["applied"]:
                    continue
                entity_id = run["members"][member_id]["entities"][key]
                series = run["samples"].get(entity_id, [])
                if not series or series[-1][0] < run["applied_at"]:
                    return False
        return True

    async def _step_verifying(self, run: dict[str, Any]) -> None:
        """Kontrolliert das Ergebnis mit den neuen Offsets."""
        now = self._now()
        if "verify_start" not in run:
            if (
                self._reported_since_apply(run)
                or now - run["applied_at"] >= VERIFY_WAIT_SECONDS
            ):
                run["verify_start"] = now
                run["verify_end"] = now + run["verify_seconds"]
            return
        if now < run["verify_end"]:
            return
        for key, data in run["result"].items():
            references = data.get("references") or []
            ids = [
                member_id
                for member_id, item in data["sensors"].items()
                if item["applied"] or item["status"] == STATUS_REFERENCE
            ]
            stats = analysis.analyse_window(
                self._series(run, key, since=run["applied_at"]),
                run["verify_start"],
                run["verify_end"],
                group_ids=[item for item in ids if item not in references],
                reference_ids=references,
                step=GRID_SECONDS,
                max_hold=MAX_HOLD_SECONDS,
                min_points=MIN_WINDOW_POINTS,
            )
            for member_id, item in data["sensors"].items():
                if member_id in stats:
                    item["after"] = round(stats[member_id].deviation, 2)
            data["spread_after"] = _round(
                analysis.spread(
                    stats[item].deviation for item in ids if item in stats
                )
            )
            before, after = data["spread_before"], data["spread_after"]
            if before is not None and after is not None and after > before:
                run["warnings"].append(
                    f"{data['label']}: Die Streuung ist nicht kleiner geworden. "
                    "Prüfe die Werte oder mache die Änderung rückgängig."
                )
        await self._finish(
            run,
            PHASE_DONE,
            "Die Kalibrierung ist fertig. Du kannst die Sensoren zurückbringen.",
        )

    async def _finish(self, run: dict[str, Any], outcome: str, message: str) -> None:
        """Beendet einen Lauf und behält nur die Zusammenfassung."""
        self._detach()
        self._last = {
            "outcome": outcome,
            "message": message,
            "mode": run.get("mode", MODE_STANDARD),
            "started_at": run["started_at"],
            "finished_at": self._now(),
            "names": {
                member_id: member["name"]
                for member_id, member in run["members"].items()
            },
            "members": {
                member_id: {
                    "name": member["name"],
                    "ieee": member["ieee"],
                    "key": member.get("key") or member["ieee"] or member_id,
                }
                for member_id, member in run["members"].items()
            },
            "references": run.get("references", []),
            "result": run.get("result"),
            "warnings": run["warnings"],
            "dismissed": False,
            "rolled_back": False,
        }
        self._run = None
        self._live = {}
        await self._store.async_save(self._data())
        self._notify()
        if outcome != PHASE_CANCELLED:
            await self._send(self._summary(message, run), DOMAIN)

    def _summary(self, message: str, run: dict[str, Any]) -> str:
        """Text der Abschlussmeldung."""
        lines = [message]
        for data in (run.get("result") or {}).values():
            before, after = data["spread_before"], data["spread_after"]
            if before is not None and after is not None:
                lines.append(
                    f"{data['label']}: Streuung {before:.2f} → {after:.2f} {data['unit']}"
                )
        lines.extend(run["warnings"])
        return "\n".join(lines)

    async def _send(self, text: str, notification_id: str) -> None:
        """Meldet etwas per Benachrichtigung und an die gewählten Geräte."""
        persistent_notification.async_create(
            self.hass, text, TITLE, notification_id=notification_id
        )
        for target in self._option(CONF_NOTIFY_TARGETS, []):
            service = target.removeprefix("notify.")
            try:
                await self.hass.services.async_call(
                    "notify", service, {"title": TITLE, "message": text}
                )
            except HomeAssistantError as err:
                _LOGGER.warning("Benachrichtigung %s: %s", target, err)

    # Anzeige

    def _refresh_live(self, run: dict[str, Any]) -> None:
        """Berechnet die aktuellen Abstände für die Kachel."""
        now = self._now()
        live: dict[str, dict[str, float]] = {}
        for key in QUANTITIES:
            series = self._series(run, key)
            if len(series) < 2:
                continue
            start = max(now - SETTLE_WINDOW_SECONDS, run["prepared_at"])
            if run.get("applied_at"):
                start = max(start, run["applied_at"])
                series = self._series(run, key, since=run["applied_at"])
            stats = analysis.analyse_window(
                series,
                start,
                now,
                group_ids=self._group_ids(run, key),
                reference_ids=self._reference_ids(run, key),
                step=GRID_SECONDS,
                max_hold=MAX_HOLD_SECONDS,
                min_points=1,
            )
            live[key] = {item: round(data.deviation, 2) for item, data in stats.items()}
        self._live = live

    def _eta(self, run: dict[str, Any]) -> float | None:
        """Schätzt, wann die aktuelle Phase endet."""
        phase = run["phase"]
        if phase == PHASE_PREPARING:
            return run["prepared_at"] + PREPARE_TIMEOUT_SECONDS
        if phase == PHASE_SETTLING:
            return run["phase_started_at"] + run["settle_min_seconds"]
        if phase == PHASE_MEASURING:
            return run["measure_end"]
        if phase == PHASE_VERIFYING:
            return run.get("verify_end")
        return None

    def _message(self, run: dict[str, Any]) -> str:
        """Beschreibt den aktuellen Stand in einem Satz."""
        phase = run["phase"]
        active = self._active(run)
        if phase == PHASE_PREPARING:
            ready = sum(
                1
                for member in active
                if all(run["samples"].get(e) for e in member["entities"].values())
            )
            return f"{ready} von {len(active)} Sensoren haben sich gemeldet."
        if phase == PHASE_SETTLING:
            stable = len(active) - len(run["unstable"])
            text = f"{stable} von {len(active)} Sensoren sind stabil."
            if run.get("silent"):
                text += " Mindestens ein Sensor meldet sich nicht."
            return text
        if phase == PHASE_MEASURING:
            return "Alle Sensoren werden verglichen. Du musst nichts tun."
        if phase == PHASE_APPLYING:
            return "Die neuen Offsets werden gesetzt."
        if "verify_start" not in run:
            return "Warte auf die ersten korrigierten Werte."
        return "Die neuen Offsets werden kontrolliert."

    def _sensor_rows(self, run: dict[str, Any]) -> list[dict[str, Any]]:
        """Bereitet die Sensoren eines Laufs für die Kachel auf."""
        rows = []
        now = self._now()
        silent = set(self._silent_members(run))
        for member in run["members"].values():
            values: dict[str, Any] = {}
            for key, entity_id in member["entities"].items():
                state = self.hass.states.get(entity_id)
                values[key] = {
                    "value": state.state if state else None,
                    "deviation": self._live.get(key, {}).get(member["id"]),
                    "samples": len(run["samples"].get(entity_id, [])),
                }
            seen = self._last_seen(run, member)
            rows.append(
                {
                    "id": member["id"],
                    "name": member["name"],
                    "active": member["active"],
                    "reference": member["id"] in run.get("references", []),
                    "correctable": member["correctable"],
                    "unstable": member["id"] in run["unstable"],
                    "silent_minutes": round((now - seen) / 60)
                    if seen is not None and member["id"] in silent
                    else None,
                    "battery": battery_level(self.hass, member["battery_entity"]),
                    "quantities": values,
                }
            )
        return rows

    def _offset_state(self, item: Candidate) -> str | None:
        """Vergleicht gespeicherte Offsets mit Zigbee2MQTT."""
        stored = self._calibrations.get(item.key, {}).get("offsets")
        if not stored or not item.ieee or item.ieee not in self.bridge.devices:
            return None
        current = self.bridge.device_options(item.ieee)
        state = None
        for option, value in stored.items():
            actual = current.get(option)
            if actual is None:
                if abs(value) > OFFSET_EPSILON:
                    return OFFSET_MISSING
            elif abs(float(actual) - value) > OFFSET_EPSILON:
                state = OFFSET_DIFFERS
        return state

    def _is_new(self, item: Candidate) -> bool:
        """Neu in Home Assistant und noch nie kalibriert."""
        if item.key in self._calibrations or not item.correctable:
            return False
        device = dr.async_get(self.hass).async_get(item.member_id)
        entry = None if device else er.async_get(self.hass).async_get(item.member_id)
        created = (device or entry).created_at if (device or entry) else None
        if created is None:
            return False
        return dt_util.utcnow() - created < timedelta(days=NEW_DEVICE_DAYS)

    def _candidate_rows(self, candidates: list[Candidate]) -> list[dict[str, Any]]:
        """Bereitet die Auswahlliste für die Kachel auf."""
        rows = []
        for item in candidates:
            calibration = self._calibrations.get(item.key) or {}
            rows.append(
                item.as_dict(self.hass)
                | {
                    "last_calibrated": calibration.get("at"),
                    "offsets": calibration.get("offsets") or {},
                    "offset_state": self._offset_state(item),
                    "new": self._is_new(item),
                }
            )
        return rows

    def _durations(self) -> dict[str, dict[str, float]]:
        """Mindest- und Höchstdauer je Art in Stunden."""
        result = {}
        for mode in MODES:
            timings = self._timings(mode)
            fixed = timings["measure_seconds"] + timings["verify_seconds"]
            result[mode] = {
                "min_hours": (timings["settle_min_seconds"] + fixed) / 3600,
                "max_hours": (timings["settle_max_seconds"] + fixed) / 3600,
                "measure_hours": timings["measure_seconds"] / 3600,
            }
        return result

    @property
    def phase(self) -> str:
        """Aktuelle Phase für den Statussensor."""
        if self._run:
            return self._run["phase"]
        if self._last and not self._last["dismissed"]:
            return self._last["outcome"]
        return PHASE_IDLE

    def can_adopt(self) -> bool:
        """True, wenn Ausreißer des letzten Laufs übernommen werden können."""
        return bool(
            self._run is None
            and self._backup
            and self._last
            and self._last.get("result")
            and not self._last.get("rolled_back")
        )

    def snapshot(self) -> dict[str, Any]:
        """Erzeugt den Stand für die Kachel."""
        run = self._run
        state: dict[str, Any] = {
            "phase": self.phase,
            "bridge_ready": self.bridge.ready,
            "can_rollback": bool(self._backup) and run is None,
            "can_adopt": self.can_adopt(),
            "backup_at": (self._backup or {}).get("created_at"),
            "last": self._last,
        }
        if run:
            spread = {}
            for key, values in self._live.items():
                ids = self._group_ids(run, key)
                spread[key] = _round(
                    analysis.spread(
                        value for item, value in values.items() if item in ids
                    )
                )
            state |= {
                "step": PHASE_STEP[run["phase"]],
                "mode": run.get("mode", MODE_STANDARD),
                "message": self._message(run),
                "warnings": run["warnings"],
                "started_at": run["started_at"],
                "phase_started_at": run["phase_started_at"],
                "eta": self._eta(run),
                "sensors": self._sensor_rows(run),
                "spread": spread,
                "units": {key: item.unit for key, item in QUANTITIES.items()},
            }
            return state
        candidates = self.candidates()
        state |= {
            "candidates": self._candidate_rows(candidates),
            "selection": self._selected_ids(candidates),
            "references": self._references,
            "mode": self._mode,
            "durations": self._durations(),
        }
        return state

    def status_attributes(self) -> dict[str, Any]:
        """Zusammenfassung für die Attribute des Statussensors."""
        attributes: dict[str, Any] = {}
        last = self._last
        if last:
            attributes["last_outcome"] = last["outcome"]
            attributes["last_finished"] = dt_util.utc_from_timestamp(
                last["finished_at"]
            ).isoformat()
            attributes["last_mode"] = last.get("mode", MODE_STANDARD)
            attributes["last_rolled_back"] = last.get("rolled_back", False)
            for key, data in (last.get("result") or {}).items():
                attributes[f"{key}_spread_before"] = data["spread_before"]
                attributes[f"{key}_spread_after"] = data["spread_after"]
            attributes["last_corrected"] = sorted(
                {
                    last["names"].get(member_id, member_id)
                    for data in (last.get("result") or {}).values()
                    for member_id, item in data["sensors"].items()
                    if item["applied"]
                }
            )
            attributes["last_warnings"] = len(last.get("warnings") or [])
        if self._run is None:
            candidates = self.candidates()
            attributes["offsets_missing"] = sorted(
                item.name for item in candidates if self._offset_state(item)
            )
            attributes["new_sensors"] = sorted(
                item.name for item in candidates if self._is_new(item)
            )
        else:
            attributes["mode"] = self._run.get("mode", MODE_STANDARD)
            attributes["silent"] = [
                self._run["members"][item]["name"]
                for item in self._run.get("silent", [])
            ]
        return attributes

    @property
    def is_active(self) -> bool:
        """True, solange ein Lauf aktiv ist."""
        return self._run is not None and self._run["phase"] in ACTIVE_PHASES


def _migrate_run(run: dict[str, Any]) -> None:
    """Ergänzt Felder, die ein Lauf aus Version 1.0 noch nicht hatte."""
    if "references" not in run:
        reference = run.pop("reference", None)
        run["references"] = [reference] if reference else []
    run.setdefault("mode", MODE_STANDARD)
    run.setdefault("settle_min_seconds", SETTLE_MIN_SECONDS)
    run.setdefault("settle_window_seconds", SETTLE_WINDOW_SECONDS)
    run.setdefault("restored", {})
    run.setdefault("silent", [])
    run.setdefault("silent_notified", [])
    for member_id, member in run["members"].items():
        member.setdefault("key", member.get("ieee") or member_id)
    for data in (run.get("result") or {}).values():
        if "references" not in data:
            reference = data.pop("reference", None)
            data["references"] = [reference] if reference else []


def _round(value: float | None) -> float | None:
    """Rundet einen optionalen Wert."""
    return None if value is None else round(value, 2)
