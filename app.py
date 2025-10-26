import os
import requests
import base64
import json
import re
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv
from difflib import get_close_matches

load_dotenv()

# =========================
# Environment variables
# =========================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not all([OPENAI_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID]):
    raise ValueError("Please set OPENAI_API_KEY, TELEGRAM_BOT_TOKEN, and TELEGRAM_CHAT_ID in .env")

client = OpenAI(api_key=OPENAI_API_KEY)

# Load medicine dataset once
df = pd.read_csv("medicine_dataset.csv")

# =========================
# Prescription OCR via GPT
# =========================
def extract_prescription_data(image_path):
    """Extract medicine details from a prescription image using GPT-4o-mini."""
    with open(image_path, "rb") as f:
        image_bytes = f.read()
    image_base64 = base64.b64encode(image_bytes).decode("utf-8")

    response = client.responses.create(
        model="gpt-4o-mini",
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": (
                            "You are a prescription reader. "
                            "Extract all medicine names, dosage, and timing from this image. "
                            "Return JSON only in this format:\n"
                            '{"medicines":[{"name":"Paracetamol","dosage":"500mg","time":"Morning and Night"}]}'
                        )
                    },
                    {
                        "type": "input_image",
                        "image_url": f"data:image/jpeg;base64,{image_base64}"
                    }
                ]
            }
        ],
        max_output_tokens=500
    )
    return response.output_text

def clean_json_response(text):
    """Clean GPT output for JSON parsing."""
    text = re.sub(r"^```(?:json)?", "", text.strip(), flags=re.IGNORECASE)
    text = re.sub(r"```$", "", text.strip())
    text = text.replace("'", '"')
    return text.strip()

# =========================
# Telegram Messaging
# =========================
def send_telegram_message(med_name, med_dosage, med_time):
    """Send a medicine reminder to Telegram."""
    message = f"💊 Reminder: Take {med_name} ({med_dosage}) at {med_time}"
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        res = requests.post(url, data=payload, timeout=10)
        res.raise_for_status()
        print(f"📨 Message sent successfully for {med_name} ({med_dosage}) at {med_time}")
    except requests.exceptions.RequestException as e:
        print(f"⚠ Failed to send message: {e}")
        print("Response:", res.text if 'res' in locals() else "No response")

# =========================
# Main Processing
# =========================
def process_prescription(image_path):
    """Extract medicines from prescription image and send Telegram reminders."""
    print(f"🩺 Processing prescription: {image_path}")
    extracted_data = extract_prescription_data(image_path)
    cleaned = clean_json_response(extracted_data)

    try:
        data = json.loads(cleaned)
        medicines = data.get("medicines", [])
        if not medicines:
            print("⚠ No medicines found in prescription.")
            return

        for med in medicines:
            name = med.get("name", "Unknown")
            dosage = med.get("dosage", "Unspecified")
            time = med.get("time", "Unspecified")
            send_telegram_message(name, dosage, time)

    except json.JSONDecodeError:
        print("⚠ Failed to parse JSON from GPT output.")
        print("GPT response was:\n", extracted_data)

# =========================
# Script Entry Point
# =========================
if __name__ == "__main__":
    image_path = "123.jpg"  # Replace with your prescription image
    process_prescription(image_path)
