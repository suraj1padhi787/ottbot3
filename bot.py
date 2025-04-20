import asyncio
import random
import os
import openai
from telethon import TelegramClient, events, functions, types

# Railway Variables
api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
openai_api_key = os.getenv("OPENAI_API_KEY")
session_name = 'newuserbot'

client = openai.OpenAI(api_key=openai_api_key)
telegram_client = TelegramClient(session_name, api_id, api_hash)

GROUP_ID = -1002470019043

# Full Original System Prompt with Rules
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

Rules:
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
- 

Rules:
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

📜 Rules:
- Pehle platform pucho user se (e.g. Netflix, Pornhub, Titan)
- Phir validity pucho (6 months / 1 year / week / month)
- Fir price set karo
- Jab user confirm kare (haa/ok/done) tab group me post karo
- Dosti bhare style me friendly human reply do
- Gali dene wale user ko 3 warning ke baad mute karo
- ChatGPT style ke short aur funny replies do
- Typing animation har reply se pehle
- Always online dikhna
- 1 hour me group messages auto clear karna
"""

user_context = {}
user_flow = {}

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

confirm_words = ['haa', 'han', 'ha', 'krde', 'karde', 'kar de', 'ok', 'confirm', 'done', 'ho gaya']

categories = {
    'ott': ['netflix', 'prime', 'hotstar', 'sony', 'zee5', 'voot', 'ullu', 'hoichoi', 'mxplayer'],
    'adult': ['pornhub', 'onlyfans', 'manyvids', 'fansly', 'brazzers'],
    'game': ['titan', 'vision', 'lethal', 'gta', 'cod', 'shoot360', 'bgmi'],
    'chatgpt': ['chatgpt', 'openai', 'chat gpt']
}

prices = {
    'ott': {'6 months': 350, '1 year': 500},
    'adult': {'6 months': 300, '1 year': 500},
    'game': {'week': 800, 'month': 1300},
    'chatgpt': {'1 year': 1000}
}

@telegram_client.on(events.NewMessage(outgoing=False))
async def handler(event):
    global ai_active

    sender = await event.get_sender()
    sender_id = sender.id
    user_message = event.raw_text.strip().lower()

    if user_message == '/stopai':
        ai_active = False
        await event.respond("✅ AI system stopped.")
        return

    if user_message == '/startai':
        ai_active = True
        await event.respond("✅ AI system restarted.")
        return

    if not ai_active:
        return

    await send_typing(event)

    if sender_id not in user_context:
        user_context[sender_id] = []

    user_context[sender_id].append({"role": "user", "content": user_message})
    if len(user_context[sender_id]) > 10:
        user_context[sender_id] = user_context[sender_id][-10:]

    try:
        flow = user_flow.get(sender_id, {})

        # Step 1: Detect service category
        if 'service' not in flow:
            for category, keywords in categories.items():
                if any(word in user_message for word in keywords) or category in user_message:
                    flow['service'] = category
                    user_flow[sender_id] = flow
                    await event.respond(f"✅ Konsa {category.upper()} platform chahiye bhai? (example: {', '.join(keywords[:3])})")
                    return

        # Step 2: Platform selection
        if flow.get('service') and 'platform' not in flow:
            flow['platform'] = user_message.title()
            user_flow[sender_id] = flow

            if flow['service'] == 'game':
                await event.respond("✅ Validity choose karo bhai: Week ₹800 / Month ₹1300")
            elif flow['service'] == 'chatgpt':
                flow['validity'] = '1 year'
                flow['price'] = prices['chatgpt']['1 year']
                user_flow[sender_id] = flow
                await event.respond(f"✅ Confirm karo bhai (haa/ok) for ChatGPT Premium 1 Year ₹{flow['price']}")
            else:
                await event.respond("✅ Validity choose karo bhai: 6 Months / 1 Year")
            return

        # Step 3: Validity selection
        if flow.get('platform') and 'validity' not in flow:
            validity = user_message.lower()

            if flow['service'] == 'game':
                if validity in ['week', 'month']:
                    flow['validity'] = validity
                    flow['price'] = prices['game'][validity]
                    user_flow[sender_id] = flow
                    await event.respond(f"✅ Confirm karo bhai (haa/ok) for {flow['platform']} {validity} plan ₹{flow['price']}")
                else:
                    await event.respond("❌ Galat validity! Week ya Month likho bhai.")
            else:
                if validity in ['6 months', '1 year']:
                    flow['validity'] = validity
                    flow['price'] = prices[flow['service']][validity]
                    user_flow[sender_id] = flow
                    await event.respond(f"✅ Confirm karo bhai (haa/ok) for {flow['platform']} {validity} plan ₹{flow['price']}")
                else:
                    await event.respond("❌ Galat validity! 6 Months ya 1 Year likho bhai.")
            return

        # Step 4: Final Confirmation
        if any(word in user_message for word in confirm_words):
            if flow.get('platform') and flow.get('validity'):
                user_link = f'<a href="tg://user?id={sender_id}">{sender.first_name}</a>'

                post_text = f"""
✅ New Payment Confirmation!

👤 User: {user_link}
🎯 Service: {flow['service'].title()}
🏷️ Platform: {flow['platform']}
💰 Amount: ₹{flow['price']}
⏳ Validity: {flow['validity'].title()}
"""

                await telegram_client.send_message(
                    GROUP_ID,
                    post_text,
                    parse_mode='html'
                )

                await event.respond("✅ Sahi decision bhai! QR generate ho raha hai 📲 Wait karo 😎")
                user_flow.pop(sender_id, None)
                return
            else:
                await event.respond("❌ Pehle plan aur validity complete karo bhai.")
                return

        # Default AI ChatGPT GPT-4o Reply
        messages_for_gpt = [{"role": "system", "content": system_prompt}] + user_context[sender_id]

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages_for_gpt,
            temperature=0.6
        )

        bot_reply = response.choices[0].message.content
        user_context[sender_id].append({"role": "assistant", "content": bot_reply})

        await event.respond(bot_reply)

    except Exception as e:
        await event.respond("Error aaya bhai 😔 Try later.")
        print(f"Error: {e}")

telegram_client.start()
telegram_client.loop.create_task(keep_online())
telegram_client.loop.create_task(clear_messages())
telegram_client.run_until_disconnected()
