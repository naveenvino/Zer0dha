import asyncio
import logging
from collections import deque
from typing import Dict, Callable, Optional
import pandas as pd

from kiteconnect.technical_indicators import calculate_sma, calculate_rsi, calculate_macd, calculate_bollinger_bands, calculate_stochastic_oscillator, calculate_atr
from kiteconnect.notifications import send_telegram_message

logger = logging.getLogger(__name__)

class RealtimeMarketDataProcessor:
    """
    Processes real-time market data to calculate indicators and generate signals.
    """
    def __init__(
        self,
        instrument_token: int,
        sma_short_window: int = 5,
        sma_long_window: int = 20,
        rsi_window: int = 14,
        macd_fast_period: int = 12,
        macd_slow_period: int = 26,
        macd_signal_period: int = 9,
        bollinger_window: int = 20,
        bollinger_num_std_dev: int = 2,
        stochastic_k_period: int = 14,
        stochastic_d_period: int = 3,
        atr_window: int = 14,
        telegram_bot_token: Optional[str] = None,
        telegram_chat_id: Optional[str] = None,
        alert_callback: Optional[Callable[[str], None]] = None
    ):
        self.instrument_token = instrument_token
        self.sma_short_window = sma_short_window
        self.sma_long_window = sma_long_window
        self.rsi_window = rsi_window
        self.macd_fast_period = macd_fast_period
        self.macd_slow_period = macd_slow_period
        self.macd_signal_period = macd_signal_period
        self.bollinger_window = bollinger_window
        self.bollinger_num_std_dev = bollinger_num_std_dev
        self.stochastic_k_period = stochastic_k_period
        self.stochastic_d_period = stochastic_d_period
        self.atr_window = atr_window
        self.telegram_bot_token = telegram_bot_token
        self.telegram_chat_id = telegram_chat_id
        self.alert_callback = alert_callback

        # Max length should accommodate the longest indicator period
        max_len = max(sma_long_window, rsi_window, macd_slow_period, bollinger_window, stochastic_k_period, atr_window)
        self.data_history = deque(maxlen=max_len)

        self.last_sma_short = None
        self.last_sma_long = None
        self.position = "FLAT" # Can be "LONG", "SHORT", "FLAT"

    async def process_tick(self, tick: Dict):
        """
        Processes a single tick of real-time data.
        """
        # Only process ticks for the specified instrument
        if tick['instrument_token'] != self.instrument_token:
            return

        # Append new tick data. Ensure it has 'high', 'low', 'close' for indicators.
        # For live ticks, 'last_price' can be used as 'close'. 'high' and 'low' might need to be tracked per candle.
        # For simplicity, we'll use last_price for all for now.
        processed_tick = {
            'date': pd.to_datetime(tick['timestamp']),
            'open': tick['last_price'], # Placeholder
            'high': tick['last_price'], # Placeholder
            'low': tick['last_price'], # Placeholder
            'close': tick['last_price'],
            'volume': tick.get('volume', 0) # Use get to handle missing volume
        }
        self.data_history.append(processed_tick)

        # Ensure enough data for longest indicator
        if len(self.data_history) < self.data_history.maxlen:
            logger.info(f"Collecting data for {self.instrument_token}. Current size: {len(self.data_history)}")
            return

        df = pd.DataFrame(list(self.data_history))
        df = df.set_index('date')

        # Extract close prices for SMA and RSI
        close_prices = df['close']

        # Calculate indicators
        current_sma_short = calculate_sma(close_prices, self.sma_short_window)
        current_sma_long = calculate_sma(close_prices, self.sma_long_window)
        current_rsi = calculate_rsi(close_prices, self.rsi_window)
        
        macd_data = calculate_macd(df, self.macd_fast_period, self.macd_slow_period, self.macd_signal_period)
        current_macd = macd_data['MACD']
        current_signal_line = macd_data['Signal_Line']
        
        bollinger_data = calculate_bollinger_bands(df, self.bollinger_window, self.bollinger_num_std_dev)
        current_middle_band = bollinger_data['Middle_Band']
        current_upper_band = bollinger_data['Upper_Band']
        current_lower_band = bollinger_data['Lower_Band']
        
        stochastic_data = calculate_stochastic_oscillator(df, self.stochastic_k_period, self.stochastic_d_period)
        current_k_percent = stochastic_data['K_Percent']
        current_d_percent = stochastic_data['D_Percent']
        
        current_atr = calculate_atr(df, self.atr_window)

        logger.info(f"Instrument: {self.instrument_token}, LTP: {tick['last_price']:.2f}, SMA_S: {current_sma_short:.2f}, SMA_L: {current_sma_long:.2f}, RSI: {current_rsi:.2f}, MACD: {current_macd:.2f}, Signal: {current_signal_line:.2f}, BB_Mid: {current_middle_band:.2f}, BB_Upper: {current_upper_band:.2f}, BB_Lower: {current_lower_band:.2f}, %K: {current_k_percent:.2f}, %D: {current_d_percent:.2f}, ATR: {current_atr:.2f}")

        # Generate signals (example: SMA crossover)
        if self.last_sma_short and self.last_sma_long:
            # Golden Cross (Buy Signal)
            if current_sma_short > current_sma_long and self.last_sma_short <= self.last_sma_long:
                if self.position != "LONG":
                    signal = f"BUY Signal for {self.instrument_token}! Short SMA ({current_sma_short:.2f}) crossed above Long SMA ({current_sma_long:.2f})."
                    logger.info(signal)
                    await self._send_alert(signal)
                    self.position = "LONG"
            # Death Cross (Sell Signal)
            elif current_sma_short < current_sma_long and self.last_sma_short >= self.last_sma_long:
                if self.position != "SHORT":
                    signal = f"SELL Signal for {self.instrument_token}! Short SMA ({current_sma_short:.2f}) crossed below Long SMA ({current_sma_long:.2f})."
                    logger.info(signal)
                    await self._send_alert(signal)
                    self.position = "SHORT"

        self.last_sma_short = current_sma_short
        self.last_sma_long = current_sma_long

    async def _send_alert(self, message: str):
        """
        Sends an alert via Telegram or a custom callback.
        """
        if self.alert_callback:
            self.alert_callback(message)
        elif self.telegram_bot_token and self.telegram_chat_id:
            await asyncio.to_thread(send_telegram_message, self.telegram_bot_token, self.telegram_chat_id, message)
        else:
            logger.warning(f"No alert mechanism configured. Message: {message}")
