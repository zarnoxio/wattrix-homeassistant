import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from custom_components.wattrix.helpers import WattrixDataUpdateCoordinator
from custom_components.wattrix.wattrix_host import WattrixHost

DOMAIN = "wattrix"
_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up Wattrix from YAML (optional)."""
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Wattrix from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    host_str = entry.data["host"]
    host = WattrixHost(host_str)

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