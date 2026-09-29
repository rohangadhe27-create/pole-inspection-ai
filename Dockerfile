# Use official slim Python runtime
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=5000

# Install required system dependencies for OpenCV and PyMySQL
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy application source code (datasets/runs ignored via .dockerignore)
COPY . .

# Ensure storage directories exist
RUN mkdir -p static/uploads/inspections static/uploads/annotated database model

# Expose server port
EXPOSE 5000

# Run with Gunicorn production WSGI server (dynamic cloud PORT support)
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-5000} --workers 1 --timeout 120 'app:create_app()'"]
