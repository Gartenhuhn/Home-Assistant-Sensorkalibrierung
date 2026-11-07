# Zigbee2MQTT Sensor-Kalibrierung für Home Assistant

Gleicht Sensoren ab, die nebeneinanderliegen. Danach zeigen sie vergleichbare Werte. Die Integration nutzt die Kalibrier-Optionen von Zigbee2MQTT und bringt eine eigene Kachel mit.

Korrigiert werden nur Sensoren, die über Zigbee2MQTT laufen. Andere Sensoren, auch aus ZHA oder deCONZ, können als Vergleich oder Referenz mitmessen.

## Installation

### Über HACS

1. In HACS oben rechts das Menü öffnen, **Benutzerdefinierte Repositories** wählen.
2. `https://github.com/Gartenhuhn/Home-Assistant-Sensorkalibrierung` eintragen, Typ **Integration**.
3. **Zigbee2MQTT Sensor-Kalibrierung** herunterladen und Home Assistant neu starten.
4. Weiter mit Schritt 3 unten.

### Von Hand

1. Den Ordner `custom_components/sensor_kalibrierung` nach `/config/custom_components/` kopieren.
2. Home Assistant neu starten.
3. Unter **Einstellungen > Geräte & Dienste** die Integration **Zigbee2MQTT Sensor-Kalibrierung** hinzufügen.
4. Im Dashboard eine Kachel vom Typ `custom:sensor-kalibrierung-card` anlegen. Falls sie fehlt, die Seite neu laden.

## Ablauf

1. **Sensoren auswählen und zusammenlegen.** Alle angehakten Sensoren müssen am selben Platz liegen, ruhig und ohne Sonne, Zugluft oder Heizung in der Nähe. Nicht angehakte Sensoren bleiben unverändert.
2. **Art wählen.** *Normal* passt für alle Sensoren. *Schnell* passt für Sensoren, die sich rasch angleichen, etwa Aqara.
3. **Start drücken.** Das Tool sichert die alten Optionen und stellt die Nachkommastellen ein. Es prüft auch Batterie und erste Meldungen.
4. **Angleichen.** Es wartet, bis die Abstände zwischen den Sensoren stabil sind.
5. **Messen.** Es vergleicht die Sensoren.
6. **Korrigieren und kontrollieren.** Es setzt die neuen Offsets und prüft das Ergebnis.
7. **Zurückbringen.** Die Kachel meldet das Ende. Eine Benachrichtigung kommt ebenfalls.

| | Normal | Schnell |
|---|---|---|
| Angleichen | 2 bis 8 Stunden | 1 bis 4 Stunden |
| Messen | 4 Stunden | 2 Stunden |
| Kontrolle | 2 Stunden | 1 Stunde |
| Gesamt | 8 bis 14 Stunden | 4 bis 7 Stunden |

Die Zeiten für *Normal* und die Grenzen stehen in den Optionen der Integration. Bis Version 1.0 waren es 6 Stunden Messen und 3 Stunden Kontrolle. Bestehende Einstellungen bleiben beim Update erhalten.

Das Fragezeichen oben rechts in der Kachel öffnet eine Kurzanleitung. Sie erklärt auch alle Anzeigen, Status und Hinweise.

## Neue und zurückgesetzte Sensoren

- **Neue Sensoren** tragen in der Kachel 14 Tage lang die Markierung *Neu*, bis sie kalibriert sind.
- **Referenz:** Zwei oder drei bereits kalibrierte Sensoren dazulegen und unter *Referenz* anhaken. Sie werden nicht verändert. Die anderen werden an deren Mittelwert angeglichen. Ohne Referenz zählt der Mittelwert der Gruppe.
- **Zurückgesetzte Sensoren:** Die Offsets werden je IEEE-Adresse gespeichert. Fehlen sie in Zigbee2MQTT, zeigt die Kachel *Offsets fehlen*. **Gespeicherte Offsets zurückschreiben** stellt sie wieder her, ohne neue Messung.

## Rechenweg

Die Meldungen jedes Sensors werden auf ein 5-Minuten-Raster interpoliert. Pro Rasterpunkt zählt der Abstand zum Median der Gruppe oder zum Median der Referenzsensoren. Das Ergebnis je Sensor ist der Median dieser Abstände. Ändert sich die Raumtemperatur, betrifft das alle Sensoren gleich.

Bestehende Offsets bleiben während der Messung aktiv. Der neue Offset ist der alte Offset plus die Korrektur.

## Sensoren ohne Meldung

- Gezählt werden auch Meldungen mit gleichem Wert.
- Ein Wert nach einem Neustart zählt erst, wenn sich der Messwert wirklich ändert. Zigbee2MQTT sendet nach einem Neustart den letzten bekannten Wert erneut, auch wenn der Sensor keine Verbindung hat.
- Meldet sich ein Sensor 90 Minuten nicht, wartet das Angleichen auf ihn. Eine Benachrichtigung geht raus.
- Fehlen beim Messen mehr als 2 Stunden am Stück, wird der Sensor nicht korrigiert.

## Was das Tool nicht korrigiert

- **Ausreißer:** Größere Abweichungen als in den Optionen eingestellt werden nur gemeldet, ab Werk 3 °C, 10 % und 5 hPa. Im Ergebnis lässt sich der Wert mit **Trotzdem übernehmen** setzen. Rückgängig nimmt auch das zurück.
- **Instabile Sensoren:** Driftet ein Sensor während der Messung, bleibt sein Offset unverändert.
- **Sensoren außerhalb von Zigbee2MQTT:** Sie dienen nur zum Vergleich oder als Referenz.

## Ergebnis

Die Ergebnisansicht zeigt die Streuung vorher und nachher. Eine Grafik zeigt je Sensor die Abweichung vor und nach der Korrektur. Nach dem Schließen bleibt das Ergebnis über **Letztes Ergebnis** abrufbar.

## Rückgängig

**Rückgängig** stellt Offsets, Nachkommastellen und Kalibrierdaten von vor dem letzten Lauf wieder her. Ein neuer Start ersetzt diese Sicherung.

Die Kachel zeigt unter jedem korrigierbaren Sensor, wann er zuletzt kalibriert wurde.

## Dienste

`sensor_kalibrierung.start`, `.cancel`, `.dismiss`, `.rollback` und `.restore_offsets`

Der Sensor `sensor.sensor_kalibrierung_status` zeigt die Phase, etwa für Automationen. Seine Attribute enthalten das letzte Ergebnis, fehlende Offsets und neue Sensoren. Sie werden nicht aufgezeichnet.

## Tests

```bash
pip install pytest-homeassistant-custom-component
pytest
```

## Lizenz

MIT, siehe [LICENSE](LICENSE).
