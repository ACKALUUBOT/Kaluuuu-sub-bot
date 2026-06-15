import uuid
import asyncio
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove, WebAppInfo
import config
from utils import bot, get_time_string
from database import channels_col, users_col
from plugins.store import get_categories_markup, get_items_by_category_markup, get_store_text

# Global state manager dictionary for store steps tracking
USER_STATES = {}

@bot.on_message(filters.command("start") & filters.private)
async def start_handler(client: Client, message: Message):
    user_id = message.from_user.id if message.from_user else message.chat.id
    chat_id = message.chat.id

    USER_STATES[user_id] = {"category": "home", "page": 1}

    # ─── 1. DEEP LINK PARAMETER CHECK (3 SEPARATE FLOWS) ───
    text = message.text.split() if message.text else []
    if len(text) > 1:
        param = text[1]
        data = channels_col.find_one({"item_id": param}) or \
               channels_col.find_one({"channel_id": int(param) if param.replace('-','').isdigit() else 0})

        if data:
            buttons = []
            db_id = data.get('item_id') or data.get('channel_id')
            
            # [FLOW A] Combo Pack
            if data.get('is_combo'):
                buttons.append([InlineKeyboardButton(f"💳 🎁 ᴜɴʟᴏᴄᴋ ᴄᴏᴍʙᴏ - ₹{data['price']}", callback_data=f"select_{db_id}_manual")])
                display_name = data['combo_name']
                header = "🎁 <b>ᴘʀᴇᴍɪᴜᴍ sᴘᴇᴄɪᴀʟ ᴄᴏᴍʙᴏ ʙᴜɴᴅʟᴇ</b>"
                desc_text = f"📝 <b>ɪɴᴄʟᴜᴅᴇᴅ sᴛᴏʀɪᴇs:</b>\n<i>{data.get('description', 'Multiple premium stories inside!')}</i>"
            
            # [FLOW B] Forwarded Channel (/add flow)
            elif 'channel_id' in data and not data.get('story_name'):
                if data.get('plans') and isinstance(data['plans'], dict):
                    for p_time, p_price in data['plans'].items():
                        buttons.append([InlineKeyboardButton(f"💳 {get_time_string(p_time)} - ₹{p_price}", callback_data=f"select_{db_id}_{p_time}")])
                else:
                    buttons.append([InlineKeyboardButton(f"✅ CONFIRM & PAY - ₹{data.get('price', '49')}", callback_data=f"select_{db_id}_manual")])
                display_name = data.get('name', 'Premium Access')
                header = "💎 <b>ᴘʀᴇᴍɪᴜᴍ ᴘʀɪᴠᴀᴛᴇ ᴄʜᴀɴɴᴇʟ</b>"
                desc_text = "🤖 <b>ᴅᴇʟɪᴠᴇʀʏ:</b> <code><b>ᴄʜᴀɴɴᴇʟ ɪɴᴠɪᴛᴇ ʟɪɴᴋ (𝟷-ᴛɪᴍᴇ ᴜsᴇ)</b></code>\nℹ️ <i>Isme join hone ke liye direct temporary invite link milega.</i>"
            
            # [FLOW C] Direct Story (/add_story flow)
            else:
                buttons.append([InlineKeyboardButton(f"💳 🎧 ᴜɴʟᴏᴄᴋ sᴛᴏʀʏ - ₹{data.get('price', '49')}", callback_data=f"select_{db_id}_manual")])
                display_name = data.get('story_name')
                header = f"🔥 <b>ᴘʀᴇᴍɪᴜᴍ ᴇxᴄʟᴜsɪᴠᴇ sᴛᴏʀʏ ({data.get('source', 'audio')})</b>"
                desc_text = "🤖 <b>ᴅᴇʟɪᴠᴇʀʏ:</b> <code><b>ɪsᴛᴀɴᴛ ʙᴏᴛ ʟɪɴᴋ ᴀᴄᴄᴇss</b></code>\nℹ️ <i>Isme payment ke baad direct external link ya redirection button milega.</i>"

            if data.get('demo_link'):
                buttons.append([InlineKeyboardButton("📺 ᴠɪᴇᴡ ǫᴜᴀʟɪᴛʏ ᴅᴇᴍᴏ (ᴛᴇᴀsᴇʀ)", url=data['demo_link'])])
            
            buttons.append([InlineKeyboardButton("🏠 ʙᴀᴄᴋ ᴛᴏ ᴍᴇɴᴜ", callback_data="back_to_start")])
            markup = InlineKeyboardMarkup(buttons)
            
            premium_text = f"{header}\n──────────────────────────\n📦 <b>ᴘᴀᴄᴋ ɴᴀᴍᴇ:</b> <code>{display_name}</code>\n\n{desc_text}\n──────────────────────────"
            
            photo_id = data.get('file_id')
            if photo_id:
                return await message.reply_photo(photo=photo_id, caption=premium_text, reply_markup=markup, parse_mode="HTML")
            else:
                return await message.reply_text(text=premium_text, reply_markup=markup, parse_mode="HTML")

    # ─── 2. MAIN DASHBOARD (ADMIN VS USER SPLIT) ───
    buttons = []
    
    # 🌟 MINI APP BUTTON 
    miniapp_url = getattr(config, 'MINIAPP_URL', 'https://your-miniapp-url.com')
    buttons.append([InlineKeyboardButton("🚀 ᴏᴘᴇɴ ᴍɪɴɪ ᴀᴘᴘ 🚀", web_app=WebAppInfo(url=miniapp_url))])
    buttons.append([InlineKeyboardButton("🛍️ ᴏᴘᴇɴ ᴇxᴄʟᴜsɪᴠᴇ sᴛᴏʀᴇ 🛍️", callback_data="open_store")])
    buttons.append([
        InlineKeyboardButton("👤 ᴍʏ ᴅᴀsʜʙᴏᴀʀᴅ", callback_data="my_plan"),
        InlineKeyboardButton("📞 🌟 ʟɪᴠᴇ sᴜᴘᴘᴏʀᴛ", url=f"https://t.me/{config.CONTACT_USERNAME}")
    ])

    if user_id == config.ADMIN_ID:
        buttons.append([
            InlineKeyboardButton("➕ ᴀᴅᴅ sᴛᴏʀʏ", callback_data="admin_story"),
            InlineKeyboardButton("📺 ᴀᴅᴅ ᴄʜᴀɴɴᴇʟ", callback_data="admin_add"),
            InlineKeyboardButton("🎁 ᴄʀᴇᴀᴛᴇ ᴄᴏᴍʙᴏ", callback_data="admin_combo")
        ])
        buttons.append([
            InlineKeyboardButton("⚙️ ᴍᴀɴᴀɢᴇ ᴀʟʟ", callback_data="admin_channels"),
            InlineKeyboardButton("❌ ʀᴇᴍᴏᴠᴇ sᴜʙ", callback_data="admin_remove")
        ])

    markup = InlineKeyboardMarkup(buttons)
    title = "╔════════════════════════════╗\n       ✨ sᴛᴏʀʏ x ᴅᴇᴍᴏ ✨\n╚════════════════════════════╝"
    desc = """ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ᴛʜᴇ ᴏғғɪᴄɪᴀʟ sᴛᴏʀʏ sᴇʟʟᴇʀ ʙᴏᴛ!

ᴛʜɪs ʙᴏᴛ sᴇʟʟs ᴀʟʟ ᴛʜᴇ ᴘʀᴇᴍɪᴜᴍ ᴀɴᴅ ʟᴀᴛᴇsᴛ sᴛᴏʀɪᴇs ᴏғ ᴘᴏᴄᴋᴇᴛ ғᴍ ᴀɴᴅ ᴘʀᴀᴛɪʟɪᴘɪ ғᴍ. ʏᴏᴜ ᴄʜᴇᴄᴋ ᴛʜᴇ ᴅᴇᴍᴏ ғɪʟᴇs ʜᴇʀᴇ ʙᴇғᴏʀᴇ ᴍᴀᴋɪɴɢ ᴀ ᴘᴜʀᴄʜᴀsᴇ!

⚡ ɪɴsᴛᴀɴᴛ ᴅᴇᴍᴏ | ᴀᴜᴛᴏ ᴘᴀʏᴍᴇɴᴛ | ᴀᴜᴛᴏ ᴅᴇʟɪᴠᴇʀʏ"""

    await message.reply_text(f"{title}\n\n{desc}", reply_markup=markup, parse_mode="HTML")


