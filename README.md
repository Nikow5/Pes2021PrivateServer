# PES2021 Server Emulator Project

This project aims to emulate the online services for Pro Evolution Soccer 2021 (v1.07.02).

## Architecture

The project consists of three main components:

1.  **TCP Server (ConnectGate)**: Handles authentication, server list distribution, and session management.
    *   **Port**: 5739 (TCP)
    *   **Protocol**: NclMio (XOR Encrypted)

2.  **UDP Server (STUN)**: Facilitates NAT traversal for peer-to-peer connections.
    *   **Port**: 5730-5739 or 3478 (UDP)
    *   **Protocol**: RFC 5389 (Custom Magic Cookie: `0x2112A442`)

3.  **HTTP Server (API)**: Serves game data (MyClub, Squads, User Data).
    *   **Port**: 80/443 (HTTP/HTTPS)
    *   **Endpoints**: `/api/myclub/...`

## Directory Structure

*   `database/`: Database schema and initialization scripts.
*   `server_tcp/`: TCP server implementation.
*   `server_udp/`: UDP STUN server implementation.
*   `server_http/`: HTTP API server implementation.
*   `trace.js`: Frida script for debugging client-side connections.

## Usage

(Instructions to run each server component will be added here)

## License

MIT
