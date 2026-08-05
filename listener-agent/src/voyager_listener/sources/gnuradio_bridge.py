from __future__ import annotations
import socket
import struct
from typing import Iterator

def udp_cf32(host: str = "127.0.0.1", port: int = 8766, max_datagram: int = 65536) -> Iterator[list[complex]]:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((host, port))
    while True:
        raw, _ = sock.recvfrom(max_datagram)
        if len(raw) % 8:
            continue
        values = struct.unpack("<" + "ff" * (len(raw) // 8), raw)
        yield [complex(values[i], values[i + 1]) for i in range(0, len(values), 2)]
