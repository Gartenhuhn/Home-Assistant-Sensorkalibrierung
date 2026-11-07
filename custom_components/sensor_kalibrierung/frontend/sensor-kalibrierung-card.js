const DOMAIN = "sensor_kalibrierung";
const STEP_ICONS = [
  "mdi:access-point-check",
  "mdi:sine-wave",
  "mdi:chart-bell-curve-cumulative",
  "mdi:tune-variant",
  "mdi:check-decagram-outline",
];
const QUANTITIES = {
  temperature: { unit: "°C", scale: 1, tolerance: 0.25, icon: "mdi:thermometer", color: "#f08a3c" },
  humidity: { unit: "%", scale: 4, tolerance: 1, icon: "mdi:water-percent", color: "#2f9be0" },
  pressure: { unit: "hPa", scale: 1, tolerance: 0.3, icon: "mdi:gauge", color: "#8f78e8" },
};
const STATUS_ICONS = {
  ok: ["mdi:check-circle", "var(--success-color)"],
  manual: ["mdi:hand-okay", "var(--success-color)"],
  reference: ["mdi:target", "var(--primary-color)"],
  compare: ["mdi:eye-outline", "var(--secondary-text-color)"],
  outlier: ["mdi:alert-circle", "var(--warning-color)"],
  unstable: ["mdi:sine-wave", "var(--warning-color)"],
  no_data: ["mdi:signal-off", "var(--secondary-text-color)"],
  failed: ["mdi:close-circle", "var(--error-color)"],
};
const GROUPS = [
  { key: "full", open: true, icon: "mdi:thermometer-water" },
  { key: "temperature", open: true, icon: "mdi:thermometer" },
  { key: "compare", open: false, icon: "mdi:eye-outline" },
];

