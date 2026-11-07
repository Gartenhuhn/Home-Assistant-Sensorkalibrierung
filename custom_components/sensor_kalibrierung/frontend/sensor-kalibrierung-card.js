const DOMAIN = "sensor_kalibrierung";
const STEPS = ["Prüfen", "Angleichen", "Messen", "Korrigieren", "Kontrolle"];
const STEP_ICONS = [
  "mdi:access-point-check",
  "mdi:sine-wave",
  "mdi:chart-bell-curve-cumulative",
  "mdi:tune-variant",
  "mdi:check-decagram-outline",
];
const QUANTITIES = {
  temperature: {
    label: "Temperatur",
    unit: "°C",
    scale: 1,
    tolerance: 0.25,
    icon: "mdi:thermometer",
    color: "#f08a3c",
  },
  humidity: {
    label: "Feuchte",
    unit: "%",
    scale: 4,
    tolerance: 1,
    icon: "mdi:water-percent",
    color: "#2f9be0",
  },
  pressure: {
    label: "Druck",
    unit: "hPa",
    scale: 1,
    tolerance: 0.3,
    icon: "mdi:gauge",
    color: "#8f78e8",
  },
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
  { key: "full", title: "Temperatur und Feuchte", hint: "", open: true, icon: "mdi:thermometer-water" },
  {
    key: "temperature",
    title: "Weitere Sensoren, nur Temperatur",
    icon: "mdi:thermometer",
    hint: "Anhaken, wenn der Sensor mit dazugelegt wird.",
    open: true,
  },
  {
    key: "compare",
    title: "Nur Vergleich, keine Korrektur",
    icon: "mdi:eye-outline",
    hint: "Werden mitgemessen, aber nicht verändert.",
    open: false,
  },
];
const STATUS = {
  ok: "Korrigiert",
  reference: "Referenz",
  compare: "Nur Vergleich",
  outlier: "Zu große Abweichung",
  unstable: "Noch nicht stabil",
  no_data: "Zu wenige Daten",
};
const MODES = {
  standard: {
    label: "Normal",
    hint: "Für alle Sensoren, auch Hue-Bewegungsmelder und Rauchmelder.",
  },
  quick: {
    label: "Schnell",
    hint: "Für Sensoren, die sich schnell angleichen, etwa Aqara. Etwas ungenauer, Hue-Bewegungsmelder und Rauchmelder brauchen oft länger.",
  },
};
const HELP = [
  {
    title: "So geht's",
    open: true,
    items: [
      ["1. Anhaken", "Alle Sensoren anhaken, die mitmachen. Nicht angehakte bleiben unverändert."],
      ["2. Zusammenlegen", "Alle angehakten Sensoren dicht nebeneinander an einen ruhigen Platz legen, ohne Sonne, Zugluft oder Heizung. Guter Zigbee-Empfang ist wichtig."],
      ["3. Art wählen", "Normal passt immer. Schnell reicht für Aqara und ähnliche Sensoren."],
      ["4. Referenz, optional", "Für neue Sensoren zwei oder drei bereits kalibrierte dazulegen und unter Referenz anhaken. Ohne Referenz zählt der Mittelwert der Gruppe."],
      ["5. Starten und warten", "Ab jetzt läuft alles allein. Sensoren nicht bewegen. Ein Neustart von Home Assistant schadet nicht."],
      ["6. Zurückbringen", "Wenn die Kachel „Fertig“ zeigt und die Nachricht kommt, die Sensoren an ihre Plätze bringen."],
    ],
  },
  {
    title: "Anzeigen in der Kachel",
    items: [
      ["Neu", "Seit höchstens 14 Tagen in Home Assistant und noch nie kalibriert."],
      ["Offsets fehlen", "Zigbee2MQTT kennt die gespeicherten Offsets nicht mehr, meist nach Entfernen und neu Anlernen. Mit „Gespeicherte Offsets zurückschreiben“ beheben, eine neue Messung ist nicht nötig."],
      ["Offsets geändert", "Die Offsets wurden außerhalb der Kalibrierung geändert, etwa von Hand in Zigbee2MQTT. Zurückschreiben nur, wenn das nicht Absicht war."],
      ["Blauer Balken", "Abweichung des Sensors vom Mittel oder von der Referenz. Blau heißt stabil."],
      ["Oranger Balken", "Der Abstand ändert sich noch. Der Sensor gleicht sich noch an die Umgebung an, das ist am Anfang normal."],
      ["wartet", "Der Sensor hat noch zu wenige Werte geschickt."],
      ["still … Min.", "Der Sensor meldet sich nicht mehr. Die Kalibrierung wartet auf ihn. Kurz die Taste am Sensor drücken oder näher an einen Router legen."],
      ["◆", "Referenzsensor, wird nicht verändert."],
      ["Streuung", "Abstand zwischen dem höchsten und dem niedrigsten Sensor. Nach der Kalibrierung soll sie klein sein."],
      ["Grafik im Ergebnis", "Ring: Abweichung vorher. Punkt: Abweichung nachher. Je näher der Punkt an der 0, desto besser."],
    ],
  },
  {
    title: "Status im Ergebnis",
    items: [
      ["Korrigiert", "Der neue Offset ist geschrieben. Angezeigt wird alter → neuer Offset."],
      ["Von Hand übernommen", "Ein Ausreißer, dessen Offset du mit „Trotzdem übernehmen“ gesetzt hast."],
      ["Referenz", "Messlatte für die anderen, bleibt unverändert."],
      ["Nur Vergleich", "Lässt sich nicht über Zigbee2MQTT korrigieren, wird nur angezeigt."],
      ["Zu große Abweichung", "Die Korrektur wäre größer als die Grenze in den Optionen. Erst prüfen, ob der Sensor wirklich richtig lag. Dann „Trotzdem übernehmen“ oder liegen lassen."],
      ["Noch nicht stabil", "Der Wert hat sich während der Messung verschoben. Nicht korrigiert. Später noch einmal kalibrieren."],
      ["Zu wenige Daten", "Der Sensor hat zu selten gemeldet. Nicht korrigiert. Verbindung prüfen und wiederholen."],
      ["Nicht geschrieben", "Zigbee2MQTT hat den neuen Offset nicht bestätigt."],
    ],
  },
  {
    title: "Hinweise und was zu tun ist",
    items: [
      ["Batterie … %, die Werte können driften", "Schwache Batterien verfälschen die Messung. Am besten vorher tauschen."],
      ["Zigbee2MQTT reagiert nicht, der Sensor wird nur verglichen", "Der Sensor war beim Start nicht erreichbar. Er bekommt keinen Offset."],
      ["keine Meldung erhalten, Sensor ausgelassen", "Der Sensor hat sich in den ersten 2 Stunden nicht gemeldet und macht nicht mit."],
      ["seit über 90 Minuten keine Meldung", "Kommt auch als Nachricht. Taste am Sensor kurz drücken. Hilft das nicht, neu verbinden, ohne ihn in Zigbee2MQTT zu entfernen."],
      ["Noch nicht stabil nach maximaler Wartezeit", "Die Messung beginnt trotzdem. Bei diesen Sensoren das Ergebnis genau ansehen."],
      ["hat beim Messen zu selten gemeldet", "Mehr als 2 Stunden ohne Meldung. Der Sensor wird nicht korrigiert."],
      ["driftet noch, nicht korrigiert", "Siehe „Noch nicht stabil“."],
      ["weicht um … ab, nicht korrigiert", "Siehe „Zu große Abweichung“."],
      ["Offset konnte nicht geschrieben werden", "Zigbee2MQTT hat 12 Versuche nicht bestätigt. Zigbee2MQTT prüfen und neu kalibrieren."],
      ["Die Streuung ist nicht kleiner geworden", "Meist hat sich der Platz während der Kontrolle verändert, etwa durch Sonne oder Heizung. Werte prüfen, sonst „Rückgängig“."],
      ["Es melden sich zu wenige Sensoren", "Weniger als zwei Sensoren haben gemeldet. Der Lauf ist abgebrochen, nichts wurde geändert."],
      ["Zigbee2MQTT ist noch nicht erreichbar", "Die Kachel wartet auf Zigbee2MQTT. Prüfen, ob die App läuft."],
    ],
  },
];
const hours = (value) => number(value, Number.isInteger(value) ? 0 : 1);
const BADGES = {
  idle: "Bereit",
  done: "Fertig",
  failed: "Fehler",
  cancelled: "Abgebrochen",
};

