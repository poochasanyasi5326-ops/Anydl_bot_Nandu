FROM python:3.10-slim

# Install system tools for media handling
RUN apt-get update && apt-get install -y ffmpeg aria2 curl && \
    pip3 install --no-cache-dir --upgrade yt-dlp && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy all your bot files
COPY . .

# IMPORTANT: Launch through run.sh to ensure updates and background processes start correctly
CMD ["bash", "run.sh"]
