# We use the full image (not slim) to fix connection timeouts
FROM python:3.10

# 1. Install critical system tools
RUN apt-get update && \
    apt-get install -y aria2 ffmpeg git procps && \
    rm -rf /var/lib/apt/lists/*

# 2. Set workspace
WORKDIR /app

# 3. Install Python libraries
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy bot files
COPY . .

# 5. Run
RUN chmod +x run.sh
CMD ["./run.sh"]