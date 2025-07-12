# syntax=docker/dockerfile:1

FROM python:3.11-slim

# Install dependencies
COPY requirements.txt .
RUN pip install --upgrade --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

EXPOSE 8080

# Start the FastAPI app with Gunicorn for production
#CMD ["gunicorn", "--threads", "4", "-b", "0.0.0.0:8080", "flaskr:create_app()"]
#CMD ["entrypoint.sh"]
ENTRYPOINT ["/entrypoint.sh"]
