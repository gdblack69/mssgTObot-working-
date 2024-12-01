import asyncio
from flask import Flask, request, jsonify
from telethon import TelegramClient, events
import os
import traceback

# Flask App Initialization
app = Flask(__name__)

# Global Variables
phone_number_source_global = None
otp_source_global = None
phone_number_dest_global = None
otp_dest_global = None

# Telegram Credentials from Environment Variables
source_api_id = int(os.getenv("SOURCE_API_ID"))
source_api_hash = os.getenv("SOURCE_API_HASH")
source_session_file = os.getenv("SOURCE_SESSION_FILE")
source_chat_id = int(os.getenv("SOURCE_CHAT_ID"))

dest_api_id = int(os.getenv("DEST_API_ID"))
dest_api_hash = os.getenv("DEST_API_HASH")
dest_session_file = os.getenv("DEST_SESSION_FILE")
destination_bot_username = os.getenv("DEST_BOT_USERNAME")

# Initialize Telegram Clients
source_client = TelegramClient(source_session_file, source_api_id, source_api_hash)
destination_client = TelegramClient(dest_session_file, dest_api_id, dest_api_hash)

# Flask Endpoints
@app.route('/enter_phone_source', methods=['POST'])
def enter_phone_source():
    global phone_number_source_global
    data = request.json
    if 'phone_number' in data:
        phone_number_source_global = data['phone_number']
        return jsonify({"message": "Source phone number received successfully."}), 200
    return jsonify({"error": "Phone number not provided."}), 400


@app.route('/enter_otp_source', methods=['POST'])
def enter_otp_source():
    global otp_source_global
    data = request.json
    if 'otp' in data:
        otp_source_global = data['otp']
        return jsonify({"message": "Source OTP received successfully."}), 200
    return jsonify({"error": "OTP not provided."}), 400


@app.route('/enter_phone_dest', methods=['POST'])
def enter_phone_dest():
    global phone_number_dest_global
    data = request.json
    if 'phone_number' in data:
        phone_number_dest_global = data['phone_number']
        return jsonify({"message": "Destination phone number received successfully."}), 200
    return jsonify({"error": "Phone number not provided."}), 400


@app.route('/enter_otp_dest', methods=['POST'])
def enter_otp_dest():
    global otp_dest_global
    data = request.json
    if 'otp' in data:
        otp_dest_global = data['otp']
        return jsonify({"message": "Destination OTP received successfully."}), 200
    return jsonify({"error": "OTP not provided."}), 400


# Telegram Message Forwarding Logic
@source_client.on(events.NewMessage(chats=source_chat_id))
async def forward_message(event):
    source_message = event.raw_text

    custom_message = f"""
"{source_message}"

If the quoted text within double quotation marks is not a trading signal, respond with "Processing your question....". If it is a trading signal, extract the necessary information and fill out the form below. The symbol should be paired with USDT. Use the highest entry price. The stop loss price will be taken from inside the double quotation marks and, if not provided, calculate it as 0.5% below the entry price. Use the lowest take profit price inside the message and, if none is provided, calculate it as 2% above the entry price. Provide only the completed form; no other text.

[Remember inside the double quotation mark 'cmp'= current market price, 'sl'= stop loss, 'tp'=take profit.]

Symbol:
Price:
Stop Loss:
Take Profit:
"""
    try:
        await destination_client.send_message(destination_bot_username, custom_message)
        print("Custom message forwarded to the destination bot.")
    except Exception as e:
        print(f"Error while forwarding the message: {e}")


# Telegram Client Initialization and Verification
async def start_source_client():
    global phone_number_source_global, otp_source_global

    while not phone_number_source_global:
        print("Waiting for source phone number...")
        await asyncio.sleep(5)

    try:
        print(f"Sending OTP to source phone number: {phone_number_source_global}")
        await source_client.send_code_request(phone_number_source_global)

        while not otp_source_global:
            print("Waiting for source OTP...")
            await asyncio.sleep(5)

        print("Logging in source account...")
        await source_client.sign_in(phone_number_source_global, otp_source_global)
        print("Source client logged in successfully!")
        await source_client.start()

    except Exception as e:
        print(f"Error during source client setup: {e}")


async def start_dest_client():
    global phone_number_dest_global, otp_dest_global

    while not phone_number_dest_global:
        print("Waiting for destination phone number...")
        await asyncio.sleep(5)

    try:
        print(f"Sending OTP to destination phone number: {phone_number_dest_global}")
        await destination_client.send_code_request(phone_number_dest_global)

        while not otp_dest_global:
            print("Waiting for destination OTP...")
            await asyncio.sleep(5)

        print("Logging in destination account...")
        await destination_client.sign_in(phone_number_dest_global, otp_dest_global)
        print("Destination client logged in successfully!")
        await destination_client.start()

    except Exception as e:
        print(f"Error during destination client setup: {e}")


async def start_clients():
    await asyncio.gather(
        start_source_client(),
        start_dest_client()
    )


# Main Function with Correct Port Binding
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))  # Use the PORT variable provided by Render
    loop = asyncio.get_event_loop()
    loop.create_task(start_clients())
    app.run(host="0.0.0.0", port=port)
