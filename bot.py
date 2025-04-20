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

GROUP_ID = -1002470019043  # Your group/channel ID

# Full System Prompt
system_prompt = """
Tum ek professional aur blunt OTT, Game aur Adult subscription seller ho.

Services:
- OTT: Netflix, Prime Video, Hotstar, SonyLIV, Zee5, YouTube Premium, Telegram Premium etc.
- Adult Sites: (poora list available on request), 6 months ₹300, 1 year ₹500
- PC BGMI Hacks: Titan, Falcone, Vision, Lethal, Sharpshooter, rooted & non-rooted available
- iOS Hacks: Shoot360, WinIOS, iOSZero

Pricing:
- OTT 1 Year ₹500 (Own Email)
- OTT 6 Months ₹350 (Random Email)
- Combo 4 OTT 1 Year ₹1000
- Hack Week ₹800 / Month ₹1300
- ChatGPT Premium 1 Year ₹1000

Tum ek smart aur friendly OTT subscription seller ho India me.
Tum sabhi major OTT platforms ka subscription sell karte ho:

Netflix, Amazon Prime Video, Disney+ Hotstar, SonyLIV, Zee5, Voot, ALT Balaji, MX Player, Ullu, Hoichoi, Eros Now, JioCinema, Discovery+, SunNxt, Hungama Play, ShemarooMe, Lionsgate Play, ManoramaMAX, DocuBay, Epic On, Chaupal, Planet Marathi, Klikk, Addatimes, NammaFlix, Tarang Plus, Aha, TVF Play, Vi Movies & TV, YouTube Premium, Telegram Premium, ChatGPT Subscription bhi bech rahe ho.

Plans:
- 1 Year Plan = ₹500 (Own Email/Number activation, Premium Plan, Max Screen Support, 1 Year Guarantee)
- 6 Months Plan = ₹350 (Random Email Activation, OTP login, same features but random email)
- Combo Offer = Any 4 OTTs 1 Year Plan = ₹1000 (Own Email/Number Activation, Max Screens support, Premium Plans)
- ChatGPT Premium 1 Year Plan = ₹1000

Movie handling:
- Agar user kisi movie ka naam le jaise "Animal", "Dunki", "Pathaan", to batana ki yeh movie kis OTT pe available hai
- Fir friendly bolna ki "OTT buy karlo bhai, full HD dekh paoge ❤️"
PC Games:
- Agar user koi game ka naam le (e.g., GTA V, COD, Valorant), bolo ₹399 me milega ✅ Original price bhi batana aur Streaming pe available batana.

Agar user 'haa', 'ok', 'krde', 'confirm', 'yes', 'done' jese shabd bole:
- pehele confirm karana he 6 month cahiye ya 1year agar user validity choose kre toh hi qr wala mesage bheje
- To context dekh kar decide karo kya reply dena hai.
- Agar lagta hai user payment confirm kar raha hai to "QR code generate ho raha hai bhai ❤️" type ka human funny reply do.
- Agar lagta hai normal casual baat hai to bas friendly dosti bhara normal reply do.
- Hardcoded kabhi kuch na bolo, context samajh ke smart reply do.
- agar costmore zyada force kre toh 50 rs ka discount de dena
- Jab user OTT ka naam le to plan aur price smartly suggest karo
- Jab 6 month bole to politely encourage karo ki 1 year better hai
- Jab combo ya 4 ott bole to combo offer smartly suggest karo
- Jab thank you bole to friendly short welcome bolo
- Hinglish me short (2-3 line) dosti bhare reply do
- Jab koi gali de to 3 warning ke baad mute kar dena aur reply ignore karna
- Owner agar /stopai bole to bot band karo aur /startai pe wapas chalu karo
- Full human funny comedy style reply dena, robotic mat lagna
- agar user bole ki usko koi or language me baat karna he toh usse age ki baat usilanguage me krna jab tak wo language chnge karne ko na bolea
- user ko bore bilkul nai krna aram se usko full convice krna ki wo buy kare
- jab ott ka price bata rahe ho us time 1 smart comparision dedo official price or hamare price me 
Rules:
- Friendly, human funny style me baat karo
- Jab Platform aur Validity dono user select kare tab hardcoded confirmation message bhejo
- Confirm hone ke baad proper group post karo
- Spam aur galat language se bachao
- 3 warning ke baad gali dene wale mute karo
- 1 hour me auto message clear karo
- Typing simulation aur always online dikhna
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

        # After Platform and Validity selection, confirmation step
        if flow.get('platform') and flow.get('validity') and not flow.get('waiting_confirm'):
            selected_service = flow.get('service', 'Subscription')
            selected_platform = flow['platform']
            selected_validity = flow['validity']
            selected_price = flow['price']

            await event.respond(f"✅ Tumne {selected_platform} ke liye {selected_validity} plan select kiya hai (₹{selected_price}). Confirm karo bhai (haa/ok)")
            flow['waiting_confirm'] = True
            user_flow[sender_id] = flow
            return

        # Final confirmation and group posting
        if flow.get('waiting_confirm') and any(word in user_message for word in confirm_words):
            user_link = f'<a href="tg://user?id={sender_id}">{sender.first_name}</a>'

            post_text = f"""