// Texte der Kachel. Deutsch für deutschsprachige Oberflächen, sonst Englisch.
const I18N = {
  de: {
    title: "Sensor-Kalibrierung",
    steps: ["Prüfen", "Angleichen", "Messen", "Korrigieren", "Kontrolle"],
    q: { temperature: "Temperatur", humidity: "Feuchte", pressure: "Druck" },
    q_short: { temperature: "Temperatur", humidity: "Feuchte", pressure: "Druck" },
    groups: {
      full: ["Temperatur und Feuchte", ""],
      temperature: ["Weitere Sensoren, nur Temperatur", "Anhaken, wenn der Sensor mit dazugelegt wird."],
      compare: ["Nur Vergleich, keine Korrektur", "Werden mitgemessen, aber nicht verändert."],
    },
    status: {
      ok: "Korrigiert",
      reference: "Referenz",
      compare: "Nur Vergleich",
      outlier: "Zu große Abweichung",
      unstable: "Noch nicht stabil",
      no_data: "Zu wenige Daten",
      manual: "Von Hand übernommen",
      failed: "Nicht geschrieben",
    },
    modes: {
      standard: ["Normal", "Für alle Sensoren, auch Hue-Bewegungsmelder und Rauchmelder."],
      quick: ["Schnell", "Für Sensoren, die sich schnell angleichen, etwa Aqara. Etwas ungenauer, Hue-Bewegungsmelder und Rauchmelder brauchen oft länger."],
    },
    badges: { idle: "Bereit", done: "Fertig", failed: "Fehler", cancelled: "Abgebrochen", running: "Läuft", result: "Ergebnis", help: "Anleitung", loading: "Lädt", inactive: "Nicht aktiv" },
    soon: "gleich",
    minutes_left: (p) => `noch etwa ${p.n} Minuten`,
    hour_left: "noch etwa 1 Stunde",
    hours_left: (p) => `noch etwa ${p.n} Stunden`,
    help_button: "Anleitung und Meldungen",
    help_intro: "Kurzanleitung und was die Anzeigen und Hinweise bedeuten.",
    back: "Zurück",
    close: "Schließen",
    undo: "Rückgängig",
    undo_confirm: "Wirklich zurücknehmen?",
    cancel: "Abbrechen",
    cancel_confirm: "Wirklich abbrechen?",
    start: "Starten",
    result_button: "Ergebnis",
    result_button_title: "Letztes Ergebnis ansehen",
    battery: (p) => `Batterie ${p.level} %`,
    calibrated_at: (p) => `Kalibriert am ${p.date}`,
    not_calibrated: "Noch nicht kalibriert",
    offsets_missing: "Offsets fehlen",
    offsets_changed: "Offsets geändert",
    tag_new: "Neu",
    tag_reference: "Referenz",
    of: (p) => `${p.a} von ${p.b}`,
    from_hours: (p) => `ab ${p.h} h`,
    duration: (p) => `mindestens ${p.min} und höchstens etwa ${p.max} Stunden`,
    duration_unknown: "einige Stunden",
    ref_title: "Referenz, optional",
    ref_count: (p) => `${p.n} gewählt`,
    ref_none: "Mittelwert der Gruppe",
    ref_hint: "Kalibrierte Sensoren, die nicht verändert werden. Die anderen werden an deren Mittelwert angeglichen. Für neue Sensoren zwei oder drei davon dazulegen und hier anhaken, sie werden dann automatisch mit ausgewählt.",
    ref_empty: "Noch kein Sensor ist kalibriert. Beim ersten Lauf zählt der Mittelwert der Gruppe.",
    restore_title: "Offsets passen nicht mehr:",
    restore_missing: "fehlen, Gerät wohl zurückgesetzt",
    restore_changed: "von Hand geändert",
    restore_text: "Die gespeicherten Werte lassen sich zurückschreiben, ohne neu zu kalibrieren.",
    restore_button: "Gespeicherte Offsets zurückschreiben",
    restore_confirm: "Wirklich zurückschreiben?",
    z2m_missing: "Zigbee2MQTT ist noch nicht erreichbar.",
    idle_lead: "Sensoren nebeneinanderlegen",
    idle_sub: (p) => `Alle angehakten Sensoren müssen am selben Platz liegen, ruhig und ohne Sonne, Zugluft oder Heizung. Während des Laufs möglichst nicht lüften. Nach dem Start läuft alles allein, ${p.duration}.`,
    selected: (p) => `${p.n} Sensoren ausgewählt${p.refs ? `, davon ${p.refs} als Referenz` : ""}`,
    min_two: "Wähle mindestens zwei Sensoren aus.",
    action_failed: "Die Aktion ist fehlgeschlagen.",
    selection_failed: "Die Auswahl wurde nicht gespeichert.",
    restore_failed: "Die Offsets wurden nicht geschrieben.",
    adopt_failed: "Der Offset wurde nicht übernommen.",
    silent_title: (p) => `Keine Meldung seit ${p.n} Minuten`,
    silent_short: (p) => `still ${p.n} Min.`,
    anchor: "Bezug",
    no_value: "Noch kein Wert",
    first_values: "Die ersten Werte erscheinen in wenigen Minuten.",
    refs_one: "Referenz, bleibt unverändert",
    refs_many: "Referenzen, bleiben unverändert",
    dev_group: "Abweichung vom Mittel der Gruppe",
    dev_ref: "Abweichung von der Referenz",
    dev_refs: "Abweichung vom Mittel der Referenzen",
    sensors: (p) => `${p.n} Sensoren`,
    sensors_spread: (p) => `${p.n} Sensoren, Streuung ${p.spread}${p.refs ? " ohne Referenzen" : ""}`,
    quick_suffix: ", schnell",
    msg: {
      prep: (p) => `${p.ready} von ${p.total} Sensoren haben sich gemeldet.`,
      prep_all: (p) => `${p.ready} von ${p.total} Sensoren haben sich gemeldet. In wenigen Minuten geht es weiter.`,
      settle: (p) => `${p.stable} von ${p.total} Sensoren sind stabil.`,
      settle_silent: (p) => `${p.stable} von ${p.total} Sensoren sind stabil. Mindestens ein Sensor meldet sich nicht.`,
      measuring: "Alle Sensoren werden verglichen. Du musst nichts tun.",
      applying: "Die neuen Offsets werden gesetzt.",
      verify_wait: "Warte auf die ersten korrigierten Werte.",
      verifying: "Die neuen Offsets werden kontrolliert.",
    },
    finish: {
      done_ok_one: "1 Sensor korrigiert, innerhalb der Toleranz. Du kannst ihn zurückbringen.",
      done_ok: (p) => `${p.count} Sensoren korrigiert, alle innerhalb der Toleranz. Du kannst sie zurückbringen.`,
      done_outside: (p) => `${p.count} Sensoren korrigiert, ${p.outside} davon außerhalb der Toleranz. Details stehen unten.`,
      done_unchecked: (p) => `${p.count} Sensoren korrigiert. Die Kontrolle war ungenau, Details stehen unten.`,
      done_none: "Kein Offset gesetzt. Die Hinweise unten nennen den Grund.",
      failed_few: "Abgebrochen: Es melden sich zu wenige Sensoren. Nichts wurde geändert.",
      cancelled: "Die Kalibrierung wurde abgebrochen. Nichts wurde geändert.",
      rolled_back: "Die alten Einstellungen sind wiederhergestellt.",
    },
    note: {
      battery_low: (p) => `${p.name}: Batterie ${p.level} %, die Werte können driften.`,
      z2m_no_response: (p) => `${p.name}: Zigbee2MQTT reagiert nicht, der Sensor wird nur verglichen.`,
      no_report: (p) => `${p.name}: keine Meldung erhalten, Sensor ausgelassen.`,
      not_stable: (p) => `Noch nicht stabil nach maximaler Wartezeit: ${p.names}.`,
      too_few_reports: (p) => `${p.name}: ${p.q} hat beim Messen zu selten gemeldet, nicht korrigiert.`,
      drifting: (p) => `${p.name}: ${p.q} driftet noch, nicht korrigiert.`,
      outlier: (p) => `${p.name}: ${p.q} weicht um ${p.deviation} ab, nicht korrigiert.`,
      write_failed: (p) => `${p.name}: Offset konnte nicht geschrieben werden.`,
      outside_tolerance: (p) => `${p.q}: ${p.names} nach der Korrektur außerhalb ±${p.tolerance}. Prüfe die Werte, sonst „Rückgängig“.`,
      verify_disturbed: (p) => `${p.q}: Die Kontrolle war zu unruhig, etwa durch Lüften. Die Offsets bleiben, die Werte nachher fehlen.`,
      measure_extended: (p) => `Der Raum war beim Messen unruhig, etwa durch Lüften. Die Messung wurde um ${p.minutes} Minuten verlängert.`,
      verify_extended: (p) => `Der Raum war bei der Kontrolle unruhig. Die Kontrolle wurde um ${p.minutes} Minuten verlängert.`,
    },
    hero_spread: "Streuung nachher",
    hero_spread_before: "Streuung vorher",
    hero_max: "Größter Abstand zur Referenz",
    hero_max_before: "Größter Abstand vorher",
    before_value: (p) => `vorher ${p.v}`,
    not_measured: "nachher nicht gemessen",
    all_within: (p) => `Alle korrigierten innerhalb ±${p.t}`,
    some_outside: (p) => `${p.n} außerhalb ±${p.t}`,
    span_title: "Spannweite der korrigierten Sensoren, gestrichelt vorher, gefüllt nachher",
    offset_change: (p) => `Offset ${p.a} → ${p.b}`,
    was_off: (p) => `${p.label}, lag ${p.v} daneben`,
    adopt_confirm: (p) => `Wirklich ${p.v} setzen?`,
    adopt: (p) => `Übernehmen: ${p.v}`,
    track_title: (p) => `vorher ${p.a}${p.b ? `, nachher ${p.b}` : ""}`,
    legend_before: "vorher",
    legend_after: "nachher",
    legend_tolerance: (p) => `Toleranz ±${p.t}`,
    older: "Werte nach der Korrektur je Sensor gibt es erst bei Läufen ab Version 1.1.0.",
    quick_run: "Schnellkalibrierung, ",
    time_range: (p) => `${p.a} bis ${p.b} Uhr`,
    connecting: "Verbinde mit Home Assistant …",
    not_loaded_lead: "Integration nicht eingerichtet",
    not_loaded_sub: "Füge unter Einstellungen, Geräte & Dienste die Integration Zigbee2MQTT Sensor-Kalibrierung hinzu.",
    help: [
      {
        title: "So geht's",
        open: true,
        items: [
          ["1. Anhaken", "Alle Sensoren anhaken, die mitmachen. Nicht angehakte bleiben unverändert."],
          ["2. Zusammenlegen", "Alle angehakten Sensoren dicht nebeneinander an einen ruhigen Platz legen, ohne Sonne, Zugluft oder Heizung. Guter Zigbee-Empfang ist wichtig."],
          ["3. Art wählen", "Normal passt immer. Schnell reicht für Aqara und ähnliche Sensoren."],
          ["4. Referenz, optional", "Für neue Sensoren zwei oder drei bereits kalibrierte dazulegen und unter Referenz anhaken. Oben müssen sie nicht extra angehakt werden. Ohne Referenz zählt der Mittelwert der Gruppe."],
          ["5. Starten und warten", "Ab jetzt läuft alles allein. Sensoren nicht bewegen und möglichst nicht lüften. Ein Neustart von Home Assistant schadet nicht."],
          ["6. Zurückbringen", "Wenn die Kachel „Fertig“ zeigt und die Nachricht kommt, die Sensoren an ihre Plätze bringen."],
        ],
      },
      {
        title: "Anzeigen in der Kachel",
        items: [
          ["Neu", "Seit höchstens 14 Tagen in Home Assistant und noch nie kalibriert."],
          ["Referenz", "Der Sensor dient als Messlatte und wird nicht verändert."],
          ["Offsets fehlen", "Zigbee2MQTT kennt die gespeicherten Offsets nicht mehr, meist nach Entfernen und neu Anlernen. Mit „Gespeicherte Offsets zurückschreiben“ beheben, eine neue Messung ist nicht nötig."],
          ["Offsets geändert", "Die Offsets wurden außerhalb der Kalibrierung geändert, etwa von Hand in Zigbee2MQTT. Zurückschreiben nur, wenn das nicht Absicht war."],
          ["Blauer Balken", "Abweichung des Sensors vom Mittel oder von der Referenz. Blau heißt stabil."],
          ["Oranger Balken", "Der Abstand ändert sich noch. Der Sensor gleicht sich noch an die Umgebung an, das ist am Anfang normal."],
          ["Graue Balken", "Referenzsensoren. Sie bleiben unverändert und zeigen nur, wie weit sie untereinander auseinanderliegen."],
          ["–", "Für diesen Sensor gibt es noch keinen Wert. Die Kachel rechnet alle 5 Minuten neu."],
          ["still … Min.", "Der Sensor meldet sich nicht mehr. Die Kalibrierung wartet auf ihn. Kurz die Taste am Sensor drücken oder näher an einen Router legen."],
          ["Streuung", "Abstand zwischen dem höchsten und dem niedrigsten Sensor. Mit Referenz zählt stattdessen der größte Abstand zur Referenz."],
          ["Toleranz", "Ab hier gilt ein Sensor als richtig: ±0,25 °C, ±1 % Feuchte, ±0,3 hPa."],
          ["Grafik im Ergebnis", "Ring: Abweichung vorher. Punkt: Abweichung nachher. Die grünen Linien zeigen die Toleranz."],
        ],
      },
      {
        title: "Status im Ergebnis",
        items: [
          ["Korrigiert", "Der neue Offset ist geschrieben. Angezeigt wird alter → neuer Offset."],
          ["Von Hand übernommen", "Ein Ausreißer, dessen Offset du mit „Übernehmen“ gesetzt hast."],
          ["Referenz", "Messlatte für die anderen, bleibt unverändert."],
          ["Nur Vergleich", "Lässt sich nicht über Zigbee2MQTT korrigieren, wird nur angezeigt."],
          ["Zu große Abweichung", "Die Korrektur wäre größer als die Grenze in den Optionen. Erst prüfen, ob der Sensor wirklich richtig lag. Dann „Übernehmen“ oder liegen lassen."],
          ["Noch nicht stabil", "Der Wert hat sich während der Messung verschoben. Nicht korrigiert. Später noch einmal kalibrieren."],
          ["Zu wenige Daten", "Der Sensor hat zu selten gemeldet. Nicht korrigiert. Verbindung prüfen und wiederholen."],
          ["Nicht geschrieben", "Zigbee2MQTT hat den neuen Offset nicht bestätigt."],
        ],
      },
      {
        title: "Hinweise und was zu tun ist",
        items: [
          ["Batterie … %, die Werte können driften", "Schwache Batterien verfälschen die Messung. Am besten vorher tauschen."],
          ["Zigbee2MQTT reagiert nicht", "Der Sensor war beim Start nicht erreichbar. Er bekommt keinen Offset."],
          ["keine Meldung erhalten", "Der Sensor hat sich in den ersten 2 Stunden nicht gemeldet und macht nicht mit."],
          ["seit über 90 Minuten keine Meldung", "Kommt auch als Nachricht. Taste am Sensor kurz drücken. Hilft das nicht, neu verbinden, ohne ihn in Zigbee2MQTT zu entfernen."],
          ["Raum war unruhig, verlängert", "Lüften, Kochen oder Heizung haben alle Sensoren gleichzeitig verändert. Diese Zeit zählt nicht, Messung oder Kontrolle laufen einmal länger."],
          ["außerhalb der Toleranz", "Ein Sensor liegt nach der Korrektur noch daneben. Meist hat sich der Platz verändert. Werte prüfen, sonst „Rückgängig“ und neu kalibrieren."],
          ["Kontrolle war zu unruhig", "Die Offsets sind gesetzt, nur die Kontrolle fehlt. Die Werte in den nächsten Stunden vergleichen."],
          ["driftet noch / weicht ab", "Siehe „Noch nicht stabil“ und „Zu große Abweichung“."],
          ["Offset konnte nicht geschrieben werden", "Zigbee2MQTT hat 12 Versuche nicht bestätigt. Zigbee2MQTT prüfen und neu kalibrieren."],
          ["Es melden sich zu wenige Sensoren", "Weniger als zwei Sensoren haben gemeldet. Der Lauf ist abgebrochen, nichts wurde geändert."],
        ],
      },
    ],
  },
  en: {
    title: "Sensor calibration",
    steps: ["Check", "Settle", "Measure", "Correct", "Verify"],
    q: { temperature: "Temperature", humidity: "Humidity", pressure: "Pressure" },
    q_short: { temperature: "Temperature", humidity: "Humidity", pressure: "Pressure" },
    groups: {
      full: ["Temperature and humidity", ""],
      temperature: ["Other sensors, temperature only", "Tick if the sensor is placed with the others."],
      compare: ["Comparison only, no correction", "Measured along, but never changed."],
    },
    status: {
      ok: "Corrected",
      reference: "Reference",
      compare: "Comparison only",
      outlier: "Deviation too large",
      unstable: "Not stable yet",
      no_data: "Too little data",
      manual: "Applied manually",
      failed: "Not written",
    },
    modes: {
      standard: ["Normal", "For all sensors, including Hue motion sensors and smoke detectors."],
      quick: ["Quick", "For sensors that settle fast, such as Aqara. Slightly less accurate; Hue motion sensors and smoke detectors often need longer."],
    },
    badges: { idle: "Ready", done: "Done", failed: "Error", cancelled: "Cancelled", running: "Running", result: "Result", help: "Guide", loading: "Loading", inactive: "Inactive" },
    soon: "shortly",
    minutes_left: (p) => `about ${p.n} minutes left`,
    hour_left: "about 1 hour left",
    hours_left: (p) => `about ${p.n} hours left`,
    help_button: "Guide and messages",
    help_intro: "Quick guide and what the indicators and notes mean.",
    back: "Back",
    close: "Close",
    undo: "Undo",
    undo_confirm: "Really undo?",
    cancel: "Cancel",
    cancel_confirm: "Really cancel?",
    start: "Start",
    result_button: "Result",
    result_button_title: "Show the last result",
    battery: (p) => `Battery ${p.level} %`,
    calibrated_at: (p) => `Calibrated ${p.date}`,
    not_calibrated: "Not calibrated yet",
    offsets_missing: "Offsets missing",
    offsets_changed: "Offsets changed",
    tag_new: "New",
    tag_reference: "Reference",
    of: (p) => `${p.a} of ${p.b}`,
    from_hours: (p) => `from ${p.h} h`,
    duration: (p) => `at least ${p.min} and at most about ${p.max} hours`,
    duration_unknown: "a few hours",
    ref_title: "Reference, optional",
    ref_count: (p) => `${p.n} selected`,
    ref_none: "Group average",
    ref_hint: "Calibrated sensors that are not changed. The others are matched to their average. For new sensors, place two or three of them alongside and tick them here; they are selected automatically.",
    ref_empty: "No sensor is calibrated yet. The first run uses the group average.",
    restore_title: "Offsets no longer match:",
    restore_missing: "missing, device probably reset",
    restore_changed: "changed manually",
    restore_text: "The stored values can be written back without calibrating again.",
    restore_button: "Write back stored offsets",
    restore_confirm: "Really write back?",
    z2m_missing: "Zigbee2MQTT is not reachable yet.",
    idle_lead: "Place the sensors side by side",
    idle_sub: (p) => `All ticked sensors must lie in the same spot, calm and away from sun, draughts and heating. Avoid airing the room during the run. After the start everything runs on its own, ${p.duration}.`,
    selected: (p) => `${p.n} sensors selected${p.refs ? `, ${p.refs} of them as reference` : ""}`,
    min_two: "Select at least two sensors.",
    action_failed: "The action failed.",
    selection_failed: "The selection was not saved.",
    restore_failed: "The offsets were not written.",
    adopt_failed: "The offset was not applied.",
    silent_title: (p) => `No report for ${p.n} minutes`,
    silent_short: (p) => `silent ${p.n} min`,
    anchor: "Anchor",
    no_value: "No value yet",
    first_values: "The first values appear in a few minutes.",
    refs_one: "Reference, stays unchanged",
    refs_many: "References, stay unchanged",
    dev_group: "Deviation from the group average",
    dev_ref: "Deviation from the reference",
    dev_refs: "Deviation from the reference average",
    sensors: (p) => `${p.n} sensors`,
    sensors_spread: (p) => `${p.n} sensors, spread ${p.spread}${p.refs ? " without references" : ""}`,
    quick_suffix: ", quick",
    msg: {
      prep: (p) => `${p.ready} of ${p.total} sensors have reported.`,
      prep_all: (p) => `${p.ready} of ${p.total} sensors have reported. Continuing in a few minutes.`,
      settle: (p) => `${p.stable} of ${p.total} sensors are stable.`,
      settle_silent: (p) => `${p.stable} of ${p.total} sensors are stable. At least one sensor is not reporting.`,
      measuring: "All sensors are being compared. Nothing to do.",
      applying: "Writing the new offsets.",
      verify_wait: "Waiting for the first corrected values.",
      verifying: "Checking the new offsets.",
    },
    finish: {
      done_ok_one: "1 sensor corrected, within tolerance. You can put it back.",
      done_ok: (p) => `${p.count} sensors corrected, all within tolerance. You can put them back.`,
      done_outside: (p) => `${p.count} sensors corrected, ${p.outside} of them outside the tolerance. Details below.`,
      done_unchecked: (p) => `${p.count} sensors corrected. The check was inaccurate, details below.`,
      done_none: "No offset was set. The notes below explain why.",
      failed_few: "Stopped: too few sensors are reporting. Nothing was changed.",
      cancelled: "The calibration was cancelled. Nothing was changed.",
      rolled_back: "The previous settings are restored.",
    },
    note: {
      battery_low: (p) => `${p.name}: battery ${p.level} %, values may drift.`,
      z2m_no_response: (p) => `${p.name}: Zigbee2MQTT does not respond, the sensor is compared only.`,
      no_report: (p) => `${p.name}: no report received, sensor skipped.`,
      not_stable: (p) => `Not stable after the maximum waiting time: ${p.names}.`,
      too_few_reports: (p) => `${p.name}: ${p.q} reported too rarely while measuring, not corrected.`,
      drifting: (p) => `${p.name}: ${p.q} is still drifting, not corrected.`,
      outlier: (p) => `${p.name}: ${p.q} is off by ${p.deviation}, not corrected.`,
      write_failed: (p) => `${p.name}: the offset could not be written.`,
      outside_tolerance: (p) => `${p.q}: ${p.names} outside ±${p.tolerance} after correction. Check the values, otherwise use “Undo”.`,
      verify_disturbed: (p) => `${p.q}: the check was too unsettled, for example by airing. The offsets stay, the values after are missing.`,
      measure_extended: (p) => `The room was unsettled while measuring, for example by airing. Measuring was extended by ${p.minutes} minutes.`,
      verify_extended: (p) => `The room was unsettled during the check. The check was extended by ${p.minutes} minutes.`,
    },
    hero_spread: "Spread after",
    hero_spread_before: "Spread before",
    hero_max: "Largest distance to the reference",
    hero_max_before: "Largest distance before",
    before_value: (p) => `before ${p.v}`,
    not_measured: "not measured after",
    all_within: (p) => `All corrected within ±${p.t}`,
    some_outside: (p) => `${p.n} outside ±${p.t}`,
    span_title: "Range of the corrected sensors, dashed before, filled after",
    offset_change: (p) => `Offset ${p.a} → ${p.b}`,
    was_off: (p) => `${p.label}, was off by ${p.v}`,
    adopt_confirm: (p) => `Really set ${p.v}?`,
    adopt: (p) => `Apply: ${p.v}`,
    track_title: (p) => `before ${p.a}${p.b ? `, after ${p.b}` : ""}`,
    legend_before: "before",
    legend_after: "after",
    legend_tolerance: (p) => `Tolerance ±${p.t}`,
    older: "Per-sensor values after the correction exist only for runs from version 1.1.0.",
    quick_run: "Quick calibration, ",
    time_range: (p) => `${p.a} to ${p.b}`,
    connecting: "Connecting to Home Assistant …",
    not_loaded_lead: "Integration not set up",
    not_loaded_sub: "Add the Zigbee2MQTT Sensor Calibration integration under Settings, Devices & services.",
    help: [
      {
        title: "How it works",
        open: true,
        items: [
          ["1. Tick", "Tick every sensor that takes part. Unticked sensors stay unchanged."],
          ["2. Place together", "Put all ticked sensors close together in a calm spot, away from sun, draughts and heating. Good Zigbee reception matters."],
          ["3. Choose a mode", "Normal always works. Quick is enough for Aqara and similar sensors."],
          ["4. Reference, optional", "For new sensors, add two or three calibrated ones and tick them under Reference. They don't need to be ticked above. Without a reference the group average counts."],
          ["5. Start and wait", "From now on everything runs on its own. Don't move the sensors and avoid airing. Restarting Home Assistant does no harm."],
          ["6. Put back", "When the card shows “Done” and the notification arrives, put the sensors back in place."],
        ],
      },
      {
        title: "Indicators in the card",
        items: [
          ["New", "Added to Home Assistant within the last 14 days and never calibrated."],
          ["Reference", "The sensor serves as the yardstick and is not changed."],
          ["Offsets missing", "Zigbee2MQTT no longer knows the stored offsets, usually after removing and re-pairing. Fix with “Write back stored offsets”, no new measurement needed."],
          ["Offsets changed", "The offsets were changed outside the calibration, for example by hand in Zigbee2MQTT. Write back only if that was not intended."],
          ["Blue bar", "Deviation of the sensor from the average or the reference. Blue means stable."],
          ["Orange bar", "The distance is still changing. The sensor is still adapting to its surroundings, which is normal at first."],
          ["Grey bars", "Reference sensors. They stay unchanged and only show how far apart they are."],
          ["–", "No value for this sensor yet. The card recalculates every 5 minutes."],
          ["silent … min", "The sensor stopped reporting. The calibration waits for it. Briefly press its button or move it closer to a router."],
          ["Spread", "Distance between the highest and the lowest sensor. With a reference, the largest distance to the reference counts instead."],
          ["Tolerance", "Within this a sensor counts as correct: ±0.25 °C, ±1 % humidity, ±0.3 hPa."],
          ["Chart in the result", "Ring: deviation before. Dot: deviation after. The green lines show the tolerance."],
        ],
      },
      {
        title: "Status in the result",
        items: [
          ["Corrected", "The new offset is written. Shown as old → new offset."],
          ["Applied manually", "An outlier whose offset you set with “Apply”."],
          ["Reference", "Yardstick for the others, stays unchanged."],
          ["Comparison only", "Cannot be corrected through Zigbee2MQTT, only shown."],
          ["Deviation too large", "The correction would exceed the limit in the options. First check whether the sensor really was in the same spot. Then “Apply” or leave it."],
          ["Not stable yet", "The value shifted during the measurement. Not corrected. Calibrate again later."],
          ["Too little data", "The sensor reported too rarely. Not corrected. Check the connection and repeat."],
          ["Not written", "Zigbee2MQTT did not confirm the new offset."],
        ],
      },
      {
        title: "Notes and what to do",
        items: [
          ["battery … %, values may drift", "Weak batteries distort the measurement. Best replace them first."],
          ["Zigbee2MQTT does not respond", "The sensor was not reachable at the start. It gets no offset."],
          ["no report received", "The sensor did not report within the first 2 hours and is left out."],
          ["no report for more than 90 minutes", "Also sent as a notification. Briefly press the button on the sensor. If that doesn't help, re-pair it without removing it from Zigbee2MQTT."],
          ["room was unsettled, extended", "Airing, cooking or heating changed all sensors at once. That time does not count; measuring or checking runs once more."],
          ["outside the tolerance", "A sensor is still off after the correction. Usually the spot changed. Check the values, otherwise “Undo” and calibrate again."],
          ["check was too unsettled", "The offsets are set, only the check is missing. Compare the values over the next hours."],
          ["still drifting / is off by", "See “Not stable yet” and “Deviation too large”."],
          ["offset could not be written", "Zigbee2MQTT did not confirm 12 attempts. Check Zigbee2MQTT and calibrate again."],
          ["too few sensors are reporting", "Fewer than two sensors reported. The run stopped, nothing was changed."],
        ],
      },
    ],
  },
};

