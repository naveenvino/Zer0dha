import asyncio
import logging
from kiteconnect import AsyncKiteConnect, AsyncKiteTicker, RealtimeMarketDataProcessor

logging.basicConfig(level=logging.INFO)

# Replace with your actual API Key and Access Token
API_KEY = "your_api_key"
ACCESS_TOKEN = "your_access_token"

# Replace with the instrument token you want to monitor (e.g., NIFTY 50)
# You can get instrument tokens using kite.instruments() or kite.ltp()
INSTRUMENT_TOKEN = 256265 # Example: NIFTY 50

# Replace with your Telegram Bot Token and Chat ID for alerts
TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
TELEGRAM_CHAT_ID = "YOUR_TELEGRAM_CHAT_ID"

async def main():
    kite = AsyncKiteConnect(api_key=API_KEY)
    # In a real scenario, you'd generate a session and set the access token
    # For this example, we're assuming you have a valid access token
    kite.set_access_token(ACCESS_TOKEN)

    kws = AsyncKiteTicker(API_KEY, ACCESS_TOKEN)

    # Initialize the real-time data processor with indicator parameters
    processor = RealtimeMarketDataProcessor(
        instrument_token=INSTRUMENT_TOKEN,
        sma_short_window=5,
        sma_long_window=20,
        rsi_window=14,
        macd_fast_period=12,
        macd_slow_period=26,
        macd_signal_period=9,
        bollinger_window=20,
        bollinger_num_std_dev=2,
        stochastic_k_period=14,
        stochastic_d_period=3,
        atr_window=14,
        telegram_bot_token=TELEGRAM_BOT_TOKEN,
        telegram_chat_id=TELEGRAM_CHAT_ID
    )

    async def on_ticks(ws, ticks):
        for tick in ticks:
            await processor.process_tick(tick)

    async def on_connect(ws, response):
        logging.info("Connected to WebSocket. Subscribing to instrument...")
        ws.subscribe([INSTRUMENT_TOKEN])
        ws.set_mode(ws.MODE_FULL, [INSTRUMENT_TOKEN])

    async def on_close(ws, code, reason):
        logging.info(f"Connection closed: {code} - {reason}")

    async def on_error(ws, code, reason):
        logging.error(f"WebSocket error: {code} - {reason}")

    kws.on_ticks = on_ticks
    kws.on_connect = on_connect
    kws.on_close = on_close
    kws.on_error = on_error

    logging.info("Connecting to Kite WebSocket...")
    await kws.connect()

    # Keep the main loop running to receive ticks
    while True:
        await asyncio.sleep(1) # Keep alive

if __name__ == "__main__":
    # Check for placeholder credentials
    if API_KEY == "your_api_key" or ACCESS_TOKEN == "your_access_token":
        logging.warning("Please replace 'your_api_key' and 'your_access_token' with your actual credentials in examples/realtime_data_processing.py")
    if TELEGRAM_BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN" or TELEGRAM_CHAT_ID == "YOUR_TELEGRAM_CHAT_ID":
        logging.warning("Please replace 'YOUR_TELEGRAM_BOT_TOKEN' and 'YOUR_TELEGRAM_CHAT_ID' with your actual Telegram credentials if you want to receive alerts.")

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Real-time data processing stopped by user.")