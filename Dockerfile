# Use Python 3.10 as the base
FROM python:3.10-slim-buster

# 1. Install System Tools (This is the missing part!)
# aria2 = For downloading torrents
# ffmpeg = For processing media
RUN apt-get update && apt-get install -y \
    aria2 \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# 2. Set up the working directory
WORKDIR /app

# 3. Copy your files
COPY . .

# 4. Install Python Requirements
RUN pip install --no-cache-dir -r requirements.txt

# 5. Run the Bot
CMD ["python", "bot.py"]
