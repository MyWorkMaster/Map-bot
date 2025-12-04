# Website API Implementation Guide

This document describes the exact API endpoints your website must implement for the Telegram bot to work correctly. The bot uses these endpoints as the **source of truth** for subscription status.

## Base URL

```
http://localhost:4000
```

Or in production:
```
https://your-domain.com
```

---

## Critical: API as Source of Truth

**IMPORTANT:** The bot now checks subscription status in **real-time** via API. This means:

- ✅ When admin deactivates a user → Bot immediately sees `isActive: false`
- ✅ When admin activates a user → Bot immediately sees `isActive: true`
- ✅ No caching in bot → Always checks API for current status
- ✅ Admin panel changes take effect immediately

---

## Required Endpoints

### 1. Find User by Hash

**Endpoint:** `GET /api/users/by-hash/{hash}`

Called by bot when user enters their hash code.

**Path Parameters:**
- `hash` (required): 24-character hash (12 letters + 12 numbers)

**Response (200 OK) - Hash found:**
```json
{
  "userId": "user_1762513365727_w3s94luf2",
  "hash": "ABC123XYZ456DEF789GHI012",
  "lastSeen": 1705320000000,
  "isSubscribed": false
}
```

**Response (404 Not Found) - Hash not found:**
```json
{
  "error": "User not found"
}
```

**Response (400 Bad Request) - Invalid format:**
```json
{
  "error": "Invalid hash format"
}
```

**Example:**
```bash
curl http://localhost:4000/api/users/by-hash/ABC123XYZ456DEF789GHI012
```

**Implementation Notes:**
- Hash format: Exactly 24 characters (12 letters + 12 numbers)
- Return the `userId` associated with this hash
- This is used to link Telegram account to website user

---

### 2. Link Telegram User to Website User

**Endpoint:** `POST /api/subscription/link-telegram`

Called by bot after hash validation to link Telegram account.

**Request Body:**
```json
{
  "startParam": "dXNlcl8xNzYyNTEzMzY1NzI3X3czczk0bHVmMg",  // base64url encoded userId
  "telegramUserId": 123456789,
  "telegramUsername": "username",  // Optional
  "hash": "ABC123XYZ456DEF789GHI012"  // Optional - if provided, use this instead of startParam
}
```

**Response (200 OK):**
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

- `400 Bad Request`: Invalid start parameter or hash
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

**Implementation Notes:**
- If `hash` is provided, use it to find the user (preferred method)
- If `startParam` is provided, decode it from base64url to get userId
- Link `telegramUserId` to the website user account
- Store `telegramUsername` if provided

---

### 3. Check Subscription Status (REAL-TIME)

**Endpoint:** `GET /api/subscription/telegram/{telegramUserId}`

**CRITICAL:** This is called by the bot in real-time to check subscription status. Admin deactivations must be reflected immediately.

**Path Parameters:**
- `telegramUserId` (required): Telegram user ID (number)

**Response (200 OK) - User found:**
```json
{
  "userId": "user_1762513365727_w3s94luf2",
  "isActive": true,  // CRITICAL: Must reflect admin panel changes immediately
  "expiresAt": 1735689600000,  // Unix timestamp in milliseconds
  "telegramUsername": "username"
}
```

**Response (200 OK) - User deactivated by admin:**
```json
{
  "userId": "user_1762513365727_w3s94luf2",
  "isActive": false,  // Admin deactivated - bot must see this immediately
  "expiresAt": null,
  "telegramUsername": "username"
}
```

**Response (404 Not Found) - User not found:**
```json
{
  "error": "Subscription not found"
}
```

**Example:**
```bash
curl http://localhost:4000/api/subscription/telegram/123456789
```

**Implementation Notes:**
- **CRITICAL:** `isActive` must reflect the current state from your database
- If admin deactivated user → `isActive: false` immediately
- If admin activated user → `isActive: true` immediately
- Check expiration: if `expiresAt` is in the past, `isActive` should be `false`
- This endpoint is called frequently by the bot - optimize for performance

