import telebot
import re
import threading
import time
import json
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime
from p import check_card  # Make sure check_card(cc_line) is in p.py

# BOT Configuration
BOT_TOKEN = '7714897759:AAFIW9q-DAZlnXYYsFhkEjNO0Og1vIyXQ7s'   
ADMIN_ID = 1341028340  # Replace with your Telegram user ID (int)

bot = telebot.TeleBot(BOT_TOKEN)

AUTHORIZED_USERS = {"5618645828"}

# Dictionary to store last command time for each user for rate limiting
user_last_command_time = {}
RATE_LIMIT_SECONDS = 30 # Set your desired rate limit (e.g., 30 seconds)

# ---------------- Helper Functions ---------------- #

def load_auth():
    try:
        with open("authorized.json", "r") as f:
            return json.load(f)
    except:
        return {}

def save_auth(data):
    with open("authorized.json", "w") as f:
        json.dump(data, f)

def is_authorized(chat_id):
    if chat_id == ADMIN_ID:
        return True
    if str(chat_id) in AUTHORIZED_USERS:
        expiry = AUTHORIZED_USERS[str(chat_id)]
        if expiry == "forever":
            return True
        if time.time() < expiry:
            return True
        else:
            del AUTHORIZED_USERS[str(chat_id)]
            save_auth(AUTHORIZED_USERS)
    return False

def normalize_card(text):
    """
    Normalize credit card from any format to cc|mm|yy|cvv
    Similar to PHP normalize_card function
    """
    if not text:
        return None

    # Replace newlines and slashes with spaces
    text = text.replace('\n', ' ').replace('/', ' ')

    # Find all numbers in the text
    numbers = re.findall(r'\d+', text)

    cc = mm = yy = cvv = ''

    for part in numbers:
        if len(part) == 16:  # Credit card number
            cc = part
        elif len(part) == 4 and part.startswith('20'):  # 4-digit year starting with 20
            yy = part
        elif len(part) == 2 and int(part) <= 12 and mm == '':  # Month (2 digits <= 12)
            mm = part
        elif len(part) == 2 and not part.startswith('20') and yy == '':  # 2-digit year
            yy = '20' + part
        elif len(part) in [3, 4] and cvv == '':  # CVV (3-4 digits)
            cvv = part

    # Check if we have all required parts
    if cc and mm and yy and cvv:
        return f"{cc}|{mm}|{yy}|{cvv}"

    return None

AUTHORIZED_USERS = load_auth()

# ---------------- Bot Commands ---------------- #

@bot.message_handler(commands=['start'])
def start_handler(msg):
    bot.reply_to(msg, """✦━━━[ ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ᴄᴄ ᴄʜᴇᴄᴋᴇʀ ʙᴏᴛ ]━━━✦

⟡ ᴏɴʟʏ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ ᴍᴇᴍʙᴇʀꜱ ᴄᴀɴ ᴜꜱᴇ ᴛʜɪꜱ ʙᴏᴛ
⟡ ᴜꜱᴇ /b3 ᴛᴏ ᴄʜᴇᴄᴋ ꜱɪɴɢʟᴇ ᴄᴀʀᴅ
⟡ ꜰᴏʀ ᴍᴀꜱꜱ ᴄʜᴇᴄᴋ, ʀᴇᴘʟʏ ᴄᴄ ꜰɪʟᴇ ᴡɪᴛʜ /mb3

ʙᴏᴛ ᴘᴏᴡᴇʀᴇᴅ ʙʏ @godlegend""")

@bot.message_handler(commands=['auth'])
def authorize_user(msg):
    if msg.from_user.id != ADMIN_ID:
        return
    try:
        parts = msg.text.split()
        if len(parts) < 2:
            return bot.reply_to(msg, "❌ Usage: /auth <user_id> [days]")
        user = parts[1]
        days = int(parts[2]) if len(parts) > 2 else None

        if user.startswith('@'):
            return bot.reply_to(msg, "❌ Use numeric Telegram ID, not @username.")

        uid = int(user)
        expiry = "forever" if not days else time.time() + (days * 86400)
        AUTHORIZED_USERS[str(uid)] = expiry
        save_auth(AUTHORIZED_USERS)

        msg_text = f"✅ Authorized {uid} for {days} days." if days else f"✅ Authorized {uid} forever."
        bot.reply_to(msg, msg_text)
    except Exception as e:
        bot.reply_to(msg, f"❌ Error: {e}")

