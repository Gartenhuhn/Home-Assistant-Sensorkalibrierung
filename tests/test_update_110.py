"""Tests für die Neuerungen in Version 1.1.0."""

from __future__ import annotations

import pytest
from test_run import FakeZ2M, default_sensors, setup

from custom_components.sensor_kalibrierung.const import DOMAIN
from homeassistant.components import persistent_notification
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr


@pytest.fixture
async def z2m(hass: HomeAssistant, mqtt_mock, custom_integrations):
    """Stellt das simulierte Zigbee2MQTT bereit."""
    return FakeZ2M(hass, mqtt_mock)


def ids_by_name(manager) -> dict[str, str]:
    """Mitglieds-IDs nach Name."""
    return {item["name"]: item["id"] for item in manager.snapshot()["candidates"]}


async def run_until(z2m, freezer, manager, phase, limit_minutes=24 * 60):
    """Lässt die Simulation laufen, bis die Phase erreicht ist."""
    for _ in range(0, limit_minutes, 5):
        if manager.phase == phase:
            return
        await z2m.run(freezer, 5)
    raise AssertionError(f"Phase {phase} nicht erreicht, steht auf {manager.phase}")


async def test_silent_sensor_blocks_settling_and_is_reported(hass, z2m, freezer):
    default_sensors(z2m)
    _entry, manager = await setup(hass, z2m, settle_max_hours=4)
    await manager.async_start()
    await z2m.run(freezer, 35)
    assert manager.phase == "settling"
    silent = z2m.sensors.pop("0x01")
    await z2m.run(freezer, 120)
    assert manager.phase == "settling"
    rows = {item["name"]: item for item in manager.snapshot()["sensors"]}
    assert rows["Klima Bad"]["silent_minutes"] >= 90
    assert rows["Klima Bad"]["unstable"]
    notifications = persistent_notification._async_get_or_create_notifications(hass)
    assert "Klima Bad" in notifications[f"{DOMAIN}_silent"]["message"]

    await run_until(z2m, freezer, manager, "verifying")
    item = manager._run["result"]["temperature"]["sensors"][silent["device_id"]]
    assert item["status"] == "no_data"
    assert "temperature_calibration" not in z2m.config["devices"]["0x01"]
    assert any("zu selten" in text for text in manager._run["warnings"])


async def test_restored_state_after_restart_is_ignored(hass, z2m, freezer):
    default_sensors(z2m)
    _entry, manager = await setup(hass, z2m)
    await manager.async_start()
    await z2m.run(freezer, 35)
    entity_id = z2m.sensors["0x01"]["ids"]["temperature"]
    attributes = dict(hass.states.get(entity_id).attributes)
    count = len(manager._run["samples"][entity_id])
    # Neustart: unbekannt, dann sendet Zigbee2MQTT den alten Wert erneut.
    hass.states.async_set(entity_id, "unknown", attributes)
    hass.states.async_set(entity_id, "22.55", attributes)
    hass.states.async_set(entity_id, "22.55", attributes, force_update=True)
    await hass.async_block_till_done()
    assert len(manager._run["samples"][entity_id]) == count
    hass.states.async_set(entity_id, "22.52", attributes)
    await hass.async_block_till_done()
    assert len(manager._run["samples"][entity_id]) == count + 1


async def test_same_value_reports_keep_sensor_alive(hass, z2m, freezer):
    default_sensors(z2m)
    for item in z2m.sensors.values():
        item["static"] = {"temperature", "humidity", "pressure"}
    _entry, manager = await setup(hass, z2m)
    await manager.async_start()
    await z2m.run(freezer, 35 + 180)
    assert manager.phase == "measuring"
    rows = manager.snapshot()["sensors"]
    assert all(row["silent_minutes"] is None for row in rows)


