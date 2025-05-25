from homeassistant.core import HomeAssistant
from homeassistant.helpers.discovery import async_load_platform

DOMAIN = "wattrix"

async def async_setup(hass: HomeAssistant, config: dict):
    hass.data[DOMAIN] = {
        "host": config[DOMAIN].get("host", "http://localhost:8000"),
    }

    hass.async_create_task(
        async_load_platform(hass, "sensor", DOMAIN, {}, config)
    )

    return True