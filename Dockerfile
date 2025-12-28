FROM python:3.10-slim

# Install system dependencies for torrents and video metadata
RUN apt-get update && apt-get install -y ffmpeg aria2 curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy all files from your GitHub into the container
COPY . .

# Install libraries
RUN pip3 install --no-cache-dir -r requirements.txt

# Start Aria2 and the Bot
# We use & to run Aria2 in the background so main.py can start
CMD aria2c --enable-rpc --rpc-listen-all=false --rpc-listen-port=6800 --max-connection-per-server=10 --seed-time=0 & python3 main.py