async def test_reference_group_uses_median_of_references(hass, z2m, freezer):
    default_sensors(z2m)
    z2m.add(
        "Referenz 2",
        "0x09",
        {"temperature": 0.2, "humidity": 0.0, "pressure": 0.0},
        minute=5,
    )
    _entry, manager = await setup(hass, z2m)
    ids = ids_by_name(manager)
    selection = manager.snapshot()["selection"]
    references = [ids["Klima Schlafzimmer"], ids["Referenz 2"]]
    await manager.async_set_selection(selection, references)
    assert manager.snapshot()["references"] == references
    await manager.async_start()
    await run_until(z2m, freezer, manager, "verifying")
    devices = z2m.config["devices"]
    # Referenz ist der Median aus 0,0 und 0,2, also 0,1.
    assert devices["0x01"]["temperature_calibration"] == pytest.approx(-0.4, abs=0.04)
    assert "temperature_calibration" not in devices["0x03"]
    assert "temperature_calibration" not in devices["0x09"]
    # Auch Referenzen bekommen zwei Nachkommastellen.
    assert devices["0x03"]["temperature_precision"] == 2
    statuses = {
        member_id: item["status"]
        for member_id, item in manager._run["result"]["temperature"][
            "sensors"
        ].items()
    }
    assert statuses[ids["Klima Schlafzimmer"]] == "reference"


async def test_only_references_cannot_start(hass, z2m):
    default_sensors(z2m)
    _entry, manager = await setup(hass, z2m)
    selection = manager.snapshot()["selection"]
    await manager.async_set_selection(selection, selection)
    with pytest.raises(HomeAssistantError):
        await manager.async_start()


async def test_quick_mode_finishes_in_about_four_hours(hass, z2m, freezer):
    default_sensors(z2m)
    _entry, manager = await setup(hass, z2m)
    await manager.async_set_selection(manager.snapshot()["selection"], mode="quick")
    durations = manager.snapshot()["durations"]
    assert durations["quick"]["min_hours"] == 4
    assert durations["quick"]["measure_hours"] == 2
    await manager.async_start()
    assert manager._run["mode"] == "quick"
    await run_until(z2m, freezer, manager, "done", limit_minutes=6 * 60)
    elapsed = manager._last["finished_at"] - manager._last["started_at"]
    # Im Test kommt eine halbe Stunde Vorbereitung dazu, weil die
    # Nachkommastellen erst umgestellt werden.
    assert elapsed <= 5.5 * 3600
    assert manager._last["mode"] == "quick"
    data = manager._last["result"]["temperature"]
    assert data["spread_after"] < 0.1
    devices = z2m.config["devices"]
    assert devices["0x01"]["temperature_calibration"] == pytest.approx(-0.45, abs=0.05)


async def full_run(hass, z2m, freezer, manager):
    """Kompletter Schnelllauf bis zum Ende."""
    await manager.async_set_selection(manager.snapshot()["selection"], mode="quick")
    await manager.async_start()
    await run_until(z2m, freezer, manager, "done", limit_minutes=8 * 60)


async def test_after_values_and_last_result_stay_available(hass, z2m, freezer):
    default_sensors(z2m)
    _entry, manager = await setup(hass, z2m)
    await full_run(hass, z2m, freezer, manager)
    ids = ids_by_name(manager)
    item = manager._last["result"]["temperature"]["sensors"][ids["Klima Bad"]]
    assert item["deviation"] == pytest.approx(0.45, abs=0.05)
    assert abs(item["after"]) < 0.1
    await manager.async_dismiss()
    snapshot = manager.snapshot()
    assert snapshot["phase"] == "idle"
    assert snapshot["last"]["result"]["temperature"]["sensors"]


