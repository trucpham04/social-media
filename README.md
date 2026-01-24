# ccnlthd

A Django web application.

## Prerequisites

- Python 3.13 or higher
- [uv](https://docs.astral.sh/uv/) - Fast Python package installer and resolver

## Installation

1. Clone the repository:

```bash
git clone https://github.com/trucpham04/music-website
cd music-website
```

2. Install dependencies using uv:

```bash
uv sync
```

## Usage

### Development Server

Run the Django development server:

```bash
uv run python manage.py runserver
```

The application will be available at `http://localhost:8000`

### Database Migrations

Apply database migrations:

```bash
uv run python manage.py migrate
```

Create new migrations:

```bash
uv run python manage.py makemigrations
```

### Create Superuser

Create an admin user:

```bash
uv run python manage.py createsuperuser
```

## Project Structure

```
ccnlthd/
├── config/          # Django project settings
├── db.sqlite3       # SQLite database
├── manage.py        # Django management script
├── main.py          # Main entry point
├── pyproject.toml   # Project dependencies and metadata
└── README.md        # This file
```

## Development

### Adding Dependencies

Add a new package:

```bash
uv add <package-name>
```

Add a development dependency:

```bash
uv add --dev <package-name>
```

### Running Django Commands

Execute any Django management command with:

```bash
uv run python manage.py <command>
```

## License

Add your license information here.
