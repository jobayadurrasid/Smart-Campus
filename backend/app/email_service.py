
#/backend/app/email_service.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from .config import settings
import uuid

def send_welcome_email(email: str, user_id: str, user_fullname: str, user_role: str):
    # Generate password reset token (24h expiry)
    reset_token = str(uuid.uuid4())
    reset_link = f"http://127.0.0.1/reset-password?token={reset_token}"

    # Email content
    subject = "Welcome to Smart Campus"
    body = f"""
    <h2>Account Created Successfully</h2>
    <p> Dear {user_fullname},</br> </p>
    <p>Your account details:</p>
    <ul>
        <li>{user_role} ID: {user_id}</li>
        <li>Temporary Password: 000000</li>
    </ul>
    <p>Please <a href="{reset_link}">reset your password</a> within 24 hours.</p>
    """

    # Create message
    msg = MIMEMultipart()
    msg['From'] = settings.EMAIL_FROM
    msg['To'] = email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'html'))

    # Send email (using MailDev for development)
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        if settings.SMTP_USER and settings.SMTP_PASSWORD:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.send_message(msg)



def send_password_reset_email(email: str, reset_link: str):
    subject = "Password Reset Request"
    body = f"""
    <h2>Password Reset</h2>
    <p>You requested a password reset. This link will expire in 24 hours.</p>
    <p><a href="{reset_link}">Reset Password</a></p>
    <p>If you didn't request this, please ignore this email.</p>
    """
    
    msg = MIMEMultipart()
    msg['From'] = settings.EMAIL_FROM
    msg['To'] = email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'html'))
    
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        server.send_message(msg)