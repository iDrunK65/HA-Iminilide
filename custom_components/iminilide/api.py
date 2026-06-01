from __future__ import annotations

import asyncio
from urllib.parse import urlparse

from aiohttp import ClientError, ClientSession

from .const import DEFAULT_TIMEOUT
from .exceptions import IminilideConnectionError
from .parser import (
    ControllerDescription,
    parse_general_configuration,
    parse_network_configuration,
    parse_refresh_payload,
    parse_voie_configuration,
    parse_voie_list,
)


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
        metadata_html, network_html, voie_list_html = await asyncio.gather(
            self._async_get_text("/index?configuration_iminilide"),
            self._async_get_text("/index?configuration_reseau"),
            self._async_get_text("/index?configuration_voie"),
        )

        metadata = parse_general_configuration(metadata_html, network_html)
        voie_summaries = parse_voie_list(voie_list_html)
        voie_details = await asyncio.gather(
            *(self.async_fetch_voie_configuration(voie.number) for voie in voie_summaries)
        )

        return ControllerDescription(
            metadata=metadata,
            voies={voie.number: voie for voie in voie_details},
        )

    async def async_fetch_voie_configuration(self, number: int):
        html = await self._async_get_text(f"/index?configuration_voie{number}")
        return parse_voie_configuration(html)

    async def async_fetch_readings(self):
        payload = await self._async_post_text("/", {"action": "refresh"})
        return parse_refresh_payload(payload)

    async def _async_get_text(self, path: str) -> str:
        return await self._async_request_text("GET", path)

    async def _async_post_text(self, path: str, data: dict[str, str]) -> str:
        return await self._async_request_text("POST", path, data=data)

    async def _async_request_text(
        self, method: str, path: str, data: dict[str, str] | None = None
    ) -> str:
        url = f"{self._base_url}{path}"
        try:
            async with self._session.request(
                method,
                url,
                data=data,
                timeout=DEFAULT_TIMEOUT,
            ) as response:
                response.raise_for_status()
                return await response.text()
        except (ClientError, TimeoutError) as exc:
            raise IminilideConnectionError(
                f"Request to {url} failed: {exc}"
            ) from exc
