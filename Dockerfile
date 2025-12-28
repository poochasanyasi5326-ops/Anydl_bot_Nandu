FROM python:3.10-slim

# 1. Install system tools required for torrents and video processing
RUN apt-get update && apt-get install -y \
    ffmpeg \
    aria2 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Copy all files from your GitHub to the container
COPY . .

# 4. Install Python libraries (Pyrogram, aria2p, etc.)
RUN pip3 install --no-cache-dir -r requirements.txt

# 5. Start Aria2 (Engine) and Python (Bot) simultaneously
# --rpc-listen-all=false ensures it only listens to your bot internally
CMD aria2c --enable-rpc --rpc-listen-all=false --rpc-listen-port=6800 --max-connection-per-server=10 --rpc-max-request-size=1024M --seed-time=0 --max-overall-upload-limit=1K & python3 main.py
