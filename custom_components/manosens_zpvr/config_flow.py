"""Config flow for MaNoSens ZPVR."""
import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required("host"): str,
        vol.Required("port", default=80): int,
    }
)


class MaNoSensZPVRConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for MaNoSens ZPVR."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            # Tu sa typicky robí validácia pripojenia cez API
            return self.async_create_entry(title=f"ZPVR ({user_input['host']})", data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return MaNoSensZPVROptionsFlowHandler()


class MaNoSensZPVROptionsFlowHandler(config_entries.OptionsFlow):
    """Handle MaNoSens ZPVR options."""

    # __init__ nie je vôbec potrebné definovať!
    # HA si správu config_entry do triedy injektuje automaticky.

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        return await self.async_step_user(user_input)

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        errors = {}
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Do self.config_entry máme priamy prístup vďaka zdedenej property
        options_schema = vol.Schema(
            {
                vol.Required("host", default=self.config_entry.data.get("host", "")): str,
                vol.Required("port", default=self.config_entry.data.get("port", 80)): int,
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=options_schema, errors=errors
        )