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
python3 -m server_tcp.main &

echo "[*] Starting UDP STUN Server (Port 5730)..."
python3 -m server_udp.stun_server &

echo "[*] Starting HTTP API Server (Port 5000)..."
python3 -m server_http.api_server &

echo "[*] All servers started. Press Ctrl+C to stop."
wait
