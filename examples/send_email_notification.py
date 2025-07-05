import logging
from kiteconnect.notifications import send_email

logging.basicConfig(level=logging.DEBUG)

# --- Email Configuration ---
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "your_email@gmail.com"
SMTP_PASS = "your_password"
TO_EMAIL = "recipient_email@example.com"
FROM_EMAIL = "your_email@gmail.com"

# --- Send an email notification ---
try:
    send_email(
        subject="Test Email Notification",
        body="This is a test email notification from the Kite Connect API.",
        to_email=TO_EMAIL,
        from_email=FROM_EMAIL,
        smtp_server=SMTP_SERVER,
        smtp_port=SMTP_PORT,
        smtp_user=SMTP_USER,
        smtp_pass=SMTP_PASS,
    )
    logging.info("Email notification sent successfully.")
except Exception as e:
    logging.error(f"Failed to send email notification: {e}")
