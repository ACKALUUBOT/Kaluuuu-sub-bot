import urllib.parse
import asyncio
import time
from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ChatMemberUpdated
from utils import bot, get_time_string
from database import channels_col, users_col
import config

# States maps ko import karna state tracking ke liye
from plugins.start import USER_STATES
# Note: Agar admin_states admin.py me hai toh wahan se access hoga
from plugins.admin import admin_states 

# ===================================================
# --- EXTRA CONFIG: FRESH START MENU RE-LOAD ---
# ===================================================
async def send_home_menu(client: Client, chat_id: int):
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("« ʙᴀᴄᴋ ᴛᴏ ᴍᴇɴᴜ", callback_data="back_to_start")]
    ])

    await client.send_message(
        chat_id=chat_id, 
        text="❌ <b>ᴘᴀʏᴍᴇɴᴛ ᴄᴀɴᴄᴇʟʟᴇᴅ!</b>\n\nAapka current payment process rok diya gaya hai. Aap niche diye gaye menu se fir se shuru kar sakte hain:", 
        reply_markup=markup, 
        parse_mode="HTML"
    )


# --- 1. PAYMENT SELECTION ---
@bot.on_callback_query(filters.regex(r"^select_"))
async def confirm_step(client: Client, call: CallbackQuery):
    parts = call.data.split('_')
    mins = parts[-1]               
    item_id = "_".join(parts[1:-1]) 
    
    data = channels_col.find_one({"item_id": item_id}) or \
           channels_col.find_one({"channel_id": int(item_id) if item_id.replace('-','').isdigit() else 0})
    
    if not data: 
        return await call.answer(f"❌ Data not found! (ID: {item_id})", show_alert=True)

    if data.get('is_combo'):
        price = data['price']
        display_name = data.get('combo_name', 'Premium Combo')
    elif 'story_name' in data:
        price = data['price']
        display_name = data.get('story_name')
    else:
        price = data['plans'].get(mins, "0") if isinstance(data.get('plans'), dict) else data.get('price', '0')
        display_name = data.get('name', 'Premium Channel')
    
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 ᴘᴀʏ ᴠɪ VIA ǫʀ sᴄᴀɴ", callback_data=f"man_{item_id}_{mins}_qr")],
        [InlineKeyboardButton("📲 ᴘᴀʏ ᴠɪ VIA ᴜᴘɪ ɪᴅ", callback_data=f"man_{item_id}_{mins}_upi")],
        [InlineKeyboardButton("❌ ᴄᴀɴᴄᴇʟ ᴘᴀʏᴍᴇɴᴛ", callback_data="cancel_payment")]
    ])
    
    text = (
        f"<b>🛒 ᴄᴏɴғɪʀᴍ sᴇʟᴇᴄᴛɪᴏɴ</b>\n"
        f"────────────────────\n"
        f"📦 ɪᴛᴇᴍ: <b>{display_name}</b>\n"
        f"💰 ᴀᴍᴏᴜɴᴛ: <b>₹{price}</b>\n\n"
        f"➔ Payment method select karein:"
    )
    
    await call.answer()
    try:
        await call.message.delete()
    except Exception:
        pass

    await client.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode="HTML")