@bot.message_handler(commands=['rm'])
def remove_auth(msg):
    if msg.from_user.id != ADMIN_ID:
        return
    try:
        parts = msg.text.split()
        if len(parts) < 2:
            return bot.reply_to(msg, "❌ Usage: /rm <user_id>")
        uid = int(parts[1])
        if str(uid) in AUTHORIZED_USERS:
            del AUTHORIZED_USERS[str(uid)]
            save_auth(AUTHORIZED_USERS)
            bot.reply_to(msg, f"✅ Removed {uid} from authorized users.")
        else:
            bot.reply_to(msg, "❌ User is not authorized.")
    except Exception as e:
        bot.reply_to(msg, f"❌ Error: {e}")

@bot.message_handler(commands=['b3'])
def b3_handler(msg):
    if not is_authorized(msg.from_user.id):
        return bot.reply_to(msg, """✦━━━[  ᴀᴄᴄᴇꜱꜱ ᴅᴇɴɪᴇᴅ ]━━━✦

⟡ ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ ᴛᴏ ᴜꜱᴇ ᴛʜɪꜱ ʙᴏᴛ
⟡ ᴏɴʟʏ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ ᴍᴇᴍʙᴇʀꜱ ᴜꜱᴇ ᴛʜɪꜱ ʙᴏᴛ

✧ ᴘʟᴇᴀꜱᴇ ᴄᴏɴᴛᴀᴄᴛ ᴀᴅᴍɪɴ ꜰᴏʀ ᴀᴜᴛʜᴏʀɪᴢᴀᴛɪᴏɴ
✧ ᴀᴅᴍɪɴ: @godlegend""")

    user_id = msg.from_user.id
    current_time = time.time()

    if user_id in user_last_command_time:
        time_since_last_command = current_time - user_last_command_time[user_id]
        if time_since_last_command < RATE_LIMIT_SECONDS:
            remaining_time = int(RATE_LIMIT_SECONDS - time_since_last_command)
            return bot.reply_to(msg, f"Please wait for {remaining_time} seconds before sending another command to prevent spam.")
    
    user_last_command_time[user_id] = current_time # Update last command time

    cc = None

    # Check if user replied to a message
    if msg.reply_to_message:
        # Extract CC from replied message
        replied_text = msg.reply_to_message.text or ""
        cc = normalize_card(replied_text)

        if not cc:
            return bot.reply_to(msg, "✦━━━[ ɪɴᴠᴀʟɪᴅ ꜰᴏʀᴍᴀᴛ ]━━━✦\n\n"
"⟡ ᴄᴏᴜʟᴅɴ't ᴇxᴛʀᴀᴄᴛ ᴠᴀʟɪᴅ ᴄᴀʀᴅ ɪɴꜰᴏ ꜰʀᴏᴍ ʀᴇᴘʟɪᴇᴅ ᴍᴇꜱꜱᴀɢᴇ\n\n"
"ᴄᴏʀʀᴇᴄᴛ ꜰᴏʀᴍᴀᴛ\n\n"
"`/b3 4556737586899855|12|2026|123`\n\n"
"✧ ᴄᴏɴᴛᴀᴄᴛ ᴀᴅᴍɪɴ ɪꜰ ʏᴏᴜ ɴᴇᴇᴅ ʜᴇʟᴘ")
    else:
        # Check if CC is provided as argument
        args = msg.text.split(None, 1)
        if len(args) < 2:
            return bot.reply_to(msg, "✦━━━[ ɪɴᴠᴀʟɪᴅ ꜰᴏʀᴍᴀᴛ ]━━━✦\n\n"
"⟡ ᴘʟᴇᴀꜱᴇ ᴜꜱᴇ ᴛʜᴇ ᴄᴏʀʀᴇᴄᴛ ꜰᴏʀᴍᴀᴛ ᴛᴏ ᴄʜᴇᴄᴋ ᴄᴀʀᴅꜱ\n\n"
"ᴄᴏʀʀᴇᴄᴛ ꜰᴏʀᴍᴀᴛ\n\n"
"`/b3 4556737586899855|12|2026|123`\n\n"
"ᴏʀ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇꜱꜱᴀɢᴇ ᴄᴏɴᴛᴀɪɴɪɴɢ ᴄᴄ ᴡɪᴛʜ `/b3`\n\n"
"✧ ᴄᴏɴᴛᴀᴄᴛ ᴀᴅᴍɪɴ ɪꜰ ʏᴏᴜ ɴᴇᴇᴅ ʜᴇʟᴘ")

        # Try to normalize the provided CC
        raw_input = args[1]

        # Check if it's already in valid format
        if re.match(r'^\d{16}\|\d{2}\|\d{2,4}\|\d{3,4}$', raw_input):
            cc = raw_input
        else:
            # Try to normalize the card
            cc = normalize_card(raw_input)

            # If normalization failed, use the original input
            if not cc:
                cc = raw_input

    processing = bot.reply_to(msg, "✦━━━[  ᴘʀᴏᴄᴇꜱꜱɪɴɢ ]━━━✦\n\n"
"⟡ ʏᴏᴜʀ ᴄᴀʀᴅ ɪꜱ ʙᴇɪɴɢ ᴄʜᴇᴄᴋ...\n"
"⟡ ᴘʟᴇᴀꜱᴇ ᴡᴀɪᴛ ᴀ ꜰᴇᴡ ꜱᴇᴄᴏɴᴅꜱ\n\n"
"✧ ᴅᴏ ɴᴏᴛ ꜱᴘᴀᴍ ᴏʀ ʀᴇꜱᴜʙᴍɪᴛ ✧")
    
    bot.send_message(msg.chat.id, "Please wait for 30 seconds while your request is processed.")
    time.sleep(30)

    def check_and_reply():
        try:
            result = check_card(cc)  # This function must be in your p.py
            bot.edit_message_text(result, msg.chat.id, processing.message_id, parse_mode='HTML')
        except Exception as e:
            bot.edit_message_text(f"❌ Error: {str(e)}", msg.chat.id, processing.message_id)

    threading.Thread(target=check_and_reply).start()

