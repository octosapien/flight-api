import os
import time
import requests
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

# Read secrets from environment variables
SERP_API_KEY = os.environ["SERP_API_KEY"]
SENDER_EMAIL = os.environ["SENDER_EMAIL"]
SENDER_PASS = os.environ["SENDER_PASS"]
RECEIVER_EMAIL = os.environ["RECEIVER_EMAIL"]

INTERVAL_HOURS = 3

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

def main():
    while True:
        print(f"Polling SerpApi at {datetime.now()}")
        info = get_cheapest_flight()
        send_email(info)
        print("Email sent, sleeping 3 hours...")
        time.sleep(INTERVAL_HOURS * 3600)

if __name__ == "__main__":
    main()
