# Bot API Documentation - Subscription Types Integration

This document describes how the Telegram bot should interact with the website API to support multiple subscription types.

## Base URL

```
https://map.anomonus.com
```

Or for development:
```
http://localhost:4000
```

---

## Subscription Types

The website supports 4 subscription types:

| Type | Stars | Duration Days | API Value |
|------|-------|---------------|-----------|
| 1 Month | 115 | 30 | `"1month"` |
| 6 Months | 520 | 180 | `"6month"` |
| 1 Year | 830 | 365 | `"12month"` |
| Lifetime | 2500 | 99999 | `"lifetime"` |

---

## Endpoints

### 1. Activate Subscription

**Endpoint:** `POST /api/subscription/activate`

**Description:** Called by the bot after a user successfully purchases a subscription with Telegram Stars.

**Request Body:**
```json
{
  "telegramUserId": 123456789,
  "hash": "ABC123XYZ456DEF789GHI012",  // Optional: User's hash from website
  "durationDays": 30,  // Optional: Duration in days (defaults to 30)
  "subscriptionType": "1month"  // Required: "1month", "6month", "12month", or "lifetime"
}
```

**Subscription Type Values:**
- `"1month"` - 1 Month subscription (30 days)
- `"6month"` - 6 Months subscription (180 days)
- `"12month"` - 1 Year subscription (365 days)
- `"lifetime"` - Lifetime subscription (no expiration)

**Response (200 OK):**
```json
{
  "ok": true,
  "userId": "user_1762513365727_w3s94luf2",
  "isActive": true,
  "expiresAt": 1735689600000,  // Unix timestamp in milliseconds (null for lifetime)
  "subscriptionType": "1month",
  "isLifetime": false
}
```

**Error Responses:**

- `400 Bad Request` - Missing or invalid fields
  ```json
  {
    "error": "Missing telegramUserId"
  }
  ```

- `400 Bad Request` - Invalid subscription type
  ```json
  {
    "error": "Invalid subscriptionType. Must be one of: 1month, 6month, 12month, lifetime"
  }
  ```

- `404 Not Found` - User not found
  ```json
  {
    "error": "Subscription not found. User must start bot first."
  }
  ```

**Example Requests:**

```bash
# 1 Month subscription
curl -X POST https://map.anomonus.com/api/subscription/activate \
  -H "Content-Type: application/json" \
  -d '{
    "telegramUserId": 123456789,
    "hash": "ABC123XYZ456DEF789GHI012",
    "durationDays": 30,
    "subscriptionType": "1month"
  }'

# 6 Months subscription
curl -X POST https://map.anomonus.com/api/subscription/activate \
  -H "Content-Type: application/json" \
  -d '{
    "telegramUserId": 123456789,
    "durationDays": 180,
    "subscriptionType": "6month"
  }'

# 1 Year subscription
curl -X POST https://map.anomonus.com/api/subscription/activate \
  -H "Content-Type: application/json" \
  -d '{
    "telegramUserId": 123456789,
    "durationDays": 365,
    "subscriptionType": "12month"
  }'

# Lifetime subscription
curl -X POST https://map.anomonus.com/api/subscription/activate \
  -H "Content-Type: application/json" \
  -d '{
    "telegramUserId": 123456789,
    "durationDays": 99999,
    "subscriptionType": "lifetime"
  }'
```

**Important Notes:**
- The `hash` field is optional. If provided, the website will link the subscription to that user's hash.
- If `hash` is not provided, the website will try to find the user by `telegramUserId`.
- The `durationDays` field is optional and defaults to 30. For lifetime subscriptions, you can pass 99999 or any large number.
- The `subscriptionType` field is **required** and must match one of the valid values.

---

### 2. Check Subscription Status

**Endpoint:** `GET /api/subscription/telegram/:telegramUserId`

**Description:** Check the current subscription status for a Telegram user. Use this to verify if a user has an active subscription before granting access to premium features.

**URL Parameters:**
- `telegramUserId` (required) - The Telegram user ID

**Response (200 OK):**
```json
{
  "userId": "user_1762513365727_w3s94luf2",
  "isActive": true,
  "expiresAt": 1735689600000,  // Unix timestamp in milliseconds (null for lifetime)
  "subscriptionType": "6month",
  "isLifetime": false,
  "telegramUsername": "username"
}
```

