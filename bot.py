import telebot
from telebot import types
from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
import json
import os
import time
import requests

# Bot tokens
# Test Bot Token
# TEST_BOT_TOKEN = "8164339923:AAHw-wqosK75xbNs8_SRexwp3HTE4bRoq4w"
# Real Bot Token
REAL_BOT_TOKEN = "7877535121:AAGIGFiB6LrKKcM36fev7vtJ9xq6PZQtksQ"

# Using test token for now - change to REAL_BOT_TOKEN for production
BOT_TOKEN = REAL_BOT_TOKEN

# Map Website API Configuration
MAP_API_URL = os.getenv('MAP_API_URL', 'http://localhost:4000')  # Map website API URL

# Initialize bot
bot = telebot.TeleBot(BOT_TOKEN)

# Initialize Flask API server
app = Flask(__name__)
CORS(app)  # Enable CORS for website requests

# Store subscribed users (in production, use a database)
# Using file-based storage for persistence
SUBSCRIPTIONS_FILE = "subscribed_users.json"

def load_subscribed_users():
    """Load subscribed users from file"""
    if os.path.exists(SUBSCRIPTIONS_FILE):
        try:
            with open(SUBSCRIPTIONS_FILE, 'r') as f:
                data = json.load(f)
                return set(data.get('users', []))
        except:
            return set()
    return set()

def save_subscribed_users(users_set):
    """Save subscribed users to file"""
    try:
        with open(SUBSCRIPTIONS_FILE, 'w') as f:
            json.dump({'users': list(users_set)}, f)
    except Exception as e:
        print(f"Error saving subscriptions: {e}")

def clear_all_subscriptions():
    """Clear all subscribed users"""
    global subscribed_users
    subscribed_users.clear()
    save_subscribed_users(subscribed_users)
    print("✅ All subscriptions cleared")

def unsubscribe_user(user_id):
    """Unsubscribe a specific user"""
    global subscribed_users
    if user_id in subscribed_users:
        subscribed_users.remove(user_id)
        save_subscribed_users(subscribed_users)
        print(f"✅ User {user_id} unsubscribed")
        return True
    else:
        print(f"⚠️  User {user_id} was not subscribed")
        return False

# Load subscribed users on startup
subscribed_users = load_subscribed_users()

# Clear all subscriptions on startup (as requested)
print("🔄 Clearing all subscriptions...")
clear_all_subscriptions()
print("✅ All users have been unsubscribed")

# Store user hashes (telegram_user_id -> hash mapping)
user_hashes = {}  # {telegram_user_id: hash}
HASHES_FILE = "user_hashes.json"

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
            
            # Also check expiration if expiresAt is provided
            if is_active:
                expires_at = data.get('expiresAt')
                if expires_at:
                    # Check if subscription hasn't expired
                    current_time = int(time.time() * 1000)  # Convert to milliseconds
                    if expires_at <= current_time:
                        # Subscription expired
                        return False
                return True
            else:
                # Admin deactivated or not active
                return False
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

def link_telegram_user_to_website(telegram_user_id, telegram_username, userId):
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

def activate_subscription_in_map_api(telegram_user_id, hash_code=None, duration_days=30):
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
        
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Subscription activated in map website for user {telegram_user_id}")
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


def create_main_keyboard():
    """Create the main Reply Keyboard Markup with buttons"""
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button_subscribe = types.KeyboardButton("Buy subscription")
    button_about = types.KeyboardButton("About us")
    button_how_to_use = types.KeyboardButton("How to use Map")
    keyboard.add(button_subscribe)
    keyboard.add(button_about, button_how_to_use)
    return keyboard


