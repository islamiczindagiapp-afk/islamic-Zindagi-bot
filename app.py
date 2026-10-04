from flask import Flask, request
import os
import requests

PHONE_ID = "1206682442537337"
TOKEN = OS.environ.get("TOKEN")

app = Flask(__name__)


@app.route("/webhook", methods=["GET"])
def verify():
  if request.args.get("hub.verify_token") == "islamic123":
    return request.args.get("hub.challenge")
  return "ok"


@app.route("/webhook", methods=["POST"])
def receive():
  data = request.json
  try:
    msg_data = data["entry"][0]["changes"][0]["value"]["messages"][0]
    from_num = msg_data["from"]
    user_text = msg_data["text"]["body"].lower()

    if user_text in ["hi", "hello", "salam", "namaste", "1", "2"]:
      reply = """As-salamu Alaikum! 🤲
Islamic Zindagi Live Guidance

1️⃣ Quran Se Guidance - Type 1
2️⃣ Sahih Hadith Se Guidance - Type 2

Urdu / English / Telugu lo adagandi.
మీ ప్రశ్నను తెలుగులో అడగండి
اپنا سوال اردو میں پوچھیں"""
    elif "1" in user_text or "quran" in user_text:
      reply = """📖 Quran Guidance:
'Ala Bizikrillahi Tatmainnul Quloob' - Allah ke zikr se hi dilo ko sukoon milta hai. [Surah Raad 13:28]

Telugu: Allah smarana tho hrudayalaku shanti labhistundi."""
    else:
      reply = """🌙 Sahih Hadith Guidance:
Nabi ﷺ ne farmaya: Tum me se behtareen wo hai jo Quran seekhe aur sikhaye. [Sahih Bukhari 5027]

Telugu: Meerulo uttamudu Quran nerchukoni marokariki nerpinche vadu."""

    url = f"https://graph.facebook.com/v19.0/{PHONE_ID}/messages"
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": from_num,
        "text": {"body": reply},
    }
    requests.post(url, headers=headers, json=payload)
  except:
    pass
  return "ok", 200


if __name__ == "__main__":
  app.run(port=10000)