---

### 4. Activate Subscription

**Endpoint:** `POST /api/subscription/activate`

Called by bot after successful Telegram Stars payment.

**Request Body:**
```json
{
  "telegramUserId": 123456789,
  "hash": "ABC123XYZ456DEF789GHI012",  // Optional - if provided, link to this user
  "durationDays": 30  // Optional, defaults to 30
}
```

**Response (200 OK):**
```json
{
  "ok": true,
  "userId": "user_1762513365727_w3s94luf2",
  "isActive": true,
  "expiresAt": 1735689600000  // Unix timestamp in milliseconds
}
```

**Error Responses:**
- `400 Bad Request`: Missing telegramUserId
  ```json
  {
    "error": "Missing telegramUserId"
  }
  ```

- `404 Not Found`: User not found (must link account first)
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
    "hash": "ABC123XYZ456DEF789GHI012",
    "durationDays": 30
  }'
```

**Implementation Notes:**
- If `hash` is provided, find user by hash and activate subscription
- If `hash` is not provided, find user by `telegramUserId`
- Set `isActive: true`
- Calculate `expiresAt` based on `durationDays` (default 30 days)
- Return the activated subscription details

---

## Admin Panel Integration

### How Admin Deactivations Work

When admin deactivates a user in the admin panel:

1. **Update Database:**
   ```sql
   UPDATE subscriptions 
   SET isActive = false 
   WHERE telegramUserId = 123456789;
   ```

2. **Bot Checks Status:**
   - Bot calls: `GET /api/subscription/telegram/123456789`
   - Your API returns: `{"isActive": false, ...}`
   - Bot immediately sees user as unsubscribed

3. **Result:**
   - User cannot access premium features
   - If user tries to pay again, bot will allow it (since `isActive: false`)

### How Admin Activations Work

When admin activates a user in the admin panel:

1. **Update Database:**
   ```sql
   UPDATE subscriptions 
   SET isActive = true, expiresAt = <new_expiry> 
   WHERE telegramUserId = 123456789;
   ```

2. **Bot Checks Status:**
   - Bot calls: `GET /api/subscription/telegram/123456789`
   - Your API returns: `{"isActive": true, ...}`
   - Bot immediately sees user as subscribed

3. **Result:**
   - User can access premium features immediately

---

## Database Schema Recommendations

### Subscriptions Table
```sql
CREATE TABLE subscriptions (
  id SERIAL PRIMARY KEY,
  userId VARCHAR(255) NOT NULL,
  hash VARCHAR(24) UNIQUE,
  telegramUserId BIGINT UNIQUE,
  telegramUsername VARCHAR(255),
  isActive BOOLEAN DEFAULT false,  -- CRITICAL: Must reflect admin changes
  expiresAt BIGINT,  -- Unix timestamp in milliseconds
  createdAt BIGINT NOT NULL,
  lastChecked BIGINT,
  FOREIGN KEY (userId) REFERENCES users(id)
);

-- Index for fast lookups
CREATE INDEX idx_subscriptions_telegram_user_id ON subscriptions(telegramUserId);
CREATE INDEX idx_subscriptions_hash ON subscriptions(hash);
CREATE INDEX idx_subscriptions_user_id ON subscriptions(userId);
```

### Users Table (with Hash)
```sql
CREATE TABLE users (
  id VARCHAR(255) PRIMARY KEY,
  hash VARCHAR(24) UNIQUE NOT NULL,  -- 24 characters: 12 letters + 12 numbers
  lastSeen BIGINT,
  createdAt BIGINT NOT NULL
);

