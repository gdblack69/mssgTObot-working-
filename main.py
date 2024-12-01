import asyncio
from keep_alive import keep_alive  # Flask app to keep the bot alive
from telethon import TelegramClient, events
import os
import config  # Import config with your credentials

# API credentials from config.py
SOURCE_API_ID=config.SOURCE_API_ID
SOURCE_API_HASH=config.SOURCE_API_HASH
SOURCE_CHAT_ID=config.SOURCE_CHAT_ID
DESTINATION_API_ID=config.DESTINATION_API_ID
DESTINATION_API_HASH=config.DESTINATION_API_HASH
DESTINATION_BOT_USERNAME=config.DESTINATION_BOT_USERNAME
SOURCE_SESSION_FILE=config.SOURCE_SESSION_FILE
DESTINATION_SESSION_FILE=config.DESTINATION_SESSION_FILE

# Initialize Telegram clients
source_client = TelegramClient(SOURCE_SESSION_FILE, SOURCE_API_ID, SOURCE_API_HASH)
destination_client = TelegramClient(DESTINATION_SESSION_FILE, DESTINATION_API_ID, DESTINATION_API_HASH)

async def forward_message(event):
    if '"' in event.raw_text:
        source_id_message = event.raw_text
        custom_message = f"""
"{source_id_message}"
"""
        try:
            await destination_client.send_message(DESTINATION_BOT_USERNAME, custom_message)
            print("Custom message forwarded to destination bot.")
        except Exception as e:
            print(f"Error while forwarding the message: {e}")

async def start_clients():
    await source_client.start()
    await destination_client.start()

    @source_client.on(events.NewMessage(chats=SOURCE_CHAT_ID))
    async def handle_new_message(event):
        await forward_message(event)

    print("Bot is running... Waiting for messages...")
    await source_client.run_until_disconnected()

if __name__ == "__main__":
    keep_alive()  # Start Flask to keep the bot alive
    asyncio.run(start_clients())  # Run the clients in the same process
