import os
import time
import requests
import threading
from flask import Flask
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

# CONFIG
LOGIN_URL = "https://epass-ca.quipugroup.net/login"
PASS_URL = "https://epass-ca.quipugroup.net/?clientID=16&libraryID=1"
CHECK_INTERVAL = 60
TARGET_TEXT = "Royal Ontario Museum"

# ENV VARIABLES
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
USERNAME = os.environ.get("LIBRARY_USER")
PASSWORD = os.environ.get("LIBRARY_PASS")

app = Flask(__name__)

@app.route("/")
def home():
    return "ROM Bot is running with debug logs"

# ---------------- TELEGRAM ----------------
def send_telegram(message):
    print("📨 Sending Telegram...")
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        res = requests.post(url, data={"chat_id": CHAT_ID, "text": message})
        print("📲 Telegram sent!", res.status_code)
    except Exception as e:
        print("❌ Telegram error:", e)

# ---------------- SELENIUM ----------------
def create_driver():
    print("🖥️ Creating Chrome driver...")
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(options=options)

def login(driver):
    print("🔑 Opening login page...")
    driver.get(LOGIN_URL)
    time.sleep(3)

    print("✍️ Entering credentials...")
    driver.find_element(By.ID, "username").send_keys(USERNAME)
    driver.find_element(By.ID, "password").send_keys(PASSWORD)

    print("🚀 Clicking login...")
    driver.find_element(By.ID, "loginBtn").click()
    time.sleep(5)

    print("✅ Login step completed")

def check_availability():
    driver = None
    try:
        driver = create_driver()

        # LOGIN
        login(driver)

        print("🌐 Opening pass page...")
        driver.get(PASS_URL)
        time.sleep(5)

        # FIND ROM
        print("🔍 Searching for ROM...")
        elements = driver.find_elements(By.XPATH, f"//*[contains(text(), '{TARGET_TEXT}')]")

        if not elements:
            print("❌ ROM card not found")
            return

        for el in elements:
            try:
                el.click()
                print("👉 Clicked ROM card")
                break
            except:
                continue

        time.sleep(3)

        # CLICK OFFERS
        print("📂 Opening Offers tab...")
        offers_tab = driver.find_element(By.XPATH, "//*[contains(text(), 'Offers')]")
        offers_tab.click()
        time.sleep(3)

        # CHECK CONTENT
        body_text = driver.find_element(By.TAG_NAME, "body").text
        print("📄 Page snippet:", body_text[:200])

        if "No passes available at this time" not in body_text:
            print("✅ PASS AVAILABLE!")
            send_telegram(f"✅ ROM Pass Available!\n{PASS_URL}")
        else:
            print("❌ No passes available")

    except Exception as e:
        print("❌ ERROR:", e)

    finally:
        if driver:
            driver.quit()

# ---------------- LOOP ----------------
def bot_loop():
    print("🚀 Bot loop started")
    while True:
        print("⏱️ Checking availability...")
        check_availability()
        print(f"⏳ Sleeping {CHECK_INTERVAL}s...")
        time.sleep(CHECK_INTERVAL)

# ---------------- START ----------------
if __name__ == "__main__":
    print("🌐 Starting Flask app...")

    thread = threading.Thread(target=bot_loop)
    thread.daemon = True
    thread.start()

    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))