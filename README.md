# Social Media Backend (Django)

A Django web application using uv for dependency management and Docker Compose for local development.

## Prerequisites

- Python 3.11 or higher
- Docker and Docker Compose
- pip
- uv (https://docs.astral.sh/uv/)

## First-time Setup

### 1. Clone the repository

git clone https://github.com/trucpham04/social-media
cd social-media

### 2. Install required tools

pip install python-dotenv uv

### 3. Install project dependencies with uv

cd backend
uv sync

This will create a .venv virtual environment and install dependencies from pyproject.toml and uv.lock.

### 4. Start the application using Docker

cd ..
docker compose up

The backend will be available at:
http://localhost:8000

## Development Workflow

### Running the Backend

The backend is started automatically by Docker using:

uv run python manage.py runserver 0.0.0.0:8000

### Database Migrations

Apply migrations:

docker compose exec backend uv run python manage.py migrate

Create migrations:

docker compose exec backend uv run python manage.py makemigrations

### Create Superuser

docker compose exec backend uv run python manage.py createsuperuser

## Adding or Updating Dependencies

1. Stop the backend

docker compose down

2. Update dependencies

Edit backend/pyproject.toml

3. Lock dependencies

cd backend
uv lock

4. Restart Docker

cd ..
docker compose up

## Project Structure

social-media/
├── backend/
│   ├── config/
│   ├── manage.py
│   ├── pyproject.toml
│   ├── uv.lock
│   └── .venv/
├── docker-compose.yml
├── .env
└── README.md

## Useful Commands

Run any Django command:

docker compose exec backend uv run python manage.py <command>

View backend logs:

docker compose logs -f backend

Stop all services:

docker compose down

## Notes

- localhost works only from the host machine
- Inside Docker, services communicate using service names (e.g. postgres)
- uv hardlink warnings in Docker are expected and safe to ignore

## License

Add your license information here.