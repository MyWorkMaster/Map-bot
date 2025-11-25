# Bot & Map Website Integration

The Telegram bot is now fully integrated with the Anomonus Map Website API.

## Configuration

### Map Website API URL

The bot connects to the map website API. By default, it uses:
```
http://localhost:4000
```

To change this, set the environment variable:
```bash
export MAP_API_URL=http://your-map-server.com
```

Or in production, set it when running:
```bash
MAP_API_URL=https://your-domain.com python bot.py
```

## How It Works

### 1. Subscription Checking
- When a user clicks "Buy subscription", the bot checks both:
  - Local storage (backup)
  - Map website API (primary source)
- If user is subscribed in either, they see "You already subscribed"

### 2. Payment Processing
When a user pays with Telegram Stars:
1. Payment is received by the bot
2. Bot calls map website API: `POST /api/subscription/activate`
3. Map website activates the subscription (30 days)
4. Bot also saves locally as backup
5. User receives confirmation message

### 3. API Endpoints

#### Bot API (Port 5000)
- `GET /api/check-subscription?user_id=<id>` - Checks both local and map API
- `POST /api/subscribe` - Manually subscribe (for testing)
- `GET /api/user-info?user_id=<id>` - Get user info
- `GET /api/health` - Health check

#### Map Website API (Port 4000)
- `GET /api/subscription/telegram/:telegramUserId` - Check subscription by Telegram ID
- `POST /api/subscription/activate` - Activate subscription (called by bot)
- `GET /api/subscription/check/:userId` - Check subscription by website userId

## Integration Flow

```
User pays in Telegram Bot
    ↓
Bot receives payment
    ↓
Bot calls: POST /api/subscription/activate
    {
      "telegramUserId": 123456789,
      "durationDays": 30
    }
    ↓
Map Website activates subscription
    ↓
User can now access premium features on map website
```

## Requirements

1. **Map Website Server** must be running on port 4000 (or configured URL)
2. **Bot Server** runs on port 5000
3. Both servers must be able to communicate (same network or public URLs)

## Testing

1. Start the map website server (port 4000)
2. Start the bot: `python bot.py`
3. Test payment in Telegram bot
4. Check subscription status on map website

## Troubleshooting

### Bot can't connect to map API
- Check if map website server is running
- Verify `MAP_API_URL` is correct
- Check firewall/network settings
- Look for error messages in bot console

### Subscription not activating
- Check bot console for API errors
- Verify map website API is accessible
- Check map website server logs
- Ensure user has started the bot at least once (required for linking)

## Notes

- The bot maintains local storage as a backup
- If map API is unavailable, bot falls back to local storage
- Subscriptions are synced in real-time with map website
- Map website is the source of truth for subscription status

