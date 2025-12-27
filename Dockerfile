FROM python:3.10-slim-bookworm

# Install System Tools (aria2 for torrents, ffmpeg for media)
RUN apt-get update && apt-get install -y \
    aria2 \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "bot.py"]
