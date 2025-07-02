import asyncio
import json
import logging
import websockets

log = logging.getLogger(__name__)

class AsyncKiteTicker:
    def __init__(self, api_key, access_token, user_id=None, root="wss://ws.kite.trade", debug=False):
        self.api_key = api_key
        self.access_token = access_token
        self.user_id = user_id
        self.root = root
        self.debug = debug
        self.ws = None
        self.on_ticks = None
        self.on_connect = None
        self.on_close = None
        self.on_error = None

    async def connect(self):
        url = f"{self.root}?api_key={self.api_key}&access_token={self.access_token}"
        self.ws = await websockets.connect(url)
        if self.on_connect:
            await self.on_connect(self, None)
        asyncio.create_task(self._run())

    async def _run(self):
        try:
            async for message in self.ws:
                if self.on_ticks:
                    try:
                        data = json.loads(message)
                    except Exception:
                        data = message
                    await self.on_ticks(self, data)
        except Exception as e:
            if self.on_error:
                await self.on_error(self, e)
        finally:
            if self.on_close:
                await self.on_close(self, 1000, "closed")

    async def send(self, data):
        if self.ws:
            await self.ws.send(data)

    async def subscribe(self, tokens):
        await self.send(json.dumps({"a": "subscribe", "v": tokens}))

    async def set_mode(self, mode, tokens):
        await self.send(json.dumps({"a": "mode", "v": [mode, tokens]}))

    async def close(self):
        if self.ws:
            await self.ws.close()
