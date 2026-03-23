FROM python:3.11-slim

WORKDIR /app

# Install minimal system dependencies (using updated package names)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libx11-6 \
    libxext6 \
    libxrender1 \
    libxtst6 \
    libxi6 \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p /app/app/logs

# Expose port
EXPOSE 8283

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8283", "--reload"]
