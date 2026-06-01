from __future__ import annotations

from dataclasses import dataclass

from .api import IminilideApiClient
from .coordinator import IminilideDataUpdateCoordinator
from .parser import ControllerDescription


@dataclass(slots=True)
class IminilideRuntimeData:
    client: IminilideApiClient
    description: ControllerDescription
    coordinator: IminilideDataUpdateCoordinator
    controller_identifier: str
    host: str
