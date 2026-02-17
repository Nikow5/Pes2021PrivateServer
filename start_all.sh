#!/bin/bash

# Function to kill all background processes on exit
cleanup() {
    echo "Stopping all servers..."
    pkill -P $$
    exit
}

trap cleanup SIGINT

echo "[*] Initializing Database..."
python3 database/init_db.py

echo "[*] Starting TCP ConnectGate Server (Port 5739)..."
python3 server_tcp/main.py &

echo "[*] Starting UDP STUN Server (Port 5730)..."
python3 server_udp/stun_server.py &

echo "[*] Starting HTTP API Server (Port 5000)..."
python3 server_http/api_server.py &

echo "[*] All servers started. Press Ctrl+C to stop."
wait
