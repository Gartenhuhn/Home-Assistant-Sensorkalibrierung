# Changelog / Änderungen

## 1.1.6

**English**

- References are chosen with the target icon in each calibrated sensor's row. The separate reference list is gone, which makes the selection much shorter.
- Groups without a ticked sensor start collapsed.
- The result shows before and after as two lanes with the tolerance as a green area, so nothing is hidden. The dot for “after” is slightly larger than the ring for “before”.

**Deutsch**

- Referenzen wählt man mit der Zielscheibe in der Zeile jedes kalibrierten Sensors. Die eigene Referenzliste entfällt, die Auswahl wird deutlich kürzer.
- Gruppen ohne angehakten Sensor starten zugeklappt.
- Das Ergebnis zeigt vorher und nachher als zwei Spuren mit der Toleranz als grünes Feld, nichts wird mehr verdeckt. Der Punkt für „nachher“ ist etwas größer als der Ring für „vorher“.

## 1.1.5

**English**

- Card, notes and notifications in English and German. The card follows the language of the user interface.
- Unsettled phases are ignored: when airing, cooking or heating changes all sensors at once, those minutes do not count. Measuring or checking is extended once if needed.
- Results are judged against a tolerance (±0.25 °C, ±1 %, ±0.3 hPa). Sensors outside it are named; the misleading “spread did not get smaller” note is gone.
- With references, the result shows the largest distance to the reference instead of the spread.
- Shorter finish message and notification, for example “3 sensors corrected, all within tolerance”.
- English display name: Zigbee2MQTT Sensor Calibration. README in English and German, with screenshots.

**Deutsch**

- Kachel, Hinweise und Benachrichtigungen auf Deutsch und Englisch. Die Kachel folgt der Sprache der Oberfläche.
- Unruhige Phasen werden ausgeblendet: Verändern Lüften, Kochen oder Heizung alle Sensoren gleichzeitig, zählen diese Minuten nicht. Messen oder Kontrolle werden bei Bedarf einmal verlängert.
- Ergebnisse werden an einer Toleranz gemessen (±0,25 °C, ±1 %, ±0,3 hPa). Sensoren außerhalb werden genannt, der irreführende Hinweis „Streuung nicht kleiner geworden“ entfällt.
- Mit Referenz zeigt das Ergebnis den größten Abstand zur Referenz statt der Streuung.
- Kürzere Abschlussmeldung und Benachrichtigung, etwa „3 Sensoren korrigiert, alle innerhalb der Toleranz“.
- README auf Englisch und Deutsch, mit Bildern.

## 1.1.4

- Während des Laufs stehen die Referenzen in einem eigenen Abschnitt „Referenzen, bleiben unverändert“, mit grauen Balken.
- Die Überschrift sagt jetzt „Abweichung vom Mittel der Referenzen“ beziehungsweise „vom Mittel der Gruppe“.
- Statt „wartet“ steht bis zum ersten Wert ein Hinweis, dass die Werte in wenigen Minuten erscheinen.
- Beim Prüfen keine irreführende Restzeit mehr, sobald sich alle Sensoren gemeldet haben.
- Die Streuung in der Fußzeile sagt dazu, wenn sie ohne Referenzen gerechnet ist.

## 1.1.3

- Referenzen lassen sich direkt unter „Referenz“ wählen. Die Liste zeigt alle kalibrierten Sensoren, ein Haken wählt den Sensor automatisch mit aus.
- Referenzen tragen in der Auswahl die Markierung „Referenz“.
- Wird eine Referenz abgewählt, fällt sie ganz aus der Auswahl. So wird sie nicht versehentlich neu kalibriert.

## 1.1.2

- Toleranzbereich in den Sensorzeilen als zwei feine Linien statt einer Fläche.
- Der Nachher-Balken erscheint auch bei Läufen vor Version 1.1.0.
- „Rückgängig“ nur noch in der Ergebnisansicht, die Knöpfe der Auswahl passen in eine Zeile.

## 1.1.1

- Neuer Name: Zigbee2MQTT Sensor-Kalibrierung.
- Ergebnis mit großer Kennzahl, Spannweite vorher/nachher und einer Sensorliste mit gemeinsamer Achse.
- Schritte während des Laufs als Leiste mit Symbolen.
- Symbole für Temperatur, Feuchte und Druck.
- Kurzanleitung über das Fragezeichen in der Kachel.

## 1.1.0

- Schnellkalibrierung, etwa 4 bis 7 Stunden.
- Neue Standardzeiten: 4 Stunden Messen, 2 Stunden Kontrolle.
- Referenzgruppe aus mehreren kalibrierten Sensoren.
- Offsets werden je Zigbee-Adresse gespeichert und lassen sich nach einem Zurücksetzen zurückschreiben.
- Markierung „Neu“ für neue Sensoren.
- Letztes Ergebnis jederzeit abrufbar, mit Vorher/Nachher-Grafik.
- Ausreißer lassen sich nachträglich übernehmen.
- Stumme Sensoren werden erkannt und gemeldet. Werte nach einem Neustart zählen erst, wenn sich der Messwert ändert.
- Statussensor mit Attributen zum letzten Ergebnis.
