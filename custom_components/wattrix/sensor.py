import logging


from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from custom_components.wattrix import DOMAIN
from custom_components.wattrix.helpers import WattrixDataUpdateCoordinator, WattrixSerialNumberCoordinator, get_device_serial, WattrixSensor

_LOGGER = logging.getLogger(__name__)





async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    try:
        """Set up Wattrix sensors from a config entry."""
        host = hass.data[DOMAIN][entry.entry_id]["host"]

        _LOGGER.debug(f"Setting up Wattrix sensors for host: {host}")


        coordinator = WattrixDataUpdateCoordinator(hass, host)
        await coordinator.async_refresh()

        serial_coordinator = WattrixSerialNumberCoordinator(hass, host)
        await serial_coordinator.async_config_entry_first_refresh()

        serial_number = await get_device_serial(host)

        _LOGGER.debug(f"Setting up Wattrix sensors for serial number: {serial_number}")


        sensors = [
            WattrixSensor(coordinator, "Wattrix Current Power", "current_power", serial_number,"W"),
            WattrixSensor(coordinator, "Wattrix Target Power", "target_power", serial_number,"W"),
            WattrixSensor(coordinator, "Wattrix Power Limit Percentage", "power_limit_percentage",serial_number, "%"),
            WattrixSensor(coordinator, "Wattrix Mode Timeout", "timeout_seconds", serial_number, "s"),
        ]

        async_add_entities(sensors)
    except Exception as ex:
        _LOGGER.error(f"Error setting up Wattrix sensors: {ex}")
        raise ex





