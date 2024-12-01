from telethon import TelegramClient
from flask import Flask, request, jsonify
import asyncio
import os
import time

# Setup Flask app
app = Flask(__name__)

# Environment Variables for API credentials and session files
source_api_id = os.getenv("SOURCE_API_ID")
source_api_hash = os.getenv("SOURCE_API_HASH")
destination_api_id = os.getenv("DEST_API_ID")
destination_api_hash = os.getenv("DEST_API_HASH")

source_session_file = "source_session.session"
destination_session_file = "destination_session.session"

# Flask Routes for receiving phone numbers and OTPs
@app.route('/enter_phone_source', methods=['POST'])
def enter_phone_source():
    phone_number_source = request.json.get("phone_number")
    if not phone_number_source:
        return jsonify({"error": "Phone number is required"}), 400
    global phone_number_source_global
    phone_number_source_global = phone_number_source
    return jsonify({"message": "Phone number received, please send OTP"}), 200


@app.route('/enter_otp_source', methods=['POST'])
def enter_otp_source():
    otp_source = request.json.get("otp")
    if not otp_source:
        return jsonify({"error": "OTP is required"}), 400
    global otp_source_global
    otp_source_global = otp_source
    return jsonify({"message": "OTP received, logging in..."}), 200


# Run Telegram Clients and Flask
async def start_source_client():
    source_client = TelegramClient(source_session_file, source_api_id, source_api_hash)

    # Send code request to get the OTP
    await source_client.send_code_request(phone_number_source_global)

    # Sign in using the OTP
    try:
        await source_client.sign_in(phone_number_source_global, otp_source_global)
    except Exception as e:
        print(f"Error during source client sign-in: {e}")
    
    print("Source client logged in.")
    await source_client.start()


# Start the Flask app and Telegram clients together
async def start_clients():
    # Start Flask server
    from threading import Thread
    def run_flask():
        app.run(host="0.0.0.0", port=10000)
    flask_thread = Thread(target=run_flask)
    flask_thread.start()

    # Wait before starting Telegram client
    await asyncio.sleep(2)
    # Start the Telegram source client
    await start_source_client()


if __name__ == "__main__":
    asyncio.run(start_clients())
