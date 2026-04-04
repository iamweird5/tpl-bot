import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# CONFIG
URL = "https://epass-ca.quipugroup.net/?clientID=16&libraryID=1"
CHECK_INTERVAL = 60
TARGET_TEXT = "Toronto Zoo"

# TELEGRAM CONFIG
BOT_TOKEN = "8750333022:AAHYYfvVEuamVJTOmaX2-_1UaN5EOd3vaQQ"
CHAT_ID = "5287405098"

def send_telegram():
    message = f"🚨 Toronto Zoo pass available!\nBook now:\n{URL}"

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": message
    }

    try:
        requests.post(url, data=data)
        print("📲 Telegram sent!")
    except Exception as e:
        print("Telegram error:", e)


# Browser setup
options = webdriver.ChromeOptions()
options.add_argument("--headless")  # runs without UI
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)


def check_availability():
    driver.get(URL)
    time.sleep(5)

    passes = driver.find_elements(By.CLASS_NAME, "card")

    for p in passes:
        text = p.text

        if TARGET_TEXT in text:
            if "Unavailable" not in text:
                print("✅ AVAILABLE!!!")
                send_telegram()
                return True

    print("❌ Still unavailable")
    return False


# LOOP
while True:
    try:
        if check_availability():
            break
    except Exception as e:
        print("Error:", e)

    time.sleep(CHECK_INTERVAL)