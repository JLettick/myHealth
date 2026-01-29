# API Documentation

Base URL: `/api/v1`

## Authentication

All protected endpoints require a Bearer token in the Authorization header:
```
Authorization: Bearer <access_token>
```

---

## Endpoints

### Health Check

#### GET /health
Check if the API is running.

**Response**: `200 OK`
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:00:00Z",
  "service": "myhealth-api",
  "version": "1.0.0"
}
```

---

### Authentication

#### POST /auth/signup
Create a new user account.

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "full_name": "John Doe"  // optional
}
```

**Password Requirements**:
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit
- At least one special character

**Response**: `200 OK`
```json
{
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "full_name": "John Doe",
    "avatar_url": null,
    "created_at": "2024-01-15T10:00:00Z",
    "email_confirmed_at": null
  },
  "session": {
    "access_token": "eyJhbG...",
    "refresh_token": "eyJhbG...",
    "token_type": "Bearer",
    "expires_in": 3600,
    "expires_at": "2024-01-15T11:00:00Z"
  },
  "message": "Account created successfully"
}
```

**Errors**:
- `409 Conflict`: Email already exists
- `422 Unprocessable Entity`: Validation error

---

#### POST /auth/login
Authenticate with email and password.

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Response**: `200 OK`
```json
{
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "full_name": "John Doe",
    "avatar_url": null,
    "created_at": "2024-01-15T10:00:00Z",
    "email_confirmed_at": "2024-01-15T10:05:00Z"
  },
  "session": {
    "access_token": "eyJhbG...",
    "refresh_token": "eyJhbG...",
    "token_type": "Bearer",
    "expires_in": 3600,
    "expires_at": "2024-01-15T11:00:00Z"
  },
  "message": "Login successful"
}
```

**Errors**:
- `401 Unauthorized`: Invalid credentials

---

#### POST /auth/logout
Sign out and invalidate session.

**Headers**: `Authorization: Bearer <token>` (required)

**Response**: `200 OK`
```json
{
  "message": "Logged out successfully",
  "success": true
}
```

---

#### POST /auth/refresh
Refresh access token using refresh token.

**Request Body**:
```json
{
  "refresh_token": "eyJhbG..."
}
```

**Response**: `200 OK`
```json
{
  "user": { ... },
  "session": {
    "access_token": "new_token...",
    "refresh_token": "new_refresh...",
    ...
  },
  "message": "Token refreshed successfully"
}
```

**Errors**:
- `401 Unauthorized`: Invalid or expired refresh token

---

#### GET /auth/me
Get current authenticated user.

**Headers**: `Authorization: Bearer <token>` (required)

**Response**: `200 OK`
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "John Doe",
  "avatar_url": null,
  "created_at": "2024-01-15T10:00:00Z",
  "email_confirmed_at": "2024-01-15T10:05:00Z"
}
```

---

### Users

#### GET /users/profile
Get current user's profile.

**Headers**: `Authorization: Bearer <token>` (required)

**Response**: `200 OK`
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "John Doe",
  "avatar_url": null,
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-16T14:30:00Z"
}
```

---

#### PATCH /users/profile
Update current user's profile.

**Headers**: `Authorization: Bearer <token>` (required)

**Request Body**:
```json
{
  "full_name": "Jane Doe",      // optional
  "avatar_url": "https://..."   // optional
}
```

