from flask import Flask
import os
import threading

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running..."

def run():
    app.run(host='0.0.0.0', port=int(os.getenv("PORT", 5000)))

def keep_alive():
    # Start Flask app in a separate thread to avoid blocking the main process
    t = threading.Thread(target=run)
    t.start()
