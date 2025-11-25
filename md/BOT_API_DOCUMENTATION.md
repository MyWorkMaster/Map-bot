# Telegram Bot API Integration Documentation

## Base URL

```
http://localhost:4000
```

Or in production:
```
https://your-domain.com
```

---

## Overview

This documentation describes the API endpoints needed to integrate a Telegram bot with the Anomonus Map subscription system. The bot allows users to subscribe using their unique hash code.

### User Flow

1. User visits website and gets a unique hash (24 characters: 12 letters + 12 numbers)
2. User clicks "AI Route" button → sees their hash in a popup
3. User copies hash and goes to Telegram bot
4. User sends `/start <hash>` to the bot
5. Bot finds user by hash and links Telegram account
6. User makes payment via Telegram Stars
7. Bot activates subscription after successful payment

---

## Endpoints

### 1. Find User by Hash

#### `GET /api/users/by-hash/:hash`

Find a website user by their unique hash code.

**Path Parameters:**
- `hash` (required): User's unique hash (24 characters)

**Response:**
```json
{
  "userId": "user_1762513365727_w3s94luf2",
  "hash": "ABC123XYZ456DEF789GHI012",
  "lastSeen": 1705320000000,
  "isSubscribed": false
}
```

**Error Responses:**
- `404 Not Found`: User with this hash not found
```json
{
  "error": "User not found"
}
```

**Example:**
```bash
curl http://localhost:4000/api/users/by-hash/ABC123XYZ456DEF789GHI012
```

**cURL Example:**
```bash
curl -X GET "http://localhost:4000/api/users/by-hash/ABC123XYZ456DEF789GHI012"
```

---

### 2. Link Telegram User to Website User

#### `POST /api/subscription/link-telegram`

Link a Telegram user account to a website user. This should be called when the user sends `/start <hash>` to the bot.

**Request Body:**
```json
{
  "startParam": "dXNlcl8xNzYyNTEzMzY1NzI3X3czczk0bHVmMg",  // base64url encoded userId (from bot link)
  "telegramUserId": 123456789,
  "telegramUsername": "username"  // Optional
}
```

**Alternative: Link by Hash**

If you have the hash directly, you can:
1. First call `GET /api/users/by-hash/:hash` to get the userId
2. Then call this endpoint with the userId encoded as startParam

**Response:**
```json
{
  "ok": true,
  "userId": "user_1762513365727_w3s94luf2",
  "telegramLinked": true
}
```

**Error Responses:**
- `400 Bad Request`: Missing required fields
```json
{
  "error": "Missing required fields"
}
```

- `400 Bad Request`: Invalid start parameter
```json
{
  "error": "Invalid start parameter"
}
```

**Example:**
```bash
curl -X POST http://localhost:4000/api/subscription/link-telegram \
  -H "Content-Type: application/json" \
  -d '{
    "startParam": "dXNlcl8xNzYyNTEzMzY1NzI3X3czczk0bHVmMg",
    "telegramUserId": 123456789,
    "telegramUsername": "username"
  }'
```

---

### 3. Activate Subscription

#### `POST /api/subscription/activate`

Activate a user's subscription after successful payment. This should be called after the user completes payment via Telegram Stars.

**Request Body:**
```json
{
  "telegramUserId": 123456789,
  "durationDays": 30  // Optional, defaults to 30 days
}
```

**Response:**
```json
{
  "ok": true,
  "userId": "user_1762513365727_w3s94luf2",
  "isActive": true,
  "expiresAt": 1707912000000  // Unix timestamp in milliseconds
}
```

**Error Responses:**
- `400 Bad Request`: Missing telegramUserId
```json
{
  "error": "Missing telegramUserId"
}
```

- `404 Not Found`: Subscription not found (user must start bot first)
```json
{
  "error": "Subscription not found. User must start bot first."
}
```

**Example:**
```bash
curl -X POST http://localhost:4000/api/subscription/activate \
  -H "Content-Type: application/json" \
  -d '{
    "telegramUserId": 123456789,
    "durationDays": 30
  }'
```

