import sys
import glob
import importlib
import logging
import logging.config
import asyncio
from pathlib import Path
from pyrogram import idle, Client, __version__
from pyrogram.raw.all import layer
from database.ia_filterdb import Media
from database.users_chats_db import db
from info import *
from utils import temp
from datetime import date, datetime
import pytz
from aiohttp import web
from Script import script 
from lazybot import LazyPrincessBot
from util.keepalive import ping_server
from lazybot.clients import initialize_clients

# Logging Configuration
logging.config.fileConfig('logging.conf')
logging.getLogger().setLevel(logging.INFO)
logging.getLogger("pyrogram").setLevel(logging.ERROR)
logging.getLogger("aiohttp").setLevel(logging.ERROR)

# Get all plugin files
ppath = "plugins/*.py"
files = glob.glob(ppath)

# Fix asyncio event loop issue
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

async def Lazy_start():
    print('\n✅ Initializing The Movie Provider Bot...')
    
    # Debugging: BOT_TOKEN सही से लोड हो रहा है या नहीं, इसे चेक करें
    print(f"🔹 Debug: BOT_TOKEN = {BOT_TOKEN}")

    # Start the bot
    await LazyPrincessBot.start()
    bot_info = await LazyPrincessBot.get_me()
    LazyPrincessBot.username = bot_info.username

    # Initialize clients
    await initialize_clients()
    
    # Import plugins
    for name in files:
        with open(name) as a:
            patt = Path(a.name)
            plugin_name = patt.stem.replace(".py", "")
            plugins_dir = Path(f"plugins/{plugin_name}.py")
            import_path = f"plugins.{plugin_name}"
            spec = importlib.util.spec_from_file_location(import_path, plugins_dir)
            load = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(load)
            sys.modules[f"plugins.{plugin_name}"] = load
            print(f"✅ Plugin Imported => {plugin_name}")

    # Ensure LOG_CHANNEL is valid
    if not LOG_CHANNEL or not isinstance(LOG_CHANNEL, int):
        logging.error("❌ LOG_CHANNEL is not set properly. Please check your configuration.")
        return
    
    # Get banned users and chats
    b_users, b_chats = await db.get_banned()
    temp.BANNED_USERS = b_users
    temp.BANNED_CHATS = b_chats

    # Ensure indexes
    await Media.ensure_indexes()
    me = await LazyPrincessBot.get_me()
    temp.ME = me.id
    temp.U_NAME = me.username
    temp.B_NAME = me.first_name
    LazyPrincessBot.username = '@' + me.username

    logging.info(f"🚀 {me.first_name} with Pyrogram v{__version__} (Layer {layer}) started on @{me.username}.")
    logging.info(script.LOGO)

    # Get time
    tz = pytz.timezone('Asia/Kolkata')
    today = date.today()
    now = datetime.now(tz)
    time = now.strftime("%H:%M:%S %p")

    # Send restart message
    await LazyPrincessBot.send_message(chat_id=LOG_CHANNEL, text=script.RESTART_TXT.format(today, time))

    # Keep bot running
    await idle()

async def start_web_server():
    """ Simple Web Server for Koyeb Health Check """
    async def handle(request):
        return web.Response(text="Bot is Running!")

    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()
    print("✅ Web server started on port 8080.")

if __name__ == "__main__":
    # Create and set a new event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        # Start Web Server (Koyeb Health Check के लिए)
        loop.create_task(start_web_server())
        
        # Start Telegram Bot
        loop.create_task(Lazy_start())

        # Run the loop forever
        loop.run_forever()
    except KeyboardInterrupt:
        logging.info("❌ Service Stopped. Bye 👋")
