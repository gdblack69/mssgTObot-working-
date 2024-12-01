import asyncio
from telethon import TelegramClient
import os

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
source_phone_number = os.getenv("SOURCE_PHONE_NUMBER")
source_otp = os.getenv("SOURCE_OTP")

dest_api_id = int(os.getenv("DEST_API_ID", 0))
dest_api_hash = os.getenv("DEST_API_HASH", "")
dest_session_file = get_session_file("DEST_SESSION_FILE", "destination_session")
dest_phone_number = os.getenv("DEST_PHONE_NUMBER")
dest_otp = os.getenv("DEST_OTP")

# Initialize Telegram Clients
source_client = TelegramClient(source_session_file, source_api_id, source_api_hash)
destination_client = TelegramClient(dest_session_file, dest_api_id, dest_api_hash)

# Telegram Client Initialization and Verification
async def setup_source_client():
    if not source_phone_number:
        raise ValueError("SOURCE_PHONE_NUMBER environment variable is not set.")

    print(f"Sending OTP to source phone number: {source_phone_number}")
    await source_client.send_code_request(source_phone_number)

    if not source_otp:
        raise ValueError("SOURCE_OTP environment variable is not set.")

    print("Logging in source account...")
    await source_client.sign_in(source_phone_number, source_otp)
    print("Source client logged in successfully!")
    await source_client.start()


async def setup_dest_client():
    if not dest_phone_number:
        raise ValueError("DEST_PHONE_NUMBER environment variable is not set.")

    print(f"Sending OTP to destination phone number: {dest_phone_number}")
    await destination_client.send_code_request(dest_phone_number)

    if not dest_otp:
        raise ValueError("DEST_OTP environment variable is not set.")

    print("Logging in destination account...")
    await destination_client.sign_in(dest_phone_number, dest_otp)
    print("Destination client logged in successfully!")
    await destination_client.start()


async def main():
    await asyncio.gather(
        setup_source_client(),
        setup_dest_client()
    )


if __name__ == "__main__":
    asyncio.run(main())
