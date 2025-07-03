import requests

def send_telegram_message(bot_token: str, chat_id: str, message: str) -> bool:
    """
    Sends a message to a Telegram chat via a bot.

    :param bot_token: The Telegram bot token.
    :param chat_id: The chat ID to send the message to.
    :param message: The message text to send.
    :return: True if the message was sent successfully, False otherwise.
    """
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML" # Use HTML for basic formatting
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.json()["ok"]
    except requests.exceptions.RequestException as e:
        print(f"Error sending Telegram message: {e}")
        return False
