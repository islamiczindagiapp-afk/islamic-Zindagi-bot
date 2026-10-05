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
model = None
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-pro')

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
        print("Firebase Error:", e)

# 3. WhatsApp Setup
VERIFY_TOKEN = "islamiczindagi123"
WHATSAPP_TOKEN = os.environ.get("TOKEN")
PHONE_ID = os.environ.get("PHONE_ID")

def send_whatsapp_message(phone_number, text_message):
    try:
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
        print("WhatsApp Send Response:", response.text)
        return response.json()
    except Exception as e:
        print("WhatsApp Send Error:", e)

@app.route('/', methods=['GET'])
def home():
    return "Islamic Zindagi Bot is Live and Running!"

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        if request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return request.args.get("hub.challenge"), 200
        return "Forbidden", 403

    if request.method == 'POST':
        try:
            data = request.get_json()
            print("Incoming Data:", data)
            value = data['entry'][0]['changes'][0]['value']
            
            if 'messages' in value:
                message_data = value['messages'][0]
                sender_phone = message_data['from']
                
                if 'text' in message_data:
                    user_msg = message_data['text']['body']
                    
                    # Generate AI Reply
                    ai_response = "Assalamu Alaikum! I am your Islamic Zindagi bot."
                    if model:
                        prompt = f"You are an Islamic guide bot named 'Islamic Zindagi'. Reply respectfully, concisely and beautifully in the same language the user asked. User asked: {user_msg}"
                        response = model.generate_content(prompt)
                        ai_response = response.text

                    # Send Reply via WhatsApp
                    send_whatsapp_message(sender_phone, ai_response)

                    # Save to Firebase
                    if db:
                        db.collection("users").document(sender_phone).collection("chats").add({
                            "user_msg": user_msg,
                            "bot_reply": ai_response,
                            "timestamp": firestore.SERVER_TIMESTAMP
                        })
        except Exception as e:
            print("Webhook Processing Error:", e)
            
        return "EVENT_RECEIVED", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
