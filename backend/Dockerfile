FROM python:3.12-slim

# System deps
RUN apt-get update && apt-get install -y build-essential libpq-dev

# Set workdir
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock* ./

# Install dependencies
RUN uv sync --frozen

# Copy project
COPY . .

# Expose Django port
EXPOSE 8000

# AUTO RUN SERVER
CMD ["uv", "run", "python", "manage.py", "runserver", "0.0.0.0:8000"]
