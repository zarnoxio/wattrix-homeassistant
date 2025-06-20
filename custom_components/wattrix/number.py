from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN
from .helpers import get_device_serial, WattrixPercentageNumber, WattrixTimeoutNumber, WattrixSetpointNumber


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    host = hass.data[DOMAIN][entry.entry_id]["host"]
    serial_number = await host.async_get_serial_number()
    state = await host.async_get_status()
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    async_add_entities([
        WattrixPercentageNumber(host, serial_number, coordinator, state.get("power_limit_percentage", 100)),
        WattrixTimeoutNumber(host, serial_number, coordinator, state.get("timeout_seconds", 900)),
        WattrixSetpointNumber(host, serial_number, coordinator, state.get("setpoint", 200))
    ])