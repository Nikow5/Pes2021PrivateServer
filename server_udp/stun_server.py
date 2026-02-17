import socket
import struct
import binascii

# --- Configuration ---
HOST = '0.0.0.0'
PORT = 5730 # Standard PES UDP port range starts here
MAGIC_COOKIE = 0x2112A442

# --- STUN Protocol ---
# RFC 5389 Binding Request:
#  0                   1                   2                   3
#  0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# |0 0|     STUN Message Type     |       Message Length          |
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# |                         Magic Cookie                          |
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# |                                                               |
# |                     Transaction ID (96 bits)                  |
# |                                                               |
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

# Message Type: 0x0001 (Binding Request)
# Magic Cookie: 0x2112A442 (Big Endian)

def handle_stun_request(data, addr):
    """
    Parses a STUN Binding Request and returns a Binding Success Response
    containing the MAPPED-ADDRESS (XOR-MAPPED-ADDRESS).
    """
    if len(data) < 20:
        return None

    msg_type, msg_len, magic_cookie = struct.unpack('>HHI', data[:8])
    transaction_id = data[8:20]

    # Check Magic Cookie
    if magic_cookie != MAGIC_COOKIE:
        print(f"[UDP] Invalid Magic Cookie: {hex(magic_cookie)}")
        return None

    # Check Message Type (Binding Request = 0x0001)
    if msg_type != 0x0001:
        print(f"[UDP] Unknown Message Type: {hex(msg_type)}")
        return None

    print(f"[UDP] STUN Binding Request from {addr}")

    # --- Construct Response ---
    # Type: Binding Success Response (0x0101)
    res_type = 0x0101

    # Attributes
    # XOR-MAPPED-ADDRESS (0x0020)
    # Length: 8 bytes
    # Value: Family (1 byte), Port (2 bytes), Address (4 bytes)
    # All XOR'd with Magic Cookie (for IP) and MC high 16 bits (for Port)

    client_ip = addr[0]
    client_port = addr[1]

    # XOR Port
    # Port is XOR'd with most significant 16 bits of Magic Cookie (0x2112)
    xor_port = client_port ^ (MAGIC_COOKIE >> 16)

    # XOR Address
    # Address is XOR'd with Magic Cookie (0x2112A442)
    ip_int = struct.unpack("!I", socket.inet_aton(client_ip))[0]
    xor_ip = ip_int ^ MAGIC_COOKIE

    # Attribute Header: Type (2) + Length (2)
    attr_type = 0x0020 # XOR-MAPPED-ADDRESS
    attr_len = 8

    # Attribute Value
    # Reserved (1 byte = 0), Family (1 byte = 0x01 for IPv4)
    family = 0x01

    attr_value = struct.pack('>xBH', family, xor_port) + struct.pack('>I', xor_ip)

    payload = struct.pack('>HH', attr_type, attr_len) + attr_value

    # Response Header
    res_len = len(payload)
    header = struct.pack('>HHI', res_type, res_len, magic_cookie) + transaction_id

    return header + payload

def start_udp_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.bind((HOST, PORT))
    print(f"[*] UDP STUN Server listening on {HOST}:{PORT}")
    print(f"[*] Magic Cookie: {hex(MAGIC_COOKIE)}")

    try:
        while True:
            data, addr = server.recvfrom(1024)
            response = handle_stun_request(data, addr)
            if response:
                server.sendto(response, addr)
                print(f"[TX] Sent STUN Response to {addr}")
    except KeyboardInterrupt:
        print("\n[*] UDP Server stopping...")
    finally:
        server.close()

if __name__ == "__main__":
    start_udp_server()
