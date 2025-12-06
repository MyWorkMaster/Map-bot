import telebot
from telebot import types
import json
import os
import time
import requests

# Bot tokens
# Test Bot Token
# TEST_BOT_TOKEN = "8164339923:AAHw-wqosK75xbNs8_SRexwp3HTE4bRoq4w"
# Real Bot Token
REAL_BOT_TOKEN = "7837025186:AAH4SKBBwBsf9mc4XZVJ4sN_ksCSCKSrxSw"

# Using test token for now - change to REAL_BOT_TOKEN for production
BOT_TOKEN = REAL_BOT_TOKEN

# Map Website API Configuration
MAP_API_URL = os.getenv('MAP_API_URL', 'https://anomonus.com')  # Map website API URL

# Subscription Types and Prices (in Telegram Stars)
SUBSCRIPTION_TYPES = {
    'daily': {
        'name': '1 Day',
        'stars': 10,
        'duration_days': 1
    },
    '1month': {
        'name': '1 Month',
        'stars': 115,
        'duration_days': 30
    },
    '6month': {
        'name': '6 Months',
        'stars': 520,
        'duration_days': 180
    },
    '12month': {
        'name': '1 Year',
        'stars': 830,
        'duration_days': 365
    },
    'lifetime': {
        'name': 'Lifetime',
        'stars': 2500,
        'duration_days': 99999
    }
}

# Initialize bot
bot = telebot.TeleBot(BOT_TOKEN)

# Store user hashes (telegram_user_id -> hash mapping)
user_hashes = {}  # {telegram_user_id: hash}
HASHES_FILE = "data/user_hashes.json"

def load_user_hashes():
    """Load user hashes from file"""
    if os.path.exists(HASHES_FILE):
        try:
            with open(HASHES_FILE, 'r') as f:
                data = json.load(f)
                return data
        except:
            return {}
    return {}

def save_user_hashes():
    """Save user hashes to file"""
    try:
        with open(HASHES_FILE, 'w') as f:
            json.dump(user_hashes, f)
    except Exception as e:
        print(f"Error saving user hashes: {e}")

# Load user hashes on startup
user_hashes = load_user_hashes()

# ==================== MAP WEBSITE API INTEGRATION ====================

def check_subscription_from_map_api(telegram_user_id):
    """Check subscription status from map website API (real-time, source of truth)"""
    try:
        url = f"{MAP_API_URL}/api/subscription/telegram/{telegram_user_id}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            # Check if subscription is active (API is source of truth - respects admin deactivations)
            is_active = data.get('isActive', False)
            
            if not is_active:
                # Admin deactivated or not active
                return False
            
            # Check if it's a lifetime subscription (never expires)
            is_lifetime = data.get('isLifetime', False)
            if is_lifetime:
                # Lifetime subscriptions never expire (unless admin deactivates)
                return True
            
            # For non-lifetime subscriptions, check expiration
            expires_at = data.get('expiresAt')
            if expires_at:
                # Check if subscription hasn't expired
                current_time = int(time.time() * 1000)  # Convert to milliseconds
                if expires_at <= current_time:
                    # Subscription expired
                    return False
                return True
            else:
                # No expiration date but not lifetime - treat as active
                return True
        elif response.status_code == 404:
            # User not found in map website - not subscribed
            return False
        else:
            print(f"⚠️  Map API error checking subscription: {response.status_code}")
            return False
    except Exception as e:
        print(f"⚠️  Error checking subscription from map API: {e}")
        # Don't fallback to local storage - API is source of truth
        # If API is unavailable, assume not subscribed to be safe
        return False

