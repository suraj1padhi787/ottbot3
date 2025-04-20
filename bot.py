import asyncio
import random
import os
import openai
from telethon import TelegramClient, events, functions, types

# Railway Environment Variables
api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
openai_api_key = os.getenv("OPENAI_API_KEY")
session_name = 'newuserbot'

client = openai.OpenAI(api_key=openai_api_key)
telegram_client = TelegramClient(session_name, api_id, api_hash)

GROUP_ID = -1002470019043

system_prompt = """
Tum ek professional aur friendly OTT, Game Hack, Adult Site aur ChatGPT Premium seller ho India me.

Services:
- OTT: Netflix, Prime Video, Hotstar, SonyLIV, Zee5, YouTube Premium, Telegram Premium
- Adult Sites: Pornhub, OnlyFans, Fansly
- Game Hacks: Titan, Vision, Lethal, GTA V, COD
- ChatGPT Premium 1 Year

Pricing:
- OTT: 1 Year ₹500, 6 Months ₹350
- Adult Sites: 1 Year ₹500, 6 Months ₹300
- Games: Week ₹800, Month ₹1300
- ChatGPT: 1 Year ₹1000

Rules:
- 6M lene wale ko politely ek baar suggest karo 1Y ka lena better hai.
- Platform aur Validity final hone ke baad hardcoded confirmation message bhejna.
- Confirm hone par poora group me post karna.
- AI conversation natural human jaise karna.
- Gali par 3 warning aur mute.
- Typing animation aur Always Online.

"""

user_context = {}
user_flow = {}
warned_users = {}
muted_users = set()
ai_active = True

async def send_typing(event):
    try:
        await event.client(functions.messages.SetTypingRequest(
            peer=event.chat_id,
            action=types.SendMessageTypingAction()
        ))
        await asyncio.sleep(random.uniform(0.8, 1.5))
    except:
        pass

async def keep_online():
    while True:
        try:
            await telegram_client(functions.account.UpdateStatusRequest(offline=False))
        except:
            pass
        await asyncio.sleep(60)

async def clear_messages():
    while True:
        try:
            async for message in telegram_client.iter_messages(GROUP_ID, limit=100):
                try:
                    await telegram_client.delete_messages(GROUP_ID, message.id)
                except:
                    pass
        except:
            pass
        await asyncio.sleep(3600)

confirm_words = ['haa', 'han', 'ha', 'krde', 'karde', 'kar de', 'ok', 'confirm', 'done']

