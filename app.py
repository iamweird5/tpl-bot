import os
import requests
from flask import Flask
import json

app = Flask(__name__)

# ---------------- CONFIG ----------------
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# Cookies (from you)
EPASS = os.environ.get("EPASS")
REMEMBER = os.environ.get("REMEMBER")

HEADERS = {
    "Cookie": f"ePASS={EPASS}; ePASSRememberMe={REMEMBER}",
    "User-Agent": "Mozilla/5.0"
}

ATTRACTIONS = {
    "Ripley's Aquarium": 18,
    "ROM": 19,
    "Toronto Zoo": 22
}

BASE_URL = "https://epass-ca.quipugroup.net/epass_server.php"

last_status = {k: None for k in ATTRACTIONS}

# ---------------- TELEGRAM ----------------
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

# ---------------- CHECK FUNCTION ----------------
def check_attraction(name, attraction_id):
    params = {
        "dataType": "json",
        "method": "AttractionInfo",
        "functionFile": "Attractions",
        "attractionID": attraction_id,
        "language": "en"
    }

    try:
        r = requests.get(BASE_URL, headers=HEADERS, params=params, timeout=15)
        data = r.json()

        text = (data.get("offerDescription") or "").lower()

        print(f"\n🔍 {name} RESPONSE TEXT:\n{text[:300]}")

        if "show first available offer" in text:
            return "AVAILABLE"

        if "no passes available" in text or \
           "all passes for this attraction have been reserved" in text:
            return "NOT AVAILABLE"

        return "UNKNOWN"

    except Exception as e:
        print(f"❌ Error checking {name}:", e)
        return "ERROR"

# ---------------- ROUTE ----------------
@app.route("/check")
def check():
    global last_status

    results = {}

    for name, aid in ATTRACTIONS.items():
        status = check_attraction(name, aid)
        results[name] = status

        # Telegram only when available
        if status == "AVAILABLE" and last_status[name] != "AVAILABLE":
            send_telegram(f"🚨 {name} PASS AVAILABLE!")

        last_status[name] = status

    return json.dumps(results)

@app.route("/")
def home():
    return "API Bot Running (No Selenium 🚀)"

# ---------------- START ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)