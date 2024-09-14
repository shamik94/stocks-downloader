# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies, including gcc
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set PYTHONPATH to include /app
ENV PYTHONPATH=/app

# Copy the requirements file into the container
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Create and switch to a non-root user
RUN useradd -m celeryuser && chown -R celeryuser /app
USER celeryuser

# Specify the default command to run your Celery worker
CMD ["celery", "-A", "src.scheduler", "worker", "--beat", "--loglevel=info"]
