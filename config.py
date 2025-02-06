from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv()
ENVIRONMENT = os.getenv("ENV", "dev").lower()
API_TOKEN = (
    os.getenv("PROD_API_TOKEN") if ENVIRONMENT == "prod" else os.getenv("DEV_API_TOKEN")
)
if not API_TOKEN:
    raise ValueError(
        f"API token for environment '{ENVIRONMENT}' not found in .env file"
    )
DB_PATH = os.getenv("DB_PATH", "users.db")

user_photos = {}
user_data = {}


async def log_message(text, user=None):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    user_info = f"[USER: {user}] " if user else ""
    print(f"🕒 [{current_time}] 📋 {user_info}[LOG] - {text}")
