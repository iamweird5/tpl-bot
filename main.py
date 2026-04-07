import os
import time
import requests
from flask import Flask
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

app = Flask(__name__)

# ---------------- CONFIG ----------------
LOGIN_URL = "https://epass-ca.quipugroup.net/login"
PASS_URL = "https://epass-ca.quipugroup.net/?clientID=16&libraryID=1"
TARGET_TEXT = "Royal Ontario Museum"

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

# ---------------- DRIVER ----------------
def create_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    return webdriver.Chrome(options=options)

# ---------------- CHECK FUNCTION ----------------
def check_availability():
    global last_status
    print("🚀 Running Selenium check...")

    driver = None

    try:
        driver = create_driver()

        # LOGIN
        driver.get(LOGIN_URL)
        time.sleep(3)

        driver.find_element(By.ID, "username").send_keys(USERNAME)
        driver.find_element(By.ID, "password").send_keys(PASSWORD)
        driver.find_element(By.ID, "loginBtn").click()
        time.sleep(5)

        # OPEN PASS PAGE
        driver.get(PASS_URL)
        time.sleep(5)

        # CLICK ROM CARD
        elements = driver.find_elements(By.XPATH, f"//*[contains(text(), '{TARGET_TEXT}')]")
        for el in elements:
            try:
                el.click()
                break
            except:
                continue

        time.sleep(3)

        # CLICK OFFERS TAB
        driver.find_element(By.XPATH, "//*[contains(text(), 'Offers')]").click()
        time.sleep(4)

        # GET PAGE TEXT
        body_text = driver.find_element(By.TAG_NAME, "body").text

        print("📄 Page snippet:", body_text[:200])

        # CHECK AVAILABILITY
        if "No passes available at this time" not in body_text:
            current_status = "AVAILABLE"
            print("✅ PASS AVAILABLE!")
        else:
            current_status = "NOT AVAILABLE"
            print("❌ No passes available")

        # SEND TELEGRAM ONLY IF STATUS CHANGED
        if current_status != last_status:
            last_status = current_status

            if current_status == "AVAILABLE":
                send_telegram("🚨 ROM Pass AVAILABLE NOW!\nBook immediately!")
            else:
                send_telegram("❌ ROM Pass no longer available")

        return current_status

    except Exception as e:
        print("❌ ERROR:", e)
        return "ERROR"

    finally:
        if driver:
            driver.quit()

# ---------------- ROUTES ----------------
@app.route("/")
def home():
    return "ROM Selenium Bot running"

@app.route("/check")
def run_check():
    result = check_availability()
    return f"Check done: {result}"

# ---------------- START ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))