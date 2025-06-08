import logging


from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from custom_components.wattrix import DOMAIN
from custom_components.wattrix.helpers import WattrixDataUpdateCoordinator, WattrixSerialNumberCoordinator, get_device_serial, WattrixSensor, WattrixVersionCoordinator, WattrixDeviceStateCoordinator

_LOGGER = logging.getLogger(__name__)





async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    """Set up Wattrix sensors from a config entry."""
    try:
        host = hass.data[DOMAIN][entry.entry_id]["host"]
        coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

        serial_coordinator = WattrixSerialNumberCoordinator(hass, host)
        await serial_coordinator.async_config_entry_first_refresh()

        version_coordinator = WattrixVersionCoordinator(hass, host)
        await version_coordinator.async_config_entry_first_refresh()

        device_info_coordinator = WattrixDeviceStateCoordinator(hass, host)
        await device_info_coordinator.async_config_entry_first_refresh()

        serial_number = await host.async_get_serial_number()

        sensors = [
            WattrixSensor(coordinator, "Wattrix Current Power", "current_power", serial_number, "W"),
            WattrixSensor(coordinator, "Wattrix Target Power", "target_power", serial_number, "W"),
            WattrixSensor(coordinator, "Wattrix Power Limit Percentage", "power_limit_percentage", serial_number, "%"),
            WattrixSensor(coordinator, "Wattrix Mode Timeout", "timeout_seconds", serial_number, "s"),
            WattrixSensor(serial_coordinator, "Wattrix Serial Number", "serial_number", serial_number, ),
            WattrixSensor(version_coordinator, "Wattrix Version", "version", serial_number, ),
            WattrixSensor(device_info_coordinator, "Wattrix Internal Temperature", "thermal_sensor", serial_number, "°C"),
        ]

        async_add_entities(sensors)

    except Exception as ex:
        _LOGGER.error(f"Error setting up Wattrix sensors: {ex}")
        raise ex





