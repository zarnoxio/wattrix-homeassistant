import logging


from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from custom_components.wattrix import DOMAIN
from custom_components.wattrix.helpers import WattrixDataUpdateCoordinator, WattrixSerialNumberCoordinator, get_device_serial, WattrixSensor, WattrixVersionCoordinator, WattrixDeviceStateCoordinator, \
    WattrixOnlineSensor

_LOGGER = logging.getLogger(__name__)





async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    """Set up Wattrix sensors from a config entry."""
    host = hass.data[DOMAIN][entry.entry_id]["host"]
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]


    serial_number = await get_device_serial(host._base_url)
    if serial_number and len(serial_number) > 0:
        _LOGGER.info("Using serial number: %s", serial_number)
    else:
        _LOGGER.error("No serial number found for Wattrix device.")
        return False

    serial_coordinator = WattrixSerialNumberCoordinator(hass, host)
    version_coordinator = WattrixVersionCoordinator(hass, host)
    device_info_coordinator = WattrixDeviceStateCoordinator(hass, host)


    sensors = [
        WattrixSensor(coordinator, "Wattrix Current Power", "current_power", serial_number, "W"),
        WattrixSensor(coordinator, "Wattrix Target Power", "target_power", serial_number, "W"),
        WattrixSensor(coordinator, "Wattrix Power Limit Percentage", "power_limit_percentage", serial_number, "%"),
        WattrixSensor(coordinator, "Wattrix Mode Timeout", "timeout_seconds", serial_number, "s"),
        WattrixSensor(coordinator, "Wattrix Mode Setpoint", "setpoint", serial_number, "W"),
        WattrixSensor(coordinator, "Wattrix Temperature Sensor", "temperature_sensor", serial_number, "°C"),
        WattrixSensor(coordinator, "Wattrix Heating Override Sensor", "heating_override", serial_number),
        WattrixSensor(serial_coordinator, "Wattrix Serial Number", "serial_number", serial_number),
        WattrixSensor(version_coordinator, "Wattrix Version", "version", serial_number),
        WattrixSensor(device_info_coordinator, "Wattrix Internal Temperature", "thermal_sensor", serial_number, "°C"),
        WattrixOnlineSensor(coordinator, serial_number),
    ]

    async_add_entities(sensors)



async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, ["sensor"])


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry, hass.helpers.entity_platform.async_add_entities)