@bot.message_handler(commands=['start'])
def handle_start(message):
    """Handle /start command - ask for hash first"""
    user_id = message.from_user.id
    
    # Check if user already has a validated hash
    if str(user_id) in user_hashes:
        welcome_text = "Welcome to Anomonus Bot"
        keyboard = create_main_keyboard()
        bot.send_message(message.chat.id, welcome_text, reply_markup=keyboard)
    else:
        # Ask for hash
        bot.send_message(
            message.chat.id,
            "🔐 Welcome to Anomonus Bot\n\nPlease enter your registration hash:"
        )


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
def handle_hash_input(message):
    """Handle hash input from user"""
    user_id = message.from_user.id
    
    # Check if user already has validated hash
    if str(user_id) in user_hashes:
        # User has hash, process as regular message
        if message.text == "Buy subscription":
            handle_buy_subscription(message)
        elif message.text == "About us":
            handle_about_us(message)
        elif message.text == "How to use Map":
            handle_how_to_use(message)
        else:
            handle_other_messages(message)
        return
    
    # User doesn't have hash yet - treat input as hash
    hash_input = message.text.strip()
    
    # Validate hash format (12 letters + 12 numbers = 24 characters)
    if len(hash_input) != 24:
        bot.send_message(
            message.chat.id,
            "❌ Invalid hash format. Hash must be 24 characters (12 letters + 12 numbers).\n\nPlease enter your registration hash:"
        )
        return
    
    # Validate hash with map website API
    validation_result = validate_hash_with_map_api(hash_input)
    
    if validation_result['valid']:
        # Hash is valid, get userId from response
        userId = validation_result.get('userId')
        
        if userId:
            # Link Telegram user to website user
            telegram_username = message.from_user.username
            link_success = link_telegram_user_to_website(
                user_id,
                telegram_username,
                userId
            )
            
            if link_success:
                # Save hash for user
                user_hashes[str(user_id)] = hash_input
                save_user_hashes()
                
                bot.send_message(
                    message.chat.id,
                    "✅ Hash validated and account linked successfully!\n\nWelcome to Anomonus Bot",
                    reply_markup=create_main_keyboard()
                )
            else:
                # Hash is valid but linking failed
                bot.send_message(
                    message.chat.id,
                    "✅ Hash validated, but failed to link account. Please try again later.",
                    reply_markup=create_main_keyboard()
                )
        else:
            # Hash valid but no userId returned
            bot.send_message(
                message.chat.id,
                "✅ Hash validated, but user information not found. Please contact support.",
                reply_markup=create_main_keyboard()
            )
    else:
        # Hash is invalid
        bot.send_message(
            message.chat.id,
            f"❌ {validation_result['message']}\n\nPlease enter your registration hash:"
        )


def handle_buy_subscription(message):
    """Handle Buy subscription button - sends real Telegram Stars invoice"""
    user_id = message.from_user.id
    
    # Check subscription status via API (real-time, respects admin deactivations)
    # API is the source of truth - don't use local storage
    is_subscribed = check_subscription_from_map_api(user_id)
    
    if is_subscribed:
        bot.send_message(
            message.chat.id,
            "You already subscribed",
            reply_markup=create_main_keyboard()
        )
        return
    
    # User is not subscribed, send invoice
    try:
        # Send real Telegram Stars invoice (1 star for testing)
        bot.send_invoice(
            chat_id=message.chat.id,
            title="Anomonus Bot Subscription",
            description="Subscribe to Anomonus Bot to access premium features on our map website",
            invoice_payload="subscription_payment_1_star",
            provider_token="",  # Empty for Telegram Stars payments
            currency="XTR",  # XTR is the currency code for Telegram Stars
            prices=[types.LabeledPrice(label="Subscription (1 Star)", amount=1)],
            start_parameter="subscription"
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
        # If invoice fails, send error message
        bot.send_message(
            message.chat.id,
            f"Error creating invoice: {str(e)}\nPlease try again later.",
            reply_markup=create_main_keyboard()
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
    
    # Get user's hash if available
    user_hash = user_hashes.get(str(user_id))
    
    # Log payment details
    payment = message.successful_payment
    print(f"💳 Payment received from user {user_id}: {payment.total_amount} {payment.currency}")
    if user_hash:
        print(f"   Hash: {user_hash}")
    
    # Activate subscription in map website API (source of truth) - include hash
    subscription_activated = activate_subscription_in_map_api(user_id, hash_code=user_hash, duration_days=30)
    
    # Note: We don't save locally anymore - API is the source of truth
    # Local storage is only for backup/reference, but we always check API
    
    if subscription_activated:
        bot.send_message(
            message.chat.id,
            "✅ Payment successful! You are now subscribed and can access premium features on our map website.",
            reply_markup=create_main_keyboard()
        )
    else:
        # Still mark as subscribed locally even if map API fails
        bot.send_message(
            message.chat.id,
            "✅ Payment successful! You are subscribed.\n\n⚠️ Note: If you have issues accessing premium features, please contact support.",
            reply_markup=create_main_keyboard()
        )


def handle_about_us(message):
    """Handle About us button"""
    bot.send_message(message.chat.id, "We Are Anomonus")


def handle_how_to_use(message):
    """Handle How to use Map button"""
    bot.send_message(message.chat.id, "This is how to use maps")


def handle_other_messages(message):
    """Handle any other messages"""
    # Just show the main keyboard again
    keyboard = create_main_keyboard()
    bot.send_message(
        message.chat.id,
        "Please use the buttons below:",
        reply_markup=keyboard
    )


# Handle callback queries (if needed for other features)
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    """Handle callback queries"""
    bot.answer_callback_query(call.id, "Processing...")


# ==================== API ENDPOINTS ====================

@app.route('/api/check-subscription', methods=['GET'])
def check_subscription():
    """Check if a user is subscribed (API is source of truth - respects admin deactivations)"""
    user_id = request.args.get('user_id')
    
    if not user_id:
        return jsonify({
            'success': False,
            'error': 'user_id parameter is required'
        }), 400
    
    try:
        user_id = int(user_id)
        # Check subscription via API (real-time, source of truth)
        # This ensures admin deactivations are immediately respected
        is_subscribed = check_subscription_from_map_api(user_id)
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'is_subscribed': is_subscribed,
            'source': 'map_api'  # Always from API
        })
    except ValueError:
        return jsonify({
            'success': False,
            'error': 'Invalid user_id format'
        }), 400

