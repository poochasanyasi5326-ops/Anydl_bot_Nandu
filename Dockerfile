FROM python:3.10-slim
RUN apt-get update && apt-get install -y ffmpeg aria2 curl && \
    pip3 install --no-cache-dir --upgrade yt-dlp && \
    rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt
COPY . .
CMD ["bash", "run.sh"]
