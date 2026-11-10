"""DataUpdateCoordinator for MaNoSens ZPVR.

The device intermittently replies with config-only packets (data == {}). These
are valid HTTP replies, but not new pump measurements. Retain the last complete
sample only briefly; never treat a real connection failure as fresh data.
"""

from datetime import timedelta
import logging
import math
from time import monotonic

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import MaNoSensZPVRAPI
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

NORMAL_UPDATE_INTERVAL = timedelta(seconds=30)
# With 30-second polling, a config-only packet should not cause a brief
# unavailable state. After 45 seconds without NEW measurement data, signal
# unavailable so that HA safety alarms are not based on stale pump state.
MAX_MEASUREMENT_AGE_SECONDS = 45


class MaNoSensZPVRDataUpdateCoordinator(DataUpdateCoordinator):
    """Fetch pump measurements; distinguish a config packet from a failure."""

    def __init__(self, hass: HomeAssistant, api: MaNoSensZPVRAPI):
        self.api = api
        self._last_measurement = None
        self._last_measurement_at = None
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=NORMAL_UPDATE_INTERVAL,
        )

    def _invalidate(self, message: str):
        """Make later config-only packets unable to resurrect stale measurements."""
        self._last_measurement = None
        self._last_measurement_at = None
        raise UpdateFailed(message)

    async def _async_update_data(self):
        try:
            data = await self.api.async_get_data()
        except Exception as err:
            self._last_measurement = None
            self._last_measurement_at = None
            raise UpdateFailed("Unexpected ZPVR API reading error") from err
        if data is None:
            # An HTTP error, network failure or corrupt JSON is not a new sample.
            self._invalidate("Cannot fetch usable response from MaNoSens ZPVR")
        if not isinstance(data, dict) or not isinstance(data.get("data"), dict):
            self._invalidate("Invalid MaNoSens ZPVR data format")

        if not data["data"]:
            # A config-only response is expected occasionally; do not
            # consider it a new measurement or reset the safety timeout.
            if (
                self._last_measurement is not None
                and self._last_measurement_at is not None
                and monotonic() - self._last_measurement_at < MAX_MEASUREMENT_AGE_SECONDS
            ):
                _LOGGER.debug("Config-only packet; preserving recent ZPVR measurement")
                return self._last_measurement
            self._invalidate("No fresh MaNoSens ZPVR measurements in the last 45 seconds")

        # The house safety automations infer pump operation from the CURRENT
        # entity. A malformed sample must never be accepted as a fresh value.
        for field in ("frequency", "current", "pressure", "temperature"):
            if field in data["data"]:
                item = data["data"][field]
                if not isinstance(item, dict) or "value" not in item:
                    self._invalidate(f"Malformed ZPVR measurement field: {field}")
        if "secret" in data and not isinstance(data["secret"], dict):
            self._invalidate("Malformed ZPVR secret state")
        current = data["data"].get("current")
        value = current.get("value") if isinstance(current, dict) else None
        if (isinstance(value, bool) or not isinstance(value, (int, float))
                or not math.isfinite(value) or value < 0):
            self._invalidate("Invalid or missing ZPVR current measurement")

        # Version retrieval is not safety-critical. Never reject a fresh
        # pump-current measurement just because the /version endpoint fails.
        try:
            version_data = await self.api.async_get_version()
        except Exception:
            _LOGGER.warning("ZPVR version request failed", exc_info=True)
            version_data = None
        if version_data is None:
            _LOGGER.debug("Version endpoint unavailable; keeping previous version")
            version_data = (
                self._last_measurement.get("version", "")
                if self._last_measurement is not None
                else ""
            )

        result = {**data, "version": version_data}
        self._last_measurement = result
        self._last_measurement_at = monotonic()
        return result
