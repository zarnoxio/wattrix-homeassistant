import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from custom_components.wattrix import DOMAIN
from custom_components.wattrix.helpers import get_device_serial

_LOGGER = logging.getLogger(__name__)

class WattrixModeReapplyButton(ButtonEntity):
    def __init__(self, host, coordinator: DataUpdateCoordinator,  serial_number, name: str = "Re-apply Wattrix Mode") -> None:
        self._coordinator = coordinator
        self._host = host
        self._attr_name = name
        self._attr_icon = "mdi:reload"
        self._attr_unique_id = f"wattrix_mode_reapply_{serial_number}"

    async def async_press(self) -> None:
        # Získame aktuálny mód z koordinátora (alebo iného zdroja)
        current_mode = self._coordinator.data.get("mode")
        if current_mode:
            await self._call_wattrix_api(current_mode)

    async def _call_wattrix_api(self, mode: str):

        try:
            raw_mode = self._coordinator.data.get("raw_mode_to_set", mode)
            power_limit_percentage = self._coordinator.data.get("power_limit_percentage_to_set", 100.0)
            timeout_seconds = self._coordinator.data.get("timeout_seconds_to_set", 0)
            setpoint = self._coordinator.data.get("setpoint_to_set", None)

            _LOGGER.debug(f"Calling Wattrix API with: mode={raw_mode}, "
                          f"power_limit_percentage={power_limit_percentage}, "
                          f"timeout_seconds={timeout_seconds}"
                          f", setpoint={setpoint}")

            success = await self._host.async_set_mode(raw_mode, power_limit_percentage, timeout_seconds, setpoint)

            if success:
                _LOGGER.info(f"Wattrix mode successfully set to {raw_mode}")
                await self._coordinator.async_request_refresh()
                return True
            else:
                _LOGGER.warning(f"Wattrix mode change to {raw_mode} failed without exception.")
                return False

        except Exception as e:
            _LOGGER.error(f"Exception during Wattrix API call for mode {mode}: {e}")
            return False


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    """Set up Wattrix sensors from a config entry."""
    try:
        host = hass.data[DOMAIN][entry.entry_id]["host"]
        coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

        serial_number = await get_device_serial(host._base_url)
        if serial_number and len(serial_number) > 0:
            _LOGGER.info("Using serial number: %s", serial_number)
        else:
            _LOGGER.error("No serial number found for Wattrix device.")
            return False

        refresh_button = WattrixModeReapplyButton(host, coordinator, serial_number)

        async_add_entities([refresh_button])

    except Exception as ex:
        _LOGGER.error(f"Error setting up Wattrix sensors: {ex}")
        raise ex


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, ["button"])

async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry, hass.helpers.entity_platform.async_add_entities)
