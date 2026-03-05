## Users API

Base URL: `/api/users/`

### 1. Register

- **URL**: `/api/users/register/`
- **Method**: `POST`
- **Auth**: Public
- **Request body (JSON)**:

```json
{
  "username": "testuser",
  "email": "test@example.com",
  "password": "StrongPass123!"
}
```

- **Response 201 (JSON)**:

```json
{
  "id": 1,
  "username": "testuser",
  "email": "test@example.com"
}
```

### 2. Login (JWT)

- **URL**: `/api/users/login/`
- **Method**: `POST`
- **Auth**: Public
- **Request body (JSON)**:

```json
{
  "username": "testuser",
  "password": "StrongPass123!"
}
```

- **Response 200 (JSON)**:

```json
{
  "refresh": "<refresh_token>",
  "access": "<access_token>"
}
```

### 3. Refresh access token

- **URL**: `/api/users/token/refresh/`
- **Method**: `POST`
- **Auth**: Public (yêu cầu `refresh` token hợp lệ)
- **Request body (JSON)**:

```json
{
  "refresh": "<refresh_token>"
}
```

- **Response 200 (JSON)**:

```json
{
  "access": "<new_access_token>"
}
```
