import os
import requests
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

def register_webhook():
    if not TOKEN or "REPLACE" in TOKEN:
        print("❌ Error: TELEGRAM_BOT_TOKEN is missing or invalid in .env")
        return

    print("--- Telegram Webhook Setup ---")
    ngrok_url = input("Enter your ngrok HTTPS URL (e.g., https://abcd.ngrok-free.app): ").strip()
    
    if not ngrok_url.startswith("https://"):
        print("❌ Error: URL must start with https://")
        return

    # Trim trailing slash
    if ngrok_url.endswith("/"):
        ngrok_url = ngrok_url[:-1]

    webhook_url = f"{ngrok_url}/api/telegram/webhook"
    api_url = f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={webhook_url}"

    print(f"\nRegistering webhook: {webhook_url}...")
    
    try:
        response = requests.get(api_url)
        data = response.json()
        
        if data.get("ok"):
            print("✅ Success! Webhook is live.")
            print("👉 You can now go to Telegram and chat with your bot.")
        else:
            print(f"❌ Failed: {data.get('description')}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    register_webhook()
