import os
import asyncio
from flask import Flask, request, jsonify
from telethon import TelegramClient, events
from telethon.errors import FloodWaitError, SessionPasswordNeededError
from threading import Thread
from b2sdk.v2 import InMemoryAccountInfo, B2Api
from dotenv import load_dotenv

# === LOAD ENV ===
load_dotenv()

# === CONFIG ===
SOURCE_API_ID = os.environ.get('SOURCE_API_ID')
SOURCE_API_HASH = os.environ.get('SOURCE_API_HASH')
SOURCE_PHONE_NUMBER = os.environ.get('SOURCE_PHONE_NUMBER')
SOURCE_CHAT_ID = os.environ.get('SOURCE_CHAT_ID')

DESTINATION_API_ID = os.environ.get('DESTINATION_API_ID')
DESTINATION_API_HASH = os.environ.get('DESTINATION_API_HASH')
DESTINATION_PHONE_NUMBER = os.environ.get('DESTINATION_PHONE_NUMBER')
DESTINATION_BOT_USERNAME = os.environ.get('DESTINATION_BOT_USERNAME')

SESSION_DIR = os.environ.get('SESSION_DIR', ".")
SOURCE_SESSION_NAME = os.environ.get('SOURCE_SESSION_NAME', "source_session.session")
DESTINATION_SESSION_NAME = os.environ.get('DESTINATION_SESSION_NAME', "destination_session.session")
SOURCE_SESSION_FILE = os.path.join(SESSION_DIR, SOURCE_SESSION_NAME)
DESTINATION_SESSION_FILE = os.path.join(SESSION_DIR, DESTINATION_SESSION_NAME)

B2_KEY_ID = os.environ.get('B2_KEY_ID')
B2_APP_KEY = os.environ.get('B2_APP_KEY')
B2_BUCKET_NAME = os.environ.get('B2_BUCKET_NAME')

otp_data = {'source': None, 'destination': None}
otp_request_sent = {'source': False, 'destination': False}

# === B2 HELPERS ===
def init_b2_api():
    info = InMemoryAccountInfo()
    b2_api = B2Api(info)
    b2_api.authorize_account("production", B2_KEY_ID, B2_APP_KEY)
    return b2_api

def download_session_from_b2(session_name, local_path):
    try:
        b2_api = init_b2_api()
        bucket = b2_api.get_bucket_by_name(B2_BUCKET_NAME)
        downloaded_file = bucket.download_file_by_name(session_name)
        downloaded_file.save_to(local_path)
        print(f"✅ Downloaded {session_name} from B2.")
    except Exception as e:
        print(f"⚠️ Warning: Could not download {session_name} from B2: {e}")

def upload_session_to_b2(session_name, local_path):
    try:
        if not os.path.exists(local_path):
            print(f"⚠️ Warning: Local session file {local_path} not found.")
            return
        b2_api = init_b2_api()
        bucket = b2_api.get_bucket_by_name(B2_BUCKET_NAME)
        with open(local_path, "rb") as f:
            bucket.upload_bytes(f.read(), session_name)
        print(f"✅ Uploaded {session_name} to B2.")
    except Exception as e:
        print(f"❌ Error uploading {session_name} to B2: {e}")

# === ENV VALIDATION ===
required_vars = {
    'SOURCE_API_ID': SOURCE_API_ID,
    'SOURCE_API_HASH': SOURCE_API_HASH,
    'SOURCE_PHONE_NUMBER': SOURCE_PHONE_NUMBER,
    'SOURCE_CHAT_ID': SOURCE_CHAT_ID,
    'DESTINATION_API_ID': DESTINATION_API_ID,
    'DESTINATION_API_HASH': DESTINATION_API_HASH,
    'DESTINATION_PHONE_NUMBER': DESTINATION_PHONE_NUMBER,
    'DESTINATION_BOT_USERNAME': DESTINATION_BOT_USERNAME,
    'B2_KEY_ID': B2_KEY_ID,
    'B2_APP_KEY': B2_APP_KEY,
    'B2_BUCKET_NAME': B2_BUCKET_NAME
}
missing_vars = [key for key, value in required_vars.items() if not value]
if missing_vars:
    raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

try:
    SOURCE_API_ID = int(SOURCE_API_ID)
    SOURCE_CHAT_ID = int(SOURCE_CHAT_ID)
    DESTINATION_API_ID = int(DESTINATION_API_ID)
