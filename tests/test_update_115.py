"""Tests für Version 1.1.5: unruhige Umgebung, Toleranz und Texte."""

from __future__ import annotations

import pytest
import test_run
from test_run import FakeZ2M, default_sensors, setup

from custom_components.sensor_kalibrierung import analysis
from custom_components.sensor_kalibrierung.const import DOMAIN
from homeassistant.components import persistent_notification
from homeassistant.core import HomeAssistant


@pytest.fixture
async def z2m(hass: HomeAssistant, mqtt_mock, custom_integrations):
    """Stellt das simulierte Zigbee2MQTT bereit."""
    return FakeZ2M(hass, mqtt_mock)


@pytest.fixture(autouse=True)
def room():
    """Setzt die Raumwerte nach jedem Test zurück."""
    saved = dict(test_run.ROOM)
    yield test_run.ROOM
    test_run.ROOM.clear()
    test_run.ROOM.update(saved)


async def run_until(z2m, freezer, manager, phase, limit_minutes=24 * 60):
    """Lässt die Simulation laufen, bis die Phase erreicht ist."""
    for _ in range(0, limit_minutes, 5):
        if manager.phase == phase:
            return
        await z2m.run(freezer, 5)
    raise AssertionError(f"Phase {phase} nicht erreicht, steht auf {manager.phase}")


async def airing(hass, z2m, freezer, room, drop=6.0):
    """Lüften: alle melden den Abfall sofort, die Erholung nur nach Plan."""
    room["humidity"] -= drop
    for ieee in z2m.sensors:
        z2m.report(ieee, jitter=0)
    await hass.async_block_till_done()
    await z2m.run(freezer, 5)
    room["humidity"] += drop


def notes(manager_or_last):
    """Schlüssel aller Hinweise."""
    return [item["key"] for item in manager_or_last["warnings"]]


def test_disturbed_points_find_fast_change():
    flat = [[0, 50.0], [3600, 50.0]]
    jump = [[0, 50.0], [1800, 50.0], [1801, 44.0], [2400, 50.0], [7200, 50.0]]
    series = {"a": jump, "b": jump, "c": flat}
    skip = analysis.disturbed_points(
        series,
        0,
        7200,
        level_ids=["a", "b"],
        tolerance=1.0,
        step=300,
        max_hold=9000,
        lookback=2700,
    )
    assert 7 in skip and 8 in skip
    assert 6 not in skip and 24 not in skip
    calm = analysis.disturbed_points(
        {"c": flat},
        0,
        3600,
        level_ids=["c"],
        tolerance=1.0,
        step=300,
        max_hold=9000,
    )
    assert calm == set()


async def test_airing_during_check_extends_it(hass, z2m, freezer, room):
    default_sensors(z2m)
    _entry, manager = await setup(hass, z2m)
    await manager.async_set_selection(manager.snapshot()["selection"], mode="quick")
    await manager.async_start()
    await run_until(z2m, freezer, manager, "verifying")
    while "verify_start" not in manager._run:
        await z2m.run(freezer, 5)
    await z2m.run(freezer, 10)
    await airing(hass, z2m, freezer, room)
    await run_until(z2m, freezer, manager, "done", limit_minutes=6 * 60)
    last = manager._last
    assert "verify_extended" in notes(last)
    humidity = last["result"]["humidity"]
    assert humidity["checked"]
    assert humidity["outside"] == []
    assert last["summary"] == {"corrected": 4, "outside": 0, "checked": True}


async def test_airing_during_measurement_extends_it(hass, z2m, freezer, room):
    default_sensors(z2m)
    _entry, manager = await setup(hass, z2m)
    await manager.async_set_selection(manager.snapshot()["selection"], mode="quick")
    await manager.async_start()
    await run_until(z2m, freezer, manager, "measuring")
    await z2m.run(freezer, 30)
    await airing(hass, z2m, freezer, room, drop=8.0)
    await run_until(z2m, freezer, manager, "verifying", limit_minutes=6 * 60)
    assert "measure_extended" in notes(manager._run)
    devices = z2m.config["devices"]
    assert devices["0x01"]["humidity_calibration"] == pytest.approx(-1.5, abs=0.3)


async def test_sensor_outside_tolerance_is_reported(hass, z2m, freezer):
    default_sensors(z2m)
    _entry, manager = await setup(hass, z2m)
    await manager.async_set_selection(manager.snapshot()["selection"], mode="quick")
    await manager.async_start()
    await run_until(z2m, freezer, manager, "verifying")
    z2m.sensors["0x01"]["errors"]["temperature"] += 0.8
    await run_until(z2m, freezer, manager, "done", limit_minutes=6 * 60)
    last = manager._last
    data = last["result"]["temperature"]
    member = z2m.sensors["0x01"]["device_id"]
    assert data["outside"] == [member]
    assert data["max_after"] > 0.5
    assert "outside_tolerance" in notes(last)
    assert last["summary"]["outside"] == 1
    message = persistent_notification._async_get_or_create_notifications(hass)[
        DOMAIN
    ]["message"]
    assert "1 of them outside the tolerance" in message


async def test_reference_run_reports_distance_to_reference(hass, z2m, freezer):
    default_sensors(z2m)
    _entry, manager = await setup(hass, z2m)
    ids = {item["name"]: item["id"] for item in manager.snapshot()["candidates"]}
    await manager.async_set_selection(
        manager.snapshot()["selection"], [ids["Klima Schlafzimmer"]], mode="quick"
    )
    await manager.async_start()
    await run_until(z2m, freezer, manager, "done", limit_minutes=6 * 60)
    data = manager._last["result"]["temperature"]
    assert data["max_before"] == pytest.approx(0.5, abs=0.05)
    assert data["max_after"] < 0.1
    attributes = manager.status_attributes()
    assert attributes["temperature_max_after"] < 0.1
    assert attributes["last_outside_tolerance"] == 0


async def test_german_texts(hass, z2m, freezer):
    hass.config.language = "de"
    default_sensors(z2m)
    _entry, manager = await setup(hass, z2m)
    await manager.async_set_selection(manager.snapshot()["selection"], mode="quick")
    await manager.async_start()
    await run_until(z2m, freezer, manager, "done", limit_minutes=6 * 60)
    message = persistent_notification._async_get_or_create_notifications(hass)[
        DOMAIN
    ]["message"]
    assert message.startswith("4 Sensoren korrigiert, alle innerhalb der Toleranz.")
    assert "1 Hinweis in der Kachel." in message
    with pytest.raises(Exception, match="mindestens zwei"):
        await manager.async_set_selection([], [])
        await manager.async_start()


async def test_running_message_is_structured(hass, z2m, freezer):
    default_sensors(z2m)
    _entry, manager = await setup(hass, z2m)
    await manager.async_start()
    message = manager.snapshot()["message"]
    assert message["key"] == "prep"
    assert message["params"]["total"] == 4
    await z2m.run(freezer, 35)
    assert manager.snapshot()["message"]["key"] in ("settle", "settle_silent")
