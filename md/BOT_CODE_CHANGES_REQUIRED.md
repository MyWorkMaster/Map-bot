# Bot Code Changes Required

## Overview

Your bot needs to be updated to work with the hash-based registration system. Here are the exact changes you need to make:

---

## 1. Handle `/start` Command with Hash

### Current Flow (if exists):
- User sends `/start`
- Bot asks for hash or processes payment

### New Required Flow:
- User sends `/start <hash>` (e.g., `/start ABC123XYZ456DEF789GHI012`)
- Bot validates hash via API
- Bot links Telegram account to website user

### Code Changes Needed:

```python
# Example in Python (python-telegram-bot)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command with hash"""
    chat_id = update.effective_chat.id
    telegram_user_id = update.effective_user.id
    telegram_username = update.effective_user.username
    
    # Check if hash provided
    if not context.args or len(context.args) == 0:
        await update.message.reply_text(
            "👋 Welcome!\n\n"
            "To subscribe, please enter your hash code:\n"
            "/start YOUR_HASH_CODE\n\n"
            "You can find your hash on the website when clicking 'AI Route' button."
        )
        return
    
    hash_code = context.args[0].strip()
    
    # Step 1: Validate hash
    try:
        response = requests.get(
            f"{API_BASE}/api/subscription/validate-hash/{hash_code}"
        )
        
        if response.status_code == 404:
            await update.message.reply_text(
                "❌ Hash not found. Please check your hash code and try again.\n\n"
                "Make sure you copied the complete 24-character hash from the website."
            )
            return
        
        if response.status_code == 400:
            await update.message.reply_text(
                "❌ Invalid hash format. Hash must be exactly 24 characters.\n\n"
                "Please check your hash and try again."
            )
            return
        
        if response.status_code != 200:
            await update.message.reply_text(
                "❌ Error validating hash. Please try again later."
            )
            return
        
        data = response.json()
        if not data.get("valid"):
            await update.message.reply_text(
                "❌ Hash validation failed. Please check your hash."
            )
            return
        
        userId = data["userId"]
        
        # Step 2: Link Telegram account
        link_response = requests.post(
            f"{API_BASE}/api/subscription/link-telegram",
            json={
                "hash": hash_code,  # Use hash instead of startParam
                "telegramUserId": telegram_user_id,
                "telegramUsername": telegram_username
            }
        )
        
        if link_response.status_code == 200:
            # Store hash in bot's user data for later use
            context.user_data["hash"] = hash_code
            context.user_data["userId"] = userId
            
            await update.message.reply_text(
                "✅ Account linked successfully!\n\n"
                "💰 To activate your subscription, please make a payment.\n\n"
                "Your hash has been saved. You can now proceed with payment."
            )
        else:
            await update.message.reply_text(
                "❌ Failed to link account. Please try again."
            )
            
    except Exception as e:
        await update.message.reply_text(
            f"❌ Error: {str(e)}\n\nPlease try again later."
        )
```

**Key Changes:**
- Extract hash from `/start <hash>` command
- Call `GET /api/subscription/validate-hash/:hash` to validate
- Call `POST /api/subscription/link-telegram` with `hash` field (not `startParam`)
- Store hash in bot's user data for later use

---

## 2. Update Payment Processing

### Current Flow (if exists):
- User pays
- Bot activates subscription using only `telegramUserId`

### New Required Flow:
- User pays
- Bot activates subscription using `telegramUserId` AND `hash` (if available)

### Code Changes Needed:

