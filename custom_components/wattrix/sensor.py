from homeassistant.components.sensor import SensorEntity
import aiohttp

class WattrixStatusSensor(SensorEntity):
    def __init__(self, host):
        self._attr_name = "Wattrix Power"
        self._host = host
        self._state = None

    async def async_update(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self._host}/status") as resp:
                data = await resp.json()
                self._state = data.get("current_power")

    @property
    def state(self):
        return self._state