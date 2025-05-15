from telethon import TelegramClient, events
import os
import asyncio
import traceback
from flask import Flask, request, jsonify
from threading import Thread

# Credentials and constants
SOURCE_API_ID = 26697231
SOURCE_API_HASH = "35f2769c773534c6ebf24c9d0731703a"
SOURCE_PHONE_NUMBER = "919598293175"
SOURCE_CHAT_ID = -1002256615512

DESTINATION_API_ID = 14135677
DESTINATION_API_HASH = "edbecdc187df07fddb10bcff89964a8e"
DESTINATION_PHONE_NUMBER = "+917897293175"
DESTINATION_BOT_USERNAME = "@gpt3_unlim_chatbot"

SOURCE_SESSION_FILE = "new10_source.session"
DESTINATION_SESSION_FILE = "new10_destination.session"

otp_events = {
    'source': asyncio.Event(),
    'destination': asyncio.Event()
}
otp_data = {
    'source': None,
    'destination': None
}

# Telegram clients
source_client = TelegramClient(SOURCE_SESSION_FILE, SOURCE_API_ID, SOURCE_API_HASH)
destination_client = TelegramClient(DESTINATION_SESSION_FILE, DESTINATION_API_ID, DESTINATION_API_HASH)

# Flask app
app = Flask(__name__)

@app.route('/')
def home():
    return "The bot is running. Use /receive_otp to send OTPs.", 200

@app.route('/receive_otp', methods=['POST'])
def receive_otp():
    data = request.json
    account_type = data.get('account_type')
    otp = data.get('otp')

    if account_type in otp_data:
        otp_data[account_type] = otp
        otp_events[account_type].set()
        return jsonify({"status": "OTP received", "account": account_type}), 200
    return jsonify({"error": "Invalid account type"}), 400

# Login function with clean async event
async def login_with_phone(client, phone_number, account_type):
    await client.connect()
    if not await client.is_user_authorized():
        print(f"[{account_type}] Sending code...")
        await client.send_code_request(phone_number)
        print(f"[{account_type}] Waiting for OTP...")
        await otp_events[account_type].wait()
        await client.sign_in(phone_number, otp_data[account_type])
        print(f"[{account_type}] Logged in successfully!")

# Message forwarder
@source_client.on(events.NewMessage(chats=SOURCE_CHAT_ID))
async def forward_message(event):
    custom_message = f'''
"{event.raw_text}"
 
If the text inside the double quotation marks is not a trading signal or indicates a short/sell, respond with:
👉 "No it's not your call"

If it is a long/buy trading signal, extract the necessary details and fill in the form below:

Symbol: Pair with USDT (without using /).

Price: Use the highest entry price.

Stop Loss: If given inside the quotation marks, use it; otherwise, calculate it as 0.5% below the entry price.

Take Profit: If provided, use the lowest take profit price; otherwise, calculate it as 2% above the entry price.

🔹 Output only the completed form—no extra text.
💡 Note: Inside the quotation marks, 'cmp' refers to the current market price, 'sl' is the stop loss, and 'tp' is the take profit.
'''
    try:
        await destination_client.send_message(DESTINATION_BOT_USERNAME, custom_message)
        print("Message forwarded.")
    except Exception as e:
        print(f"Forward error: {traceback.format_exc()}")

# Resilient reconnect handler for both clients
async def handle_clients():
    while True:
        try:
            await asyncio.gather(
                source_client.run_until_disconnected(),
                destination_client.run_until_disconnected()
            )
        except Exception:
            print(f"Disconnected! Restarting...\n{traceback.format_exc()}")
            await asyncio.sleep(5)

# Main bot runner
async def main():
    await asyncio.gather(
        login_with_phone(source_client, SOURCE_PHONE_NUMBER, 'source'),
        login_with_phone(destination_client, DESTINATION_PHONE_NUMBER, 'destination')
    )
    print("Both clients ready.")
    await handle_clients()

# Flask runner
def run_flask():
    port = int(os.environ.get('PORT', 5000))
    app.run(host="0.0.0.0", port=port, threaded=True)

# Entry point
if __name__ == "__main__":
    Thread(target=run_flask, daemon=True).start()
    asyncio.run(main())
