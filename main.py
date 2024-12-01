from flask import Flask, request, jsonify
import asyncio
from telethon.sync import TelegramClient
from telethon.errors import RPCError

app = Flask(__name__)

# Replace these with your actual Telegram API credentials for two accounts
API_ID_SOURCE = 26697231  # Replace with your actual API ID for source account (integer)
API_HASH_SOURCE = "35f2769c773534c6ebf24c9d0731703a"  # Replace with your actual API Hash for source account (string)

API_ID_DEST = 14135677  # Replace with your actual API ID for destination account (integer)
API_HASH_DEST = "edbecdc187df07fddb10bcff89964a8e"  # Replace with your actual API Hash for destination account (string)

SOURCE_PHONE_NUMBER = "918400477507"  # Replace with your source phone number
DEST_PHONE_NUMBER = "917897293175"  # Replace with your destination phone number

# Sessions files for Telethon
SOURCE_SESSION_FILE = "source_session"
DEST_SESSION_FILE = "destination_session"

# Telethon clients for source and destination
source_client = TelegramClient(SOURCE_SESSION_FILE, API_ID_SOURCE, API_HASH_SOURCE)
destination_client = TelegramClient(DEST_SESSION_FILE, API_ID_DEST, API_HASH_DEST)

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
