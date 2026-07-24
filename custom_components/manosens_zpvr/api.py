"""API for Manosens ZPVR."""
import logging
import json
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)

class MaNoSensZPVRAPI:
    """Manages communication with the Manosens ZPVR REST API."""

    def __init__(self, hass: HomeAssistant, host: str, port: int):
        """Initialize the API client."""
        self._base_url = f"http://{host}:{port}"
        self._client = async_get_clientsession(hass)

    async def async_get_data(self):
        """Fetch data from the device."""
        url = f"{self._base_url}/get-rs-data" # Changed to /get-rs-data as per error log
        _LOGGER.debug("Fetching data from %s", url)
        try:
            async with self._client.get(url) as response:
                _LOGGER.debug("Response status for %s: %s", url, response.status)
                response.raise_for_status()
                
                text = None
                try:
                    text = await response.text() # Try decoding with Content-Type charset or UTF-8
                except UnicodeDecodeError:
                    _LOGGER.warning("UnicodeDecodeError when decoding response from %s with default encoding. Trying latin-1.", url)
                    # If default decoding fails, try latin-1
                    text = (await response.read()).decode("latin-1")

                _LOGGER.debug("Response body for %s: %s", url, text)

                content_type = response.headers.get("Content-Type", "")
                if "application/json" in content_type:
                    try:
                        json_data = json.loads(text)
                        _LOGGER.debug("Successfully parsed JSON data from %s", url)
                        
                        # --- NEW VALIDATION LOGIC ---
                        # Ensure json_data is a dictionary
                        if not isinstance(json_data, dict):
                            _LOGGER.warning("Received JSON data is not a dictionary from %s. Response: %s", url, text)
                            return None
                        
                        # Ensure the 'data' key exists and its value is a non-empty dictionary
                        if "data" not in json_data or not isinstance(json_data["data"], dict) or not json_data["data"]:
                            _LOGGER.warning("Received JSON data missing 'data' key, or 'data' is not a dictionary, or 'data' is empty from %s. Treating as no valid sensor data. Response: %s", url, text)
                            return None
                        # --- END NEW VALIDATION LOGIC ---
                        
                        return json_data
                    except json.JSONDecodeError:
                        _LOGGER.warning("Received JSON content type but failed to decode JSON from %s. Response: %s", url, text)
                        return None # Return None if JSON decoding fails
                else:
                    _LOGGER.warning("Received non-JSON content type (%s) from %s. Response: %s", content_type, url, text)
                    return None # Return None for non-JSON content

        except Exception as e:
            _LOGGER.error("Error communicating with Manosens ZPVR device at %s: %s", url, e, exc_info=True)
            return None

    async def async_get_version(self):
        """Fetch version information from the device."""
        url = f"{self._base_url}/version"
        _LOGGER.debug("Fetching version from %s", url)
        try:
            async with self._client.get(url) as response:
                _LOGGER.debug("Response status for %s: %s", url, response.status)
                response.raise_for_status()
                text = await response.text()
                _LOGGER.debug("Response body for %s: %s", url, text)
                # Assuming the version endpoint now returns plain text directly
                return text

        except Exception as e:
            _LOGGER.error("Error communicating with Manosens ZPVR device for version at %s: %s", url, e, exc_info=True)
            return None

    async def async_set_pressure(self, value: float):
        """Set the pressure on the device."""
        if not (0.0 <= value <= 5.0):
            _LOGGER.warning("Attempted to set pressure to %s, which is outside the allowed range (0.0 - 5.0).", value)
            return False

        url = f"{self._base_url}/set-pressure"
        payload = {"value": value}
        _LOGGER.debug("Setting pressure at %s with payload: %s", url, payload)
        try:
            async with self._client.post(url, json=payload) as response:
                _LOGGER.debug("Response status for %s: %s", url, response.status)
                response.raise_for_status()
                _LOGGER.debug("Successfully set pressure to %s", value)
                return True
        except Exception as e:
            _LOGGER.error("Error setting pressure on Manosens ZPVR device at %s: %s", url, e, exc_info=True)
            return False

    async def async_set_start_stop(self, value: bool):
        """Set the start/stop state on the device."""
        url = f"{self._base_url}/start-stop"
        payload = {"value": value}
        _LOGGER.debug("Setting start/stop at %s with payload: %s", url, payload)
        try:
            async with self._client.post(url, json=payload) as response:
                _LOGGER.debug("Response status for %s: %s", url, response.status)
                response.raise_for_status()
                _LOGGER.debug("Successfully set start/stop to %s", value)
                return True
        except Exception as e:
            _LOGGER.error("Error setting start/stop on Manosens ZPVR device at %s: %s", url, e, exc_info=True)
            return False
