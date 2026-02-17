import struct
import binascii

# --- Configuration ---
# Command IDs (Hypothetical/Heuristic based on user description)
CMD_LOBBY_INIT = 0x2EE0
CMD_MATCHMAKING = 0x2E04

# --- Steam Auth Logic ---
def parse_steam_ticket(payload):
    """
    Parses the CmdLobbyInit (0x2EE0) payload to extract the Steam Ticket.

    The user states:
    - Payload size is fixed 124 bytes.
    - Ticket starts at +0x00 or +0x04.
    - No double encryption (just transport XOR).
    """
    if len(payload) < 16:
        print("[Auth] Payload too short to contain ticket.")
        return None

    # Heuristic: The ticket is likely the bulk of the payload.
    # Steam tickets are binary blobs.
    # Let's assume it starts at offset 4 (after some header) for now,
    # or offset 0 if it's raw.

    # User says "Ticket starts generally at +0x00 or +0x04".
    # We'll treat the whole payload as the ticket container for validation.
    ticket_blob = payload

    return ticket_blob

def validate_steam_ticket(ticket_blob):
    """
    Validates the Steam Session Ticket.

    In a real scenario:
    1. Send ticket to Steam Web API (ISteamUserAuth/AuthenticateUserTicket).
    2. Receive SteamID64 if valid.

    For emulation:
    1. Mock validation.
    2. Return a valid SteamID64 if the ticket looks somewhat real (length > 0).
    """
    if not ticket_blob:
        return None

    print(f"[Auth] Validating Ticket: {binascii.hexlify(ticket_blob[:16]).decode()}... (Len: {len(ticket_blob)})")

    # Mock Success
    # Return the SteamID of our test user (76561198000000000)
    return "76561198000000000"

def create_auth_response(steam_id):
    """
    Constructs the response for CmdLobbyInit / CmdMatchmaking.
    CRITICAL: Must set AuthStatus (+32) and ReadyStatus (+33) to 0x01.
    """
    # Payload Structure (CmdMatchmaking 0x2E04 Response)
    # Size: ~64-128 bytes usually.
    # Let's construct a 64-byte payload.

    payload = bytearray(64)

    # +0x20 (32): AuthStatus = 1
    payload[32] = 0x01

    # +0x21 (33): ReadyStatus = 1
    payload[33] = 0x01

    # +0x24 (36): Public IP (Inject Public IP if known, or 0)
    # 127.0.0.1 -> 7F 00 00 01
    payload[36] = 0x7F
    payload[37] = 0x00
    payload[38] = 0x00
    payload[39] = 0x01

    return bytes(payload)
