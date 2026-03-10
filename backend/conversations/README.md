## API Conversations

Tài liệu này mô tả các API REST và WebSocket của app `conversations`.

---

### 1. REST API

Prefix chung (xem `config/urls.py`):

- **Base path**: `/api/conversations/`
- **Auth**: Bắt buộc JWT (`Authorization: Bearer <token>`)

#### 1.1. Danh sách conversations của user hiện tại

- **URL**: `GET /api/conversations/`
- **View**: `UserConversationsListView`
- **Mục đích**: Trả về các conversation mà user hiện tại là member.

**Query params**: không có.

**Response 200** (array `ConversationMember`):

```json
[
  {
    "id": 1,
    "conversation": {
      "id": 10,
      "is_group": false,
      "created_at": "2026-03-10T02:40:12.123456Z"
    },
    "joined_at": "2026-03-10T02:45:00.000000Z"
  }
]
```

- `conversation.is_group`: `true` nếu là group chat, `false` nếu là 1-1.

#### 1.2. Tạo conversation mới

- **URL**: `POST /api/conversations/list-create/`
- **View**: `ConversationListCreateView`
- **Auth**: JWT, user hiện tại sẽ luôn được thêm vào members.

**Request body**:

```json
{
  "name": "Group chat bạn bè",
  "is_group": true,
  "member_ids": [2, 3]
}
```

- `name`: tên cuộc trò chuyện (có thể rỗng cho 1-1).
- `is_group`: bắt buộc, `true` nếu là group.
- `member_ids`: (tùy chọn) danh sách ID user sẽ được thêm vào cùng với user hiện tại.

**Response 201**:

```json
{
  "id": 10,
  "name": "Group chat bạn bè",
  "is_group": true,
  "created_at": "2026-03-10T02:40:12.123456Z"
}
```

**Lỗi thường gặp**:

- `400 Bad Request`: dữ liệu không hợp lệ.
- `401 Unauthorized`: thiếu hoặc token không hợp lệ.

#### 1.3. Lấy thông tin cơ bản của một conversation

- **URL**: `GET /api/conversations/<id>/`
- **View**: `ConversationDetailView`
- **Mục đích**: Trả về thông tin cơ bản của conversation (không bao gồm members, messages).
- **Yêu cầu**: User phải là member của conversation.

**Response 200**:

```json
{
  "id": 10,
  "name": "Group chat bạn bè",
  "is_group": true,
  "created_at": "2026-03-10T02:40:12.123456Z"
}
```

**Lỗi**:

- `403 Forbidden`: user không phải member.
- `404 Not Found`: conversation không tồn tại.

#### 1.4. Danh sách thành viên của một conversation

- **URL**: `GET /api/conversations/<id>/members/`
- **View**: `ConversationMembersListView`
- **Mục đích**: Lấy danh sách các thành viên trong conversation.
- **Yêu cầu**: User phải là member.

**Response 200** (array `ConversationMemberDetail`):

```json
[
  {
    "id": 1,
    "user_id": 1,
    "username": "alice",
    "email": "alice@example.com",
    "joined_at": "2026-03-10T02:45:00.000000Z"
  },
  {
    "id": 2,
    "user_id": 2,
    "username": "bob",
    "email": "bob@example.com",
    "joined_at": "2026-03-10T02:46:00.000000Z"
  }
]
```

**Lỗi**:

- `403 Forbidden`: user không phải member.
- `404 Not Found`: conversation không tồn tại.

#### 1.5. Danh sách messages trong một conversation

- **URL**: `GET /api/conversations/<conversation_id>/messages/`
- **View**: `ConversationMessagesListView`
- **Mục đích**: Lấy lịch sử tin nhắn của một conversation.

**URL params**:

- `conversation_id` (integer): ID của conversation.

**Response 200** (array `Message`):

```json
[
  {
    "id": 1,
    "conversation_id": 10,
    "sender_id": 3,
    "content": "Hello",
    "media_url": null,
    "media_type": "text",
    "created_at": "2026-03-10T02:50:00.000000Z"
  }
]
```

- `media_type`: `"text" | "image" | "video"`.
- Với `media_type = "text"`: `content` bắt buộc, `media_url` thường `null`.
- Với `media_type = "image" | "video"`: `media_url` bắt buộc, `content` có thể rỗng.

#### 1.6. Thêm thành viên vào conversation

- **URL**: `POST /api/conversations/<id>/members/add/`
- **View**: `ConversationMemberAddView`
- **Mục đích**: Thêm một user vào conversation.
- **Yêu cầu**: Người gọi API phải là member của conversation.

