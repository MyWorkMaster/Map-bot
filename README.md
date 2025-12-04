# Anomonus Telegram Bot

A Telegram bot for managing subscriptions and user accounts for the Anomonus Map service.

## Project Structure

```
ANOMONUS-MAP-BOT/
├── bot.py                 # Main bot application
├── requirements.txt       # Python dependencies
├── .gitignore            # Git ignore rules
├── README.md             # This file
│
├── data/                 # Data storage directory
│   ├── subscribed_users.json    # Subscribed users (backup/reference)
│   └── user_hashes.json         # User hash mappings
│
└── docs/                 # Documentation directory
    ├── BOT_API_DOCUMENTATION.md          # Bot API integration guide
    ├── SUBSCRIPTION_TYPES_API.md         # Subscription types API docs
    ├── DEPLOYMENT.md                     # Deployment guide for Ubuntu
    ├── API_DOCUMENTATION.md              # General API documentation
    ├── API_DOCUMENTATION copy.md         # API documentation (backup)
    ├── BOT_CODE_CHANGES_REQUIRED.md      # Code change requirements
    ├── HASH_SYSTEM.md                    # Hash system documentation
    ├── INTEGRATION.md                    # Integration guide
    ├── MAP_WEBSITE_API_REQUIREMENTS.md   # Map website API requirements
    └── WEBSITE_API_IMPLEMENTATION.md     # Website API implementation guide
```

## Features

- **Subscription Management**: 4 subscription types (1 month, 6 months, 1 year, lifetime)
- **Telegram Stars Payments**: Secure payment processing via Telegram Stars
- **Hash-based Registration**: User validation and account linking via hash codes
- **Map Website Integration**: Real-time subscription status sync with map website
- **REST API Server**: Flask-based API for website integration

## Quick Start

### Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment variables:
   ```bash
   export MAP_API_URL="https://map.anomonus.com"  # or http://localhost:4000 for dev
   ```

4. Run the bot:
   ```bash
   python bot.py
   ```

### Configuration

- **Bot Token**: Set `BOT_TOKEN` in `bot.py` (use `REAL_BOT_TOKEN` for production)
- **Map API URL**: Set via `MAP_API_URL` environment variable (defaults to `http://localhost:4000`)

## Documentation

All documentation is located in the `docs/` directory:

- **[BOT_API_DOCUMENTATION.md](docs/BOT_API_DOCUMENTATION.md)** - Complete API integration guide
- **[SUBSCRIPTION_TYPES_API.md](docs/SUBSCRIPTION_TYPES_API.md)** - Subscription types API documentation
- **[DEPLOYMENT.md](docs/DEPLOYMENT.md)** - Ubuntu deployment guide

## Subscription Types

| Type | Stars | Duration |
|------|-------|----------|
| 1 Month | 115 | 30 days |
| 6 Months | 520 | 180 days |
| 1 Year | 830 | 365 days |
| Lifetime | 2500 | Permanent |

## Bot Commands

- `/start` - Start the bot and enter hash for registration
- `/terms` - View Terms of Use
- `/paysupport` - Payment and subscription support

## Main Menu Buttons

- **Buy subscription** - Purchase a subscription plan
- **About us** - Learn about Anomonus
- **How to use Map** - Map usage guide
- **Subscription Plans** - View all subscription plans

## Data Storage

- **Location**: `data/` directory
- **Files**:
  - `subscribed_users.json` - Backup/reference of subscribed users
  - `user_hashes.json` - Telegram user ID to hash mappings

**Note**: The map website API is the source of truth for subscription status. Local files are for backup/reference only.

## API Endpoints

The bot runs a Flask API server on port 5000 (default) with the following endpoints:

- `GET /api/check-subscription?telegramUserId=<id>` - Check subscription status
- `POST /api/subscribe` - Subscribe a user (legacy)
- `GET /api/user-info?telegramUserId=<id>` - Get user information
- `GET /api/health` - Health check

## Development

### Testing

Use the test bot token for development:
```python
TEST_BOT_TOKEN = "8164339923:AAHw-wqosK75xbNs8_SRexwp3HTE4bRoq4w"
```

### Production

Switch to real bot token:
```python
BOT_TOKEN = REAL_BOT_TOKEN
```

## Deployment

See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed Ubuntu deployment instructions.

## License

Proprietary - Anomonus

## Support

For issues or questions, contact the development team.

