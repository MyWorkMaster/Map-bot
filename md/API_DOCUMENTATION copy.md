# Anomonus Map API Documentation

## Base URL

```
http://localhost:4000
```

Or in production:
```
https://your-domain.com
```

## Authentication

### Admin Endpoints
Most admin endpoints require authentication using a Bearer token obtained from the login endpoint.

**Header Format:**
```
Authorization: Bearer <token>
```

**Query Parameter Alternative:**
```
?token=<token>
```

---

## Endpoints

### Health Check

#### `GET /api/health`
Check if the API server is running.

**Response:**
```json
{
  "ok": true
}
```

---

## Incidents

### Get Active Incidents

#### `GET /api/incidents`
Retrieve all active incidents (police reports and car crashes).

**Query Parameters:**
- `userId` (optional): User ID for tracking user activity

**Headers:**
- `X-User-Id` (optional): User ID for tracking user activity

**Response:**
```json
[
  {
    "id": "abc123def456",
    "type": "police",
    "lat": 40.7128,
    "lon": -74.0060,
    "createdAt": "2025-01-15T10:30:00.000Z",
    "expiresAt": "2025-01-15T12:30:00.000Z",
    "votes": {
      "yes": ["user1", "user2"],
      "no": ["user3"]
    }
  }
]
```

**Example:**
```bash
curl http://localhost:4000/api/incidents?userId=user_123
```

---

### Report Incident

#### `POST /api/admin/report`
Report a new incident (police or car crash).

**Query Parameters:**
- `userId` (optional): User ID for tracking

**Headers:**
- `X-User-Id` (optional): User ID for tracking
- `Content-Type: application/json`

**Request Body:**
```json
{
  "type": "police",  // or "crash"
  "lat": 40.7128,
  "lon": -74.0060
}
```

**Response:**
```json
{
  "ok": true
}
```

**Error Responses:**
- `400 Bad Request`: Invalid type or coordinates
  ```json
  {
    "error": "Invalid type"
  }
  ```

**Example:**
```bash
curl -X POST http://localhost:4000/api/admin/report?userId=user_123 \
  -H "Content-Type: application/json" \
  -H "X-User-Id: user_123" \
  -d '{
    "type": "police",
    "lat": 40.7128,
    "lon": -74.0060
  }'
```

---

### Vote on Incident

#### `POST /api/incidents/vote`
Vote on an incident (confirm or deny it exists).

**Request Body:**
```json
{
  "incidentId": "abc123def456",
  "vote": "yes",  // or "no"
  "userId": "user_123"
}
```

**Response:**
```json
{
  "ok": true,
  "removed": false  // true if incident was removed due to too many "no" votes
}
```

**Error Responses:**
- `400 Bad Request`: Invalid request
  ```json
  {
    "error": "Invalid request"
  }
  ```

**Example:**
```bash
curl -X POST http://localhost:4000/api/incidents/vote \
  -H "Content-Type: application/json" \
  -d '{
    "incidentId": "abc123def456",
    "vote": "yes",
    "userId": "user_123"
  }'
```

---

### Check if User Voted

#### `GET /api/incidents/:id/voted/:userId`
Check if a user has already voted on a specific incident.

**Path Parameters:**
- `id`: Incident ID
- `userId`: User ID

**Response:**
```json
{
  "voted": true
}
```

**Example:**
```bash
curl http://localhost:4000/api/incidents/abc123def456/voted/user_123
```

---

## Admin Endpoints

### Admin Login

#### `POST /api/admin/login`
Authenticate as an admin user.

**Request Body:**
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**Response:**
```json
{
  "token": "admin_1705320000_abc123def",
  "username": "admin"
}
```

**Error Responses:**
- `401 Unauthorized`: Invalid credentials
  ```json
  {
    "error": "Invalid credentials"
  }
  ```

**Example:**
```bash
curl -X POST http://localhost:4000/api/admin/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }'
```

**Note:** Default credentials can be changed via environment variables:
- `ADMIN_USERNAME`
- `ADMIN_PASSWORD`

---

### Get Statistics

#### `GET /api/admin/statistics`
Get comprehensive statistics about the system.

**Authentication:** Required (Bearer token)