---

### 4. Check Subscription Status

#### `GET /api/subscription/telegram/:telegramUserId`

Check if a Telegram user has an active subscription. Useful for verifying subscription status before allowing access to premium features.

**Path Parameters:**
- `telegramUserId` (required): Telegram user ID (number)

**Response:**
```json
{
  "userId": "user_1762513365727_w3s94luf2",
  "isActive": true,
  "expiresAt": 1707912000000,
  "telegramUsername": "username"
}
```

**Error Responses:**
- `404 Not Found`: Subscription not found
```json
{
  "error": "Subscription not found"
}
```

**Example:**
```bash
curl http://localhost:4000/api/subscription/telegram/123456789
```

---

### 5. Check Subscription by User ID

#### `GET /api/subscription/check/:userId`

Check subscription status by website user ID.

**Path Parameters:**
- `userId` (required): Website user ID

**Response:**
```json
{
  "isActive": true,
  "expiresAt": 1707912000000,
  "telegramLinked": true
}
```

**Example:**
```bash
curl http://localhost:4000/api/subscription/check/user_1762513365727_w3s94luf2
```

---

## Bot Implementation Flow

### Step 1: User Starts Bot with Hash

When user sends `/start <hash>` to your bot:

```python
# Python example
import requests

hash_code = message.text.split()[1]  # Extract hash from /start command

# Find user by hash
response = requests.get(f"http://localhost:4000/api/users/by-hash/{hash_code}")
if response.status_code == 404:
    bot.send_message(chat_id, "❌ Hash not found. Please check your hash and try again.")
    return

user_data = response.json()
userId = user_data["userId"]
```

### Step 2: Link Telegram Account

```python
# Link Telegram user to website user
link_response = requests.post(
    "http://localhost:4000/api/subscription/link-telegram",
    json={
        "startParam": base64url_encode(userId),  # Encode userId as base64url
        "telegramUserId": message.from_user.id,
        "telegramUsername": message.from_user.username
    }
)

if link_response.status_code == 200:
    bot.send_message(chat_id, "✅ Account linked successfully!")
```

### Step 3: Process Payment

Use Telegram Stars API to process payment. After successful payment:

```python
# Activate subscription
activate_response = requests.post(
    "http://localhost:4000/api/subscription/activate",
    json={
        "telegramUserId": message.from_user.id,
        "durationDays": 30  # or based on payment tier
    }
)

if activate_response.status_code == 200:
    bot.send_message(chat_id, "🎉 Subscription activated! You now have access to AI Route.")
```

### Step 4: Verify Subscription (Optional)

Before allowing premium features, verify subscription:

```python
# Check subscription status
status_response = requests.get(
    f"http://localhost:4000/api/subscription/telegram/{message.from_user.id}"
)

if status_response.status_code == 200:
    subscription = status_response.json()
    if subscription["isActive"]:
        # User has active subscription
        pass
```

---

## Data Models

### User
```typescript
interface User {
  userId: string;           // Website user ID (e.g., "user_1762513365727_w3s94luf2")
  hash: string;             // Unique 24-character hash (12 letters + 12 numbers)
  lastSeen: number;         // Unix timestamp in milliseconds
  isSubscribed: boolean;     // Current subscription status
}
```

### Subscription
```typescript
interface Subscription {
  userId: string;                    // Website user ID
  telegramUserId?: number;           // Telegram user ID (if linked)
  telegramUsername?: string;         // Telegram username (if linked)
  isActive: boolean;                 // Whether subscription is active
  expiresAt?: number;                 // Unix timestamp in milliseconds (if active)
  createdAt: number;                  // When subscription was created
  lastChecked: number;                // Last time subscription was checked
}
```

---

## Error Codes

| Status Code | Description |
|------------|-------------|
| 200 | Success |
| 400 | Bad Request - Missing or invalid parameters |
| 403 | Forbidden - Admin access required |
| 404 | Not Found - Resource doesn't exist |
| 500 | Internal Server Error |

---

