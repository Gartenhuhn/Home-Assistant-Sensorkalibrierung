"""Sensor-Kalibrierung: gleicht nebeneinanderliegende Sensoren automatisch ab."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
import json
from pathlib import Path

from homeassistant.components import mqtt
from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryNotReady, HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .const import CARD_URL, CONF_BASE_TOPIC, DEFAULT_BASE_TOPIC, DOMAIN
from .manager import CalibrationManager
from .websocket import async_register_commands
from .z2m import Z2MBridge

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)
PLATFORMS = [Platform.SENSOR]


@dataclass
class DomainData:
    """Gemeinsame Daten, bleiben beim Neuladen des Eintrags erhalten."""

    manager: CalibrationManager | None = None
    listeners: set[Callable[[], None]] = field(default_factory=set)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Registriert Kachel, Dienste und Websocket-Befehle."""
    data = hass.data.setdefault(DOMAIN, DomainData())
    folder = Path(__file__).parent
    version = await hass.async_add_executor_job(
        lambda: json.loads((folder / "manifest.json").read_text())["version"]
    )
    await hass.http.async_register_static_paths(
        [
            StaticPathConfig(
                CARD_URL, str(folder / "frontend/sensor-kalibrierung-card.js"), False
            )
        ]
    )
    add_extra_js_url(hass, f"{CARD_URL}?v={version}")
    async_register_commands(hass)

    def manager() -> CalibrationManager:
        if data.manager is None:
            raise HomeAssistantError("Sensor calibration is not set up")
        return data.manager

    async def start(_call: ServiceCall) -> None:
        await manager().async_start()

    async def cancel(_call: ServiceCall) -> None:
        await manager().async_cancel()

    async def dismiss(_call: ServiceCall) -> None:
        await manager().async_dismiss()

    async def rollback(_call: ServiceCall) -> None:
        await manager().async_rollback()

    async def restore_offsets(_call: ServiceCall) -> None:
        await manager().async_restore_offsets()

    hass.services.async_register(DOMAIN, "start", start)
    hass.services.async_register(DOMAIN, "restore_offsets", restore_offsets)
    hass.services.async_register(DOMAIN, "cancel", cancel)
    hass.services.async_register(DOMAIN, "dismiss", dismiss)
    hass.services.async_register(DOMAIN, "rollback", rollback)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Richtet Bridge und Manager ein."""
    if not await mqtt.async_wait_for_mqtt_client(hass):
        raise ConfigEntryNotReady("MQTT is not available")
    data: DomainData = hass.data[DOMAIN]
    base_topic = entry.options.get(
        CONF_BASE_TOPIC, entry.data.get(CONF_BASE_TOPIC, DEFAULT_BASE_TOPIC)
    )
    bridge = Z2MBridge(hass, base_topic)
    await bridge.async_start()
    manager = CalibrationManager(hass, entry, bridge, data.listeners)
    await manager.async_setup()
    data.manager = manager
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_options_changed))
    return True


async def _async_options_changed(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Lädt neu, ein laufender Durchgang wird dabei fortgesetzt."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Entlädt die Integration, der Lauf bleibt gespeichert."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    data: DomainData = hass.data[DOMAIN]
    if unloaded and data.manager:
        await data.manager.async_unload()
        await data.manager.bridge.async_stop()
        data.manager = None
    return unloaded
