from __future__ import annotations

import socket


class DolphinGDBError(RuntimeError):
    pass


class DolphinGDBMemory:
    """Minimal GDB remote-protocol memory transport for Dolphin.

    Dolphin's built-in PowerPC GDB stub accepts ordinary ``m`` and ``M``
    packets while emulation is running.  Keeping the implementation here small
    avoids requiring a platform-specific process-memory library on macOS.
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 55000):
        self.host = host
        self.port = port
        self.socket: socket.socket | None = None

    def connect(self) -> None:
        self.close()
        connection = socket.create_connection((self.host, self.port), timeout=2.0)
        connection.settimeout(2.0)
        self.socket = connection
        # The stub starts with control of the CPU. Continue once so the game
        # runs; Dolphin continues servicing memory packets on scheduled ticks.
        self._send_packet("c", expect_reply=False)

    def close(self) -> None:
        if self.socket is not None:
            try:
                self.socket.close()
            finally:
                self.socket = None

    def _read_byte(self) -> bytes:
        if self.socket is None:
            raise DolphinGDBError("GDB connection is closed")
        data = self.socket.recv(1)
        if not data:
            raise DolphinGDBError("Dolphin closed the GDB connection")
        return data

    def _read_packet(self) -> str:
        while self._read_byte() != b"$":
            pass
        payload = bytearray()
        while True:
            byte = self._read_byte()
            if byte == b"#":
                break
            payload.extend(byte)
        checksum_text = self._read_byte() + self._read_byte()
        expected = int(checksum_text, 16)
        actual = sum(payload) & 0xFF
        if self.socket is None:
            raise DolphinGDBError("GDB connection is closed")
        self.socket.sendall(b"+" if actual == expected else b"-")
        if actual != expected:
            raise DolphinGDBError("bad checksum from Dolphin GDB stub")
        return payload.decode("ascii")

    def _send_packet(self, command: str, *, expect_reply: bool = True) -> str:
        if self.socket is None:
            raise DolphinGDBError("GDB connection is closed")
        payload = command.encode("ascii")
        checksum = sum(payload) & 0xFF
        self.socket.sendall(b"$" + payload + f"#{checksum:02x}".encode("ascii"))
        if self._read_byte() != b"+":
            raise DolphinGDBError("Dolphin rejected a GDB packet")
        return self._read_packet() if expect_reply else ""

    def read_bytes(self, address: int, size: int) -> bytes:
        if size < 0:
            raise ValueError("negative memory read")
        reply = self._send_packet(f"m{address:x},{size:x}")
        # GDB errors are exactly E followed by a two-digit code. A successful
        # hexadecimal payload may legitimately begin with byte 0xE0-EF.
        if len(reply) == 3 and reply.startswith("E"):
            raise DolphinGDBError(f"Dolphin memory read failed: {reply}")
        try:
            result = bytes.fromhex(reply)
        except ValueError as error:
            raise DolphinGDBError(f"invalid memory reply: {reply!r}") from error
        if len(result) != size:
            raise DolphinGDBError(
                f"short Dolphin memory read: received {len(result)}, expected {size}"
            )
        return result

    def write_bytes(self, address: int, data: bytes) -> None:
        # Dolphin's stub stops replying when an M packet grows beyond its
        # internal packet buffer.  Keep each payload comfortably below that
        # limit; this also permits whole save records to be synchronized.
        maximum_chunk = 0x40
        for offset in range(0, len(data), maximum_chunk):
            chunk = data[offset:offset + maximum_chunk]
            reply = self._send_packet(
                f"M{address + offset:x},{len(chunk):x}:{chunk.hex()}"
            )
            if reply != "OK":
                raise DolphinGDBError(
                    f"Dolphin memory write failed at "
                    f"0x{address + offset:08X}: {reply}"
                )

    def __enter__(self) -> "DolphinGDBMemory":
        self.connect()
        return self

    def __exit__(self, *_args) -> None:
        self.close()