**Response:**
```json
{
  "totalUsers": 150,
  "totalIncidents": 45,
  "totalPoliceReports": 30,
  "totalCrashReports": 15,
  "totalSpeedCameras": 2500,
  "incidents": [
    {
      "id": "abc123",
      "type": "police",
      "lat": 40.7128,
      "lon": -74.0060,
      "createdAt": "2025-01-15T10:30:00.000Z",
      "expiresAt": "2025-01-15T12:30:00.000Z",
      "votes": {
        "yes": ["user1"],
        "no": []
      }
    }
  ]
}
```

**Example:**
```bash
curl http://localhost:4000/api/admin/statistics \
  -H "Authorization: Bearer admin_1705320000_abc123def"
```

---

### Get All Incidents (Admin)

#### `GET /api/admin/incidents`
Get all incidents (including expired ones).

**Authentication:** Required (Bearer token)

**Response:**
```json
[
  {
    "id": "abc123",
    "type": "police",
    "lat": 40.7128,
    "lon": -74.0060,
    "createdAt": "2025-01-15T10:30:00.000Z",
    "expiresAt": "2025-01-15T12:30:00.000Z",
    "votes": {
      "yes": ["user1"],
      "no": []
    }
  }
]
```

**Example:**
```bash
curl http://localhost:4000/api/admin/incidents \
  -H "Authorization: Bearer admin_1705320000_abc123def"
```

---

### Get Incident by ID (Admin)

#### `GET /api/admin/incidents/:id`
Get a specific incident by ID.

**Authentication:** Required (Bearer token)

**Path Parameters:**
- `id`: Incident ID

**Response:**
```json
{
  "id": "abc123",
  "type": "police",
  "lat": 40.7128,
  "lon": -74.0060,
  "createdAt": "2025-01-15T10:30:00.000Z",
  "expiresAt": "2025-01-15T12:30:00.000Z",
  "votes": {
    "yes": ["user1"],
    "no": []
  }
}
```

**Error Responses:**
- `404 Not Found`: Incident not found
  ```json
  {
    "error": "Incident not found"
  }
  ```

**Example:**
```bash
curl http://localhost:4000/api/admin/incidents/abc123 \
  -H "Authorization: Bearer admin_1705320000_abc123def"
```

---

### Delete Incident (Admin)

#### `DELETE /api/admin/incidents/:id`
Delete an incident by ID.

**Authentication:** Required (Bearer token)

**Path Parameters:**
- `id`: Incident ID

**Response:**
```json
{
  "ok": true
}
```

**Error Responses:**
- `404 Not Found`: Incident not found
  ```json
  {
    "error": "Incident not found"
  }
  ```

**Example:**
```bash
curl -X DELETE http://localhost:4000/api/admin/incidents/abc123 \
  -H "Authorization: Bearer admin_1705320000_abc123def"
```

---

### Add Vote Manually (Admin)

#### `POST /api/admin/votes/add`
Manually add a vote to an incident (admin override).

**Authentication:** Required (Bearer token)

**Request Body:**
```json
{
  "incidentId": "abc123def456",
  "vote": "yes",  // or "no"
  "userId": "user_123",
  "token": "admin_token"  // Alternative to Authorization header
}
```

**Response:**
```json
{
  "ok": true,
  "removed": false
}
```

**Error Responses:**
- `400 Bad Request`: Invalid request
- `404 Not Found`: Incident not found

**Example:**
```bash
curl -X POST http://localhost:4000/api/admin/votes/add \
  -H "Authorization: Bearer admin_1705320000_abc123def" \
  -H "Content-Type: application/json" \
  -d '{
    "incidentId": "abc123def456",
    "vote": "yes",
    "userId": "user_123"
  }'
```

---

### Remove Vote Manually (Admin)

#### `POST /api/admin/votes/remove`
Manually remove a vote from an incident.

**Authentication:** Required (Bearer token)

**Request Body:**
```json
{
  "incidentId": "abc123def456",
  "vote": "yes",  // or "no"
  "userId": "user_123",
  "token": "admin_token"  // Alternative to Authorization header
}
```

**Response:**
```json
{
  "ok": true
}
```

**Error Responses:**
- `400 Bad Request`: Invalid request
- `404 Not Found`: Incident not found

