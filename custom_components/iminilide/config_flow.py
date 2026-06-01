from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import IminilideApiClient, normalize_host
from .const import DOMAIN
from .exceptions import IminilideConnectionError, IminilideParseError

_LOGGER = logging.getLogger(__name__)


async def _async_validate_input(
    hass: HomeAssistant,
    user_input: dict[str, str],
) -> dict[str, str]:
    host = normalize_host(user_input[CONF_HOST])
    client = IminilideApiClient(async_get_clientsession(hass), host)
    description = await client.async_fetch_controller_description()
    return {
        "host": host,
        "title": description.metadata.name or host,
        "unique_id": description.metadata.serial_number or host,
    }


class IminilideConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for i-MINILide."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, str] | None = None):
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await _async_validate_input(self.hass, user_input)
            except IminilideConnectionError:
                errors["base"] = "cannot_connect"
            except IminilideParseError:
                errors["base"] = "invalid_response"
            except Exception:  # pragma: no cover - defensive guard for Home Assistant
                _LOGGER.exception("Unexpected error while validating i-MINILide config")
                errors["base"] = "unknown"
            else:
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
