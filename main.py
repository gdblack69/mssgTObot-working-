from telethon import TelegramClient, events
import os
import asyncio
import traceback
from flask import Flask, request, jsonify
from threading import Thread

# API credentials for source chat
SOURCE_API_ID = os.getenv('SOURCE_API_ID')
SOURCE_API_HASH = os.getenv('SOURCE_API_HASH')
SOURCE_CHAT_ID = os.getenv('SOURCE_CHAT_ID')
SOURCE_PHONE_NUMBER = os.getenv('SOURCE_PHONE_NUMBER')  # Source phone number

# API credentials for destination account
DESTINATION_API_ID = os.getenv('DESTINATION_API_ID')
DESTINATION_API_HASH = os.getenv('DESTINATION_API_HASH')
DESTINATION_BOT_USERNAME = os.getenv('DESTINATION_BOT_USERNAME')
DESTINATION_PHONE_NUMBER = os.getenv('DESTINATION_PHONE_NUMBER')  # Destination phone number

# Paths for session files (use a fallback if environment variables are not set)
SOURCE_SESSION_FILE = os.getenv('SOURCE_SESSION_FILE', 'source_session.session')  # Default fallback value
DESTINATION_SESSION_FILE = os.getenv('DESTINATION_SESSION_FILE', 'destination_session.session')  # Default fallback value

# OTP storage
otp_data = {
    'source': None,
    'destination': None
}

# Initialize Telegram clients
source_client = TelegramClient(SOURCE_SESSION_FILE, SOURCE_API_ID, SOURCE_API_HASH)
destination_client = TelegramClient(DESTINATION_SESSION_FILE, DESTINATION_API_ID, DESTINATION_API_HASH)

# Flask application for receiving OTP via POST request
app = Flask(__name__)

@app.route('/receive_otp', methods=['POST'])
def receive_otp():
    data = request.json
    account_type = data.get('account_type')  # 'source' or 'destination'
    otp = data.get('otp')

    if account_type == 'source':
        otp_data['source'] = otp
    elif account_type == 'destination':
        otp_data['destination'] = otp

    return jsonify({"status": "OTP received", "account": account_type}), 200

# Function to handle disconnections and reconnections
async def handle_disconnection():
    while True:
        try:
            await source_client.run_until_disconnected()
        except Exception as e:
            print(f"Error: {e}. Reconnecting...")
            await asyncio.sleep(5)  # Wait before attempting to reconnect
            await source_client.start()  # Restart the client

# Function to log in using phone number and OTP from Postman
async def login_with_phone(client, phone_number, account_type):
    await client.connect()
    if not await client.is_user_authorized():
        print(f"Logging in with phone number: {phone_number}")
        await client.send_code_request(phone_number)
        
        # Wait for OTP to be received via Postman
        while otp_data.get(account_type) is None:
            await asyncio.sleep(1)  # Wait for the OTP to be posted

        otp = otp_data.get(account_type)
        if otp:
            await client.sign_in(phone_number, otp)
        else:
            print(f"Failed to receive OTP for {account_type}.")
            raise Exception(f"OTP not received for {account_type}")

# Event handler for messages in the source chat
@source_client.on(events.NewMessage(chats=SOURCE_CHAT_ID))
async def forward_message(event):
    # Extract the original message
    source_id_message = event.raw_text

    # Custom message format with highlighted source message
    custom_message = f"""
"{source_id_message}"

 If the quoted text within double quotation mark is not a trading signal, respond with "Processing your question....". If it is a trading signal, extract the necessary information and fill out the form below. The symbol should be paired with USDT. Use the highest entry price. The stop loss price will be taken from inside the double quotation mark and if it is not given then calculate it as 0.5% below the entry price. Use the lowest take profit price given inside the double quoted message and if none is provided then calculate take profit price as 2% above the entry price.Provide only the completed form, no other text.[Remember inside the double quotation mark 'cmp'= current market price, 'sl'= stop loss, 'tp'=take profit]


Symbol:
Price:
Stop Loss:
Take Profit:
Take Profit:
"""

    # Send the formatted message to the bot
    async with destination_client:
        try:
            await destination_client.send_message(DESTINATION_BOT_USERNAME, custom_message)
            print("Custom message forwarded to destination bot.")
        except Exception as e:
            print(f"Error while forwarding the message: {e}")

# Main function to start both clients
async def main():
    print("Starting both clients...")
    
    # Log in to the Telegram clients using the phone numbers
    await login_with_phone(source_client, SOURCE_PHONE_NUMBER, 'source')
    await login_with_phone(destination_client, DESTINATION_PHONE_NUMBER, 'destination')
    
    # Start both clients
    await source_client.start()
    await destination_client.start()
    print("Bot is running... Waiting for messages...")
    await handle_disconnection()  # Handle reconnections

# Entry point - running within the existing event loop
def run_flask():
    app.run(host="0.0.0.0", port=5000)

if __name__ == "__main__":
    # Start the Flask server in a separate thread
    flask_thread = Thread(target=run_flask)
    flask_thread.start()

    # Loop to restart the script in case of error
    async def run_bot():
        while True:  # Loop to restart the script on error
            try:
                # Run the main function within the existing event loop
                await main()
            except Exception as e:
                print(f"Error occurred: {e}. Restarting the script...")
                await asyncio.sleep(5)  # Optional sleep to prevent rapid restarts

    # Start the event loop to run the bot
    asyncio.run(run_bot())
