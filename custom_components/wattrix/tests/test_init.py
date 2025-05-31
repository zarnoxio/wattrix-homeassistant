import asyncio
import logging
from custom_components.wattrix import async_setup

# Nastav logging pre lepšiu viditeľnosť
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

DOMAIN = "wattrix"

class MockHass:
    """Mockovaný objekt hass, ktorý simuluje Home Assistant."""
    def __init__(self):
        self.data = {}
        self.config = {
            DOMAIN: {
                "host": "http://localhost:8000"  # <- toto je kľúčové
            }
        }
        self.states = {}
        self.services = {}
        self.bus = None
        self.loop = asyncio.get_event_loop()

    def async_create_task(self, coro):
        return asyncio.create_task(coro)  # Spustí async úlohu ako Home Assistant

async def main():
    hass = MockHass()

    # Volaj async_setup() priamo z __init__.py
    result = await async_setup(hass, hass.config)

    if result:
        logger.info("✅ Wattrix setup completed successfully.")
    else:
        logger.error("❌ Wattrix setup failed.")

if __name__ == "__main__":
    asyncio.run(main())