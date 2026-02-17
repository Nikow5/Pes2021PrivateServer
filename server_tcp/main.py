import socket
import struct
import threading
import time
import sqlite3
from server_tcp.steam_auth import parse_steam_ticket, validate_steam_ticket, create_auth_response

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
def get_user_by_steamid(steam_id):
    """
    Retrieves or creates a user based on SteamID64.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT id, username, region_code FROM users WHERE steam_id = ?", (steam_id,))
        user = cursor.fetchone()

        if not user:
            print(f"[DB] Registering new user: {steam_id}")
            # Register new user
            cursor.execute("INSERT INTO users (steam_id, username, region_code) VALUES (?, ?, ?)",
                           (steam_id, f"User_{steam_id[-4:]}", "UNK"))
            conn.commit()

            # Initialize Stats
            user_id = cursor.lastrowid
            cursor.execute("INSERT INTO myclub_stats (user_id) VALUES (?)", (user_id,))
            conn.commit()

            # Retrieve again
            cursor.execute("SELECT id, username, region_code FROM users WHERE id = ?", (user_id,))
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
    # Expected: B0 5B 85 42 01 00 00 00
    # NOTE: Python's struct '<Q' might pack 0x14285B5B0 differently depending on interpretation.
    # 0x14285B5B0 -> B0 5B 85 42 01 00 00 00
    # Let's use explicit byte construction to be safe and match the requirement exactly.
    vtable = b'\xB0\x5B\x85\x42\x01\x00\x00\x00'

    # 2. Server ID (4 bytes, Big Endian)
    sid = struct.pack('>I', server_id)

    # 3. Server Type (4 bytes, Big Endian)
    stype = struct.pack('>I', server_type)

    # 4. IP Address (4 bytes, Network Byte Order)
    ip_bytes = socket.inet_aton(ip_str)

    # 5. Port (2 bytes, Little Endian)
    port_bytes = struct.pack('<H', port)

    # Construct the payload (22 bytes)
    payload = vtable + sid + stype + ip_bytes + port_bytes

    # Padding to 32 bytes (10 bytes)
    padding = b'\x00' * (32 - len(payload))

    return payload + padding

def create_server_list_response():
    """
    Generates the full 128-byte payload for CmdGetSvrList (0x2EE4).
    Contains 4 server entries.
    """
    # 1. Real Server (ConnectGate / Game Server)
    # Using local IP for emulation
    entry1 = create_server_entry(1, 1, "127.0.0.1", 5739)

    # 2. Dummy Server 2
    entry2 = create_server_entry(2, 1, "127.0.0.1", 10000)

    # 3. Dummy Server 3
    entry3 = create_server_entry(3, 1, "127.0.0.1", 10000)

    # 4. Dummy Server 4
    entry4 = create_server_entry(4, 1, "127.0.0.1", 10000)

    # Total Payload: 128 bytes
    return entry1 + entry2 + entry3 + entry4

def create_matchmaking_response(public_ip_str):
    """
    Constructs the response for CmdMatchmaking (0x2E04).
    CRITICAL: Must set AuthStatus (+32) and ReadyStatus (+33) to 0x01.
    Injects Public IP at +0x24.
    """
    # Size: Typically 64 bytes is sufficient for this ack.
    payload = bytearray(64)

    # +0x20 (32): AuthStatus = 1
    payload[32] = 0x01

    # +0x21 (33): ReadyStatus = 1
    payload[33] = 0x01

    # +0x24 (36): Opponent/Public IP
    if public_ip_str:
        try:
            ip_bytes = socket.inet_aton(public_ip_str)
            payload[36] = ip_bytes[0]
            payload[37] = ip_bytes[1]
            payload[38] = ip_bytes[2]
            payload[39] = ip_bytes[3]
        except:
            pass # Leave as 0.0.0.0 if invalid

    return bytes(payload)

# --- Connection Handler ---
def handle_client(conn, addr):
    print(f"[TCP] New connection from {addr}")
    # Context to store session info like Public IP from STUN Handover
    client_ctx = {"public_ip": None}

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
            # Usually a large packet > 64 bytes
            if len(decrypted) > 64:
                print(f"[TCP] Received Potential Auth Ticket (Len: {len(decrypted)})")

                # 1. Parse Packet (CmdLobbyInit)
                ticket = parse_steam_ticket(decrypted)

                # 2. Validate Ticket (Steam Web API)
                steam_id = validate_steam_ticket(ticket)

                if steam_id:
                    # 3. DB Lookup / Registration
                    user = get_user_by_steamid(steam_id)

                    if user:
                        print(f"[TCP] Authenticated User: {user['username']} (ID: {user['id']})")

                        # 4. Send Success Response (CmdMatchmaking Response Logic is also used here usually)
                        # We use create_auth_response which is basically 0x2E04 structure
                        auth_response = create_auth_response(steam_id)
                        encrypted_res = xor_crypt(auth_response)
                        conn.sendall(encrypted_res)
                        print(f"[TX] Sent Auth Response with Success Flags ({len(auth_response)} bytes)")
                    else:
                        print("[TCP] DB Error during Auth")
                else:
                    print("[TCP] Steam Ticket Invalid")

            # HEURISTIC: State 6 - CmdGetSvrList
            # Usually a small packet request, length around 32-64 bytes?
            # Or specifically looking for the "Handover" packet which contains the STUN IP.
            # The user states: "Cmd 0x2EE4" payload has IP at +0x04.
            elif len(decrypted) < 64:
                 # Check if this is explicitly CmdGetSvrList or CmdMatchmaking
                 # We don't have perfect packet ID extraction (it's XOR'd with a rolling key/mask usually)
                 # But we can infer based on content.

                 # Case A: Server List Request (Handover IP at +0x04)
                 # If we see an IP-like structure at +0x04, it's likely State 6.

                 # Case B: Matchmaking Request (CmdMatchmaking 0x2E04)
                 # Also small packet.

                 # For now, let's assume the flow is sequential: Auth -> List -> Matchmaking.
                 # But sticking to the Server List logic first if we extract an IP.

                 is_handover = False
                 if len(decrypted) >= 8:
                     # Check if bytes at 4-8 look like a valid IP (not 0.0.0.0)
                     if decrypted[4] != 0:
                         is_handover = True

                 if is_handover:
                     print(f"[TCP] Received Server List Request (CmdGetSvrList)")

                     # 1. Extract Handover IP (STUN Public IP)
                     stun_ip_bytes = decrypted[4:8]
                     try:
                         client_ctx["public_ip"] = socket.inet_ntoa(stun_ip_bytes)
                         print(f"[TCP] Captured Client Public IP (STUN): {client_ctx['public_ip']}")
                     except:
                         print("[TCP] Failed to parse STUN IP")

                     # 2. Construct Server List Response (128 bytes)
                     svr_list_payload = create_server_list_response()

                     if len(svr_list_payload) != 128:
                         print(f"[TCP] CRITICAL ERROR: Server List Payload size is {len(svr_list_payload)} != 128")

                     # 3. Encrypt and Send
                     response = xor_crypt(svr_list_payload)
                     conn.sendall(response)
                     print(f"[TX] Sent Server List (128 bytes)")

                 else:
                     # Assume Matchmaking Request (State 10 Transition)
                     # Or general KeepAlive/Ack
                     print(f"[TCP] Received Generic/Matchmaking Request (Len: {len(decrypted)})")

                     # Respond with Matchmaking/Auth Success packet to force State 10
                     # Inject the Public IP we captured earlier (or loopback if none)
                     ip_to_inject = client_ctx["public_ip"] if client_ctx["public_ip"] else "127.0.0.1"

                     mm_response = create_matchmaking_response(ip_to_inject)
                     encrypted_mm = xor_crypt(mm_response)
                     conn.sendall(encrypted_mm)
                     print(f"[TX] Sent Matchmaking/Success Response (IP: {ip_to_inject})")


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
