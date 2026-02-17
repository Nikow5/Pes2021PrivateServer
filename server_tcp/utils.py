def get_command_id(decrypted_packet):
    """
    Parses the NclMio header to determine the Command ID based on Payload Length.
    Header Format (Decrypted):
    [0-1]: Cmd ID (Network Endian - often Big Endian in NclMio)
    [2-3]: Payload Length (Big Endian)
    [4-7]: Sequence/Checksum

    Formula from issue: cmd_id = payload_length ^ 0x2E64
    Note: The user states "taille_payload ^ 0x2E64".
    The payload length is at offset 2 (2 bytes).
    """
    if len(decrypted_packet) < 8:
        return None, 0

    # Extract Payload Length (Big Endian)
    # Why Big Endian? NclMio is usually Big Endian.
    # User example: 0x90 (144) ^ 0x2E64 = 0x2EF4.
    # If byte[2] is 0x00 and byte[3] is 0x90 -> 144.

    try:
        payload_len = struct.unpack('>H', decrypted_packet[2:4])[0]
    except:
        return None, 0

    # Calculate Command ID
    cmd_id = payload_len ^ 0x2E64

    return cmd_id, payload_len
