import logging
from datetime import timedelta

import aiohttp
import async_timeout
from homeassistant.components.number import NumberEntity
from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.components.sensor import SensorEntity
from homeassistant.core import callback, HomeAssistant
from homeassistant.helpers import translation
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.translation import async_get_translations
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.update_coordinator import UpdateFailed, CoordinatorEntity



_LOGGER = logging.getLogger(__name__)



WATTRIX_MODE_SELECT_DESCRIPTION = SelectEntityDescription(
    key="mode",
    name="Wattrix Mode Selector",
    icon="mdi:toggle-switch",
    options=[
        "UNRESTRICTED_HEATING",
        "EXPORT_SURPLUS_HEATING",
        "SOLAR_AND_GRID_HEATING",
        "DISABLED"
    ],
    translation_key = "mode_selector"
)


async def get_translated_options(hass: HomeAssistant, domain: str = "wattrix") -> dict:
    """Get translated options for mode selector."""

    # Získaj preklady pre aktuálny jazyk
    translations = await translation.async_get_translations(
        hass=hass,
        language=hass.config.language,
        category="entity",
        integrations=[domain]
    )

    # Vráť preložené možnosti
    translation_key = f"component.{domain}.entity.select.mode_selector.state"

    mode_translations = {}
    for mode in ["UNRESTRICTED_HEATING", "EXPORT_SURPLUS_HEATING", "SOLAR_AND_GRID_HEATING", "DISABLED"]:
        key = f"{translation_key}.{mode.lower()}"
        mode_translations[mode] = translations.get(key, mode)

    return mode_translations


async def get_device_serial(host: str) -> str:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{host}/serial-number") as response:
                response.raise_for_status()
                data = await response.json()
                return data.get("serial_number", None)
    except Exception as e:
        _LOGGER.warning(f"Failed to fetch serial number: {e}")
        return None


class WattrixDataUpdateCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, host):
        self._host = host
        super().__init__(
            hass,
            _LOGGER,
            name="Wattrix data coordinator",
            update_interval=timedelta(seconds=15),
        )

        self.data = {
            "mode": "DISABLED",
            "power_limit_percentage": 100,
            "timeout_seconds": 900,
            "power_limit_percentage_to_set": 100,
            "timeout_seconds_to_set": 900,
            "setpoint": 200,
            "setpoint_to_set": 200,
        }

    async def _async_update_data(self):
        """Fetch data from Wattrix."""
        try:
            async with async_timeout.timeout(10):
                data = await self._host.async_get_status()

                if not data:
                    raise UpdateFailed("No data received from Wattrix")

                if self.data is None:
                    raise  UpdateFailed("Data is not initialized")
                else:
                    self.data.update(data)

                _LOGGER.info(f"Fetched data: {self.data}")

                return self.data

        except Exception as err:
            _LOGGER.warning("Wattrix communication failed: %s", err)
            raise UpdateFailed(f"Error fetching data: {err}") from err


class WattrixSensor(SensorEntity):
    def __init__(self, coordinator, name, key, serial_number, unit=None):
        self.coordinator = coordinator
        self._name = name
        self._key = key
        self._unit = unit
        self._attr_unique_id = f"wattrix_{key}_{serial_number}"
        _LOGGER.debug(f"Wattrix sensor created: self._attr_unique_id {self._attr_unique_id}")


    @property
    def name(self):
        return self._name

    @property
    def native_value(self):
        if self.coordinator.data is None:
            return None
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

class WattrixOnlineSensor(SensorEntity):
    def __init__(self, coordinator, serial_number):
        self.coordinator = coordinator
        self._name = "Wattrix Online Status"
        self._key = "online_status"
        self._attr_unique_id = f"wattrix_online_{serial_number}"

    @property
    def name(self):
        return self._name

    @property
    def native_value(self):
        if self.coordinator:
            return self.coordinator.last_update_success
        else:
            return False

    @property
    def native_unit_of_measurement(self):
        return None

    @property
    def available(self):
        return True

    async def async_added_to_hass(self):
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )

    @property
    def should_poll(self):
        return False

