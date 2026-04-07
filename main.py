import os
import time
import requests
from flask import Flask
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

app = Flask(__name__)

# ---------------- CONFIG ----------------
URL_LOGIN = "https://epass-ca.quipugroup.net/login"
URL_ROM = "https://epass-ca.quipugroup.net/?clientID=16&libraryID=1"
CHECK_INTERVAL = 60  # seconds

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

# ---------------- SELENIUM SETUP ----------------
def get_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

# ---------------- CHECK FUNCTION ----------------
def check_rom():
    global last_status
    driver = get_driver()
    try:
        driver.get(URL_LOGIN)
        time.sleep(2)

        # Login
        driver.find_element(By.ID, "username").send_keys(USERNAME)
        driver.find_element(By.ID, "password").send_keys(PASSWORD)
        driver.find_element(By.ID, "loginBtn").click()
        print("🔐 Logged in")
        time.sleep(5)  # wait for redirect

        # Navigate to ROM page
        driver.get(URL_ROM)
        time.sleep(5)

        # Click Offers tab
        offers_tab = driver.find_element(By.XPATH, "//button[contains(text(),'Offers')]")
        offers_tab.click()
        time.sleep(3)  # wait for content

        # Read offer cards
        cards = driver.find_elements(By.CLASS_NAME, "card")
        available = False
        for card in cards:
            text = card.text
            if "Show first available offer" in text or "Mobile or Printed Pass Accepted" in text:
                available = True
                break

        if available:
            current_status = "AVAILABLE"
            print("✅ ROM Pass Available!")
        else:
            current_status = "NOT AVAILABLE"
            print("❌ ROM Pass Not Available")

        # Send Telegram if status changed
        if current_status != last_status:
            last_status = current_status
            if current_status == "AVAILABLE":
                send_telegram("🚨 ROM PASS AVAILABLE! BOOK NOW!")

        return current_status

    except Exception as e:
        print("❌ ERROR:", e)
        return "ERROR"
    finally:
        driver.quit()

# ---------------- FLASK ROUTES ----------------
@app.route("/")
def home():
    return "ROM Selenium Bot Running"

@app.route("/check")
def run_check():
    result = check_rom()
    return f"Check done: {result}"

# ---------------- START ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))