## Friends API

Base URL: `/api/friends/`

Tất cả endpoint trong file này đều yêu cầu JWT access token hợp lệ ở header:

```text
Authorization: Bearer <access_token>
```

### 1. Send friend request

- **URL**: `/api/friends/requests/`
- **Method**: `POST`
- **Auth**: Required
- **Request body (JSON)**:

```json
{
  "friend_id": 7
}
```

- **Response 201 (JSON)**:

```json
{
  "id": 8,
  "user_id": 1,
  "user_username": "alice",
  "friend_id": 7,
  "friend_username": "yan",
  "status": "pending",
  "created_at": "2026-03-17T10:00:00Z"
}
```

- **Behavior**:
  - Tạo lời mời kết bạn từ user đang login đến `friend_id`
  - Đồng thời tự động tạo follow 1 chiều: `login_user -> friend_id`

### 2. Get sent friend requests

- **URL**: `/api/friends/requests/sent/`
- **Method**: `GET`
- **Auth**: Required
- **Meaning**: Xem các lời mời kết bạn `pending` mà user đang login đã gửi

- **Response 200 (JSON)**:

```json
[
  {
    "id": 2,
    "user_id": 1,
    "user_username": "alice",
    "friend_id": 3,
    "friend_username": "carol",
    "status": "pending",
    "created_at": "2026-03-17T09:28:39Z"
  }
]
```

### 3. Get received friend requests

- **URL**: `/api/friends/requests/received/`
- **Method**: `GET`
- **Auth**: Required
- **Meaning**: Xem các lời mời kết bạn `pending` mà người khác gửi cho user đang login

- **Response 200 (JSON)**:

```json
[
  {
    "id": 3,
    "user_id": 4,
    "user_username": "dave",
    "friend_id": 1,
    "friend_username": "alice",
    "status": "pending",
    "created_at": "2026-03-17T09:28:39Z"
  }
]
```

### 4. Accept friend request

- **URL**: `/api/friends/requests/{request_id}/accept/`
- **Method**: `POST`
- **Auth**: Required
- **Meaning**: Chấp nhận lời mời kết bạn mà user đang login nhận được

- **Response 200 (JSON)**:

```json
{
  "id": 3,
  "user_id": 4,
  "user_username": "dave",
  "friend_id": 1,
  "friend_username": "alice",
  "status": "accepted",
  "created_at": "2026-03-17T09:28:39Z"
}
```

- **Behavior**:
  - Đổi trạng thái request từ `pending` sang `accepted`
  - Tự động tạo follow 2 chiều nếu chưa có:
    - `sender -> receiver`
    - `receiver -> sender`

### 5. Reject friend request

- **URL**: `/api/friends/requests/{request_id}/reject/`
- **Method**: `POST`
- **Auth**: Required
- **Meaning**: Từ chối lời mời kết bạn mà user đang login nhận được

- **Response 204**: No Content

- **Behavior**:
  - Xóa record friend request `pending`

### 6. Cancel friend request

- **URL**: `/api/friends/requests/{request_id}/cancel/`
- **Method**: `DELETE`
- **Auth**: Required
- **Meaning**: Hủy lời mời kết bạn mà user đang login đã gửi

- **Response 204**: No Content

- **Behavior**:
  - Xóa record friend request `pending`

### 7. Get friend list

- **URL**: `/api/friends/list/`
- **Method**: `GET`
- **Auth**: Required
- **Meaning**: Xem danh sách bạn bè của user đang login

- **Response 200 (JSON)**:

```json
[
  {
    "id": 1,
    "user_id": 1,
    "user_username": "alice",
    "friend_id": 2,
    "friend_username": "bob",
    "status": "accepted",
    "created_at": "2026-03-17T09:28:39Z"
  },
  {
    "id": 4,
    "user_id": 1,
    "user_username": "alice",
    "friend_id": 5,
    "friend_username": "erin",
    "status": "accepted",
    "created_at": "2026-03-17T09:28:39Z"
  }
]
```

- **Behavior**:
  - Response đã được normalize theo user đang login
  - `user_*` luôn là user đang login
  - `friend_*` luôn là người bạn còn lại

### 8. Unfriend

- **URL**: `/api/friends/{user_id}/`
- **Method**: `DELETE`
- **Auth**: Required
- **Meaning**: Xóa quan hệ bạn bè với một user đã `accepted`

- **Response 204**: No Content

- **Behavior**:
  - Xóa quan hệ friend `accepted`
  - Đồng thời xóa follow theo chiều: `login_user -> target_user`
  - Không xóa follow chiều ngược lại: `target_user -> login_user`

### 9. Follow user

- **URL**: `/api/friends/follows/`
- **Method**: `POST`
- **Auth**: Required
- **Meaning**: Follow 1 user theo kiểu 1 chiều, không cần accept
- **Request body (JSON)**:

```json
{
  "followed_id": 7
}
```

- **Response 201 (JSON)**:

```json
{
  "id": 5,
  "follower_id": 6,
  "follower_username": "zoe",
  "followed_id": 7,
  "followed_username": "yan",
  "created_at": "2026-03-17T09:28:39Z"
}
```

- **Behavior**:
  - Chỉ tạo follow 1 chiều: `follower -> followed`
  - Không tự tạo follow ngược lại

### 10. Get following list

- **URL**: `/api/friends/follows/following/`
- **Method**: `GET`
- **Auth**: Required
- **Meaning**: Xem danh sách những người user đang login đang follow

- **Response 200 (JSON)**:

```json
[
  {
    "id": 5,
    "follower_id": 6,
    "follower_username": "zoe",
    "followed_id": 7,
    "followed_username": "yan",
    "created_at": "2026-03-17T09:28:39Z"
  }
]
```

### 11. Get followers list

- **URL**: `/api/friends/follows/followers/`
- **Method**: `GET`
- **Auth**: Required
- **Meaning**: Xem danh sách những người đang follow user đang login

- **Response 200 (JSON)**:

```json
[
  {
    "id": 5,
    "follower_id": 6,
    "follower_username": "zoe",
    "followed_id": 7,
    "followed_username": "yan",
    "created_at": "2026-03-17T09:28:39Z"
  }
]
```

### 12. Unfollow user

- **URL**: `/api/friends/follows/{user_id}/`
- **Method**: `DELETE`
- **Auth**: Required
- **Meaning**: Bỏ follow một user

- **Response 204**: No Content

### 13. Common validation rules

- Không thể gửi friend request cho chính mình
- Không thể follow chính mình
- Không thể tạo trùng friend request / friend relation đã tồn tại
- Không thể tạo trùng follow relation đã tồn tại
- `accept`, `reject`, `cancel`, `unfriend`, `unfollow` sẽ trả `404` nếu không tìm thấy quan hệ hợp lệ