**Response**: `200 OK`
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "Jane Doe",
  "avatar_url": "https://...",
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-16T15:00:00Z"
}
```

---

#### DELETE /users/account
Delete current user's account permanently.

**Headers**: `Authorization: Bearer <token>` (required)

**Request Body**:
```json
{
  "confirm": true
}
```

**Response**: `200 OK`
```json
{
  "message": "Account deleted successfully",
  "success": true
}
```

---

### Whoop Integration

#### GET /whoop/connect
Get OAuth authorization URL to connect Whoop account.

**Headers**: `Authorization: Bearer <token>` (required)

**Response**: `200 OK`
```json
{
  "authorization_url": "https://api.prod.whoop.com/oauth/oauth2/auth?...",
  "state": "random_state_string"
}
```

---

#### GET /whoop/callback
OAuth callback handler. Redirects to dashboard after processing.

**Query Parameters**:
- `code`: Authorization code from Whoop
- `state`: State parameter for CSRF verification

**Response**: `302 Redirect` to `/dashboard?whoop_connected=true` or `/dashboard?whoop_error=...`

---

#### DELETE /whoop/disconnect
Disconnect Whoop account. Historical data is retained.

**Headers**: `Authorization: Bearer <token>` (required)

**Response**: `200 OK`
```json
{
  "success": true,
  "message": "Whoop account disconnected successfully"
}
```

---

#### GET /whoop/status
Get Whoop connection status.

**Headers**: `Authorization: Bearer <token>` (required)

**Response**: `200 OK`
```json
{
  "is_connected": true,
  "whoop_user_id": "12345",
  "connected_at": "2024-01-15T10:00:00Z",
  "last_sync_at": "2024-01-16T08:00:00Z",
  "scopes": ["read:profile", "read:cycles", "read:recovery", "read:sleep", "read:workout"]
}
```

---

#### POST /whoop/sync
Trigger synchronization of Whoop data.

**Headers**: `Authorization: Bearer <token>` (required)

**Query Parameters** (optional):
- `start_date`: ISO 8601 datetime (default: 30 days ago)
- `end_date`: ISO 8601 datetime (default: now)

**Response**: `200 OK`
```json
{
  "success": true,
  "cycles_synced": 30,
  "recovery_synced": 30,
  "sleep_synced": 35,
  "workouts_synced": 12,
  "sync_completed_at": "2024-01-16T10:05:00Z"
}
```

---

#### GET /whoop/dashboard
Get summary metrics for dashboard display.

**Headers**: `Authorization: Bearer <token>` (required)

**Response**: `200 OK`
```json
{
  "is_connected": true,
  "last_sync_at": "2024-01-16T08:00:00Z",
  "latest_recovery_score": 78.5,
  "latest_strain_score": 12.4,
  "latest_hrv": 45.2,
  "latest_resting_hr": 52.0,
  "latest_sleep_score": 82.0,
  "latest_sleep_hours": 7.5,
  "avg_recovery_7d": 72.3,
  "avg_strain_7d": 11.8,
  "avg_sleep_hours_7d": 7.2,
  "total_workouts_7d": 5
}
```

---

#### GET /whoop/sleep
Get paginated sleep records.

**Headers**: `Authorization: Bearer <token>` (required)

**Query Parameters**:
- `page`: Page number (default: 1)
- `page_size`: Records per page, max 50 (default: 10)
- `include_naps`: Include nap records (default: false)

**Response**: `200 OK`
```json
{
  "data": [
    {
      "id": "uuid",
      "whoop_sleep_id": 12345,
      "start_time": "2024-01-15T23:00:00Z",
      "end_time": "2024-01-16T07:00:00Z",
      "is_nap": false,
      "sleep_score": 82.0,
      "total_in_bed_milli": 28800000,
      "total_awake_milli": 1800000,
      "total_light_sleep_milli": 10800000,
      "total_slow_wave_sleep_milli": 7200000,
      "total_rem_sleep_milli": 9000000,
      "sleep_efficiency": 0.94,
      "respiratory_rate": 14.5,
      "created_at": "2024-01-16T08:00:00Z"
    }
  ],
  "total": 30,
  "page": 1,
  "page_size": 10
}
```

---

#### GET /whoop/workouts
Get paginated workout records.

**Headers**: `Authorization: Bearer <token>` (required)

**Query Parameters**:
- `page`: Page number (default: 1)
- `page_size`: Records per page, max 50 (default: 10)

**Response**: `200 OK`
```json
{
  "data": [
    {
      "id": "uuid",
      "whoop_workout_id": 67890,
      "start_time": "2024-01-16T06:00:00Z",
      "end_time": "2024-01-16T07:00:00Z",
      "sport_id": 1,
      "sport_name": "Running",
      "strain_score": 14.2,
      "kilojoules": 2500.0,
      "average_heart_rate": 145,
      "max_heart_rate": 175,
      "distance_meter": 8000.0,
      "created_at": "2024-01-16T08:00:00Z"
    }
  ],
  "total": 12,
  "page": 1,
  "page_size": 10
}
```

---

#### GET /whoop/recovery
Get paginated recovery records.

**Headers**: `Authorization: Bearer <token>` (required)

**Query Parameters**:
- `page`: Page number (default: 1)
- `page_size`: Records per page, max 50 (default: 10)

**Response**: `200 OK`
```json
{
  "data": [
    {
      "id": "uuid",
      "whoop_cycle_id": 11111,
      "recovery_score": 78.5,
      "resting_heart_rate": 52.0,
      "hrv_rmssd_milli": 45.2,
      "spo2_percentage": 97.5,
      "skin_temp_celsius": 33.2,
      "created_at": "2024-01-16T08:00:00Z"
    }
  ],
  "total": 30,
  "page": 1,
  "page_size": 10
}
```

---

### Nutrition Tracking

#### POST /nutrition/foods
Create a custom food item.

**Headers**: `Authorization: Bearer <token>` (required)

**Request Body**:
```json
{
  "name": "Chicken Breast",
  "brand": "Organic Farms",
  "serving_size": 100,
  "serving_unit": "g",
  "calories": 165,
  "protein_g": 31,
  "carbs_g": 0,
  "fat_g": 3.6,
  "fiber_g": 0
}
```

**Response**: `201 Created`

---

#### GET /nutrition/foods/search
Search for foods by name.

**Headers**: `Authorization: Bearer <token>` (required)

**Query Parameters**:
- `q`: Search query (min 2 chars)
- `page`: Page number (default: 1)
- `page_size`: Results per page (default: 20)

**Response**: `200 OK`
```json
{
  "results": [{ "id": "uuid", "name": "Chicken Breast", ... }],
  "total": 15,
  "query": "chicken"
}
```

---

#### POST /nutrition/entries
Log a food entry (meal).

**Headers**: `Authorization: Bearer <token>` (required)

**Request Body**:
```json
{
  "food_id": "uuid",
  "entry_date": "2024-01-16",
  "meal_type": "lunch",
  "servings": 1.5,
  "notes": "optional notes"
}
```

**Response**: `201 Created`

---

#### GET /nutrition/summary/daily
Get daily nutrition summary.

**Headers**: `Authorization: Bearer <token>` (required)

**Query Parameters**:
- `summary_date`: Date in YYYY-MM-DD format (defaults to today)

**Response**: `200 OK`
```json
{
  "date": "2024-01-16",
  "meals": [
    {
      "meal_type": "breakfast",
      "entries": [...],
      "total_calories": 450,
      "total_protein_g": 25,
      "total_carbs_g": 45,
      "total_fat_g": 18
    }
  ],
  "total_calories": 1850,
  "total_protein_g": 120,
  "total_carbs_g": 180,
  "total_fat_g": 65,
  "calories_target": 2000,
  "protein_g_target": 150
}
```

---

#### GET /nutrition/goals
Get nutrition goals.

**Headers**: `Authorization: Bearer <token>` (required)

**Response**: `200 OK`
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "calories_target": 2000,
  "protein_g_target": 150,
  "carbs_g_target": 200,
  "fat_g_target": 65,
  "fiber_g_target": 25,
  "is_active": true,
  "created_at": "2024-01-16T10:00:00Z",
  "updated_at": "2024-01-16T10:00:00Z"
}
```

