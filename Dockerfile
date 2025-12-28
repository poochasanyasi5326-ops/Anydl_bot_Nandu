FROM python:3.10-slim

RUN apt-get update && apt-get install -y ffmpeg aria2 curl && \
    pip3 install --upgrade yt-dlp && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .
RUN pip3 install --no-cache-dir -r requirements.txt

# Step 3 & 8: Stable background engine startup
CMD aria2c --enable-rpc --rpc-listen-all=false --rpc-listen-port=6800 --max-connection-per-server=10 --seed-time=0 --max-overall-upload-limit=1K & python3 main.py
