import os

BOT_TOKEN = os.getenv('BOT_TOKEN')
MONGO_URI = os.getenv('MONGO_URI')
ADMIN_ID = int(os.getenv('ADMIN_ID', 0))
UPI_ID = os.getenv('UPI_ID')
CONTACT_USERNAME = os.getenv('CONTACT_USERNAME')

# ─── ⚡ PYROGRAM EXTRA CONFIGS ───
# Pyrogram को चलाने के लिए इन दो वेरिएबल्स की ज़रूरत होती है
API_ID = int(os.getenv('API_ID', 0))          # my.telegram.org से मिलने वाला ID
API_HASH = os.getenv('API_HASH', '')          # my.telegram.org से मिलने वाला HASH

# Razorpay Configs
RZP_KEY_ID = os.getenv('RZP_KEY_ID', '')
RZP_KEY_SECRET = os.getenv('RZP_KEY_SECRET', '')
RZP_WEBHOOK_SECRET = os.getenv('RZP_WEBHOOK_SECRET', '')

BASE_URL = os.getenv('BASE_URL', 'https://ac-sub-bot.onrender.com')
