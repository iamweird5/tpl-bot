import os
import requests
from flask import Flask

app = Flask(__name__)

# ---------------- CONFIG ----------------
ROM_API_URL = "https://epass-ca.quipugroup.net/epass_server.php"
ROM_ATTRACTION_ID = 19  # ROM attraction ID

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
USERNAME = os.environ.get("LIBRARY_USER")
PASSWORD = os.environ.get("LIBRARY_PASS")

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
def check_rom_pass():
    global last_status
    print("🚀 Checking ROM pass via API...")

    try:
        # API call to fetch attraction info
        params = {
            "dataType": "json",
            "method": "AttractionInfo",
            "functionFile": "Attractions",
            "attractionID": ROM_ATTRACTION_ID,
            "language": "en"
        }

        response = requests.get(ROM_API_URL, params=params, auth=(USERNAME, PASSWORD))
        data = response.json()

        # Extract offer info
        offer_title = data.get("offerTitle", "")
        offer_desc = data.get("offerDescription", "")

        # Determine availability
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

        # Send Telegram if status changed
        if current_status != last_status:
            last_status = current_status
            if current_status == "AVAILABLE":
                send_telegram("🚨 ROM PASS AVAILABLE! Book now!")
            elif current_status == "UNKNOWN":
                send_telegram("⚠️ ROM status unclear - check manually")

        return current_status

    except Exception as e:
        print("❌ ERROR:", e)
        return "ERROR"

# ---------------- FLASK ROUTES ----------------
@app.route("/")
def home():
    return "ROM API Bot running"

@app.route("/check")
def run_check():
    result = check_rom_pass()
    return f"Check done: {result}"

# ---------------- START ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))