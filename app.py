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
        print("Firebase Connected Successfully!")
    except Exception as e:
        print("Firebase Setup Error:", e)

# 3. WhatsApp Security & Tokens (Safe Mode)
VERIFY_TOKEN = "islamiczindagi123"
WHATSAPP_TOKEN = os.environ.get("TOKEN")
PHONE_ID = os.environ.get("PHONE_ID")

@app.route('/', methods=['GET'])
def home():
    return "Islamic Zindagi Bot is Live and Running!"

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    # WhatsApp Webhook Verification
    if request.method == 'GET':
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        
        if mode == "subscribe" and token == VERIFY_TOKEN:
            return challenge, 200
        return "Forbidden", 403

    # Receiving Messages from Users
    if request.method == 'POST':
        data = request.get_json()
        print("New Message Received:", data)
        return "EVENT_RECEIVED", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
