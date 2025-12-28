FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y ffmpeg aria2 curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

# Install python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Start Aria2 in the background and then start the Bot
CMD aria2c --enable-rpc --rpc-listen-all=false --rpc-listen-port=6800 --max-connection-per-server=10 --rpc-max-request-size=1024M --seed-time=0 --max-overall-upload-limit=1K & python3 main.py