def validate_hash_with_map_api(hash_code):
    """Validate hash with map website API - finds user by hash"""
    try:
        url = f"{MAP_API_URL}/api/users/by-hash/{hash_code}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return {
                'valid': True,
                'userId': data.get('userId'),
                'hash': data.get('hash'),
                'message': 'Hash validated successfully'
            }
        elif response.status_code == 404:
            return {
                'valid': False,
                'message': 'This hash is either incorrect or non-existing'
            }
        else:
            return {
                'valid': False,
                'message': 'Error validating hash. Please try again later.'
            }
    except Exception as e:
        print(f"⚠️  Error validating hash with map API: {e}")
        return {
            'valid': False,
            'message': 'Error connecting to server. Please try again later.'
        }

def link_telegram_user_to_website(telegram_user_id, telegram_username, userId, hash_code=None):
    """Link Telegram user to website user account"""
    try:
        import base64
        
        # Encode userId as base64url
        def base64url_encode(s):
            return base64.urlsafe_b64encode(s.encode()).decode().rstrip('=')
        
        start_param = base64url_encode(userId)
        
        url = f"{MAP_API_URL}/api/subscription/link-telegram"
        payload = {
            "startParam": start_param,
            "telegramUserId": telegram_user_id,
            "telegramUsername": telegram_username
        }
        # Include hash if available (optional, but helps with linking)
        if hash_code:
            payload["hash"] = hash_code
        
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Telegram user {telegram_user_id} linked to website user {userId}")
            return True
        else:
            print(f"⚠️  Failed to link Telegram user: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"⚠️  Error linking Telegram user: {e}")
        return False

def activate_subscription_in_map_api(telegram_user_id, hash_code=None, duration_days=30, subscription_type=None):
    """Activate subscription in map website API"""
    try:
        url = f"{MAP_API_URL}/api/subscription/activate"
        payload = {
            "telegramUserId": telegram_user_id,
            "durationDays": duration_days
        }
        # Include hash if available
        if hash_code:
            payload["hash"] = hash_code
        # Include subscription type if available
        if subscription_type:
            payload["subscriptionType"] = subscription_type
        
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Subscription activated in map website for user {telegram_user_id} ({subscription_type or duration_days} days)")
            return True
        elif response.status_code == 404:
            print(f"⚠️  User {telegram_user_id} not found in map website. User must start bot first.")
            return False
        else:
            print(f"⚠️  Map API error activating subscription: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"⚠️  Error activating subscription in map API: {e}")
        return False


@bot.message_handler(commands=['start'])
def handle_start(message):
    """Handle /start command with subscription_type and hash from URL parameter"""
    user_id = message.from_user.id
    
    # Parse start parameter from URL: format is {subscription_type}_{hash}
    # Example: /start 1month_5L07HJI149355S6RG0R99071
    command_args = message.text.split()[1:] if len(message.text.split()) > 1 else []
    
    if len(command_args) == 0:
        bot.send_message(
            message.chat.id,
            "❌ Invalid command format.\n\n"
            "Please use the link from the website to start the bot.\n\n"
            "Available subscription types:\n"
            "• 1month - 115 Stars\n"
            "• 6month - 520 Stars\n"
            "• 12month - 830 Stars\n"
            "• lifetime - 2500 Stars"
        )
        return
    
    # Parse the start parameter: format is {subscription_type}_{hash}
    start_param = command_args[0].strip()
    
    # Split by underscore - first part is subscription_type, rest is hash
    if '_' not in start_param:
        bot.send_message(
            message.chat.id,
            "❌ Invalid parameter format.\n\n"
            "Expected format: {subscription_type}_{hash}\n"
            "Example: 1month_5L07HJI149355S6RG0R99071"
        )
        return
    
    # Split by first underscore only (in case hash contains underscores)
    parts = start_param.split('_', 1)
    if len(parts) != 2:
        bot.send_message(
            message.chat.id,
            "❌ Invalid parameter format.\n\n"
            "Expected format: {subscription_type}_{hash}"
        )
        return
    
    subscription_type = parts[0].strip().lower()
    hash_code = parts[1].strip()
    
    # Validate subscription type
    if subscription_type not in SUBSCRIPTION_TYPES:
        bot.send_message(
            message.chat.id,
            f"❌ Invalid subscription type: {subscription_type}\n\n"
            "Available types: daily, 1month, 6month, 12month, lifetime"
        )
        return
    
    # Validate hash format (24 characters)
    if len(hash_code) != 24:
        bot.send_message(
            message.chat.id,
            "❌ Invalid hash format. Hash must be 24 characters."
        )
        return
    
    # Validate hash with map website API
    validation_result = validate_hash_with_map_api(hash_code)
    
    if not validation_result['valid']:
        bot.send_message(
            message.chat.id,
            f"❌ {validation_result['message']}"
        )
        return
    
    # Hash is valid, get subscription details
    subscription_info = SUBSCRIPTION_TYPES[subscription_type]
    userId = validation_result.get('userId')
    
    # Link Telegram user to website user
    telegram_username = message.from_user.username
    link_success = link_telegram_user_to_website(
        user_id,
        telegram_username,
        userId,
        hash_code=hash_code
    )
    
    if not link_success:
        bot.send_message(
            message.chat.id,
            "❌ Failed to link account. Please try again later."
        )
        return
    
    # Save hash for user
    user_hashes[str(user_id)] = hash_code
    save_user_hashes()
    
    # Create invoice payload: hash__subscription_type
    invoice_payload = f"{hash_code}__{subscription_type}"
    
    # Send invoice immediately
    try:
        bot.send_invoice(
            chat_id=message.chat.id,
            title=f"Anomonus Bot Subscription - {subscription_info['name']}",
            description=f"Subscribe to Anomonus Bot to access premium features on our map website",
            invoice_payload=invoice_payload,
            provider_token="",  # Empty for Telegram Stars payments
            currency="XTR",  # XTR is the currency code for Telegram Stars
            prices=[types.LabeledPrice(
                label=f"Subscription ({subscription_info['stars']} Stars)",
                amount=subscription_info['stars']
            )],
            start_parameter=f"subscription_{subscription_type}"
        )
        
        # Send "Buy Stars" button below the invoice
        keyboard = types.InlineKeyboardMarkup()
        buy_stars_button = types.InlineKeyboardButton(
            text="Buy Stars",
            url="https://t.me/anomonuschannel"
        )
        keyboard.add(buy_stars_button)
        bot.send_message(
            message.chat.id,
            "Need Telegram Stars?",
            reply_markup=keyboard
        )
    except Exception as e:
        bot.send_message(
            message.chat.id,
            f"❌ Error creating invoice: {str(e)}\nPlease try again later."
        )
        print(f"Error sending invoice: {e}")


@bot.message_handler(commands=['terms'])
def handle_terms(message):
    """Handle /terms command - show link to Terms of Use"""
    # Create inline keyboard with Terms button
    keyboard = types.InlineKeyboardMarkup()
    terms_button = types.InlineKeyboardButton(
        text="Terms",
        url="https://telegra.ph/Terms-of-Use-of-the-Anomonuscom-Service-11-18-2"
    )
    keyboard.add(terms_button)
    
    bot.send_message(
        message.chat.id,
        "📄 Terms of Use\n\nClick the button below to view our Terms of Use:",
        reply_markup=keyboard
    )


@bot.message_handler(commands=['paysupport'])
def handle_paysupport(message):
    """Handle /paysupport command - show payment support links"""
    # Create inline keyboard with two buttons
    keyboard = types.InlineKeyboardMarkup()
    paysupport_button = types.InlineKeyboardButton(
        text="Paysupport",
        url="https://telegra.ph/Payment--Subscription-Support-11-18"
    )
    support_button = types.InlineKeyboardButton(
        text="Support",
        url="https://support.anomonus.com"
    )
    keyboard.add(paysupport_button)
    keyboard.add(support_button)
    
    bot.send_message(
        message.chat.id,
        "💳 Payment & Subscription Support\n\nFor payment or subscription issues, please use the options below:",
        reply_markup=keyboard
    )


@bot.message_handler(func=lambda message: True)
def handle_other_messages(message):
    """Handle other messages - redirect to start command"""
    bot.send_message(
        message.chat.id,
        "👋 Welcome to Anomonus Bot!\n\n"
        "To subscribe, please use the link from the website.\n\n"
        "Available subscription types:\n"
        "• daily - 10 Stars\n"
        "• 1month - 115 Stars\n"
        "• 6month - 520 Stars\n"
        "• 12month - 830 Stars\n"
        "• lifetime - 2500 Stars"
    )


# Payment handlers for Telegram Stars
@bot.pre_checkout_query_handler(func=lambda query: True)
def checkout(pre_checkout_query):
    """Handle pre-checkout query - approve all payments"""
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


@bot.message_handler(content_types=['successful_payment'])
def handle_successful_payment(message):
    """Handle successful Telegram Stars payment"""
    user_id = message.from_user.id
    
    # Log payment details
    payment = message.successful_payment
    payment_amount = payment.total_amount
    invoice_payload = payment.invoice_payload
    
    print(f"💳 Payment received from user {user_id}: {payment_amount} {payment.currency}")
    print(f"   Invoice payload: {invoice_payload}")
    
    # Parse invoice payload: hash__subscription_type
    if '__' not in invoice_payload:
        bot.send_message(
            message.chat.id,
            "❌ Invalid payment payload. Please contact support."
        )
        return
    
    hash_code, subscription_type = invoice_payload.split('__', 1)
    
    # Validate subscription type
    if subscription_type not in SUBSCRIPTION_TYPES:
        bot.send_message(
            message.chat.id,
            f"❌ Invalid subscription type: {subscription_type}. Please contact support."
        )
        return
    
    # Get subscription info
    subscription_info = SUBSCRIPTION_TYPES[subscription_type]
    duration_days = subscription_info['duration_days']
    subscription_name = subscription_info['name']
    
    # Save hash for user (if not already saved)
    if str(user_id) not in user_hashes:
        user_hashes[str(user_id)] = hash_code
        save_user_hashes()
    
    # Activate subscription in map website API
    subscription_activated = activate_subscription_in_map_api(
        user_id, 
        hash_code=hash_code, 
        duration_days=duration_days,
        subscription_type=subscription_type
    )
    
    if subscription_activated:
        bot.send_message(
            message.chat.id,
            f"✅ Payment successful! You are now subscribed ({subscription_name}) and can access premium features on our map website."
        )
    else:
        bot.send_message(
            message.chat.id,
            f"✅ Payment successful! You are subscribed ({subscription_name}).\n\n⚠️ Note: If you have issues accessing premium features, please contact support."
        )




# ==================== RUN BOT ====================

def test_telegram_connection():
    """Test if we can reach Telegram API"""
    try:
        response = requests.get('https://api.telegram.org', timeout=5)
        return True
    except Exception as e:
        print(f"⚠️  Cannot reach Telegram API: {e}")
        print("   Please check your internet connection and firewall settings.")
        return False

def run_bot():
    """Run the Telegram bot"""
    # Test connection first
    if not test_telegram_connection():
        print("❌ Connection test failed. Retrying in 10 seconds...")
        time.sleep(10)
        run_bot()  # Retry
        return
    
    print("✅ Connection to Telegram API successful")
    print("Bot is running...")
    try:
        bot.infinity_polling(none_stop=True, interval=0, timeout=20)
    except Exception as e:
        print(f"❌ Bot connection error: {e}")
        print("Retrying in 5 seconds...")
        time.sleep(5)
        run_bot()  # Retry

if __name__ == "__main__":
    print("=" * 50)
    print("Anomonus Bot Started")
    print("=" * 50)
    print(f"Map Website API: {MAP_API_URL}")
    print("Integration:")
    print("  ✅ Connected to Map Website API")
    print("  ✅ Subscriptions sync with map website")
    print("  ✅ Payment activates subscription in map website")
    print("=" * 50)
    print("")
    
    # Run bot
    run_bot()

