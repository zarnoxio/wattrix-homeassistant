from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from custom_components.wattrix.helpers import WattrixDataUpdateCoordinator
from custom_components.wattrix.wattrix_host import WattrixHost

DOMAIN = "wattrix"

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up Wattrix from YAML (optional)."""
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Wattrix from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    host_str = entry.data["host"]
    host = WattrixHost(host_str)

    coordinator = WattrixDataUpdateCoordinator(hass, host)
    await coordinator.async_refresh()

    hass.data[DOMAIN][entry.entry_id] = {
        "host": host,
        "coordinator": coordinator,
    }

    # Forward setup to sensor and select platforms
    await hass.config_entries.async_forward_entry_setups(entry,  ["sensor", "number", "select", "button"])

    return True