from __future__ import annotations


def game_id_error(raw_game_id: bytes, expected_game_id: str) -> str | None:
    """Explain a Dolphin game-ID mismatch in terms useful to the player."""

    expected = expected_game_id.encode("ascii")
    if raw_game_id == expected:
        return None
    if raw_game_id and not any(raw_game_id):
        return (
            "Dolphin memory is all zeroes. Start the patched game before the "
            "client and close every extra Dolphin instance; the memory engine "
            "can otherwise attach to the wrong process."
        )
    actual = raw_game_id.decode("ascii", "replace")
    return f"Dolphin is running {actual!r}; expected {expected_game_id!r}"


def is_expected_disconnect(error: BaseException) -> bool:
    """Return whether an exception means Dolphin was simply closed."""

    message = str(error).lower()
    return any(
        fragment in message
        for fragment in (
            "could not read memory",
            "not hooked",
            "connection is closed",
            "closed the gdb connection",
            "connection refused",
            "connection reset",
            "broken pipe",
            "short game-memory read",
        )
    )
