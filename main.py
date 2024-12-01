import asyncio
from flask import Flask, request, jsonify
from telethon import TelegramClient, events
import os
import traceback
import threading

# Flask App Initialization
app = Flask(__name__)

# Global Variables
phone_number_source_global = asyncio.Queue()
otp_source_global = asyncio.Queue()
phone_number_dest_global = asyncio.Queue()
otp_dest_global = asyncio.Queue()

# Function to check or create session files
def get_session_file(env_var, default_name):
    session_file = os.getenv(env_var)
    if not session_file:
        print(f"{env_var} not set. Creating a new session file: {default_name}")
        return default_name
    return session_file

# Telegram Credentials from Environment Variables
source_api_id = int(os.getenv("SOURCE_API_ID", 0))
source_api_hash = os.getenv("SOURCE_API_HASH", "")
source_session_file = get_session_file("SOURCE_SESSION_FILE", "source_session")

dest_api_id = int(os.getenv("DEST_API_ID", 0))
dest_api_hash = os.getenv("DEST_API_HASH", "")
dest_session_file = get_session_file("DEST_SESSION_FILE", "destination_session")

source_chat_id = os.getenv("SOURCE_CHAT_ID")
if source_chat_id:
    source_chat_id = int(source_chat_id)

destination_bot_username = os.getenv("DEST_BOT_USERNAME", "")

# Initialize Telegram Clients
source_client = TelegramClient(source_session_file, source_api_id, source_api_hash)
destination_client = TelegramClient(dest_session_file, dest_api_id, dest_api_hash)

# Flask Endpoints
@app.route('/enter_phone_source', methods=['POST'])
def enter_phone_source():
    data = request.json
    if 'phone_number' in data:
        asyncio.run_coroutine_threadsafe(phone_number_source_global.put(data['phone_number']), asyncio.get_event_loop())
        return jsonify({"message": "Source phone number received successfully."}), 200
    return jsonify({"error": "Phone number not provided."}), 400


@app.route('/enter_otp_source', methods=['POST'])
def enter_otp_source():
    data = request.json
    if 'otp' in data:
        asyncio.run_coroutine_threadsafe(otp_source_global.put(data['otp']), asyncio.get_event_loop())
        return jsonify({"message": "Source OTP received successfully."}), 200
    return jsonify({"error": "OTP not provided."}), 400


@app.route('/enter_phone_dest', methods=['POST'])
def enter_phone_dest():
    data = request.json
    if 'phone_number' in data:
        asyncio.run_coroutine_threadsafe(phone_number_dest_global.put(data['phone_number']), asyncio.get_event_loop())
        return jsonify({"message": "Destination phone number received successfully."}), 200
    return jsonify({"error": "Phone number not provided."}), 400


@app.route('/enter_otp_dest', methods=['POST'])
def enter_otp_dest():
    data = request.json
    if 'otp' in data:
        asyncio.run_coroutine_threadsafe(otp_dest_global.put(data['otp']), asyncio.get_event_loop())
        return jsonify({"message": "Destination OTP received successfully."}), 200
    return jsonify({"error": "OTP not provided."}), 400


# Telegram Client Initialization and Verification
async def start_source_client():
    print("Waiting for source phone number...")
    phone_number = await phone_number_source_global.get()
    try:
        print(f"Sending OTP to source phone number: {phone_number}")
        await source_client.send_code_request(phone_number)

        print("Waiting for source OTP...")
        otp = await otp_source_global.get()

        print("Logging in source account...")
        await source_client.sign_in(phone_number, otp)
        print("Source client logged in successfully!")
        await source_client.start()

    except Exception as e:
        print(f"Error during source client setup: {e}")


async def start_dest_client():
    print("Waiting for destination phone number...")
    phone_number = await phone_number_dest_global.get()
    try:
        print(f"Sending OTP to destination phone number: {phone_number}")
        await destination_client.send_code_request(phone_number)

        print("Waiting for destination OTP...")
        otp = await otp_dest_global.get()

        print("Logging in destination account...")
        await destination_client.sign_in(phone_number, otp)
        print("Destination client logged in successfully!")
        await destination_client.start()

    except Exception as e:
        print(f"Error during destination client setup: {e}")


async def start_clients():
    await asyncio.gather(
        start_source_client(),
        start_dest_client()
    )


# Function to run Telegram clients in a separate thread
def run_telegram_clients():
    asyncio.run(start_clients())

# Main Function with Flask and Telegram Integration
if __name__ == "__main__":
    # Run Telegram clients in a separate thread
    telegram_thread = threading.Thread(target=run_telegram_clients)
    telegram_thread.start()

    # Start Flask app
    port = int(os.getenv("PORT", 5000))  # Use the PORT variable provided by Render
    app.run(host="0.0.0.0", port=port)
