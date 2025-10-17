from flask import Flask
import threading
import time
import os
import requests
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

app = Flask(__name__)

INTERVAL_HOURS = 3

SERP_API_KEY = os.environ["SERP_API_KEY"]
SENDER_EMAIL = os.environ["SENDER_EMAIL"]
SENDER_PASS = os.environ["SENDER_PASS"]
RECEIVER_EMAIL = os.environ["RECEIVER_EMAIL"]

def get_cheapest_flight():
    params = {
        "engine": "google_flights",
        "departure_id": "PNQ",
        "arrival_id": "VNS",
        "outbound_date": "2025-12-15",
        "stops": 0,
        "currency": "INR",
        "api_key": SERP_API_KEY
    }

    try:
        response = requests.get("https://serpapi.com/search", params=params)
        data = response.json()
        flight = data["best_flights"][0]
        airline = flight["flights"][0]["airline"]
        price = flight["price"]
        link = data.get("search_metadata", {}).get("google_flights_url", "No link")
        return f"Cheapest nonstop flight:\nAirline: {airline}\nPrice: ₹{price}\nLink: {link}"
    except Exception as e:
        return f"Error fetching flight: {e}"

def send_email(message):
    msg = MIMEText(message)
    msg["Subject"] = f"[Flight Update] Pune → Varanasi (15 Dec 2025) - {datetime.now().strftime('%H:%M %d-%b')}"
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECEIVER_EMAIL
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(SENDER_EMAIL, SENDER_PASS)
        smtp.send_message(msg)

def poller_loop():
    while True:
        info = get_cheapest_flight()
        send_email(info)
        print(f"[{datetime.now()}] Email sent. Sleeping {INTERVAL_HOURS} hours.")
        time.sleep(INTERVAL_HOURS * 3600)

# Run poller in background thread
threading.Thread(target=poller_loop, daemon=True).start()

# Minimal web route to keep Render happy
@app.route("/")
def home():
    return "Flight watcher is running!"

if __name__ == "__main__":
    # Bind to port Render expects
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
