import os
import asyncio
from threading import Thread
from pyrogram import Client, filters
from pyrogram.types import Message
import config
from utils import bot  # 'bot' is now a Pyrogram Client instance
from server import app
from scheduler import start_scheduler

# ─── 🌟 GLOBAL STATE TRACKER (CROSS-PLUGIN SYNC) ───
USER_STATES = {}  # Format: {user_id: {"category": "story", "page": 1}}

# Plugins folder ke handlers register karne ke liye explicitly import karein
import plugins.start
import plugins.admin
import plugins.payment
import plugins.broadcast

# ─── ⚙️ DYNAMIC FSM ROUTER FOR ADMIN INPUTS ───
# Yeh handler plugins se pehle check karega agar admin ka koi setup step 'pending' hai
@bot.on_message(filters.private & filters.incoming & (filters.text | filters.photo), group=-1)
async def global_fsm_router(client: Client, message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id if message.from_user else chat_id

    # Strict check: Sirf admin ke state flow को रूट करने के लिए
    if user_id == config.ADMIN_ID:
        from plugins.story import admin_states
        state_data = admin_states.get(chat_id)

        if state_data:
            step = state_data.get("step")
            
            # --- STORY ADDING FLOWS ---
            if step == "get_story_name":
                from plugins.story import get_story_name
                await get_story_name(client, message)
                return
                
            elif step == "get_demo_link":
                from plugins.story import get_demo_link
                await get_demo_link(client, message, state_data)
                return
                
            elif step == "get_final_link":
                from plugins.story import get_final_link
                await get_final_link(client, message, state_data)
                return
                
            elif step == "ask_category":
                from plugins.story import ask_category
                await ask_category(client, message, state_data)
                return

            # --- FORWARDED CHANNEL ADDING FLOWS ---
            elif step == "get_channel_info":
                from plugins.admin import process_channel_forward
                await process_channel_forward(client, message)
                return

    # Agar koi state pending nahi hai, toh message baaki normal commands (/start, /broadcast) ke paas jayega
    message.continue_propagation()


async def main():
    print("Cleaning up old connections and starting Pyrogram Bot...")
    
    # 1. Flask Web Server running thread (Render Port issue fix)
    port = int(os.environ.get("PORT", 5000))
    Thread(target=lambda: app.run(host='0.0.0.0', port=port, use_reloader=False), daemon=True).start()
    print(f"ℹ️ Web Server successfully linked on Port: {port}")
    
    # 2. Start Background Scheduler for Expiries
    start_scheduler()
    print("ℹ️ Background Scheduler started successfully.")
    
    # 3. Start Pyrogram Client
    print("Bot setup separated successfully! Starting Pyrogram client...")
    await bot.start()
    
    # client.me ko populate karna taaki boti files me bina API call username access ho sake
    bot.me = await bot.get_me()
    print(f"✅ Bot is successfully running via Pyrogram on @{bot.me.username}!")
    
    # Keep the async loop alive
    await asyncio.Event().wait()

if __name__ == '__main__':
    try:
        # Running the async main function
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped by Admin.")
