FROM python:3.10-slim

# Install system tools: ffmpeg for screenshots, aria2 for torrents
RUN apt-get update && apt-get install -y ffmpeg aria2 curl && \
    pip3 install --no-cache-dir --upgrade yt-dlp && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

# MUST use bash run.sh to trigger the yt-dlp update script
CMD ["bash", "run.sh"]