**Note**: Returns `null` if no goals are set (not 404).

---

#### PUT /nutrition/goals
Set nutrition goals.

**Headers**: `Authorization: Bearer <token>` (required)

**Request Body**:
```json
{
  "calories_target": 2000,
  "protein_g_target": 150,
  "carbs_g_target": 200,
  "fat_g_target": 65
}
```

**Response**: `200 OK`

---

### USDA Food Database

#### GET /nutrition/foods/usda/search
Search the USDA FoodData Central database.

**Headers**: `Authorization: Bearer <token>` (required)

**Query Parameters**:
- `q`: Search query (min 2 chars)
- `page`: Page number (default: 1)
- `page_size`: Results per page (default: 20, max: 50)
- `data_type`: Comma-separated data types (default: "Foundation,SR Legacy")
  - Options: `Foundation`, `SR Legacy`, `Branded`, `Survey (FNDDS)`
  - Example: `Foundation,SR Legacy` for basic foods, `Branded` for branded products

**Response**: `200 OK`
```json
{
  "results": [
    {
      "fdc_id": "748967",
      "name": "Chicken, breast, meat only, cooked, roasted",
      "brand": null,
      "data_type": "SR Legacy",
      "serving_size": 100,
      "serving_unit": "g",
      "calories": 165,
      "protein_g": 31,
      "carbs_g": 0,
      "fat_g": 3.6,
      "fiber_g": 0
    }
  ],
  "total": 150,
  "query": "chicken breast",
  "page": 1,
  "page_size": 20
}
```

