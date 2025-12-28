#!/bin/bash
pip3 install -U yt-dlp 
# Start Aria2 with a secret token to fix the "Insecure" warning in logs
aria2c --enable-rpc --rpc-listen-all=false --rpc-listen-port=6800 --rpc-secret="AnyDL_Secret_123" --max-connection-per-server=10 --seed-time=0 & 
echo "🚀 Starting AnyDL Bot..."
python3 -u main.py
