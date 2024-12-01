from flask import Flask, request, jsonify
import asyncio
from telethon.sync import TelegramClient
from telethon.errors import RPCError

app = Flask(__name__)

# Replace these with your actual Telegram API credentials
API_ID = "your_api_id"
API_HASH = "your_api_hash"
SOURCE_PHONE_NUMBER = "source_phone_number"  # Replace with your source phone number
DEST_PHONE_NUMBER = "destination_phone_number"  # Replace with your destination phone number

# Sessions files for Telethon
SOURCE_SESSION_FILE = "source_session"
DEST_SESSION_FILE = "destination_session"

# Telethon clients for source and destination
source_client = TelegramClient(SOURCE_SESSION_FILE, API_ID, API_HASH)
destination_client = TelegramClient(DEST_SESSION_FILE, API_ID, API_HASH)

@app.route('/send-otp', methods=['POST'])
def send_otp():
    data = request.get_json()
    phone_number = data.get('phone_number')
    
    if not phone_number:
        return jsonify({"error": "Phone number is required"}), 400

    try:
        if phone_number == SOURCE_PHONE_NUMBER:
            asyncio.run(send_otp_to_source())
        elif phone_number == DEST_PHONE_NUMBER:
            asyncio.run(send_otp_to_destination())
        else:
            return jsonify({"error": "Invalid phone number"}), 400
        
        return jsonify({"message": "OTP sent successfully"}), 200

    except RPCError as e:
        return jsonify({"error": f"Failed to send OTP: {str(e)}"}), 500

async def send_otp_to_source():
    print(f"Sending OTP to source phone number: {SOURCE_PHONE_NUMBER}")
    await source_client.connect()
    await source_client.send_code_request(SOURCE_PHONE_NUMBER)

async def send_otp_to_destination():
    print(f"Sending OTP to destination phone number: {DEST_PHONE_NUMBER}")
    await destination_client.connect()
    await destination_client.send_code_request(DEST_PHONE_NUMBER)

# Start the Flask server
if __name__ == "__main__":
    app.run(debug=True)
