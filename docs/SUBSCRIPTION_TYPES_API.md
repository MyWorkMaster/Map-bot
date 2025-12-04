# Subscription Types API Documentation

This document describes the API endpoints and data structures needed to support multiple subscription types in the Anomonus bot.

## Subscription Types

The bot supports 4 subscription types:

1. **1 Month** - 115 Telegram Stars - 30 days
2. **6 Months** - 520 Telegram Stars - 180 days
3. **1 Year** - 830 Telegram Stars - 365 days
4. **Lifetime** - 2500 Telegram Stars - 99999 days (permanent)

---

## Updated Endpoint: Activate Subscription

**Endpoint:** `POST /api/subscription/activate`

Now includes `subscriptionType` field to identify which plan was purchased.

**Request Body:**
```json
{
  "telegramUserId": 123456789,
  "hash": "ABC123XYZ456DEF789GHI012",  // Optional
  "durationDays": 30,  // Optional, defaults to 30
  "subscriptionType": "1month"  // Optional: "1month", "6month", "12month", "lifetime"
}
```

**Subscription Type Values:**
- `"1month"` - 1 Month subscription (30 days)
- `"6month"` - 6 Months subscription (180 days)
- `"12month"` - 1 Year subscription (365 days)
- `"lifetime"` - Lifetime subscription (99999 days or use special flag)

**Response (200 OK):**
```json
{
  "ok": true,
  "userId": "user_1762513365727_w3s94luf2",
  "isActive": true,
  "expiresAt": 1735689600000,  // Unix timestamp in milliseconds
  "subscriptionType": "1month"  // Type of subscription activated
}
```

**Example Requests:**

```bash
# 1 Month subscription
curl -X POST http://localhost:4000/api/subscription/activate \
  -H "Content-Type: application/json" \
  -d '{
    "telegramUserId": 123456789,
    "hash": "ABC123XYZ456DEF789GHI012",
    "durationDays": 30,
    "subscriptionType": "1month"
  }'

# 6 Months subscription
curl -X POST http://localhost:4000/api/subscription/activate \
  -H "Content-Type: application/json" \
  -d '{
    "telegramUserId": 123456789,
    "durationDays": 180,
    "subscriptionType": "6month"
  }'

# 1 Year subscription
curl -X POST http://localhost:4000/api/subscription/activate \
  -H "Content-Type: application/json" \
  -d '{
    "telegramUserId": 123456789,
    "durationDays": 365,
    "subscriptionType": "12month"
  }'

# Lifetime subscription
curl -X POST http://localhost:4000/api/subscription/activate \
  -H "Content-Type: application/json" \
  -d '{
    "telegramUserId": 123456789,
    "durationDays": 99999,
    "subscriptionType": "lifetime"
  }'
```

---

## Implementation Details

### Handling Lifetime Subscriptions

For lifetime subscriptions, you have two options:

**Option 1: Use very large expiration date**
```javascript
if (subscriptionType === 'lifetime') {
  expiresAt = Date.now() + (99999 * 24 * 60 * 60 * 1000); // ~274 years
}
```

**Option 2: Use special flag (Recommended)**
```javascript
// In database
isLifetime: true  // Special flag for lifetime subscriptions
expiresAt: null   // No expiration

// When checking subscription
if (subscription.isLifetime) {
  isActive = true;  // Always active
} else {
  isActive = subscription.isActive && subscription.expiresAt > Date.now();
}
```

### Database Schema Update

```sql
ALTER TABLE subscriptions ADD COLUMN subscription_type VARCHAR(20);
ALTER TABLE subscriptions ADD COLUMN is_lifetime BOOLEAN DEFAULT false;

-- Index for subscription type
CREATE INDEX idx_subscriptions_type ON subscriptions(subscription_type);
```

### Subscription Type Mapping

| Type | Stars | Duration Days | Database Value |
|------|-------|---------------|----------------|
| 1 Month | 115 | 30 | `"1month"` |
| 6 Months | 520 | 180 | `"6month"` |
| 1 Year | 830 | 365 | `"12month"` |
| Lifetime | 2500 | 99999 | `"lifetime"` |

---

## Example Implementation (Node.js/Express)

