import sys  
import glob  
import importlib  
from pathlib import Path  
import asyncio  
import logging  
import logging.config  
import pytz  
from datetime import date, datetime  
from aiohttp import web  
from pyrogram import Client, __version__, idle  
from pyrogram.raw.all import layer  
from pyrogram.storage import SQLiteStorage  
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

# 🔹 Logging Configuration  
logging.config.fileConfig('logging.conf')  
logging.getLogger().setLevel(logging.INFO)  
logging.getLogger("pyrogram").setLevel(logging.ERROR)  
logging.getLogger("imdbpy").setLevel(logging.ERROR)  
logging.basicConfig(  
    level=logging.INFO,  
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"  
)  
logging.getLogger("aiohttp").setLevel(logging.ERROR)  
logging.getLogger("aiohttp.web").setLevel(logging.ERROR)  

# 🔹 Plugin Loader  
ppath = "plugins/*.py"  
files = glob.glob(ppath)  

# 🔹 Start the Bot  
LazyPrincessBot.start()  
loop = asyncio.new_event_loop()  
asyncio.set_event_loop(loop)  

# 🔹 SQLite Database Reset Function  
async def reset_sqlite_db():  
    try:  
        storage = SQLiteStorage("LazyPrincessBot.session")  # Change this to your actual session name  
        await storage.reset()  
        logging.info("✅ SQLite Database has been reset successfully!")  
    except Exception as e:  
        logging.error(f"❌ Error resetting SQLite Database: {e}")  

# 🔹 Main Bot Start Function  
async def Lazy_start():  
    print('\n')  
    print('Initializing The Movie Provider Bot...')  
    bot_info = await LazyPrincessBot.get_me()  
    LazyPrincessBot.username = bot_info.username  
    await initialize_clients()  

    # 🔹 Reset SQLite Database before starting (Optional)  
    await reset_sqlite_db()  

    # 🔹 Plugin Import  
    for name in files:  
        with open(name) as a:  
            patt = Path(a.name)  
            plugin_name = patt.stem.replace(".py", "")  
            plugins_dir = Path(f"plugins/{plugin_name}.py")  
            import_path = "plugins.{}".format(plugin_name)  
            spec = importlib.util.spec_from_file_location(import_path, plugins_dir)  
            load = importlib.util.module_from_spec(spec)  
            spec.loader.exec_module(load)  
            sys.modules["plugins." + plugin_name] = load  
            print(f"The Movie Provider Imported => {plugin_name}")  

    if ON_HEROKU:  
        asyncio.create_task(ping_server())  

    # 🔹 Fetching Banned Users & Chats  
    b_users, b_chats = await db.get_banned()  
    temp.BANNED_USERS = b_users  
    temp.BANNED_CHATS = b_chats  
    await Media.ensure_indexes()  

    # 🔹 Bot Information  
    me = await LazyPrincessBot.get_me()  
    temp.ME = me.id  
    temp.U_NAME = me.username  
    temp.B_NAME = me.first_name  
    LazyPrincessBot.username = '@' + me.username  
    logging.info(f"{me.first_name} with Pyrogram v{__version__} (Layer {layer}) started on {me.username}.")  
    logging.info(LOG_STR)  
    logging.info(script.LOGO)  

    # 🔹 Get Current Time  
    tz = pytz.timezone('Asia/Kolkata')  
    today = date.today()  
    now = datetime.now(tz)  
    time = now.strftime("%H:%M:%S %p")  

    # 🔹 LOG_CHANNEL Error Handling  
    try:  
        peer = await LazyPrincessBot.resolve_peer(LOG_CHANNEL)  
        await LazyPrincessBot.send_message(  
            chat_id=LOG_CHANNEL,  
            text=script.RESTART_TXT.format(today, time)  
        )  
        logging.info(f"✅ Successfully sent message to LOG_CHANNEL: {LOG_CHANNEL}")  
    except KeyError:  
        logging.error(f"❌ LOG_CHANNEL ID not found: {LOG_CHANNEL}. Please check if the bot is added as an admin in the channel.")  
    except ValueError as e:  
        logging.error(f"❌ Error: {e}. LOG_CHANNEL ID may be incorrect or the bot has no access.")  

    # 🔹 Start Web Server  
    app = web.AppRunner(await web_server())  
    await app.setup()  
    bind_address = "0.0.0.0"  
    await web.TCPSite(app, bind_address, PORT).start()  

    await idle()  

# 🔹 Run the Bot  
if __name__ == '__main__':  
    try:  
        loop.run_until_complete(Lazy_start())  
    except KeyboardInterrupt:  
        logging.info('Service Stopped. Bye 👋')
