"""Spielt komplette Kalibrierläufe gegen ein simuliertes Zigbee2MQTT durch."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_mqtt_message,
    async_fire_time_changed,
)

from custom_components.sensor_kalibrierung.const import DOMAIN
from homeassistant.components import persistent_notification
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr, entity_registry as er

ROOM = {"temperature": 22.0, "humidity": 50.0, "pressure": 1020.0}
UNITS = {
    "temperature": ("temperature", "°C"),
    "humidity": ("humidity", "%"),
    "pressure": ("atmospheric_pressure", "hPa"),
}


class FakeZ2M:
    """Antwortet wie Zigbee2MQTT und simuliert die Sensoren."""

    def __init__(self, hass, mqtt_mock) -> None:
        self.hass = hass
        self.mqtt = mqtt_mock
        self.config = {"device_options": {"temperature_precision": 0}, "devices": {}}
        self.sensors = {}
        self.requests = []
        self.online = True
        mqtt_mock.async_publish = AsyncMock(side_effect=self._publish)
        self.minute = 0

    async def _publish(self, topic, payload, qos=0, retain=False):
        if not topic.endswith("bridge/request/device/options") or not self.online:
            return
        request = json.loads(payload)
        self.requests.append(request)
        device = self.config["devices"].setdefault(request["id"], {})
        before = dict(device)
        for key, value in request["options"].items():
            if value is None:
                device.pop(key, None)
            else:
                device[key] = value
        async_fire_mqtt_message(
            self.hass,
            "zigbee2mqtt/bridge/response/device/options",
            json.dumps(
                {
                    "data": {"from": before, "to": dict(device), "id": request["id"]},
                    "status": "ok",
                    "transaction": request["transaction"],
                }
            ),
        )

    def add(self, name, ieee, errors, options=None, battery=None, minute=0, z2m=True):
        devices = dr.async_get(self.hass)
        entities = er.async_get(self.hass)
        entry = self.hass.config_entries.async_entries("mqtt")[0]
        identifier = f"zigbee2mqtt_{ieee}" if z2m else f"other_{ieee}"
        device = devices.async_get_or_create(
            config_entry_id=entry.entry_id,
            identifiers={("mqtt", identifier)},
            name=name,
        )
        ids = {}
        for key in errors:
            entity = entities.async_get_or_create(
                "sensor",
                "mqtt",
                f"{ieee}_{key}_zigbee2mqtt",
                device_id=device.id,
                original_device_class=UNITS[key][0],
                unit_of_measurement=UNITS[key][1],
                config_entry=entry,
            )
            ids[key] = entity.entity_id
        if battery is not None:
            entity = entities.async_get_or_create(
                "sensor",
                "mqtt",
                f"{ieee}_battery_zigbee2mqtt",
                device_id=device.id,
                original_device_class="battery",
                config_entry=entry,
            )
            self.hass.states.async_set(entity.entity_id, str(battery))
        self.config["devices"][ieee] = {"friendly_name": name, **(options or {})}
        self.sensors[ieee] = {
            "name": name,
            "ids": ids,
            "errors": errors,
            "minute": minute,
            "device_id": device.id,
            "options": options or {},
            "z2m": z2m,
        }
        self.report(ieee, jitter=0)

    def publish_bridge(self):
        devices = [
            {
                "ieee_address": ieee,
                "friendly_name": item["name"],
                "definition": {
                    "model": "X",
                    "vendor": "Y",
                    "options": [
                        {"property": f"{key}_calibration"} for key in item["errors"]
                    ]
                    + [{"property": f"{key}_precision"} for key in item["errors"]],
                },
            }
            for ieee, item in self.sensors.items()
            if item["z2m"]
        ]
        async_fire_mqtt_message(
            self.hass, "zigbee2mqtt/bridge/devices", json.dumps(devices)
        )
        async_fire_mqtt_message(
            self.hass,
            "zigbee2mqtt/bridge/info",
            json.dumps({"config": self.config}),
        )

    def report(self, ieee, jitter):
        item = self.sensors[ieee]
        options = self.config["devices"].get(ieee, {})
        for key, entity_id in item["ids"].items():
            noise = 0 if key in item.get("static", ()) else jitter
            value = ROOM[key] + item["errors"][key] + noise
            value += options.get(f"{key}_calibration", 0)
            precision = options.get(
                f"{key}_precision",
                self.config["device_options"].get(f"{key}_precision", 2),
            )
            self.hass.states.async_set(
                entity_id,
                str(round(value, precision)),
                {
                    "device_class": UNITS[key][0],
                    "unit_of_measurement": UNITS[key][1],
                    "state_class": "measurement",
                },
            )

    async def run(self, freezer, minutes, every=30):
        for _ in range(0, minutes, 5):
            self.minute += 5
            freezer.tick(300)
            for index, ieee in enumerate(self.sensors):
                if (self.minute + self.sensors[ieee]["minute"]) % every == 0:
                    jitter = ((self.minute // 5 + index) % 5 - 2) * 0.005
                    self.report(ieee, jitter)
            async_fire_time_changed(self.hass)
            await self.hass.async_block_till_done()


@pytest.fixture
async def z2m(hass: HomeAssistant, mqtt_mock, custom_integrations):
    """Stellt das simulierte Zigbee2MQTT bereit."""
    return FakeZ2M(hass, mqtt_mock)


async def setup(hass, z2m, **options):
    """Richtet die Integration ein."""
    options = {"measure_hours": 6, "verify_hours": 3} | options
    entry = MockConfigEntry(
        domain=DOMAIN, data={"base_topic": "zigbee2mqtt"}, options=options
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    z2m.publish_bridge()
    await hass.async_block_till_done()
    return entry, hass.data[DOMAIN].manager


def default_sensors(z2m):
    z2m.add(
        "Klima Bad",
        "0x01",
        {"temperature": 0.5, "humidity": 2.0, "pressure": 0.3},
        minute=0,
    )
    z2m.add(
        "Klima Wohnzimmer",
        "0x02",
        {"temperature": -0.3, "humidity": -1.0, "pressure": -0.2},
        options={"temperature_calibration": 0.2},
        minute=10,
    )
    z2m.add(
        "Klima Schlafzimmer",
        "0x03",
        {"temperature": 0.0, "humidity": 0.0, "pressure": 0.0},
        minute=15,
    )
    z2m.add(
        "Klima Keller",
        "0x04",
        {"temperature": 0.1, "humidity": 0.5, "pressure": 0.1},
        battery=0,
        minute=20,
    )


async def test_candidates_are_grouped(hass, z2m):
    default_sensors(z2m)
    z2m.add("BWM Flur", "0x05", {"temperature": 0.2}, minute=5)
    z2m.add("WLAN", "0x06", {"temperature": 0.0}, z2m=False)
    _entry, manager = await setup(hass, z2m)
    snapshot = manager.snapshot()
    groups = {item["name"]: item["group"] for item in snapshot["candidates"]}
    assert groups["Klima Bad"] == "full"
    assert groups["BWM Flur"] == "temperature"
    assert groups["WLAN"] == "compare"
    assert len(snapshot["selection"]) == 4


async def test_full_run_corrects_sensors(hass, z2m, freezer):
    default_sensors(z2m)
    _entry, manager = await setup(hass, z2m)
    await manager.async_start()
    await hass.async_block_till_done()
    assert manager.phase == "preparing"
    assert z2m.config["devices"]["0x01"]["temperature_precision"] == 2
    assert any("Batterie" in item for item in manager.snapshot()["warnings"])

    await z2m.run(freezer, 35)
    assert manager.phase == "settling"
    await z2m.run(freezer, 125)
    assert manager.phase == "measuring"
    await z2m.run(freezer, 6 * 60 + 5)
    assert manager.phase == "verifying"

    devices = z2m.config["devices"]
    assert devices["0x01"]["temperature_calibration"] == pytest.approx(-0.45, abs=0.04)
    # Bestehender Offset 0,2 bleibt in der Rechnung erhalten.
    assert devices["0x02"]["temperature_calibration"] == pytest.approx(0.35, abs=0.04)

    await z2m.run(freezer, 4 * 60)
    assert manager.phase == "done"
    snapshot = manager.snapshot()
    data = snapshot["last"]["result"]["temperature"]
    assert data["spread_before"] == pytest.approx(0.6, abs=0.05)
    assert data["spread_after"] < 0.1
    notifications = persistent_notification._async_get_or_create_notifications(hass)
    assert DOMAIN in notifications
    assert "zurückbringen" in notifications[DOMAIN]["message"]
    assert snapshot["can_rollback"]
    dates = {
        item["name"]: item["last_calibrated"] for item in snapshot["candidates"]
    }
    assert dates["Klima Bad"] is not None

    await manager.async_rollback()
    await hass.async_block_till_done()
    dates = {
        item["name"]: item["last_calibrated"]
        for item in manager.snapshot()["candidates"]
    }
    assert dates["Klima Bad"] is None
    assert "temperature_precision" not in devices["0x01"]
    assert "temperature_calibration" not in devices["0x01"]
    assert devices["0x02"]["temperature_calibration"] == 0.2


async def test_outlier_is_only_reported(hass, z2m, freezer):
    default_sensors(z2m)
    z2m.add(
        "Defekt",
        "0x07",
        {"temperature": 4.0, "humidity": 0.0, "pressure": 0.0},
        minute=25,
    )
    _entry, manager = await setup(hass, z2m)
    await manager.async_start()
    await z2m.run(freezer, 170)
    await z2m.run(freezer, 6 * 60 + 5)
    assert manager.phase == "verifying"
    assert "temperature_calibration" not in z2m.config["devices"]["0x07"]
    assert any("Defekt" in item for item in manager.snapshot()["warnings"])


async def test_run_survives_reload(hass, z2m, freezer):
    default_sensors(z2m)
    entry, manager = await setup(hass, z2m)
    await manager.async_start()
    await z2m.run(freezer, 170)
    assert manager.phase == "measuring"
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    z2m.publish_bridge()
    await hass.async_block_till_done()
    manager = hass.data[DOMAIN].manager
    assert manager.phase == "measuring"
    await z2m.run(freezer, 6 * 60 + 5)
    assert manager.phase == "verifying"
    assert "temperature_calibration" in z2m.config["devices"]["0x01"]


async def test_apply_retries_when_z2m_is_offline(hass, z2m, freezer):
    default_sensors(z2m)
    _entry, manager = await setup(hass, z2m)
    await manager.async_start()
    await z2m.run(freezer, 170)
    z2m.online = False
    with patch(
        "custom_components.sensor_kalibrierung.z2m.Z2M_RESPONSE_TIMEOUT", 0.01
    ):
        await z2m.run(freezer, 6 * 60 + 5)
        assert manager.phase == "applying"
        assert "temperature_calibration" not in z2m.config["devices"]["0x01"]
        z2m.online = True
        await z2m.run(freezer, 5)
    assert manager.phase == "verifying"
    assert "temperature_calibration" in z2m.config["devices"]["0x01"]


async def test_cancel_keeps_offsets(hass, z2m, freezer):
    default_sensors(z2m)
    _entry, manager = await setup(hass, z2m)
    await manager.async_start()
    await z2m.run(freezer, 60)
    await manager.async_cancel()
    assert manager.phase == "cancelled"
    assert z2m.config["devices"]["0x02"]["temperature_calibration"] == 0.2
    assert "temperature_calibration" not in z2m.config["devices"]["0x01"]
    await manager.async_dismiss()
    assert manager.phase == "idle"


async def test_sensor_with_constant_value_still_counts(hass, z2m, freezer):
    default_sensors(z2m)
    for item in z2m.sensors.values():
        item["static"] = {"pressure"}
    _entry, manager = await setup(hass, z2m)
    await manager.async_start()
    await z2m.run(freezer, 170)
    await z2m.run(freezer, 6 * 60 + 5)
    assert manager.phase == "verifying"
    assert z2m.config["devices"]["0x01"]["pressure_calibration"] == pytest.approx(
        -0.25, abs=0.06
    )


async def test_unavailable_sensor_is_not_corrected(hass, z2m, freezer):
    default_sensors(z2m)
    _entry, manager = await setup(hass, z2m)
    await manager.async_start()
    await z2m.run(freezer, 170)
    await z2m.run(freezer, 6 * 60 - 30)
    temperature = z2m.sensors["0x01"]["ids"]["temperature"]
    del z2m.sensors["0x01"]
    hass.states.async_set(temperature, "unavailable")
    await z2m.run(freezer, 35)
    assert "temperature_calibration" not in z2m.config["devices"]["0x01"]


async def test_non_room_sensors_are_hidden(hass, z2m):
    default_sensors(z2m)
    z2m.add("Wechselrichter Dach", "0x08", {"temperature": 0.0}, z2m=False)
    _entry, manager = await setup(hass, z2m)
    entity = z2m.sensors["0x08"]["ids"]["temperature"]
    state = hass.states.get(entity)
    hass.states.async_set(
        entity,
        state.state,
        {**state.attributes, "friendly_name": "Wechselrichter 1 Temperatur"},
    )
    names = [item["name"] for item in manager.snapshot()["candidates"]]
    assert "Klima Bad" in names
    assert "Wechselrichter Dach" not in names


async def test_mixed_selection_uses_each_quantity_separately(hass, z2m, freezer):
    default_sensors(z2m)
    z2m.add("BWM Flur", "0x05", {"temperature": 0.9}, minute=5)
    z2m.add("BWM Bad", "0x06", {"temperature": -0.7}, minute=25)
    _entry, manager = await setup(hass, z2m)
    snapshot = manager.snapshot()
    everything = [item["id"] for item in snapshot["candidates"]]
    await manager.async_set_selection(everything, None)
    await manager.async_start()
    await z2m.run(freezer, 170)
    await z2m.run(freezer, 6 * 60 + 5)
    assert manager.phase == "verifying"
    devices = z2m.config["devices"]
    result = manager._run["result"]
    assert len(result["temperature"]["sensors"]) == 6
    assert len(result["humidity"]["sensors"]) == 4
    assert "temperature_calibration" in devices["0x05"]
    assert "temperature_calibration" in devices["0x06"]
    assert "humidity_calibration" not in devices["0x05"]
    assert "humidity_calibration" in devices["0x01"]


async def test_unticked_sensor_stays_untouched(hass, z2m, freezer):
    default_sensors(z2m)
    z2m.add("BWM Flur", "0x05", {"temperature": 0.9}, minute=5)
    _entry, manager = await setup(hass, z2m)
    await manager.async_start()
    await z2m.run(freezer, 170)
    await z2m.run(freezer, 6 * 60 + 5)
    assert manager.phase == "verifying"
    assert "temperature_calibration" not in z2m.config["devices"]["0x05"]
    assert "temperature_precision" not in z2m.config["devices"]["0x05"]


async def test_start_needs_two_sensors(hass, z2m):
    default_sensors(z2m)
    _entry, manager = await setup(hass, z2m)
    first = manager.snapshot()["selection"][0]
    await manager.async_set_selection([first], None)
    with pytest.raises(HomeAssistantError):
        await manager.async_start()


async def test_reference_sensor_stays_untouched(hass, z2m, freezer):
    default_sensors(z2m)
    _entry, manager = await setup(hass, z2m)
    snapshot = manager.snapshot()
    reference = next(
        item["id"] for item in snapshot["candidates"] if item["name"] == "Klima Schlafzimmer"
    )
    await manager.async_set_selection(snapshot["selection"], [reference])
    await manager.async_start()
    await z2m.run(freezer, 170)
    await z2m.run(freezer, 6 * 60 + 5)
    devices = z2m.config["devices"]
    assert "temperature_calibration" not in devices["0x03"]
    assert devices["0x01"]["temperature_calibration"] == pytest.approx(-0.5, abs=0.04)
