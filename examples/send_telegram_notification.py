import logging
from kiteconnect import send_telegram_message

logging.basicConfig(level=logging.DEBUG)

# Replace with your actual bot token and chat ID
TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
TELEGRAM_CHAT_ID = "YOUR_TELEGRAM_CHAT_ID"

if TELEGRAM_BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN" or TELEGRAM_CHAT_ID == "YOUR_TELEGRAM_CHAT_ID":
    logging.warning("Please replace YOUR_TELEGRAM_BOT_TOKEN and YOUR_TELEGRAM_CHAT_ID with your actual credentials in examples/send_telegram_notification.py")
else:
    try:
        message = "Hello from KiteConnect CLI! This is a test notification."
        success = send_telegram_message(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, message)

        if success:
            logging.info("Telegram message sent successfully!")
        else:
            logging.error("Failed to send Telegram message.")

    except Exception as e:
        logging.error(f"An error occurred while sending Telegram message: {e}")