# --- 2. MANUAL PAYMENT SYSTEM ---
@bot.on_callback_query(filters.regex(r"^man_"))
async def manual_pay(client: Client, call: CallbackQuery):
    parts = call.data.split('_')
    mode = parts[-1]                
    mins = parts[-2]                
    item_id = "_".join(parts[1:-2]) 
    
    data = channels_col.find_one({"item_id": item_id}) or \
           channels_col.find_one({"channel_id": int(item_id) if item_id.replace('-','').isdigit() else 0})
    
    if not data:
        return await call.answer("❌ Data Error on Payment!", show_alert=True)

    if data.get('is_combo') or 'story_name' in data:
        price = data['price']
    else:
        price = data['plans'].get(mins, "0") if isinstance(data.get('plans'), dict) else data.get('price', '0')
        
    upi_string = f"upi://pay?pa={config.UPI_ID}&am={price}&cu=INR&tn=Pay_{item_id}"
    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=350x350&data={urllib.parse.quote(upi_string)}"
    
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ sᴜʙᴍɪᴛ sᴄʀᴇᴇɴsʜᴏᴛ", callback_data=f"paid_{item_id}_{mins}")],
        [InlineKeyboardButton("❌ ᴄᴀɴᴄᴇʟ ᴘᴀʏᴍᴇɴᴛ", callback_data="cancel_payment")]
    ])

    await call.answer()
    try:
        await call.message.delete()
    except Exception:
        pass

    if mode == "qr":
        await client.send_photo(
            chat_id=call.message.chat.id, 
            photo=qr_url, 
            caption=f"📥 <b>ǫʀ sᴄᴀɴɴᴇʀ</b>\n\nAmount: <b>₹{price}</b>\n\n➔ Pay karke niche wala button dabayein.", 
            reply_markup=markup, 
            parse_mode="HTML"
        )
    else:
        await client.send_message(
            chat_id=call.message.chat.id, 
            text=f"📲 <b>ᴜᴘɪ ɪᴅ:</b> <code>{config.UPI_ID}</code>\nAmount: <b>₹{price}</b>\n\n➔ Pay karne ke baad niche button dabayein.", 
            reply_markup=markup, 
            parse_mode="HTML"
        )


# --- 3. DIRECT SCREENSHOT SUBMISSION ---
@bot.on_callback_query(filters.regex(r"^paid_"))
async def handle_paid(client: Client, call: CallbackQuery):
    parts = call.data.split('_')
    mins = parts[-1]
    item_id = "_".join(parts[1:-1])
    await call.answer()
    
    try:
        await call.message.delete()
    except Exception:
        pass
    
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ ᴄᴀɴᴄᴇʟ ᴘᴀʏᴍᴇɴᴛ", callback_data="cancel_payment")]
    ])
        
    # State mapping set karna next step handle karne ke liye (register_next_step ka substitute)
    USER_STATES[call.from_user.id] = {
        "step": "awaiting_screenshot",
        "item_id": item_id,
        "mins": mins
    }
        
    await client.send_message(
        chat_id=call.message.chat.id, 
        text="📸 Payment ka <b>Screenshot</b> bhejein:\n\n"
             "➔ <i>Agar cancel karna chahte hain toh niche button par click karein ya chat me <code>/cancel</code> likhein.</i>", 
        reply_markup=markup, 
        parse_mode="HTML"
    )

# Note: Jab user image bhejega, toh message handler is function ko trigger karega (State router ke through)
async def send_request_to_admin(client: Client, message: Message, item_id: str, mins: str):
    if message.text and message.text.lower() in ['/cancel', 'cancel']:
        USER_STATES.pop(message.from_user.id, None)
        return await send_home_menu(client, message.chat.id)

    if not message.photo:
        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ ᴄᴀɴᴄᴇʟ ᴘᴀʏᴍᴇɴᴛ", callback_data="cancel_payment")]
        ])
        await message.reply_text(
            "❌ Please sirf Photo (Screenshot) bhejein!\n"
            "Cancel karne ke liye <code>/cancel</code> likhein ya neeche click karein:", 
            reply_markup=markup, 
            parse_mode="HTML"
        )
        return # State delete nahi hogi, bacha rahega jab tak photo na aaye
    
    USER_STATES.pop(message.from_user.id, None) # State successfully capture hone par clear
    photo_id = message.photo.file_id
    
    data = channels_col.find_one({"item_id": item_id}) or \
           channels_col.find_one({"channel_id": int(item_id) if item_id.replace('-','').isdigit() else 0})
    
    if not data:
        return await message.reply_text("❌ Something went wrong, item not found!")

    display_name = data.get('combo_name') or data.get('story_name') or data.get('name')
    await message.reply_text("⏳ <b>ʀᴇǫᴜᴇsᴛ sᴇɴᴛ!</b>\nAdmin check karke aapka access on kar dega.")
    
    markup = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Approve", callback_data=f"app_{message.from_user.id}_{item_id}_{mins}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"rej_{message.from_user.id}")
        ],
        [InlineKeyboardButton("💬 Support", url=f"tg://openmessage?user_id={message.from_user.id}")]
    ])
    
    admin_text = f"📥 <b>ɴᴇᴡ ᴘᴀʏᴍᴇɴᴛ ʀᴇǫᴜᴇsᴛ</b>\n────────────────────\n👤 User ID: <code>{message.from_user.id}</code>\n📦 Item: <b>{display_name}</b>\n⏳ Plan: {mins if mins != 'manual' else 'Lifetime'}"
    await client.send_photo(chat_id=config.ADMIN_ID, photo=photo_id, caption=admin_text, reply_markup=markup, parse_mode="HTML")


