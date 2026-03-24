"""Flask webhook for Twilio WhatsApp bot."""

from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from bot import handle_message
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)


@app.route("/webhook", methods=["POST"])
def webhook():
    incoming_msg = request.form.get("Body", "").strip()
    sender = request.form.get("From", "")  # e.g. whatsapp:+91XXXXXXXXXX

    reply = handle_message(sender, incoming_msg)

    resp = MessagingResponse()
    resp.message(reply)
    return str(resp)


@app.route("/", methods=["GET"])
def health():
    return "Boki WhatsApp Bot is running!", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