class WattrixModeSelect(CoordinatorEntity, SelectEntity):
    def __init__(self, coordinator, description: SelectEntityDescription, host, serial_number, initial_state, get_percentage, get_timeout, get_setpoint):
        super().__init__(coordinator)
        self._hass = coordinator.hass
        self.entity_description = description
        self._host = host
        self._serial_number = serial_number
        self._get_percentage = get_percentage
        self._get_timeout = get_timeout
        self._get_setpoint = get_setpoint

        self._attr_unique_id = f"wattrix_{description.key}_{serial_number}"
        self._attr_options = description.options
        self._attr_name = description.name

        # Set initial option from raw value to human-readable
        _LOGGER.debug(f"self._attr_options  {self._attr_options}")
        _LOGGER.debug(f"Setting initial state for {self._attr_name} to {initial_state}")
        self._attr_current_option = initial_state
        self._translated_options = {}


    @property
    def options(self) -> list[str]:
        """Return translated options."""
        return list(self._translated_options.values())

    @property
    def current_option(self) -> str:
        """Return current translated option."""
        current_mode = self.coordinator.data.get("mode")
        return self._translated_options.get(current_mode, current_mode)

    async def async_added_to_hass(self):
        """Called when entity is added to hass."""
        await super().async_added_to_hass()

        # Načítaj preklady pri pridaní entity
        await self._load_translations()
        self.async_write_ha_state()

    async def _load_translations(self):
        """Load translations for current language."""
        try:
            self._translated_options = await get_translated_options(self._hass)
            _LOGGER.debug(f"Loaded translations: {self._translated_options}")
        except Exception as err:
            _LOGGER.warning(f"Failed to load translations: {err}")
            # Fallback na anglické názvy
            self._translated_options = {
                "UNRESTRICTED_HEATING": "Unrestricted Heating",
                "EXPORT_SURPLUS_HEATING": "Export Surplus Heating",
                "SOLAR_AND_GRID_HEATING": "Solar and Grid Heating",
                "DISABLED": "Disabled"
            }


    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success

    async def async_select_option(self, option: str) -> None:
        if option not in self._attr_options:
            _LOGGER.error(f"Invalid option selected: {option}")
            return

        power_limit_percentage = self._get_percentage()
        timeout_seconds = self._get_timeout()
        setpoint = self._get_setpoint()

        success = await self._host.async_set_mode(option, power_limit_percentage, timeout_seconds, setpoint)
        if success:
            _LOGGER.info(f"Mode changed to {option}")
            self.coordinator.data.update({self.entity_description.key: option})
            self.async_write_ha_state()
            await self.coordinator.async_request_refresh()
        else:
            _LOGGER.error(f"Failed to set mode to {option}")



    @property
    def extra_state_attributes(self) -> dict:
        return {
            "power_limit_percentage": self.coordinator.data.get("power_limit_percentage", 100.0),
            "timeout_seconds": self.coordinator.data.get("timeout_seconds"),
            "setpoint": self.coordinator.data.get("setpoint"),
            "serial_number": self._serial_number,
        }


class WattrixPercentageNumber(NumberEntity):
    def __init__(self, host, serial_number, coordinator, initial_value=100):
        self._host = host
        self.coordinator = coordinator
        self._attr_name = "Wattrix Mode Percentage"
        self._attr_min_value = 0
        self._attr_max_value = 100
        self._attr_step = 1
        self._attr_native_unit_of_measurement = "%"
        self._attr_unique_id = f"wattrix_mode_percentage_{serial_number}"
        self.coordinator.data["power_limit_percentage_to_set"] = initial_value

    @property
    def native_value(self):
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get("power_limit_percentage_to_set", 100)

    async def async_set_native_value(self, value):
        self.coordinator.data["power_limit_percentage_to_set"] = value

class WattrixTimeoutNumber(NumberEntity):
    def __init__(self, host, serial_number, coordinator, initial_value=300):
        self._host = host
        self.coordinator = coordinator
        self._attr_name = "Wattrix Mode Timeout"
        self._attr_native_min_value = 0
        self._attr_native_max_value = 24 * 3600  # 86400 seconds (24h)
        self._attr_native_step = 10
        self._attr_native_unit_of_measurement = "s"
        self._attr_unique_id = f"wattrix_mode_timeout_{serial_number}"
        self.coordinator.data["timeout_seconds_to_set"] = initial_value

    @property
    def native_value(self):
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get("timeout_seconds_to_set", 300)

    async def async_set_native_value(self, value):
        self.coordinator.data["timeout_seconds_to_set"] = value

class WattrixSetpointNumber(NumberEntity):
    def __init__(self, host, serial_number, coordinator, initial_value=200):
        self._host = host
        self.coordinator = coordinator
        self._attr_name = "Wattrix Regulation Setpoint"
        self._attr_native_min_value = 0
        self._attr_native_max_value = 10000  # 86400 seconds (24h)
        self._attr_native_step = 10
        self._attr_native_unit_of_measurement = "W"
        self._attr_unique_id = f"wattrix_mode_setpoint_{serial_number}"
        self.coordinator.data["setpoint_to_set"] = initial_value

    @property
    def native_value(self):
        return self.coordinator.data.get("setpoint_to_set", 200)

    async def async_set_native_value(self, value):
        self.coordinator.data["setpoint_to_set"] = value

class WattrixSerialNumberCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, host):
        self._host = host
        super().__init__(
            hass,
            _LOGGER,
            name="Wattrix Serial Number Coordinator",
            update_interval=timedelta(seconds=15),
        )

    async def _async_update_data(self):
        """Fetch data from Wattrix."""
        try:
            async with async_timeout.timeout(10):
                data = await self._host.async_get_serial_number()
                return data
        except Exception as err:
            raise UpdateFailed(f"Error fetching data: {err}") from err



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


class WattrixVersionCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, host):
        self._host = host
        super().__init__(
            hass,
            _LOGGER,
            name="Wattrix Version Coordinator",
            update_interval=timedelta(seconds=15),
        )

    async def _async_update_data(self):
        """Fetch data from Wattrix."""
        try:
            async with async_timeout.timeout(10):
                data = await self._host.async_get_version()
                return data
        except Exception as err:
            raise UpdateFailed(f"Error fetching data: {err}") from err

class WattrixDeviceStateCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, host):
        self._host = host
        super().__init__(
            hass,
            _LOGGER,
            name="Wattrix Device State Coordinator",
            update_interval=timedelta(seconds=15),
        )

    async def _async_update_data(self):
        """Fetch data from Wattrix."""
        try:
            async with async_timeout.timeout(10):
                data = await self._host.async_get_device_info()
                return data
        except Exception as err:
            raise UpdateFailed(f"Error fetching data: {err}") from err