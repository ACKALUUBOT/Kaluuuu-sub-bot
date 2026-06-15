import uuid
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from utils import bot
from database import channels_col
import config

# Admin state tracking dictionary (Aap isko plugins.admin se bhi import kar sakte hain)
admin_states = {}

# --- ADMIN BUTTON SE DIRECT CALL HONE WALA FUNCTION ---
@bot.on_message(filters.command("add_story") & filters.private)
async def start_add_story(client: Client, message: Message):
    if message.from_user.id != config.ADMIN_ID: 
        return
    
    chat_id = message.chat.id
    
    admin_states[chat_id] = {"step": "get_story_name"}
    
    await message.reply_text(
        text="🎬 <b>sᴛᴏʀʏ sᴇᴛᴜᴘ:</b>\n\n"
             "Story ka naam kya hai?\n"
             "<i>(Aap direct <b>Photo</b> bhi bhej sakte hain, bas uske <b>Caption</b> mein Story ka naam likh dein)</i>\n\n"
             "➔ Cancel karne ke liye <code>/cancel</code> likhein.", 
        parse_mode="HTML"
    )

# --- STATE ROUTER MECHANISM FOR NEXT STEPS ---
async def get_story_name(client: Client, message: Message):
    chat_id = message.chat.id
    if message.text and message.text == "/cancel":
        admin_states.pop(chat_id, None)
        return await message.reply_text("❌ Setup cancelled.")
    
    story_name = None
    file_id = None

    if message.photo:
        file_id = message.photo.file_id  
        story_name = message.caption.split("\n")[0] if message.caption else "Untitled Story"
    elif message.text:
        story_name = message.text
    else:
        return await message.reply_text("❌ Please ek valid text naam ya photo bhejein:")

    admin_states[chat_id] = {
        "step": "get_demo_link",
        "story_name": story_name,
        "file_id": file_id
    }

    await message.reply_text(
        text="🔗 <b>ᴅᴇᴍᴏ ʟɪɴᴋ:</b>\nDemo channel ya video link dein (Ya 'skip' likhein):"
    )

async def get_demo_link(client: Client, message: Message, state_data: dict):
    chat_id = message.chat.id
    if message.text and message.text == "/cancel":
        admin_states.pop(chat_id, None)
        return await message.reply_text("❌ Setup cancelled.")

    demo = None if message.text and message.text.lower() == 'skip' else message.text
        
    state_data["step"] = "get_final_link"
    state_data["demo_link"] = demo
    admin_states[chat_id] = state_data

    await message.reply_text(
        text="🤖 <b><b>ғɪɴᴀʟ ʙᴏᴛ ʟɪɴᴋ:</b></b>\nPayment ke baad milne wala main link dein:"
    )

async def get_final_link(client: Client, message: Message, state_data: dict):
    chat_id = message.chat.id
    if message.text and message.text == "/cancel":
        admin_states.pop(chat_id, None)
        return await message.reply_text("❌ Setup cancelled.")

    state_data["step"] = "ask_category"
    state_data["final_link"] = message.text
    admin_states[chat_id] = state_data

    await message.reply_text(
        text="💰 <b><b>ᴘʀɪᴄᴇ:</b></b>\nSirf number likhein (Example: 49):"
    )

async def ask_category(client: Client, message: Message, state_data: dict):
    chat_id = message.chat.id
    if message.text and message.text == "/cancel":
        admin_states.pop(chat_id, None)
        return await message.reply_text("❌ Setup cancelled.")

    if not message.text or not message.text.isdigit():
        return await message.reply_text("❌ Price sirf number mein likhein:")

    price = message.text
    story_id = str(uuid.uuid4())[:10] 
    admin_states.pop(chat_id, None) # Flow complete, state clear

    # Database me temporary save
    channels_col.insert_one({
        "item_id": story_id,
        "story_name": state_data["story_name"],
        "demo_link": state_data["demo_link"],
        "bot_link": state_data["final_link"],
        "price": price,
        "file_id": state_data["file_id"], 
        "type": "story",
        "status": "pending" 
    })

    markup = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🎧 pocket", callback_data=f"src_pocket_{story_id}"),
            InlineKeyboardButton("📚 pratilipi", callback_data=f"src_pratilipi_{story_id}")
        ]
    ])

    await message.reply_text(
        text="📂 <b><b>ᴄᴀᴛᴇɢᴏʀʏ sᴇʟᴇᴄᴛ ᴋᴀʀᴇɪɴ:</b></b>\nYeh story kiski hai?", 
        reply_markup=markup, 
        parse_mode="HTML"
    )


# --- CALLBACK HANDLER FOR SOURCE SELECTION ---
@bot.on_callback_query(filters.regex(r"^src_"))
async def save_story_with_source(client: Client, call: CallbackQuery):
    if call.from_user.id != config.ADMIN_ID:
        return await call.answer("Unauthorized!", show_alert=True)

    parts = call.data.split('_')
    platform = "pocket" if parts[1] == "pocket" else "pratilipi"
    story_id = parts[2]

    # Database document update
    story_data = channels_col.find_one_and_update(
        {"item_id": story_id, "status": "pending"},
        {"$set": {"source": platform}, "$unset": {"status": ""}}, 
        return_document=True
    )

    if not story_data:
        return await call.answer("❌ Session expired ya data nahi mila!", show_alert=True)

    await call.answer()
    try:
        await call.message.delete()
    except Exception:
        pass

    share_link = f"https://t.me/{client.me.username}?start={story_id}"
    
    res = (
        f"✅ <b>sᴛᴏʀʏ ᴀᴅᴅᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ!</b>\n"
        f"────────────────────\n"
        f"📖 Name: <b>{story_data['story_name']}</b>\n"
        f"📂 Platform: <code>{platform}</code>\n"
        f"💰 Price: <b>₹{story_data['price']}</b>\n"
        f"🖼️ Media: <b>{'Saved' if story_data['file_id'] else 'No Photo'}</b>\n\n"
        f"🔗 <b>ʏᴏᴜʀ sʜᴀʀᴇ ʟɪɴᴋ:</b>\n<code>{share_link}</code>\n"
        f"────────────────────\n"
        f"➔ Is link ko copy karke promote karein."
    )
    
    if story_data['file_id']:
        await client.send_photo(chat_id=call.message.chat.id, photo=story_data['file_id'], caption=res, parse_mode="HTML")
    else:
        await client.send_message(chat_id=call.message.chat.id, text=res, parse_mode="HTML")