**Example:**
```bash
curl -X POST http://localhost:4000/api/admin/votes/remove \
  -H "Authorization: Bearer admin_1705320000_abc123def" \
  -H "Content-Type: application/json" \
  -d '{
    "incidentId": "abc123def456",
    "vote": "yes",
    "userId": "user_123"
  }'
```

---

## Speed Cameras

### Report Speed Cameras

#### `POST /api/speed-cameras/report`
Report speed cameras from the frontend (used for tracking).

**Request Body:**
```json
{
  "cameras": [
    {
      "lat": 40.7128,
      "lon": -74.0060
    },
    {
      "lat": 40.7130,
      "lon": -74.0062
    }
  ]
}
```

**Response:**
```json
{
  "ok": true
}
```

**Error Responses:**
- `400 Bad Request`: Invalid request
  ```json
  {
    "error": "Invalid request"
  }
  ```

**Example:**
```bash
curl -X POST http://localhost:4000/api/speed-cameras/report \
  -H "Content-Type: application/json" \
  -d '{
    "cameras": [
      {"lat": 40.7128, "lon": -74.0060}
    ]
  }'
```

---

### Get All Speed Cameras (Admin)

#### `GET /api/admin/speed-cameras`
Get all speed cameras in the system.

**Authentication:** Required (Bearer token)

**Response:**
```json
{
  "cameras": [
    {
      "id": "camera_123",
      "lat": 40.7128,
      "lon": -74.0060,
      "source": "overpass",
      "createdAt": 1705320000000
    }
  ],
  "count": 2500,
  "sample": [
    {
      "lat": 40.7128,
      "lon": -74.0060,
      "id": "camera_123"
    }
  ]
}
```

**Example:**
```bash
curl http://localhost:4000/api/admin/speed-cameras \
  -H "Authorization: Bearer admin_1705320000_abc123def"
```

---

## Subscriptions

### Check Subscription Status

#### `GET /api/subscription/check/:userId`
Check if a user has an active subscription.

**Path Parameters:**
- `userId`: User ID (from localStorage)

**Response:**
```json
{
  "isActive": true,
  "expiresAt": 1735689600000,  // Unix timestamp in milliseconds
  "telegramLinked": true
}
```

**Example:**
```bash
curl http://localhost:4000/api/subscription/check/user_1762513365727_w3s94luf2
```

---

### Get Telegram Bot Link

#### `GET /api/subscription/bot-link/:userId`
Get the Telegram bot deep link for a user.

**Path Parameters:**
- `userId`: User ID

**Response:**
```json
{
  "botLink": "https://t.me/anomonusalltestbot?start=dXNlcl8xNzYyNTEzMzY1NzI3X3czczk0bHVmMg"
}
```

**Example:**
```bash
curl http://localhost:4000/api/subscription/bot-link/user_1762513365727_w3s94luf2
```

---

### Link Telegram User

#### `POST /api/subscription/link-telegram`
Link a Telegram user to a website user (called by Telegram bot).

**Request Body:**
```json
{
  "startParam": "dXNlcl8xNzYyNTEzMzY1NzI3X3czczk0bHVmMg",  // Base64url encoded userId
  "telegramUserId": 123456789,
  "telegramUsername": "username"  // Optional
}
```

**Response:**
```json
{
  "ok": true,
  "userId": "user_1762513365727_w3s94luf2",
  "telegramLinked": true
}
```

**Error Responses:**
- `400 Bad Request`: Missing required fields or invalid start parameter
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

### Activate Subscription

#### `POST /api/subscription/activate`
Activate a user's subscription (called by Telegram bot after payment).

**Request Body:**
```json
{
  "telegramUserId": 123456789,
  "durationDays": 30  // Optional, defaults to 30
}
```

**Response:**
```json
{
  "ok": true,
  "userId": "user_1762513365727_w3s94luf2",
  "isActive": true,
  "expiresAt": 1735689600000
}
```

**Error Responses:**
- `400 Bad Request`: Missing telegramUserId
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

### Admin: Activate Subscription

#### `POST /api/subscription/admin/activate`
Activate a subscription directly by userId (for testing/admin use).

**Request Body:**
```json
{
  "userId": "user_1762513365727_w3s94luf2",
  "durationDays": 365  // Optional, defaults to 365 (1 year)
}
```

**Response:**
```json
{
  "ok": true,
  "userId": "user_1762513365727_w3s94luf2",
  "isActive": true,
  "expiresAt": 1786867200000
}
```

