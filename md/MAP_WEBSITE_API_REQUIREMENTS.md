# Map Website API Requirements for Bot Integration

This document describes the API endpoints that the map website must implement for the Telegram bot to work with the hash registration system.

## Base URL

```
http://localhost:4000
```

Or in production:
```
https://your-domain.com
```

---

## Required Endpoints

### 1. Validate Hash

**Endpoint:** `GET /api/subscription/validate-hash/{hash}`

Validates a user's registration hash. Called by the bot when a user enters their hash.

**Path Parameters:**
- `hash` (required): The 24-character hash (12 letters + 12 numbers)

**Response (200 OK) - Hash is valid:**
```json
{
  "valid": true,
  "userId": "user_1762513365727_w3s94luf2",
  "message": "Hash validated successfully"
}
```

**Response (404 Not Found) - Hash is invalid or non-existing:**
```json
{
  "error": "Hash not found",
  "valid": false
}
```

**Response (400 Bad Request) - Invalid hash format:**
```json
{
  "error": "Invalid hash format",
  "valid": false
}
```

**Example Request:**
```bash
curl http://localhost:4000/api/subscription/validate-hash/abcdefghijkl123456789012
```

**Example Response (Valid):**
```json
{
  "valid": true,
  "userId": "user_1762513365727_w3s94luf2",
  "message": "Hash validated successfully"
}
```

**Example Response (Invalid):**
```json
{
  "error": "Hash not found",
  "valid": false
}
```

**Implementation Notes:**
- Hash format: 24 characters (12 letters + 12 numbers)
- Each hash should be unique and linked to a user account
- Return the `userId` associated with the hash
- If hash doesn't exist, return 404

---

### 2. Activate Subscription (Updated)

**Endpoint:** `POST /api/subscription/activate`

Activates a user's subscription after payment. Now includes optional hash field.

**Request Body:**
```json
{
  "telegramUserId": 123456789,
  "hash": "abcdefghijkl123456789012",  // Optional - included if user has validated hash
  "durationDays": 30  // Optional, defaults to 30
}
```

**Response (200 OK):**
```json
{
  "ok": true,
  "userId": "user_1762513365727_w3s94luf2",
  "isActive": true,
  "expiresAt": 1735689600000
}
```

**Response (404 Not Found) - User not found:**
```json
{
  "error": "Subscription not found. User must start bot first."
}
```

**Response (400 Bad Request):**
```json
{
  "error": "Missing telegramUserId"
}
```

**Example Request:**
```bash
curl -X POST http://localhost:4000/api/subscription/activate \
  -H "Content-Type: application/json" \
  -d '{
    "telegramUserId": 123456789,
    "hash": "abcdefghijkl123456789012",
    "durationDays": 30
  }'
```

**Implementation Notes:**
- `hash` field is optional - only included if user validated their hash in bot
- If hash is provided, link the subscription to the user account associated with that hash
- If hash is not provided, use `telegramUserId` to find/create subscription
- Duration defaults to 30 days if not specified

---

### 3. Get Subscription by Telegram User ID (Existing)

**Endpoint:** `GET /api/subscription/telegram/{telegramUserId}`

Get subscription details by Telegram user ID. This endpoint already exists but is used by the bot.

**Path Parameters:**
- `telegramUserId`: Telegram user ID (number)

**Response (200 OK):**
```json
{
  "userId": "user_1762513365727_w3s94luf2",
  "isActive": true,
  "expiresAt": 1735689600000,
  "telegramUsername": "username"
}
```

**Response (404 Not Found):**
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

## Integration Flow

### 1. User Registration Flow

```
User visits website
    ↓
Website generates unique hash (12 letters + 12 numbers)
    ↓
Hash is stored and linked to user account
    ↓
User copies hash
```

### 2. Bot Hash Validation Flow

```
User clicks /start in bot
    ↓
Bot asks for hash
    ↓
User enters hash
    ↓
Bot calls: GET /api/subscription/validate-hash/{hash}
    ↓
Website validates hash and returns userId
    ↓
Bot saves hash for user
    ↓
User can now use bot features
```

### 3. Payment & Subscription Flow

```
User pays in bot
    ↓
Bot receives payment
    ↓
Bot calls: POST /api/subscription/activate
    {
      "telegramUserId": 123456789,
      "hash": "abcdefghijkl123456789012",  // If available
      "durationDays": 30
    }
    ↓
Website activates subscription for user (linked by hash or telegramUserId)
    ↓
User can access premium features on website
```

---

## Hash Format Specification

- **Length**: Exactly 24 characters
- **Format**: 12 letters (a-z, A-Z) + 12 numbers (0-9)
- **Example**: `abcdefghijkl123456789012`
- **Uniqueness**: Each hash must be unique
- **Storage**: Hash should be linked to a user account in your database

---

## Database Schema Suggestions

