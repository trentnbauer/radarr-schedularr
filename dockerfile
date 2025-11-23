FROM python:3.11-slim
WORKDIR /app

# Install timezone data
RUN apt-get update && apt-get install -y tzdata && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy script
COPY main.py .

# --- HEALTHCHECK ---
# Checks if /tmp/healthy was updated less than 120 seconds ago
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c 'import os, time, sys; file="/tmp/healthy"; sys.exit(0) if os.path.exists(file) and time.time() - os.path.getmtime(file) < 120 else sys.exit(1)'

# Run unbuffered
CMD ["python", "-u", "main.py"]