# ─── 3. TEXT NAVIGATION HANDLERS (FIXED & REAL-TIME) ───
@bot.on_message(filters.private & filters.text & filters.incoming & filters.create(lambda _, __, msg: msg.text in [
    "✨ ᴘʀᴀᴛɪʟɪᴘɪ ғᴍ sᴛᴏʀɪᴇs", 
    "🔥 ᴘᴏᴄᴋᴇᴛ ғᴍ sᴛᴏʀɪᴇs", 
    "🎁 SPECIAL COMBO PACKS (BIG SAVE)",
    "🔙 BACK TO CATEGORIES",
    "« BACK TO MENU",
    "❌ CLOSE STORE",
    "🚫 STORE IS EMPTY"
]))
async def store_navigation_text_handler(client: Client, message: Message):
    user_id = message.from_user.id
    text = message.text

    if text == "🚫 STORE IS EMPTY":
        return await message.reply_text("<blockquote>⚠️ ❌ NO STORY AVAILABLE RIGHT NOW.</blockquote>", parse_mode="HTML")

    if text in ["❌ CLOSE STORE", "« BACK TO MENU"]:
        USER_STATES[user_id] = {"category": "home", "page": 1}
        await message.reply_text("⬅️ <i>Returning to Dashboard Panel...</i>", reply_markup=ReplyKeyboardRemove())
        return await start_handler(client, message)

    if text == "🔙 BACK TO CATEGORIES":
        USER_STATES[user_id] = {"category": "home", "page": 1}
        return await message.reply_text(get_store_text(), reply_markup=get_categories_markup(), parse_mode="HTML")

    # Dynamic Routing strictly matching with database and store file layout
    if text == "✨ ᴘʀᴀᴛɪʟɪᴘɪ ғᴍ sᴛᴏʀɪᴇs":
        USER_STATES[user_id] = {"category": "pratilipi", "page": 1}
        cat_title, c_type = "🎬 <b>ᴘʀᴀᴛɪʟɪᴘɪ ғᴍ sᴛᴏʀɪᴇs</b>", "pratilipi"
    elif text == "🔥 ᴘᴏᴄᴋᴇᴛ ғᴍ sᴛᴏʀɪᴇs":
        USER_STATES[user_id] = {"category": "pocket", "page": 1}
        cat_title, c_type = "🎧 <b>ᴘᴏᴄᴋᴇᴛ ғᴍ sᴛᴏʀɪᴇs</b>", "pocket"
    elif text == "🎁 SPECIAL COMBO PACKS (BIG SAVE)":
        USER_STATES[user_id] = {"category": "combo", "page": 1}
        cat_title, c_type = "🎁 <b>✨ ᴘʀᴇᴍɪᴜᴍ ᴄᴏᴍʙᴏ ᴘᴀᴄᴋs ✨</b>", "combo"

    # Real-time database items rendering
    markup = get_items_by_category_markup(c_type, client.me.username, page=1)
    await message.reply_text(
        f"{cat_title}\n──────────────────────────\n👇 <i>apni pasand ka item select karke full access lein:</i>", 
        reply_markup=markup, 
        parse_mode="HTML"
    )


