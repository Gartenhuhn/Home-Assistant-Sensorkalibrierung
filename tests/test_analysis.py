"""Tests der Rechenlogik."""

from custom_components.sensor_kalibrierung import analysis

HOUR = 3600.0


def make(offset, drift=0.0, hours=8, every=1800, phase=0):
    """Erzeugt eine Reihe mit Raumverlauf plus festem Sensorfehler."""
    series = []
    ts = phase
    while ts <= hours * HOUR:
        room = 22 + drift * ts / HOUR
        series.append([float(ts), room + offset])
        ts += every
    return series


def test_interpolate_between_reports_and_hold():
    series = [[0.0, 20.0], [100.0, 21.0]]
    assert analysis.interpolate(series, 50, 1000) == 20.5
    assert analysis.interpolate(series, -1, 1000) is None
    assert analysis.interpolate(series, 500, 1000) == 21.0
    assert analysis.interpolate(series, 2000, 1000) is None


def test_offsets_found_with_drifting_room_and_shifted_reports():
    series = {
        "a": make(0.5, drift=0.4, every=1800, phase=0),
        "b": make(-0.3, drift=0.4, every=3300, phase=700),
        "c": make(0.0, drift=0.4, every=2400, phase=300),
        "d": make(0.1, drift=0.4, every=3000, phase=900),
    }
    stats = analysis.analyse_window(
        series, HOUR, 8 * HOUR, group_ids=list(series), max_hold=3 * HOUR
    )
    expected = {"a": 0.45, "b": -0.35, "c": -0.05, "d": 0.05}
    for key, value in expected.items():
        assert abs(stats[key].deviation - value) < 0.03


def test_outlier_does_not_move_the_group():
    series = {
        "a": make(0.0),
        "b": make(0.1),
        "c": make(-0.1),
        "d": make(0.05),
        "defekt": make(4.0),
    }
    stats = analysis.analyse_window(series, HOUR, 8 * HOUR, group_ids=list(series))
    assert abs(stats["defekt"].deviation - 3.95) < 0.11
    assert abs(stats["a"].deviation) < 0.11


def test_reference_sensor_sets_zero():
    series = {"ref": make(0.0), "a": make(0.7), "b": make(-0.4)}
    stats = analysis.analyse_window(
        series, HOUR, 8 * HOUR, group_ids=["a", "b"], reference_ids=["ref"]
    )
    assert abs(stats["a"].deviation - 0.7) < 1e-9
    assert abs(stats["b"].deviation + 0.4) < 1e-9
    assert abs(stats["ref"].deviation) < 1e-9


def test_compare_only_sensor_does_not_enter_group():
    series = {"a": make(0.2), "b": make(-0.2), "alt": make(5.0)}
    stats = analysis.analyse_window(series, HOUR, 8 * HOUR, group_ids=["a", "b"])
    assert abs(stats["a"].deviation - 0.2) < 1e-9
    assert abs(stats["alt"].deviation - 5.0) < 1e-9


def test_unstable_until_sensor_has_warmed_up():
    cold = []
    for step in range(0, 49):
        ts = step * 300.0
        cold.append([ts, 22 - 6 * 0.3 ** (ts / 1800)])
    series = {"a": make(0.0, every=900), "b": make(0.0, every=900), "cold": cold}
    assert analysis.unstable_sensors(
        series, 2 * HOUR, group_ids=list(series), tolerance=0.15
    ) == ["cold"]
    assert (
        analysis.unstable_sensors(
            series, 4 * HOUR, group_ids=list(series), tolerance=0.15
        )
        == []
    )


def test_spread():
    assert analysis.spread([1.0, -0.5, 0.2]) == 1.5
    assert analysis.spread([1.0]) is None
