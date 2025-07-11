# syntax=docker/dockerfile:1

FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --upgrade --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create a non-root user
RUN useradd -m appuser
USER appuser

EXPOSE 8000

# Start the FastAPI app with Gunicorn for production
CMD ["gunicorn", "--threads", "4", "0.0.0.0", "--port", "8000", "flaskr:create_app()"]