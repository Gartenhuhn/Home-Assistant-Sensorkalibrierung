"""Reine Rechenlogik der Kalibrierung, ohne Abhängigkeit zu Home Assistant.

Sensoren melden unregelmäßig, oft nur nach einer Änderung oder etwa stündlich.
Deshalb werden die Meldungen auf ein gemeinsames Zeitraster interpoliert. An
jedem Rasterpunkt zählt der Abstand zur Referenz, nicht der absolute Wert:
ändert sich die Raumtemperatur, betrifft das alle Sensoren gleich.

Die Referenz ist entweder der Median der Gruppe oder der Median einer
Referenzgruppe aus bereits kalibrierten Sensoren.
"""

from __future__ import annotations

from bisect import bisect_right
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from statistics import median

Series = Sequence[Sequence[float]]


def interpolate(series: Series, ts: float, max_hold: float) -> float | None:
    """Liefert den Wert einer sortierten Reihe zum Zeitpunkt ts."""
    if not series or ts < series[0][0]:
        return None
    index = bisect_right([point[0] for point in series], ts)
    if index >= len(series):
        last_ts, last_value = series[-1]
        return last_value if ts - last_ts <= max_hold else None
    left_ts, left_value = series[index - 1]
    right_ts, right_value = series[index]
    if right_ts - left_ts > 2 * max_hold:
        return None
    if right_ts == left_ts:
        return right_value
    share = (ts - left_ts) / (right_ts - left_ts)
    return left_value + (right_value - left_value) * share


def time_grid(start: float, end: float, step: float) -> list[float]:
    """Erzeugt die Rasterzeitpunkte im Intervall."""
    count = int((end - start) // step) + 1
    return [start + index * step for index in range(max(count, 0))]


def _references(
    series_by_id: Mapping[str, Series], reference_ids: Iterable[str] | None
) -> list[str]:
    """Referenzsensoren, die in den Daten vorkommen."""
    return [item for item in reference_ids or () if item in series_by_id]


def deviations(
    series_by_id: Mapping[str, Series],
    start: float,
    end: float,
    *,
    group_ids: Iterable[str],
    reference_ids: Iterable[str] | None = None,
    step: float = 300,
    max_hold: float = 3 * 3600,
) -> dict[str, list[tuple[float, float]]]:
    """Berechnet je Sensor den Abstand zur Referenz pro Rasterpunkt."""
    references = _references(series_by_id, reference_ids)
    group = [item for item in group_ids if item in series_by_id]
    result: dict[str, list[tuple[float, float]]] = {key: [] for key in series_by_id}
    for ts in time_grid(start, end, step):
        values = {
            key: value
            for key, series in series_by_id.items()
            if (value := interpolate(series, ts, max_hold)) is not None
        }
        if references:
            members = [values[key] for key in references if key in values]
            if not members:
                continue
        else:
            members = [values[key] for key in group if key in values]
            if len(members) < 2:
                continue
        reference = median(members)
        for key, value in values.items():
            result[key].append((ts, value - reference))
    return result


@dataclass(frozen=True)
class WindowStats:
    """Auswertung eines Sensors über ein Messfenster."""

    deviation: float
    drift: float
    noise: float
    points: int
    coverage: float


def summarize(
    points: Sequence[tuple[float, float]], grid_points: int = 0
) -> WindowStats | None:
    """Fasst die Abstände eines Sensors robust zusammen."""
    if not points:
        return None
    values = [value for _, value in points]
    center = median(values)
    half = len(values) // 2
    drift = median(values[half:]) - median(values[:half]) if half else 0.0
    noise = median(abs(value - center) for value in values)
    coverage = len(values) / grid_points if grid_points else 1.0
    return WindowStats(center, drift, noise, len(values), coverage)


def analyse_window(
    series_by_id: Mapping[str, Series],
    start: float,
    end: float,
    *,
    group_ids: Iterable[str],
    reference_ids: Iterable[str] | None = None,
    step: float = 300,
    max_hold: float = 3 * 3600,
    min_points: int = 6,
    min_coverage: float = 0.0,
) -> dict[str, WindowStats]:
    """Wertet ein Messfenster aus.

    Ohne Referenzgruppe wird die Gruppe anschließend auf null zentriert.
    Sensoren, die zu selten gemeldet haben, fehlen im Ergebnis.
    """
    group = list(group_ids)
    references = _references(series_by_id, reference_ids)
    grid_points = len(time_grid(start, end, step))
    data = deviations(
        series_by_id,
        start,
        end,
        group_ids=group,
        reference_ids=references,
        step=step,
        max_hold=max_hold,
    )
    needed = max(min_points, int(min_coverage * grid_points))
    stats: dict[str, WindowStats] = {}
    for key, points in data.items():
        if len(points) >= needed and (summary := summarize(points, grid_points)):
            stats[key] = summary
    if not references:
        centered = [stats[key].deviation for key in group if key in stats]
        if centered:
            shift = median(centered)
            stats = {
                key: WindowStats(
                    item.deviation - shift,
                    item.drift,
                    item.noise,
                    item.points,
                    item.coverage,
                )
                for key, item in stats.items()
            }
    return stats


def spread(values: Iterable[float]) -> float | None:
    """Abstand zwischen höchstem und niedrigstem Sensor."""
    items = list(values)
    return max(items) - min(items) if len(items) >= 2 else None


def unstable_sensors(
    series_by_id: Mapping[str, Series],
    now: float,
    *,
    group_ids: Iterable[str],
    tolerance: float,
    reference_ids: Iterable[str] | None = None,
    window: float = 3600,
    step: float = 300,
    max_hold: float = 3 * 3600,
    min_points: int = 6,
) -> list[str]:
    """Findet Sensoren, deren Abstand zur Referenz sich noch verändert."""
    arguments = {
        "group_ids": list(group_ids),
        "reference_ids": list(reference_ids or ()),
        "step": step,
        "max_hold": max_hold,
        "min_points": min_points,
    }
    recent = analyse_window(series_by_id, now - window, now, **arguments)
    earlier = analyse_window(series_by_id, now - 2 * window, now - window, **arguments)
    unstable = []
    for key in series_by_id:
        if key not in recent or key not in earlier or abs(recent[key].deviation - earlier[key].deviation) > tolerance:
            unstable.append(key)
    return unstable
