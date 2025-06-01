import aiohttp
import logging

from homeassistant.helpers.update_coordinator import UpdateFailed

_LOGGER = logging.getLogger(__name__)

class WattrixHost:
    def __init__(self, base_url):
        self._base_url = base_url


    async def async_get_status(self):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self._base_url}/status") as resp:
                    if resp.status != 200:
                        raise UpdateFailed(f"HTTP {resp.status}")
                    resp.raise_for_status()
                    return await resp.json()
        except Exception as e:
            _LOGGER.error(f"Failed to fetch status: {e}")
            return {}

    async def async_get_serial_number(self):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self._base_url}/serial-number") as resp:
                    if resp.status != 200:
                        raise UpdateFailed(f"HTTP {resp.status}")
                    data = await resp.json()
                    return data
        except Exception as err:
            raise UpdateFailed(f"Failed to fetch serial number: {err}")

    async def async_get_version(self):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self._base_url}/version") as resp:
                    if resp.status != 200:
                        raise UpdateFailed(f"HTTP {resp.status}")
                    data = await resp.json()
                    return data
        except Exception as err:
            raise UpdateFailed(f"Failed to fetch serial number: {err}")

    async def async_set_mode(self, mode: str, power_limit_percentage: float, timeout_seconds: int):
        payload = {
            "mode": mode,
            "power_limit_percentage": power_limit_percentage,
            "timeout_seconds": timeout_seconds
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self._base_url}/mode", json=payload) as response:
                    response.raise_for_status()
                    _LOGGER.info(f"Mode set to {mode} with payload {payload}")
                    return True
        except Exception as e:
            _LOGGER.error(f"Failed to set mode: {e}")
            return False