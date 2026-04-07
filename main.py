import os
import time
import requests
from flask import Flask
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

app = Flask(__name__)

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
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

# ---------------- DRIVER ----------------
def get_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    return webdriver.Chrome(options=options)

# ---------------- CHECK ----------------
def check():
    global last_status
    driver = get_driver()

    try:
        # STEP 1: LOGIN
        driver.get(LOGIN_URL)
        time.sleep(3)

        driver.find_element(By.NAME, "username").send_keys(USERNAME)
        driver.find_element(By.NAME, "password").send_keys(PASSWORD)

        # Click login using JS (more reliable)
        login_btn = driver.find_element(By.XPATH, "//button[contains(., 'Login')]")
        driver.execute_script("arguments[0].click();", login_btn)

        time.sleep(6)

        # 🔥 VERIFY LOGIN SUCCESS
        page = driver.page_source

        if "logout" not in page.lower():
            print("❌ LOGIN FAILED")
            return "LOGIN FAILED"

        print("✅ LOGIN SUCCESS")

        # STEP 2: OPEN MAIN PAGE
        driver.get(MAIN_URL)
        time.sleep(6)

        body = driver.find_element(By.TAG_NAME, "body").text
        print(body[:500])

        # STEP 3: DETECTION
        if "Show first available offer" in body:
            status = "AVAILABLE"
            print("✅ AVAILABLE")

        elif "All passes for this attraction have been reserved" in body:
            status = "NOT AVAILABLE"
            print("❌ NOT AVAILABLE")

        else:
            status = "UNKNOWN"
            print("⚠️ UNKNOWN")

        # STEP 4: TELEGRAM
        if status != last_status:
            last_status = status
            if status == "AVAILABLE":
                send_telegram("🚨 PASS AVAILABLE! BOOK NOW!")

        return status

    except Exception as e:
        print("ERROR:", e)
        return "ERROR"

    finally:
        driver.quit()

# ---------------- ROUTES ----------------
@app.route("/")
def home():
    return "Login Bot Running"

@app.route("/check")
def run():
    result = check()
    return f"Check done: {result}"

# ---------------- START ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))