```javascript
app.post('/api/subscription/activate', async (req, res) => {
  const { telegramUserId, hash, durationDays = 30, subscriptionType } = req.body;
  
  if (!telegramUserId) {
    return res.status(400).json({ error: 'Missing telegramUserId' });
  }
  
  try {
    let userId;
    
    // Find user by hash or telegramUserId
    if (hash) {
      const user = await db.users.findOne({ where: { hash } });
      if (user) userId = user.id;
    }
    
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
    
    // Calculate expiration
    let expiresAt;
    let isLifetime = false;
    
    if (subscriptionType === 'lifetime') {
      // Lifetime subscription - no expiration
      expiresAt = null;
      isLifetime = true;
    } else {
      // Calculate expiration based on durationDays
      expiresAt = Date.now() + (durationDays * 24 * 60 * 60 * 1000);
    }
    
    // Activate subscription
    const [subscription] = await db.subscriptions.upsert({
      userId,
      telegramUserId,
      hash,
      subscriptionType: subscriptionType || '1month',
      isLifetime,
      isActive: true,
      expiresAt,
      lastChecked: Date.now()
    }, {
      returning: true
    });
    
    res.json({
      ok: true,
      userId,
      isActive: true,
      expiresAt,
      subscriptionType: subscription.subscriptionType
    });
  } catch (error) {
    res.status(500).json({ error: 'Internal server error' });
  }
});
```

---

## Checking Subscription Status

When checking subscription status, handle lifetime subscriptions:

```javascript
app.get('/api/subscription/telegram/:telegramUserId', async (req, res) => {
  const { telegramUserId } = req.params;
  
  const subscription = await db.subscriptions.findOne({
    where: { telegramUserId: parseInt(telegramUserId) }
  });
  
  if (!subscription) {
    return res.status(404).json({ error: 'Subscription not found' });
  }
  
  // Check if active
  let isActive = subscription.isActive;
  
  if (isActive) {
    // Lifetime subscriptions are always active
    if (subscription.isLifetime) {
      isActive = true;
    } else if (subscription.expiresAt) {
      // Check expiration
      const now = Date.now();
      if (subscription.expiresAt <= now) {
        isActive = false;
        // Update database
        await subscription.update({ isActive: false });
      }
    }
  }
  
  res.json({
    userId: subscription.userId,
    isActive,
    expiresAt: subscription.expiresAt,
    subscriptionType: subscription.subscriptionType,
    isLifetime: subscription.isLifetime,
    telegramUsername: subscription.telegramUsername
  });
});
```

---

## Subscription Type Constants

For reference, here are the subscription type constants used by the bot:

```javascript
const SUBSCRIPTION_TYPES = {
  ONE_MONTH: {
    type: '1month',
    stars: 115,
    days: 30
  },
  SIX_MONTHS: {
    type: '6month',
    stars: 520,
    days: 180
  },
  ONE_YEAR: {
    type: '12month',
    stars: 830,
    days: 365
  },
  LIFETIME: {
    type: 'lifetime',
    stars: 2500,
    days: 99999
  }
};
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

---

## Important Notes

1. **Lifetime Subscriptions**: Use `isLifetime: true` flag or `expiresAt: null` to mark lifetime subscriptions. When checking status, lifetime subscriptions should always return `isActive: true` (unless admin deactivated).

2. **Subscription Type**: Store the `subscriptionType` field to track which plan the user purchased.

3. **Duration Days**: The bot sends `durationDays` but for lifetime, you may want to use a special flag instead of relying on the large number.

4. **Backward Compatibility**: If `subscriptionType` is not provided, default to `"1month"` (30 days).

5. **Admin Panel**: When displaying subscriptions in admin panel, show the subscription type clearly.

---

## Database Migration

```sql
-- Add subscription type column
ALTER TABLE subscriptions 
ADD COLUMN subscription_type VARCHAR(20) DEFAULT '1month';

-- Add lifetime flag
ALTER TABLE subscriptions 
ADD COLUMN is_lifetime BOOLEAN DEFAULT false;

-- Update existing subscriptions (if any)
UPDATE subscriptions 
SET subscription_type = '1month' 
WHERE subscription_type IS NULL;

-- Create index
CREATE INDEX idx_subscriptions_type ON subscriptions(subscription_type);
```

---

## Response Format

The subscription status response should include the type:

```json
{
  "userId": "user_123",
  "isActive": true,
  "expiresAt": 1735689600000,
  "subscriptionType": "6month",
  "isLifetime": false,
  "telegramUsername": "username"
}
```

For lifetime subscriptions:
```json
{
  "userId": "user_123",
  "isActive": true,
  "expiresAt": null,
  "subscriptionType": "lifetime",
  "isLifetime": true,
  "telegramUsername": "username"
}
```

