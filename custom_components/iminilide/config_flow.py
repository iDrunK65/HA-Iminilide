from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import IminilideApiClient, normalize_host
from .const import (
    DEFAULT_SCAN_INTERVAL_SECONDS,
    DOMAIN,
    MAX_SCAN_INTERVAL_SECONDS,
    MIN_SCAN_INTERVAL_SECONDS,
)
from .exceptions import IminilideConnectionError, IminilideParseError

_LOGGER = logging.getLogger(__name__)


async def _async_validate_input(
    hass: HomeAssistant,
    user_input: dict[str, str],
) -> dict[str, str]:
    raw_host = user_input[CONF_HOST]
    host = normalize_host(raw_host)
    _LOGGER.debug(
        "Validating i-MINILide config input: raw_host=%s normalized_host=%s",
        raw_host,
        host,
    )
    client = IminilideApiClient(async_get_clientsession(hass), host)
    description = await client.async_fetch_controller_description()
    _LOGGER.debug(
        "Validation succeeded for host %s: title=%s unique_id=%s voies=%d",
        host,
        description.metadata.name or host,
        description.metadata.serial_number or host,
        len(description.voies),
    )
    return {
        "host": host,
        "title": description.metadata.name or host,
        "unique_id": description.metadata.serial_number or host,
    }


class IminilideConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for i-MINILide."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return IminilideOptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input: dict[str, str] | None = None):
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await _async_validate_input(self.hass, user_input)
            except IminilideConnectionError:
                _LOGGER.debug(
                    "Cannot connect to i-MINILide during config flow for host input %s",
                    user_input.get(CONF_HOST),
                    exc_info=True,
                )
                errors["base"] = "cannot_connect"
            except IminilideParseError:
                _LOGGER.debug(
                    "Invalid i-MINILide response during config flow for host input %s",
                    user_input.get(CONF_HOST),
                    exc_info=True,
                )
                errors["base"] = "invalid_response"
            except Exception:  # pragma: no cover - defensive guard for Home Assistant
                _LOGGER.exception("Unexpected error while validating i-MINILide config")
                errors["base"] = "unknown"
            else:
                _LOGGER.debug(
                    "Creating config entry for host %s with title=%s unique_id=%s",
                    info["host"],
                    info["title"],
                    info["unique_id"],
                )
                await self.async_set_unique_id(info["unique_id"])
                self._abort_if_unique_id_configured(updates={CONF_HOST: info["host"]})
                return self.async_create_entry(
                    title=info["title"],
                    data={CONF_HOST: info["host"]},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_HOST): str}),
            errors=errors,
        )


class IminilideOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle i-MINILide options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, int] | None = None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_SCAN_INTERVAL,
                        default=self._config_entry.options.get(
                            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_SECONDS
                        ),
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(
                            min=MIN_SCAN_INTERVAL_SECONDS,
                            max=MAX_SCAN_INTERVAL_SECONDS,
                        ),
                    )
                }
            ),
        )