async def test_reset_device_offsets_are_detected_and_restored(hass, z2m, freezer):
    default_sensors(z2m)
    _entry, manager = await setup(hass, z2m)
    await full_run(hass, z2m, freezer, manager)
    stored = z2m.config["devices"]["0x01"]["temperature_calibration"]
    rows = {item["name"]: item for item in manager.snapshot()["candidates"]}
    assert rows["Klima Bad"]["offset_state"] is None
    assert rows["Klima Bad"]["offsets"]["temperature_calibration"] == stored

    # Gerät in Zigbee2MQTT entfernt und neu angelernt: Optionen sind weg.
    z2m.config["devices"]["0x01"] = {"friendly_name": "Klima Bad"}
    z2m.publish_bridge()
    await hass.async_block_till_done()
    rows = {item["name"]: item for item in manager.snapshot()["candidates"]}
    assert rows["Klima Bad"]["offset_state"] == "missing"
    assert rows["Klima Wohnzimmer"]["offset_state"] is None
    assert manager.status_attributes()["offsets_missing"] == ["Klima Bad"]

    await manager.async_restore_offsets([rows["Klima Bad"]["id"]])
    await hass.async_block_till_done()
    device = z2m.config["devices"]["0x01"]
    assert device["temperature_calibration"] == stored
    assert device["temperature_precision"] == 2
    rows = {item["name"]: item for item in manager.snapshot()["candidates"]}
    assert rows["Klima Bad"]["offset_state"] is None


async def test_changed_offset_is_reported_as_different(hass, z2m, freezer):
    default_sensors(z2m)
    _entry, manager = await setup(hass, z2m)
    await full_run(hass, z2m, freezer, manager)
    z2m.config["devices"]["0x02"]["temperature_calibration"] = 1.5
    z2m.publish_bridge()
    await hass.async_block_till_done()
    rows = {item["name"]: item for item in manager.snapshot()["candidates"]}
    assert rows["Klima Wohnzimmer"]["offset_state"] == "differs"


async def test_new_device_is_flagged_until_calibrated(hass, z2m, freezer):
    default_sensors(z2m)
    z2m.add("WLAN", "0x06", {"temperature": 0.0}, z2m=False)
    _entry, manager = await setup(hass, z2m)
    rows = {item["name"]: item for item in manager.snapshot()["candidates"]}
    assert rows["Klima Bad"]["new"]
    assert not rows["WLAN"]["new"]
    assert "Klima Bad" in manager.status_attributes()["new_sensors"]
    await full_run(hass, z2m, freezer, manager)
    rows = {item["name"]: item for item in manager.snapshot()["candidates"]}
    assert not rows["Klima Bad"]["new"]
    assert manager.status_attributes()["new_sensors"] == []


async def test_outlier_can_be_adopted_and_rolled_back(hass, z2m, freezer):
    default_sensors(z2m)
    z2m.add(
        "Defekt",
        "0x07",
        {"temperature": 4.0, "humidity": 0.0, "pressure": 0.0},
        minute=25,
    )
    _entry, manager = await setup(hass, z2m)
    await full_run(hass, z2m, freezer, manager)
    ids = ids_by_name(manager)
    item = manager._last["result"]["temperature"]["sensors"][ids["Defekt"]]
    assert item["status"] == "outlier"
    assert manager.snapshot()["can_adopt"]
    with pytest.raises(HomeAssistantError):
        await manager.async_adopt_offset(ids["Klima Bad"], "temperature")

    await manager.async_adopt_offset(ids["Defekt"], "temperature")
    await hass.async_block_till_done()
    device = z2m.config["devices"]["0x07"]
    # Bezug ist der Median der Gruppe (0,1), nicht der fehlerfreie Sensor.
    assert device["temperature_calibration"] == pytest.approx(-3.9, abs=0.06)
    assert item["applied"] and item["manual"]
    rows = {item["name"]: item for item in manager.snapshot()["candidates"]}
    assert rows["Defekt"]["last_calibrated"] is not None
    assert "Defekt" in manager.status_attributes()["last_corrected"]

    await manager.async_rollback()
    await hass.async_block_till_done()
    assert "temperature_calibration" not in z2m.config["devices"]["0x07"]
    assert not manager.snapshot()["can_adopt"]


