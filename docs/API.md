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
