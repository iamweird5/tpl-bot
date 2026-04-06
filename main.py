import os
import requests
from flask import Flask
from datetime import datetime

app = Flask(__name__)

# ---------------- CONFIG ----------------
API_URL = "https://epass-ca.quipugroup.net/epass_server.php?dataType=json&method=AttractionInfo&functionFile=Attractions&attractionID=19&language=en"

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# To prevent duplicate notifications
last_status = None

# ---------------- TELEGRAM ----------------
def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": message})
        print("📲 Telegram sent!")
    except Exception as e:
        print("❌ Telegram error:", e)

# ---------------- CHECK FUNCTION ----------------
def check_availability():
    global last_status
    print("🚀 Checking ROM via API...")

    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(API_URL, headers=headers)
        data = response.json()  # ✅ parse JSON correctly

        # DEBUG: Print full response
        print("📄 Full JSON response:", data)

        # Robust availability check
        offer_id = data.get("offerID")
        if offer_id and int(offer_id) > 0:
            current_status = "AVAILABLE"
            print(f"✅ Pass detected! offerID = {offer_id}")
        else:
            current_status = "NOT AVAILABLE"
            print("❌ No pass available")

        # Send Telegram only if status changed
        if current_status != last_status:
            last_status = current_status
            if current_status == "AVAILABLE":
                send_telegram(f"🚨 ROM Pass AVAILABLE NOW! offerID={offer_id}")
            else:
                send_telegram("❌ ROM Pass no longer available")

        return current_status

    except Exception as e:
        print("❌ ERROR:", e)
        return "ERROR"

# ---------------- ROUTES ----------------
@app.route("/")
def home():
    return "ROM API Bot running"

@app.route("/check")
def run_check():
    result = check_availability()
    return f"Check done: {result}"

# ---------------- START ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))