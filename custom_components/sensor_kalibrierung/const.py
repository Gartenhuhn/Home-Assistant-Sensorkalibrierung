"""Konstanten der Sensor-Kalibrierung."""

from __future__ import annotations

from dataclasses import dataclass

DOMAIN = "sensor_kalibrierung"
CARD_URL = f"/{DOMAIN}/sensor-kalibrierung-card.js"

CONF_BASE_TOPIC = "base_topic"
CONF_MEASURE_HOURS = "measure_hours"
CONF_VERIFY_HOURS = "verify_hours"
CONF_SETTLE_MAX_HOURS = "settle_max_hours"
CONF_MAX_TEMPERATURE = "max_temperature_offset"
CONF_MAX_HUMIDITY = "max_humidity_offset"
CONF_MAX_PRESSURE = "max_pressure_offset"
CONF_NOTIFY_TARGETS = "notify_targets"

MODE_STANDARD = "standard"
MODE_QUICK = "quick"
MODES = (MODE_STANDARD, MODE_QUICK)

DEFAULT_BASE_TOPIC = "zigbee2mqtt"
DEFAULT_MEASURE_HOURS = 4
DEFAULT_VERIFY_HOURS = 2
DEFAULT_SETTLE_MAX_HOURS = 8

# Schnellkalibrierung, abgeleitet aus einem Lauf mit 14 Sensoren:
# 2 Stunden Messen wichen im Median 0,03 °C vom 6-Stunden-Ergebnis ab.
QUICK_SETTLE_MIN_HOURS = 1
QUICK_SETTLE_MAX_HOURS = 4
QUICK_MEASURE_HOURS = 2
QUICK_VERIFY_HOURS = 1

PHASE_IDLE = "idle"
PHASE_PREPARING = "preparing"
PHASE_SETTLING = "settling"
PHASE_MEASURING = "measuring"
PHASE_APPLYING = "applying"
PHASE_VERIFYING = "verifying"
PHASE_DONE = "done"
PHASE_FAILED = "failed"
PHASE_CANCELLED = "cancelled"
PHASES = [
    PHASE_IDLE,
    PHASE_PREPARING,
    PHASE_SETTLING,
    PHASE_MEASURING,
    PHASE_APPLYING,
    PHASE_VERIFYING,
    PHASE_DONE,
    PHASE_FAILED,
    PHASE_CANCELLED,
]
ACTIVE_PHASES = (
    PHASE_PREPARING,
    PHASE_SETTLING,
    PHASE_MEASURING,
    PHASE_APPLYING,
    PHASE_VERIFYING,
)
PHASE_STEP = {
    PHASE_PREPARING: 1,
    PHASE_SETTLING: 2,
    PHASE_MEASURING: 3,
    PHASE_APPLYING: 4,
    PHASE_VERIFYING: 5,
}

TICK_SECONDS = 300
GRID_SECONDS = 300
MAX_HOLD_SECONDS = int(2.5 * 3600)
SILENT_SECONDS = 90 * 60
MAX_GAP_SECONDS = 2 * 3600
# Lüften, Kochen oder Heizung: schwankt der Bezugswert innerhalb von 45 Minuten
# um mehr als zwei Toleranzen, zählen diese Rasterpunkte nicht.
DISTURB_LOOKBACK_SECONDS = 45 * 60
MAX_DISTURBED_MEASURE = 0.3
MAX_DISTURBED_VERIFY = 0.5
MIN_COVERAGE = 0.7
NEW_DEVICE_DAYS = 14
MAX_SAMPLES_PER_ENTITY = 3000

PREPARE_TIMEOUT_SECONDS = 2 * 3600
SETTLE_MIN_SECONDS = 2 * 3600
SETTLE_WINDOW_SECONDS = 3600
VERIFY_WAIT_SECONDS = 3 * 3600
APPLY_MAX_ATTEMPTS = 12
BATTERY_WARN_PERCENT = 15
MIN_WINDOW_POINTS = 6
Z2M_RESPONSE_TIMEOUT = 15

STATUS_OK = "ok"
STATUS_REFERENCE = "reference"
STATUS_COMPARE = "compare"
STATUS_OUTLIER = "outlier"
STATUS_UNSTABLE = "unstable"
STATUS_NO_DATA = "no_data"


@dataclass(frozen=True)
class Quantity:
    """Eine Messgröße, die kalibriert werden kann."""

    key: str
    device_class: str
    unit: str
    label: str
    max_offset: float
    tolerance: float
    precision: int
    default_precision: int
    minimum: float
    maximum: float

    @property
    def calibration_option(self) -> str:
        """Name der Z2M-Option für den Offset."""
        return f"{self.key}_calibration"

    @property
    def precision_option(self) -> str:
        """Name der Z2M-Option für die Nachkommastellen."""
        return f"{self.key}_precision"


QUANTITIES: dict[str, Quantity] = {
    "temperature": Quantity(
        "temperature", "temperature", "°C", "Temperatur", 3.0, 0.25, 2, 2, -40, 85
    ),
    "humidity": Quantity(
        "humidity", "humidity", "%", "Luftfeuchte", 10.0, 1.0, 2, 2, 0, 100
    ),
    "pressure": Quantity(
        "pressure", "atmospheric_pressure", "hPa", "Luftdruck", 5.0, 0.3, 1, 1, 800, 1200
    ),
}
