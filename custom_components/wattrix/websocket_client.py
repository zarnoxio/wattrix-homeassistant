import asyncio
import websockets
import json

class WattrixWebSocketClient:
    def __init__(self, hass, host, on_event_callback):
        self._host = host
        self._hass = hass
        self._on_event_callback = on_event_callback

    async def listen(self):
        uri = f"ws://{self._host}:8765"
        async with websockets.connect(uri) as ws:
            async for message in ws:
                data = json.loads(message)
                self._hass.async_create_task(self._on_event_callback(data))