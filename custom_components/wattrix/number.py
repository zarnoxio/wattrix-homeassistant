import logging

from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN
from .helpers import WattrixPercentageNumber, WattrixTimeoutNumber, WattrixSetpointNumber, get_device_serial, WatttrixTemperatureNumber

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    host = hass.data[DOMAIN][entry.entry_id]["host"]
    serial_number = await get_device_serial(host._base_url)
    if serial_number and len(serial_number) > 0:
        _LOGGER.info("Using serial number: %s", serial_number)
    else:
        _LOGGER.error("No serial number found for Wattrix device.")
        return False
    state = await host.async_get_status()
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    async_add_entities([
        WattrixPercentageNumber(host, serial_number, coordinator, state.get("power_limit_percentage", 100)),
        WattrixTimeoutNumber(host, serial_number, coordinator, 900),
        WatttrixTemperatureNumber(host, serial_number, coordinator, "target_temperature_to_set","Wattrix Target Temperature", 30),
        WatttrixTemperatureNumber(host, serial_number, coordinator, "minimal_temperature_to_set","Wattrix Minimal Temperature", 30),
        WatttrixTemperatureNumber(host, serial_number, coordinator, "minimal_temperature_recovery_delta_to_set", "Wattrix Temperature Recovery Delta",2),
        WattrixSetpointNumber(host, serial_number, coordinator, state.get("setpoint", 200))
    ])


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, ["number"])  # ak sú tvoje entity "number"

async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry, hass.helpers.entity_platform.async_add_entities)