-- Index for hash lookups
CREATE INDEX idx_users_hash ON users(hash);
```

---

## Implementation Checklist

### Required Endpoints
- [ ] `GET /api/users/by-hash/{hash}` - Find user by hash
- [ ] `POST /api/subscription/link-telegram` - Link Telegram account
- [ ] `GET /api/subscription/telegram/{telegramUserId}` - Check subscription (REAL-TIME)
- [ ] `POST /api/subscription/activate` - Activate subscription

### Critical Requirements
- [ ] `isActive` field must reflect database state in real-time
- [ ] Admin deactivations must immediately return `isActive: false`
- [ ] Admin activations must immediately return `isActive: true`
- [ ] Check expiration dates - expired subscriptions = `isActive: false`
- [ ] Optimize `GET /api/subscription/telegram/{telegramUserId}` for performance (called frequently)

### Database
- [ ] Create subscriptions table with `isActive` field
- [ ] Create users table with `hash` field
- [ ] Add indexes for fast lookups
- [ ] Ensure `isActive` updates immediately when admin changes it

### Testing
- [ ] Test hash validation
- [ ] Test account linking
- [ ] Test subscription activation
- [ ] Test admin deactivation → verify bot sees `isActive: false`
- [ ] Test admin activation → verify bot sees `isActive: true`
- [ ] Test expiration handling

---

## Example Implementation (Node.js/Express)

```javascript
// GET /api/users/by-hash/:hash
app.get('/api/users/by-hash/:hash', async (req, res) => {
  const { hash } = req.params;
  
  // Validate format
  if (!/^[a-zA-Z]{12}[0-9]{12}$/.test(hash)) {
    return res.status(400).json({ error: 'Invalid hash format' });
  }
  
  try {
    const user = await db.users.findOne({ where: { hash } });
    
    if (!user) {
      return res.status(404).json({ error: 'User not found' });
    }
    
    // Check subscription status
    const subscription = await db.subscriptions.findOne({
      where: { userId: user.id }
    });
    
    res.json({
      userId: user.id,
      hash: user.hash,
      lastSeen: user.lastSeen,
      isSubscribed: subscription?.isActive || false
    });
  } catch (error) {
    res.status(500).json({ error: 'Internal server error' });
  }
});

// POST /api/subscription/link-telegram
app.post('/api/subscription/link-telegram', async (req, res) => {
  const { startParam, telegramUserId, telegramUsername, hash } = req.body;
  
  let userId;
  
  // If hash provided, use it
  if (hash) {
    const user = await db.users.findOne({ where: { hash } });
    if (!user) {
      return res.status(404).json({ error: 'User not found' });
    }
    userId = user.id;
  } else if (startParam) {
    // Decode startParam (base64url)
    try {
      userId = Buffer.from(startParam, 'base64url').toString('utf-8');
    } catch (e) {
      return res.status(400).json({ error: 'Invalid start parameter' });
    }
  } else {
    return res.status(400).json({ error: 'Missing required fields' });
  }
  
  try {
    // Create or update subscription record
    const [subscription] = await db.subscriptions.upsert({
      userId,
      telegramUserId,
      telegramUsername,
      telegramLinked: true,
      isActive: false,  // Not active until payment
      createdAt: Date.now(),
      lastChecked: Date.now()
    }, {
      returning: true
    });
    
    res.json({
      ok: true,
      userId,
      telegramLinked: true
    });
  } catch (error) {
    res.status(500).json({ error: 'Internal server error' });
  }
});

// GET /api/subscription/telegram/:telegramUserId
// CRITICAL: This must return real-time status (respects admin changes)
app.get('/api/subscription/telegram/:telegramUserId', async (req, res) => {
  const { telegramUserId } = req.params;
  
  try {
    const subscription = await db.subscriptions.findOne({
      where: { telegramUserId: parseInt(telegramUserId) }
    });
    
    if (!subscription) {
      return res.status(404).json({ error: 'Subscription not found' });
    }
    
    // Check if expired
    let isActive = subscription.isActive;
    if (isActive && subscription.expiresAt) {
      const now = Date.now();
      if (subscription.expiresAt <= now) {
        isActive = false;
        // Update database if expired
        await subscription.update({ isActive: false });
      }
    }
    
    // CRITICAL: Return current state from database (respects admin changes)
    res.json({
      userId: subscription.userId,
      isActive: isActive,  // Must reflect admin panel changes
      expiresAt: subscription.expiresAt,
      telegramUsername: subscription.telegramUsername
    });
  } catch (error) {
    res.status(500).json({ error: 'Internal server error' });
  }
});

