import logging
from homeassistant.helpers.update_coordinator import UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)

class WattrixHost:
    def __init__(self, hass, base_url: str):
        self._base_url = base_url
        self._session = async_get_clientsession(hass)

    async def async_get_status(self):
        try:
            async with self._session.get(f"{self._base_url}/status") as resp:
                if resp.status != 200:
                    raise UpdateFailed(f"HTTP {resp.status}")
                return await resp.json()
        except Exception as e:
            raise UpdateFailed(f"Failed to fetch status: {e}") from e

    async def async_get_sensor(self, sensor_id: str):
        try:
            async with self._session.get(f"{self._base_url}/sensors/{sensor_id}") as resp:
                if resp.status != 200:
                    raise UpdateFailed(f"HTTP {resp.status}")
                return await resp.json()
        except Exception as e:
            _LOGGER.error(f"Failed to fetch sensor {sensor_id}: {e}")
            return None  # lepšie než {}

    async def async_get_serial_number(self):
        try:
            async with self._session.get(f"{self._base_url}/serial-number") as resp:
                if resp.status != 200:
                    raise UpdateFailed(f"HTTP {resp.status}")
                return await resp.json()
        except Exception as e:
            raise UpdateFailed(f"Failed to fetch serial number: {e}") from e

    async def async_get_version(self):
        try:
            async with self._session.get(f"{self._base_url}/version") as resp:
                if resp.status != 200:
                    raise UpdateFailed(f"HTTP {resp.status}")
                return await resp.json()
        except Exception as e:
            raise UpdateFailed(f"Failed to fetch version: {e}") from e

    async def async_get_device_info(self):
        try:
            async with self._session.get(f"{self._base_url}/device-info") as resp:
                if resp.status != 200:
                    raise UpdateFailed(f"HTTP {resp.status}")
                return await resp.json()
        except Exception as e:
            raise UpdateFailed(f"Failed to fetch device info: {e}") from e

    async def async_set_mode(self, mode: str, power_limit_percentage: float, timeout_seconds: int, setpoint: int = None):
        payload = {
            "mode": mode,
            "power_limit_percentage": power_limit_percentage,
            "timeout_seconds": timeout_seconds,
        }
        if setpoint is not None:
            payload["setpoint"] = setpoint

        try:
            async with self._session.post(f"{self._base_url}/mode", json=payload) as resp:
                if resp.status != 200:
                    raise UpdateFailed(f"HTTP {resp.status}")
                _LOGGER.info(f"Mode set to {mode} with payload {payload}")
                return True
        except Exception as e:
            _LOGGER.error(f"Failed to set mode: {e}")
            return False

    async def async_get_schedule(self, hours: int = 24):
        try:
            async with self._session.get(f"{self._base_url}/schedule?hours={hours}") as resp:
                if resp.status != 200:
                    raise UpdateFailed(f"HTTP {resp.status}")
                return await resp.json()
        except Exception as e:
            raise UpdateFailed(f"Failed to fetch schedule: {e}") from e
