# Anomonus Bot API Documentation

This API allows your website to interact with the Telegram bot, specifically to check and manage user subscriptions.

## Base URL

```
http://localhost:5000
```

For production, replace `localhost:5000` with your server's IP/domain.

## Endpoints

### 1. Check Subscription Status

Check if a user is subscribed.

**Endpoint:** `GET /api/check-subscription`

**Parameters:**
- `user_id` (required): Telegram user ID

**Example Request:**
```
GET http://localhost:5000/api/check-subscription?user_id=123456789
```

**Example Response:**
```json
{
  "success": true,
  "user_id": 123456789,
  "is_subscribed": true
}
```

### 2. Subscribe User

Mark a user as subscribed (useful if payment is verified on website).

**Endpoint:** `POST /api/subscribe`

**Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "user_id": 123456789
}
```

**Example Response:**
```json
{
  "success": true,
  "user_id": 123456789,
  "message": "User subscribed successfully"
}
```

### 3. Get User Info

Get user information including subscription status.

**Endpoint:** `GET /api/user-info`

**Parameters:**
- `user_id` (required): Telegram user ID

**Example Request:**
```
GET http://localhost:5000/api/user-info?user_id=123456789
```

**Example Response:**
```json
{
  "success": true,
  "user_id": 123456789,
  "is_subscribed": true
}
```

### 4. Health Check

Check if the API server is running.

**Endpoint:** `GET /api/health`

**Example Response:**
```json
{
  "success": true,
  "status": "online",
  "subscribed_users_count": 5
}
```

## Error Responses

All endpoints return error responses in this format:

```json
{
  "success": false,
  "error": "Error message here"
}
```

## Usage Examples

### JavaScript (Fetch API)

```javascript
// Check subscription
async function checkSubscription(userId) {
  const response = await fetch(`http://localhost:5000/api/check-subscription?user_id=${userId}`);
  const data = await response.json();
  return data.is_subscribed;
}

// Subscribe user
async function subscribeUser(userId) {
  const response = await fetch('http://localhost:5000/api/subscribe', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ user_id: userId })
  });
  const data = await response.json();
  return data.success;
}
```

### Python (Requests)

```python
import requests

# Check subscription
def check_subscription(user_id):
    response = requests.get(
        'http://localhost:5000/api/check-subscription',
        params={'user_id': user_id}
    )
    data = response.json()
    return data.get('is_subscribed', False)

# Subscribe user
def subscribe_user(user_id):
    response = requests.post(
        'http://localhost:5000/api/subscribe',
        json={'user_id': user_id}
    )
    data = response.json()
    return data.get('success', False)
```

## CORS

CORS is enabled, so your website can make requests from any domain. For production, you may want to restrict this to your specific domain.

## Notes

- The API runs on port 5000 by default
- Subscription data is stored in `subscribed_users.json` file
- The bot and API server run in separate threads
- All endpoints return JSON responses

