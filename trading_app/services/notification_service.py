import smtplib
from email.mime.text import MIMEText
import logging
import os
from trading_app.db import get_db

logger = logging.getLogger(__name__)

def send_email_notification(subject: str, body: str):
    """
    Sends an email notification using configured SMTP settings.
    """
    db = get_db()
    config = db.execute('SELECT email_notifications_enabled, email_recipients, smtp_server, smtp_port, smtp_username, smtp_password FROM config').fetchone()

    if not config or not config['email_notifications_enabled']:
        logger.info("Email notifications are disabled or not configured.")
        return

    recipients = config['email_recipients']
    smtp_server = config['smtp_server']
    smtp_port = config['smtp_port']
    smtp_username = config['smtp_username']
    smtp_password = config['smtp_password']

    if not all([recipients, smtp_server, smtp_port, smtp_username, smtp_password]):
        logger.error("Email notification settings are incomplete.")
        return

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = smtp_username
    msg['To'] = recipients

    try:
        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
        logger.info(f"Email notification sent to {recipients} with subject: {subject}")
    except Exception as e:
        logger.error(f"Failed to send email notification: {e}")