async def test_status_sensor_has_attributes(hass, z2m, freezer):
    default_sensors(z2m)
    _entry, manager = await setup(hass, z2m)
    await full_run(hass, z2m, freezer, manager)
    await z2m.run(freezer, 10)
    state = hass.states.get("sensor.sensor_kalibrierung_status")
    assert state.state == "done"
    assert state.attributes["last_outcome"] == "done"
    assert state.attributes["temperature_spread_after"] < 0.1
    assert "Klima Bad" in state.attributes["last_corrected"]
    assert state.attributes["offsets_missing"] == []


async def test_storage_from_version_10_is_migrated(hass, z2m, hass_storage):
    default_sensors(z2m)
    device = dr.async_get(hass).async_get_device(
        identifiers={("mqtt", "zigbee2mqtt_0x01")}
    )
    other = dr.async_get(hass).async_get_device(
        identifiers={("mqtt", "zigbee2mqtt_0x02")}
    )
    hass_storage[DOMAIN] = {
        "version": 1,
        "minor_version": 1,
        "key": DOMAIN,
        "data": {
            "selection": [device.id, other.id],
            "reference": other.id,
            "run": None,
            "backup": {"created_at": 1, "devices": {}, "calibrations": {}},
            "calibrations": {device.id: 1762470000.0, other.id: 1762470000.0},
            "last": {
                "outcome": "done",
                "message": "fertig",
                "started_at": 1762400000.0,
                "finished_at": 1762470000.0,
                "names": {device.id: "Klima Bad", other.id: "Klima Wohnzimmer"},
                "result": {
                    "temperature": {
                        "label": "Temperatur",
                        "unit": "°C",
                        "reference": None,
                        "sensors": {
                            device.id: {
                                "deviation": 0.5,
                                "correction": -0.5,
                                "old_offset": 0.0,
                                "new_offset": -0.5,
                                "status": "ok",
                                "applied": True,
                            },
                            other.id: {
                                "deviation": -0.1,
                                "correction": 0.1,
                                "old_offset": 0.2,
                                "new_offset": 0.3,
                                "status": "ok",
                                "applied": True,
                            },
                        },
                        "spread_before": 0.6,
                        "spread_after": 0.05,
                    }
                },
                "warnings": [],
                "dismissed": True,
                "rolled_back": False,
            },
        },
    }
    _entry, manager = await setup(hass, z2m)
    assert manager._references == [other.id]
    assert set(manager._calibrations) == {"0x01", "0x02"}
    assert manager._calibrations["0x01"]["offsets"] == {
        "temperature_calibration": -0.5
    }
    rows = {item["name"]: item for item in manager.snapshot()["candidates"]}
    assert rows["Klima Bad"]["last_calibrated"] == 1762470000.0
    assert not rows["Klima Bad"]["new"]
    # Im Test hat Zigbee2MQTT die Offsets nie bekommen.
    assert rows["Klima Bad"]["offset_state"] == "missing"


async def test_websocket_commands(hass, z2m, hass_ws_client):
    default_sensors(z2m)
    _entry, manager = await setup(hass, z2m)
    client = await hass_ws_client(hass)
    ids = ids_by_name(manager)
    await client.send_json(
        {
            "id": 1,
            "type": f"{DOMAIN}/set_selection",
            "members": list(ids.values()),
            "references": [ids["Klima Schlafzimmer"]],
            "mode": "quick",
        }
    )
    response = await client.receive_json()
    assert response["success"]
    assert manager._mode == "quick"
    assert manager._references == [ids["Klima Schlafzimmer"]]
    await client.send_json(
        {
            "id": 2,
            "type": f"{DOMAIN}/adopt_offset",
            "member": ids["Klima Bad"],
            "quantity": "temperature",
        }
    )
    response = await client.receive_json()
    assert not response["success"]
    assert response["error"]["code"] == "not_allowed"