**For Lifetime Subscriptions:**
```json
{
  "userId": "user_1762513365727_w3s94luf2",
  "isActive": true,
  "expiresAt": null,
  "subscriptionType": "lifetime",
  "isLifetime": true,
  "telegramUsername": "username"
}
```

**Response (404 Not Found):**
```json
{
  "error": "Subscription not found"
}
```

**Example Request:**
```bash
curl https://map.anomonus.com/api/subscription/telegram/123456789
```

**Important Notes:**
- `isActive` will be `false` if the subscription has expired or was deactivated by an admin.
- For lifetime subscriptions, `expiresAt` will be `null` and `isLifetime` will be `true`.
- Always check `isActive` before granting access to premium features.

---

### 3. Link Telegram User (When User Starts Bot)

**Endpoint:** `POST /api/subscription/link-telegram`

**Description:** Called when a user starts the bot for the first time. This links the Telegram account to the website user account.

**Request Body:**
```json
{
  "telegramUserId": 123456789,
  "telegramUsername": "username",  // Optional
  "startParam": "dXNlcl8xNzYyNTEzMzY1NzI3X3czczk0bHVmMg==",  // Optional: Base64 encoded userId
  "hash": "ABC123XYZ456DEF789GHI012"  // Optional: User's hash from website
}
```

**Note:** You must provide either `startParam` or `hash` to identify the website user.

**Response (200 OK):**
```json
{
  "ok": true,
  "userId": "user_1762513365727_w3s94luf2",
  "telegramLinked": true
}
```

**Example Request:**
```bash
curl -X POST https://map.anomonus.com/api/subscription/link-telegram \
  -H "Content-Type: application/json" \
  -d '{
    "telegramUserId": 123456789,
    "telegramUsername": "username",
    "startParam": "dXNlcl8xNzYyNTEzMzY1NzI3X3czczk0bHVmMg=="
  }'
```

---

## Implementation Guide

### Step 1: User Starts Bot

When a user starts the bot (sends `/start` command):

1. Extract the `start` parameter from the deep link (if present)
2. Call `POST /api/subscription/link-telegram` to link the Telegram account to the website user
3. Store the `userId` returned in the response for future use

**Example:**
```python
# When user sends /start
start_param = update.message.text.split()[1] if len(update.message.text.split()) > 1 else None

# Link Telegram account
response = requests.post(
    'https://map.anomonus.com/api/subscription/link-telegram',
    json={
        'telegramUserId': update.effective_user.id,
        'telegramUsername': update.effective_user.username,
        'startParam': start_param
    }
)
```

### Step 2: User Purchases Subscription

When a user successfully purchases a subscription with Telegram Stars:

1. Determine which subscription type was purchased (1month, 6month, 12month, lifetime)
2. Calculate the duration in days (or use 99999 for lifetime)
3. Call `POST /api/subscription/activate` with the subscription details

**Example:**
```python
# After successful payment
subscription_type = "1month"  # or "6month", "12month", "lifetime"
duration_days = 30  # or 180, 365, 99999

response = requests.post(
    'https://map.anomonus.com/api/subscription/activate',
    json={
        'telegramUserId': user_id,
        'subscriptionType': subscription_type,
        'durationDays': duration_days
    }
)

if response.status_code == 200:
    data = response.json()
    # Subscription activated successfully
    # data['userId'] - website user ID
    # data['isActive'] - subscription is now active
    # data['expiresAt'] - expiration timestamp
else:
    # Handle error
    error = response.json()
    print(f"Error: {error['error']}")
```

### Step 3: Check Subscription Before Granting Access

Before granting access to premium features, check if the user has an active subscription:

**Example:**
```python
# Check subscription status
response = requests.get(
    f'https://map.anomonus.com/api/subscription/telegram/{user_id}'
)

if response.status_code == 200:
    data = response.json()
    if data['isActive']:
        # User has active subscription
        subscription_type = data['subscriptionType']
        is_lifetime = data.get('isLifetime', False)
        expires_at = data.get('expiresAt')
        
        # Grant access to premium features
    else:
        # Subscription expired or inactive
        # Show message to purchase subscription
else:
    # User not found or error
    # Show message to start bot first
```

