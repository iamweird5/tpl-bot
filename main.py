import os
import time
import requests
from flask import Flask
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

app = Flask(__name__)

# ---------------- CONFIG ----------------
URL = "https://epass-ca.quipugroup.net/?clientID=16&libraryID=1"
TARGET_TEXT = "Royal Ontario Museum"

COOKIES = os.environ.get("COOKIES")

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
    return webdriver.Chrome(options=options)

# ---------------- ADD COOKIES ----------------
def load_cookies(driver):
    driver.get("https://epass-ca.quipugroup.net")

    for c in COOKIES.split(";"):
        name, value = c.strip().split("=", 1)
        driver.add_cookie({
            "name": name,
            "value": value,
            "domain": "epass-ca.quipugroup.net",
            "path": "/"
        })

# ---------------- CHECK ----------------
def check_rom():
    global last_status

    driver = get_driver()

    try:
        # inject session
        load_cookies(driver)

        # open page
        driver.get(URL)
        time.sleep(5)

        # click ROM
        driver.find_element(By.XPATH, f"//*[contains(text(), '{TARGET_TEXT}')]").click()
        time.sleep(3)

        # click Offers tab (JS safe click)
        offers = driver.find_element(By.XPATH, "//a[contains(., 'Offers')]")
        driver.execute_script("arguments[0].click();", offers)

        time.sleep(6)

        body = driver.find_element(By.TAG_NAME, "body").text
        print(body[:500])

        # -------- DETECTION --------
        if "Show first available offer" in body:
            status = "AVAILABLE"
            print("✅ AVAILABLE")
        elif "No passes available" in body:
            status = "NOT AVAILABLE"
            print("❌ NOT AVAILABLE")
        else:
            status = "UNKNOWN"
            print("⚠️ UNKNOWN")

        # notify
        if status != last_status:
            last_status = status
            if status == "AVAILABLE":
                send_telegram("🚨 ROM PASS AVAILABLE NOW!")

        return status

    except Exception as e:
        print("ERROR:", e)
        return "ERROR"

    finally:
        driver.quit()

# ---------------- ROUTES ----------------
@app.route("/")
def home():
    return "ROM Bot Running"

@app.route("/check")
def check():
    result = check_rom()
    return f"Check done: {result}"

# ---------------- START ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))