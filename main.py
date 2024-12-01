import asyncio
import os
from telethon import TelegramClient, events
from keep_alive import keep_alive  # Import Flask app to keep the bot alive

# API credentials from environment variables
source_api_id = int(os.getenv('SOURCE_API_ID'))  # Replace with your first API ID
source_api_hash = os.getenv('SOURCE_API_HASH')  # Replace with your first API Hash
source_chat_id = int(os.getenv('SOURCE_CHAT_ID'))  # Replace with the chat ID to listen to

# API credentials for destination account
destination_api_id = int(os.getenv('DESTINATION_API_ID'))  # Replace with your second API ID
destination_api_hash = os.getenv('DESTINATION_API_HASH')  # Replace with your second API Hash
destination_bot_username = os.getenv('DESTINATION_BOT_USERNAME')  # Replace with the bot's username

# Paths for session files from environment variables
source_session_file = os.getenv('SOURCE_SESSION_FILE')  # Replace with the path to your source session file
destination_session_file = os.getenv('DESTINATION_SESSION_FILE')  # Replace with the path to your destination session file

# Check if session files exist before starting
if not os.path.exists(source_session_file):
    print(f"Warning: Source session file '{source_session_file}' not found!")
if not os.path.exists(destination_session_file):
    print(f"Warning: Destination session file '{destination_session_file}' not found!")

# Initialize Telegram clients with session files from environment variables
source_client = TelegramClient(source_session_file, source_api_id, source_api_hash)
destination_client = TelegramClient(destination_session_file, destination_api_id, destination_api_hash)

# Function to handle disconnections and reconnections
async def handle_disconnection():
    while True:
        try:
            await source_client.run_until_disconnected()
        except Exception as e:
            print(f"Error: {e}. Reconnecting...")
            await asyncio.sleep(5)  # Wait before attempting to reconnect
            await source_client.start()  # Restart the client

# Event handler for messages in the source chat
@source_client.on(events.NewMessage(chats=source_chat_id))
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
            await destination_client.send_message(destination_bot_username, custom_message)
            print("Custom message forwarded to destination bot.")
        except Exception as e:
            print(f"Error while forwarding the message: {e}")

# Main function to start both clients
async def main():
    print("Starting both clients...")
    # Start both clients
    await source_client.start()
    await destination_client.start()
    print("Bot is running... Waiting for messages...")
    await handle_disconnection()  # Handle reconnections

# Entry point - running within the existing event loop
if __name__ == "__main__":
    async def run_bot():
        while True:  # Loop to restart the script on error
            try:
                # Run the main function within the existing event loop
                await main()
            except Exception as e:
                print(f"Error occurred: {e}. Restarting the script...")
                await asyncio.sleep(5)  # Optional sleep to prevent rapid restarts

    # Start the event loop to run the bot
    keep_alive()  # Start Flask to keep the bot alive
    asyncio.run(run_bot())
