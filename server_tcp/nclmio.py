import struct
import hashlib

def build_nclmio_packet(command_id, payload):
    """
    Encapsulates payload in NclMio packet structure.
    Header: [Command ID (2)] [Payload Length (2)] [Sequence/Checksum (4)]
    """
    # 1. Header Construction
    # Command ID (2 bytes, Big Endian usually for NclMio, let's try Little based on VTable)
    # Actually NclMio often uses Big Endian for network fields.
    # Let's assume the user's "Header 8 bytes" is standard.

    # Payload Length (2 bytes)
    length = len(payload)

    # Checksum/Sequence (4 bytes)
    # Often a simple sequence or 0. For now 0.
    seq = 0

    # Construct Header (8 bytes)
    # Format: >H (Cmd) >H (Len) >I (Seq) ?
    # Let's try Big Endian for NclMio network standard
    header = struct.pack('>HHI', command_id, length, seq)

    return header + payload
