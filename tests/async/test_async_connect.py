import pytest
import utils

@pytest.mark.asyncio
async def test_positions(akiteconnect, monkeypatch):
    async def fake_get(*args, **kwargs):
        return utils.get_json_response("portfolio.positions")
    monkeypatch.setattr(akiteconnect, "_get", fake_get)
    pos = await akiteconnect.positions()
    assert isinstance(pos, dict)

@pytest.mark.asyncio
async def test_profile(akiteconnect, monkeypatch):
    async def fake_get(*args, **kwargs):
        return utils.get_json_response("user.profile")
    monkeypatch.setattr(akiteconnect, "_get", fake_get)
    profile = await akiteconnect.profile()
    assert isinstance(profile, dict)

from kiteconnect.async_ticker import AsyncKiteTicker
import websockets

@pytest.mark.asyncio
async def test_async_ticker_connect(monkeypatch):
    called = {}
    async def fake_connect(url):
        called['url'] = url
        class Dummy:
            async def send(self, *a, **kw): pass
            async def __aiter__(self):
                if False:
                    yield None
            async def close(self):
                pass
        return Dummy()
    monkeypatch.setattr(websockets, 'connect', fake_connect)
    ticker = AsyncKiteTicker('key', 'token', root='ws://example.com')
    await ticker.connect()
    assert called['url'].startswith('ws://example.com')
