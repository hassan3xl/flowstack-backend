# 1. Start with a lightweight Python base image
FROM python:3.11-slim

# 2. Set environment variables
# PYTHONDONTWRITEBYTECODE: Prevents Python from writing .pyc files
# PYTHONUNBUFFERED: Ensures logs are output immediately to the terminal
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 3. Set the working directory inside the container
WORKDIR /app

# 4. Install system dependencies (optional, but good for Postgres/other libs)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 5. Copy your requirements file first (for caching layers)
COPY requirements.txt /app/

# 6. Install Python dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# 7. Copy the rest of your application code
COPY . /app/

# 8. Command to run when the container starts
# We use 0.0.0.0 so the container listens on all interfaces (crucial for Docker)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]