"""DataUpdateCoordinator for MaNoSens ZPVR."""
from datetime import timedelta
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import MaNoSensZPVRAPI
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Define update intervals
NORMAL_UPDATE_INTERVAL = timedelta(seconds=30)
# DataUpdateCoordinator automatically handles exponential backoff on successive failures.
# This means the interval between updates will increase beyond NORMAL_UPDATE_INTERVAL
# when errors persist, which is a standard and recommended practice to avoid
# overwhelming a failing device.

class MaNoSensZPVRDataUpdateCoordinator(DataUpdateCoordinator):
    """Manages fetching data from the MaNoSens ZPVR device."""

    def __init__(self, hass: HomeAssistant, api: MaNoSensZPVRAPI):
        """Initialize my coordinator."""
        self.api = api
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=NORMAL_UPDATE_INTERVAL,
        )

    async def _async_update_data(self):
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can work with them.
        """
        try:
            # Fetch general data
            data = await self.api.async_get_data()
            if data is None:
                raise UpdateFailed("Failed to fetch general data from device.")

            # Fetch version data
            version_data = await self.api.async_get_version()
            if version_data is None:
                _LOGGER.warning("Failed to fetch version data from device. Proceeding without it.")
                version_data = "" # Provide an empty string if version data is not available

            # Combine all data into a single dictionary
            # You might want to structure this differently based on your needs
            # For now, let's put version data under a 'version' key
            combined_data = {**data, "version": version_data}

            return combined_data
        except Exception as err:
            # DataUpdateCoordinator will automatically handle exponential backoff
            # when UpdateFailed is raised. The interval will increase on repeated failures.
            _LOGGER.error("Error fetching manosens_zpvr data: %s", err)
            raise UpdateFailed(f"Error communicating with API: {err}")
