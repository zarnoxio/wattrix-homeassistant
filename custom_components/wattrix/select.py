from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .helpers import WattrixDataUpdateCoordinator, get_device_serial, WattrixModeSelect, WATTRIX_MODE_SELECT_DESCRIPTION


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    host = hass.data[DOMAIN][entry.entry_id]["host"]

    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    await coordinator.async_refresh()

    serial_number = await host.async_get_serial_number()
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