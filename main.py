import asyncio
import threading
from telethon import TelegramClient, events
from flask import Flask, request, jsonify
import os

# Flask app to keep the bot alive
app = Flask(__name__)

@app.route('/')
def home():
    return "The bot is running!"

# API to set credentials (phone number and OTP) for Telegram authentication
@app.route('/set_credentials', methods=['POST'])
def set_credentials():
    try:
        phone = request.json['phone']
        otp = request.json['otp']
        
        # Set the credentials globally to use in TelegramClient
        global PHONE_NUMBER, OTP
        PHONE_NUMBER = phone
        OTP = otp
        
        return jsonify({"status": "success", "message": "Credentials set successfully!"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

# API credentials (use environment variables here)
SOURCE_API_ID = os.getenv("SOURCE_API_ID")
SOURCE_API_HASH = os.getenv("SOURCE_API_HASH")
DESTINATION_API_ID = os.getenv("DESTINATION_API_ID")
DESTINATION_API_HASH = os.getenv("DESTINATION_API_HASH")
SOURCE_CHAT_ID = os.getenv("SOURCE_CHAT_ID")
DESTINATION_BOT_USERNAME = os.getenv("DESTINATION_BOT_USERNAME")
SOURCE_SESSION_FILE = os.getenv("SOURCE_SESSION_FILE")
DESTINATION_SESSION_FILE = os.getenv("DESTINATION_SESSION_FILE")

# Initialize Telegram clients
source_client = TelegramClient(SOURCE_SESSION_FILE, SOURCE_API_ID, SOURCE_API_HASH)
destination_client = TelegramClient(DESTINATION_SESSION_FILE, DESTINATION_API_ID, DESTINATION_API_HASH)

# Telegram login
async def login_to_telegram():
    global PHONE_NUMBER, OTP
    try:
        # Ensure credentials are provided via API
        if not PHONE_NUMBER or not OTP:
            raise ValueError("Phone number or OTP is not set.")
        
        await source_client.start(PHONE_NUMBER, code_callback=lambda: OTP)
        print("Successfully logged in to Telegram.")
    except Exception as e:
        print(f"Error logging in to Telegram: {e}")

# Function to forward messages
async def forward_message(event):
    if '"' in event.raw_text:
        source_id_message = event.raw_text
        custom_message = f"""
        "{source_id_message}"

        If the quoted text within double quotation mark is not a trading signal, respond with "Processing your question....". If it is a trading signal, extract the necessary information and fill out the form below. The symbol should be paired with USDT. Use the highest entry price. The stop loss price will be taken from inside the double quotation mark and if it is not given then calculate it as 0.5% below the entry price. Use the lowest take profit price given inside the double quoted message and if none is provided then calculate take profit price as 2% above the entry price. Provide only the completed form, no other text.[Remember inside the double quotation mark 'cmp'= current market price, 'sl'= stop loss, 'tp'= take profit]

        Symbol:
        Price:
        Stop Loss:
        Take Profit:
        Take Profit:
        """
        try:
            await destination_client.send_message(DESTINATION_BOT_USERNAME, custom_message)
            print("Custom message forwarded to destination bot.")
        except Exception as e:
            print(f"Error while forwarding the message: {e}")

# Main function to handle Telegram bot events and forward messages
async def start_clients():
    await login_to_telegram()
    await source_client.start()
    await destination_client.start()

    @source_client.on(events.NewMessage(chats=SOURCE_CHAT_ID))
    async def handle_new_message(event):
        await forward_message(event)

    print("Bot is running... Waiting for messages...")
    await source_client.run_until_disconnected()

# Function to start Flask in a separate thread
def run_flask():
    app.run(host="0.0.0.0", port=8080)  # Running Flask app on port 8080

# Run Flask and Telegram client on the same port
if __name__ == "__main__":
    # Run Flask app in a separate thread
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()
    
    # Run Telegram clients
    asyncio.run(start_clients())  # Start Telegram bot and listen for messages
