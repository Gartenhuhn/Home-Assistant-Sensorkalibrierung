"""Einrichtung und Einstellungen der Sensor-Kalibrierung."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
)

from .const import (
    CONF_BASE_TOPIC,
    CONF_MAX_HUMIDITY,
    CONF_MAX_PRESSURE,
    CONF_MAX_TEMPERATURE,
    CONF_MEASURE_HOURS,
    CONF_NOTIFY_TARGETS,
    CONF_SETTLE_MAX_HOURS,
    CONF_VERIFY_HOURS,
    DEFAULT_BASE_TOPIC,
    DEFAULT_MEASURE_HOURS,
    DEFAULT_SETTLE_MAX_HOURS,
    DEFAULT_VERIFY_HOURS,
    DOMAIN,
    QUANTITIES,
)


def _number(minimum: float, maximum: float, step: float, unit: str) -> NumberSelector:
    """Erzeugt ein Zahlenfeld."""
    return NumberSelector(
        NumberSelectorConfig(
            min=minimum,
            max=maximum,
            step=step,
            mode=NumberSelectorMode.BOX,
            unit_of_measurement=unit,
        )
    )


class SensorKalibrierungConfigFlow(ConfigFlow, domain=DOMAIN):
    """Richtet die Integration ein."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Fragt das Zigbee2MQTT-Topic ab."""
        if user_input is not None:
            return self.async_create_entry(title="Sensor-Kalibrierung", data=user_input)
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {vol.Required(CONF_BASE_TOPIC, default=DEFAULT_BASE_TOPIC): TextSelector()}
            ),
        )

    @staticmethod
    @callback
    def async_get_options_flow(_entry: ConfigEntry) -> SensorKalibrierungOptionsFlow:
        """Liefert den Einstellungsdialog."""
        return SensorKalibrierungOptionsFlow()


class SensorKalibrierungOptionsFlow(OptionsFlow):
    """Bearbeitet Messzeiten, Grenzen und Benachrichtigungen."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Zeigt die Einstellungen."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)
        options = self.config_entry.options
        targets = sorted(
            f"notify.{name}"
            for name in self.hass.services.async_services_for_domain("notify")
            if name not in ("send_message", "persistent_notification", "notify")
        )
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_MEASURE_HOURS,
                    default=options.get(CONF_MEASURE_HOURS, DEFAULT_MEASURE_HOURS),
                ): _number(3, 48, 1, "h"),
                vol.Required(
                    CONF_VERIFY_HOURS,
                    default=options.get(CONF_VERIFY_HOURS, DEFAULT_VERIFY_HOURS),
                ): _number(1, 24, 1, "h"),
                vol.Required(
                    CONF_SETTLE_MAX_HOURS,
                    default=options.get(CONF_SETTLE_MAX_HOURS, DEFAULT_SETTLE_MAX_HOURS),
                ): _number(3, 48, 1, "h"),
                vol.Required(
                    CONF_MAX_TEMPERATURE,
                    default=options.get(
                        CONF_MAX_TEMPERATURE, QUANTITIES["temperature"].max_offset
                    ),
                ): _number(0.5, 10, 0.1, "°C"),
                vol.Required(
                    CONF_MAX_HUMIDITY,
                    default=options.get(
                        CONF_MAX_HUMIDITY, QUANTITIES["humidity"].max_offset
                    ),
                ): _number(1, 30, 0.5, "%"),
                vol.Required(
                    CONF_MAX_PRESSURE,
                    default=options.get(
                        CONF_MAX_PRESSURE, QUANTITIES["pressure"].max_offset
                    ),
                ): _number(0.5, 30, 0.5, "hPa"),
                vol.Optional(
                    CONF_NOTIFY_TARGETS,
                    default=options.get(CONF_NOTIFY_TARGETS, []),
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=targets,
                        multiple=True,
                        custom_value=True,
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Required(
                    CONF_BASE_TOPIC,
                    default=options.get(
                        CONF_BASE_TOPIC,
                        self.config_entry.data.get(CONF_BASE_TOPIC, DEFAULT_BASE_TOPIC),
                    ),
                ): TextSelector(),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
