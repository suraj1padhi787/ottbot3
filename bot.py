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

user_context = {}
user_confirm_pending = {}
group_msg_to_user = {}

ai_active = True

async def send_typing(event):
    try:
        await event.client(functions.messages.SetTypingRequest(
            peer=event.chat_id,
            action=types.SendMessageTypingAction()
        ))
        await asyncio.sleep(random.uniform(1.0, 2.0))
    except Exception as e:
        print(f"Typing error: {e}")

async def keep_online():
    while True:
        try:
            await telegram_client(functions.account.UpdateStatusRequest(offline=False))
        except Exception as e:
            print(f"Online error: {e}")
        await asyncio.sleep(60)

async def clear_messages():
    while True:
        try:
            async for message in telegram_client.iter_messages(GROUP_ID, limit=100):
                try:
                    await telegram_client.delete_messages(GROUP_ID, message.id)
                except Exception as e:
                    print(f"Delete Error: {e}")
        except Exception as e:
            print(f"Fetch Error: {e}")

        await asyncio.sleep(3600)  # 1 hour

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
- Jab user OTT ka naam le to smartly plan suggest karo
- Jab adult site ya game ya combo ya chatgpt ka bole to uske hisab se suggest karo
- Jab 6 month bole politely 1 year recommend karo
- Jab confirm kare tabhi payment post karo
- Full funny, human style reply do
"""

confirm_words = ['haa', 'han', 'ha', 'krde', 'karde', 'kar de', 'done', 'paid', 'payment ho gaya', 'payment done', 'payment hogaya']

# OTT, Adult, Game, ChatGPT Keywords
ott_keywords = ['netflix', 'prime', 'hotstar', 'sony', 'zee5', 'voot', 'mxplayer', 'ullu', 'hoichoi']
adult_keywords = ['pornhub', 'onlyfans', 'adult']
game_keywords = ['titan', 'vision', 'lethal', 'gta', 'cod', 'bgmi', 'shoot360']
chatgpt_keywords = ['chatgpt', 'chat gpt', 'openai']
combo_keywords = ['combo', '4 ott']

@telegram_client.on(events.NewMessage(outgoing=False))
async def handler(event):
    global ai_active

    sender = await event.get_sender()
    sender_id = sender.id
    user_message = event.raw_text.strip().lower()

    if user_message == '/stopai':
        ai_active = False
        await event.respond("✅ AI reply system stopped.")
        return

    if user_message == '/startai':
        ai_active = True
        await event.respond("✅ AI reply system started.")
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
        # Detect Plans
        if any(word in user_message for word in ott_keywords):
            user_confirm_pending[sender_id] = {
                "service": "OTT Subscription",
                "platform": user_message,
                "price": "₹500",
                "validity": "1 Year"
            }
            await event.respond("✅ OTT Plan selected bhai! Confirm karo (haa/ok/krde).")
            return

        if any(word in user_message for word in adult_keywords):
            user_confirm_pending[sender_id] = {
                "service": "Adult Site Subscription",
                "platform": user_message,
                "price": "₹500",
                "validity": "1 Year"
            }
            await event.respond("✅ Adult Site Plan selected bhai! Confirm karo (haa/ok/krde).")
            return

        if any(word in user_message for word in game_keywords):
            user_confirm_pending[sender_id] = {
                "service": "Game Hack Subscription",
                "platform": user_message,
                "price": "₹1300",
                "validity": "1 Month"
            }
            await event.respond("✅ Game Hack Plan selected bhai! Confirm karo (haa/ok/krde).")
            return

        if any(word in user_message for word in chatgpt_keywords):
            user_confirm_pending[sender_id] = {
                "service": "ChatGPT Premium",
                "platform": "ChatGPT",
                "price": "₹1000",
                "validity": "1 Year"
            }
            await event.respond("✅ ChatGPT Plan selected bhai! Confirm karo (haa/ok/krde).")
            return

        if any(word in user_message for word in combo_keywords):
            user_confirm_pending[sender_id] = {
                "service": "Combo Offer",
                "platform": "Any 4 OTTs",
                "price": "₹1000",
                "validity": "1 Year"
            }
            await event.respond("✅ Combo Offer selected bhai! Confirm karo (haa/ok/krde).")
            return

        # Confirm Words Handle
        if any(word in user_message for word in confirm_words):
            if sender_id in user_confirm_pending:
                plan = user_confirm_pending[sender_id]
                service = plan['service']
                platform = plan['platform']
                payment_amount = plan['price']
                validity = plan['validity']

                user_link = f'<a href="tg://user?id={sender_id}">{sender.first_name}</a>'

                post_text = f"""
✅ New Payment Confirmation!

👤 User: {user_link}
🎯 Service: {service}
🏷️ Platform: {platform}
💰 Amount: {payment_amount}
⏳ Validity: {validity}
"""
                post = await telegram_client.send_message(
                    GROUP_ID,
                    post_text,
                    parse_mode='html'
                )

                group_msg_to_user[post.id] = sender_id
                del user_confirm_pending[sender_id]

                await event.respond("✅ Sahi decision bhai! QR generate ho raha hai 📲 Wait karo 😎")
                return
            else:
                await event.respond("✅ Bhai abhi koi plan select nahi kiya tune! Pehle plan select karo 😄")
                return

        # Screenshot Handle
        if event.photo or (event.document and "image" in event.file.mime_type):
            await telegram_client.send_message(
                GROUP_ID,
                f"✅ Payment Screenshot from {sender.first_name} ({sender_id})"
            )
            await telegram_client.forward_messages(
                GROUP_ID,
                event.message,
                event.chat_id
            )
            await event.respond("✅ Screenshot mil gaya bhai! Check ho raha hai.")
            return

        # Normal Chat Conversation
        messages_for_gpt = [{"role": "system", "content": system_prompt}] + user_context[sender_id]

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages_for_gpt,
            temperature=0.7
        )

        bot_reply = response.choices[0].message.content

        user_context[sender_id].append({"role": "assistant", "content": bot_reply})

        await event.respond(bot_reply)

    except Exception as e:
        await event.respond("Bhai thoda error aagaya 😔 Try later.")
        print(f"Error: {e}")

telegram_client.start()
telegram_client.loop.create_task(keep_online())
telegram_client.loop.create_task(clear_messages())
telegram_client.run_until_disconnected()
