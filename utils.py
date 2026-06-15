from datetime import datetime, timedelta
from pyrogram import Client
import config
from database import users_col, channels_col

# Pyrogram Client इनिशियलाइजेशन (जो main.py में इम्पोर्ट होगा)
bot = Client(
    "story_store_bot",
    api_id=config.API_ID,       # ध्यान दें: Pyrogram के लिए config में API_ID होना ज़रूरी है
    api_hash=config.API_HASH,   # config में API_HASH होना ज़रूरी है
    bot_token=config.BOT_TOKEN
)

def get_time_string(mins):
    mins = int(mins)
    if mins < 60: return f"{mins} Min"
    if mins < 1440: return f"{mins//60} Hours"
    return f"{mins//1440} Days"

# Pyrogram में टेलीग्राम ऑपरेशन्स के लिए फंक्शन को async बनाना आवश्यक है
async def approve_user_logic(u_id, ch_id, mins, method="Automatic"):
    user_record = users_col.find_one({"user_id": u_id, "channel_id": ch_id})
    now = datetime.now()
    base_time = datetime.fromtimestamp(user_record['expiry']) if user_record and user_record['expiry'] > now.timestamp() else now
    new_expiry = base_time + timedelta(minutes=mins)

    try:
        # Pyrogram Method: create_chat_invite_link (member_limit और expire_date के साथ)
        link = await bot.create_chat_invite_link(
            chat_id=ch_id, 
            member_limit=1, 
            expire_date=int(new_expiry.timestamp())
        )
        
        users_col.update_one(
            {"user_id": u_id, "channel_id": ch_id}, 
            {"$set": {"expiry": new_expiry.timestamp()}}, 
            upsert=True
        )
        
        msg_text = (
            f"🥳 <b>Subscription Activated!</b>\n\n"
            f"<b>Plan:</b> {get_time_string(mins)}\n"
            f"<b>Expires:</b> {new_expiry.strftime('%Y-%m-%d %H:%M')}\n"
            f"<b>Method:</b> {method}\n\n"
            f"🔗 <b>Join Link:</b> {link.invite_link}"
        )
        
        # Pyrogram send_message (parse_mode डिफ़ॉल्ट रूप से HTML/Markdown सपोर्ट करता है)
        await bot.send_message(u_id, msg_text)
        await bot.send_message(config.ADMIN_ID, f"✅ <b>Approved:</b> User <code>{u_id}</code> via {method}")
        
    except Exception as e:
        await bot.send_message(config.ADMIN_ID, f"❌ <b>Approval Error:</b> {str(e)}")