let LANG = "de";
let LOCALE = "de-DE";

const t = (key, params = {}) => {
  const parts = key.split(".");
  let value = I18N[LANG];
  let fallback = I18N.en;
  for (const part of parts) {
    value = value?.[part];
    fallback = fallback?.[part];
  }
  const found = value ?? fallback;
  if (typeof found === "function") return found(params);
  return found ?? key;
};

const qLabel = (key) => t(`q.${key}`);

const escapeHtml = (value) =>
  String(value ?? "").replace(
    /[&<>"']/g,
    (char) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        char
      ],
  );

const number = (value, digits = 2) =>
  Number(value).toLocaleString(LOCALE, {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });

const signed = (value, digits = 2) => {
  const text = number(Math.abs(value), digits);
  if (Number(value.toFixed(digits)) === 0) return text;
  return `${value > 0 ? "+" : "−"}${text}`;
};

const hours = (value) => number(value, Number.isInteger(value) ? 0 : 1);

const tolerance = (key) => {
  const value = QUANTITIES[key].tolerance;
  return `${number(value, value < 1 ? 2 : 0)}\u00a0${QUANTITIES[key].unit}`;
};

const remaining = (timestamp) => {
  if (!timestamp) return "";
  const minutes = Math.round((timestamp * 1000 - Date.now()) / 60000);
  if (minutes <= 2) return t("soon");
  if (minutes < 60) return t("minutes_left", { n: minutes });
  const left = minutes / 60;
  if (left < 1.5) return t("hour_left");
  return t("hours_left", { n: Math.round(left) });
};

