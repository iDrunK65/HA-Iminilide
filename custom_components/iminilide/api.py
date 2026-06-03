from __future__ import annotations

import asyncio
import logging
from urllib.parse import urlparse

from aiohttp import ClientError, ClientSession

from .const import DEFAULT_TIMEOUT, MAX_CONCURRENT_VOIE_REQUESTS
from .exceptions import IminilideConnectionError
from .parser import (
    ControllerDescription,
    parse_general_configuration,
    parse_measurements_html,
    parse_network_configuration,
    parse_refresh_payload,
    parse_voie_configuration,
    parse_voie_list,
)

_LOGGER = logging.getLogger(__name__)


def normalize_host(host: str) -> str:
    """Normalize a user-provided host or URL into a host:port string."""

    candidate = host.strip()
    if "://" not in candidate:
        candidate = f"http://{candidate}"

    parsed = urlparse(candidate)
    normalized = parsed.netloc or parsed.path
    return normalized.rstrip("/")


class IminilideApiClient:
    """Async client for the i-MINILide HTTP interface."""

    def __init__(self, session: ClientSession, host: str) -> None:
        self._session = session
        self.host = normalize_host(host)
        self._base_url = f"http://{self.host}"

    async def async_fetch_controller_description(self) -> ControllerDescription:
        _LOGGER.debug("Fetching controller description from host %s", self.host)
        metadata_html, network_html, voie_list_html = await asyncio.gather(
            self._async_get_text("/index?configuration_iminilide"),
            self._async_get_text("/index?configuration_reseau"),
            self._async_get_text("/index?configuration_voie"),
        )

        metadata = parse_general_configuration(metadata_html, network_html)
        voie_summaries = parse_voie_list(voie_list_html)
        _LOGGER.debug(
            "Fetched base controller pages from %s: name=%s serial=%s voies=%d",
            self.host,
            metadata.name or self.host,
            metadata.serial_number,
            len(voie_summaries),
        )
        semaphore = asyncio.Semaphore(MAX_CONCURRENT_VOIE_REQUESTS)

        async def _async_fetch_limited(voie_number: int):
            async with semaphore:
                return await self.async_fetch_voie_configuration(voie_number)

        _LOGGER.debug(
            "Fetching %d voie configurations from %s with concurrency limit %d",
            len(voie_summaries),
            self.host,
            MAX_CONCURRENT_VOIE_REQUESTS,
        )
        voie_details = await asyncio.gather(
            *(_async_fetch_limited(voie.number) for voie in voie_summaries)
        )

        description = ControllerDescription(
            metadata=metadata,
            voies={voie.number: voie for voie in voie_details},
        )
        _LOGGER.debug(
            "Controller description ready for %s with %d parsed voies",
            self.host,
            len(description.voies),
        )
        return description

    async def async_fetch_voie_configuration(self, number: int):
        _LOGGER.debug("Fetching configuration for host %s voie %d", self.host, number)
        html = await self._async_get_text(f"/index?configuration_voie{number}")
        voie = parse_voie_configuration(html)
        _LOGGER.debug(
            "Parsed configuration for host %s voie %d: name=%s active=%s sensor_type=%s surveillance=%s",
            self.host,
            number,
            voie.name,
            voie.active,
            voie.sensor_type,
            voie.alarm_surveillance_enabled,
        )
        return voie

    async def async_fetch_readings(self):
        _LOGGER.debug("Refreshing readings from host %s", self.host)
        payload = await self._async_post_text("/", {"action": "refresh"})
        if _looks_like_html(payload):
            _LOGGER.debug(
                "Refresh payload from host %s returned HTML, using legacy parser",
                self.host,
            )
            readings = parse_measurements_html(payload)
        else:
            readings = parse_refresh_payload(payload)

        _LOGGER.debug(
            "Parsed %d readings from host %s",
            len(readings),
            self.host,
        )
        return readings

    async def _async_get_text(self, path: str) -> str:
        return await self._async_request_text("GET", path)

    async def _async_post_text(self, path: str, data: dict[str, str]) -> str:
        return await self._async_request_text("POST", path, data=data)

    async def _async_request_text(
        self, method: str, path: str, data: dict[str, str] | None = None
    ) -> str:
        url = f"{self._base_url}{path}"
        _LOGGER.debug("HTTP %s %s", method, url)
        try:
            async with self._session.request(
                method,
                url,
                data=data,
                timeout=DEFAULT_TIMEOUT,
            ) as response:
                response.raise_for_status()
                text = await response.text()
                _LOGGER.debug(
                    "HTTP %s %s -> %s (%d bytes, content_type=%s)",
                    method,
                    url,
                    response.status,
                    len(text),
                    response.content_type,
                )
                return text
        except (ClientError, TimeoutError) as exc:
            _LOGGER.debug("HTTP %s %s failed", method, url, exc_info=True)
            raise IminilideConnectionError(
                f"Request to {url} failed: {exc}"
            ) from exc


def _looks_like_html(payload: str) -> bool:
    stripped = payload.lstrip().lower()
    return stripped.startswith("<html") or stripped.startswith("<!doctype html")
