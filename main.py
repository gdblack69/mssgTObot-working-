import sys
import subprocess
import importlib
import os
from dotenv import load_dotenv
import asyncio
from flask import Flask, request, jsonify
from threading import Thread
from telethon import TelegramClient, events

# Function to check and install missing modules
def install_missing_modules():
    required_modules = [
        ('flask', '2.0.1'),
        ('python-dotenv', '0.19.0'),
        ('telethon', '1.24.0'),
        ('gunicorn', '20.1.0'),
        ('werkzeug', '2.0.3')
    ]
    for module, version in required_modules:
        try:
            importlib.import_module(module)
        except ImportError:
            print(f"Installing {module}=={version}...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', f'{module}=={version}'])
    # Restart the app after installing modules
    print("Dependencies installed, restarting...")
    os.execv(sys.executable, [sys.executable] + sys.argv)

# Check and install dependencies before proceeding
install_missing_modules()

# Load environment variables from .env file
load_dotenv()

# Retrieve credentials from .env file with error handling
SOURCE_API_ID = os.getenv("SOURCE_API_ID")
if SOURCE_API_ID is None:
    raise ValueError("SOURCE_API_ID not found in .env file.")
SOURCE_API_ID = int(SOURCE_API_ID)

SOURCE_API_HASH = os.getenv("SOURCE_API_HASH")
if SOURCE_API_HASH is None:
    raise ValueError("SOURCE_API_HASH not found in .env file.")

SOURCE_PHONE_NUMBER = os.getenv("SOURCE_PHONE_NUMBER")
if SOURCE_PHONE_NUMBER is None:
    raise ValueError("SOURCE_PHONE_NUMBER not found in .env file.")

SOURCE_CHAT_ID = os.getenv("SOURCE_CHAT_ID")
if SOURCE_CHAT_ID is None:
    raise ValueError("SOURCE_CHAT_ID not found in .env file.")
SOURCE_CHAT_ID = int(SOURCE_CHAT_ID)

DESTINATION_API_ID = os.getenv("DESTINATION_API_ID")
if DESTINATION_API_ID is None:
    raise ValueError("DESTINATION_API_ID not found in .env file.")
DESTINATION_API_ID = int(DESTINATION_API_ID)

DESTINATION_API_HASH = os.getenv("DESTINATION_API_HASH")
if DESTINATION_API_HASH is None:
    raise ValueError("DESTINATION_API_HASH not found in .env file.")

DESTINATION_PHONE_NUMBER = os.getenv("DESTINATION_PHONE_NUMBER")
if DESTINATION_PHONE_NUMBER is None:
    raise ValueError("DESTINATION_PHONE_NUMBER not found in .env file.")

DESTINATION_BOT_USERNAME = os.getenv("DESTINATION_BOT_USERNAME")
if DESTINATION_BOT_USERNAME is None:
    raise ValueError("DESTINATION_BOT_USERNAME not found in .env file.")

SOURCE_SESSION_FILE = os.getenv("SOURCE_SESSION_FILE", "new10_source_sehjhn.session")
DESTINATION_SESSION_FILE = os.getenv("DESTINATION_SESSION_FILE", "new10_destination_session.session")
PORT = int(os.getenv("PORT", 5000))

# OTP storage to avoid overwriting
otp_data = {
    'source': None,
    'destination': None
}

# Initialize Telegram clients
source_client = TelegramClient(SOURCE_SESSION_FILE, SOURCE_API_ID, SOURCE_API_HASH)
destination_client = TelegramClient(DESTINATION_SESSION_FILE, DESTINATION_API_ID, DESTINATION_API_HASH)

# Flask app setup
app = Flask(__name__)

@app.route('/')
def home():
    return "The bot is running. Use /receive_otp to send OTPs.", 200

@app.route('/receive_otp', methods=['POST'])
def receive_otp():
    """Receive OTP for login from Postman."""
    data = request.json
    account_type = data.get('account_type')  # 'source' or 'destination'
    otp = data.get('otp')

    if account_type in otp_data:
        otp_data[account_type] = otp
        return jsonify({"status": "OTP received", "account": account_type}), 200
    else:
        return jsonify({"error": "Invalid account type"}), 400

# Function to handle reconnection
async def handle_disconnection():
    while True:
        try:
            if not source_client.is_connected():
                await source_client.start()
            await source_client.run_until_disconnected()
        except Exception as e:
            print(f"Error: {e}. Reconnecting...")
            await asyncio.sleep(5)

# Function to log in using phone number and OTP
async def login_with_phone(client, phone_number, account_type):
    await client.connect()
    
    if not await client.is_user_authorized():
        print(f"Logging in with phone number: {phone_number}")
        await client.send_code_request(phone_number)
        
        print(f"Waiting for OTP for {account_type} account...")
        
        while otp_data[account_type] is None:
            await asyncio.sleep(1)

        otp = otp_data[account_type]
        if otp:
            await client.sign_in(phone_number, otp)
            print(f"Logged in successfully for {account_type}!")
        else:
            raise Exception(f"OTP not received for {account_type}")

# Event handler for messages
@source_client.on(events.NewMessage(chats=SOURCE_CHAT_ID))
async def forward_message(event):
    source_message = event.raw_text

    custom_message = f"""
"{source_message}"
 
If the text inside the double quotation marks is not a trading signal or indicates a short/sell, respond with:
👉 "No it's not your call"

If it is a long/buy trading signal, extract the necessary details and fill in the form below:

Symbol: Pair with USDT (without using /).

Price: Use the highest entry price.

Stop Loss: If given inside the quotation marks, use it; otherwise, calculate it as 0.5% below the entry price.

Take Profit: If provided, use the lowest take profit price; otherwise, calculate it as 2% above the entry price.

🔹 Output only the completed form—no extra text.
💡 Note: Inside the quotation marks, 'cmp' refers to the current market price, 'sl' is the stop loss, and 'tp' is the take profit.
"""

    try:
        await destination_client.send_message(DESTINATION_BOT_USERNAME, custom_message)
        print("Custom message forwarded to destination bot.")
    except Exception as e:
        print(f"Error while forwarding the message: {e}")

# Main function to start both clients
async def main():
    print("Starting both clients...")
    
    await login_with_phone(source_client, SOURCE_PHONE_NUMBER, 'source')
    await login_with_phone(destination_client, DESTINATION_PHONE_NUMBER, 'destination')
    
    await source_client.start()
    await destination_client.start()
    
    print("Bot is running... Waiting for messages...")
    await handle_disconnection()

# Function to run Flask in a separate thread
def run_flask():
    port = int(os.environ.get('PORT', 5000))
    app.run(host="0.0.0.0", port=port, debug=False)  # Disable debug in production

if __name__ == "__main__":
    # Start Flask server
    flask_thread = Thread(target=run_flask)
    flask_thread.start()

    # Run the bot with proper asyncio handling
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