const clock = (timestamp) =>
  new Date(timestamp * 1000).toLocaleString(LOCALE, {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });

const fullDate = (timestamp) =>
  new Date(timestamp * 1000).toLocaleString(LOCALE, {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });

// Hinweise kommen als Schlüssel mit Parametern, ältere Läufe als fertiger Text.
const noteText = (item) => {
  if (typeof item === "string") return item;
  const params = { ...item.params };
  if (params.quantity) params.q = qLabel(params.quantity);
  if (params.deviation !== undefined && params.quantity) {
    params.deviation = `${signed(params.deviation)}\u00a0${QUANTITIES[params.quantity].unit}`;
  }
  if (params.tolerance !== undefined && params.quantity) {
    params.tolerance = tolerance(params.quantity);
  }
  return t(`note.${item.key}`, params);
};

const messageText = (message) => {
  if (!message) return "";
  if (typeof message === "string") return message;
  return t(`msg.${message.key}`, message.params || {});
};

const finishText = (last) => {
  if (last.rolled_back) return t("finish.rolled_back");
  const message = last.message;
  const summary = last.summary;
  if (message === "done" && summary) {
    if (summary.outside) {
      return t("finish.done_outside", { count: summary.corrected, outside: summary.outside });
    }
    if (!summary.checked) return t("finish.done_unchecked", { count: summary.corrected });
    if (summary.corrected === 1) return t("finish.done_ok_one");
    return t("finish.done_ok", { count: summary.corrected });
  }
  if (I18N.de.finish[message]) return t(`finish.${message}`, summary || {});
  return message;
};

