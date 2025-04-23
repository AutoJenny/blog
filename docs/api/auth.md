# Authentication API

## Overview
The Authentication API provides endpoints for user authentication, registration, and token management. It supports both session-based and token-based authentication.

## Authentication Endpoints

### Login
```http
POST /api/v1/auth/login
```

#### Request Body
```json
{
  "username": "user@example.com",
  "password": "secure_password",
  "remember": true
}
```

#### Response
```json
{
  "status": "success",
  "data": {
    "user": {
      "id": 1,
      "username": "user@example.com",
      "name": "John Doe",
      "role": "author",
      "created_at": "2025-04-23T15:34:10Z"
    },
    "token": {
      "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
      "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
      "token_type": "Bearer",
      "expires_in": 3600
    }
  }
}
```

### Register
```http
POST /api/v1/auth/register
```

#### Request Body
```json
{
  "username": "user@example.com",
  "password": "secure_password",
  "name": "John Doe",
  "email": "user@example.com"
}
```

#### Response
```json
{
  "status": "success",
  "data": {
    "user": {
      "id": 1,
      "username": "user@example.com",
      "name": "John Doe",
      "role": "user",
      "created_at": "2025-04-23T15:34:10Z"
    },
    "message": "Registration successful. Please check your email for verification."
  }
}
```

### Verify Email
```http
GET /api/v1/auth/verify/{token}
```

#### Response
```json
{
  "status": "success",
  "data": {
    "message": "Email verified successfully"
  }
}
```

### Refresh Token
```http
POST /api/v1/auth/refresh
```

#### Request Body
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### Response
```json
{
  "status": "success",
  "data": {
    "token": {
      "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
      "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
      "token_type": "Bearer",
      "expires_in": 3600
    }
  }
}
```

### Logout
```http
POST /api/v1/auth/logout
```

#### Response
```json
{
  "status": "success",
  "data": {
    "message": "Logged out successfully"
  }
}
```

## Password Management

### Request Password Reset
```http
POST /api/v1/auth/password/reset-request
```

#### Request Body
```json
{
  "email": "user@example.com"
}
```

#### Response
```json
{
  "status": "success",
  "data": {
    "message": "Password reset instructions sent to email"
  }
}
```

### Reset Password
```http
POST /api/v1/auth/password/reset
```

#### Request Body
```json
{
  "token": "reset_token",
  "password": "new_password",
  "password_confirmation": "new_password"
}
```

#### Response
```json
{
  "status": "success",
  "data": {
    "message": "Password reset successfully"
  }
}
```

### Change Password
```http
POST /api/v1/auth/password/change
```

#### Request Body
```json
{
  "current_password": "old_password",
  "new_password": "new_password",
  "new_password_confirmation": "new_password"
}
```

## API Key Management

### List API Keys
```http
GET /api/v1/auth/api-keys
```

#### Response
```json
{
  "status": "success",
  "data": [
    {
      "id": 1,
      "name": "Blog API",
      "key": "pk_test_abc123...",
      "last_used": "2025-04-23T15:34:10Z",
      "created_at": "2025-04-23T15:34:10Z",
      "expires_at": "2026-04-23T15:34:10Z"
    }
  ]
}
```

### Create API Key
```http
POST /api/v1/auth/api-keys
```

#### Request Body
```json
{
  "name": "Blog API",
  "expires_in": 31536000,  // 1 year in seconds
  "scopes": ["read", "write"]
}
```

#### Response
```json
{
  "status": "success",
  "data": {
    "id": 1,
    "name": "Blog API",
    "key": "pk_test_abc123...",
    "created_at": "2025-04-23T15:34:10Z",
    "expires_at": "2026-04-23T15:34:10Z"
  }
}
```

### Delete API Key
```http
DELETE /api/v1/auth/api-keys/{id}
```

## Error Responses

### Invalid Credentials
```json
{
  "status": "error",
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "Invalid username or password"
  }
}
```

### Token Error
```json
{
  "status": "error",
  "error": {
    "code": "TOKEN_ERROR",
    "message": "Invalid or expired token"
  }
}
```

### Validation Error
```json
{
  "status": "error",
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed",
    "details": {
      "password": ["Password must be at least 8 characters"]
    }
  }
}
```

## Best Practices

### Security
1. Use HTTPS only
2. Implement rate limiting
3. Enforce password policies
4. Monitor failed attempts

### Token Management
1. Short-lived access tokens
2. Secure token storage
3. Regular token rotation
4. Token revocation

### Password Security
1. Hash passwords
2. Salt passwords
3. Enforce complexity
4. Prevent common passwords

### API Key Security
1. Limit key scopes
2. Monitor key usage
3. Regular key rotation
4. Secure key storage

## Usage Examples

### Login
```bash
curl -X POST \
     -H "Content-Type: application/json" \
     -d '{"username": "user@example.com", "password": "password123"}' \
     https://api.blog.com/v1/auth/login
```

### Refresh Token
```bash
curl -X POST \
     -H "Content-Type: application/json" \
     -d '{"refresh_token": "token123"}' \
     https://api.blog.com/v1/auth/refresh
```

### Create API Key
```bash
curl -X POST \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{"name": "Blog API", "expires_in": 31536000}' \
     https://api.blog.com/v1/auth/api-keys
``` 