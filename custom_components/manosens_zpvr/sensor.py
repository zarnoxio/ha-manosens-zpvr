"""Platform for sensor integration."""
from __future__ import annotations

import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.const import UnitOfTemperature, UnitOfPressure, UnitOfFrequency

from .const import DOMAIN
from .coordinator import MaNoSensZPVRDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator: MaNoSensZPVRDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities = [
        MaNoSensZPVRVersionSensor(coordinator, config_entry.entry_id),
        MaNoSensZPVRFrequencySensor(coordinator, config_entry.entry_id),
        MaNoSensZPVRCurrentSensor(coordinator, config_entry.entry_id),
        MaNoSensZPVRPressureSensor(coordinator, config_entry.entry_id),
        MaNoSensZPVRTemperatureSensor(coordinator, config_entry.entry_id),
    ]
    async_add_entities(entities)


class MaNoSensZPVRVersionSensor(CoordinatorEntity, SensorEntity):
    """Representation of the MaNoSens ZPVR Version Sensor."""

    def __init__(self, coordinator: MaNoSensZPVRDataUpdateCoordinator, entry_id: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = f"MaNoSens ZPVR Version ({entry_id})"
        self._attr_unique_id = f"{entry_id}_version"
        self._attr_icon = "mdi:information-outline"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry_id)},
            "name": "MaNoSens ZPVR Device",
            "manufacturer": "MaNoSens",
        }

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self.coordinator.data and "version" in self.coordinator.data:
            return self.coordinator.data["version"]
        return None

class MaNoSensZPVRFrequencySensor(CoordinatorEntity, SensorEntity):
    """Representation of the MaNoSens ZPVR Frequency Sensor."""

    def __init__(self, coordinator: MaNoSensZPVRDataUpdateCoordinator, entry_id: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = f"MaNoSens ZPVR Frequency ({entry_id})"
        self._attr_unique_id = f"{entry_id}_frequency"
        self._attr_native_unit_of_measurement = UnitOfFrequency.HERTZ
        self._attr_icon = "mdi:sine-wave"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry_id)},
            "name": "MaNoSens ZPVR Device",
            "manufacturer": "MaNoSens",
        }

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self.coordinator.data and "data" in self.coordinator.data and "frequency" in self.coordinator.data["data"]:
            return self.coordinator.data["data"]["frequency"]["value"]
        return None

class MaNoSensZPVRCurrentSensor(CoordinatorEntity, SensorEntity):
    """Representation of the MaNoSens ZPVR Current Sensor."""

    def __init__(self, coordinator: MaNoSensZPVRDataUpdateCoordinator, entry_id: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = f"MaNoSens ZPVR Current ({entry_id})"
        self._attr_unique_id = f"{entry_id}_current"
        self._attr_native_unit_of_measurement = "A" # Changed from UnitOfCurrent.AMPERE
        self._attr_icon = "mdi:current-ac"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry_id)},
            "name": "MaNoSens ZPVR Device",
            "manufacturer": "MaNoSens",
        }

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self.coordinator.data and "data" in self.coordinator.data and "current" in self.coordinator.data["data"]:
            return self.coordinator.data["data"]["current"]["value"]
        return None

class MaNoSensZPVRPressureSensor(CoordinatorEntity, SensorEntity):
    """Representation of the MaNoSens ZPVR Pressure Sensor."""

    def __init__(self, coordinator: MaNoSensZPVRDataUpdateCoordinator, entry_id: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = f"MaNoSens ZPVR Pressure ({entry_id})"
        self._attr_unique_id = f"{entry_id}_pressure"
        self._attr_native_unit_of_measurement = UnitOfPressure.BAR
        self._attr_icon = "mdi:gauge"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry_id)},
            "name": "MaNoSens ZPVR Device",
            "manufacturer": "MaNoSens",
        }

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self.coordinator.data and "data" in self.coordinator.data and "pressure" in self.coordinator.data["data"]:
            return self.coordinator.data["data"]["pressure"]["value"]
        return None

class MaNoSensZPVRTemperatureSensor(CoordinatorEntity, SensorEntity):
    """Representation of the MaNoSens ZPVR Temperature Sensor."""

    def __init__(self, coordinator: MaNoSensZPVRDataUpdateCoordinator, entry_id: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = f"MaNoSens ZPVR Temperature ({entry_id})"
        self._attr_unique_id = f"{entry_id}_temperature"
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
        self._attr_icon = "mdi:thermometer"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry_id)},
            "name": "MaNoSens ZPVR Device",
            "manufacturer": "MaNoSens",
        }

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self.coordinator.data and "data" in self.coordinator.data and "temperature" in self.coordinator.data["data"]:
            return self.coordinator.data["data"]["temperature"]["value"]
        return None
