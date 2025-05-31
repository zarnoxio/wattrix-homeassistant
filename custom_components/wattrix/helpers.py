import logging
import re
from datetime import timedelta

import aiohttp
import async_timeout

from homeassistant.components.number import NumberEntity
from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed, CoordinatorEntity
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator


_LOGGER = logging.getLogger(__name__)

WATTRIX_MODE_SELECT_DESCRIPTION = SelectEntityDescription(
    key="mode",
    name="Wattrix Mode Selector",
    icon="mdi:toggle-switch",
    options=[
        "ENABLE_ALL_SOURCES",
        "EXPORT_SURPLUS",
        "SOLAR_AND_GRID_ONLY",
        "DISABLED"
    ]
)


async def get_device_serial(host: str) -> str:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{host}/serial-number") as response:
                response.raise_for_status()
                data = await response.json()
                return data.get("serial_number", "unknown")
    except Exception as e:
        _LOGGER.warning(f"Failed to fetch serial number: {e}")
        return "unknown"


class WattrixDataUpdateCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, host):
        self._host = host
        super().__init__(
            hass,
            _LOGGER,
            name="Wattrix data coordinator",
            update_interval=timedelta(seconds=15),
        )
        self.data = {}

    async def _async_update_data(self):
        """Fetch data from Wattrix API."""
        try:
            async with async_timeout.timeout(10):
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{self._host}/status") as response:
                        response.raise_for_status()
                        data = await response.json()
                        return data
        except Exception as err:
            raise UpdateFailed(f"Error fetching data: {err}") from err

class WattrixSensor(SensorEntity):
    def __init__(self, coordinator, name, key, serial_number, unit=None):
        self.coordinator = coordinator
        self._name = name
        self._key = key
        self._unit = unit
        self._attr_unique_id = f"wattrix_{key}_{serial_number}"


    @property
    def name(self):
        return self._name

    @property
    def native_value(self):
        return self.coordinator.data.get(self._key)

    @property
    def native_unit_of_measurement(self):
        return self._unit

    @property
    def available(self):
        return self.coordinator.last_update_success

    async def async_added_to_hass(self):
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )

    @property
    def should_poll(self):
        return False


