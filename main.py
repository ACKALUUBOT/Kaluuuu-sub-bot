import os
import asyncio
from threading import Thread
import config
from utils import bot  # Ensure 'bot' in utils is now a Pyrogram Client instance
from server import app
from scheduler import start_scheduler

# ─── 🌟 GLOBAL STATE TRACKER (CROSS-PLUGIN SYNC) ───
# Isko yahan rakhne se plugins.start aur plugins.payment dono ise bina crash ke use kar payenge
USER_STATES = {}  # Format: {user_id: {"category": "story", "page": 1}}

# Plugins folder ke handlers register karne ke liye explicitly import karein
# Note: Pyrogram me handlers explicitly ya 'plugins' parameter ke through load hote hain
import plugins.start
import plugins.admin
import plugins.payment
import plugins.broadcast

async def main():
    print("Cleaning up old connections and starting Pyrogram Bot...")
    
    # 1. Flask Web Server running thread
    port = int(os.environ.get("PORT", 5000))
    Thread(target=lambda: app.run(host='0.0.0.0', port=port, use_reloader=False), daemon=True).start()
    
    # 2. Start Background Scheduler for Expiries
    start_scheduler()
    
    # 3. Start Pyrogram Client (Handling drop_pending_updates implicitly if needed via fast start)
    print("Bot setup separated successfully! Starting Pyrogram client...")
    
    # Pyrogram automatically handles updates like messages, callback queries, and chat members
    await bot.start()
    print("Bot is successfully running via Pyrogram!")
    
    # Keep the async loop alive
    await asyncio.Event().wait()

if __name__ == '__main__':
    try:
        # Running the async main function
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped by Admin.")
