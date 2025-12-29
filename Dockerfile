# Use a specific minor version for stability
FROM python:3.10-slim

# Set Environment Variables
# 1. Prevents Python from writing .pyc files (keeps image clean)
# 2. Ensures logs are sent straight to the terminal without buffering
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install FFmpeg and clean up apt cache in one layer to reduce size
# --no-install-recommends avoids installing unnecessary 'suggested' packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first to leverage Docker layer caching
# If you only change your code (main.py), Docker skips reinstalling libraries
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Launch the bot
CMD ["python", "main.py"]