const STYLES = `
  :host { display: block; }
  ha-card { padding: 16px; color: var(--primary-text-color); }
  * { box-sizing: border-box; }
  header { display: flex; align-items: center; gap: 10px; }
  header ha-icon { color: var(--primary-color); --mdc-icon-size: 24px; }
  h2 { font-size: 16px; font-weight: 500; margin: 0; flex: 1; min-width: 0; }
  .badge { font-size: 12px; padding: 3px 10px; border-radius: 12px; white-space: nowrap;
    background: color-mix(in srgb, var(--badge) 16%, transparent); color: var(--badge); }
  .lead { font-size: 16px; font-weight: 500; margin: 14px 0 2px; }
  .sub { font-size: 14px; color: var(--secondary-text-color); margin: 0 0 12px; line-height: 1.45; }
  .steps { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 4px; margin-bottom: 14px; }
  .step { font-size: 11px; color: var(--secondary-text-color); overflow: hidden; text-overflow: ellipsis; }
  .step i { display: block; height: 5px; border-radius: 3px; margin-bottom: 4px;
    background: var(--divider-color); }
  .step.done i { background: var(--primary-color); }
  .step.now i { background: color-mix(in srgb, var(--primary-color) 55%, transparent); }
  .step.now { color: var(--primary-color); }
  .tabs { display: flex; gap: 4px; margin-bottom: 10px; }
  .tabs button { flex: 1; min-height: 34px; font-size: 13px; }
  .tabs button.on { background: color-mix(in srgb, var(--primary-color) 16%, transparent);
    border-color: var(--primary-color); color: var(--primary-color); }
  .label { font-size: 13px; color: var(--secondary-text-color); margin: 0 0 8px; }
  .bars { display: grid; grid-template-columns: minmax(0, 120px) minmax(0, 1fr) 72px; gap: 8px; align-items: center; font-size: 13px; }
  .name { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .track { position: relative; height: 8px; }
  .track::before { content: ""; position: absolute; left: 50%; top: -3px; bottom: -3px; width: 1px; background: var(--divider-color); }
  .bar { position: absolute; top: 0; height: 8px; background: var(--primary-color); }
  .bar.warn { background: var(--warning-color); }
  .bar.ref { background: color-mix(in srgb, var(--secondary-text-color) 55%, transparent); }
  .label.sublabel { margin-top: 14px; }
  .value { text-align: right; white-space: nowrap; font-variant-numeric: tabular-nums; }
  .muted { color: var(--secondary-text-color); }
  .warn-text { color: var(--warning-color); }
  .notes { margin: 12px 0 0; padding: 0; list-style: none; font-size: 13px; line-height: 1.4; }
  .notes li { display: flex; gap: 6px; color: var(--warning-color); margin-top: 4px; }
  .notes ha-icon { --mdc-icon-size: 16px; flex: none; }
  footer { display: flex; align-items: center; justify-content: flex-end; flex-wrap: wrap; gap: 8px; border-top: 1px solid var(--divider-color); margin-top: 14px; padding-top: 12px; }
  footer .info { flex: 1; min-width: 140px; font-size: 13px; color: var(--secondary-text-color); }
  button { font: inherit; font-size: 14px; min-height: 40px; padding: 0 14px; border-radius: 8px; cursor: pointer;
    background: transparent; color: var(--primary-text-color); border: 1px solid var(--divider-color); }
  button:hover { border-color: var(--primary-color); }
  button:focus-visible, select:focus-visible, input:focus-visible { outline: 2px solid var(--primary-color); outline-offset: 2px; }
  button.primary { background: var(--primary-color); border-color: var(--primary-color); color: var(--text-primary-color); }
  button.danger { border-color: var(--error-color); color: var(--error-color); }
  details { border-top: 1px solid var(--divider-color); padding: 8px 0; }
  summary { font-size: 13px; color: var(--secondary-text-color); cursor: pointer; min-height: 28px; display: flex; align-items: center; gap: 6px; }
  summary span { margin-left: auto; }
  .hint { font-size: 12px; color: var(--secondary-text-color); margin: 0 0 4px; }
  label.pick { display: flex; align-items: center; gap: 10px; min-height: 44px; padding: 4px 0; font-size: 14px; line-height: 1.3; cursor: pointer; }
  label.pick input { width: 18px; height: 18px; margin: 0; flex: none; accent-color: var(--primary-color); }
  label.pick .text { flex: 1; min-width: 0; }
  label.pick .line { display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  label.pick .when { display: block; font-size: 12px; color: var(--secondary-text-color); }
  label.pick small { color: var(--secondary-text-color); font-size: 12px; }
  label.pick .low { color: var(--warning-color); font-size: 12px; white-space: nowrap; }
  .field { display: flex; flex-direction: column; gap: 4px; font-size: 13px; color: var(--secondary-text-color); border-top: 1px solid var(--divider-color); padding-top: 10px; }
  select { font: inherit; font-size: 14px; min-height: 40px; padding: 0 8px; border-radius: 8px; width: 100%;
    color: var(--primary-text-color); background: var(--card-background-color); border: 1px solid var(--divider-color); }
  .metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(110px, 1fr)); gap: 8px; margin: 12px 0; }
  .metric { background: color-mix(in srgb, var(--primary-text-color) 5%, transparent); border-radius: 8px; padding: 10px 12px; }
  .metric span { display: block; font-size: 12px; color: var(--secondary-text-color); }
  .metric b { font-size: 18px; font-weight: 500; font-variant-numeric: tabular-nums; }
  .result { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 2px 10px; font-size: 13px; }
  .result .name { padding-top: 6px; }
  .result .value { padding-top: 6px; }
  .result .state { grid-column: 1 / -1; font-size: 12px; color: var(--secondary-text-color); }
  .error { color: var(--error-color); font-size: 13px; margin: 10px 0 0; }
  .segment { display: flex; gap: 4px; margin: 0 0 6px; }
  .segment button { flex: 1; }
  .segment button.on, .tabs button.on { background: color-mix(in srgb, var(--primary-color) 16%, transparent);
    border-color: var(--primary-color); color: var(--primary-color); }
  .tag { display: inline-block; font-size: 11px; line-height: 16px; padding: 0 6px; border-radius: 8px; margin-left: 6px; vertical-align: 1px;
    background: color-mix(in srgb, var(--tag) 16%, transparent); color: var(--tag); white-space: nowrap; }
  .box { border: 1px solid color-mix(in srgb, var(--warning-color) 50%, transparent); border-radius: 8px; padding: 10px 12px; margin: 10px 0 0; font-size: 13px; line-height: 1.45; }
  .box p { margin: 0 0 8px; }
  .box button { min-height: 36px; }
  .silent { color: var(--warning-color); }
  .chart { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 0 8px; align-items: center; font-size: 13px; margin: 4px 0 12px; }
  .chart .name { padding-top: 4px; }
  .chart .value { padding-top: 4px; font-size: 12px; color: var(--secondary-text-color); }
  .chart .track { grid-column: 1 / -1; height: 14px; margin: 2px 0 2px; }
  .chart .track::before { top: 0; bottom: 0; }
  .chart .link { position: absolute; top: 6px; height: 2px; background: color-mix(in srgb, var(--secondary-text-color) 45%, transparent); }
  .dot { position: absolute; top: 3px; width: 8px; height: 8px; margin-left: -4px; border-radius: 50%; }
  .dot.before { border: 2px solid var(--secondary-text-color); background: var(--card-background-color); }
  .dot.after { background: var(--primary-color); box-shadow: 0 0 0 2px var(--card-background-color); }
  .axis { grid-column: 1 / -1; padding: 0 1%; display: flex; justify-content: space-between; font-size: 11px; color: var(--secondary-text-color); font-variant-numeric: tabular-nums; }
  .legend { display: flex; gap: 14px; font-size: 12px; color: var(--secondary-text-color); margin: 0 0 6px; }
  .legend span { display: inline-flex; align-items: center; gap: 6px; }
  .legend .dot { position: static; margin: 0; }
  .result .state button { min-height: 32px; font-size: 12px; margin-top: 4px; }
  header button.help { min-height: 36px; min-width: 36px; padding: 0; border: none; border-radius: 50%;
    display: inline-flex; align-items: center; justify-content: center; color: var(--secondary-text-color); }
  header button.help:hover { color: var(--primary-color); }
  header button.help ha-icon { color: inherit; --mdc-icon-size: 22px; }
  dl { margin: 0 0 6px; font-size: 13px; line-height: 1.45; }
  dt { font-weight: 500; margin-top: 8px; }
  dd { margin: 2px 0 0; color: var(--secondary-text-color); }

  /* Kopf */
  header .mark { width: 36px; height: 36px; border-radius: 10px; flex: none; display: grid; place-items: center;
    background: color-mix(in srgb, var(--primary-color) 14%, transparent); }
  header .mark ha-icon { --mdc-icon-size: 22px; }
  h2 { font-size: 17px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

  /* Reiter mit Symbol und Farbe je Messgröße */
  .tabs { background: color-mix(in srgb, var(--primary-text-color) 6%, transparent); border-radius: 12px; padding: 4px; gap: 2px; margin-bottom: 14px; }
  .tabs button { border: none; border-radius: 9px; min-height: 36px; display: inline-flex; align-items: center; justify-content: center; gap: 6px; color: var(--secondary-text-color); }
  .tabs button ha-icon { --mdc-icon-size: 18px; color: var(--q); }
  .tabs button.on { background: var(--card-background-color); color: var(--primary-text-color); border: none;
    box-shadow: 0 1px 3px color-mix(in srgb, #000 22%, transparent); }

  /* Schritte */
  .stepper { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); margin: 4px 0 16px; }
  .stepper .s { position: relative; display: flex; flex-direction: column; align-items: center; gap: 6px; font-size: 11px; color: var(--secondary-text-color); text-align: center; }
  .stepper .s::before { content: ""; position: absolute; top: 15px; left: -50%; right: 50%; height: 2px; background: var(--divider-color); z-index: 0; }
  .stepper .s:first-child::before { display: none; }
  .stepper .s.done::before, .stepper .s.now::before { background: var(--primary-color); }
  .stepper .c { position: relative; z-index: 1; width: 32px; height: 32px; border-radius: 50%; display: grid; place-items: center;
    background: var(--card-background-color); border: 2px solid var(--divider-color); }
  .stepper .c ha-icon { --mdc-icon-size: 17px; }
  .stepper .s.done .c { background: var(--primary-color); border-color: var(--primary-color); color: var(--text-primary-color); }
  .stepper .s.now .c { border-color: var(--primary-color); color: var(--primary-color); animation: breathe 2.4s ease-in-out infinite; }
  .stepper .s.now { color: var(--primary-text-color); font-weight: 500; }
  @keyframes breathe { 0%, 100% { box-shadow: 0 0 0 0 color-mix(in srgb, var(--primary-color) 35%, transparent); }
    50% { box-shadow: 0 0 0 6px color-mix(in srgb, var(--primary-color) 0%, transparent); } }
  @media (prefers-reduced-motion: reduce) { .stepper .s.now .c { animation: none; } }

  /* Ergebnis: Kopfzahl und Spannweite */
  .hero { display: grid; grid-template-columns: auto minmax(0, 1fr); gap: 2px 14px; align-items: end; margin: 2px 0 12px; }
  .hero .big { font-size: 34px; line-height: 1; font-weight: 600; font-variant-numeric: tabular-nums; letter-spacing: -0.5px; }
  .hero .big small { font-size: 16px; font-weight: 500; margin-left: 3px; color: var(--secondary-text-color); }
  .hero .what { font-size: 13px; color: var(--secondary-text-color); line-height: 1.35; padding-bottom: 2px; }
  .hero .what b { color: var(--primary-text-color); font-weight: 500; }
  .span { position: relative; height: 34px; margin: 6px 0 2px; }
  .span .base { position: absolute; left: 0; right: 0; top: 16px; height: 2px; background: var(--divider-color); }
  .span .zero { position: absolute; left: 50%; top: 4px; bottom: 4px; width: 1px; background: var(--secondary-text-color); opacity: .5; }
  .span .before { position: absolute; top: 11px; height: 12px; border-radius: 6px; border: 2px dashed color-mix(in srgb, var(--secondary-text-color) 80%, transparent); }
  .span .after { position: absolute; top: 9px; height: 16px; border-radius: 8px; min-width: 6px; background: var(--primary-color); box-shadow: 0 0 0 3px var(--card-background-color); }
  .span-legend { display: flex; justify-content: space-between; font-size: 11px; color: var(--secondary-text-color); font-variant-numeric: tabular-nums; margin-bottom: 14px; }

  /* Sensorliste mit gemeinsamer Achse */
  .list { margin: 0; }
  .list .row { display: grid; grid-template-columns: 22px minmax(0, 1fr) minmax(104px, 40%); gap: 0 10px; align-items: center; padding: 7px 0;
    border-top: 1px solid color-mix(in srgb, var(--divider-color) 70%, transparent); }
  .list .row > ha-icon { --mdc-icon-size: 20px; }
  .list .who { min-width: 0; }
  .list .who b { display: block; font-weight: 500; font-size: 14px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .list .who span { display: block; font-size: 12px; color: var(--secondary-text-color); font-variant-numeric: tabular-nums; }
  .list .who button { min-height: 30px; font-size: 12px; margin-top: 5px; padding: 0 10px; }
  .mini { position: relative; height: 22px; }
  .mini .zone { position: absolute; top: 2px; bottom: 2px; border-left: 1px solid color-mix(in srgb, var(--success-color) 75%, transparent);
    border-right: 1px solid color-mix(in srgb, var(--success-color) 75%, transparent); }
  .mini .zero { position: absolute; left: 50%; top: 0; bottom: 0; width: 1px; background: var(--divider-color); }
  .mini .link { position: absolute; top: 10px; height: 2px; background: color-mix(in srgb, var(--secondary-text-color) 45%, transparent); }
  .mini .dot.clip::after { content: ""; position: absolute; top: 1px; width: 0; height: 0; border-top: 4px solid transparent; border-bottom: 4px solid transparent; }
  .mini .dot.clip.right::after { left: 11px; border-left: 5px solid var(--secondary-text-color); }
  .mini .dot.clip.left::after { right: 11px; border-right: 5px solid var(--secondary-text-color); }
  .mini .dot { top: 6px; width: 10px; height: 10px; margin-left: -5px; }
  .mini .dot.before, .legend .dot.before { border: 2px solid var(--secondary-text-color); background: var(--card-background-color); }
  .mini .dot.after, .legend .dot.after { background: var(--primary-color); box-shadow: 0 0 0 2px var(--card-background-color); }
  .list .scale { display: grid; grid-template-columns: 22px minmax(0, 1fr) minmax(104px, 40%); gap: 0 10px; font-size: 11px; color: var(--secondary-text-color);
    border-top: 1px solid color-mix(in srgb, var(--divider-color) 70%, transparent); padding-top: 4px; font-variant-numeric: tabular-nums; }
  .list .scale div { grid-column: 3; display: flex; justify-content: space-between; }
  .legend { flex-wrap: wrap; margin: 0 0 4px; }
  .legend .zonekey { width: 12px; height: 12px; border-left: 1px solid var(--success-color); border-right: 1px solid var(--success-color); }
  .legend .dot { width: 10px; height: 10px; }
  .older { font-size: 12px; color: var(--secondary-text-color); margin: 0 0 6px; }

  /* Auswahl */
  .qi { display: inline-flex; gap: 1px; flex: none; }
  .qi ha-icon { --mdc-icon-size: 16px; color: var(--q); opacity: .9; }
  summary ha-icon { --mdc-icon-size: 18px; }
  .segment { background: color-mix(in srgb, var(--primary-text-color) 6%, transparent); border-radius: 12px; padding: 4px; gap: 2px; }
  .segment button { border: none; border-radius: 9px; display: inline-flex; align-items: center; justify-content: center; gap: 6px; color: var(--secondary-text-color); }
  .segment button ha-icon { --mdc-icon-size: 18px; }
  .segment button.on { background: var(--card-background-color); color: var(--primary-text-color); border: none;
    box-shadow: 0 1px 3px color-mix(in srgb, #000 22%, transparent); }
  .segment button.on ha-icon { color: var(--primary-color); }
  button.primary { display: inline-flex; align-items: center; gap: 6px; font-weight: 500; }
  button.primary ha-icon, button.with-icon ha-icon { --mdc-icon-size: 18px; }
  button.with-icon { display: inline-flex; align-items: center; gap: 6px; }
  footer .info.full { flex: 1 1 100%; }
  .notes li.info, .notes li.info ha-icon { color: var(--secondary-text-color); }
  .tabs button { flex: 1 1 0; min-width: 0; padding: 4px; flex-direction: column; gap: 1px; min-height: 46px; font-size: 12px; }
  .tabs button span { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
`;

class SensorKalibrierungCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._state = null;
    this._quantity = "temperature";
    this._error = "";
    this._confirm = null;
    this._openGroups = {};
    this._busy = false;
    this._showLast = false;
    this._help = false;
  }

  static getStubConfig() {
    return {};
  }

  setConfig(config) {
    this._config = config || {};
    this._render();
  }

  set hass(hass) {
    const first = !this._hass;
    this._hass = hass;
    const language = hass?.locale?.language || hass?.language || "en";
    const lang = language.toLowerCase().startsWith("de") ? "de" : "en";
    const changed = lang !== LANG || language !== LOCALE;
    LANG = lang;
    LOCALE = language;
    if (first || !this._unsubscribe) this._subscribe();
    else if (changed) this._render();
  }

  connectedCallback() {
    if (this._hass) this._subscribe();
    this._timer = window.setInterval(() => this._render(), 60000);
  }

  disconnectedCallback() {
    window.clearInterval(this._timer);
    const unsubscribe = this._unsubscribe;
    this._unsubscribe = null;
    this._subscribing = false;
    if (unsubscribe) unsubscribe.then((stop) => stop()).catch(() => {});
  }

  getCardSize() {
    return 6;
  }

  getGridOptions() {
    return { columns: 12, rows: "auto" };
  }

  _subscribe() {
    if (this._subscribing || !this._hass?.connection) return;
    this._subscribing = true;
    this._unsubscribe = this._hass.connection.subscribeMessage(
      (state) => {
        this._state = state;
        this._render();
      },
      { type: `${DOMAIN}/subscribe` },
    );
    this._unsubscribe.catch(() => {
      this._state = { phase: "not_loaded" };
      this._unsubscribe = null;
      this._render();
    });
  }

  async _call(service) {
    if (this._busy) return;
    this._busy = true;
    this._error = "";
    this._confirm = null;
    this._render();
    try {
      await this._hass.callService(DOMAIN, service, {});
    } catch (err) {
      this._error = err.message || t("action_failed");
    }
    this._busy = false;
    this._render();
  }

  async _send(message, fallback) {
    if (this._busy) return;
    this._busy = true;
    this._error = "";
    this._confirm = null;
    this._render();
    try {
      await this._hass.connection.sendMessagePromise(message);
    } catch (err) {
      this._error = err.message || fallback;
    }
    this._busy = false;
    this._render();
  }

  async _saveSelection(changes) {
    const next = {
      selection: this._state.selection,
      references: this._state.references || [],
      mode: this._state.mode || "standard",
      ...changes,
    };
    next.references = next.references.filter((id) => next.selection.includes(id));
    this._error = "";
    this._state = { ...this._state, ...next };
    this._render();
    try {
      await this._hass.connection.sendMessagePromise({
        type: `${DOMAIN}/set_selection`,
        members: next.selection,
        references: next.references,
        mode: next.mode,
      });
    } catch (err) {
      this._error = err.message || t("selection_failed");
      this._render();
    }
  }

  _togglePick(id, checked) {
    const selected = new Set(this._state.selection);
    if (checked) selected.add(id);
    else selected.delete(id);
    this._saveSelection({ selection: [...selected] });
  }

  _toggleReference(id, checked) {
    // Eine Referenz misst immer mit. Wird sie abgewählt, fällt sie ganz aus
    // der Auswahl, damit sie nicht versehentlich neu kalibriert wird.
    const references = new Set(this._state.references || []);
    const selected = new Set(this._state.selection);
    if (checked) {
      references.add(id);
      selected.add(id);
    } else {
      references.delete(id);
      selected.delete(id);
    }
    this._saveSelection({ selection: [...selected], references: [...references] });
  }

  _askOrRun(action, service) {
    if (this._confirm === action) {
      this._call(service);
      return;
    }
    this._confirm = action;
    this._render();
  }

  _start() {
    if ((this._state.selection || []).length < 2) {
      this._error = t("min_two");
      this._render();
      return;
    }
    this._call("start");
  }

  _bind() {
    const root = this.shadowRoot;
    root.querySelectorAll("[data-action]").forEach((element) => {
      element.addEventListener("click", () => {
        const { action, quantity, member, mode } = element.dataset;
        if (action === "quantity") {
          this._quantity = quantity;
          this._render();
        } else if (action === "help") {
          this._help = !this._help;
          this._render();
        } else if (action === "mode") this._saveSelection({ mode });
        else if (action === "start") this._start();
        else if (action === "cancel") this._askOrRun("cancel", "cancel");
        else if (action === "rollback") this._askOrRun("rollback", "rollback");
        else if (action === "dismiss") this._call("dismiss");
        else if (action === "show-last") {
          this._showLast = true;
          this._error = "";
          this._render();
        } else if (action === "back") {
          this._showLast = false;
          this._confirm = null;
          this._error = "";
          this._render();
        } else if (action === "restore") {
          if (this._confirm !== "restore") {
            this._confirm = "restore";
            this._render();
            return;
          }
          const members = this._state.candidates
            .filter((item) => item.offset_state)
            .map((item) => item.id);
          this._send({ type: `${DOMAIN}/restore_offsets`, members }, t("restore_failed"));
        } else if (action === "adopt") {
          const key = `adopt:${member}:${quantity}`;
          if (this._confirm !== key) {
            this._confirm = key;
            this._render();
            return;
          }
          this._send({ type: `${DOMAIN}/adopt_offset`, member, quantity }, t("adopt_failed"));
        }
      });
    });
    root.querySelectorAll("input[data-reference]").forEach((element) => {
      element.addEventListener("change", () =>
        this._toggleReference(element.dataset.reference, element.checked),
      );
    });
    root.querySelectorAll("input[data-pick]").forEach((element) => {
      element.addEventListener("change", () =>
        this._togglePick(element.dataset.pick, element.checked),
      );
    });
    root.querySelectorAll("details[data-group]").forEach((element) => {
      element.addEventListener("toggle", () => {
        this._openGroups[element.dataset.group] = element.open;
      });
    });
  }

  _header(badge, color) {
    const label = t("help_button");
    return `<header>
      <span class="mark"><ha-icon icon="mdi:tune-vertical"></ha-icon></span>
      <h2>${escapeHtml(this._config?.title || t("title"))}</h2>
      <span class="badge" style="--badge: ${color}">${escapeHtml(badge)}</span>
      <button class="help" data-action="help" title="${escapeHtml(label)}" aria-label="${escapeHtml(label)}"><ha-icon icon="${this._help ? "mdi:close" : "mdi:help-circle-outline"}"></ha-icon></button>
    </header>`;
  }

  _helpView() {
    const sections = t("help")
      .map((section, index) => {
        const open = this._openGroups[`help${index}`] ?? Boolean(section.open);
        return `<details data-group="help${index}" ${open ? "open" : ""}>
        <summary>${escapeHtml(section.title)}</summary>
        <dl>${section.items
          .map(([term, text]) => `<dt>${escapeHtml(term)}</dt><dd>${escapeHtml(text)}</dd>`)
          .join("")}</dl>
      </details>`;
      })
      .join("");
    return `${this._header(t("badges.help"), "var(--primary-color)")}
      <p class="sub" style="margin-top: 12px">${escapeHtml(t("help_intro"))}</p>
      ${sections}
      <footer><button class="primary" data-action="help">${escapeHtml(t("back"))}</button></footer>`;
  }

  _notes(items) {
    if (!items?.length) return "";
    return `<ul class="notes">${items
      .map((item) => {
        const info = typeof item === "object" && item.level === "info";
        return `<li class="${info ? "info" : ""}"><ha-icon icon="${info ? "mdi:information-outline" : "mdi:alert-outline"}"></ha-icon><span>${escapeHtml(noteText(item))}</span></li>`;
      })
      .join("")}</ul>`;
  }

  _errorLine() {
    return this._error ? `<p class="error">${escapeHtml(this._error)}</p>` : "";
  }

  _tabs(keys) {
    if (!keys.includes(this._quantity)) this._quantity = keys[0];
    if (keys.length < 2) return "";
    return `<div class="tabs">${keys
      .map(
        (key) =>
          `<button class="${key === this._quantity ? "on" : ""}" style="--q: ${QUANTITIES[key].color}" data-action="quantity" data-quantity="${key}" title="${escapeHtml(qLabel(key))}"><ha-icon icon="${QUANTITIES[key].icon}"></ha-icon><span>${escapeHtml(t(`q_short.${key}`))}</span></button>`,
      )
      .join("")}</div>`;
  }

  _pick(item, selected, references) {
    const areaText = item.area ? `<small> · ${escapeHtml(item.area)}</small>` : "";
    const low =
      item.battery !== null && item.battery <= 15
        ? `<span class="low">${escapeHtml(t("battery", { level: number(item.battery, 0) }))}</span>`
        : "";
    let when = "";
    if (item.correctable.length) {
      const text = item.last_calibrated
        ? t("calibrated_at", { date: fullDate(item.last_calibrated) })
        : t("not_calibrated");
      const offsets =
        item.offset_state === "missing"
          ? ` · <span class="warn-text">${escapeHtml(t("offsets_missing"))}</span>`
          : item.offset_state === "differs"
            ? ` · <span class="warn-text">${escapeHtml(t("offsets_changed"))}</span>`
            : "";
      when = `<span class="when">${escapeHtml(text)}${offsets}</span>`;
    }
    let tag = item.new
      ? `<span class="tag" style="--tag: var(--primary-color)">${escapeHtml(t("tag_new"))}</span>`
      : "";
    if (references.has(item.id)) {
      tag += `<span class="tag" style="--tag: var(--success-color)">${escapeHtml(t("tag_reference"))}</span>`;
    }
    const icons = `<span class="qi" title="${escapeHtml(
      item.quantities.map((key) => qLabel(key)).join(", "),
    )}">${item.quantities
      .map(
        (key) =>
          `<ha-icon style="--q: ${QUANTITIES[key].color}" icon="${QUANTITIES[key].icon}"></ha-icon>`,
      )
      .join("")}</span>`;
    return `<label class="pick">
      <input type="checkbox" data-pick="${escapeHtml(item.id)}" ${selected.has(item.id) ? "checked" : ""}>
      <span class="text"><span class="line">${escapeHtml(item.name)}${tag}${areaText}</span>${when}</span>${low}${icons}
    </label>`;
  }

  _idle(state) {
    const selected = new Set(state.selection);
    const references = new Set(state.references || []);
    const referenceCandidates = state.candidates.filter(
      (item) => item.last_calibrated || references.has(item.id),
    );
    const groups = GROUPS.map((group) => {
      const items = state.candidates.filter((item) => item.group === group.key);
      if (!items.length) return "";
      const [title, hint] = t(`groups.${group.key}`);
      const count = items.filter((item) => selected.has(item.id)).length;
      const open = this._openGroups[group.key] ?? group.open;
      return `<details data-group="${group.key}" ${open ? "open" : ""}>
        <summary><ha-icon icon="${group.icon}"></ha-icon>${escapeHtml(title)}<span>${escapeHtml(t("of", { a: count, b: items.length }))}</span></summary>
        ${hint ? `<p class="hint">${escapeHtml(hint)}</p>` : ""}
        ${items.map((item) => this._pick(item, selected, references)).join("")}
      </details>`;
    }).join("");
    const mode = ["standard", "quick"].includes(state.mode) ? state.mode : "standard";
    const duration = state.durations?.[mode];
    const durationText = duration
      ? t("duration", { min: hours(duration.min_hours), max: hours(duration.max_hours) })
      : t("duration_unknown");
    const modes = `<div class="segment">${["standard", "quick"]
      .map((key) => {
        const [label] = t(`modes.${key}`);
        const from = state.durations?.[key]
          ? `, ${t("from_hours", { h: hours(state.durations[key].min_hours) })}`
          : "";
        return `<button class="${key === mode ? "on" : ""}" data-action="mode" data-mode="${key}"><ha-icon icon="${key === "quick" ? "mdi:lightning-bolt-outline" : "mdi:timer-sand"}"></ha-icon>${escapeHtml(label + from)}</button>`;
      })
      .join("")}</div><p class="hint">${escapeHtml(t(`modes.${mode}`)[1])}</p>`;
    const referenceOpen = this._openGroups.reference ?? references.size > 0;
    const referenceList = referenceCandidates.length
      ? referenceCandidates
          .map(
            (item) => `<label class="pick">
              <input type="checkbox" data-reference="${escapeHtml(item.id)}" ${references.has(item.id) ? "checked" : ""}>
              <span class="text"><span class="line">${escapeHtml(item.name)}</span>${
                item.last_calibrated
                  ? `<span class="when">${escapeHtml(t("calibrated_at", { date: fullDate(item.last_calibrated) }))}</span>`
                  : item.correctable.length
                    ? `<span class="when warn-text">${escapeHtml(t("not_calibrated"))}</span>`
                    : ""
              }</span>
            </label>`,
          )
          .join("")
      : `<p class="hint">${escapeHtml(t("ref_empty"))}</p>`;
    const referenceBlock = `<details data-group="reference" ${referenceOpen ? "open" : ""}>
        <summary><ha-icon icon="mdi:target"></ha-icon>${escapeHtml(t("ref_title"))}<span>${escapeHtml(references.size ? t("ref_count", { n: references.size }) : t("ref_none"))}</span></summary>
        <p class="hint">${escapeHtml(t("ref_hint"))}</p>
        ${referenceList}
      </details>`;
    const flagged = state.candidates.filter((item) => item.offset_state);
    const restoreConfirm = this._confirm === "restore";
    const restore = flagged.length
      ? `<div class="box">
          <p><b>${escapeHtml(t("restore_title"))}</b> ${flagged
            .map(
              (item) =>
                `${escapeHtml(item.name)} (${escapeHtml(item.offset_state === "missing" ? t("restore_missing") : t("restore_changed"))})`,
            )
            .join(", ")}. ${escapeHtml(t("restore_text"))}</p>
          <button class="${restoreConfirm ? "danger" : ""}" data-action="restore">${escapeHtml(restoreConfirm ? t("restore_confirm") : t("restore_button"))}</button>
        </div>`
      : "";
    const bridge = state.bridge_ready ? "" : `<p class="error">${escapeHtml(t("z2m_missing"))}</p>`;
    const lastButton = state.last?.result
      ? `<button class="with-icon" data-action="show-last" title="${escapeHtml(t("result_button_title"))}"><ha-icon icon="mdi:history"></ha-icon>${escapeHtml(t("result_button"))}</button>`
      : "";
    return `${this._header(t("badges.idle"), "var(--success-color)")}
      <p class="lead">${escapeHtml(t("idle_lead"))}</p>
      <p class="sub">${escapeHtml(t("idle_sub", { duration: durationText }))}</p>
      ${modes}
      ${bridge}
      ${restore}
      ${groups}
      ${referenceBlock}
      ${this._errorLine()}
      <footer>
        <span class="info full">${escapeHtml(t("selected", { n: selected.size, refs: references.size }))}</span>
        ${lastButton}
        <button class="primary" data-action="start"><ha-icon icon="mdi:play"></ha-icon>${escapeHtml(t("start"))}</button>
      </footer>`;
  }

  _progress(state) {
    return `<div class="stepper">${t("steps")
      .map((title, index) => {
        const step = index + 1;
        const kind = step < state.step ? "done" : step === state.step ? "now" : "";
        const icon = step < state.step ? "mdi:check" : STEP_ICONS[index];
        return `<div class="s ${kind}"><span class="c"><ha-icon icon="${icon}"></ha-icon></span>${escapeHtml(title)}</div>`;
      })
      .join("")}</div>`;
  }

  _bars(rows, key) {
    const unit = QUANTITIES[key].unit;
    const values = rows
      .map((row) => ({ row, data: row.quantities[key] }))
      .filter(({ row, data }) => data && row.active)
      .sort((a, b) => (b.data.deviation ?? -99) - (a.data.deviation ?? -99));
    const limit = Math.max(
      QUANTITIES[key].scale,
      ...values.map(({ data }) => Math.abs(data.deviation ?? 0)),
    );
    const anyValue = values.some(
      ({ data }) => data.deviation !== null && data.deviation !== undefined,
    );
    const references = values.filter(({ row }) => row.reference);
    const line = ({ row, data }) => {
      const name = `<span class="name" title="${escapeHtml(row.name)}">${escapeHtml(row.name)}</span>`;
      if (row.silent_minutes) {
        return `${name}<div class="track"></div><span class="value silent" title="${escapeHtml(t("silent_title", { n: row.silent_minutes }))}">${escapeHtml(t("silent_short", { n: row.silent_minutes }))}</span>`;
      }
      if (row.reference && references.length === 1) {
        return `${name}<div class="track"></div><span class="value muted">${escapeHtml(t("anchor"))}</span>`;
      }
      if (data.deviation === null || data.deviation === undefined) {
        return `${name}<div class="track"></div><span class="value muted" title="${escapeHtml(t("no_value"))}">–</span>`;
      }
      const width = (Math.abs(data.deviation) / limit) * 50;
      const side =
        data.deviation >= 0
          ? `left: 50%; width: ${width}%; border-radius: 0 3px 3px 0;`
          : `right: 50%; width: ${width}%; border-radius: 3px 0 0 3px;`;
      const kind = row.reference ? "ref" : row.unstable ? "warn" : "";
      return `${name}<div class="track"><div class="bar ${kind}" style="${side}"></div></div>
        <span class="value">${signed(data.deviation)} ${unit}</span>`;
    };
    const measured = values.filter(({ row }) => !row.reference);
    const waiting = anyValue ? "" : `<p class="hint">${escapeHtml(t("first_values"))}</p>`;
    const refBlock = references.length
      ? `<p class="label sublabel">${escapeHtml(references.length === 1 ? t("refs_one") : t("refs_many"))}</p>
        <div class="bars">${references.map(line).join("")}</div>`
      : "";
    return `${waiting}<div class="bars">${measured.map(line).join("")}</div>${refBlock}`;
  }

  _running(state) {
    const keys = Object.keys(QUANTITIES).filter((key) =>
      state.sensors.some((row) => row.active && row.quantities[key]),
    );
    const tabs = this._tabs(keys);
    const key = this._quantity;
    const spread = state.spread?.[key];
    const count = state.sensors.filter((row) => row.active).length;
    const eta = remaining(state.eta);
    const refCount = state.sensors.filter((row) => row.active && row.reference).length;
    const label = !refCount ? t("dev_group") : refCount === 1 ? t("dev_ref") : t("dev_refs");
    const info =
      spread === null || spread === undefined
        ? t("sensors", { n: count })
        : t("sensors_spread", {
            n: count,
            spread: `${number(spread)}\u00a0${QUANTITIES[key].unit}`,
            refs: refCount,
          });
    const cancel = this._confirm === "cancel";
    const message = messageText(state.message);
    return `${this._header(t("badges.running"), "var(--primary-color)")}
      <p class="lead">${escapeHtml(t("steps")[state.step - 1])}${state.mode === "quick" ? escapeHtml(t("quick_suffix")) : ""}</p>
      <p class="sub">${escapeHtml(message)}${eta ? ` ${escapeHtml(eta[0].toUpperCase() + eta.slice(1))}.` : ""}</p>
      ${this._progress(state)}
      ${tabs}
      <p class="label">${escapeHtml(label)}</p>
      ${this._bars(state.sensors, key)}
      ${this._notes(state.warnings)}
      ${this._errorLine()}
      <footer>
        <span class="info">${escapeHtml(info)}</span>
        <button class="${cancel ? "danger" : ""}" data-action="cancel">${escapeHtml(cancel ? t("cancel_confirm") : t("cancel"))}</button>
      </footer>`;
  }

  _spread(data, key) {
    const meta = QUANTITIES[key];
    const unit = escapeHtml(meta.unit);
    const items = Object.values(data.sensors).filter(
      (item) => item.deviation !== null && item.deviation !== undefined,
    );
    if (!items.length) return "";
    const counted = items.filter(
      (item) => ["ok", "reference"].includes(item.status) || item.applied,
    );
    const before = counted.map((item) => item.deviation);
    let after = counted
      .map((item) => item.after)
      .filter((value) => value !== null && value !== undefined);
    if (!after.length && data.spread_after !== null && data.spread_after !== undefined) {
      // Läufe vor 1.1.0 haben nur die Streuung nachher, keine Werte je Sensor.
      after = [-data.spread_after / 2, data.spread_after / 2];
    }
    const limit = Math.max(
      meta.scale / 2,
      ...counted.flatMap((item) => [Math.abs(item.deviation), Math.abs(item.after ?? 0)]),
    );
    const pos = (value) => Math.min(99, Math.max(1, 50 + (value / limit) * 48));
    const band = (values, cls) => {
      if (!values.length) return "";
      const left = pos(Math.min(...values));
      const right = pos(Math.max(...values));
      return `<i class="${cls}" style="left: ${left}%; width: ${Math.max(right - left, 0.5)}%"></i>`;
    };
    // Mit Referenz zählt der größte Abstand zur Referenz, sonst die Streuung.
    const withReference = (data.references || []).length > 0 && "max_after" in data;
    const was = withReference ? data.max_before : data.spread_before;
    const now = withReference ? data.max_after : data.spread_after;
    const has = (value) => value !== null && value !== undefined;
    const big = has(now)
      ? `${number(now)}<small>${unit}</small>`
      : has(was)
        ? `${number(was)}<small>${unit}</small>`
        : "–";
    let tolerancePart = "";
    if (Array.isArray(data.outside) && data.checked !== undefined) {
      if (data.outside.length) {
        tolerancePart = `<br><span class="warn-text">${escapeHtml(t("some_outside", { n: data.outside.length, t: tolerance(key) }))}</span>`;
      } else if (data.checked) {
        tolerancePart = `<br>${escapeHtml(t("all_within", { t: tolerance(key) }))}`;
      }
    }
    const what = has(now)
      ? `<b>${escapeHtml(withReference ? t("hero_max") : t("hero_spread"))}</b><br>${escapeHtml(
          has(was) ? t("before_value", { v: `${number(was)}\u00a0${meta.unit}` }) : "",
        )}${tolerancePart}`
      : `<b>${escapeHtml(withReference ? t("hero_max_before") : t("hero_spread_before"))}</b><br>${escapeHtml(t("not_measured"))}`;
    const edge = number(limit, limit < 1 ? 2 : 1);
    return `<div class="hero" style="--q: ${meta.color}">
        <div class="big">${big}</div><div class="what">${what}</div>
      </div>
      <div class="span" style="--q: ${meta.color}" title="${escapeHtml(t("span_title"))}">
        <i class="base"></i><i class="zero"></i>${band(before, "before")}${band(after, "after")}
      </div>
      <div class="span-legend"><span>−${edge}</span><span>0</span><span>+${edge}</span></div>`;
  }

  _rows(data, names, key, canAdopt) {
    const meta = QUANTITIES[key];
    const unit = meta.unit;
    const rows = Object.entries(data.sensors).sort(
      ([, a], [, b]) => (b.deviation ?? -99) - (a.deviation ?? -99),
    );
    const values = rows
      .filter(([, item]) => item.status !== "outlier" || item.applied)
      .flatMap(([, item]) => [Math.abs(item.deviation ?? 0), Math.abs(item.after ?? 0)]);
    const limit = Math.max(meta.scale / 2, ...values);
    const pos = (value) => Math.min(97, Math.max(3, 50 + (value / limit) * 46));
    const clip = (value) =>
      Math.abs(value) > limit * 1.04 ? ` clip ${value > 0 ? "right" : "left"}` : "";
    const zone = (meta.tolerance / limit) * 46;
    const hasAfter = rows.some(([, item]) => item.after !== null && item.after !== undefined);
    const outside = new Set(data.outside || []);
    const lines = rows
      .map(([id, item]) => {
        const name = names[id] || id;
        let status = item.status;
        if (item.manual) status = "manual";
        else if (item.applied) status = "ok";
        else if (item.status === "ok") status = "failed";
        const label = t(`status.${status}`);
        let [icon, color] = STATUS_ICONS[status] || STATUS_ICONS.no_data;
        if (outside.has(id)) [icon, color] = ["mdi:alert-circle-outline", "var(--warning-color)"];
        let detail = label;
        if (item.applied) {
          detail = t("offset_change", {
            a: signed(item.old_offset ?? 0),
            b: `${signed(item.new_offset ?? 0)}\u00a0${unit}`,
          });
        } else if (item.deviation !== null && item.deviation !== undefined && item.status !== "reference") {
          detail = t("was_off", { label, v: `${signed(item.deviation)}\u00a0${unit}` });
        }
        let adopt = "";
        if (canAdopt && item.status === "outlier" && !item.applied) {
          const confirm = this._confirm === `adopt:${id}:${key}`;
          const value = `${signed(item.new_offset)}\u00a0${unit}`;
          adopt = `<button class="${confirm ? "danger" : ""}" data-action="adopt" data-member="${escapeHtml(id)}" data-quantity="${key}">${escapeHtml(
            confirm ? t("adopt_confirm", { v: value }) : t("adopt", { v: value }),
          )}</button>`;
        }
        let track = `<div class="mini"></div>`;
        if (item.deviation !== null && item.deviation !== undefined) {
          const before = pos(item.deviation);
          const after = item.after !== null && item.after !== undefined ? pos(item.after) : null;
          const link =
            after === null
              ? ""
              : `<i class="link" style="left: ${Math.min(before, after)}%; width: ${Math.abs(before - after)}%"></i>`;
          const title = t("track_title", {
            a: `${signed(item.deviation)}\u00a0${unit}`,
            b: after === null ? "" : `${signed(item.after)}\u00a0${unit}`,
          });
          track = `<div class="mini" title="${escapeHtml(title)}"><i class="zone" style="left: ${50 - zone}%; width: ${2 * zone}%"></i><i class="zero"></i>${link}<i class="dot before${after === null ? clip(item.deviation) : ""}" style="left: ${before}%"></i>${
            after === null ? "" : `<i class="dot after${clip(item.after)}" style="left: ${after}%"></i>`
          }</div>`;
        }
        return `<div class="row">
          <ha-icon icon="${icon}" style="color: ${color}" title="${escapeHtml(label)}"></ha-icon>
          <div class="who"><b title="${escapeHtml(name)}">${escapeHtml(name)}</b><span>${escapeHtml(detail)}</span>${adopt}</div>
          ${track}
        </div>`;
      })
      .join("");
    const edge = number(limit, limit < 1 ? 2 : 1);
    const legend = `<div class="legend"><span><i class="dot before"></i>${escapeHtml(t("legend_before"))}</span>${
      hasAfter ? `<span><i class="dot after"></i>${escapeHtml(t("legend_after"))}</span>` : ""
    }<span><i class="zonekey"></i>${escapeHtml(t("legend_tolerance", { t: tolerance(key) }))}</span></div>`;
    const older = hasAfter || "checked" in data ? "" : `<p class="older">${escapeHtml(t("older"))}</p>`;
    return `${legend}${older}<div class="list" style="--q: ${meta.color}">${lines}
      <div class="scale"><div><span>−${edge}</span><span>0</span><span>+${edge}</span></div></div></div>`;
  }

  _finished(state, reopened = false) {
    const last = state.last;
    const result = last.result || {};
    const keys = Object.keys(QUANTITIES).filter((key) => result[key]);
    const colors = {
      done: "var(--success-color)",
      failed: "var(--error-color)",
      cancelled: "var(--warning-color)",
    };
    const tabs = keys.length ? this._tabs(keys) : "";
    const data = result[this._quantity];
    const details = data
      ? `${this._spread(data, this._quantity)}${this._rows(data, last.names, this._quantity, state.can_adopt)}`
      : "";
    const confirm = this._confirm === "rollback";
    const undo = state.can_rollback
      ? `<button class="${confirm ? "danger" : ""}" data-action="rollback">${escapeHtml(confirm ? t("undo_confirm") : t("undo"))}</button>`
      : "";
    const close = reopened
      ? `<button class="primary" data-action="back">${escapeHtml(t("back"))}</button>`
      : `<button class="primary" data-action="dismiss">${escapeHtml(t("close"))}</button>`;
    const badge = reopened ? t("badges.result") : t(`badges.${last.outcome}`);
    return `${this._header(badge, colors[last.outcome])}
      <p class="lead">${escapeHtml(finishText(last))}</p>
      <p class="sub">${last.mode === "quick" ? escapeHtml(t("quick_run")) : ""}${escapeHtml(t("time_range", { a: clock(last.started_at), b: clock(last.finished_at) }))}</p>
      ${tabs}
      ${details}
      ${this._notes(last.warnings)}
      ${this._errorLine()}
      <footer>
        ${undo}
        ${close}
      </footer>`;
  }

  _render() {
    const root = this.shadowRoot;
    const state = this._state;
    let body;
    if (this._help) {
      body = this._helpView();
    } else if (!state) {
      body = `${this._header(t("badges.loading"), "var(--secondary-text-color)")}<p class="sub">${escapeHtml(t("connecting"))}</p>`;
    } else if (state.phase === "not_loaded") {
      body = `${this._header(t("badges.inactive"), "var(--warning-color)")}
        <p class="lead">${escapeHtml(t("not_loaded_lead"))}</p>
        <p class="sub">${escapeHtml(t("not_loaded_sub"))}</p>`;
    } else if (state.step) {
      body = this._running(state);
    } else if (state.phase === "idle" && this._showLast && state.last?.result) {
      body = this._finished(state, true);
    } else if (state.phase === "idle") {
      this._showLast = false;
      body = this._idle(state);
    } else {
      body = this._finished(state);
    }
    root.innerHTML = `<style>${STYLES}</style><ha-card>${body}</ha-card>`;
    this._bind();
  }
}

customElements.define("sensor-kalibrierung-card", SensorKalibrierungCard);
window.customCards = window.customCards || [];
window.customCards.push({
  type: "sensor-kalibrierung-card",
  name: "Zigbee2MQTT Sensor Calibration",
  description: "Calibrates Zigbee2MQTT sensors placed side by side. / Kalibriert nebeneinanderliegende Zigbee2MQTT-Sensoren.",
});
