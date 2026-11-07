"""Statussensor für Automationen und Anzeigen."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, PHASES

SCAN_INTERVAL = timedelta(minutes=5)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Legt den Statussensor an."""
    async_add_entities([CalibrationStatusSensor(hass, entry)])


class CalibrationStatusSensor(SensorEntity):
    """Zeigt die aktuelle Phase."""

    _attr_has_entity_name = True
    _attr_translation_key = "status"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = PHASES
    _attr_should_poll = True
    _attr_icon = "mdi:tune-vertical"
    _unrecorded_attributes = frozenset(
        {
            "last_outcome",
            "last_finished",
            "last_mode",
            "last_rolled_back",
            "last_corrected",
            "last_warnings",
            "temperature_spread_before",
            "temperature_spread_after",
            "humidity_spread_before",
            "humidity_spread_after",
            "pressure_spread_before",
            "pressure_spread_after",
            "offsets_missing",
            "new_sensors",
            "mode",
            "silent",
            "last_outside_tolerance",
            "temperature_max_before",
            "temperature_max_after",
            "humidity_max_before",
            "humidity_max_after",
            "pressure_max_before",
            "pressure_max_after",
        }
    )

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialisiert den Sensor."""
        self._data = hass.data[DOMAIN]
        self._written: str | None = None
        self._attr_unique_id = f"{entry.entry_id}_status"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Sensor-Kalibrierung",
            entry_type=DeviceEntryType.SERVICE,
        )

    async def async_added_to_hass(self) -> None:
        """Abonniert Änderungen."""
        self._data.listeners.add(self._updated)
        self.async_on_remove(lambda: self._data.listeners.discard(self._updated))

    @callback
    def _updated(self) -> None:
        """Schreibt den Zustand bei einem Phasenwechsel."""
        if self.native_value != self._written:
            self._written = self.native_value
            self.async_write_ha_state()

    async def async_update(self) -> None:
        """Alle fünf Minuten werden die Attribute neu berechnet."""

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Letztes Ergebnis, fehlende Offsets und neue Sensoren."""
        manager = self._data.manager
        return manager.status_attributes() if manager else None

    @property
    def native_value(self) -> str | None:
        """Aktuelle Phase."""
        manager = self._data.manager
        return manager.phase if manager else None
