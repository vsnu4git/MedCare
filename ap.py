import requests
TELEGRAM_BOT_TOKEN = "your_bot_token_here"
TELEGRAM_CHAT_ID = "your_chat_id_here"

url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
payload = {"chat_id": TELEGRAM_CHAT_ID, "text": "Hello from Python!"}

res = requests.post(url, data=payload)
print(res.status_code, res.text)
