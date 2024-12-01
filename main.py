import os
import asyncio
from telethon import TelegramClient, events
from flask import Flask, request
from keep_alive import keep_alive  # Flask app to keep the bot alive

# Flask app to handle API requests
app = Flask(__name__)

# Initialize Telegram clients
source_client = None
destination_client = None

# Variables to store credentials and phone number/OTP
source_api_id = os.getenv("SOURCE_API_ID")
source_api_hash = os.getenv("SOURCE_API_HASH")
source_session_file = "source_session"
destination_api_id = os.getenv("DESTINATION_API_ID")
destination_api_hash = os.getenv("DESTINATION_API_HASH")
destination_session_file = "destination_session"

phone_number_source = None
phone_number_destination = None
otp_source = None
otp_destination = None

# Step 1: API to enter phone number for source account
@app.route('/enter_phone_source', methods=['POST'])
def enter_phone_source():
    global phone_number_source
    phone_number_source = request.json.get("phone_number")
    return {"message": "Phone number for source account received. Please check your Telegram for OTP."}, 200

# Step 2: API to enter OTP for source account
@app.route('/enter_otp_source', methods=['POST'])
def enter_otp_source():
    global otp_source
    otp_source = request.json.get("otp")
    return {"message": "OTP for source account received."}, 200

# Step 3: API to enter phone number for destination account
@app.route('/enter_phone_destination', methods=['POST'])
def enter_phone_destination():
    global phone_number_destination
    phone_number_destination = request.json.get("phone_number")
    return {"message": "Phone number for destination account received. Please check your Telegram for OTP."}, 200

# Step 4: API to enter OTP for destination account
@app.route('/enter_otp_destination', methods=['POST'])
def enter_otp_destination():
    global otp_destination
    otp_destination = request.json.get("otp")
    return {"message": "OTP for destination account received."}, 200

# Function to start source client
async def start_source_client():
    global source_client
    source_client = TelegramClient(source_session_file, source_api_id, source_api_hash)
    await source_client.start(phone=phone_number_source, code=otp_source)
    print("Source client started.")

# Function to start destination client
async def start_destination_client():
    global destination_client
    destination_client = TelegramClient(destination_session_file, destination_api_id, destination_api_hash)
    await destination_client.start(phone=phone_number_destination, code=otp_destination)
    print("Destination client started.")

# Function to forward message
async def forward_message(event):
    if '"' in event.raw_text:
        source_id_message = event.raw_text
        custom_message = f"""
        "{source_id_message}"
        """
        try:
            await destination_client.send_message("@destination_bot", custom_message)
            print("Custom message forwarded to destination bot.")
        except Exception as e:
            print(f"Error while forwarding the message: {e}")

# Function to start the main clients
async def start_clients():
    await start_source_client()
    await start_destination_client()

    @source_client.on(events.NewMessage())
    async def handle_new_message(event):
        await forward_message(event)

    await source_client.run_until_disconnected()

if __name__ == "__main__":
    keep_alive()  # Keep Flask alive
    asyncio.run(start_clients())  # Run Telegram clients and Flask together
