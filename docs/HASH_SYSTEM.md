# Hash Registration System

The bot now requires users to enter a registration hash before accessing features.

## How It Works

### 1. User Flow

1. **User clicks /start** → Bot asks for hash
2. **User enters hash** → Bot validates with map website API
3. **If valid** → User can access bot features
4. **If invalid** → Error message, asks to try again

### 2. Hash Format

- **Length**: 24 characters
- **Format**: 12 letters + 12 numbers
- **Example**: `abcdefghijkl123456789012`

### 3. Hash Validation

The bot validates hashes with the map website API:
- **Endpoint**: `GET /api/subscription/validate-hash/{hash}`
- **Success (200)**: Hash is valid, user can proceed
- **Not Found (404)**: Hash is incorrect or non-existing
- **Error**: Connection/server issues

### 4. Hash Storage

- Hashes are stored locally in `user_hashes.json`
- Format: `{"telegram_user_id": "hash_code"}`
- Once validated, user doesn't need to enter hash again

### 5. Subscription with Hash

When user pays for subscription:
- Bot includes the hash in the activation request
- Map website knows which user (by hash) made the payment
- Subscription is linked to the hash/user

## API Integration

### Map Website API Endpoints Required

#### Validate Hash
```
GET /api/subscription/validate-hash/{hash}
```

**Response (200 OK):**
```json
{
  "valid": true,
  "userId": "user_123",
  "message": "Hash validated successfully"
}
```

**Response (404 Not Found):**
```json
{
  "error": "Hash not found"
}
```

#### Activate Subscription (Updated)
```
POST /api/subscription/activate
```

**Request Body:**
```json
{
  "telegramUserId": 123456789,
  "hash": "abcdefghijkl123456789012",  // Optional, included if available
  "durationDays": 30
}
```

## Error Messages

- **Invalid format**: "Invalid hash format. Hash must be 24 characters (12 letters + 12 numbers)."
- **Invalid/non-existing hash**: "This hash is either incorrect or non-existing"
- **Connection error**: "Error connecting to server. Please try again later."

## Files

- `bot.py` - Main bot code with hash validation
- `user_hashes.json` - Stores validated hashes (auto-generated)

## Testing

1. Generate a hash on the website (12 letters + 12 numbers)
2. Start the bot: `/start`
3. Enter the hash when prompted
4. If valid, you'll see the main menu
5. If invalid, you'll see an error message

## Notes

- Once a hash is validated, it's saved and user doesn't need to enter it again
- Hash is included in subscription activation so website knows which user paid
- All other bot functions remain unchanged

