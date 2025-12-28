#!/bin/bash
pip3 install -U yt-dlp
# Starts Aria2 background process
aria2c --enable-rpc --rpc-listen-all=false --rpc-listen-port=6800 --max-connection-per-server=10 --seed-time=0 &
python3 -u main.py