### Hash Table
```sql
CREATE TABLE user_hashes (
  id SERIAL PRIMARY KEY,
  hash VARCHAR(24) UNIQUE NOT NULL,
  user_id VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  used_at TIMESTAMP,
  telegram_user_id BIGINT,
  FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### Subscription Table (Updated)
```sql
ALTER TABLE subscriptions ADD COLUMN hash VARCHAR(24);
ALTER TABLE subscriptions ADD COLUMN telegram_user_id BIGINT;
```

---

## Error Handling

### Common Errors

1. **Hash Not Found (404)**
   - User entered incorrect hash
   - Hash doesn't exist in database
   - Response: `{"error": "Hash not found", "valid": false}`

2. **Invalid Hash Format (400)**
   - Hash doesn't match 24-character format
   - Response: `{"error": "Invalid hash format", "valid": false}`

3. **User Not Found (404)**
   - Telegram user not linked to any account
   - Response: `{"error": "Subscription not found. User must start bot first."}`

4. **Server Error (500)**
   - Internal server error
   - Response: `{"error": "Internal server error"}`

---

## Testing

### Test Hash Validation

```bash
# Valid hash
curl http://localhost:4000/api/subscription/validate-hash/abcdefghijkl123456789012

# Invalid hash
curl http://localhost:4000/api/subscription/validate-hash/invalidhash123

# Wrong format
curl http://localhost:4000/api/subscription/validate-hash/short
```

### Test Subscription Activation

```bash
# With hash
curl -X POST http://localhost:4000/api/subscription/activate \
  -H "Content-Type: application/json" \
  -d '{
    "telegramUserId": 123456789,
    "hash": "abcdefghijkl123456789012",
    "durationDays": 30
  }'

# Without hash (fallback)
curl -X POST http://localhost:4000/api/subscription/activate \
  -H "Content-Type: application/json" \
  -d '{
    "telegramUserId": 123456789,
    "durationDays": 30
  }'
```

---

## Security Considerations

1. **Hash Validation**
   - Rate limit hash validation requests to prevent brute force
   - Consider adding expiration to hashes (e.g., 24 hours)
   - Log failed validation attempts

2. **Subscription Activation**
   - Verify payment before activating subscription
   - Validate telegramUserId is legitimate
   - Check hash hasn't been used multiple times (if one-time use)

3. **API Security**
   - Use HTTPS in production
   - Consider API key authentication for bot requests
   - Validate all input parameters

---

## Implementation Checklist

- [ ] Create hash generation function (12 letters + 12 numbers)
- [ ] Store hashes in database linked to user accounts
- [ ] Implement `GET /api/subscription/validate-hash/{hash}` endpoint
- [ ] Update `POST /api/subscription/activate` to accept `hash` field
- [ ] Link subscriptions to users by hash when provided
- [ ] Add error handling for invalid/non-existing hashes
- [ ] Test hash validation flow
- [ ] Test subscription activation with hash
- [ ] Add rate limiting for hash validation
- [ ] Add logging for hash usage

---

## Example Implementation (Node.js/Express)

```javascript
// Validate hash endpoint
app.get('/api/subscription/validate-hash/:hash', async (req, res) => {
  const { hash } = req.params;
  
  // Validate format
  if (!/^[a-zA-Z]{12}[0-9]{12}$/.test(hash)) {
    return res.status(400).json({
      error: 'Invalid hash format',
      valid: false
    });
  }
  
  // Find hash in database
  const userHash = await db.userHashes.findOne({ where: { hash } });
  
  if (!userHash) {
    return res.status(404).json({
      error: 'Hash not found',
      valid: false
    });
  }
  
  // Return user ID
  res.json({
    valid: true,
    userId: userHash.userId,
    message: 'Hash validated successfully'
  });
});

// Activate subscription (updated)
app.post('/api/subscription/activate', async (req, res) => {
  const { telegramUserId, hash, durationDays = 30 } = req.body;
  
  if (!telegramUserId) {
    return res.status(400).json({ error: 'Missing telegramUserId' });
  }
  
  let userId;
  
  // If hash provided, find user by hash
  if (hash) {
    const userHash = await db.userHashes.findOne({ where: { hash } });
    if (userHash) {
      userId = userHash.userId;
    }
  }
  
  // If no hash or hash not found, try to find by telegramUserId
  if (!userId) {
    const subscription = await db.subscriptions.findOne({
      where: { telegramUserId }
    });
    if (subscription) {
      userId = subscription.userId;
    } else {
      return res.status(404).json({
        error: 'Subscription not found. User must start bot first.'
      });
    }
  }
  
  // Activate subscription
  const expiresAt = Date.now() + (durationDays * 24 * 60 * 60 * 1000);
  
  await db.subscriptions.upsert({
    userId,
    telegramUserId,
    hash,
    isActive: true,
    expiresAt
  });
  
  res.json({
    ok: true,
    userId,
    isActive: true,
    expiresAt
  });
});
```

---

## Support

If you need help implementing these endpoints, refer to:
- `HASH_SYSTEM.md` - Bot-side hash system documentation
- `INTEGRATION.md` - General bot-website integration guide
- `API_DOCUMENTATION copy.md` - Full map website API documentation

