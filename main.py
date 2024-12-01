import os
import asyncio
from telethon import TelegramClient
from telethon.errors import ConnectionError

# Load API credentials from environment variables
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")

# Set session file paths
source_session_file = os.getenv("SOURCE_SESSION_FILE", "source_session")
destination_session_file = os.getenv("DEST_SESSION_FILE", "destination_session")

# Proxy configuration (optional, replace with valid proxy details if needed)
PROXY = None  # Example: ('socks5', 'proxy_host', proxy_port)

# Ensure required environment variables are set
if not API_ID or not API_HASH:
    raise ValueError("API_ID and API_HASH must be set as environment variables.")

async def safe_connect(client):
    """Attempt to connect to Telegram with retries."""
    retries = 3
    for attempt in range(retries):
        try:
            await client.connect()
            if client.is_connected():
                print(f"Connected successfully with session: {client.session.filename}")
                return True
        except ConnectionError:
            print(f"Connection attempt {attempt + 1} failed. Retrying...")
            await asyncio.sleep(2)
    raise ConnectionError("Unable to connect to Telegram after retries.")

async def setup_source_client():
    """Set up and authenticate the source client."""
    async with TelegramClient(source_session_file, API_ID, API_HASH, proxy=PROXY) as source_client:
        await safe_connect(source_client)
        if not await source_client.is_user_authorized():
            source_phone_number = os.getenv("SOURCE_PHONE_NUMBER")
            if not source_phone_number:
                raise ValueError("SOURCE_PHONE_NUMBER environment variable is not set.")
            
            print(f"Sending OTP to source phone number: {source_phone_number}")
            await source_client.send_code_request(source_phone_number)
            source_otp = os.getenv("SOURCE_OTP")
            if not source_otp:
                raise ValueError("SOURCE_OTP environment variable is not set.")
            await source_client.sign_in(source_phone_number, source_otp)
        return source_client

async def setup_destination_client():
    """Set up and authenticate the destination client."""
    async with TelegramClient(destination_session_file, API_ID, API_HASH, proxy=PROXY) as destination_client:
        await safe_connect(destination_client)
        if not await destination_client.is_user_authorized():
            destination_phone_number = os.getenv("DEST_PHONE_NUMBER")
            if not destination_phone_number:
                raise ValueError("DEST_PHONE_NUMBER environment variable is not set.")
            
            print(f"Sending OTP to destination phone number: {destination_phone_number}")
            await destination_client.send_code_request(destination_phone_number)
            destination_otp = os.getenv("DEST_OTP")
            if not destination_otp:
                raise ValueError("DEST_OTP environment variable is not set.")
            await destination_client.sign_in(destination_phone_number, destination_otp)
        return destination_client

async def main():
    """Main function to handle both clients."""
    await asyncio.gather(
        setup_source_client(),
        setup_destination_client()
    )

if __name__ == "__main__":
    asyncio.run(main())
