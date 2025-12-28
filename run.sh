#!/bin/bash
pip3 install -U yt-dlp 
# Start Aria2 with RPC enabled
aria2c --enable-rpc --rpc-listen-all=false --rpc-listen-port=6800 --max-connection-per-server=10 --seed-time=0 & 
echo "🚀 Starting AnyDL Bot..."
python3 -u main.py
