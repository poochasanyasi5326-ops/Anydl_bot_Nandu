#!/bin/bash

# 1. Update yt-dlp to ensure YouTube Mastery works (no 403 errors)
pip3 install -U yt-dlp

# 2. Start Aria2 in the background
# seed-time=0 ensures files are deleted immediately after download
aria2c --enable-rpc --rpc-listen-all=false --rpc-listen-port=6800 --max-connection-per-server=10 --seed-time=0 &

# 3. Start the Bot using main.py
# The '-u' flag ensures logs show up in Koyeb in real-time
echo "🚀 Starting AnyDL Bot..."
python3 -u main.py
