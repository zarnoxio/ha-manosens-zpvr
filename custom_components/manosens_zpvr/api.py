"""API for Manosens ZPVR."""
import logging
import json
import asyncio
import math
from aiohttp import ClientTimeout
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)

class MaNoSensZPVRAPI:
    """Manages communication with the Manosens ZPVR REST API."""

    def __init__(self, hass: HomeAssistant, host: str, port: int):
        """Initialize the API client."""
        self._base_url = f"http://{host}:{port}"
        self._client = async_get_clientsession(hass)
        # Bound each HTTP GET, so a stalled connection cannot hide sensor loss.
        self._read_timeout = ClientTimeout(total=5, connect=3)

    async def async_get_data(self):
        """Fetch data from the device."""
        url = f"{self._base_url}/get-rs-data" # Changed to /get-rs-data as per error log
        _LOGGER.debug("Fetching data from %s", url)
        try:
            async with self._client.get(url, timeout=self._read_timeout) as response:
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
                        
                        # The device can return a config/electrometer packet with
                        # HTTP 200 and "data": {}. It is not a sensor sample, but
                        # it does prove that the HTTP connection works. Let the
                        # coordinator decide whether an earlier measurement is fresh.
                        if not isinstance(json_data.get("data"), dict):
                            _LOGGER.warning("Missing or invalid 'data' object from %s", url)
                            return None
                        if not json_data["data"]:
                            if not isinstance(json_data.get("config"), dict) or not json_data["config"]:
                                _LOGGER.warning("Empty 'data' without config packet from %s", url)
                                return None
                            _LOGGER.debug("Received config-only packet from %s", url)
                        # --- END NEW VALIDATION LOGIC ---
                        
                        return json_data
                    except json.JSONDecodeError:
                        _LOGGER.warning("Received JSON content type but failed to decode JSON from %s. Response: %s", url, text)
                        return None # Return None if JSON decoding fails
                else:
                    _LOGGER.warning("Received non-JSON content type (%s) from %s. Response: %s", content_type, url, text)
                    return None # Return None for non-JSON content

        except Exception as e:
            _LOGGER.debug("Error communicating with Manosens ZPVR device at %s: %s", url, e, exc_info=True)
            return None

    async def async_get_version(self):
        """Fetch version information from the device."""
        url = f"{self._base_url}/version"
        _LOGGER.debug("Fetching version from %s", url)
        try:
            async with self._client.get(url, timeout=self._read_timeout) as response:
                _LOGGER.debug("Response status for %s: %s", url, response.status)
                response.raise_for_status()
                text = await response.text()
                _LOGGER.debug("Response body for %s: %s", url, text)
                # Assuming the version endpoint now returns plain text directly
                return text

        except Exception as e:
            _LOGGER.debug("Error communicating with Manosens ZPVR device for version at %s: %s", url, e, exc_info=True)
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
            async with self._client.post(url, json=payload, timeout=self._read_timeout) as response:
                _LOGGER.debug("Response status for %s: %s", url, response.status)
                response.raise_for_status()
                _LOGGER.debug("Pressure POST acknowledged for %s bar; checking read-back", value)
        except Exception as e:
            _LOGGER.error("MaNoSens ZPVR pressure POST failed at %s: %s", url, e)
            return False

        # A successful HTTP POST alone does not prove the pressure was applied.
        # Check only the actual config.required_pressure in NEW device replies.
        # A config-only /get-rs-data packet carries electro_meter settings,
        # not pressure; do not mistake it for confirmation.
        for attempt in range(4):
            if attempt:
                await asyncio.sleep(0.5)
            packet = await self.async_get_data()
            if not isinstance(packet, dict):
                continue
            cfg = packet.get("config")
            required = cfg.get("required_pressure") if isinstance(cfg, dict) else None
            if not isinstance(required, dict):
                continue
            actual = required.get("value")
            unit = required.get("unit")
            if (
                unit == "bar"
                and isinstance(actual, (int, float))
                and not isinstance(actual, bool)
                and math.isfinite(actual)
                and abs(actual - value) <= 0.051
            ):
                _LOGGER.debug("MaNoSens pressure setpoint confirmed by read-back: %s bar", actual)
                return True
        _LOGGER.error(
            "Pressure command POST was acknowledged, but %s bar not confirmed by device read-back",
            value,
        )
        return False

    async def async_set_start_stop(self, value: bool):
        """Set the start/stop state on the device."""
        url = f"{self._base_url}/start-stop"
        payload = {"value": value}
        _LOGGER.debug("Setting start/stop at %s with payload: %s", url, payload)
        try:
            async with self._client.post(url, json=payload, timeout=self._read_timeout) as response:
                _LOGGER.debug("Response status for %s: %s", url, response.status)
                response.raise_for_status()
                _LOGGER.debug("Start/stop HTTP POST acknowledged for %s (physical state not confirmed)", value)
                return True
        except Exception as e:
            _LOGGER.error("Start/stop POST failed on MaNoSens ZPVR at %s: %s", url, e)
            return False