```python
async def process_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process payment and activate subscription"""
    telegram_user_id = update.effective_user.id
    hash_code = context.user_data.get("hash")  # Get stored hash
    
    # TODO: Verify payment via Telegram Stars API here
    # payment_verified = await verify_telegram_stars_payment(...)
    # if not payment_verified:
    #     return
    
    try:
        # Prepare request body
        request_body = {
            "telegramUserId": telegram_user_id,
            "durationDays": 30  # or based on payment tier
        }
        
        # Include hash if available
        if hash_code:
            request_body["hash"] = hash_code
        
        # Activate subscription
        response = requests.post(
            f"{API_BASE}/api/subscription/activate",
            json=request_body
        )
        
        if response.status_code == 200:
            data = response.json()
            expires_at = datetime.fromtimestamp(data["expiresAt"] / 1000)
            
            await update.message.reply_text(
                f"🎉 Subscription activated successfully!\n\n"
                f"✅ Active until: {expires_at.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                f"You now have access to AI Route feature on the website."
            )
        elif response.status_code == 404:
            await update.message.reply_text(
                "❌ User account not found. Please start the bot again with your hash:\n"
                "/start YOUR_HASH_CODE"
            )
        else:
            await update.message.reply_text(
                "❌ Failed to activate subscription. Please contact support."
            )
            
    except Exception as e:
        await update.message.reply_text(
            f"❌ Error: {str(e)}\n\nPlease try again later."
        )
```

**Key Changes:**
- Get stored hash from user data
- Include `hash` field in activation request (if available)
- Handle case where hash is not available (fallback to telegramUserId only)

---

## 3. Update Subscription Status Checks

### Current Flow (if exists):
- Bot checks subscription before allowing premium features
- Uses cached status or checks via API

### New Required Flow:
- Bot checks subscription status via API (real-time)
- Respects admin deactivations immediately

### Code Changes Needed:

```python
async def check_subscription_status(telegram_user_id: int) -> bool:
    """Check if user has active subscription"""
    try:
        response = requests.get(
            f"{API_BASE}/api/subscription/telegram/{telegram_user_id}"
        )
        
        if response.status_code == 404:
            return False
        
        if response.status_code == 200:
            data = response.json()
            return data.get("isActive", False)
        
        return False
        
    except Exception as e:
        print(f"Error checking subscription: {e}")
        return False

# Use before allowing premium features
async def handle_premium_feature(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Example: Handle premium feature request"""
    telegram_user_id = update.effective_user.id
    
    # Check subscription status (real-time)
    is_subscribed = await check_subscription_status(telegram_user_id)
    
    if not is_subscribed:
        await update.message.reply_text(
            "❌ This feature requires an active subscription.\n\n"
            "Please subscribe to access premium features."
        )
        return
    
    # User has active subscription, proceed with feature
    await update.message.reply_text("✅ Access granted!")
    # ... your premium feature code here
```

