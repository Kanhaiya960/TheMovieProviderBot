import sys
import glob
import importlib
import logging
import logging.config
import asyncio
import pytz
from datetime import date, datetime
from pathlib import Path
from aiohttp import web
from pyrogram import idle, Client, __version__
from pyrogram.raw.all import layer
from database.ia_filterdb import Media
from database.users_chats_db import db
from info import *
from utils import temp
from typing import Union, Optional, AsyncGenerator
from pyrogram import types
from Script import script
from plugins import web_server
from lazybot import LazyPrincessBot
from util.keepalive import ping_server
from lazybot.clients import initialize_clients

# ✅ **Logging Configuration**
logging.config.fileConfig('logging.conf')
logging.getLogger().setLevel(logging.INFO)
logging.getLogger("pyrogram").setLevel(logging.ERROR)

# ✅ **Load Plugins**
ppath = "plugins/*.py"
files = glob.glob(ppath)

# ✅ **Main Function to Start Bot**
async def Lazy_start():
    print("\n✅ Initializing The Movie Provider Bot...")

    await LazyPrincessBot.start()
    bot_info = await LazyPrincessBot.get_me()
    LazyPrincessBot.username = bot_info.username
    await initialize_clients()

    # ✅ **Load Plugins**
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

    # ✅ **Validate LOG_CHANNEL**
    if not LOG_CHANNEL or not isinstance(LOG_CHANNEL, int):
        logging.error("❌ LOG_CHANNEL is not set properly. Please check your configuration.")
        return

    # ✅ **Fix MongoDB asyncio Issue**
    loop = asyncio.get_event_loop()
    b_users, b_chats = await loop.run_in_executor(None, lambda: asyncio.run(db.get_banned()))
    temp.BANNED_USERS = b_users
    temp.BANNED_CHATS = b_chats
    await Media.ensure_indexes()

    # ✅ **Bot Info**
    me = await LazyPrincessBot.get_me()
    temp.ME = me.id
    temp.U_NAME = me.username
    temp.B_NAME = me.first_name
    LazyPrincessBot.username = f'@{me.username}'

    logging.info(f"🚀 {me.first_name} with Pyrogram v{__version__} (Layer {layer}) started on {me.username}.")
    logging.info(script.LOGO)

    # ✅ **Log Restart Time**
    tz = pytz.timezone("Asia/Kolkata")
    today = date.today()
    now = datetime.now(tz)
    time = now.strftime("%H:%M:%S %p")

    await LazyPrincessBot.send_message(chat_id=LOG_CHANNEL, text=script.RESTART_TXT.format(today, time))

    # ✅ **Start Web Server**
    app = web.AppRunner(await web_server())
    await app.setup()
    bind_address = "0.0.0.0"
    await web.TCPSite(app, bind_address, 8080).start()

    await idle()

# ✅ **Main Execution**
if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(Lazy_start())
