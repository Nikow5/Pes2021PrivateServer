import struct
import hashlib

def build_nclmio_packet(command_id, payload, sequence=0):
    """
    Encapsulates payload in NclMio packet structure.
    Header: [Command ID (2)] [Payload Length (2)] [Sequence/Checksum (4)]
    """
    # Payload Length (2 bytes)
    length = len(payload)

    # Construct Header (8 bytes)
    # Format: >H (Cmd) >H (Len) >I (Seq)
    header = struct.pack('>HHI', command_id, length, sequence)

    return header + payload
