import os
import asyncio
from telethon import TelegramClient

# Validate environment variables
def validate_env_variables():
    required_env_vars = ['SOURCE_API_ID', 'SOURCE_API_HASH', 'DEST_API_ID', 'DEST_API_HASH', 'SOURCE_PHONE_NUMBER', 'DEST_PHONE_NUMBER']
    for var in required_env_vars:
        if not os.getenv(var):
            raise EnvironmentError(f"Missing required environment variable: {var}")

validate_env_variables()

# API credentials for source and destination accounts
SOURCE_API_ID = int(os.getenv('SOURCE_API_ID'))
SOURCE_API_HASH = os.getenv('SOURCE_API_HASH')
DEST_API_ID = int(os.getenv('DEST_API_ID'))
DEST_API_HASH = os.getenv('DEST_API_HASH')

# Session file names
SOURCE_SESSION_FILE = os.getenv('SOURCE_SESSION_FILE', 'source_session')
DEST_SESSION_FILE = os.getenv('DEST_SESSION_FILE', 'destination_session')

# Phone numbers for authentication
SOURCE_PHONE_NUMBER = os.getenv('SOURCE_PHONE_NUMBER')
DEST_PHONE_NUMBER = os.getenv('DEST_PHONE_NUMBER')

async def setup_client(session_file, api_id, api_hash, phone_number):
    """
    Sets up the Telegram client. Sends an OTP if the session is not already authorized.
    """
    client = TelegramClient(session_file, api_id, api_hash, device_model="Windows", system_version="10")
    try:
        await client.connect()
        if not await client.is_user_authorized():
            print(f"Sending OTP to phone number: {phone_number}")
            await client.send_code_request(phone_number)
            otp = input(f"Enter OTP for {phone_number}: ").strip()
            await client.sign_in(phone_number, otp)
            print(f"Logged in successfully for phone number: {phone_number}")
        else:
            print(f"Client already authorized for phone number: {phone_number}")
    except Exception as e:
        print(f"Error during setup for {phone_number}: {e}")
    return client

async def main():
    """
    Main function to set up source and destination clients.
    """
    source_client = await setup_client(SOURCE_SESSION_FILE, SOURCE_API_ID, SOURCE_API_HASH, SOURCE_PHONE_NUMBER)
    dest_client = await setup_client(DEST_SESSION_FILE, DEST_API_ID, DEST_API_HASH, DEST_PHONE_NUMBER)

    print("Both clients are connected and ready!")
    # Add your main functionality here

if __name__ == '__main__':
    asyncio.run(main())
