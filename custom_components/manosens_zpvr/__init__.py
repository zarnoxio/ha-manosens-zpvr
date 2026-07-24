"""The ManoSens ZPVR integration."""
from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv

from .const import (
    DOMAIN,
    CONF_HOST,
    CONF_PORT,
    SERVICE_SET_PRESSURE,
    CONF_PRESSURE_VALUE,
    SERVICE_SET_START_STOP,
    CONF_START_STOP_VALUE,
)
from .coordinator import MaNoSensZPVRDataUpdateCoordinator
from .api import MaNoSensZPVRAPI

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR] # Added Platform.BINARY_SENSOR

SERVICE_SET_PRESSURE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_PRESSURE_VALUE): vol.All(cv.positive_float, vol.Range(max=5.0)),
    }
)

SERVICE_SET_START_STOP_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_START_STOP_VALUE): cv.boolean,
    }
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up MaNoSens ZPVR from a config entry."""
    host = entry.data[CONF_HOST]
    port = entry.data[CONF_PORT]

    api = MaNoSensZPVRAPI(hass, host, port)
    coordinator = MaNoSensZPVRDataUpdateCoordinator(hass, api)

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    async def handle_set_pressure(call: ServiceCall):
        """Handle the set pressure service call."""
        value = call.data.get(CONF_PRESSURE_VALUE)
        _LOGGER.debug("Service call to set pressure with value: %s", value)

        for entry_id in hass.data[DOMAIN]:
            coordinator = hass.data[DOMAIN][entry_id]
            await coordinator.api.async_set_pressure(value)
            _LOGGER.info("Pressure set to %s for device %s", value, entry_id)
            break

    hass.services.async_register(
        DOMAIN, SERVICE_SET_PRESSURE, handle_set_pressure, schema=SERVICE_SET_PRESSURE_SCHEMA
    )

    async def handle_set_start_stop(call: ServiceCall):
        """Handle the set start/stop service call."""
        value = call.data.get(CONF_START_STOP_VALUE)
        _LOGGER.debug("Service call to set start/stop with value: %s", value)

        for entry_id in hass.data[DOMAIN]:
            coordinator = hass.data[DOMAIN][entry_id]
            await coordinator.api.async_set_start_stop(value)
            _LOGGER.info("Start/stop set to %s for device %s", value, entry_id)
            break

    hass.services.async_register(
        DOMAIN, SERVICE_SET_START_STOP, handle_set_start_stop, schema=SERVICE_SET_START_STOP_SCHEMA
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    hass.services.async_remove(DOMAIN, SERVICE_SET_PRESSURE)
    hass.services.async_remove(DOMAIN, SERVICE_SET_START_STOP)

    return unload_ok
