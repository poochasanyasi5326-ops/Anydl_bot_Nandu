FROM python:3.10-slim

# 1. Install system tools and update yt-dlp to avoid "Sign in" errors
RUN apt-get update && apt-get install -y ffmpeg aria2 curl && \
    pip3 install --no-cache-dir --upgrade yt-dlp && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2. Cache dependencies first to speed up builds
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# 3. Copy the rest of your bot code
COPY . .

# 4. Use a wrapper command that handles signals better
# Setting seed-time=0 is critical for Koyeb to free up disk space
CMD aria2c --enable-rpc --rpc-listen-all=false --rpc-listen-port=6800 --max-connection-per-server=10 --seed-time=0 & python3 main.py
