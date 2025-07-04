import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from custom_components.wattrix.helpers import WattrixDataUpdateCoordinator, get_device_serial
from custom_components.wattrix.wattrix_host import WattrixHost

DOMAIN = "wattrix"
_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "select", "number"]

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up Wattrix from YAML (optional)."""
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Wattrix from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    host = entry.data["host"]
    serial_number = await get_device_serial(host)
    if serial_number and len(serial_number) > 0:
        _LOGGER.info("Using serial number: %s", serial_number)
    else:
        _LOGGER.error("No serial number found for Wattrix device.")
        return False

    host = WattrixHost(host)

    coordinator = WattrixDataUpdateCoordinator(hass, host)
    try:
        await coordinator.async_refresh()
    except Exception as e:
        # Log warning and return False so HA will retry later
        _LOGGER.warning("Wattrix not available during startup: %s", e)
        return False  # HA will retry setup automatically later

    hass.data[DOMAIN][entry.entry_id] = {
        "host": host,
        "coordinator": coordinator,
    }

    # Forward setup to sensor and select platforms
    await hass.config_entries.async_forward_entry_setups(entry,  ["sensor", "number", "select", "button"])

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok

async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)