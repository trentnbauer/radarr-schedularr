FROM python:3.11-slim
WORKDIR /app

# Install timezone data
RUN apt-get update && apt-get install -y tzdata && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy script
COPY main.py .

# Run unbuffered so logs show up instantly
CMD ["python", "-u", "main.py"]