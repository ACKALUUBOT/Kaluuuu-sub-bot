import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from utils import bot
from database import users_col
import config

# admin.py ke main state manager dictionary ka use karne ke liye
# Agar admin.py me ye already imported hai toh state_manager isko handle karega
from plugins.admin import admin_states

# ==========================================
# --- ADMIN BROADCAST SYSTEM (BULK SEND) ---
# ==========================================

@bot.on_message(filters.command("broadcast") & filters.user(config.ADMIN_ID))
async def start_broadcast(client: Client, message: Message):
    admin_states[message.from_user.id] = {"step": "awaiting_broadcast_msg"}
    
    await message.reply_text(
        "📢 <b>ᴀᴅᴍɪɴ ʙʀᴏᴀᴅᴄᴀsᴛ:</b>\n\n"
        "Aap jo bhi message sabhi users ko bhejna chahte hain, woh yahan <b>Forward</b> karein ya direct <b>Type/Upload</b> karein.\n\n"
        "➔ <i>Isme Text, Photo, Video, Animation sab support hoga. Cancel karne ke liye <code>/cancel</code> likhein.</i>",
        parse_mode="HTML"
    )

# Note: Is function ko call karne ka kaam admin.py ke state_manager me niche diye gaye handler ke through hoga
async def process_broadcast(client: Client, message: Message):
    admin_states.pop(message.from_user.id, None)
    
    if message.text and message.text.lower() in ['/cancel', 'cancel']:
        return await message.reply_text("❌ Broadcast cancelled.")

    # Database se unique users nikalna
    all_users = users_col.distinct("user_id")
    total_users = len(all_users)

    if total_users == 0:
        return await message.reply_text("❌ Database mein koi user nahi mila!")

    status_msg = await message.reply_text(
        f"🚀 <b>Broadcast Shuru Ho Gaya Hai...</b>\n\n👥 Total Targets: <code>{total_users}</code>\n⏳ Processing...", 
        parse_mode="HTML"
    )

    # Background me loop chalane ke liye asyncio task create karna (threading ka alternative)
    asyncio.create_task(run_broadcast_loop(client, message, all_users, status_msg.chat.id, status_msg.id))

async def run_broadcast_loop(client: Client, media_msg: Message, user_list: list, admin_chat_id: int, status_message_id: int):
    success = 0
    failed = 0
    total = len(user_list)

    for index, u_id in enumerate(user_list):
        try:
            # Pyrogram me copy_message ki jagah message.copy use hota hai (Sab media types support karta hai)
            await media_msg.copy(chat_id=int(u_id))
            success += 1
        except Exception:
            failed += 1

        # Flood wait se bachne ke liye thoda pause aur har 10 users ke baad status update
        if (index + 1) % 10 == 0 or (index + 1) == total:
            try:
                await client.edit_message_text(
                    chat_id=admin_chat_id,
                    message_id=status_message_id,
                    text=f"📢 <b>ʙʀᴏᴀᴅᴄᴀsᴛ ɪɴ ᴘʀᴏɢʀᴇss:</b>\n"
                         f"────────────────────\n"
                         f"📊 Progress: <code>{index + 1}/{total}</code>\n"
                         f"✅ Successful: <code>{success}</code>\n"
                         f"❌ Failed/Blocked: <code>{failed}</code>",
                    parse_mode="HTML"
                )
            except Exception:
                pass
            # Telegram Limits ko dhyan me rakhte hue safe sleep
            await asyncio.sleep(0.5)

    await client.send_message(
        chat_id=admin_chat_id, 
        text=f"🏁 <b>ʙʀᴏᴀᴅᴄᴀsᴛ ғɪɴɪsʜᴇᴅ!</b>\n"
             f"────────────────────\n"
             f"✅ Total Delivered: <code>{success}</code>\n"
             f"❌ Total Failed: <code>{failed}</code>\n"
             f"👥 Grand Total: <code>{total}</code>", 
        parse_mode="HTML"
    )