const escapeHtml = (value) =>
  String(value ?? "").replace(
    /[&<>"']/g,
    (char) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        char
      ],
  );

const number = (value, digits = 2) =>
  Number(value).toLocaleString("de-DE", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });

const signed = (value, digits = 2) => {
  const text = number(Math.abs(value), digits);
  if (Number(value.toFixed(digits)) === 0) return text;
  return `${value > 0 ? "+" : "−"}${text}`;
};

const remaining = (timestamp) => {
  if (!timestamp) return "";
  const minutes = Math.round((timestamp * 1000 - Date.now()) / 60000);
  if (minutes <= 2) return "gleich";
  if (minutes < 60) return `noch etwa ${minutes} Minuten`;
  const hours = minutes / 60;
  if (hours < 1.5) return "noch etwa 1 Stunde";
  return `noch etwa ${Math.round(hours)} Stunden`;
};

const clock = (timestamp) =>
  new Date(timestamp * 1000).toLocaleString("de-DE", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });

const fullDate = (timestamp) =>
  new Date(timestamp * 1000).toLocaleString("de-DE", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });

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
    if (first || !this._unsubscribe) this._subscribe();
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
      this._error = err.message || "Die Aktion ist fehlgeschlagen.";
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
      this._error = err.message || "Die Auswahl wurde nicht gespeichert.";
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
    const references = new Set(this._state.references || []);
    if (checked) references.add(id);
    else references.delete(id);
    this._saveSelection({ references: [...references] });
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
      this._error = "Wähle mindestens zwei Sensoren aus.";
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
          this._send(
            { type: `${DOMAIN}/restore_offsets`, members },
            "Die Offsets wurden nicht geschrieben.",
          );
        } else if (action === "adopt") {
          const key = `adopt:${member}:${quantity}`;
          if (this._confirm !== key) {
            this._confirm = key;
            this._render();
            return;
          }
          this._send(
            { type: `${DOMAIN}/adopt_offset`, member, quantity },
            "Der Offset wurde nicht übernommen.",
          );
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
    return `<header>
      <span class="mark"><ha-icon icon="mdi:tune-vertical"></ha-icon></span>
      <h2>${escapeHtml(this._config?.title || "Sensor-Kalibrierung")}</h2>
      <span class="badge" style="--badge: ${color}">${escapeHtml(badge)}</span>
      <button class="help" data-action="help" title="Anleitung und Meldungen" aria-label="Anleitung und Meldungen"><ha-icon icon="${this._help ? "mdi:close" : "mdi:help-circle-outline"}"></ha-icon></button>
    </header>`;
  }

  _helpView() {
    const sections = HELP.map((section, index) => {
      const open = this._openGroups[`help${index}`] ?? Boolean(section.open);
      return `<details data-group="help${index}" ${open ? "open" : ""}>
        <summary>${escapeHtml(section.title)}</summary>
        <dl>${section.items
          .map(([term, text]) => `<dt>${escapeHtml(term)}</dt><dd>${escapeHtml(text)}</dd>`)
          .join("")}</dl>
      </details>`;
    }).join("");
    return `${this._header("Anleitung", "var(--primary-color)")}
      <p class="sub" style="margin-top: 12px">Kurzanleitung und was die Anzeigen und Hinweise bedeuten.</p>
      ${sections}
      <footer><button class="primary" data-action="help">Zurück</button></footer>`;
  }

  _notes(items) {
    if (!items?.length) return "";
    return `<ul class="notes">${items
      .map(
        (item) =>
          `<li><ha-icon icon="mdi:alert-outline"></ha-icon><span>${escapeHtml(item)}</span></li>`,
      )
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
          `<button class="${key === this._quantity ? "on" : ""}" style="--q: ${QUANTITIES[key].color}" data-action="quantity" data-quantity="${key}"><ha-icon icon="${QUANTITIES[key].icon}"></ha-icon>${QUANTITIES[key].label}</button>`,
      )
      .join("")}</div>`;
  }

  _pick(item, selected) {
    const areaText = item.area
      ? `<small> · ${escapeHtml(item.area)}</small>`
      : "";
    const low =
      item.battery !== null && item.battery <= 15
        ? `<span class="low">Batterie ${number(item.battery, 0)} %</span>`
        : "";
    let when = "";
    if (item.correctable.length) {
      const text = item.last_calibrated
        ? `Kalibriert am ${fullDate(item.last_calibrated)}`
        : "Noch nicht kalibriert";
      const offsets =
        item.offset_state === "missing"
          ? ` · <span class="warn-text">Offsets fehlen</span>`
          : item.offset_state === "differs"
            ? ` · <span class="warn-text">Offsets geändert</span>`
            : "";
      when = `<span class="when">${escapeHtml(text)}${offsets}</span>`;
    }
    const tag = item.new
      ? `<span class="tag" style="--tag: var(--primary-color)">Neu</span>`
      : "";
    const icons = `<span class="qi" title="${escapeHtml(
      item.quantities.map((key) => QUANTITIES[key]?.label).join(", "),
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
    const chosen = state.candidates.filter((item) => selected.has(item.id));
    const groups = GROUPS.map((group) => {
      const items = state.candidates.filter((item) => item.group === group.key);
      if (!items.length) return "";
      const count = items.filter((item) => selected.has(item.id)).length;
      const open = this._openGroups[group.key] ?? group.open;
      return `<details data-group="${group.key}" ${open ? "open" : ""}>
        <summary><ha-icon icon="${group.icon}"></ha-icon>${escapeHtml(group.title)}<span>${count} von ${items.length}</span></summary>
        ${group.hint ? `<p class="hint">${escapeHtml(group.hint)}</p>` : ""}
        ${items.map((item) => this._pick(item, selected)).join("")}
      </details>`;
    }).join("");
    const mode = MODES[state.mode] ? state.mode : "standard";
    const duration = state.durations?.[mode];
    const durationText = duration
      ? `mindestens ${hours(duration.min_hours)} und höchstens etwa ${hours(duration.max_hours)} Stunden`
      : "einige Stunden";
    const modes = `<div class="segment">${Object.entries(MODES)
      .map(
        ([key, item]) =>
          `<button class="${key === mode ? "on" : ""}" data-action="mode" data-mode="${key}"><ha-icon icon="${key === "quick" ? "mdi:lightning-bolt-outline" : "mdi:timer-sand"}"></ha-icon>${item.label}${state.durations?.[key] ? `, ab ${hours(state.durations[key].min_hours)} h` : ""}</button>`,
      )
      .join("")}</div><p class="hint">${escapeHtml(MODES[mode].hint)}</p>`;
    const referenceOpen = this._openGroups.reference ?? references.size > 0;
    const referenceList = chosen.length
      ? chosen
          .map(
            (item) => `<label class="pick">
              <input type="checkbox" data-reference="${escapeHtml(item.id)}" ${references.has(item.id) ? "checked" : ""}>
              <span class="text"><span class="line">${escapeHtml(item.name)}</span>${
                item.last_calibrated
                  ? `<span class="when">Kalibriert am ${fullDate(item.last_calibrated)}</span>`
                  : item.correctable.length
                    ? `<span class="when warn-text">Noch nicht kalibriert</span>`
                    : ""
              }</span>
            </label>`,
          )
          .join("")
      : `<p class="hint">Zuerst oben Sensoren anhaken.</p>`;
    const referenceBlock = `<details data-group="reference" ${referenceOpen ? "open" : ""}>
        <summary><ha-icon icon="mdi:target"></ha-icon>Referenz, optional<span>${references.size ? `${references.size} gewählt` : "Mittelwert der Gruppe"}</span></summary>
        <p class="hint">Bereits kalibrierte Sensoren, die nicht verändert werden. Die anderen werden an deren Mittelwert angeglichen. Für neue Sensoren zwei oder drei kalibrierte dazulegen und hier anhaken.</p>
        ${referenceList}
      </details>`;
    const flagged = state.candidates.filter((item) => item.offset_state);
    const restoreConfirm = this._confirm === "restore";
    const restore = flagged.length
      ? `<div class="box">
          <p><b>Offsets passen nicht mehr:</b> ${flagged
            .map(
              (item) =>
                `${escapeHtml(item.name)} (${item.offset_state === "missing" ? "fehlen, Gerät wohl zurückgesetzt" : "von Hand geändert"})`,
            )
            .join(", ")}. Die gespeicherten Werte lassen sich zurückschreiben, ohne neu zu kalibrieren.</p>
          <button class="${restoreConfirm ? "danger" : ""}" data-action="restore">${restoreConfirm ? "Wirklich zurückschreiben?" : "Gespeicherte Offsets zurückschreiben"}</button>
        </div>`
      : "";
    const bridge = state.bridge_ready
      ? ""
      : `<p class="error">Zigbee2MQTT ist noch nicht erreichbar.</p>`;
    const lastButton = state.last?.result
      ? `<button class="with-icon" data-action="show-last" title="Letztes Ergebnis ansehen"><ha-icon icon="mdi:history"></ha-icon>Ergebnis</button>`
      : "";
    return `${this._header("Bereit", "var(--success-color)")}
      <p class="lead">Sensoren nebeneinanderlegen</p>
      <p class="sub">Alle angehakten Sensoren müssen am selben Platz liegen, ruhig und ohne Sonne, Zugluft oder Heizung. Nach dem Start läuft alles allein, ${durationText}.</p>
      ${modes}
      ${bridge}
      ${restore}
      ${groups}
      ${referenceBlock}
      ${this._errorLine()}
      <footer>
        <span class="info full">${selected.size} Sensoren ausgewählt${references.size ? `, davon ${references.size} als Referenz` : ""}</span>
        ${lastButton}
        <button class="primary" data-action="start"><ha-icon icon="mdi:play"></ha-icon>Starten</button>
      </footer>`;
  }

  _progress(state) {
    return `<div class="stepper">${STEPS.map((title, index) => {
      const step = index + 1;
      const kind = step < state.step ? "done" : step === state.step ? "now" : "";
      const icon = step < state.step ? "mdi:check" : STEP_ICONS[index];
      return `<div class="s ${kind}"><span class="c"><ha-icon icon="${icon}"></ha-icon></span>${title}</div>`;
    }).join("")}</div>`;
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
    return `<div class="bars">${values
      .map(({ row, data }) => {
        const name = `<span class="name" title="${escapeHtml(row.name)}">${row.reference ? "◆ " : ""}${escapeHtml(row.name)}</span>`;
        if (row.silent_minutes) {
          return `${name}<div class="track"></div><span class="value silent" title="Keine Meldung seit ${row.silent_minutes} Minuten">still ${row.silent_minutes} Min.</span>`;
        }
        if (data.deviation === null || data.deviation === undefined) {
          return `${name}<div class="track"></div><span class="value muted">wartet</span>`;
        }
        const width = (Math.abs(data.deviation) / limit) * 50;
        const side =
          data.deviation >= 0
            ? `left: 50%; width: ${width}%; border-radius: 0 3px 3px 0;`
            : `right: 50%; width: ${width}%; border-radius: 3px 0 0 3px;`;
        return `${name}<div class="track"><div class="bar ${row.unstable ? "warn" : ""}" style="${side}"></div></div>
          <span class="value">${signed(data.deviation)} ${unit}</span>`;
      })
      .join("")}</div>`;
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
    const info =
      spread === null || spread === undefined
        ? `${count} Sensoren`
        : `Streuung ${number(spread)} ${QUANTITIES[key].unit} · ${count} Sensoren`;
    const cancel = this._confirm === "cancel";
    return `${this._header("Läuft", "var(--primary-color)")}
      <p class="lead">${STEPS[state.step - 1]}${state.mode === "quick" ? ", schnell" : ""}</p>
      <p class="sub">${escapeHtml(state.message)}${eta ? ` ${escapeHtml(eta[0].toUpperCase() + eta.slice(1))}.` : ""}</p>
      ${this._progress(state)}
      ${tabs}
      <p class="label">Abweichung von der ${state.sensors.some((row) => row.reference) ? "Referenz (◆)" : "Gruppe"}</p>
      ${this._bars(state.sensors, key)}
      ${this._notes(state.warnings)}
      ${this._errorLine()}
      <footer>
        <span class="info">${info}</span>
        <button class="${cancel ? "danger" : ""}" data-action="cancel">${cancel ? "Wirklich abbrechen?" : "Abbrechen"}</button>
      </footer>`;
  }

  _spread(data, key) {
    const meta = QUANTITIES[key];
    const items = Object.values(data.sensors).filter(
      (item) => item.deviation !== null && item.deviation !== undefined,
    );
    if (!items.length) return "";
    const counted = items.filter((item) => ["ok", "reference"].includes(item.status) || item.applied);
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
    const { spread_before: was, spread_after: now } = data;
    const percent =
      was && now !== null && now !== undefined ? Math.round((1 - now / was) * 100) : null;
    const big =
      now !== null && now !== undefined
        ? `${number(now)}<small>${escapeHtml(data.unit)}</small>`
        : was !== null && was !== undefined
          ? `${number(was)}<small>${escapeHtml(data.unit)}</small>`
          : "–";
    const what =
      now !== null && now !== undefined
        ? `<b>Streuung nachher</b><br>vorher ${number(was)} ${escapeHtml(data.unit)}${percent !== null && percent > 0 ? `, ${percent} % kleiner` : ""}`
        : `<b>Streuung vorher</b><br>nachher nicht gemessen`;
    const edge = number(limit, limit < 1 ? 2 : 1);
    return `<div class="hero" style="--q: ${meta.color}">
        <div class="big">${big}</div><div class="what">${what}</div>
      </div>
      <div class="span" style="--q: ${meta.color}" title="Spannweite aller korrigierten Sensoren, gestrichelt vorher, gefüllt nachher">
        <i class="base"></i><i class="zero"></i>${band(before, "before")}${band(after, "after")}
      </div>
      <div class="span-legend"><span>−${edge}</span><span>0</span><span>+${edge}</span></div>`;
  }

  _rows(data, names, key, canAdopt) {
    const meta = QUANTITIES[key];
    const unit = data.unit;
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
    const lines = rows
      .map(([id, item]) => {
        const name = names[id] || id;
        let status = item.status;
        let label = STATUS[item.status];
        if (item.manual) [status, label] = ["manual", "Von Hand übernommen"];
        else if (item.applied) [status, label] = ["ok", "Korrigiert"];
        else if (item.status === "ok") [status, label] = ["failed", "Nicht geschrieben"];
        const [icon, color] = STATUS_ICONS[status] || STATUS_ICONS.no_data;
        let detail = label;
        if (item.applied) {
          detail = `Offset ${signed(item.old_offset ?? 0)} → ${signed(item.new_offset ?? 0)} ${unit}`;
        } else if (item.deviation !== null && item.deviation !== undefined && item.status !== "reference") {
          detail = `${label}, lag ${signed(item.deviation)} ${unit} daneben`;
        }
        let adopt = "";
        if (canAdopt && item.status === "outlier" && !item.applied) {
          const confirm = this._confirm === `adopt:${id}:${key}`;
          adopt = `<button class="${confirm ? "danger" : ""}" data-action="adopt" data-member="${escapeHtml(id)}" data-quantity="${key}">${
            confirm
              ? `Wirklich ${signed(item.new_offset)} ${unit} setzen?`
              : `Übernehmen: ${signed(item.new_offset)} ${unit}`
          }</button>`;
        }
        let track = `<div class="mini"></div>`;
        if (item.deviation !== null && item.deviation !== undefined) {
          const before = pos(item.deviation);
          const after =
            item.after !== null && item.after !== undefined ? pos(item.after) : null;
          const link =
            after === null
              ? ""
              : `<i class="link" style="left: ${Math.min(before, after)}%; width: ${Math.abs(before - after)}%"></i>`;
          const title = `vorher ${signed(item.deviation)} ${unit}${after === null ? "" : `, nachher ${signed(item.after)} ${unit}`}`;
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
    const legend = `<div class="legend"><span><i class="dot before"></i>vorher</span>${
      hasAfter ? `<span><i class="dot after"></i>nachher</span>` : ""
    }<span><i class="zonekey"></i>Toleranz ±${number(meta.tolerance, meta.tolerance < 1 ? 2 : 0)} ${escapeHtml(unit)}</span></div>`;
    const older = hasAfter
      ? ""
      : `<p class="older">Werte nach der Korrektur je Sensor gibt es erst bei Läufen ab Version 1.1.0.</p>`;
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
      ? `<button class="${confirm ? "danger" : ""}" data-action="rollback">${confirm ? "Wirklich zurücknehmen?" : "Rückgängig"}</button>`
      : "";
    const message = last.rolled_back
      ? "Die alten Einstellungen sind wiederhergestellt."
      : last.message;
    const close = reopened
      ? `<button class="primary" data-action="back">Zurück</button>`
      : `<button class="primary" data-action="dismiss">Schließen</button>`;
    const badge = reopened ? "Ergebnis" : BADGES[last.outcome];
    return `${this._header(badge, colors[last.outcome])}
      <p class="lead">${escapeHtml(message)}</p>
      <p class="sub">${last.mode === "quick" ? "Schnellkalibrierung, " : ""}${clock(last.started_at)} bis ${clock(last.finished_at)} Uhr</p>
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
      body = `${this._header("Lädt", "var(--secondary-text-color)")}<p class="sub">Verbinde mit Home Assistant …</p>`;
    } else if (state.phase === "not_loaded") {
      body = `${this._header("Nicht aktiv", "var(--warning-color)")}
        <p class="lead">Integration nicht eingerichtet</p>
        <p class="sub">Füge unter Einstellungen, Geräte &amp; Dienste die Integration Sensor-Kalibrierung hinzu.</p>`;
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
  name: "Zigbee2MQTT Sensor-Kalibrierung",
  description: "Gleicht nebeneinanderliegende Zigbee2MQTT-Sensoren automatisch ab.",
});
