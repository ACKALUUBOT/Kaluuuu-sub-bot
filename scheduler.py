import asyncio
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from database import users_col
from utils import bot

def check_expiries():
    expired = list(users_col.find({"expiry": {"$lte": datetime.now().timestamp()}}))
    for user in expired:
        try:
            # Pyrogram के इवेंट लूप को गेट करना
            loop = bot.loop
            
            # 1. Ban Chat Member (Async execution inside sync thread)
            ban_future = asyncio.run_coroutine_threadsafe(
                bot.ban_chat_member(chat_id=user['channel_id'], user_id=user['user_id']),
                loop
            )
            ban_future.result(timeout=10) # Wait for execution
            
            # 2. Unban Chat Member (Taaki user baad me fir se join kar sake)
            unban_future = asyncio.run_coroutine_threadsafe(
                bot.unban_chat_member(chat_id=user['channel_id'], user_id=user['user_id']),
                loop
            )
            unban_future.result(timeout=10)
            
            # डेटाबेस से रिकॉर्ड डिलीट करना
            users_col.delete_one({"_id": user['_id']})
        except Exception as e: 
            print(f"Scheduler single-user processing error: {e}")
            pass

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_expiries, 'interval', minutes=1)
    scheduler.start()
          
