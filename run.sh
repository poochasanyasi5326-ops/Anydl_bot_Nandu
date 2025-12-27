#!/bin/bash

# 1. Start Dummy Web Server (Keeps Hugging Face happy)
python3 -m http.server 7860 &

# 2. Start the Bot
# The '-u' flag forces Python to print logs immediately
echo "🚀 Starting Bot..."
python3 -u bot.py