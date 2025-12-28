FROM python:3.10-slim
# Install ffmpeg for screenshots and aria2 for magnets
RUN apt-get update && apt-get install -y ffmpeg aria2 curl && \
    pip3 install --no-cache-dir --upgrade yt-dlp && \
    rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt
COPY . .
# CRITICAL: Must run bash run.sh to start all background processes
CMD ["bash", "run.sh"]
