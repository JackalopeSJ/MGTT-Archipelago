from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


class MemorySafetyError(RuntimeError):
    """Raised before a short read or an unapproved game-memory write is used."""


@dataclass(frozen=True)
class WritableRange:
    name: str
    address: int
    size: int

    @property
    def end(self) -> int:
        return self.address + self.size

    def contains(self, address: int, size: int) -> bool:
        return self.address <= address and address + size <= self.end


class GuardedMemory:
    """Require exact reads and constrain every desktop-client memory write.

    Dolphin backends can return a short byte string while a process is closing.
    Treating that data as a complete field can turn a normal disconnect into a
    bogus item/check observation.  Writes are also limited to the small set of
    ranges deliberately owned by the MGTT bridge, so a future address typo
    fails before it can touch unrelated retail state.
    """

    def __init__(self, memory, writable_ranges: Iterable[WritableRange]):
        self.memory = memory
        self.writable_ranges = tuple(writable_ranges)

    def read_bytes(self, address: int, size: int) -> bytes:
        if not isinstance(address, int) or not isinstance(size, int) or size <= 0:
            raise MemorySafetyError("invalid game-memory read request")
        data = self.memory.read_bytes(address, size)
        if not isinstance(data, (bytes, bytearray, memoryview)):
            raise MemorySafetyError(
                f"non-byte game-memory read at 0x{address:08X}"
            )
        result = bytes(data)
        if len(result) != size:
            raise MemorySafetyError(
                f"short game-memory read at 0x{address:08X}: "
                f"received {len(result)}, expected {size}"
            )
        return result

    def write_bytes(self, address: int, data: bytes) -> None:
        if not isinstance(address, int) or not isinstance(
            data, (bytes, bytearray, memoryview)
        ):
            raise MemorySafetyError("invalid game-memory write request")
        payload = bytes(data)
        if not payload:
            raise MemorySafetyError("refusing an empty game-memory write")
        allowed = next(
            (
                region
                for region in self.writable_ranges
                if region.contains(address, len(payload))
            ),
            None,
        )
        if allowed is None:
            raise MemorySafetyError(
                f"blocked unapproved game-memory write at 0x{address:08X} "
                f"({len(payload)} byte(s))"
            )
        self.memory.write_bytes(address, payload)

