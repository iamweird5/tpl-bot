import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

# CONFIG
LOGIN_URL = "https://epass-ca.quipugroup.net/login"  # adjust if needed
PASS_URL = "https://epass-ca.quipugroup.net/?clientID=16&libraryID=1"
CHECK_INTERVAL = 60
TARGET_TEXT = "Royal Ontario Museum"

# TELEGRAM CONFIG
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# LIBRARY LOGIN
USERNAME = os.environ.get("LIBRARY_USER")
PASSWORD = os.environ.get("LIBRARY_PASS")

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": message})
        print("📲 Telegram sent!")
    except Exception as e:
        print("Telegram error:", e)

def create_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    print("🖥️ Creating Chrome driver...")
    return webdriver.Chrome(options=options)

def login(driver):
    print("🔑 Opening login page...")
    driver.get(LOGIN_URL)
    time.sleep(2)

    print("✍️ Filling username and password...")
    driver.find_element(By.ID, "username").send_keys(USERNAME)
    driver.find_element(By.ID, "password").send_keys(PASSWORD)
    
    print("🚀 Clicking login button...")
    driver.find_element(By.ID, "loginBtn").click()
    time.sleep(5)

    print("✅ Logged in successfully")

def check_availability():
    driver = create_driver()
    try:
        login(driver)
        print("🔍 Navigating to pass page...")
        driver.get(PASS_URL)
        time.sleep(5)

        print("🔎 Searching for ROM card...")
        elements = driver.find_elements(By.XPATH, f"//*[contains(text(), '{TARGET_TEXT}')]")
        if not elements:
            print("⚠️ ROM card not found")
        else:
            for el in elements:
                try:
                    el.click()
                    print("👉 Clicked ROM card")
                    break
                except Exception as e:
                    print("Error clicking ROM card:", e)

        print("📂 Looking for Offers tab...")
        offers_tab = driver.find_element(By.XPATH, "//*[contains(text(), 'Offers')]")
        offers_tab.click()
        time.sleep(2)

        body_text = driver.find_element(By.TAG_NAME, "body").text
        print("📄 Offers section text:", body_text[:200], "...")  # show first 200 chars

        if "No passes available at this time" not in body_text:
            print("✅ ROM PASS AVAILABLE!")
            send_telegram(f"✅ ROM Pass available!\n{PASS_URL}")
        else:
            print("❌ No passes available")

    except Exception as e:
        print("Error during check_availability:", e)
    finally:
        driver.quit()

def bot_loop():
    while True:
        print("⏱️ Checking pass availability...")
        check_availability()
        print(f"⏳ Waiting {CHECK_INTERVAL} seconds before next check...")
        time.sleep(CHECK_INTERVAL)

# Run bot loop
if __name__ == "__main__":
    import threading
    threading.Thread(target=bot_loop, daemon=True).start()

    from flask import Flask
    app = Flask(__name__)

    @app.route("/")
    def home():
        return "ROM Bot is running with debug logs"

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)