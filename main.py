from telethon import TelegramClient, events
import os
import asyncio
from flask import Flask, request, jsonify
from threading import Thread

# Replace with your actual credentials
SOURCE_API_ID = 26697231
SOURCE_API_HASH = "35f2769c773534c6ebf24c9d0731703a"
SOURCE_PHONE_NUMBER = "919598293175"
SOURCE_CHAT_ID = -1002256615512

DESTINATION_API_ID = 14135677
DESTINATION_API_HASH = "edbecdc187df07fddb10bcff89964a8e"
DESTINATION_PHONE_NUMBER = "+917897293175"
DESTINATION_BOT_USERNAME = "@gpt3_unlim_chatbot"

SOURCE_SESSION_FILE = "new10_souce_sehjhn.session"
DESTINATION_SESSION_FILE = "new10_desajhion_session.session"

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
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    # Start Flask server
    flask_thread = Thread(target=run_flask)
    flask_thread.start()

    # Run the bot with proper asyncio handling
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
