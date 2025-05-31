import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import aiohttp_client
import logging

_LOGGER = logging.getLogger(__name__)

DOMAIN = "wattrix"

CONFIG_SCHEMA = vol.Schema({
    vol.Required("host"): str
})

_LOGGER.info("WattrixConfigFlow loaded")

class WattrixConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    def __init__(self):
        self._host = None

    async def async_step_user(self, user_input=None):
        _LOGGER.warning("async_step_user called!")

        errors = {}

        if user_input is not None:
            self._host = user_input["host"]

            # Tu môžeš otestovať pripojenie k API Wattrix
            try:
                session = aiohttp_client.async_get_clientsession(self.hass)
                async with session.get(f"{self._host}/version") as response:
                    if response.status != 200:
                        errors["base"] = f"cannot_connect ({response.status})"
                    else:
                        return self.async_create_entry(title="Wattrix", data=user_input)
            except Exception as e:
                errors["base"] = "cannot_connect"
                _LOGGER.error(f"Error connecting to Wattrix API: {e}", exc_info=True)


        return self.async_show_form(
            step_id="user",
            data_schema=CONFIG_SCHEMA,
            errors=errors
        )