import json
import os

CONFIG_FILE = "config.json"

def save_config(api_key: str, api_secret: str, access_token: str):
    """
    Saves API configuration to a JSON file.
    """
    config = {
        "api_key": api_key,
        "api_secret": api_secret,
        "access_token": access_token
    }
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

def load_config():
    """
    Loads API configuration from a JSON file.
    """
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return None