**Error Responses:**
- `400 Bad Request`: Missing userId

**Example:**
```bash
curl -X POST http://localhost:4000/api/subscription/admin/activate \
  -H "Content-Type: application/json" \
  -d '{
    "userId": "user_1762513365727_w3s94luf2",
    "durationDays": 365
  }'
```

---

### Get Subscription by Telegram User ID

#### `GET /api/subscription/telegram/:telegramUserId`
Get subscription details by Telegram user ID (for bot to check status).

**Path Parameters:**
- `telegramUserId`: Telegram user ID (number)

**Response:**
```json
{
  "userId": "user_1762513365727_w3s94luf2",
  "isActive": true,
  "expiresAt": 1735689600000,
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

### Get All Subscriptions (Admin)

#### `GET /api/admin/subscriptions`
Get all subscriptions in the system.

**Authentication:** Required (Bearer token)

**Response:**
```json
[
  {
    "userId": "user_1762513365727_w3s94luf2",
    "telegramUserId": 123456789,
    "telegramUsername": "username",
    "isActive": true,
    "expiresAt": 1735689600000,
    "createdAt": 1705320000000,
    "lastChecked": 1705320000000
  }
]
```

**Example:**
```bash
curl http://localhost:4000/api/admin/subscriptions \
  -H "Authorization: Bearer admin_1705320000_abc123def"
```

---

## Error Codes

| Status Code | Description |
|------------|-------------|
| 200 | Success |
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Invalid credentials |
| 403 | Forbidden - Admin access required |
| 404 | Not Found - Resource not found |
| 500 | Internal Server Error |

---

## Data Models

### Incident
```typescript
{
  id: string;                    // Unique incident ID
  type: "police" | "crash";      // Incident type
  lat: number;                   // Latitude
  lon: number;                   // Longitude
  createdAt: string;             // ISO 8601 timestamp
  expiresAt?: string;            // ISO 8601 timestamp (optional)
  votes?: {                      // Voting data (optional)
    yes: string[];               // Array of user IDs who voted "yes"
    no: string[];                // Array of user IDs who voted "no"
  };
}
```

### Subscription
```typescript
{
  userId: string;                // Website user ID
  telegramUserId?: number;        // Telegram user ID (optional)
  telegramUsername?: string;      // Telegram username (optional)
  isActive: boolean;             // Whether subscription is active
  expiresAt?: number;            // Unix timestamp in milliseconds (optional)
  createdAt: number;             // Unix timestamp in milliseconds
  lastChecked: number;           // Unix timestamp in milliseconds
}
```

### Speed Camera
```typescript
{
  id: string;                    // Unique camera ID
  lat: number;                   // Latitude
  lon: number;                   // Longitude
  source: string;                // Data source (e.g., "overpass")
  createdAt: number;             // Unix timestamp in milliseconds
}
```

---

## Notes

1. **User Tracking**: Most endpoints accept `userId` as a query parameter or `X-User-Id` header for tracking user activity.

2. **Incident Expiration**: Incidents automatically expire after 2 hours. They can also be removed if they receive 20 "no" votes.

3. **Admin Tokens**: Admin tokens are stored in memory and will be lost on server restart. In production, use JWT or session management.

4. **Subscription Storage**: Subscriptions are stored in memory. In production, use a database.

5. **CORS**: The API has CORS enabled for all origins. Configure appropriately for production.

6. **Environment Variables**:
   - `PORT`: Server port (default: 4000)
   - `HOST`: Server host (default: 0.0.0.0)
   - `ADMIN_USERNAME`: Admin username (default: "admin")
   - `ADMIN_PASSWORD`: Admin password (default: "admin123")
   - `TELEGRAM_BOT_USERNAME`: Telegram bot username
   - `TELEGRAM_BOT_TOKEN`: Telegram bot token

---

## Rate Limiting

Currently, there is no rate limiting implemented. Consider adding rate limiting in production to prevent abuse.

---

## WebSocket / Real-time Updates

Currently, the API does not support WebSocket connections. Clients should poll endpoints periodically for updates.

---

## Versioning

The API does not currently use versioning. All endpoints are under `/api/`. Consider adding versioning (e.g., `/api/v1/`) for future updates.