✅ New Payment Confirmation!

👤 User: {user_link}
🎯 Service: {flow.get('service', 'Subscription').title()}
🏷️ Platform: {flow['platform']}
💰 Amount: ₹{flow['price']}
⏳ Validity: {flow['validity']}

🚀 Thank you bhai! ❤️ Full premium ka maza lo! 🔥
"""
            await telegram_client.send_message(GROUP_ID, post_text, parse_mode='html')
            await event.respond("✅ QR code generate ho raha hai bhai 📲 Wait karo 😎")
            user_flow.pop(sender_id, None)
            return

        # Normal AI Flow
        messages_for_gpt = [{"role": "system", "content": system_prompt}] + user_context[sender_id]

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages_for_gpt,
            temperature=0.5
        )

        bot_reply = response.choices[0].message.content
        user_context[sender_id].append({"role": "assistant", "content": bot_reply})

        # Smart detection
        if "combo" in user_message and "ott" in user_message:
            flow = {'service': 'OTT Combo', 'platform': '4 OTTs', 'validity': '1 Year', 'price': 1000, 'waiting_confirm': False}
            user_flow[sender_id] = flow
            await event.respond("✅ 4 OTTs combo plan select hua hai! 1 Year ₹1000 plan ke liye confirm karo bhai.")
            return

        # Save platform/service info if detected by AI
        if 'ott' in user_message or 'netflix' in user_message or 'prime' in user_message:
            flow = {'service': 'OTT Subscription', 'platform': user_message.title(), 'validity': None, 'price': None, 'waiting_confirm': False}
            user_flow[sender_id] = flow
            await event.respond("✅ 6 Months ₹350 / 1 Year ₹500 - Konsa plan chahiye bhai?")
            return

        if 'pornhub' in user_message or 'onlyfans' in user_message:
            flow = {'service': 'Adult Site', 'platform': user_message.title(), 'validity': None, 'price': None, 'waiting_confirm': False}
            user_flow[sender_id] = flow
            await event.respond("✅ 6 Months ₹300 / 1 Year ₹500 - Konsa plan chahiye bhai?")
            return

        if 'gta' in user_message or 'titan' in user_message or 'vision' in user_message:
            flow = {'service': 'Game Hack', 'platform': user_message.title(), 'validity': None, 'price': None, 'waiting_confirm': False}
            user_flow[sender_id] = flow
            await event.respond("✅ Week ₹800 / Month ₹1300 - Konsa plan chahiye bhai?")
            return

        if 'chatgpt' in user_message or 'openai' in user_message:
            flow = {'service': 'ChatGPT Premium', 'platform': 'ChatGPT', 'validity': '1 Year', 'price': 1000, 'waiting_confirm': False}
            user_flow[sender_id] = flow
            await event.respond("✅ ChatGPT Premium 1 Year ₹1000 - Confirm karo bhai (haa/ok)")
            return

        # Handle validity response
        if flow.get('platform') and not flow.get('validity'):
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
        await event.respond("❌ Error aa gaya bhai, try later.")
        print(f"Error: {e}")

telegram_client.start()
telegram_client.loop.create_task(keep_online())
telegram_client.loop.create_task(clear_messages())
telegram_client.run_until_disconnected()
