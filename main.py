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
MAIN_URL = "https://epass-ca.quipugroup.net/?clientID=16&libraryID=1"

USERNAME = os.environ.get("LIBRARY_USER")
PASSWORD = os.environ.get("LIBRARY_PASS")

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

last_status = None

# ---------------- TELEGRAM ----------------
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
        print("📲 Telegram sent!")
    except Exception as e:
        print("❌ Telegram error:", e)

# ---------------- DRIVER ----------------
def get_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    return webdriver.Chrome(options=options)

# ---------------- CHECK FUNCTION ----------------
def check():
    global last_status
    driver = get_driver()

    try:
        # ---------------- LOGIN ----------------
        driver.get(LOGIN_URL)
        time.sleep(3)

        driver.find_element(By.NAME, "username").send_keys(USERNAME)
        driver.find_element(By.NAME, "password").send_keys(PASSWORD)

        login_btn = driver.find_element(By.XPATH, "//button[contains(., 'Login')]")
        driver.execute_script("arguments[0].click();", login_btn)

        time.sleep(6)

        # Verify login
        if "logout" not in driver.page_source.lower():
            print("❌ LOGIN FAILED")
            return "LOGIN FAILED"

        print("✅ LOGIN SUCCESS")

        # ---------------- OPEN MAIN PAGE ----------------
        driver.get(MAIN_URL)
        time.sleep(6)

        # ---------------- CLICK ROM (CORRECT ELEMENT) ----------------
        print("🎯 Finding ROM card...")

        rom_clicked = False
        elements = driver.find_elements(By.XPATH, "//*[contains(text(),'Royal Ontario Museum')]")

        for el in elements:
            try:
                # avoid clicking external link
                if el.tag_name != "a":
                    driver.execute_script("arguments[0].click();", el)
                    rom_clicked = True
                    print("✅ Clicked ROM internal element")
                    break
            except:
                continue

        if not rom_clicked:
            print("❌ Could not click ROM correctly")
            return "ERROR"

        time.sleep(6)

        # ---------------- READ PAGE ----------------
        body = driver.find_element(By.TAG_NAME, "body").text
        print("📄 Page snippet:")
        print(body[:500])

        # ---------------- DETECT STATUS ----------------
        if "Show first available offer" in body:
            status = "AVAILABLE"
            print("✅ AVAILABLE")

        elif "No passes available at this time" in body or \
             "All passes for this attraction have been reserved" in body:
            status = "NOT AVAILABLE"
            print("❌ NOT AVAILABLE")

        else:
            status = "UNKNOWN"
            print("⚠️ UNKNOWN")

        # ---------------- TELEGRAM ----------------
        if status != last_status:
            last_status = status
            if status == "AVAILABLE":
                send_telegram("🚨 ROM PASS AVAILABLE! BOOK NOW!")

        return status

    except Exception as e:
        print("❌ ERROR:", e)
        return "ERROR"

    finally:
        driver.quit()

# ---------------- ROUTES ----------------
@app.route("/")
def home():
    return "ROM Bot Running"

@app.route("/check")
def run():
    result = check()
    return f"Check done: {result}"

# ---------------- START ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))