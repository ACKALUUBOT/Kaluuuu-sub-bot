import sys
import os
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery
from utils import bot
import config

# Python path correction taaki 'start' module project me kahin se bhi successfully import ho sake
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Plugins se functions import ho rahe hain (Async-ready functions)
try:
    # Note: start_add_story agar abhi tak convert nahi hui hai, toh use async bana lijiyega
    from plugins.story import start_add_story 
    from plugins.admin import add_start, remove_user_start, list_channels
except Exception as e:
    print(f"Error importing plugins: {e}")

# =======================================================
# ─── 1. ADMIN BUTTONS HANDLER (Fix for Add & Remove) ───
# =======================================================
@bot.on_callback_query(filters.regex(r"^admin_"))
async def handle_admin_menu_buttons(client: Client, call: CallbackQuery):
    if call.from_user.id != config.ADMIN_ID:
        return await call.answer("❌ Access Denied!", show_alert=True)

    action = call.data.split('_')[1]
    await call.answer()  # Callback spinner ko rokne ke liye

    if action == "story":
        # Agar start_add_story function async hai (recommended), toh await lagayein
        # Agar abhi tak sync hai, toh await hata sakte hain jab tak wo convert na ho
        await start_add_story(client, call.message)
    elif action == "add":
        await add_start(client, call.message)
    elif action == "channels":
        await list_channels(client, call.message)
    elif action == "remove":
        await remove_user_start(client, call.message)


# =======================================================
# ─── 2. BACK TO START & DASHBOARD HANDLERS ───
# =======================================================
@bot.on_callback_query(filters.regex("^back_to_start$"))
async def back_to_start_handler(client: Client, call: CallbackQuery):
    await call.answer()
    
    try:
        await call.message.delete()
    except Exception:
        pass
        
    # Safe Import wrapper pattern block for runtime protection
    try:
        import start
        await start.start_handler(client, call.message)
    except (ModuleNotFoundError, AttributeError):
        try:
            from plugins import start
            await start.start_handler(client, call.message)
        except Exception as err:
            await client.send_message(
                chat_id=call.message.chat.id, 
                text=f"❌ System routing breakdown error: <code>{str(err)}</code>", 
                parse_mode="HTML"
            )

@bot.on_callback_query(filters.regex("^my_plan$"))
async def user_dashboard_link(client: Client, call: CallbackQuery):
    await call.answer("📊 Loading your plans...", show_alert=False)
    # Aap yahan apna plan checker logic ya dashboard function call judna chahein toh add kar sakte hain.

