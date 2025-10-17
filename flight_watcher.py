from flask import Flask
import threading
import time
import os
import requests
from datetime import datetime

app = Flask(__name__)

# ---------------- CONFIG ---------------- #
INTERVAL_HOURS = 3  # poll every 3 hours

SERP_API_KEY = os.environ["SERP_API_KEY"]
SENDGRID_API_KEY = os.environ["SENDGRID_API_KEY"]
SENDER_EMAIL = os.environ["SENDER_EMAIL"]
RECEIVER_EMAIL = os.environ["RECEIVER_EMAIL"]
# ---------------------------------------- #

def log(msg):
    """Timestamped log for Render Live Tail"""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}", flush=True)

def get_cheapest_flight():
    log("Fetching flight data from SerpApi...")
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
        response = requests.get("https://serpapi.com/search", params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        flight = data["best_flights"][0]
        airline = flight["flights"][0]["airline"]
        price = flight["price"]
        link = data.get("search_metadata", {}).get("google_flights_url", "No link")
        log(f"Flight data fetched: {airline} ₹{price}")
        return f"Cheapest nonstop flight:\nAirline: {airline}\nPrice: ₹{price}\nLink: {link}"
    except Exception as e:
        log(f"Error fetching flight data: {e}")
        return f"Error fetching flight: {e}"

def send_email(message):
    subject = f"[Flight Update] Pune → Varanasi (15 Dec 2025) - {datetime.now().strftime('%H:%M %d-%b')}"
    log(f"Sending email via SendGrid to {RECEIVER_EMAIL}...")
    
    url = "https://api.sendgrid.com/v3/mail/send"
    headers = {
        "Authorization": f"Bearer {SENDGRID_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "personalizations": [{"to": [{"email": RECEIVER_EMAIL}]}],
        "from": {"email": SENDER_EMAIL},
        "subject": subject,
        "content": [{"type": "text/plain", "value": message}]
    }

    try:
        r = requests.post(url, headers=headers, json=data, timeout=20)
        if r.status_code == 202:
            log("Email sent successfully via SendGrid.")
        else:
            log(f"SendGrid error: {r.status_code} - {r.text}")
    except Exception as e:
        log(f"Exception sending email via SendGrid: {e}")

def poller_loop():
    while True:
        log("=== Starting new polling cycle ===")
        info = get_cheapest_flight()
        send_email(info)
        log(f"Sleeping for {INTERVAL_HOURS} hours before next cycle...")
        time.sleep(INTERVAL_HOURS * 3600)

# ---------------- START BACKGROUND THREAD ---------------- #
threading.Thread(target=poller_loop, daemon=True).start()
log("Background poller thread started.")

# ---------------- MINIMAL WEB ROUTE FOR RENDER ---------------- #
@app.route("/")
def home():
    return "Flight watcher is running!"

# ---------------- RUN FLASK ---------------- #
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    log(f"Starting Flask web server on port {port}...")
    app.run(host="0.0.0.0", port=port)
