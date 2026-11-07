"""Texte, die Home Assistant selbst ausgibt: Fehler und Benachrichtigungen.

Die Kachel übersetzt Hinweise und Statusmeldungen selbst, anhand von Schlüssel
und Parametern. Hier stehen nur Texte, die ohne Kachel beim Nutzer ankommen.
Gewählt wird die Sprache, die in Home Assistant eingestellt ist.
"""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant

TEXTS: dict[str, dict[str, str]] = {
    "de": {
        "title": "Sensor-Kalibrierung",
        "err_selection_locked": "Während eines Laufs ist die Auswahl gesperrt",
        "err_unknown_mode": "Unbekannte Art: {mode}",
        "err_running": "Es läuft bereits eine Kalibrierung",
        "err_min_two": "Wähle mindestens zwei Sensoren aus",
        "err_none_correctable": "Keiner der gewählten Sensoren lässt sich korrigieren",
        "err_only_references": "Neben der Referenz fehlt ein Sensor, der korrigiert wird",
        "err_z2m_not_ready": "Zigbee2MQTT ist noch nicht erreichbar",
        "err_not_running": "Es läuft keine Kalibrierung",
        "err_cancel_first": "Zuerst den laufenden Durchgang abbrechen",
        "err_nothing_to_undo": "Es gibt nichts wiederherzustellen",
        "err_not_restored": "Nicht wiederhergestellt: {names}",
        "err_during_run": "Während eines Laufs nicht möglich",
        "err_nothing_stored": "Für diese Sensoren ist nichts gespeichert",
        "err_last_inactive": "Das letzte Ergebnis ist nicht mehr aktiv",
        "err_cannot_adopt": "Dieser Wert kann nicht übernommen werden",
        "err_no_backup": "Für diesen Sensor fehlt die Sicherung",
        "err_z2m": "Zigbee2MQTT: {error}",
        "err_z2m_no_confirm": "Zigbee2MQTT hat keine Änderung bestätigt",
        "silent": (
            "{names}: seit über {minutes} Minuten keine Meldung. Prüfe die "
            "Zigbee-Verbindung, zum Beispiel mit einem kurzen Druck auf die Taste. "
            "Die Kalibrierung wartet so lange."
        ),
        "done_ok_one": "1 Sensor korrigiert, innerhalb der Toleranz. Du kannst ihn zurückbringen.",
        "done_ok": "{count} Sensoren korrigiert, alle innerhalb der Toleranz. Du kannst sie zurückbringen.",
        "done_outside": "{count} Sensoren korrigiert, {outside} davon außerhalb der Toleranz. Details stehen in der Kachel.",
        "done_unchecked": "{count} Sensoren korrigiert. Die Kontrolle war ungenau, Details stehen in der Kachel.",
        "done_none": "Kein Offset gesetzt. Die Hinweise in der Kachel nennen den Grund.",
        "failed_few": "Abgebrochen: Es melden sich zu wenige Sensoren. Nichts wurde geändert.",
        "notes_one": "1 Hinweis in der Kachel.",
        "notes": "{count} Hinweise in der Kachel.",
    },
    "en": {
        "title": "Sensor calibration",
        "err_selection_locked": "The selection is locked while a run is active",
        "err_unknown_mode": "Unknown mode: {mode}",
        "err_running": "A calibration is already running",
        "err_min_two": "Select at least two sensors",
        "err_none_correctable": "None of the selected sensors can be corrected",
        "err_only_references": "Besides the reference, select a sensor to correct",
        "err_z2m_not_ready": "Zigbee2MQTT is not reachable yet",
        "err_not_running": "No calibration is running",
        "err_cancel_first": "Cancel the running calibration first",
        "err_nothing_to_undo": "There is nothing to restore",
        "err_not_restored": "Not restored: {names}",
        "err_during_run": "Not possible while a run is active",
        "err_nothing_stored": "Nothing is stored for these sensors",
        "err_last_inactive": "The last result is no longer active",
        "err_cannot_adopt": "This value cannot be applied",
        "err_no_backup": "The backup for this sensor is missing",
        "err_z2m": "Zigbee2MQTT: {error}",
        "err_z2m_no_confirm": "Zigbee2MQTT did not confirm any change",
        "silent": (
            "{names}: no report for more than {minutes} minutes. Check the Zigbee "
            "connection, for example by briefly pressing the button. The "
            "calibration waits until then."
        ),
        "done_ok_one": "1 sensor corrected, within tolerance. You can put it back.",
        "done_ok": "{count} sensors corrected, all within tolerance. You can put them back.",
        "done_outside": "{count} sensors corrected, {outside} of them outside the tolerance. See the card for details.",
        "done_unchecked": "{count} sensors corrected. The check was inaccurate, see the card for details.",
        "done_none": "No offset was set. The notes in the card explain why.",
        "failed_few": "Stopped: too few sensors are reporting. Nothing was changed.",
        "notes_one": "1 note in the card.",
        "notes": "{count} notes in the card.",
    },
}


def language(hass: HomeAssistant) -> str:
    """Sprache für Texte aus Home Assistant."""
    return "de" if (hass.config.language or "").startswith("de") else "en"


def text(hass: HomeAssistant, key: str, **params: Any) -> str:
    """Liefert einen Text in der Sprache von Home Assistant."""
    return TEXTS[language(hass)][key].format(**params)


def note(key: str, *, info: bool = False, **params: Any) -> dict[str, Any]:
    """Ein Hinweis, den die Kachel in der Sprache des Nutzers anzeigt."""
    return {"key": key, "level": "info" if info else "warning", "params": params}