@bot.on_callback_query(filters.regex("^cancel_payment$"))
async def process_inline_cancel(client: Client, call: CallbackQuery):
    await call.answer("Process Cancelled!")
    USER_STATES.pop(call.from_user.id, None) # State clear karna
    try:
        await call.message.delete()
    except Exception:
        pass
    await send_home_menu(client, call.message.chat.id)


# --- 4. ADMIN APPROVAL CONTROL PANEL ---
@bot.on_callback_query(filters.regex(r"^app_"))
async def admin_approve(client: Client, call: CallbackQuery):
    parts = call.data.split('_')
    u_id = parts[1]
    mins = parts[-1]
    item_id = "_join".join(parts[2:-1]) if "_join" in call.data else "_".join(parts[2:-1])
    
    data = channels_col.find_one({"item_id": item_id}) or \
           channels_col.find_one({"channel_id": int(item_id) if item_id.replace('-','').isdigit() else 0})
    
    if not data: 
        return await call.answer("❌ Data not found on Approval!", show_alert=True)
    
    expiry = int(time.time()) + (int(mins) * 60) if mins != 'manual' else int(time.time()) + (365*24*60*60)
    buttons = []

    # ─── CASE A: COMBO PACK APPROVAL ───
    if data.get('is_combo') and 'channels_list' in data:
        msg = "🎁 <b>ᴄᴏᴍʙᴏ ᴘᴀᴄᴋ ᴀᴘᴘʀᴏᴠᴇᴅ!</b>\n\nAapko sabhi linked channels ka access de diya gaya hai. Niche diye buttons se join karein:\n\n"
        for ch_id in data['channels_list']:
            users_col.update_one({"user_id": int(u_id), "channel_id": int(ch_id)}, {"$set": {"expiry": expiry}}, upsert=True)
            try:
                # Pyrogram me generate_chat_invite_link use hota hai
                invite = await client.generate_chat_invite_link(chat_id=int(ch_id), member_limit=1)
                ch_info = channels_col.find_one({"channel_id": int(ch_id)})
                ch_title = ch_info.get('name') or ch_info.get('story_name') if ch_info else f"VIP Channel {ch_id}"
                buttons.append([InlineKeyboardButton(f"📢 Join: {ch_title}", url=invite.invite_link)])
            except Exception as e:
                print(f"Combo Link Error: {e}")
        msg += "⚠️ <i>Links single-use hain, ek baar join hone ke baad automatic expire ho jayengi!</i>"

    # ─── CASE B: FORWARDED CHANNEL (/add Flow) ───
    elif data.get('type') == 'channel' or ('channel_id' in data and data.get('source') not in ['pocket', 'pratilipi'] and not data.get('is_combo')):
        target_channel = int(data['channel_id'])
        users_col.update_one({"user_id": int(u_id), "channel_id": target_channel}, {"$set": {"expiry": expiry}}, upsert=True)
        try:
            # Pyrogram style Single-use link create karna
            invite = await client.generate_chat_invite_link(chat_id=target_channel, member_limit=1, name=f"Paid_{u_id}")
            buttons.append([InlineKeyboardButton("🔐 JOIN PREMIUM CHANNEL", url=invite.invite_link)])
            
            validity_display = data.get('validity', mins)
            msg = (
                f"✅ <b>ᴀᴘᴘʀᴏᴠᴇᴅ!</b>\n\n"
                f"📂 <b>ᴄʜᴀɴɴᴇʟ:</b> <b>{data.get('name', 'VIP Channel')}</b>\n"
                f"⏱️ <b>ᴠᴀʟɪᴅɪᴛʏ:</b> {validity_display if validity_display != 'manual' else 'Lifetime'}\n\n"
                f"Join karne ke liye neeche button par click karein:\n\n"
                f"⚠️ <i>Yeh link single use hai, ek baar use hone ke baad automatic expire ho jayegi!</i>"
            )
        except Exception as e: 
            print(f"Error: {e}")
            msg = "✅ <b>ᴀᴘᴘʀᴏᴠᴇᴅ!</b>\n\nBot link generate nahi kar saka, admin rights setup check karein."

    # ─── CASE C: MANUAL PREMIUM STORY (/add_story Flow) ───
    else:
        users_col.update_one({"user_id": int(u_id), "channel_id": data.get('channel_id', 0)}, {"$set": {"expiry": expiry}}, upsert=True)
        target_link = data.get('bot_link') or data.get('final_link') or 'https://t.me'
        
        buttons.append([InlineKeyboardButton("🚀 sᴛᴀʀᴛ sᴛᴏʀỹ", url=target_link)])
        
        platform_info = f"\n📂 Platform: <code>{data.get('source')}</code>" if data.get('source') else ""
        msg = (
            f"🎉 <b>ᴘᴀʏᴍᴇɴᴛ ᴀᴘᴘʀᴏᴠᴇᴅ!</b>\n"
            f"────────────────────\n"
            f"📖 <b>sᴛᴏʀỹ:</b> {data.get('story_name', 'Premium Story')}"
            f"{platform_info}\n"
            f"💰 <b>ᴘʀɪᴄᴇ:</b> ₹{data.get('price', '49')}\n"
            f"────────────────────\n"
            f"➔ Niche diye gaye button par click karke apni full story access karein 👇"
        )

    markup = InlineKeyboardMarkup(buttons)
    try:
        if 'story_name' in data and data.get('file_id') and data.get('type') != 'channel':
            await client.send_photo(chat_id=int(u_id), photo=data['file_id'], caption=msg, reply_markup=markup, protect_content=True)
        else:
            await client.send_message(chat_id=int(u_id), text=msg, reply_markup=markup, protect_content=True)
    except Exception as e:
        print(f"Delivery Error: {e}")
        
    await call.message.edit_caption(caption=f"✅ Approved for User: {u_id}")


@bot.on_callback_query(filters.regex(r"^rej_"))
async def admin_reject(call: CallbackQuery):
    u_id = call.data.split('_')[1]
    await call.message.edit_caption(caption="❌ Payment Rejected!")
    try:
        await bot.send_message(chat_id=int(u_id), text="❌ Aapka payment reject ho gaya hai. Support se baat karein.")
    except Exception:
        pass


# --- 5. AUTOMATIC LINK REVOKE ---
# Pyrogram style Chat member update event tracking
@bot.on_chat_member_updated()
async def handle_chat_member_updates(client: Client, update: ChatMemberUpdated):
    # Check if the chat is a channel
    if update.chat.type.name != "CHANNEL":
        return

    # Check join status
    if update.new_chat_member and update.new_chat_member.status.name == "MEMBER":
        # Pyrogram ensures checking old status if required, or directly checking if invite link was used
        if update.invite_link:
            used_link = update.invite_link.invite_link
            channel_id = update.chat.id
            try:
                await client.revoke_chat_invite_link(chat_id=channel_id, invite_link=used_link)
                print(f"[SUCCESS] Revoked: {used_link}")
            except Exception as e:
                print(f"[ERROR] Revoke failed: {e}")