@bot.message_handler(commands=['mb3'])
def mb3_handler(msg):
    if not is_authorized(msg.from_user.id):
        return bot.reply_to(msg, """✦━━━[  ᴀᴄᴄᴇꜱꜱ ᴅᴇɴɪᴇᴅ ]━━━✦

⟡ ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ ᴛᴏ ᴜꜱᴇ ᴛʜɪꜱ ʙᴏᴛ
⟡ ᴏɴʟʏ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ ᴍᴇᴍʙᴇʀꜱ ᴜꜱᴇ ᴛʜɪꜱ ʙᴏᴛ

✧ ᴘʟᴇᴀꜱᴇ ᴄᴏɴᴛᴀᴄᴛ ᴀᴅᴍɪɴ ꜰᴏʀ ᴀᴜᴛʜᴏʀɪᴢᴀᴛɪᴏɴ
✧ ᴀᴅᴍɪɴ: @godlegend""")

    user_id = msg.from_user.id
    current_time = time.time()

    if user_id in user_last_command_time:
        time_since_last_command = current_time - user_last_command_time[user_id]
        if time_since_last_command < RATE_LIMIT_SECONDS:
            remaining_time = int(RATE_LIMIT_SECONDS - time_since_last_command)
            return bot.reply_to(msg, f"Please wait for {remaining_time} seconds before sending another command to prevent spam.")
            
    user_last_command_time[user_id] = current_time # Update last command time

    if not msg.reply_to_message:
        return bot.reply_to(msg, "✦━━━[ ᴡʀᴏɴɢ ᴜꜱᴀɢᴇ ]━━━✦\n\n"
"⟡ ᴘʟᴇᴀꜱᴇ ʀᴇᴘʟʏ ᴛᴏ ᴀ `.txt` ꜰɪʟᴇ ᴏʀ ᴄʀᴇᴅɪᴛ ᴄᴀʀᴅ ᴛᴇxᴛ\n\n"
"✧ ᴏɴʟʏ ᴠᴀʟɪᴅ ᴄᴀʀᴅꜱ ᴡɪʟʟ ʙᴇ ᴄʜᴇᴄᴋᴇᴅ & ᴀᴘᴘʀᴏᴠᴇᴅ ᴄᴀʀᴅꜱ ꜱʜᴏᴡɴ ✧")

    reply = msg.reply_to_message

    # Detect whether it's file or raw text
    if reply.document:
        file_info = bot.get_file(reply.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        text = downloaded_file.decode('utf-8', errors='ignore')
    else:
        text = reply.text or ""
        if not text.strip():
            return bot.reply_to(msg, "❌ Empty text message.")

    # Extract CCs using improved normalization
    cc_lines = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        # Try to normalize each line
        normalized_cc = normalize_card(line)
        if normalized_cc:
            cc_lines.append(normalized_cc)
        else:
            # Fallback to original regex patterns
            found = re.findall(r'\b(?:\d[ -]*?){13,16}\b.*?\|.*?\|.*?\|.*', line)
            if found:
                cc_lines.extend(found)
            else:
                parts = re.findall(r'\d{12,16}[|: -]\d{1,2}[|: -]\d{2,4}[|: -]\d{3,4}', line)
                cc_lines.extend(parts)

    if not cc_lines:
        return bot.reply_to(msg, "✦━━━[ ⚠️ ɴᴏ ᴠᴀʟɪᴅ ᴄᴀʀᴅꜱ ꜰᴏᴜɴᴅ ]━━━✦\n\n"
"⟡ ɴᴏ ᴠᴀʟɪᴅ ᴄʀᴇᴅɪᴛ ᴄᴀʀᴅꜱ ᴅᴇᴛᴇᴄᴛᴇᴅ ɪɴ ᴛʜᴇ ꜰɪʟᴇ\n"
"⟡ ᴘʟᴇᴀꜱᴇ ᴍᴀᴋᴇ ꜱᴜʀᴇ ᴛʜᴇ ᴄᴀʀᴅꜱ ᴀʀᴇ ɪɴ ᴄᴏʀʀᴇᴄᴛ ꜰᴏʀᴍᴀᴛ\n\n"
"ᴄᴏʀʀᴇᴄᴛ ꜰᴏʀᴍᴀᴛ\n"
"`4556737586899855|12|2026|123`\n\n"
"✧ ᴄᴏɴᴛᴀᴄᴛ ᴀᴅᴍɪɴ ɪꜰ ʏᴏᴜ ɴᴇᴇᴅ ʜᴇʟᴘ")

    if not reply.document and len(cc_lines) > 15:
        return bot.reply_to(msg, "✦━━━[ ⚠️ ʟɪᴍɪᴛ ᴇxᴄᴇᴇᴅᴇᴅ ]━━━✦\n\n"
"⟡ ᴏɴʟʏ 15 ᴄᴀʀᴅꜱ ᴀʟʟᴏᴡᴇᴅ ɪɴ ʀᴀᴡ ᴘᴀꜱᴛᴇ\n"
"⟡ ꜰᴏʀ ᴍᴏʀᴇ ᴄᴀʀᴅꜱ, ᴘʟᴇᴀꜱᴇ ᴜᴘʟᴏᴀᴅ ᴀ `.txt` ꜰɪʟᴇ")

    total = len(cc_lines)
    user_id = msg.from_user.id

    # Initial Message with Inline Buttons
    kb = InlineKeyboardMarkup(row_width=1)
    buttons = [
        InlineKeyboardButton(f"ᴀᴘᴘʀᴏᴠᴇᴅ 0 ✅", callback_data="none"),
        InlineKeyboardButton(f"ᴅᴇᴄʟɪɴᴇᴅ 0 ❌", callback_data="none"),
        InlineKeyboardButton(f"ᴛᴏᴛᴀʟ ᴄʜᴇᴄᴋᴇᴅ 0", callback_data="none"),
        InlineKeyboardButton(f"ᴛᴏᴛᴀʟ {total} ✅", callback_data="none"),
    ]
    for btn in buttons:
        kb.add(btn)

    status_msg = bot.send_message(user_id, f"✦━━━[  ᴍᴀꜱꜱ ᴄʜᴇᴄᴋ ꜱᴛᴀʀᴛᴇᴅ ]━━━✦\n\n"
"⟡ ᴘʀᴏᴄᴇꜱꜱɪɴɢ ʏᴏᴜʀ ᴄᴀʀᴅꜱ...\n"
"⟡ ᴘʟᴇᴀꜱᴇ ᴡᴀɪᴛ ᴀ ꜰᴇᴡ ᴍᴏᴍᴇɴᴛꜱ\n\n"
" ʟɪᴠᴇ ꜱᴛᴀᴛᴜꜱ ᴡɪʟʟ ʙᴇ ᴜᴘᴅᴀᴛᴇᴅ ʙᴇʟᴏᴡ", reply_markup=kb)

    bot.send_message(user_id, "Please wait for 30 seconds while your mass check is processed.")
    time.sleep(30)

    approved, declined, checked = 0, 0, 0

    def process_all():
        nonlocal approved, declined, checked
        for cc in cc_lines:
            try:
                checked += 1
                result = check_card(cc.strip())
                if "[APPROVED]" in result:
                    approved += 1
                    bot.send_message(user_id, result, parse_mode='HTML')
                    if ADMIN_ID != user_id:
                        bot.send_message(ADMIN_ID, f"✅ Approved by {user_id}:\n{result}", parse_mode='HTML')
                else:
                    declined += 1

                # Update inline buttons
                new_kb = InlineKeyboardMarkup(row_width=1)
                new_kb.add(
                    InlineKeyboardButton(f"ᴀᴘᴘʀᴏᴠᴇᴅ {approved} 🔥", callback_data="none"),
                    InlineKeyboardButton(f"ᴅᴇᴄʟɪɴᴇᴅ {declined} ❌", callback_data="none"),
                    InlineKeyboardButton(f"ᴛᴏᴛᴀʟ ᴄʜᴇᴄᴋᴇᴅ {checked} ✔️", callback_data="none"),
                    InlineKeyboardButton(f"ᴛᴏᴛᴀʟ {total} ✅", callback_data="none"),
                )
                bot.edit_message_reply_markup(user_id, status_msg.message_id, reply_markup=new_kb)
                time.sleep(2)
            except Exception as e:
                bot.send_message(user_id, f"❌ Error: {e}")

        bot.send_message(user_id, "✦━━━[ ᴄʜᴇᴄᴋɪɴɢ ᴄᴏᴍᴘʟᴇᴛᴇᴅ ]━━━✦\n\n"
"⟡ ᴀʟʟ ᴄᴀʀᴅꜱ ʜᴀᴠᴇ ʙᴇᴇɴ ᴘʀᴏᴄᴇꜱꜱᴇᴅ\n"
"⟡ ᴛʜᴀɴᴋ ʏᴏᴜ ꜰᴏʀ ᴜꜱɪɴɢ ᴍᴀꜱꜱ ᴄʜᴇᴄᴋ\n\n"
" ᴏɴʟʏ ᴀᴘᴘʀᴏᴠᴇᴅ ᴄᴀʀᴅꜱ ᴡᴇʀᴇ ꜱʜᴏᴡɴ ᴛᴏ ʏᴏᴜ\n"
" ʏᴏᴜ ᴄᴀɴ ʀᴜɴ /mb3 ᴀɢᴀɪɴ ᴡɪᴛʜ ᴀ ɴᴇᴡ ʟɪꜱᴛ")

    threading.Thread(target=process_all).start()

# ---------------- Start Bot ---------------- #
bot.infinity_polling()