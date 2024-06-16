"""
Mail server config
"""
import requests
from fastapi_mail import FastMail, ConnectionConfig, MessageSchema

from agent.config import CONFIG
import httpx

mail_conf = ConnectionConfig(
    MAIL_USERNAME=CONFIG.mail_username,
    MAIL_PASSWORD=CONFIG.mail_password,
    MAIL_FROM=CONFIG.mail_sender,
    MAIL_PORT=CONFIG.mail_port,
    MAIL_SERVER=CONFIG.mail_server,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
)

mail = FastMail(mail_conf)

mail_key = "c089295bd98a9205826627142e3adb6f-2cc48b29-21f6d3f0"

async def send_simple_message(target_mail,code):
    async with httpx.AsyncClient() as client:
        client.auth
        return requests.post(
            "https://api.mailgun.net/v3/mail.0xbot.org/messages",
            auth=("api", mail_key),
            data={"from": "0xbot-protocl <service@mail.0xbot.org>",
                  "to": [target_mail],
                  "subject": "Welcome to join 0xbot-protocol world",
                  "text": "Welcome to join 0xbot-protocol world ,an AI and blockchain driven world.Your register code is: "+str(code)})

# r =  MailService().send_simple_message()

async def send_verification_email(email: str, token: str):
    """Send user verification email"""
    # Change this later to public endpoint
    url = CONFIG.root_url + "/mail/verify/" + token
    if CONFIG.mail_console:
        print("POST to " + url)
    else:
        message = MessageSchema(
            recipients=[email],
            subject="MyServer Email Verification",
            body="Welcome to MyServer! We just need to verify your email to begin: "
            + url,
        )
        await mail.send_message(message)


async def send_password_reset_email(email: str, token: str):
    """Sends password reset email"""
    # Change this later to public endpoint
    url = CONFIG.root_url + "/register/reset-password/" + token
    if CONFIG.mail_console:
        print("POST to " + url)
    else:
        message = MessageSchema(
            recipients=[email],
            subject="0xbots Password Reset",
            body=f"Click the link to reset your MyServer account password: {url}\nIf you did not request this, please ignore this email",
        )
        await mail.send_message(message)