---

#### POST /nutrition/foods/usda/import
Import a USDA food into user's food database.

**Headers**: `Authorization: Bearer <token>` (required)

**Request Body** (full USDAFoodItem from search results):
```json
{
  "fdc_id": "748967",
  "name": "Chicken, breast, meat only, cooked, roasted",
  "brand": null,
  "data_type": "SR Legacy",
  "serving_size": 100,
  "serving_unit": "g",
  "calories": 165,
  "protein_g": 31,
  "carbs_g": 0,
  "fat_g": 3.6,
  "fiber_g": 0
}
```

**Response**: `201 Created`
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "name": "Chicken, breast, meat only, cooked, roasted",
  "brand": null,
  "serving_size": 100,
  "serving_unit": "g",
  "calories": 165,
  "protein_g": 31,
  "carbs_g": 0,
  "fat_g": 3.6,
  "fiber_g": 0,
  "is_verified": true,
  "created_at": "2024-01-16T10:00:00Z"
}
```

---

## Error Responses

All errors follow this format:
```json
{
  "error": "ERROR_CODE",
  "message": "Human readable message",
  "details": { ... },
  "request_id": "abc123"
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `AUTHENTICATION_ERROR` | 401 | Invalid or expired token |
| `AUTHORIZATION_ERROR` | 403 | Permission denied |
| `NOT_FOUND` | 404 | Resource not found |
| `VALIDATION_ERROR` | 422 | Invalid input data |
| `CONFLICT` | 409 | Resource already exists |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `EXTERNAL_SERVICE_ERROR` | 502 | External service failed |
| `INTERNAL_ERROR` | 500 | Unexpected server error |
| `WHOOP_AUTH_ERROR` | 401 | Whoop authentication failed |
| `WHOOP_NOT_CONNECTED` | 404 | Whoop account not connected |
| `WHOOP_TOKEN_EXPIRED` | 401 | Whoop tokens expired, reconnect required |
| `WHOOP_RATE_LIMIT` | 429 | Whoop API rate limit exceeded |
| `WHOOP_SYNC_ERROR` | 502 | Failed to sync Whoop data |

---

## Rate Limits

| Endpoint | Limit |
|----------|-------|
| POST /auth/login | 5 requests/minute |
| POST /auth/signup | 3 requests/hour |
| Other endpoints | 100 requests/minute |

---

## Request Headers

| Header | Description |
|--------|-------------|
| `Authorization` | Bearer token for authentication |
| `Content-Type` | `application/json` for all requests |
| `X-Request-ID` | Optional request ID for tracking |

## Response Headers

| Header | Description |
|--------|-------------|
| `X-Request-ID` | Request ID for debugging |
