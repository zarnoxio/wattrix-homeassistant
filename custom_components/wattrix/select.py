from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .helpers import WattrixDataUpdateCoordinator, get_device_serial, WattrixPercentageNumber, WattrixTimeoutNumber, WattrixModeSelect, WATTRIX_MODE_SELECT_DESCRIPTION
from .const import DOMAIN

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    host = hass.data[DOMAIN][entry.entry_id]["host"]

    coordinator = WattrixDataUpdateCoordinator(hass, host)
    await coordinator.async_refresh()
    serial_number = await get_device_serial(host)

    percentage = WattrixPercentageNumber(host, serial_number)
    timeout = WattrixTimeoutNumber(host, serial_number)

    entity = WattrixModeSelect(
        coordinator=coordinator,
        description=WATTRIX_MODE_SELECT_DESCRIPTION,
        host=host,
        serial_number=serial_number,
        get_percentage=lambda: percentage.native_value,
        get_timeout=lambda: timeout.native_value
    )

    async_add_entities([entity])