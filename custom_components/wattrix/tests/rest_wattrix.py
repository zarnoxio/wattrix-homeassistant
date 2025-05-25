import httpx
import pytest
import aiohttp

BASE_URL = "http://wattrix:8000/api"

@pytest.mark.asyncio
async def test_real_wattrix_status():
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/status")
        assert response.status_code == 200
        data = response.json()
        assert "mode" in data
        assert "current_power" in data