# ─── 4. PAGINATION HANDLER ───
@bot.on_message(filters.private & filters.text & filters.incoming & filters.create(lambda _, __, msg: msg.text in ["NEXT ›", "‹ PREV"]))
async def store_pagination_handler(client: Client, message: Message):
    user_id = message.from_user.id
    state = USER_STATES.get(user_id, {"category": "home", "page": 1})
    if state["category"] == "home": return

    if message.text == "NEXT ›": state["page"] += 1
    else: state["page"] -= 1

    USER_STATES[user_id] = state
    markup = get_items_by_category_markup(state["category"], client.me.username, page=state["page"])
    await message.reply_text(
        f"<b>AVAILABLE STORIES — {state['category'].upper()}</b>\n`PAGE {state['page']}`\n──────────────────────────", 
        reply_markup=markup, 
        parse_mode="HTML"
    )


# ─── 5. STORY CLICK ROUTER (3 SEPARATE STRICT FLOWS MATCHING INDEX LOGIC) ───
@bot.on_message(filters.private & filters.text & filters.incoming & filters.create(lambda _, __, msg: any(char in msg.text for char in ['[ ₹', '➔ ['])))
async def item_selection_handler(client: Client, message: Message):
    input_text = message.text
    clean_name = input_text
    
    # Strictly handle serial numbers like "1. Story Name [ ₹49 ]"
    if "." in input_text:
        try:
            clean_name = input_text.split(".", 1)[1].split("[")[0].strip()
        except Exception:
            clean_name = input_text.split("[")[0].strip()
    elif "🎁" in input_text:
        clean_name = input_text.replace("🎁", "").split("➔")[0].strip()

    state = USER_STATES.get(message.from_user.id, {"category": "pratilipi"})
    
    if state["category"] == "combo":
        data = channels_col.find_one({"combo_name": clean_name})
    elif state["category"] == "pocket":
        data = channels_col.find_one({"story_name": clean_name, "source": "pocket"})
    elif state["category"] == "pratilipi":
        data = channels_col.find_one({"story_name": clean_name, "source": "pratilipi"})
    else:
        data = channels_col.find_one({"name": clean_name}) or channels_col.find_one({"story_name": clean_name})

    if not data:
        return await message.reply_text("❌ Is item ki details load nahi ho payi.")

    load_msg = await message.reply_text("⌛ <i>Loading Details...</i>", reply_markup=ReplyKeyboardRemove(), parse_mode="HTML")
    inline_buttons = []
    db_id = data.get('item_id') or data.get('channel_id')

    # ─── 🎁 FLOW 1: COMBO PACK ───
    if data.get('is_combo'):
        inline_buttons.append([InlineKeyboardButton(f"✅ CONFIRM & PAY COMBO - ₹{data['price']}", callback_data=f"select_{db_id}_manual")])
        header = "🎁 <b>ᴘʀᴇᴍɪᴜᴍ sᴘᴇᴄɪᴀʟ ᴄᴏᴍʙᴏ ʙᴜɴᴅʟᴇ</b>"
        item_label = data.get('combo_name')
        desc_text = f"📝 <b>ɪɴᴄʟᴜᴅᴇᴅ sᴛᴏʀɪᴇs:</b>\n<i>{data.get('description', 'Multiple bundles inside!')}</i>"
        
    # ─── 📢 FLOW 2: FORWARDED CHANNEL (/add Flow) ───
    elif 'channel_id' in data and not data.get('story_name'):
        if data.get('plans') and isinstance(data['plans'], dict):
            for p_time, p_price in data['plans'].items():
                inline_buttons.append([InlineKeyboardButton(f"💳 {get_time_string(p_time)} - ₹{p_price}", callback_data=f"select_{db_id}_{p_time}")])
        else:
            inline_buttons.append([InlineKeyboardButton(f"✅ CONFIRM & PAY - ₹{data.get('price', '49')}", callback_data=f"select_{db_id}_manual")])
            
        header = "📢 <b>ᴘʀᴇᴍɪᴜᴍ ᴘʀɪᴠᴀᴛᴇ ᴄʜᴀɴɴᴇʟ</b>"
        item_label = data.get('name', 'VIP Channel')
        desc_text = "🤖 <b>ᴅᴇʟɪᴠᴇʀʏ:</b> <code>ᴄʜᴀɴɴᴇʟ ɪɴᴠɪᴛᴇ ʟɪɴᴋ (𝟷-ᴛɪᴍᴇ ᴜsᴇ)</code>\nℹ️ <i>Is pack me aapko private channel join karne ka temporary link milega.</i>"

    # ─── 🔥 FLOW 3: MANUAL STORY (/add_story Flow) ───
    else:
        inline_buttons.append([InlineKeyboardButton(f"💳 UNLOCK PREMIUM STORY - ₹{data.get('price', '49')}", callback_data=f"select_{db_id}_manual")])
        header = f"🔥 <b>ᴘʀᴇᴍɪᴜᴍ ᴇxᴄʟᴜsɪᴠᴇ sᴛᴏʀʏ ({data.get('source', 'audio')})</b>"
        item_label = data.get('story_name')
        desc_text = "🤖 <b>ᴅᴇʟɪᴠᴇʀʏ:</b> <code>ɪɴsᴛᴀɴᴛ ʙᴏᴛ ʟɪɴᴋ ᴀᴄᴄᴇss</code>\nℹ️ <i>Is pack me aapko direct bot file redirection button milega.</i>"

    if data.get('demo_link'):
        inline_buttons.append([InlineKeyboardButton("📺 ᴠɪᴇᴡ ǫᴜᴀʟɪᴛʏ ᴅᴇᴍᴏ (ᴛᴇᴀsᴇʀ)", url=data['demo_link'])])
    
    inline_buttons.append([InlineKeyboardButton("⬅️ BACK TO LIST", callback_data="return_to_list_True")])
    inline_markup = InlineKeyboardMarkup(inline_buttons)

    details_text = f"{header}\n──────────────────────────\n📦 <b>ɪᴛᴇᴍ:</b> <code>{item_label}</code>\n\n{desc_text}\n──────────────────────────"
    
    photo_id = data.get('file_id')
    if photo_id:
        await client.send_photo(chat_id=message.chat.id, photo=photo_id, caption=details_text, reply_markup=inline_markup, parse_mode="HTML")
    else:
        await client.send_message(chat_id=message.chat.id, text=details_text, reply_markup=inline_markup, parse_mode="HTML")

    try:
        await load_msg.delete()
    except Exception:
        pass