@telegram_client.on(events.NewMessage(outgoing=False))
async def handler(event):
    global ai_active

    sender = await event.get_sender()
    sender_id = sender.id
    user_message = event.raw_text.strip().lower()

    if sender_id in muted_users:
        return

    if user_message == '/stopai' and sender_id == int(os.getenv("OWNER_ID", "0")):
        ai_active = False
        await event.respond("✅ AI reply band kar diya gaya hai.")
        return

    if user_message == '/startai' and sender_id == int(os.getenv("OWNER_ID", "0")):
        ai_active = True
        await event.respond("✅ AI reply wapas chalu kar diya gaya hai.")
        return

    if not ai_active:
        return

    # Gali Check
    bad_words = ["madarchod", "bhenchod", "lode", "loda", "gaand", "chutiya", "mc", "bc", "bkl"]
    if any(word in user_message for word in bad_words):
        warned_users[sender_id] = warned_users.get(sender_id, 0) + 1
        if warned_users[sender_id] >= 3:
            muted_users.add(sender_id)
            await event.respond("🚫 Tumhe mute kar diya gaya hai.")
            return
        else:
            await event.respond(f"⚠️ Warning {warned_users[sender_id]}: Gali mat do bhai.")
            return

    await send_typing(event)

    if sender_id not in user_context:
        user_context[sender_id] = []

    user_context[sender_id].append({"role": "user", "content": user_message})
    if len(user_context[sender_id]) > 10:
        user_context[sender_id] = user_context[sender_id][-10:]

    try:
        flow = user_flow.get(sender_id, {})

        if flow.get('platform') and flow.get('validity') and not flow.get('waiting_confirm'):
            selected_service = flow.get('service', 'Subscription')
            selected_platform = flow['platform']
            selected_validity = flow['validity']
            selected_price = flow['price']

            await event.respond(f"✅ Tumne {selected_platform} ka {selected_validity} plan select kiya hai. Confirm karo bhai (haa/ok).")
            flow['waiting_confirm'] = True
            user_flow[sender_id] = flow
            return

        if flow.get('waiting_confirm') and any(word in user_message for word in confirm_words):
            user_link = f'<a href="tg://user?id={sender_id}">{sender.first_name}</a>'

            post_text = f"""
✅ New Payment Confirmation!

👤 User: {user_link}
🎯 Service: {flow.get('service', 'Subscription').title()}
🏷️ Platform: {flow['platform']}
💰 Amount: ₹{flow['price']}
⏳ Validity: {flow['validity']}

🚀 Enjoy full premium experience bhai! ❤️
"""
            await telegram_client.send_message(GROUP_ID, post_text, parse_mode='html')
            await event.respond("✅ QR code generate ho raha hai bhai 📲 Wait karo 😎")
            user_flow.pop(sender_id, None)
            return

        # Normal AI Chat Flow
        messages_for_gpt = [{"role": "system", "content": system_prompt}] + user_context[sender_id]

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages_for_gpt,
            temperature=0.5
        )

        bot_reply = response.choices[0].message.content
        user_context[sender_id].append({"role": "assistant", "content": bot_reply})

        # Platform detection smart
        if any(x in user_message for x in ['netflix', 'prime', 'hotstar', 'zee5', 'youtube', 'telegram']):
            flow = {'service': 'OTT Subscription', 'platform': user_message.title(), 'validity': None, 'price': None, 'waiting_confirm': False, 'promotion_done': False}
            user_flow[sender_id] = flow
            await event.respond("✅ Netflix/OTT ke liye 6 Months ₹350 ya 1 Year ₹500 available hai. Konsa chahoge?")
            return

        if any(x in user_message for x in ['pornhub', 'onlyfans', 'fansly']):
            flow = {'service': 'Adult Site', 'platform': user_message.title(), 'validity': None, 'price': None, 'waiting_confirm': False, 'promotion_done': False}
            user_flow[sender_id] = flow
            await event.respond("✅ Adult site ke liye 6 Months ₹300 ya 1 Year ₹500 available hai. Konsa chahoge?")
            return

        if any(x in user_message for x in ['gta', 'titan', 'vision', 'cod']):
            flow = {'service': 'Game Hack', 'platform': user_message.title(), 'validity': None, 'price': None, 'waiting_confirm': False, 'promotion_done': False}
            user_flow[sender_id] = flow
            await event.respond("✅ Game hack ke liye Week ₹800 ya Month ₹1300 available hai. Konsa chahoge?")
            return

        if 'chatgpt' in user_message:
            flow = {'service': 'ChatGPT Premium', 'platform': 'ChatGPT', 'validity': '1 Year', 'price': 1000, 'waiting_confirm': False}
            user_flow[sender_id] = flow
            await event.respond("✅ ChatGPT Premium 1 Year ₹1000 - Confirm karo bhai (haa/ok)")
            return

        if flow.get('platform') and not flow.get('validity'):
            if '6' in user_message and not flow.get('promotion_done'):
                await event.respond("✅ Bhai 1 Year ka lena better rahega, ₹500 me full saal chalega ❤️")
                flow['promotion_done'] = True
            if '6' in user_message:
                flow['validity'] = '6 Months'
                flow['price'] = 350 if flow['service'] == 'OTT Subscription' else 300
            elif '1' in user_message or '12' in user_message:
                flow['validity'] = '1 Year'
                flow['price'] = 500
            elif 'week' in user_message:
                flow['validity'] = '1 Week'
                flow['price'] = 800
            elif 'month' in user_message:
                flow['validity'] = '1 Month'
                flow['price'] = 1300
            user_flow[sender_id] = flow

        await event.respond(bot_reply)

    except Exception as e:
        await event.respond("❌ Error aaya bhai, try later.")
        print(f"Error: {e}")

telegram_client.start()
telegram_client.loop.create_task(keep_online())
telegram_client.loop.create_task(clear_messages())
telegram_client.run_until_disconnected()
