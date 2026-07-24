"""Platform for binary sensor integration."""
from __future__ import annotations

import logging

from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import MaNoSensZPVRDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the binary sensor platform."""
    coordinator: MaNoSensZPVRDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities = [
        MaNoSensZPVROnOffStateBinarySensor(coordinator, config_entry.entry_id),
    ]
    async_add_entities(entities)

class MaNoSensZPVROnOffStateBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of the MaNoSens ZPVR On/Off State Binary Sensor."""

    def __init__(self, coordinator: MaNoSensZPVRDataUpdateCoordinator, entry_id: str) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._attr_name = f"MaNoSens ZPVR On/Off State ({entry_id})"
        self._attr_unique_id = f"{entry_id}_on_off_state"
        self._attr_device_class = BinarySensorDeviceClass.POWER
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry_id)},
            "name": "MaNoSens ZPVR Device",
            "manufacturer": "MaNoSens",
        }

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        if self.coordinator.data and "secret" in self.coordinator.data and "on_off_state" in self.coordinator.data["secret"]:
            state_value = self.coordinator.data["secret"]["on_off_state"]
            if state_value == 1:
                return True
            elif state_value == 5:
                return False
        return None