## Important Notes

1. **Hash Format**: User hashes are exactly 24 characters: 12 uppercase letters (A-Z) + 12 numbers (0-9), randomly shuffled.

2. **User ID Encoding**: When using `startParam`, the userId must be base64url encoded. The API provides `decodeStartParam()` function to decode it.

3. **Subscription Duration**: Default subscription duration is 30 days. You can specify a different duration in `durationDays` parameter.

4. **Hash Persistence**: User hashes are stored in browser localStorage and sent to the server with each API request. The server stores the hash with user activity data.

5. **Linking Flow**: 
   - User must be linked via `/api/subscription/link-telegram` before subscription can be activated
   - Linking can be done using either `startParam` (base64url encoded userId) or by finding user by hash first

6. **Payment Integration**: This API doesn't handle payments. You need to integrate Telegram Stars API separately in your bot code.

---

## Example Bot Code (Python)

```python
import requests
import base64
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

API_BASE = "http://localhost:4000"

def base64url_encode(s):
    """Encode string to base64url format"""
    return base64.urlsafe_b64encode(s.encode()).decode().rstrip('=')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    chat_id = update.effective_chat.id
    telegram_user_id = update.effective_user.id
    telegram_username = update.effective_user.username
    
    # Check if hash provided
    if len(context.args) == 0:
        await update.message.reply_text(
            "👋 Welcome! Please send your hash code:\n"
            "/start YOUR_HASH_CODE"
        )
        return
    
    hash_code = context.args[0]
    
    # Step 1: Find user by hash
    try:
        response = requests.get(f"{API_BASE}/api/users/by-hash/{hash_code}")
        if response.status_code == 404:
            await update.message.reply_text("❌ Hash not found. Please check your hash.")
            return
        
        user_data = response.json()
        userId = user_data["userId"]
        
        # Step 2: Link Telegram account
        link_response = requests.post(
            f"{API_BASE}/api/subscription/link-telegram",
            json={
                "startParam": base64url_encode(userId),
                "telegramUserId": telegram_user_id,
                "telegramUsername": telegram_username
            }
        )
        
        if link_response.status_code == 200:
            await update.message.reply_text(
                "✅ Account linked successfully!\n\n"
                "💰 To activate subscription, please make a payment."
            )
        else:
            await update.message.reply_text("❌ Failed to link account.")
            
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

async def activate_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Activate subscription after payment"""
    telegram_user_id = update.effective_user.id
    
    # TODO: Verify payment via Telegram Stars API here
    
    try:
        response = requests.post(
            f"{API_BASE}/api/subscription/activate",
            json={
                "telegramUserId": telegram_user_id,
                "durationDays": 30
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            await update.message.reply_text(
                f"🎉 Subscription activated!\n\n"
                f"✅ Active until: {data['expiresAt']}\n"
                f"You now have access to AI Route feature."
            )
        else:
            await update.message.reply_text("❌ Failed to activate subscription.")
            
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

# Bot setup
def main():
    application = Application.builder().token("YOUR_BOT_TOKEN").build()
    application.add_handler(CommandHandler("start", start))
    # Add other handlers...
    application.run_polling()

if __name__ == "__main__":
    main()
```

---

## Testing

### Test Hash Lookup
```bash
curl http://localhost:4000/api/users/by-hash/TESTHASH123456789012
```

### Test Link Account
```bash
curl -X POST http://localhost:4000/api/subscription/link-telegram \
  -H "Content-Type: application/json" \
  -d '{
    "startParam": "dXNlcl8xNzYyNTEzMzY1NzI3X3czczk0bHVmMg",
    "telegramUserId": 123456789,
    "telegramUsername": "testuser"
  }'
```

### Test Activate Subscription
```bash
curl -X POST http://localhost:4000/api/subscription/activate \
  -H "Content-Type: application/json" \
  -d '{
    "telegramUserId": 123456789,
    "durationDays": 30
  }'
```

---

## Support

For issues or questions, check the main API documentation: `API_DOCUMENTATION.md`

