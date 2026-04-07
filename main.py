import os
import requests
from flask import Flask

app = Flask(__name__)

# ---------------- CONFIG ----------------
LOGIN_URL = "https://epass-ca.quipugroup.net/login"  # TPL login
API_URL = "https://epass-ca.quipugroup.net/epass_server.php"

ATTRACTION_ID = 19  # ROM

USERNAME = os.environ.get("LIBRARY_USER")
PASSWORD = os.environ.get("LIBRARY_PASS")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

last_status = None

# ---------------- TELEGRAM ----------------
def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": message})
        print("📲 Telegram sent!")
    except Exception as e:
        print("❌ Telegram error:", e)

# ---------------- LOGIN SESSION ----------------
def login_session():
    session = requests.Session()
    payload = {"username": USERNAME, "password": PASSWORD}
    headers = {"User-Agent": "Mozilla/5.0"}

    # Log in and capture session cookies
    res = session.post(LOGIN_URL, data=payload, headers=headers)
    print("🔐 Login status:", res.status_code)
    return session

# ---------------- CHECK FUNCTION ----------------
def check_rom():
    global last_status
    print("🚀 Checking ROM pass availability...")

    try:
        session = login_session()
        params = {
            "dataType": "json",
            "method": "AttractionInfo",
            "functionFile": "Attractions",
            "attractionID": ATTRACTION_ID,
            "language": "en"
        }

        res = session.get(API_URL, params=params)
        data = res.json()
        print("📄 API Response:", data)

        # -------- DETECT AVAILABILITY --------
        offer_title = data.get("offerTitle", "")
        offer_desc = data.get("offerDescription", "")

        if "Show first available offer" in offer_desc or offer_title:
            current_status = "AVAILABLE"
            print("✅ ROM pass AVAILABLE!")
        elif "No passes available at this time" in offer_desc or \
             "All passes for this attraction have been reserved" in offer_desc:
            current_status = "NOT AVAILABLE"
            print("❌ ROM pass NOT available")
        else:
            current_status = "UNKNOWN"
            print("⚠️ ROM status UNKNOWN")

        # -------- TELEGRAM ALERT --------
        if current_status != last_status:
            last_status = current_status
            if current_status == "AVAILABLE":
                send_telegram("🚨 ROM PASS AVAILABLE! BOOK NOW!")
            elif current_status == "UNKNOWN":
                send_telegram("⚠️ ROM pass status unclear — check manually")

        return current_status

    except Exception as e:
        print("❌ ERROR:", e)
        return "ERROR"

# ---------------- FLASK ROUTES ----------------
@app.route("/")
def home():
    return "ROM Pass Bot Running"

@app.route("/check")
def run_check():
    result = check_rom()
    return f"Check done: {result}"

# ---------------- START ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))