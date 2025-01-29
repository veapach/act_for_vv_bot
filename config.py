from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv()
API_TOKEN = os.getenv("API_TOKEN")

user_photos = {}
user_data = {}


def log_message(action, message):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    username = message.from_user.username
    if not username:
        username = f"{message.from_user.first_name} {message.from_user.id}"
    print(f"🕒 [{current_time}] 📋 [LOG] - {action} @{username}")
