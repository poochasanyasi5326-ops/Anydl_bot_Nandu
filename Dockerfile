# Use Python 3.10 on Debian Bookworm (Newer, Working Version)
FROM python:3.10-slim-bookworm

# 1. Install System Tools
RUN apt-get update && apt-get install -y \
    aria2 \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# 2. Set working directory
WORKDIR /app

# 3. Copy files
COPY . .

# 4. Install Python Requirements
RUN pip install --no-cache-dir -r requirements.txt

# 5. Run the Bot
CMD ["python", "bot.py"]
