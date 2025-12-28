#!/bin/bash

# 1. Update yt-dlp to fix YouTube 'NoneType' and 403 errors
pip3 install -U yt-dlp

# 2. Start Aria2 in the background for Magnet/Torrent support
# rpc-listen-port 6800 matches the bridge in task_manager.py
aria2c --enable-rpc --rpc-listen-all=false --rpc-listen-port=6800 --max-connection-per-server=10 --seed-time=0 &

# 3. Start the Bot
echo "🚀 Starting AnyDL Bot..."
python3 -u main.py
