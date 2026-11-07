"""Websocket-Befehle für die Kachel."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN, MODES, QUANTITIES


@callback
def async_register_commands(hass: HomeAssistant) -> None:
    """Meldet die Befehle an."""
    websocket_api.async_register_command(hass, ws_subscribe)
    websocket_api.async_register_command(hass, ws_set_selection)
    websocket_api.async_register_command(hass, ws_restore_offsets)
    websocket_api.async_register_command(hass, ws_adopt_offset)


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/subscribe"})
@callback
def ws_subscribe(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Schickt der Kachel den Stand und jede Änderung."""
    data = hass.data[DOMAIN]

    @callback
    def forward() -> None:
        snapshot = data.manager.snapshot() if data.manager else {"phase": "not_loaded"}
        connection.send_message(websocket_api.event_message(msg["id"], snapshot))

    data.listeners.add(forward)

    @callback
    def unsubscribe() -> None:
        data.listeners.discard(forward)

    connection.subscriptions[msg["id"]] = unsubscribe
    connection.send_result(msg["id"])
    forward()


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/set_selection",
        vol.Required("members"): [str],
        vol.Optional("references"): [str],
        vol.Optional("reference"): vol.Any(str, None),
        vol.Optional("mode"): vol.In(MODES),
    }
)
@websocket_api.async_response
async def ws_set_selection(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Speichert die Sensorauswahl."""
    manager = hass.data[DOMAIN].manager
    if manager is None:
        connection.send_error(msg["id"], "not_loaded", "Nicht eingerichtet")
        return
    try:
        references = msg.get("references")
        if references is None and "reference" in msg:
            references = [msg["reference"]] if msg["reference"] else []
        await manager.async_set_selection(
            msg["members"], references, msg.get("mode")
        )
    except HomeAssistantError as err:
        connection.send_error(msg["id"], "not_allowed", str(err))
        return
    connection.send_result(msg["id"])


async def _run_action(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
    action: Callable[[Any], Awaitable[None]],
) -> None:
    """Führt eine Aktion aus und meldet Fehler lesbar zurück."""
    manager = hass.data[DOMAIN].manager
    if manager is None:
        connection.send_error(msg["id"], "not_loaded", "Nicht eingerichtet")
        return
    try:
        await action(manager)
    except HomeAssistantError as err:
        connection.send_error(msg["id"], "not_allowed", str(err))
        return
    connection.send_result(msg["id"])


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/restore_offsets",
        vol.Optional("members"): [str],
    }
)
@websocket_api.async_response
async def ws_restore_offsets(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Schreibt gespeicherte Offsets erneut nach Zigbee2MQTT."""
    await _run_action(
        hass,
        connection,
        msg,
        lambda manager: manager.async_restore_offsets(msg.get("members")),
    )


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/adopt_offset",
        vol.Required("member"): str,
        vol.Required("quantity"): vol.In(list(QUANTITIES)),
    }
)
@websocket_api.async_response
async def ws_adopt_offset(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Übernimmt den Offset eines Ausreißers."""
    await _run_action(
        hass,
        connection,
        msg,
        lambda manager: manager.async_adopt_offset(msg["member"], msg["quantity"]),
    )
