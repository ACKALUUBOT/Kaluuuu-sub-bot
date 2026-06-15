from pyrogram.types import ReplyKeyboardMarkup, KeyboardButton
from database import channels_col
import config

# ─── 1. BOTTOM KEYBOARD CATEGORIES MENU (WITH COMBO PACKS) ───
def get_categories_markup():
    """User ko niche keyboard me 3 categories dikhane ke liye"""
    markup = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton("✨ ᴘʀᴀᴛɪʟɪᴘɪ ғᴍ sᴛᴏʀɪᴇs")],
            [KeyboardButton("🔥 ᴘᴏᴄᴋᴇᴛ ғᴍ sᴛᴏʀɪᴇs")],
            [KeyboardButton("🎁 SPECIAL COMBO PACKS (BIG SAVE)")],
            [KeyboardButton("« BACK TO MENU")]
        ],
        resize_keyboard=True
    )
    return markup


# ─── 2. PAGINATED ITEMS MENU BY CATEGORY (DYNAMIC FILTER FIXED) ───
def get_items_by_category_markup(category_type, bot_username=None, page=1):
    """Source aur combo ke hisab se database se items filter karega (8 items per page)"""
    
    # 🌟 REAL-TIME DATABASE FETCH FILTER
    if category_type == "pratilipi":
        # Strict filter for pratilipi stories (excluding combos)
        all_items = list(channels_col.find({"story_name": {"$exists": True}, "source": "pratilipi", "is_combo": {"$exists": False}}))
    elif category_type == "pocket":
        # Strict filter for pocket stories (excluding combos)
        all_items = list(channels_col.find({"story_name": {"$exists": True}, "source": "pocket", "is_combo": {"$exists": False}}))
    elif category_type == "combo":
        # Pure filter for registered combo bundles only
        all_items = list(channels_col.find({"is_combo": True}))
    else:
        all_items = []
        
    # Agar data nahi hai toh direct ye button show hoga
    if not all_items:
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton("🚫 STORE IS EMPTY")],
                [KeyboardButton("🔙 BACK TO CATEGORIES")]
            ],
            resize_keyboard=True
        )

    per_page = 8
    total_items = len(all_items)
    total_pages = (total_items + per_page - 1) // per_page
    
    if page < 1: page = 1
    if page > total_pages: page = total_pages
    
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    sliced_items = all_items[start_idx:end_idx]

    # Dynamically build layout list for Pyrogram keyboard
    keyboard_layout = []

    # Buttons display generation loop (Aligned with start.py item selection handler)
    for index, item in enumerate(sliced_items, start=start_idx + 1):
        if category_type == "combo":
            # Aligned with split pattern: "🎁 " handling
            btn_text = f"🎁 {item['combo_name']} ➔ [ ₹{item['price']} ]"
        else:
            # Aligned with split pattern: "{index}. {story_name}" handling
            btn_text = f"{index}. {item['story_name']} [ ₹{item['price']} ]"
            
        keyboard_layout.append([KeyboardButton(btn_text)])
            
    # Navigation Row (Next/Prev Setup)
    nav_buttons = []
    if page > 1:
        nav_buttons.append(KeyboardButton("‹ PREV"))
    if page < total_pages:
        nav_buttons.append(KeyboardButton("NEXT ›"))
        
    if nav_buttons:
        keyboard_layout.append(nav_buttons)
        
    # Bottom Static Navigation Controls
    keyboard_layout.append([KeyboardButton("🔙 BACK TO CATEGORIES")])
    keyboard_layout.append([KeyboardButton("❌ CLOSE STORE")])
    
    return ReplyKeyboardMarkup(keyboard=keyboard_layout, resize_keyboard=True)


# ─── 3. TEXT FOR CATEGORIES PAGE ───
def get_store_text():
    return (
        "🛍️ <b>ᴘʀᴇᴍɪᴜᴍ sᴛᴏʀỹ ᴄᴀᴛᴇɢᴏʀɪᴇs</b> 🛍️\n"
        "──────────────────────────\n"
        "ᴀᴀᴘ ᴋɪs ᴘʟᴀᴛғᴏʀᴍ ᴋɪ sᴛᴏʀɪᴇs ᴅᴇᴋʜɴᴀ ᴄʜᴀʜᴛᴇ ʜᴀɪɴ? ɴɪᴄʜᴇ sᴇ sᴇʟᴇᴄᴛ ᴋᴀʀᴇɪɴ:\n\n"
        "✨ <b>ᴘʀ่าᴛɪʟɪᴘɪ ғᴍ sᴛᴏʀɪᴇs:</b> sᴇʟᴇᴄᴛ ᴛᴏ ᴠɪᴇᴡ ᴀʟʟ ᴘʀᴀᴛɪʟɪᴘɪ sᴛᴏʀɪᴇs.\n"
        "🔥 <b>ᴘᴏᴄᴋᴇᴛ ғᴍ sᴛᴏʀɪᴇs:</b> sᴇʟᴇᴄᴛ ᴛᴏ ᴠɪᴇᴡ ᴀʟʟ ᴘᴏᴄᴋᴇᴛ ғᴍ sᴛᴏʀɪᴇs.\n"
        "🎁 <b>sᴘᴇᴄɪᴀʟ ᴄᴏᴍʙᴏ ᴘᴀᴄᴋs:</b> ᴍᴜʟᴛɪ-sᴛᴏʀɪᴇs ʙᴜɴᴅʟᴇ ᴀᴛ ᴀ ᴄʜᴇᴀᴘ ᴘʀɪᴄᴇ!\n"
        "──────────────────────────"
    )
