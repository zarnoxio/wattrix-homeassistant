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

            _LOGGER.debug(f"Calling Wattrix API with: mode={raw_mode}, "
                          f"power_limit_percentage={power_limit_percentage}, "
                          f"timeout_seconds={timeout_seconds}")

            success = await self._host.async_set_mode(raw_mode, power_limit_percentage, timeout_seconds)

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

        serial_number = await get_device_serial(host._base_url)  # alebo inak podľa implementácie

        refresh_button = WattrixModeReapplyButton(host, coordinator, serial_number)

        async_add_entities([refresh_button])

    except Exception as ex:
        _LOGGER.error(f"Error setting up Wattrix sensors: {ex}")
        raise ex

