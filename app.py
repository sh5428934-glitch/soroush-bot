from flask import Flask, request, jsonify
import asyncio
import threading
from datetime import datetime
from spluspy import Client, events
from spluspy.tl.functions.account import UpdateProfileRequest
import os

app = Flask(__name__)

PHONE = "+989922742686"

bot_status = {
    "running": False,
    "connected": False,
    "first_name": "",
    "clock_active": False,
    "last_time": "",
    "waiting_code": False,
    "code_needed": False
}

phone_code_hash = None
pending_code = None

class ClockBot:
    def __init__(self):
        self.client = None
        self.clock_active = False
        self.clock_task = None
        self.last_time = ""
    
    async def start(self):
        global phone_code_hash
        
        self.client = Client("/tmp/session.session")
        await self.client.connect()
        
        try:
            await self.client.start(phone=PHONE)
        except:
            bot_status['waiting_code'] = True
            bot_status['code_needed'] = True
            
            result = await self.client.send_code_request(PHONE)
            phone_code_hash = result.phone_code_hash
            
            while pending_code is None:
                await asyncio.sleep(1)
            
            await self.client.sign_in(PHONE, phone_code_hash, pending_code)
            bot_status['waiting_code'] = False
            bot_status['code_needed'] = False
        
        me = await self.client.get_me()
        bot_status['connected'] = True
        bot_status['first_name'] = me.first_name
        bot_status['running'] = True
        
        @self.client.on(events.NewMessage)
        async def handler(event):
            if str(event.sender_id) != str(me.id):
                return
            
            chat = await event.get_chat()
            text = event.text or ""
            
            if text == ".ساعت":
                if self.clock_active:
                    await self.stop_clock()
                    await self.client.send_message(chat, "🔴 ساعت غیرفعال شد", reply_to=event.id)
                else:
                    await self.start_clock()
                    await self.client.send_message(chat, "🟢 ساعت فعال شد", reply_to=event.id)
            
            elif text == ".پنل":
                panel = """━━━━━━━━━━━━━━━━━━━━
📋 پنل سلف‌بات
━━━━━━━━━━━━━━━━━━━━
🕐 .ساعت → فعال/غیرفعال
━━━━━━━━━━━━━━━━━━━━"""
                await self.client.send_message(chat, panel, reply_to=event.id)
        
        await self.client.run_until_disconnected()
    
    async def start_clock(self):
        self.clock_active = True
        bot_status['clock_active'] = True
        self.clock_task = asyncio.create_task(self._clock_loop())
    
    async def stop_clock(self):
        if self.clock_task:
            self.clock_task.cancel()
        self.clock_active = False
        bot_status['clock_active'] = False
        me = await self.client.get_me()
        await self.client(UpdateProfileRequest(first_name=me.first_name, last_name=""))
    
    async def _clock_loop(self):
        while True:
            try:
                now = datetime.now().strftime("%H:%M")
                if now != self.last_time:
                    self.last_time = now
                    bot_status['last_time'] = now
                    me = await self.client.get_me()
                    await self.client(UpdateProfileRequest(first_name=me.first_name, last_name=now))
            except:
                pass
            await asyncio.sleep(10)

@app.route('/')
def home():
    return jsonify(bot_status)

@app.route('/api/ping')
def ping():
    return jsonify({"status": "ok"})

@app.route('/api/send-code')
def send_code():
    global phone_code_hash
    async def send():
        global phone_code_hash
        client = Client("/tmp/session2.session")
        await client.connect()
        result = await client.send_code_request(PHONE)
        phone_code_hash = result.phone_code_hash
        await client.disconnect()
        return result
    loop = asyncio.new_event_loop()
    result = loop.run_until_complete(send())
    loop.close()
    bot_status['waiting_code'] = True
    return jsonify({
        "success": True,
        "message": f"کد تایید به {PHONE} ارسال شد"
    })

@app.route('/api/verify-code', methods=['POST'])
def verify_code():
    global pending_code
    data = request.json
    code = data.get('code', '')
    if not code:
        return jsonify({"success": False, "error": "کد رو وارد کن"})
    pending_code = code
    return jsonify({"success": True, "message": "کد دریافت شد"})

def run_bot():
    bot = ClockBot()
    asyncio.run(bot.start())

threading.Thread(target=run_bot, daemon=True).start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