except ValueError as e:
    raise ValueError("SOURCE_API_ID, SOURCE_CHAT_ID, DESTINATION_API_ID must be integers") from e

# === TELEGRAM CLIENTS ===
download_session_from_b2(SOURCE_SESSION_NAME, SOURCE_SESSION_FILE)
download_session_from_b2(DESTINATION_SESSION_NAME, DESTINATION_SESSION_FILE)

source_client = TelegramClient(SOURCE_SESSION_FILE, SOURCE_API_ID, SOURCE_API_HASH)
destination_client = TelegramClient(DESTINATION_SESSION_FILE, DESTINATION_API_ID, DESTINATION_API_HASH)

# === FLASK APP ===
app = Flask(__name__)

@app.route('/')
def home():
    return "Telegram Bot is running. Use /receive_otp to send OTPs."

@app.route('/receive_otp', methods=['POST'])
def receive_otp():
    data = request.json
    account_type = data.get('account_type')
    otp = data.get('otp')
    if account_type not in otp_data:
        return jsonify({"error": "Invalid account type. Must be 'source' or 'destination'."}), 400
    otp_data[account_type] = otp
    return jsonify({"status": "OTP received successfully", "account": account_type}), 200

async def login_with_phone(client, phone_number, account_type, session_name, session_file):
    try:
        await client.connect()
        if not await client.is_user_authorized():
            if not otp_request_sent[account_type]:
                try:
                    await client.send_code_request(phone_number)
                    otp_request_sent[account_type] = True
                    print(f"📨 OTP sent to {phone_number} for {account_type}.")
                except FloodWaitError as e:
                    print(f"⏳ Too many requests for {account_type}, wait {e.seconds}s.")
                    return False
                except Exception as e:
                    print(f"❌ Error requesting OTP for {account_type}: {str(e)}")
                    return False
            while otp_data[account_type] is None:
                await asyncio.sleep(1)
            try:
                await client.sign_in(phone_number, otp_data[account_type])
                upload_session_to_b2(session_name, session_file)
                print(f"✅ Login successful for {account_type}.")
                return True
            except SessionPasswordNeededError:
                print(f"🔒 2FA not supported for {account_type}.")
                return False
            except Exception as e:
                print(f"❌ Invalid OTP for {account_type}: {str(e)}")
                otp_data[account_type] = None
                return False
        else:
            print(f"✅ {account_type.capitalize()} already authorized.")
            return True
    except Exception as e:
        print(f"❌ Login error for {account_type}: {str(e)}")
        return False

@source_client.on(events.NewMessage(chats=SOURCE_CHAT_ID))
async def forward_message(event):
    message = event.raw_text
    custom_message = f"""
"{message}"

If the text inside double quotes is not a trading signal or says to short/sell, reply with:
👉 "No it's not your call"

If it's a buy/long signal, extract the details and fill the form like this:

Symbol: Use the coin name with 'USDT' (without '/').
Price: Take the highest entry price.
Stop Loss : If given, use that.
If not given, calculate 1.88% below the entry price.
Take Profit : If given, use the lowest TP price.
If not given, calculate 2% above the entry price.

🔹 Output only the filled form, no extra text.

💡 Notes: 'cmp' = current market price
           'sl' = stop loss
           'tp' = take profit
"""
    try:
        await destination_client.send_message(DESTINATION_BOT_USERNAME, custom_message)
        print("✅ Message forwarded to destination bot.")
    except Exception as e:
        print(f"❌ Error forwarding message: {str(e)}")

async def start_bot():
    print("🚀 Starting Telegram bot...")
    source_ok = await login_with_phone(source_client, SOURCE_PHONE_NUMBER, 'source', SOURCE_SESSION_NAME, SOURCE_SESSION_FILE)
    if not source_ok:
        print("❌ Source login failed.")
        return
    dest_ok = await login_with_phone(destination_client, DESTINATION_PHONE_NUMBER, 'destination', DESTINATION_SESSION_NAME, DESTINATION_SESSION_FILE)
    if not dest_ok:
        print("❌ Destination login failed.")
        return
    await source_client.start()
    await destination_client.start()
    print("✅ Both clients running.")
    await source_client.run_until_disconnected()

def run_flask():
    port = int(os.environ.get('PORT', 5000))
    print(f"🌐 Starting Flask on port {port}...")
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    Thread(target=run_flask).start()
    asyncio.run(start_bot())