# ─── 6. CALLBACK HANDLERS ───
@bot.on_callback_query(filters.regex("^return_to_list_"))
async def return_to_list_callback(client: Client, call: CallbackQuery):
    await call.answer()
    state = USER_STATES.get(call.from_user.id, {"category": "pratilipi", "page": 1})
    try:
        await call.message.delete()
    except Exception:
        pass
    markup = get_items_by_category_markup(state["category"], client.me.username, page=state["page"])
    await client.send_message(call.message.chat.id, "👇 <i>apni pasand ka item select karke full access lein:</i>", reply_markup=markup, parse_mode="HTML")

@bot.on_callback_query(filters.regex("^open_store$"))
async def open_store_callback(client: Client, call: CallbackQuery):
    await call.answer()
    try:
        await call.message.delete()
    except Exception:
        pass
    await client.send_message(call.message.chat.id, get_store_text(), reply_markup=get_categories_markup(), parse_mode="HTML")

@bot.on_callback_query(filters.regex("^back_to_start$"))
async def back_to_start_callback(client: Client, call: CallbackQuery):
    await call.answer()
    try:
        await call.message.delete()
    except Exception:
        pass
    await start_handler(client, call.message)

@bot.on_callback_query(filters.regex("^my_plan$"))
async def my_plan_callback(client: Client, call: CallbackQuery):
    u_id = call.from_user.id
    await call.answer()
    load_title_msg = await client.send_message(u_id, "⌛ <i>Opening Dashboard...</i>", reply_markup=ReplyKeyboardRemove(), parse_mode="HTML")
    
    back_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("🛍️ Open Store", callback_data="open_store"), 
         InlineKeyboardButton("« ʙᴀᴄᴋ ᴛᴏ ᴍᴇɴᴜ", callback_data="back_to_start")]
    ])

    if u_id == config.ADMIN_ID:
        all_subs = list(users_col.find().sort("expiry", 1))
        try:
            await load_title_msg.delete()
        except Exception:
            pass

        if not all_subs:
            return await client.send_message(u_id, "📋 **Database clear hai. Koi active premium member nahi mila.**", reply_markup=back_markup, parse_mode="HTML")

        report = "📋 <b>ᴀʟʟ ᴀᴄᴛɪᴠᴇ sᴜʙsᴄʀɪᴘᴛɪᴏɴs (ᴀᴅᴍɪɴ)</b>\n──────────────────────────\n\n"
        for s in all_subs:
            ch = channels_col.find_one({"channel_id": s['channel_id']})
            ch_name = ch.get('story_name') or ch.get('combo_name', 'Deleted Pack') if ch else 'Unknown Pack'
            days_left = (datetime.fromtimestamp(s['expiry']) - datetime.now()).days
            report += f"👤 <code>{s['user_id']}</code>\n➔ 📦 {ch_name}\n➔ ⏳ Left: <b>{max(0, days_left)} Days</b>\n─────────────────\n"
        await client.send_message(u_id, text=report, reply_markup=back_markup, parse_mode="HTML")
    else:
        subs = list(users_col.find({"user_id": u_id}))
        try:
            await load_title_msg.delete()
        except Exception:
            pass

        if not subs:
            return await client.send_message(u_id, "❌ <b><b>ɴᴏ ᴀᴄᴛɪᴠᴇ ᴘʟᴀɴ</b></b>\n\nAapka filhal koi active plan nahi chal raha hai.", reply_markup=back_markup, parse_mode="HTML")

        res = "👤 <b>ᴍʏ ᴘᴇʀsᴏɴᴀʟ ᴅᴀsʜʙᴏᴀʀᴅ</b>\n──────────────────────────\n\n"
        for s in subs:
            ch = channels_col.find_one({"channel_id": s['channel_id']})
            name = ch.get('story_name') or ch.get('combo_name', 'Premium Bundle') if ch else 'Premium Access'
            expiry = datetime.fromtimestamp(s['expiry']).strftime('%d %b %Y | %I:%M %p')
            res += f"🎬 <b>ɪᴛᴇμ:</b> {name}\n⌛ <b>ᴇxᴘɪʀʏ:</b> <code>{expiry}</code>\n──────────────────────────\n"
        await client.send_message(u_id, text=res, reply_markup=back_markup, parse_mode="HTML")
