import os
import sys
import pytest
import pytest_asyncio
from kiteconnect import AsyncKiteConnect

sys.path.append(os.path.join(os.path.dirname(__file__), '../helpers'))

@pytest_asyncio.fixture()
async def akiteconnect():
    kite = AsyncKiteConnect(api_key='<API-KEY>', access_token='<ACCESS-TOKEN>')
    kite.root = 'http://kite_trade_test'
    yield kite
    await kite.close()
