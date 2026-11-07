"""Findet in Home Assistant die Sensoren, die kalibriert werden können."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.helpers import (
    area_registry as ar,
    device_registry as dr,
    entity_registry as er,
)

from .const import QUANTITIES, Quantity
from .z2m import Z2MBridge

GROUP_FULL = "full"
GROUP_TEMPERATURE = "temperature"
GROUP_COMPARE = "compare"

EXCLUDED_WORDS = (
    "device_temperature",
    "cpu",
    "prozessor",
    "processor",
    "wechselrichter",
    "inverter",
    "whirlpool",
    "swimspa",
    "schwimm",
    "pool",
    "forecast",
    "prognose",
    "target",
    "ziel",
    "soll",
    "heizung",
    "boiler",
    "wasser",
)


@dataclass
class Candidate:
    """Ein Gerät oder eine einzelne Entität zur Auswahl."""

    member_id: str
    name: str
    area: str | None
    group: str
    entities: dict[str, str] = field(default_factory=dict)
    correctable: list[str] = field(default_factory=list)
    ieee: str | None = None
    friendly_name: str | None = None
    battery_entity: str | None = None
    selected_by_default: bool = False

    @property
    def key(self) -> str:
        """Dauerhafter Schlüssel, bei Zigbee2MQTT die IEEE-Adresse."""
        return self.ieee or self.member_id

    def as_dict(self, hass: HomeAssistant) -> dict[str, Any]:
        """Bereitet den Kandidaten für die Kachel auf."""
        return {
            "id": self.member_id,
            "name": self.name,
            "area": self.area,
            "group": self.group,
            "quantities": sorted(self.entities, key=list(QUANTITIES).index),
            "correctable": self.correctable,
            "battery": battery_level(hass, self.battery_entity),
            "default": self.selected_by_default,
        }


def battery_level(hass: HomeAssistant, entity_id: str | None) -> float | None:
    """Liest den Batteriestand, falls vorhanden."""
    state = hass.states.get(entity_id) if entity_id else None
    if state is None or state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
        return None
    try:
        return float(state.state)
    except ValueError:
        return None


def _quantity_of(
    hass: HomeAssistant, entry: er.RegistryEntry
) -> Quantity | None:
    """Ordnet eine Entität einer Messgröße zu."""
    state = hass.states.get(entry.entity_id)
    attributes = state.attributes if state else {}
    device_class = (
        entry.device_class
        or entry.original_device_class
        or attributes.get("device_class")
    )
    unit = entry.unit_of_measurement or attributes.get("unit_of_measurement")
    for quantity in QUANTITIES.values():
        if device_class == quantity.device_class and unit == quantity.unit:
            return quantity
    return None


def _is_room_sensor(hass: HomeAssistant, entry: er.RegistryEntry) -> bool:
    """Schließt alles aus, was keine Raumluft misst."""
    if entry.disabled_by or entry.hidden_by or entry.entity_category:
        return False
    state = hass.states.get(entry.entity_id)
    if state is None or state.attributes.get("state_class") != "measurement":
        return False
    text = " ".join(
        str(item).lower()
        for item in (
            entry.entity_id,
            entry.unique_id,
            entry.original_name,
            entry.name,
            state.attributes.get("friendly_name"),
        )
        if item
    )
    return not any(word in text for word in EXCLUDED_WORDS)


def z2m_ieee(device: dr.DeviceEntry | None) -> str | None:
    """Liest die IEEE-Adresse eines Z2M-Geräts."""
    if device is None:
        return None
    for domain, identifier in device.identifiers:
        if domain == "mqtt" and identifier.startswith("zigbee2mqtt_0x"):
            return identifier.removeprefix("zigbee2mqtt_")
    return None


def find_candidates(hass: HomeAssistant, bridge: Z2MBridge) -> list[Candidate]:
    """Erstellt die Auswahlliste, gruppiert nach Gerät."""
    entities = er.async_get(hass)
    devices = dr.async_get(hass)
    areas = ar.async_get(hass)
    found: dict[str, Candidate] = {}

    for entry in list(entities.entities.values()):
        if entry.domain != "sensor":
            continue
        quantity = _quantity_of(hass, entry)
        if quantity is None or not _is_room_sensor(hass, entry):
            continue
        device = devices.async_get(entry.device_id) if entry.device_id else None
        ieee = z2m_ieee(device)
        member_id = entry.device_id or entry.entity_id
        candidate = found.get(member_id)
        if candidate is None:
            state = hass.states.get(entry.entity_id)
            area_id = entry.area_id or (device.area_id if device else None)
            area = areas.async_get_area(area_id) if area_id else None
            name = (
                (device.name_by_user or device.name)
                if device
                else state.attributes.get("friendly_name", entry.entity_id)
            )
            candidate = Candidate(
                member_id=member_id,
                name=name or entry.entity_id,
                area=area.name if area else None,
                group=GROUP_COMPARE,
                ieee=ieee,
                friendly_name=bridge.devices.get(ieee, {}).get("friendly_name")
                if ieee
                else None,
            )
            found[member_id] = candidate
        direct = ieee is not None and entry.unique_id == (
            f"{ieee}_{quantity.key}_zigbee2mqtt"
        )
        if quantity.key in candidate.entities and not direct:
            continue
        candidate.entities[quantity.key] = entry.entity_id
        if direct and bridge.supports(ieee, quantity.calibration_option):
            if quantity.key not in candidate.correctable:
                candidate.correctable.append(quantity.key)

    for candidate in found.values():
        if "temperature" in candidate.correctable:
            if "humidity" in candidate.correctable:
                candidate.group = GROUP_FULL
                candidate.selected_by_default = True
            else:
                candidate.group = GROUP_TEMPERATURE
        if devices.async_get(candidate.member_id):
            for entry in er.async_entries_for_device(entities, candidate.member_id):
                if (
                    entry.domain == "sensor"
                    and (entry.device_class or entry.original_device_class)
                    == "battery"
                ):
                    candidate.battery_entity = entry.entity_id
                    break

    order = {GROUP_FULL: 0, GROUP_TEMPERATURE: 1, GROUP_COMPARE: 2}
    return sorted(
        found.values(), key=lambda item: (order[item.group], item.name.lower())
    )
