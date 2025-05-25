import pytest
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

@pytest.mark.asyncio
async def test_plugin_setup(hass: HomeAssistant):
    # Simuluj načítanie konfigurácie pluginu
    config = {
        "wattrix": {
            "host": "http://wattrix.local:8000",
            "token": "test_token"
        }
    }

    # Setup integrácie s konfiguráciou
    success = await async_setup_component(hass, "wattrix", config)
    assert success

    # Skontroluj, či sa komponent správne zaregistroval
    assert "wattrix" in hass.config.components