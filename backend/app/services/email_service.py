import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import settings

"""
Email Service for sending OTP emails.

How SMTP works:
1. Connect to SMTP server (Gmail, SendGrid, etc.)
2. Authenticate with username/password
3. Compose email (headers + body)
4. Send email
5. Close connection

For Gmail:
- Enable 2-factor authentication
- Generate "App Password" at https://myaccount.google.com/apppasswords
- Use app password in SMTP_PASSWORD env var (NOT your regular Gmail password)
"""


async def send_otp_email(email: str, otp: str, username: str) -> bool:
    """
    Send OTP verification email to user.

    Args:
        email: Recipient email address
        otp: 6-digit OTP code
        username: User's username for personalization

    Returns:
        True if email sent successfully, False otherwise

    How it works:
    1. Create email message with HTML content
    2. Connect to SMTP server over TLS (encrypted)
    3. Login with credentials
    4. Send email
    5. Handle errors gracefully
    """
    try:
        # Create email message
        message = MIMEMultipart("alternative")
        message["Subject"] = "Verify Your TalkTribe Account"
        message["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
        message["To"] = email

        # HTML email body with styling
        # We use HTML for better user experience (colors, formatting, etc.)
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background-color: #4A90E2;
                    color: white;
                    padding: 20px;
                    text-align: center;
                    border-radius: 5px 5px 0 0;
                }}
                .content {{
                    background-color: #f9f9f9;
                    padding: 30px;
                    border-radius: 0 0 5px 5px;
                }}
                .otp-box {{
                    background-color: #fff;
                    border: 2px dashed #4A90E2;
                    padding: 20px;
                    text-align: center;
                    margin: 20px 0;
                    border-radius: 5px;
                }}
                .otp-code {{
                    font-size: 32px;
                    font-weight: bold;
                    color: #4A90E2;
                    letter-spacing: 5px;
                }}
                .footer {{
                    margin-top: 20px;
                    font-size: 12px;
                    color: #666;
                    text-align: center;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to TalkTribe!</h1>
                </div>
                <div class="content">
                    <p>Hi <strong>{username}</strong>,</p>
                    <p>Thank you for registering with TalkTribe. To complete your registration, please verify your email address using the OTP below:</p>

                    <div class="otp-box">
                        <p>Your verification code is:</p>
                        <div class="otp-code">{otp}</div>
                    </div>

                    <p><strong>Important:</strong> This OTP will expire in {settings.OTP_EXPIRE_MINUTES} minutes.</p>
                    <p>If you didn't request this, please ignore this email.</p>

                    <div class="footer">
                        <p>This is an automated email. Please do not reply.</p>
                        <p>&copy; 2026 TalkTribe. All rights reserved.</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """

        # Attach HTML content to message
        html_part = MIMEText(html_content, "html")
        message.attach(html_part)

        # Send email via SMTP
        # STARTTLS = Start TLS encryption after initial connection
        await aiosmtplib.send(
            message,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            start_tls=True,  # Upgrade connection to encrypted TLS
        )

        return True

    except aiosmtplib.SMTPException as e:
        # SMTP-specific errors (connection, auth, sending)
        print(f"SMTP Error sending OTP email to {email}: {str(e)}")
        return False
    except Exception as e:
        # Generic errors
        print(f"Error sending OTP email to {email}: {str(e)}")
        return False
