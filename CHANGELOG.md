# Änderungen

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
