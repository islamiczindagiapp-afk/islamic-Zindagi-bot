import os
import json
import requests
from flask import Flask, request
import google.generativeai as genai
import firebase_admin
from firebase_admin import credentials, firestore

app = Flask(__name__)

# 1. Gemini AI Setup
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')

# 2. Firebase Database Setup
FIREBASE_JSON_STR = os.environ.get("FIREBASE_JSON")
db = None
if FIREBASE_JSON_STR and not firebase_admin._apps:
    try:
        cert_dict = json.loads(FIREBASE_JSON_STR)
        cred = credentials.Certificate(cert_dict)
        firebase_admin.initialize_app(cred)
        db = firestore.client()
    except Exception as e:
        print("Firebase Setup Error:", e)

# 3. WhatsApp Setup
VERIFY_TOKEN = "islamiczindagi123"
WHATSAPP_TOKEN = os.environ.get("TOKEN")
PHONE_ID = os.environ.get("PHONE_ID")

def send_whatsapp_message(phone_number, text_message):
    url = f"https://graph.facebook.com/v17.0/{PHONE_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": phone_number,
        "type": "text",
        "text": {"body": text_message}
    }
    response = requests.post(url, headers=headers, json=payload)
    return response.json()

@app.route('/', methods=['GET'])
def home():
    return "Islamic Zindagi Bot is Live!"

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    # Verification for Meta
    if request.method == 'GET':
        if request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return request.args.get("hub.challenge"), 200
        return "Forbidden", 403

    # Receiving User Messages
    if request.method == 'POST':
        data = request.get_json()
        try:
            value = data['entry'][0]['changes'][0]['value']
            
            # Check if it's an actual message from a user
            if 'messages' in value:
                message_data = value['messages'][0]
                sender_phone = message_data['from']
                
                # Check if message is text
                if 'text' in message_data:
                    user_msg = message_data['text']['body']
                    
                    # Generate AI Reply
                    ai_response = "Assalamu Alaikum! Network error, please try again."
                    if GEMINI_API_KEY:
                        prompt = f"You are an Islamic guide bot named 'Islamic Zindagi'. Reply respectfully and beautifully. User asked: {user_msg}"
                        response = model.generate_content(prompt)
                        ai_response = response.text

                    # Send Reply to User
                    send_whatsapp_message(sender_phone, ai_response)

                    # Save to Firebase Firestore
                    if db:
                        db.collection("users").document(sender_phone).collection("chats").add({
                            "user_msg": user_msg,
                            "bot_reply": ai_response,
                            "timestamp": firestore.SERVER_TIMESTAMP
                        })

        except Exception as e:
            print("Message Processing Error:", e)
            
        return "EVENT_RECEIVED", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
