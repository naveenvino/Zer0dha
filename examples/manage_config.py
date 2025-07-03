import logging
from kiteconnect import save_config, load_config

logging.basicConfig(level=logging.DEBUG)

# Example usage:

# Save configuration
api_key = "YOUR_API_KEY"
api_secret = "YOUR_API_SECRET"
access_token = "YOUR_ACCESS_TOKEN"
save_config(api_key, api_secret, access_token)
logging.info("Configuration saved to config.json")

# Load configuration
loaded_config = load_config()
if loaded_config:
    logging.info("Configuration loaded from config.json:")
    logging.info(f"API Key: {loaded_config['api_key']}")
    logging.info(f"API Secret: {loaded_config['api_secret']}")
    logging.info(f"Access Token: {loaded_config['access_token']}")
else:
    logging.info("No configuration found.")
