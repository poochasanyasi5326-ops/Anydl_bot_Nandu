FROM python:3.10-slim

# 1. Install system tools
# ffmpeg: for screenshots/merging [cite: 3]
# aria2: for magnet links [cite: 3]
# curl: for health checks [cite: 3]
RUN apt-get update && apt-get install -y ffmpeg aria2 curl && \
    pip3 install --no-cache-dir --upgrade yt-dlp && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2. Install Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt [cite: 4]

# 3. Copy all bot files
COPY . .

# 4. CRITICAL FIX: Execute run.sh instead of running commands directly
# This ensures your 'pip3 install -U yt-dlp' in run.sh actually happens.
CMD ["bash", "run.sh"]