---

## Subscription Type Mapping

Use this mapping when processing payments:

```python
SUBSCRIPTION_TYPES = {
    '1month': {
        'stars': 115,
        'days': 30,
        'api_value': '1month'
    },
    '6month': {
        'stars': 520,
        'days': 180,
        'api_value': '6month'
    },
    '12month': {
        'stars': 830,
        'days': 365,
        'api_value': '12month'
    },
    'lifetime': {
        'stars': 2500,
        'days': 99999,
        'api_value': 'lifetime'
    }
}
```

---

## Error Handling

### Common Errors

1. **"Subscription not found. User must start bot first."**
   - **Cause:** User hasn't started the bot yet
   - **Solution:** Ask user to start the bot first using `/start` command

2. **"Invalid subscriptionType"**
   - **Cause:** Wrong subscription type value
   - **Solution:** Use one of: `"1month"`, `"6month"`, `"12month"`, `"lifetime"`

3. **"Missing telegramUserId"**
   - **Cause:** Required field not provided
   - **Solution:** Always include `telegramUserId` in the request

### Retry Logic

For network errors, implement retry logic:

```python
import time

def activate_subscription_with_retry(telegram_user_id, subscription_type, duration_days, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.post(
                'https://map.anomonus.com/api/subscription/activate',
                json={
                    'telegramUserId': telegram_user_id,
                    'subscriptionType': subscription_type,
                    'durationDays': duration_days
                },
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
                continue
            raise
```

---

## Testing

### Test 1 Month Subscription
```bash
curl -X POST http://localhost:4000/api/subscription/activate \
  -H "Content-Type: application/json" \
  -d '{
    "telegramUserId": 123456789,
    "subscriptionType": "1month",
    "durationDays": 30
  }'
```

### Test 6 Months Subscription
```bash
curl -X POST http://localhost:4000/api/subscription/activate \
  -H "Content-Type: application/json" \
  -d '{
    "telegramUserId": 123456789,
    "subscriptionType": "6month",
    "durationDays": 180
  }'
```

### Test 1 Year Subscription
```bash
curl -X POST http://localhost:4000/api/subscription/activate \
  -H "Content-Type: application/json" \
  -d '{
    "telegramUserId": 123456789,
    "subscriptionType": "12month",
    "durationDays": 365
  }'
```

### Test Lifetime Subscription
```bash
curl -X POST http://localhost:4000/api/subscription/activate \
  -H "Content-Type: application/json" \
  -d '{
    "telegramUserId": 123456789,
    "subscriptionType": "lifetime",
    "durationDays": 99999
  }'
```

### Check Subscription Status
```bash
curl http://localhost:4000/api/subscription/telegram/123456789
```

---

## Important Notes

1. **Lifetime Subscriptions:**
   - Set `subscriptionType` to `"lifetime"`
   - `expiresAt` will be `null` in the response
   - `isLifetime` will be `true`
   - These subscriptions never expire (unless admin deactivates)

2. **Subscription Type is Required:**
   - Always include `subscriptionType` in the activation request
   - If not provided, defaults to `"1month"` (30 days)

3. **Duration Days:**
   - For lifetime, you can pass `99999` or any large number
   - The website will handle lifetime subscriptions specially based on `subscriptionType`

4. **User Identification:**
   - Use `telegramUserId` to identify users
   - `hash` is optional but helps link to website user if provided
   - If `hash` is not provided, the website will find the user by `telegramUserId`

5. **Status Checking:**
   - Always check `isActive` before granting premium access
   - `expiresAt` is in Unix timestamp (milliseconds)
   - For lifetime subscriptions, `expiresAt` is `null`

---

## Support

For questions or issues:
- Check the website API logs
- Verify the subscription type values match exactly
- Ensure `telegramUserId` is a valid number
- Test with the provided curl examples

---

## Changelog

### Version 1.0.0 (Current)
- Added support for 4 subscription types: 1month, 6month, 12month, lifetime
- Added `subscriptionType` field to activation endpoint
- Added `isLifetime` flag for lifetime subscriptions
- Updated status endpoint to return subscription type