class WattrixModeSelect(CoordinatorEntity, SelectEntity):
    def __init__(self, coordinator, description: SelectEntityDescription, host, serial_number, get_percentage, get_timeout):
        super().__init__(coordinator)
        self.entity_description = description
        self._host = host
        self._serial_number = serial_number
        self._get_percentage = get_percentage
        self._get_timeout = get_timeout

        self._attr_unique_id = f"wattrix_{description.key}_{serial_number}"
        self._attr_options = description.options
        self._attr_name = description.name

        self._set_initial_option()

    def _set_initial_option(self):
        initial_mode = self.coordinator.data.get(self.entity_description.key)
        if initial_mode in self._attr_options:
            self._attr_current_option = initial_mode
        else:
            if initial_mode:
                _LOGGER.warning(f"Unknown mode received: {initial_mode}, defaulting to first option")
            self._attr_current_option = self._attr_options[0]

    @property
    def current_option(self) -> str | None:
        current = self.coordinator.data.get(self.entity_description.key)
        return current if current in self._attr_options else self._attr_current_option

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success

    async def async_select_option(self, option: str) -> None:
        if option not in self._attr_options:
            _LOGGER.error(f"Invalid option selected: {option}")
            return

        payload = {
            "mode": option,
            "power_limit_percentage": self._get_percentage(),
            "timeout": self._get_timeout()
        }

        _LOGGER.debug(f"Setting mode to {option} with payload: {payload}")

        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.post(f"{self._host}/mode", json=payload) as response:
                    response.raise_for_status()
                    _LOGGER.info(f"Successfully changed mode to {option}")
                    self._attr_current_option = option
                    self.async_write_ha_state()
                    await self.coordinator.async_request_refresh()
        except aiohttp.ClientError as e:
            _LOGGER.error(f"HTTP error when setting mode: {e}")
            raise
        except Exception as e:
            _LOGGER.error(f"Unexpected error when setting mode: {e}")
            raise

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "power_limit_percentage": self.coordinator.data.get("power_limit_percentage", 100.0),
            "timeout": self.coordinator.data.get("timeout"),
            "serial_number": self._serial_number,
        }

    @property
    def current_option(self) -> str | None:
        """Return the currently selected option from coordinator data."""
        current_mode = self.coordinator.data.get("mode")
        return current_mode if current_mode in self._attr_options else self._attr_current_option

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success

    async def async_select_option(self, option: str) -> None:
        """Handle option selection from the UI."""
        if option not in self._attr_options:
            _LOGGER.error(f"Invalid option selected: {option}")
            return

        # Get current values
        percentage = self._get_percentage()
        timeout_val = self._get_timeout()

        payload = {
            "mode": option,
            "power_limit_percentage": percentage,
            "timeout": timeout_val
        }

        _LOGGER.debug(f"Setting mode to {option} with payload: {payload}")

        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.post(f"{self._host}/mode", json=payload) as response:
                    response.raise_for_status()

                    _LOGGER.info(f"Successfully changed mode to {option}")

                    # Update local state immediately for better UX
                    self._attr_current_option = option
                    self.async_write_ha_state()

                    # Refresh coordinator data
                    await self.coordinator.async_request_refresh()

        except aiohttp.ClientError as e:
            _LOGGER.error(f"HTTP error when setting mode to {option}: {e}")
            raise
        except Exception as e:
            _LOGGER.error(f"Unexpected error when setting mode to {option}: {e}")
            raise

    @property
    def extra_state_attributes(self) -> dict:
        """Return additional state attributes."""
        return {
            "power_limit_percentage": self.coordinator.data.get("power_limit_percentage", 100.0),
            "timeout": self.coordinator.data.get("timeout"),
            "serial_number": self._serial_number,
        }

class WattrixPercentageNumber(NumberEntity):
    def __init__(self, host, serial_number):
        self._host = host
        self._attr_name = "Wattrix Mode Percentage"
        self._attr_min_value = 0
        self._attr_max_value = 100
        self._attr_step = 1
        self._attr_native_unit_of_measurement = "%"
        self._attr_unique_id = f"wattrix_mode_percentage_{serial_number}"
        self._value = 100

    @property
    def native_value(self):
        return self._value

    async def async_set_native_value(self, value):
        self._value = value
        self.async_write_ha_state()



class WattrixTimeoutNumber(NumberEntity):
    def __init__(self, host, serial_number):
        self._host = host
        self._attr_name = "Wattrix Mode Timeout"
        self._attr_min_value = 0
        self._attr_max_value = 24*3600
        self._attr_step = 10
        self._attr_native_unit_of_measurement = "s"
        self._attr_unique_id = f"wattrix_mode_timeout_{serial_number}"
        self._value = 300

    @property
    def native_value(self):
        return self._value

    async def async_set_native_value(self, value):
        self._value = value
        self.async_write_ha_state()


class WattrixSerialNumberCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, host):
        self._host = host
        super().__init__(
            hass,
            _LOGGER,
            name="Wattrix Serial Number Coordinator",
            update_interval=timedelta(days=1),  # stačí 1× denne
        )

    async def _async_update_data(self):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self._host}/serial-number") as resp:
                    if resp.status != 200:
                        raise UpdateFailed(f"HTTP {resp.status}")
                    data = await resp.json()
                    return data
        except Exception as err:
            raise UpdateFailed(f"Failed to fetch serial number: {err}")

class WattrixSerialNumberSensor(Entity):
    def __init__(self, coordinator: WattrixSerialNumberCoordinator, serial_number):
        self.coordinator = coordinator
        self._attr_name = "Wattrix Serial Number"
        self._attr_unique_id = f"wattrix_serial_{serial_number}"

    @property
    def state(self):
        return self.coordinator.data.get("serial_number")

    @property
    def available(self):
        return self.coordinator.last_update_success

    async def async_update(self):
        await self.coordinator.async_request_refresh()


