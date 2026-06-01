from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import IminilideApiClient, normalize_host
from .const import DOMAIN, MANUFACTURER, PLATFORMS
from .exceptions import IminilideError
from .models import IminilideRuntimeData
from .parser import ControllerMetadata
from .coordinator import IminilideDataUpdateCoordinator


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the integration from YAML, which is not used."""

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up i-MINILide from a config entry."""

    host = normalize_host(entry.data[CONF_HOST])
    client = IminilideApiClient(async_get_clientsession(hass), host)

    try:
        description = await client.async_fetch_controller_description()
    except IminilideError as exc:
        raise ConfigEntryNotReady(str(exc)) from exc

    coordinator = IminilideDataUpdateCoordinator(hass, client)
    await coordinator.async_config_entry_first_refresh()

    controller_identifier = description.metadata.serial_number or host
    controller_device_identifier = f"controller_{controller_identifier}"
    _async_register_controller_device(
        hass,
        entry,
        controller_device_identifier,
        host,
        description.metadata,
    )

    entry.runtime_data = IminilideRuntimeData(
        client=client,
        description=description,
        coordinator=coordinator,
        controller_identifier=controller_identifier,
        host=host,
    )
    entry.async_on_unload(entry.add_update_listener(_async_reload_entry))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        entry.runtime_data = None
    return unload_ok


async def _async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


def _async_register_controller_device(
    hass: HomeAssistant,
    entry: ConfigEntry,
    controller_device_identifier: str,
    host: str,
    metadata: ControllerMetadata,
) -> None:
    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, controller_device_identifier)},
        connections={
            (dr.CONNECTION_NETWORK_MAC, metadata.mac_address)
        }
        if metadata.mac_address
        else None,
        manufacturer=MANUFACTURER,
        model="i-MINILide",
        name=metadata.name or host,
        serial_number=metadata.serial_number,
        sw_version=_build_sw_version(metadata),
        configuration_url=f"http://{host}/",
    )


def _build_sw_version(metadata: ControllerMetadata) -> str | None:
    parts: list[str] = []
    if metadata.firmware_web:
        parts.append(f"web {metadata.firmware_web}")
    if metadata.firmware_base:
        parts.append(f"base {metadata.firmware_base}")
    if metadata.firmware_display:
        parts.append(f"display {metadata.firmware_display}")
    return ", ".join(parts) or None
