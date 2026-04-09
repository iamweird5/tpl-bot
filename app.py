import os
import requests
import json
import traceback
from flask import Flask

app = Flask(__name__)

# ---------------- CONFIG ----------------
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

EPASS = os.environ.get("EPASS")
REMEMBER = os.environ.get("REMEMBER")  # MUST BE URL-ENCODED

BASE_URL = "https://epass-ca.quipugroup.net/epass_server.php"

HEADERS = {
    "Cookie": f"ePASS={EPASS}; ePASSRememberMe={REMEMBER}",
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
}

ATTRACTIONS = {
    "Ripley's Aquarium": 18,
    "ROM": 19,
    "Toronto Zoo": 22
}

last_status = {k: None for k in ATTRACTIONS}

# ---------------- TELEGRAM ----------------
def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
        print("📲 Telegram sent")
    except Exception as e:
        print("❌ Telegram error:", e)

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

        print(f"\n🔍 {name} STATUS CODE:", r.status_code)
        print(f"🔍 RAW RESPONSE:\n{r.text[:500]}")

        if r.status_code != 200:
            return "ERROR"

        data = r.json()

        # Combine all possible fields
        text = (
            (data.get("offerDescription") or "") +
            (data.get("attractionInfoDescription") or "")
        ).lower()

        print(f"🧠 PARSED TEXT SAMPLE:\n{text[:300]}")

        if "show first available offer" in text:
            return "AVAILABLE"

        if "no passes available" in text or \
           "all passes for this attraction have been reserved" in text:
            return "NOT AVAILABLE"

        return "UNKNOWN"

    except Exception:
        print(f"❌ ERROR checking {name}:")
        traceback.print_exc()
        return "ERROR"

# ---------------- ROUTES ----------------
@app.route("/")
def home():
    return "API Bot Running 🚀"

@app.route("/check")
def run_check():
    global last_status

    results = {}

    for name, aid in ATTRACTIONS.items():
        status = check_attraction(name, aid)
        results[name] = status

        # Send alert only when becomes AVAILABLE
        if status == "AVAILABLE" and last_status[name] != "AVAILABLE":
            send_telegram(f"🚨 {name} PASS AVAILABLE!")

        last_status[name] = status

    return json.dumps(results)

# ---------------- START ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)