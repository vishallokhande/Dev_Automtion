import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import logging

logger = logging.getLogger(__name__)

def send_otp_email(to_email: str, otp_code: str):
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")

    if not smtp_user or not smtp_password:
        logger.warning("SMTP_USERNAME or SMTP_PASSWORD not set. Simulating email instead.")
        print(f"========== EMAIL SIMULATION ==========")
        print(f"To: {to_email}")
        print(f"Subject: Your AutoApply-Ops Login Code")
        print(f"Code: {otp_code} (Expires in 10 minutes)")
        print(f"======================================")
        return

    try:
        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = to_email
        msg['Subject'] = "Your AutoApply-Ops Login Code"

        body = f"""
        Hello,

        Your one-time verification code for AutoApply-Ops is: {otp_code}

        This code will expire in 10 minutes.

        If you did not request this code, please ignore this email.
        """
        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
            logger.info(f"Successfully sent OTP email to {to_email}")
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {str(e)}")
        # Still raise so the user knows
        raise Exception("Failed to send email.")
