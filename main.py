import os
import time
import requests
from flask import Flask
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

app = Flask(__name__)

# CONFIG
LOGIN_URL = "https://epass-ca.quipugroup.net/login"
PASS_URL = "https://epass-ca.quipugroup.net/?clientID=16&libraryID=1"
TARGET_TEXT = "Royal Ontario Museum"

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
USERNAME = os.environ.get("LIBRARY_USER")
PASSWORD = os.environ.get("LIBRARY_PASS")


def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": message})
    print("📲 Telegram sent!")


def create_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(options=options)


def check_availability():
    print("🚀 Running check...")
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

        # CLICK ROM
        elements = driver.find_elements(By.XPATH, f"//*[contains(text(), '{TARGET_TEXT}')]")
        for el in elements:
            try:
                el.click()
                break
            except:
                continue

        time.sleep(3)

        # OPEN OFFERS
        driver.find_element(By.XPATH, "//*[contains(text(), 'Offers')]").click()
        time.sleep(3)

        body_text = driver.find_element(By.TAG_NAME, "body").text

        if "No passes available at this time" not in body_text:
            send_telegram(f"✅ ROM Pass Available!\n{PASS_URL}")
            return "AVAILABLE"
        else:
            return "NOT AVAILABLE"

    except Exception as e:
        print("Error:", e)
        return "ERROR"

    finally:
        if driver:
            driver.quit()


# HEALTH ROUTE
@app.route("/")
def home():
    return "Bot is running"


# TRIGGER ROUTE
@app.route("/check")
def run_check():
    result = check_availability()
    return f"Check done: {result}"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))