// POST /api/subscription/activate
app.post('/api/subscription/activate', async (req, res) => {
  const { telegramUserId, hash, durationDays = 30 } = req.body;
  
  if (!telegramUserId) {
    return res.status(400).json({ error: 'Missing telegramUserId' });
  }
  
  try {
    let subscription;
    
    // If hash provided, find by hash
    if (hash) {
      const user = await db.users.findOne({ where: { hash } });
      if (!user) {
        return res.status(404).json({ error: 'User not found' });
      }
      subscription = await db.subscriptions.findOne({
        where: { userId: user.id }
      });
    } else {
      // Find by telegramUserId
      subscription = await db.subscriptions.findOne({
        where: { telegramUserId: parseInt(telegramUserId) }
      });
    }
    
    if (!subscription) {
      return res.status(404).json({
        error: 'Subscription not found. User must start bot first.'
      });
    }
    
    // Calculate expiration
    const expiresAt = Date.now() + (durationDays * 24 * 60 * 60 * 1000);
    
    // Activate subscription
    await subscription.update({
      isActive: true,
      expiresAt,
      lastChecked: Date.now()
    });
    
    res.json({
      ok: true,
      userId: subscription.userId,
      isActive: true,
      expiresAt
    });
  } catch (error) {
    res.status(500).json({ error: 'Internal server error' });
  }
});
```

---

## Admin Panel Integration Example

```javascript
// Admin deactivates user
async function adminDeactivateUser(telegramUserId) {
  await db.subscriptions.update(
    { isActive: false },
    { where: { telegramUserId } }
  );
  // Bot will see this immediately on next API call
}

// Admin activates user
async function adminActivateUser(telegramUserId, durationDays = 30) {
  const expiresAt = Date.now() + (durationDays * 24 * 60 * 60 * 1000);
  await db.subscriptions.update(
    { isActive: true, expiresAt },
    { where: { telegramUserId } }
  );
  // Bot will see this immediately on next API call
}
```

---

## Testing

### Test Hash Validation
```bash
curl http://localhost:4000/api/users/by-hash/ABC123XYZ456DEF789GHI012
```

### Test Account Linking
```bash
curl -X POST http://localhost:4000/api/subscription/link-telegram \
  -H "Content-Type: application/json" \
  -d '{
    "hash": "ABC123XYZ456DEF789GHI012",
    "telegramUserId": 123456789,
    "telegramUsername": "testuser"
  }'
```

### Test Subscription Check (Real-time)
```bash
# Check status
curl http://localhost:4000/api/subscription/telegram/123456789

# Admin deactivates user in panel
# Check again - should see isActive: false
curl http://localhost:4000/api/subscription/telegram/123456789
```

### Test Subscription Activation
```bash
curl -X POST http://localhost:4000/api/subscription/activate \
  -H "Content-Type: application/json" \
  -d '{
    "telegramUserId": 123456789,
    "hash": "ABC123XYZ456DEF789GHI012",
    "durationDays": 30
  }'
```

---

## Important Notes

1. **Real-time Status**: The `GET /api/subscription/telegram/{telegramUserId}` endpoint is called frequently by the bot. Always return the current state from your database.

2. **Admin Changes**: When admin deactivates/activates a user, the database must be updated immediately. The bot will see the change on the next API call.

3. **Expiration Handling**: Check `expiresAt` - if it's in the past, `isActive` should be `false`.

4. **Performance**: Optimize the subscription check endpoint - it's called frequently. Use database indexes.

5. **Error Handling**: Return proper HTTP status codes and error messages.

6. **Hash Format**: Hash must be exactly 24 characters (12 letters + 12 numbers).

---

## Support

For bot-side implementation, refer to:
- `bot.py` - Current bot implementation
- `BOT_API_DOCUMENTATION.md` - Full bot API documentation
- `INTEGRATION.md` - Integration guide

