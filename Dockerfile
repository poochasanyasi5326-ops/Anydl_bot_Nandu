FROM python:3.10-slim

# 1. Install System Tools (Essential for your bot)
# FFmpeg = Video Thumbnails/Processing
# Aria2 = Torrent Downloading
RUN apt-get update && \
    apt-get install -y ffmpeg aria2 && \
    rm -rf /var/lib/apt/lists/*

# 2. Set the folder
WORKDIR /app

# 3. Copy your code into the container
COPY . .

# 4. Install Python Libraries
RUN pip install --no-cache-dir -r requirements.txt

# 5. Start the Bot
CMD ["python", "bot.py"]