**Key Changes:**
- Always check subscription status via API (don't cache)
- Use `GET /api/subscription/telegram/:telegramUserId` endpoint
- Check `isActive` field in response
- This ensures admin deactivations are immediately respected

---

## 4. Handle Hash Re-entry (Optional but Recommended)

If user loses their hash or wants to change it:

```python
async def set_hash_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Allow user to set/update their hash"""
    if not context.args or len(context.args) == 0:
        await update.message.reply_text(
            "Please provide your hash:\n"
            "/sethash YOUR_HASH_CODE"
        )
        return
    
    hash_code = context.args[0].strip()
    
    # Validate hash
    response = requests.get(
        f"{API_BASE}/api/subscription/validate-hash/{hash_code}"
    )
    
    if response.status_code == 200:
        data = response.json()
        context.user_data["hash"] = hash_code
        context.user_data["userId"] = data["userId"]
        
        await update.message.reply_text("✅ Hash updated successfully!")
    else:
        await update.message.reply_text("❌ Invalid hash. Please check and try again.")
```

---

## Summary of Required Changes

### 1. **`/start` Command Handler**
   - ✅ Extract hash from command arguments
   - ✅ Call `GET /api/subscription/validate-hash/:hash`
   - ✅ Call `POST /api/subscription/link-telegram` with `hash` field
   - ✅ Store hash in bot's user data

### 2. **Payment Processing**
   - ✅ Get stored hash from user data
   - ✅ Include `hash` in `POST /api/subscription/activate` request
   - ✅ Handle both cases: with hash and without hash (fallback)

### 3. **Subscription Status Checks**
   - ✅ Use `GET /api/subscription/telegram/:telegramUserId` for real-time checks
   - ✅ Check `isActive` field (not cached status)
   - ✅ This ensures admin deactivations work immediately

### 4. **Error Handling**
   - ✅ Handle 404 (hash not found)
   - ✅ Handle 400 (invalid hash format)
   - ✅ Handle network errors

---

## API Base URL

Make sure your bot has the correct API base URL:

```python
# Development
API_BASE = "http://localhost:4000"

# Production
API_BASE = "https://your-domain.com"
```

---

## Testing Checklist

- [ ] Test `/start <hash>` with valid hash
- [ ] Test `/start <hash>` with invalid hash
- [ ] Test `/start <hash>` with wrong format
- [ ] Test payment activation with hash
- [ ] Test subscription status check
- [ ] Test admin deactivation (verify bot sees `isActive: false`)

---

## Example Complete Bot Handler (Python)

```python
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import requests

API_BASE = "http://localhost:4000"  # Change to production URL

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command with hash"""
    chat_id = update.effective_chat.id
    telegram_user_id = update.effective_user.id
    telegram_username = update.effective_user.username
    
    if not context.args or len(context.args) == 0:
        await update.message.reply_text(
            "👋 Welcome!\n\n"
            "To subscribe, enter your hash:\n"
            "/start YOUR_HASH_CODE"
        )
        return
    
    hash_code = context.args[0].strip()
    
    # Validate hash
    try:
        response = requests.get(f"{API_BASE}/api/subscription/validate-hash/{hash_code}")
        
        if response.status_code != 200:
            await update.message.reply_text("❌ Invalid hash. Please check and try again.")
            return
        
        data = response.json()
        if not data.get("valid"):
            await update.message.reply_text("❌ Hash validation failed.")
            return
        
        userId = data["userId"]
        
        # Link account
        link_response = requests.post(
            f"{API_BASE}/api/subscription/link-telegram",
            json={
                "hash": hash_code,
                "telegramUserId": telegram_user_id,
                "telegramUsername": telegram_username
            }
        )
        
        if link_response.status_code == 200:
            context.user_data["hash"] = hash_code
            context.user_data["userId"] = userId
            await update.message.reply_text("✅ Account linked! Proceed with payment.")
        else:
            await update.message.reply_text("❌ Failed to link account.")
            
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

async def activate_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Activate subscription after payment"""
    telegram_user_id = update.effective_user.id
    hash_code = context.user_data.get("hash")
    
    # TODO: Verify payment here
    
    try:
        request_body = {
            "telegramUserId": telegram_user_id,
            "durationDays": 30
        }
        
        if hash_code:
            request_body["hash"] = hash_code
        
        response = requests.post(
            f"{API_BASE}/api/subscription/activate",
            json=request_body
        )
        
        if response.status_code == 200:
            await update.message.reply_text("🎉 Subscription activated!")
        else:
            await update.message.reply_text("❌ Activation failed.")
            
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

async def check_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check subscription status"""
    telegram_user_id = update.effective_user.id
    
    try:
        response = requests.get(
            f"{API_BASE}/api/subscription/telegram/{telegram_user_id}"
        )
        
        if response.status_code == 200:
            data = response.json()
            status = "✅ Active" if data.get("isActive") else "❌ Inactive"
            await update.message.reply_text(f"Subscription Status: {status}")
        else:
            await update.message.reply_text("❌ Not found")
            
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

# Register handlers
def main():
    application = Application.builder().token("YOUR_BOT_TOKEN").build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("activate", activate_subscription))
    application.add_handler(CommandHandler("status", check_status))
    application.run_polling()

if __name__ == "__main__":
    main()
```

---

## Important Notes

1. **Hash Storage**: Store the hash in bot's user data (e.g., `context.user_data["hash"]`) so it persists during the session.

2. **Real-time Status**: Always check subscription status via API, don't cache it. This ensures admin deactivations work immediately.

3. **Error Handling**: Handle all error cases (404, 400, network errors) gracefully.

4. **Hash Format**: Hash must be exactly 24 characters (12 letters + 12 numbers).

5. **Backward Compatibility**: The `activate` endpoint still works without hash (falls back to telegramUserId), but using hash is recommended for proper linking.

---

## Questions?

If you need help implementing any of these changes, refer to:
- `BOT_API_DOCUMENTATION.md` - Full API documentation
- `MAP_WEBSITE_API_REQUIREMENTS.md` - Requirements specification

