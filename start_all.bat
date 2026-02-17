@echo off
title PES2021 Private Server Launcher

echo Starting Database Initialization...
python database/init_db.py

echo Starting TCP ConnectGate Server (Port 5739)...
start "PES2021 TCP Server" python server_tcp/main.py

echo Starting UDP STUN Server (Port 5730)...
start "PES2021 UDP Server" python server_udp/stun_server.py

echo Starting HTTP API Server (Port 5000)...
start "PES2021 HTTP API" python server_http/api_server.py

echo All servers started!
pause
