import asyncio
import random
import os
from telethon import TelegramClient, events, functions, types
import openai

# Railway Environment Variables
api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
openai_api_key = os.getenv("OPENAI_API_KEY")
session_name = 'newuserbot'

client = openai.OpenAI(api_key=openai_api_key)
telegram_client = TelegramClient(session_name, api_id, api_hash)

GROUP_ID = -1002470019043

# Full System Prompt
system_prompt = """
Tum ek professional aur blunt OTT, Game aur Adult subscription seller ho.

Services:
- OTT: Netflix, Prime Video, Hotstar, SonyLIV, Zee5, YouTube Premium, Telegram Premium etc.
- Adult Sites: (list on request) 6M ₹300 / 1Y ₹500
- PC BGMI Hacks: Titan, Falcone, Vision, Lethal, Sharpshooter
- iOS Hacks: Shoot360, WinIOS, iOSZero
- ChatGPT Premium 1 Year ₹1000

Pricing:
- OTT 1 Year ₹500 (Own Email)
- OTT 6 Months ₹350 (Random Email)
- Combo 4 OTTs 1 Year ₹1000
- Hack Week ₹800 / Month ₹1300
- ChatGPT Premium 1 Year ₹1000

Rules:
- Dosti bhare human funny style me reply do.
- Jab user OTT ka bole tab plan suggest karo with Smart Comparison (Official vs Our price).
- Jab combo bole to 4 OTT selection karwao ek-ek karke.
- Jab Adult Site bole to naam pucho, validity pucho.
- Jab Game bole to naam aur week/month pucho.
- Validity 6 Months/1 Year/Week/Month smartly offer karo.
- Confirm ('haa', 'ok', 'done') karne par group me post karo.
- Agar user price me force kare to smartly ₹50 discount suggest karo.
- Galat language me spam mat karo, normal friendly AI reply do.
- Gali dene wale ko 3 warning baad mute karo.
- Multilanguage respect jab tak user bole.
- Owner /stopai aur /startai kar sakta hai.
- Har response typing animation ke sath do.
- Auto clear group messages 1 hr ke baad.
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

confirm_words = ['haa', 'han', 'ha', 'krde', 'karde', 'kar de', 'ok', 'confirm', 'done', 'ho gaya']

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

        # Combo 4 OTT handling
        if flow.get('combo_selecting'):
            selected = flow.get('combo_selected', [])
            if user_message not in selected:
                selected.append(user_message.title())
            flow['combo_selected'] = selected
            user_flow[sender_id] = flow

            if len(selected) >= 4:
                await event.respond(f"✅ Selected OTTs: {', '.join(selected)}\nConfirm karo bhai (haa/ok)")
                flow['waiting_confirm'] = True
            else:
                await event.respond(f"✅ {len(selected)}/4 OTTs select ho gaye. Aur OTT batao bhai.")
            return

        # Final confirmation for combo
        if flow.get('waiting_confirm') and any(word in user_message for word in confirm_words):
            user_link = f'<a href="tg://user?id={sender_id}">{sender.first_name}</a>'
            otts = ', '.join(flow['combo_selected'])
            post_text = f"""
✅ New Payment Confirmation!

👤 User: {user_link}
🎯 Service: OTT Combo 4 Plan
🏷️ Platforms: {otts}
💰 Amount: ₹1000
⏳ Validity: 1 Year
"""
            await telegram_client.send_message(GROUP_ID, post_text, parse_mode='html')
            await event.respond("✅ Sahi decision bhai! QR generate ho raha hai 📲 Wait karo 😎")
            user_flow.pop(sender_id, None)
            return

        # AI Based Flow
        messages_for_gpt = [{"role": "system", "content": system_prompt}] + user_context[sender_id]

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages_for_gpt,
            temperature=0.5
        )

        bot_reply = response.choices[0].message.content
        user_context[sender_id].append({"role": "assistant", "content": bot_reply})

        # Combo Detection
        if "combo" in user_message and "ott" in user_message:
            user_flow[sender_id] = {'combo_selecting': True, 'combo_selected': []}
            await event.respond("✅ Bhai 4 OTT select karo ek-ek karke. Example: Netflix, Prime Video, Hotstar, Zee5")
            return

        await event.respond(bot_reply)

    except Exception as e:
        await event.respond("❌ Bhai error aagaya. Try later.")
        print(f"Error: {e}")

telegram_client.start()
telegram_client.loop.create_task(keep_online())
telegram_client.loop.create_task(clear_messages())
telegram_client.run_until_disconnected()
