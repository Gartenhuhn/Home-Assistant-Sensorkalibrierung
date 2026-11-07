"""Anbindung an die Zigbee2MQTT-Bridge per MQTT."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
import json
import logging
from typing import Any
from uuid import uuid4

from homeassistant.components import mqtt
from homeassistant.core import HomeAssistant, callback

from .const import Z2M_RESPONSE_TIMEOUT, Quantity

_LOGGER = logging.getLogger(__name__)


class Z2MError(Exception):
    """Zigbee2MQTT hat eine Anfrage nicht ausgeführt."""


class Z2MBridge:
    """Liest Geräteliste und Optionen und schreibt Optionen."""

    def __init__(self, hass: HomeAssistant, base_topic: str) -> None:
        """Bereitet die Bridge vor."""
        self.hass = hass
        self.on_update: Callable[[], None] | None = None
        self.base_topic = base_topic.rstrip("/")
        self.devices: dict[str, dict[str, Any]] = {}
        self.config: dict[str, Any] | None = None
        self._pending: dict[str, asyncio.Future[dict[str, Any]]] = {}
        self._unsubscribe: list[Callable[[], None]] = []

    @property
    def ready(self) -> bool:
        """True, sobald Geräteliste und Konfiguration vorliegen."""
        return bool(self.devices) and self.config is not None

    async def async_start(self) -> None:
        """Abonniert die Bridge-Topics, die retained vorliegen."""
        self._unsubscribe = [
            await mqtt.async_subscribe(
                self.hass, f"{self.base_topic}/bridge/devices", self._on_devices
            ),
            await mqtt.async_subscribe(
                self.hass, f"{self.base_topic}/bridge/info", self._on_info
            ),
            await mqtt.async_subscribe(
                self.hass,
                f"{self.base_topic}/bridge/response/device/options",
                self._on_response,
            ),
        ]

    async def async_stop(self) -> None:
        """Beendet die Abos und offene Anfragen."""
        for unsubscribe in self._unsubscribe:
            unsubscribe()
        self._unsubscribe = []
        for future in self._pending.values():
            future.cancel()
        self._pending.clear()

    @callback
    def _on_devices(self, message: mqtt.ReceiveMessage) -> None:
        """Merkt sich Gerätenamen und unterstützte Optionen."""
        try:
            payload = json.loads(message.payload)
        except ValueError:
            _LOGGER.warning("bridge/devices konnte nicht gelesen werden")
            return
        devices: dict[str, dict[str, Any]] = {}
        for device in payload:
            definition = device.get("definition") or {}
            options = {
                option.get("property") or option.get("name")
                for option in definition.get("options") or []
            }
            devices[device["ieee_address"]] = {
                "friendly_name": device.get("friendly_name"),
                "model": definition.get("model"),
                "vendor": definition.get("vendor"),
                "options": options,
            }
        self.devices = devices
        if self.on_update:
            self.on_update()

    @callback
    def _on_info(self, message: mqtt.ReceiveMessage) -> None:
        """Merkt sich die aktuelle Z2M-Konfiguration."""
        try:
            self.config = json.loads(message.payload).get("config") or {}
        except ValueError:
            _LOGGER.warning("bridge/info konnte nicht gelesen werden")
            return
        if self.on_update:
            self.on_update()

    @callback
    def _on_response(self, message: mqtt.ReceiveMessage) -> None:
        """Ordnet eine Antwort der offenen Anfrage zu."""
        try:
            payload = json.loads(message.payload)
        except ValueError:
            return
        future = self._pending.get(payload.get("transaction"))
        if future is not None and not future.done():
            future.set_result(payload)

    def supports(self, ieee: str, option: str) -> bool:
        """Prüft, ob ein Gerät eine Option anbietet."""
        return option in self.devices.get(ieee, {}).get("options", ())

    def device_options(self, ieee: str) -> dict[str, Any]:
        """Liefert die gespeicherten Optionen eines Geräts."""
        return ((self.config or {}).get("devices") or {}).get(ieee) or {}

    def effective_precision(self, ieee: str, quantity: Quantity) -> int:
        """Ermittelt die wirksame Nachkommastellen-Einstellung."""
        key = quantity.precision_option
        value = self.device_options(ieee).get(key)
        if value is None:
            value = ((self.config or {}).get("device_options") or {}).get(key)
        return quantity.default_precision if value is None else int(value)

    async def async_set_options(
        self, ieee: str, options: dict[str, Any]
    ) -> dict[str, Any]:
        """Setzt Optionen und wartet auf die Bestätigung von Z2M."""
        transaction = uuid4().hex
        future = self.hass.loop.create_future()
        self._pending[transaction] = future
        try:
            await mqtt.async_publish(
                self.hass,
                f"{self.base_topic}/bridge/request/device/options",
                json.dumps({"id": ieee, "options": options, "transaction": transaction}),
                qos=1,
            )
            async with asyncio.timeout(Z2M_RESPONSE_TIMEOUT):
                response = await future
        except TimeoutError as err:
            raise Z2MError("Zigbee2MQTT hat nicht geantwortet") from err
        finally:
            self._pending.pop(transaction, None)
        if response.get("status") != "ok":
            raise Z2MError(response.get("error") or "Zigbee2MQTT meldet einen Fehler")
        data = response.get("data") or {}
        if isinstance(data.get("to"), dict) and self.config is not None:
            devices = self.config.setdefault("devices", {})
            devices[ieee] = data["to"]
        return data
