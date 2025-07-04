import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .helpers import WattrixDataUpdateCoordinator, get_device_serial, WattrixModeSelect, WATTRIX_MODE_SELECT_DESCRIPTION


_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    host = hass.data[DOMAIN][entry.entry_id]["host"]

    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    await coordinator.async_refresh()

    serial_number = await get_device_serial(host._base_url)
    if serial_number and len(serial_number) > 0:
        _LOGGER.info("Using serial number: %s", serial_number)
    else:
        _LOGGER.error("No serial number found for Wattrix device.")
        return False

    state = await host.async_get_status()

    entity = WattrixModeSelect(
        coordinator=coordinator,
        description=WATTRIX_MODE_SELECT_DESCRIPTION,
        host=host,
        serial_number=serial_number,
        initial_state=state.get("mode", "UNRESTRICTED_HEATING"),
        get_percentage=lambda: coordinator.data.get("power_limit_percentage_to_set", 100),
        get_timeout=lambda: coordinator.data.get("timeout_seconds_to_set", 900),
        get_setpoint=lambda: coordinator.data.get("setpoint_to_set", None)
    )

    async_add_entities([entity])

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, ["select"])  # alebo "sensor" podľa typu entity

async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry, hass.helpers.entity_platform.async_add_entities)