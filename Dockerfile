FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user
RUN useradd -m backend

# Copy requirements first to leverage Docker cache
COPY requirements.txt requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Set proper permissions
RUN chown -R backend:backend /app

# Switch to non-root user
USER backend

# Expose the port the app runs on
EXPOSE 8005

# Use the Python migration script as entrypoint
ENTRYPOINT ["python", "migrations/run_migrations.py"]

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8005", "--reload"] 