from twilio.rest import Client
import os

def send_whatsapp_alert(message, to_number):
    account_sid = os.getenv("TWILIO_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    from_number = os.getenv("TWILIO_WHATSAPP_FROM")

    client = Client(account_sid, auth_token)

    client.messages.create(
        from_=f'whatsapp:{from_number}',
        body=message,
        to=f'whatsapp:{to_number}'
    )