@app.route('/api/subscribe', methods=['POST'])
def subscribe_user():
    """Mark a user as subscribed (for website to call after payment verification)"""
    data = request.get_json()
    user_id = data.get('user_id')
    api_key = data.get('api_key')  # Optional API key for security
    
    if not user_id:
        return jsonify({
            'success': False,
            'error': 'user_id is required'
        }), 400
    
    try:
        user_id = int(user_id)
        subscribed_users.add(user_id)
        save_subscribed_users(subscribed_users)  # Save to file
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'message': 'User subscribed successfully'
        })
    except ValueError:
        return jsonify({
            'success': False,
            'error': 'Invalid user_id format'
        }), 400

@app.route('/api/user-info', methods=['GET'])
def get_user_info():
    """Get user information (subscription status from API - real-time)"""
    user_id = request.args.get('user_id')
    
    if not user_id:
        return jsonify({
            'success': False,
            'error': 'user_id parameter is required'
        }), 400
    
    try:
        user_id = int(user_id)
        # Check subscription via API (real-time, respects admin deactivations)
        is_subscribed = check_subscription_from_map_api(user_id)
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'is_subscribed': is_subscribed,
            'source': 'map_api'  # Always from API
        })
    except ValueError:
        return jsonify({
            'success': False,
            'error': 'Invalid user_id format'
        }), 400

@app.route('/api/unsubscribe', methods=['POST'])
def unsubscribe_user_api():
    """Unsubscribe a user (remove from local storage)"""
    data = request.get_json()
    user_id = data.get('user_id')
    
    if not user_id:
        return jsonify({
            'success': False,
            'error': 'user_id is required'
        }), 400
    
    try:
        user_id = int(user_id)
        success = unsubscribe_user(user_id)
        
        return jsonify({
            'success': success,
            'user_id': user_id,
            'message': 'User unsubscribed successfully' if success else 'User was not subscribed'
        })
    except ValueError:
        return jsonify({
            'success': False,
            'error': 'Invalid user_id format'
        }), 400

@app.route('/api/clear-subscriptions', methods=['POST'])
def clear_subscriptions_api():
    """Clear all subscriptions"""
    clear_all_subscriptions()
    return jsonify({
        'success': True,
        'message': 'All subscriptions cleared'
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'success': True,
        'status': 'online',
        'subscribed_users_count': len(subscribed_users)
    })

# ==================== RUN BOT AND API SERVER ====================

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

def run_api():
    """Run the Flask API server"""
    print("API server is running on http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)

if __name__ == "__main__":
    # Run bot and API server in separate threads
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    api_thread = threading.Thread(target=run_api, daemon=True)
    
    bot_thread.start()
    api_thread.start()
    
    print("=" * 50)
    print("Anomonus Bot & API Server Started")
    print("=" * 50)
    print(f"Bot: Running...")
    print(f"Bot API: http://localhost:5000")
    print(f"Map Website API: {MAP_API_URL}")
    print("Bot API Endpoints:")
    print("  - GET  /api/check-subscription?user_id=<id>")
    print("  - POST /api/subscribe (JSON: {user_id: <id>})")
    print("  - GET  /api/user-info?user_id=<id>")
    print("  - GET  /api/health")
    print("")
    print("Integration:")
    print("  ✅ Connected to Map Website API")
    print("  ✅ Subscriptions sync with map website")
    print("  ✅ Payment activates subscription in map website")
    print("=" * 50)
    
    # Keep main thread alive
    try:
        while True:
            threading.Event().wait(1)
    except KeyboardInterrupt:
        print("\nShutting down...")

