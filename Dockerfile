FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV TZ=Europe/Paris
ENV PYTHONPATH=/app

# Default runtime command. Can be overridden for tests/backtests without
# reinstalling dependencies on every container start.
CMD ["python", "src/main.py"]
