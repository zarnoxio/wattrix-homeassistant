from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN
from .helpers import get_device_serial, WattrixPercentageNumber, WattrixTimeoutNumber


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    host = hass.data[DOMAIN][entry.entry_id]["host"]
    serial_number = await get_device_serial(host)

    async_add_entities([
        WattrixPercentageNumber(host, serial_number),
        WattrixTimeoutNumber(host, serial_number)
    ])