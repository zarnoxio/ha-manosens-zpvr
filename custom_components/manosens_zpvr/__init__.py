"""MaNoSens ZPVR integration.

Register service actions even when the device is offline during setup. A
service call is *never* treated as successful unless the API reports success.
"""
from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

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

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

SERVICE_SET_PRESSURE_SCHEMA = vol.Schema(
    {vol.Required(CONF_PRESSURE_VALUE): vol.All(cv.positive_float, vol.Range(max=5.0))}
)
SERVICE_SET_START_STOP_SCHEMA = vol.Schema(
    {vol.Required(CONF_START_STOP_VALUE): cv.boolean}
)


def _get_active_coordinator(hass: HomeAssistant) -> MaNoSensZPVRDataUpdateCoordinator:
    """Fail closed if there is no device, or the service target is ambiguous."""
    coordinators = list(hass.data.get(DOMAIN, {}).values())
    if len(coordinators) != 1:
        raise HomeAssistantError(
            f"MaNoSens ZPVR requires exactly one loaded device; found {len(coordinators)}"
        )
    coordinator = coordinators[0]
    if not coordinator.last_update_success:
        raise HomeAssistantError("MaNoSens ZPVR has no current validated measurements")
    return coordinator


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Register services independently of a successful device fetch."""
    hass.data.setdefault(DOMAIN, {})

    async def handle_set_pressure(call: ServiceCall) -> None:
        value = call.data[CONF_PRESSURE_VALUE]
        coordinator = _get_active_coordinator(hass)
        if not await coordinator.api.async_set_pressure(value):
            # HTTP failure or no verified read-back: do not imply success.
            raise HomeAssistantError(
                f"MaNoSens ZPVR: pressure {value} bar was not confirmed by read-back"
            )
        _LOGGER.info("MaNoSens ZPVR required pressure verified: %s bar", value)

    async def handle_set_start_stop(call: ServiceCall) -> None:
        value = call.data[CONF_START_STOP_VALUE]
        coordinator = _get_active_coordinator(hass)
        if not await coordinator.api.async_set_start_stop(value):
            raise HomeAssistantError("MaNoSens ZPVR: start/stop HTTP command failed")
        # The device-specific semantic state encoding is still unverified.
        # An HTTP acknowledgement does NOT prove physical action.
        _LOGGER.info("MaNoSens ZPVR start/stop HTTP request acknowledged; physical state not verified")

    hass.services.async_register(
        DOMAIN, SERVICE_SET_PRESSURE, handle_set_pressure,
        schema=SERVICE_SET_PRESSURE_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN, SERVICE_SET_START_STOP, handle_set_start_stop,
        schema=SERVICE_SET_START_STOP_SCHEMA,
    )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Require real sensor data at initial setup; HA retries offline entries.

    A config-only first response raises ConfigEntryNotReady via the standard
    coordinator helper, without making the service action disappear.
    """
    host = entry.data[CONF_HOST]
    port = entry.data[CONF_PORT]
    api = MaNoSensZPVRAPI(hass, host, port)
    coordinator = MaNoSensZPVRDataUpdateCoordinator(hass, api)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    try:
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    except Exception:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        raise
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload entities but keep service actions registered for offline entries."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    return unload_ok
