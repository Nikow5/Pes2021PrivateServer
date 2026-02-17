@echo off
title PES2021 Private Server Launcher

echo Starting Database Initialization...
python database/init_db.py

echo Starting TCP ConnectGate Server (Port 10000)...
start "PES2021 TCP Server" python -m server_tcp.main

echo Starting UDP STUN Server (Port 5730)...
start "PES2021 UDP Server" python -m server_udp.stun_server

echo Starting HTTP API Server (Port 5000)...
start "PES2021 HTTP API" python -m server_http.api_server

echo All servers started!
pause
