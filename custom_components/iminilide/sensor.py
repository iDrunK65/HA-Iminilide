from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import IminilideVoieEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up i-MINILide sensor entities."""

    runtime_data = entry.runtime_data
    entities: list[SensorEntity] = []

    for voie in sorted(runtime_data.description.voies.values(), key=lambda voie: voie.number):
        entities.append(IminilideMeasurementSensor(runtime_data, voie))

    async_add_entities(entities)


class IminilideMeasurementSensor(IminilideVoieEntity, SensorEntity):
    """Current measurement for one voie."""

    def __init__(self, runtime_data, voie) -> None:
        super().__init__(runtime_data, voie, "measurement")
        self._attr_name = "Mesure"

    @property
    def native_value(self):
        if self.reading is None:
            return None
        if self.reading.numeric_value is not None:
            return self.reading.numeric_value
        return self.reading.raw_value

    @property
    def native_unit_of_measurement(self) -> str | None:
        if self.reading is None or self.reading.numeric_value is None:
            return None
        return self.reading.unit or self.voie.unit

    @property
    def device_class(self) -> SensorDeviceClass | None:
        if self.native_unit_of_measurement == UnitOfTemperature.CELSIUS:
            return SensorDeviceClass.TEMPERATURE
        return None

    @property
    def suggested_display_precision(self) -> int | None:
        if self.reading is not None and self.reading.numeric_value is not None:
            return 1
        return None

    @property
    def extra_state_attributes(self) -> dict[str, str | bool | float] | None:
        attributes: dict[str, str | bool | float] = {
            "active": self.voie.active,
            "sensor_type": self.voie.sensor_type,
        }
        if self.reading is not None:
            if self.reading.state:
                attributes["controller_state"] = self.reading.state
            if self.reading.cycle_in_progress:
                attributes["cycle_in_progress"] = self.reading.cycle_in_progress
            if self.reading.duration:
                attributes["duration"] = self.reading.duration
            if self.reading.product_name:
                attributes["product_name"] = self.reading.product_name
        return attributes
