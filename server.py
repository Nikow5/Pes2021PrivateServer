import socket
import struct
import threading
import time

# Configuration
HOST = '0.0.0.0'
PORT = 5739 # Standard PES port, adjust if needed

# Crypto
XOR_KEY = bytes([0x5B, 0x9F, 0x2E, 0x64])

def xor_crypt(data):
    """
    Cyclic XOR encryption/decryption.
    Key: 5B 9F 2E 64
    """
    return bytes([b ^ XOR_KEY[i % 4] for i, b in enumerate(data)])

def create_server_entry(server_id, server_type, ip_str, port):
    """
    Creates a 32-byte Server Entry structure.
    CRITICAL: Must start with VTable 0x14285B5B0.
    """
    # 1. VTable (8 bytes, Little Endian) -> 0x14285B5B0
    # B0 5B 85 42 01 00 00 00
    vtable = struct.pack('<Q', 0x14285B5B0)

    # 2. Server ID (4 bytes, Big Endian)
    sid = struct.pack('>I', server_id)

    # 3. Server Type (4 bytes, Little Endian assumed, or Big?)
    # Usually types are simple integers. Let's use Little Endian.
    stype = struct.pack('<I', server_type)

    # 4. IP Address (4 bytes)
    # e.g., "127.0.0.1" -> 7F 00 00 01
    ip_bytes = socket.inet_aton(ip_str)

    # 5. Port (2 bytes, Little Endian)
    port_bytes = struct.pack('<H', port)

    # Construct the payload
    # VTable (8) + ID (4) + Type (4) + IP (4) + Port (2) = 22 bytes
    payload = vtable + sid + stype + ip_bytes + port_bytes

    # Padding to 32 bytes
    padding = b'\x00' * (32 - len(payload))

    return payload + padding

def handle_client(conn, addr):
    print(f"[+] New connection from {addr}")
    try:
        while True:
            # Receive data
            data = conn.recv(4096)
            if not data:
                break

            # Decrypt
            decrypted = xor_crypt(data)
            print(f"[RX] {addr} | Raw: {len(data)} bytes | Decrypted: {decrypted.hex()}")

            # HEURISTIC: Identify Packet Type
            # Since we don't have the exact Command IDs for everything, we look at the size or content.

            # If Client sends "CmdLobbyInit" (Steam Ticket), it's likely the first packet.
            # We should probably respond with an acknowledgement or the Server List.

            # For demonstration, let's blindly send back a Server List if the packet seems to be a request.
            # In a real scenario, check the Command ID (bytes 0-2 usually).

            # Prepare a Mock Server List Response
            # Entry 1: Test Server
            entry1 = create_server_entry(1, 1, "127.0.0.1", 5739)

            # If the client expects a specific header before the list, we might need to add it.
            # For now, we send the entry encrypted.
            response_payload = entry1

            # Encrypt response
            encrypted_response = xor_crypt(response_payload)

            # Send
            # conn.sendall(encrypted_response)
            # print(f"[TX] Sent Server List Entry ({len(response_payload)} bytes)")

            # Note: Uncomment the send above to enable auto-response.
            # Currently disabled to prevent confusing the client with malformed headers
            # until the header structure is confirmed.

    except ConnectionResetError:
        print(f"[-] Connection reset by {addr}")
    except Exception as e:
        print(f"[-] Error with {addr}: {e}")
    finally:
        conn.close()
        print(f"[-] Connection closed {addr}")

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"[*] PES2021 Private Server Emulator listening on {HOST}:{PORT}")
    print(f"[*] XOR Key: 5B 9F 2E 64")
    print(f"[*] Critical VTable: 0x14285B5B0")

    try:
        while True:
            conn, addr = server.accept()
            client_thread = threading.Thread(target=handle_client, args=(conn, addr))
            client_thread.start()
    except KeyboardInterrupt:
        print("\n[*] Server stopping...")
    finally:
        server.close()

if __name__ == "__main__":
    start_server()
