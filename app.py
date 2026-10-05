import os
import json
import requests

from flask import Flask, request

from google import genai

import firebase_admin
from firebase_admin import credentials, firestore


app = Flask(__name__)


# =========================================================
# 1. GEMINI AI
# =========================================================

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

gemini_client = None

if GEMINI_API_KEY:
    try:
        gemini_client = genai.Client(api_key=GEMINI_API_KEY)
        print("Gemini client initialized successfully")
    except Exception as e:
        print("Gemini initialization error:", e)


# =========================================================
# 2. FIREBASE
# =========================================================

FIREBASE_JSON_STR = os.environ.get("FIREBASE_JSON")

db = None

if FIREBASE_JSON_STR and not firebase_admin._apps:

    try:

        cert_dict = json.loads(FIREBASE_JSON_STR)

        cred = credentials.Certificate(cert_dict)

        firebase_admin.initialize_app(cred)

        db = firestore.client()

        print("Firebase initialized successfully")

    except Exception as e:

        print("Firebase Error:", e)


# =========================================================
# 3. WHATSAPP
# =========================================================

VERIFY_TOKEN = "islamiczindagi123"

WHATSAPP_TOKEN = os.environ.get("TOKEN")

PHONE_ID = os.environ.get("PHONE_ID")


# =========================================================
# 4. SEND WHATSAPP MESSAGE
# =========================================================

def send_whatsapp_message(phone_number, text_message):

    try:

        url = (
            f"https://graph.facebook.com/v26.0/"
            f"{PHONE_ID}/messages"
        )

        headers = {
            "Authorization": f"Bearer {WHATSAPP_TOKEN}",
            "Content-Type": "application/json"
        }

        payload = {

            "messaging_product": "whatsapp",

            "to": phone_number,

            "type": "text",

            "text": {
                "body": text_message
            }
        }

        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=30
        )

        print(
            "WhatsApp Send Status:",
            response.status_code
        )

        print(
            "WhatsApp Send Response:",
            response.text
        )

        return response.json()

    except Exception as e:

        print(
            "WhatsApp Send Error:",
            e
        )

        return None


# =========================================================
# 5. HOME
# =========================================================

@app.route("/", methods=["GET"])
def home():

    return "Islamic Zindagi Bot is Live and Running!", 200


# =========================================================
# 6. WEBHOOK VERIFICATION
# =========================================================

@app.route("/webhook", methods=["GET"])
def verify():

    mode = request.args.get("hub.mode")

    token = request.args.get(
        "hub.verify_token"
    )

    challenge = request.args.get(
        "hub.challenge"
    )

    print(
        "Webhook verification request received"
    )

    if (
        mode == "subscribe"
        and token == VERIFY_TOKEN
    ):

        print(
            "Webhook verification successful"
        )

        return challenge, 200

    print(
        "Webhook verification failed"
    )

    return "Forbidden", 403


# =========================================================
# 7. RECEIVE WHATSAPP MESSAGE
# =========================================================

@app.route("/webhook", methods=["POST"])
def receive():

    try:

        data = request.get_json()

        print(
            "Incoming WhatsApp Data:",
            data
        )

        if not data:

            return "EVENT_RECEIVED", 200


        # -------------------------------------------------
        # WhatsApp structure
        # -------------------------------------------------

        entry = data.get("entry", [])

        if not entry:

            return "EVENT_RECEIVED", 200


        changes = entry[0].get(
            "changes",
            []
        )

        if not changes:

            return "EVENT_RECEIVED", 200


        value = changes[0].get(
            "value",
            {}
        )


        messages = value.get(
            "messages",
            []
        )


        # No message = status/update event

        if not messages:

            print(
                "Webhook received without message"
            )

            return "EVENT_RECEIVED", 200


        message = messages[0]


        # -------------------------------------------------
        # Only text messages for now
        # -------------------------------------------------

        if message.get("type") != "text":

            print(
                "Non-text message received"
            )

            return "EVENT_RECEIVED", 200


        sender_phone = message.get(
            "from"
        )

        user_msg = message.get(
            "text",
            {}
        ).get(
            "body",
            ""
        )


        print(
            "User Phone:",
            sender_phone
        )

        print(
            "User Message:",
            user_msg
        )


        # -------------------------------------------------
        # GEMINI
        # -------------------------------------------------

        ai_response = (
            "Assalamu Alaikum! "
            "Islamic Zindagi Bot is working."
        )


        if gemini_client:

            try:

                prompt = f"""
You are Islamic Zindagi,
a respectful Islamic guidance assistant.

Reply in the SAME LANGUAGE used by the user.

Keep the answer concise and easy to understand.

For Islamic questions:
- Do not invent Quran verses.
- Do not invent Hadith.
- Clearly distinguish Quran, Sahih Hadith and general advice.
- If you are not certain about an Islamic reference,
  say that verification is needed.

User message:

{user_msg}
"""


                response = gemini_client.models.generate_content(

                    model="gemini-2.5-flash",

                    contents=prompt
                )


                if response.text:

                    ai_response = response.text


            except Exception as e:

                print(
                    "Gemini Error:",
                    e
                )

                ai_response = (
                    "క్షమించండి. ప్రస్తుతం "
                    "AI సేవలో సమస్య ఉంది. "
                    "కొద్దిసేపటి తర్వాత మళ్లీ ప్రయత్నించండి."
                )


        # -------------------------------------------------
        # SEND WHATSAPP REPLY
        # -------------------------------------------------

        send_whatsapp_message(
            sender_phone,
            ai_response
        )


        # -------------------------------------------------
        # FIREBASE SAVE
        # -------------------------------------------------

        if db:

            try:

                db.collection(
                    "users"
                ).document(
                    sender_phone
                ).collection(
                    "chats"
                ).add({

                    "user_msg": user_msg,

                    "bot_reply": ai_response,

                    "timestamp":
                        firestore.SERVER_TIMESTAMP

                })

            except Exception as e:

                print(
                    "Firebase save error:",
                    e
                )


    except Exception as e:

        print(
            "Webhook Processing Error:",
            e
        )


    return "EVENT_RECEIVED", 200


# =========================================================
# 8. RUN
# =========================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(
            os.environ.get(
                "PORT",
                5000
            )
        )
    )