**Request body**:

```json
{
  "user_id": 5
}
```

**Response 201**:

```json
{
  "id": 3,
  "user_id": 5,
  "username": "charlie",
  "email": "charlie@example.com",
  "joined_at": "2026-03-10T03:00:00.000000Z"
}
```

**Lỗi**:

- `400 Bad Request`: user đã là member.
- `403 Forbidden`: caller không phải member.
- `404 Not Found`: conversation hoặc user không tồn tại.

#### 1.7. Xóa thành viên khỏi conversation

- **URL**: `DELETE /api/conversations/<id>/members/<user_id>/remove/`
- **View**: `ConversationMemberRemoveView`
- **Mục đích**: Xóa một thành viên ra khỏi conversation.
- **Yêu cầu**: Người gọi API phải là member của conversation.

**Response 204**: không có body.

**Lỗi**:

- `403 Forbidden`: caller không phải member.
- `404 Not Found`: conversation hoặc membership không tồn tại.

---

### 2. WebSocket API (realtime messaging)

WebSocket được cấu hình trong:

- `config/asgi.py`
- `conversations/routing.py`
- `conversations/consumers.py`

#### 2.1. Kết nối WebSocket

- **URL**: `ws://<host>/ws/conversations/<conversation_id>/?token=<JWT>`
- **Consumer**: `ChatConsumer`

**Tham số:**

- `conversation_id`: ID của conversation.
- `token`: JWT hợp lệ của user (giống token dùng cho REST).

**Xác thực & kiểm tra:**

- Token được đọc từ query `token` hoặc header `Authorization: Bearer <token>`.
- Nếu:
  - Không có token, hoặc
  - Token không hợp lệ, hoặc
  - User không phải member của conversation (`ConversationMember`)
- Thì kết nối sẽ bị **từ chối**:
  - Mã đóng gần giống `4401` (unauthorized) hoặc `4403` (forbidden).

#### 2.2. Gửi tin nhắn từ client

Client gửi JSON qua WebSocket (text frame):

```json
{
  "content": "Hello",
  "media_type": "text",
  "media_url": null
}
```

- `content`:
  - Bắt buộc nếu `media_type = "text"` và phải khác rỗng (sau khi trim).
- `media_type`:
  - Mặc định `"text"` nếu không gửi.
  - Hợp lệ: `"text"`, `"image"`, `"video"`.
- `media_url`:
  - Bắt buộc nếu `media_type = "image"` hoặc `"video"`.

**Trường hợp lỗi (validation):**

- Nếu JSON không parse được:

```json
{ "type": "error", "message": "Invalid JSON" }
```

- Nếu `media_type = "text"` nhưng `content` rỗng:

```json
{ "type": "error", "message": "content is required for text messages" }
```

- Nếu `media_type in ["image", "video"]` nhưng thiếu `media_url`:

```json
{ "type": "error", "message": "media_url is required for media messages" }
```

Khi tin nhắn hợp lệ:

- Một bản ghi `Message` được tạo trong DB.
- Một event được broadcast tới tất cả client đang join cùng `conversation`.

#### 2.3. Nhận tin nhắn từ server

Khi có tin nhắn mới (dù chính client hiện tại gửi hay client khác), server gửi JSON:

```json
{
  "type": "message",
  "id": 1,
  "conversation_id": 10,
  "sender_id": 3,
  "content": "Hello",
  "media_url": null,
  "media_type": "text",
  "created_at": "2026-03-10T02:50:00.000000Z"
}
```

- `type = "message"` cho biết đây là event message mới.
- Client có thể dùng `sender_id` để map sang user (username, avatar, ...) thông qua API user khác.

---

### 3. Mô hình dữ liệu (tóm tắt)

- Định nghĩa trong `conversations/models.py`.

**Conversation**

- `id`: integer, primary key.
- `is_group`: boolean.
- `created_at`: datetime (auto_now_add).

**ConversationMember**

- `conversation`: FK → `Conversation`.
- `user`: FK → `AUTH_USER_MODEL`.
- `joined_at`: datetime (auto_now_add).
- Ràng buộc: unique `(conversation, user)`.

**Message**

- `id`: integer, primary key.
- `conversation`: FK → `Conversation`.
- `sender`: FK → `AUTH_USER_MODEL`.
- `content`: text.
- `media_url`: URL, nullable.
- `media_type`: `"text" | "image" | "video"`.
- `created_at`: datetime (auto_now_add).

