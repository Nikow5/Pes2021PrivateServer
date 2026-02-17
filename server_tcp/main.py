import socket
import struct
import threading
import time
import sqlite3

# --- Configuration ---
HOST = '0.0.0.0'
PORT = 5739
DB_PATH = 'pes2021.db'

# --- Crypto ---
XOR_KEY = bytes([0x5B, 0x9F, 0x2E, 0x64])

def xor_crypt(data):
    """
    Cyclic XOR encryption/decryption.
    Key: 5B 9F 2E 64
    """
    return bytes([b ^ XOR_KEY[i % 4] for i, b in enumerate(data)])

# --- Database Access ---
def get_user_by_ticket(steam_ticket):
    """
    Simulates Steam Ticket validation.
    In reality, we would call Steam Web API.
    For now, we return the mock user.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Mock Logic: Assume ticket is valid and matches our TestUser
        # In prod: decode ticket -> get steam_id -> query DB
        cursor.execute("SELECT id, username, region_code FROM users LIMIT 1")
        user = cursor.fetchone()
        conn.close()
        return user
    except Exception as e:
        print(f"[DB] Error: {e}")
        return None

# --- Packet Generators ---
def create_server_entry(server_id, server_type, ip_str, port):
    """
    Creates a 32-byte Server Entry structure.
    CRITICAL: Must start with VTable 0x14285B5B0.
    """
    # 1. VTable (8 bytes, Little Endian) -> 0x14285B5B0
    vtable = struct.pack('<Q', 0x14285B5B0)

    # 2. Server ID (4 bytes, Big Endian)
    sid = struct.pack('>I', server_id)

    # 3. Server Type (4 bytes, Little Endian)
    stype = struct.pack('<I', server_type)

    # 4. IP Address (4 bytes)
    ip_bytes = socket.inet_aton(ip_str)

    # 5. Port (2 bytes, Little Endian)
    port_bytes = struct.pack('<H', port)

    # Construct the payload
    payload = vtable + sid + stype + ip_bytes + port_bytes

    # Padding to 32 bytes
    padding = b'\x00' * (32 - len(payload))

    return payload + padding

# --- Connection Handler ---
def handle_client(conn, addr):
    print(f"[TCP] New connection from {addr}")
    try:
        while True:
            # Receive data
            raw_data = conn.recv(4096)
            if not raw_data:
                break

            # Decrypt
            decrypted = xor_crypt(raw_data)
            # print(f"[RX] {addr} | Len: {len(raw_data)} | Hex: {decrypted.hex()[:64]}...")

            # --- Simple State Machine Handling ---

            # HEURISTIC: State 5 - CmdLobbyInit (Steam Ticket)
            # Usually a large packet (ticket size ~200-400 bytes or more)
            # Let's assume any large packet > 64 bytes early on is Auth
            if len(decrypted) > 64:
                print(f"[TCP] Received Potential Auth Ticket (Len: {len(decrypted)})")
                user = get_user_by_ticket(decrypted)

                if user:
                    print(f"[TCP] Authenticated User: {user[1]} (ID: {user[0]})")
                    # Send Auth Success Response (CmdLobbyInit Response)
                    # Structure unknown, usually just 0x00000000 or similar success code?
                    # TODO: Reverse engineer exact response format for CmdLobbyInit
                    pass
                else:
                    print("[TCP] Auth Failed")

            # HEURISTIC: State 6 - CmdGetSvrList
            # Usually a small packet request
            if len(decrypted) < 64:
                 print(f"[TCP] Received Server List Request")

                 # Prepare Server List
                 # Entry 1: ConnectGate itself (or Game Server)
                 entry1 = create_server_entry(1, 1, "127.0.0.1", 5739)

                 # Send
                 response = xor_crypt(entry1)
                 conn.sendall(response)
                 print(f"[TX] Sent Server List Entry ({len(entry1)} bytes)")

    except ConnectionResetError:
        print(f"[TCP] Connection reset by {addr}")
    except Exception as e:
        print(f"[TCP] Error with {addr}: {e}")
    finally:
        conn.close()
        print(f"[TCP] Connection closed {addr}")

# --- Main Server Loop ---
def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server.bind((HOST, PORT))
    except OSError as e:
        print(f"[TCP] Error binding port {PORT}: {e}")
        return

    server.listen(5)
    print(f"[*] TCP Server (ConnectGate) listening on {HOST}:{PORT}")
    print(f"[*] Mode: NclMio (XOR)")

    try:
        while True:
            conn, addr = server.accept()
            t = threading.Thread(target=handle_client, args=(conn, addr))
            t.daemon = True
            t.start()
    except KeyboardInterrupt:
        print("\n[*] TCP Server stopping...")
    finally:
        server.close()

if __name__ == "__main__":
    start_server()
