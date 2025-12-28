FROM python:3.10-slim

# Install system tools for media handling
RUN apt-get update && apt-get install -y ffmpeg aria2 curl && \
    pip3 install --no-cache-dir --upgrade yt-dlp && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy all your bot files into the container
COPY . .

# Launch Aria2 in the background and start the bot
CMD aria2c --enable-rpc --rpc-listen-all=false --rpc-listen-port=6800 --max-connection-per-server=10 --seed-time=0 & python3 main.py
