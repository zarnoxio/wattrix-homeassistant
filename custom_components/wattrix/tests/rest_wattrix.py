import asyncio

from custom_components.wattrix.sensor import WattrixSensor


async def main():
    host = "http://wattrix.local:8000"
    sensor = WattrixSensor(host, "current_power")
    await sensor.async_update()

asyncio.run(main())