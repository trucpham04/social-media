# Social Media Backend (Django)

A Django REST API for a social media application with user authentication, posts management, and S3 media storage.

## Features

- **User Authentication**: JWT-based authentication with registration and login
- **Posts Management**: CRUD operations for posts with media upload support
- **Media Storage**: AWS S3 integration for image and video storage
- **Post Visibility**: Public, Friends, and Private visibility options
- **Django Admin**: Admin interface for managing posts and users

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.11 or higher**
- **Docker and Docker Compose** (for containerized development)
- **pip** (Python package installer)
- **uv** (Fast Python package installer) - [Installation Guide](https://docs.astral.sh/uv/)

## Project Structure

```
social-media/
├── backend/
│   ├── config/          # Django project settings
│   ├── users/            # User authentication app
│   ├── posts/            # Posts management app
│   ├── manage.py
│   ├── pyproject.toml    # Project dependencies
│   └── uv.lock           # Locked dependencies
├── docker-compose.yml    # Docker services configuration
├── .env                  # Environment variables (create from .env.example)
├── .env.example          # Example environment variables
└── README.md
```

## First-time Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd social-media
```

### 2. Install Required Tools

```bash
pip install python-dotenv uv
```

### 3. Configure Environment Variables

Create a `.env` file in the project root (same level as `backend` folder) by copying `.env.example`:

```bash
cp .env.example .env
```

Edit `.env` and fill in your configuration:

#### Database Configuration
```env
POSTGRES_DB=social_media_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
```

#### AWS S3 Configuration
To use media uploads, you need AWS S3 credentials:

1. **Create an AWS Account** (if you don't have one)
2. **Create an S3 Bucket**:
   - Go to AWS S3 Console
   - Create a new bucket
   - Note the bucket name and region
3. **Create IAM User with S3 Access**:
   - Go to AWS IAM Console
   - Create a new user with programmatic access
   - Attach policy: `AmazonS3FullAccess` (or create custom policy for your bucket)
   - Save the Access Key ID and Secret Access Key

Update `.env` with your AWS credentials:
```env
AWS_ACCESS_KEY_ID=your-actual-access-key-id
AWS_SECRET_ACCESS_KEY=your-actual-secret-access-key
AWS_DEFAULT_REGION=us-east-1  # Your bucket's region
AWS_S3_BUCKET_NAME=your-bucket-name
```

**Note**: For development/testing without AWS, you can leave AWS variables empty, but media uploads won't work.

### 4. Install Project Dependencies

```bash
cd backend
uv sync
```

This creates a `.venv` virtual environment and installs all dependencies from `pyproject.toml`.

### 5. Start Docker Services

From the project root directory:

```bash
docker compose up
```

This will start:
- **PostgreSQL database** on port `5432`
- **Django backend** on port `8000`

The backend will be available at: **http://localhost:8000**

### 6. Run Database Migrations

In a new terminal, run:

```bash
# Create migrations for all apps
docker compose exec backend uv run python manage.py makemigrations

# Apply migrations to create database tables
docker compose exec backend uv run python manage.py migrate
```

This creates all necessary database tables including:
- `users` table (user authentication)
- `posts` table (posts with media support)

**Note**: If you see "relation 'posts' does not exist" error, it means migrations haven't been run. Run the commands above to fix it.

### 7. Create a Superuser (Optional)

To access Django admin panel:

```bash
docker compose exec backend uv run python manage.py createsuperuser
```

Follow the prompts to create an admin user.

## Development Workflow

### Running the Backend

The backend runs automatically when you start Docker:

```bash
docker compose up
```

To run in detached mode (background):

```bash
docker compose up -d
```

### Database Migrations

**Create migrations** (after model changes):
```bash
docker compose exec backend uv run python manage.py makemigrations
```

**Apply migrations**:
```bash
docker compose exec backend uv run python manage.py migrate
```

**Create migrations for specific app**:
```bash
docker compose exec backend uv run python manage.py makemigrations posts
docker compose exec backend uv run python manage.py makemigrations users
```

### Accessing Django Shell

```bash
docker compose exec backend uv run python manage.py shell
```

### Viewing Logs

```bash
# All services
docker compose logs -f

# Backend only
docker compose logs -f backend

# Database only
docker compose logs -f postgres
```

### Stopping Services

```bash
# Stop services (keeps containers)
docker compose stop

# Stop and remove containers
docker compose down

# Stop and remove containers + volumes (⚠️ deletes database data)
docker compose down -v
```

## API Endpoints

### Authentication

Base URL: `http://localhost:8000/api/users/`

- **POST** `/register/` - Register a new user
  ```json
  {
    "username": "john_doe",
    "email": "john@example.com",
    "password": "securepassword123"
  }
  ```

- **POST** `/login/` - Login and get JWT tokens
  ```json
  {
    "username": "john_doe",
    "password": "securepassword123"
  }
  ```
  Returns: `access` and `refresh` tokens

- **POST** `/token/refresh/` - Refresh access token
  ```json
  {
    "refresh": "your-refresh-token"
  }
  ```

### Posts

Base URL: `http://localhost:8000/api/posts/`

**All endpoints require authentication** (include JWT token in header):
```
Authorization: Bearer <your-access-token>
```

- **GET** `/` - List all posts (filtered by visibility)
  - Query params: `?visibility=public&user_id=1`
  
- **POST** `/` - Create a new post
  ```json
  {
    "content": "My first post!",
    "media_type": "text",
    "visibility": "public"
  }
  ```
  For media upload, use `multipart/form-data`:
  - `content`: text content
  - `media_file`: image or video file
  - `media_type`: "image" or "video"
  - `visibility`: "public", "friends", or "private"

- **GET** `/{id}/` - Get a specific post

- **PUT** `/{id}/` - Update a post (owner only)

- **PATCH** `/{id}/` - Partial update (owner only)

- **DELETE** `/{id}/` - Delete a post (owner only)

- **GET** `/my_posts/` - Get authenticated user's posts

## Django Admin

Access the admin panel at: **http://localhost:8000/admin/**

Login with your superuser credentials.

### Managing Posts in Admin

1. Navigate to **Posts** → **Posts**
2. Click **Add Post**
3. Fill in:
   - **User**: Select a user
   - **Content**: Post text content
   - **Visibility**: Choose visibility level
   - **Media file**: Drag and drop or select an image/video file
   - **Media type**: Will be auto-detected from file
4. Click **Save** - file will be uploaded to S3 automatically

## Adding or Updating Dependencies

**You only need to run `uv lock` when you ADD or CHANGE dependencies in `pyproject.toml`.**

1. Edit `backend/pyproject.toml` to add/update dependencies
2. Update the lock file:
   ```bash
   cd backend
   uv lock
   ```
3. Rebuild the Docker image (to install new dependencies):
   ```bash
   docker compose build backend
   docker compose up -d
   ```

**Note**: 
- `docker compose up` uses the existing `uv.lock` file - no need to run `uv lock` unless dependencies change
- If you only modify code (not dependencies), just restart: `docker compose restart backend`
- The Dockerfile copies `uv.lock` during build, so rebuild is needed after locking new dependencies

## Troubleshooting

### Database Connection Issues

If you see connection errors:
1. Ensure PostgreSQL container is running: `docker compose ps`
2. Check `.env` file has correct database credentials
3. Verify database is ready: `docker compose logs postgres`

### Migration Errors

If migrations fail:
```bash
# Reset migrations (⚠️ deletes data)
docker compose down -v
docker compose up -d
docker compose exec backend uv run python manage.py migrate
```

### S3 Upload Errors

If media uploads fail:
1. Verify AWS credentials in `.env`
2. Check S3 bucket name and region are correct
3. Ensure IAM user has S3 permissions
4. Test S3 connection manually

### Port Already in Use

If port 8000 or 5432 is already in use:
1. Stop the conflicting service
2. Or change ports in `docker-compose.yml`

## Production Deployment

Before deploying to production:

1. **Change SECRET_KEY**: Move to environment variable
2. **Set DEBUG=False**: Update in `settings.py`
3. **Configure ALLOWED_HOSTS**: Add your domain
4. **Use environment-specific database**: Don't use Docker postgres
5. **Set up proper S3 bucket policies**: Restrict access
6. **Use HTTPS**: Configure SSL certificates
7. **Set up proper logging**: Configure log handlers
8. **Use production WSGI server**: e.g., Gunicorn + Nginx

## Useful Commands

```bash
# Run any Django management command
docker compose exec backend uv run python manage.py <command>

# Access PostgreSQL shell
docker compose exec postgres psql -U postgres -d social_media_db

# View backend logs
docker compose logs -f backend

# Rebuild containers after dependency changes
docker compose build --no-cache backend
docker compose up -d

# Check container status
docker compose ps
```

## Realtime Messaging

- **WebSocket endpoint**: `ws://localhost:8000/ws/conversations/<conversation_id>/?token=<JWT>`
- **REST endpoints**:
  - `GET /api/conversations/conversations/` – danh sách conversation mà user hiện tại tham gia
  - `GET /api/conversations/conversations/<conversation_id>/messages/` – danh sách tin nhắn trong một conversation

## License


