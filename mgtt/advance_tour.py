from __future__ import annotations

from base64 import b64decode
from collections import Counter

from .data import (
    ADVANCE_TOUR_GOLFER_ITEM,
    CUSTOM_CLUB_SETS,
    custom_club_set_item,
)


# Toadstool Tour keeps four 0x284-byte GBA transfer records in the save.  The
# in-memory save has a second working copy 0xAAAC bytes after the first.
GBA_RECORD_TABLE = 0x80234040
GBA_RECORD_MIRROR_TABLE = GBA_RECORD_TABLE + 0xAAAC
GBA_RECORD_SIZE = 0x284
GBA_RECORD_COUNT = 4
GBA_NEIL_NAME_OFFSET = 0x10
GBA_ELLA_NAME_OFFSET = 0x3C
GBA_NAME_SIZE = 0x20
# Retail builds the custom-club selector from three 16-bit masks, one each
# for its wood, iron, and wedge pages. Bit zero is the normal-club baseline;
# the 15 Advance Tour sets occupy bits 1 through 15. Older AP builds
# mistakenly treated the three unrelated bytes at 0x267 as ownership.
GBA_LEGACY_CORRUPTED_CLUB_OFFSET = 0x267
GBA_CUSTOM_CLUB_MASK_OFFSETS = (0x27E, 0x280, 0x282)
GBA_NEIL_DISTANCE_OFFSET = 0x1A
GBA_ELLA_DISTANCE_OFFSET = 0x46
GBA_NEIL_WEAK_DISTANCE = 205
GBA_ELLA_WEAK_DISTANCE = 200
GBA_NEIL_DEFAULT_DISTANCE = 305
GBA_ELLA_DEFAULT_DISTANCE = 300
GBA_NEIL_OVERPOWERED_DISTANCE = 405
GBA_ELLA_OVERPOWERED_DISTANCE = 400
GBA_DISTANCE_PROFILES = frozenset(
    {
        (GBA_NEIL_WEAK_DISTANCE, GBA_ELLA_WEAK_DISTANCE),
        (GBA_NEIL_DEFAULT_DISTANCE, GBA_ELLA_DEFAULT_DISTANCE),
        (GBA_NEIL_OVERPOWERED_DISTANCE, GBA_ELLA_OVERPOWERED_DISTANCE),
    }
)
# Priority 4's before/after-reload pair changes this retail-maintained byte
# after Joshy completes a round. It is play history, not AP ownership, and
# must be ignored when recognizing or updating an injected default profile.
GBA_PLAY_HISTORY_OFFSET = 0x27B

# Native selector order from the retail GFTE01 text table. This is deliberately
# separate from CUSTOM_CLUB_SETS: that tuple is the stable Archipelago item-ID
# order and changing it would break compatibility with already-generated rooms.
# Bit zero is Basic; these names occupy bits 1 through 15.
RETAIL_CUSTOM_CLUB_BIT_ORDER = (
    "POW",
    "Super POW",
    "Low-Fly",
    "Super Low-Fly",
    "Low-Fly Spin",
    "Backspin",
    "Super Spin",
    "Straight",
    "Super Straight",
    "Straight n' Low",
    "Sweet",
    "Super Sweet",
    "Control",
    "Sweet Control",
    "Risky",
)
assert set(RETAIL_CUSTOM_CLUB_BIT_ORDER) == set(CUSTOM_CLUB_SETS)

# Shared selector state immediately after the four transfer records. Priority
# 4's four-populated-slot save and reload pair contain 28 zero bytes, six 0x3F
# sentinels, and a final zero in both the primary and mirror state. This replaces
# the older SPS-derived 0x0003FFFF assumption.
GBA_SELECTOR_STATE = 0x80234A50
GBA_SELECTOR_MIRROR_STATE = GBA_SELECTOR_STATE + 0xAAAC
GBA_SELECTOR_TEMPLATE = bytes(28) + bytes((0x3F,)) * 6 + bytes(1)

# Capture-verified visible-name buffers. The setup buffer starts directly with
# a custom GBA name, while native golfers carry a four-byte text-control prefix.
# During play it becomes help text, so the two live player-name copies are used
# to retain the renamed golfer identity at the first tee and through the round.
SELECTED_GOLFER_TEXT = 0x802CC34C
SELECTED_GOLFER_TEXT_SIZE = 28
ACTIVE_GBA_GOLFER_NAMES = (0x804E5D84, 0x804E6728)
ACTIVE_GBA_GOLFER_NAME_SIZE = 0x20

# A retail-compatible record captured after a valid Advance Tour transfer.
# It contains the game's ordinary default Neil/Ella names, animations and
# dialogue, with no external save/container metadata. Keep every byte in the
# captured retail form: earlier builds wrote an AP tag into the first eight
# zeroes, but a byte-perfect record is safer for the native selector/validator.
_GBA_RECORD_TEMPLATE = bytearray(
    b64decode(
        "AAAAAAAAAAAAAAAAAAAAAE5laWwAAAAAAAAB4AAAAf8AAgQE/QAAAAAAAAAAAAAAAAAAAAAAAAAA"
        "AAAARWxsYQAAAAAAAAHgAQEBAwEABQYAAAAAAAAAAEtlZXAgeW91cgNoZWFkIGRvd24hAAAAAAAA"
        "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABAFdhdGNoIHlvdXIgZWxib3dz"
        "IQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABAURvbid0IG92"
        "ZXJ0aGluayBpdCEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAB"
        "AkFyZSB5b3UDZ29ubmEgc3dpbmc/AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
        "AAAAAAAAAAABA0dvb2QgbHVjayEAaXQhAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
        "AAAAAAAAAAAAAAAAAAAAAAAABFN3aW5nIGxpa2UDeW91IGFsd2F5cyBkbyEAAAAAAAAAAAAAAAAA"
        "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABURvbid0IHdvcnJ5IQNZb3UnbGwgZG8gZmluZSEA"
        "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABkxldCdzIGdvIQBiYWxsIQAAAAAA"
        "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAByU2DhsIBQEOB+gA"
        "D3FcgvkAAAAAAQAAAQABAAE="
    )
)
assert len(_GBA_RECORD_TEMPLATE) == GBA_RECORD_SIZE
# The initial injected profile inherited 480-yard test values from the SPS
# source. Keep the rest of the captured record intact while allowing generated
# slot data to choose one of the three supported distance pairs.
_GBA_RECORD_TEMPLATE[
    GBA_NEIL_DISTANCE_OFFSET:GBA_NEIL_DISTANCE_OFFSET + 2
] = GBA_NEIL_DEFAULT_DISTANCE.to_bytes(2, "big")
_GBA_RECORD_TEMPLATE[
    GBA_ELLA_DISTANCE_OFFSET:GBA_ELLA_DISTANCE_OFFSET + 2
] = GBA_ELLA_DEFAULT_DISTANCE.to_bytes(2, "big")
# Recognize and migrate profiles created by v0.7.0-v0.9.3.
GBA_RECORD_MARKER = b"APMGTT07"


def _is_default_neil_ella_record(record: bytes) -> bool:
    """Recognize the captured default pair while ignoring AP club ownership."""

    if len(record) != GBA_RECORD_SIZE:
        return False
    candidate = bytearray(record)
    if candidate.startswith(GBA_RECORD_MARKER):
        candidate[:8] = _GBA_RECORD_TEMPLATE[:8]
    # Ignore shuffled ownership while recognizing a managed profile. Also
    # ignore the three bytes overwritten by v0.7.0-v0.9.10 so those profiles
    # can be recognized and repaired in place.
    candidate[
        GBA_LEGACY_CORRUPTED_CLUB_OFFSET:
        GBA_LEGACY_CORRUPTED_CLUB_OFFSET + 3
    ] = _GBA_RECORD_TEMPLATE[
        GBA_LEGACY_CORRUPTED_CLUB_OFFSET:
        GBA_LEGACY_CORRUPTED_CLUB_OFFSET + 3
    ]
    for offset in GBA_CUSTOM_CLUB_MASK_OFFSETS:
        candidate[offset:offset + 2] = _GBA_RECORD_TEMPLATE[offset:offset + 2]
    candidate[GBA_PLAY_HISTORY_OFFSET] = _GBA_RECORD_TEMPLATE[
        GBA_PLAY_HISTORY_OFFSET
    ]
    # Recognize and migrate the 480-yard v0.7.0-v0.9.6 profile without making
    # distance a general-purpose identity check for unrelated retail golfers.
    candidate[
        GBA_NEIL_DISTANCE_OFFSET:GBA_NEIL_DISTANCE_OFFSET + 2
    ] = _GBA_RECORD_TEMPLATE[
        GBA_NEIL_DISTANCE_OFFSET:GBA_NEIL_DISTANCE_OFFSET + 2
    ]
    candidate[
        GBA_ELLA_DISTANCE_OFFSET:GBA_ELLA_DISTANCE_OFFSET + 2
    ] = _GBA_RECORD_TEMPLATE[
        GBA_ELLA_DISTANCE_OFFSET:GBA_ELLA_DISTANCE_OFFSET + 2
    ]
    return candidate == _GBA_RECORD_TEMPLATE


def _decode_record_name(record: bytes, offset: int) -> str | None:
    """Decode one bounded Advance Tour display name from a transfer record."""

    raw = record[offset:offset + GBA_NAME_SIZE].split(b"\0", 1)[0]
    if not raw:
        return None
    try:
        name = raw.decode("ascii")
    except UnicodeDecodeError:
        return None
    if not name.isprintable():
        return None
    return name


def advance_tour_identity_for_name(memory, display_name: str) -> str | None:
    """Map a possibly renamed transferred golfer to the Neil/Ella AP role.

    Primary and mirror records must agree. Duplicate names are accepted only
    when every occurrence identifies the same role, avoiding a guessed identity
    on unusual user-created saves.
    """

    if not display_name:
        return None
    matches: set[str] = set()
    for index in range(GBA_RECORD_COUNT):
        primary = memory.read_bytes(
            GBA_RECORD_TABLE + index * GBA_RECORD_SIZE, GBA_RECORD_SIZE
        )
        mirror = memory.read_bytes(
            GBA_RECORD_MIRROR_TABLE + index * GBA_RECORD_SIZE,
            GBA_RECORD_SIZE,
        )
        if (
            len(primary) != GBA_RECORD_SIZE
            or len(mirror) != GBA_RECORD_SIZE
            or primary != mirror
            or not any(primary)
        ):
            continue
        if _decode_record_name(primary, GBA_NEIL_NAME_OFFSET) == display_name:
            matches.add("Neil")
        if _decode_record_name(primary, GBA_ELLA_NAME_OFFSET) == display_name:
            matches.add("Ella")
    return next(iter(matches)) if len(matches) == 1 else None


def selected_golfer_display_name(memory) -> str | None:
    """Return the capture-verified native or custom setup-screen name."""

    raw = memory.read_bytes(SELECTED_GOLFER_TEXT, SELECTED_GOLFER_TEXT_SIZE)
    if len(raw) != SELECTED_GOLFER_TEXT_SIZE:
        return None
    # Native UI strings begin with four non-printable control bytes; transferred
    # names begin immediately at this address.
    start = 0 if raw[:1] and 0x20 <= raw[0] < 0x7F else 4
    name_bytes = raw[start:].split(b"\0", 1)[0]
    try:
        name = name_bytes.decode("ascii")
    except UnicodeDecodeError:
        return None
    return name if name and name.isprintable() else None


def active_advance_tour_identity(memory) -> tuple[str, str] | None:
    """Return ``(role, visible name)`` from the paired live tee buffers."""

    names = []
    for address in ACTIVE_GBA_GOLFER_NAMES:
        raw = memory.read_bytes(address, ACTIVE_GBA_GOLFER_NAME_SIZE)
        if len(raw) != ACTIVE_GBA_GOLFER_NAME_SIZE:
            return None
        value = raw.split(b"\0", 1)[0]
        try:
            name = value.decode("ascii")
        except UnicodeDecodeError:
            return None
        names.append(name)
    if not names[0] or names[0] != names[1]:
        return None
    role = advance_tour_identity_for_name(memory, names[0])
    return (role, names[0]) if role is not None else None


def custom_club_mask(counts: Counter[str]) -> bytes:
    """Return one retail 16-bit ownership mask for all selector pages."""

    # Bit zero keeps the ordinary-club choice. With one earned set, this gives
    # the native eligibility routine two choices and makes the X prompt appear.
    result = 1
    for bit, club_set in enumerate(RETAIL_CUSTOM_CLUB_BIT_ORDER, start=1):
        if not counts[custom_club_set_item(club_set)]:
            continue
        result |= 1 << bit
    return result.to_bytes(2, "big")


def apply_advance_tour_items(
    memory,
    counts: Counter[str],
    golfer_distances: tuple[int, int] = (
        GBA_NEIL_DEFAULT_DISTANCE,
        GBA_ELLA_DEFAULT_DISTANCE,
    ),
) -> str | None:
    """Create/update a conservative Neil/Ella transfer profile.

    A transferred retail profile has no safe spare bytes in which to persist
    AP ownership. Consequently a byte-exact Neil/Ella record cannot be
    distinguished from a profile injected by an earlier seed after a restart.
    This routine never deletes a populated slot and never replaces a genuine
    golfer record. Injection is preferred when a primary/mirror slot is blank.
    If every slot is populated, the first internally consistent transfer pair
    is adopted for the AP Neil/Ella roles and only its three retail custom-club
    ownership masks are synchronized. Names, stats, distances, dialogue, play
    history, and the other transfer slots remain untouched. Mismatched copies
    fail closed.
    """

    if golfer_distances not in GBA_DISTANCE_PROFILES:
        raise ValueError(
            f"Unsupported Advance Tour golfer distances: {golfer_distances!r}"
        )
    neil_distance, ella_distance = golfer_distances

    record_addresses = [
        GBA_RECORD_TABLE + index * GBA_RECORD_SIZE
        for index in range(GBA_RECORD_COUNT)
    ]
    primary_records = [
        memory.read_bytes(address, GBA_RECORD_SIZE)
        for address in record_addresses
    ]
    mirror_records = [
        memory.read_bytes(
            GBA_RECORD_MIRROR_TABLE + index * GBA_RECORD_SIZE,
            GBA_RECORD_SIZE,
        )
        for index in range(GBA_RECORD_COUNT)
    ]
    if any(len(record) != GBA_RECORD_SIZE for record in (*primary_records, *mirror_records)):
        return "Advance Tour records could not be read safely; no save data was changed."

    owns_golfers = bool(counts[ADVANCE_TOUR_GOLFER_ITEM])
    mismatched_slots = {
        index
        for index, (primary, mirror) in enumerate(
            zip(primary_records, mirror_records)
        )
        if primary != mirror
    }
    paired_default_slots = [
        index
        for index, (primary, mirror) in enumerate(
            zip(primary_records, mirror_records)
        )
        if index not in mismatched_slots
        and _is_default_neil_ella_record(primary)
        and _is_default_neil_ella_record(mirror)
    ]
    blank_slots = [
        index
        for index, (primary, mirror) in enumerate(
            zip(primary_records, mirror_records)
        )
        if index not in mismatched_slots and not any(primary) and not any(mirror)
    ]
    populated_slots = {
        index
        for index, (primary, mirror) in enumerate(
            zip(primary_records, mirror_records)
        )
        if any(primary) or any(mirror)
    }
    genuine_profiles_exist = any(
        index not in paired_default_slots for index in populated_slots
    )
    if mismatched_slots:
        return (
            "Advance Tour primary/mirror records disagree in slot(s) "
            + ", ".join(str(index + 1) for index in sorted(mismatched_slots))
            + "; no transfer data was changed."
        )

    if not owns_golfers:
        # A recognized byte-for-byte Neil/Ella template is the record injected
        # by this project (including the older 480-yard variants). On the
        # documented dedicated-card workflow it must follow the current seed,
        # otherwise an earlier multiworld permanently bypasses the golfer gate.
        # Never erase an unrecognized/custom Advance Tour profile.
        for index in paired_default_slots:
            primary_address = GBA_RECORD_TABLE + index * GBA_RECORD_SIZE
            mirror_address = GBA_RECORD_MIRROR_TABLE + index * GBA_RECORD_SIZE
            memory.write_bytes(primary_address, bytes(GBA_RECORD_SIZE))
            memory.write_bytes(mirror_address, bytes(GBA_RECORD_SIZE))
        if genuine_profiles_exist:
            return (
                "Existing custom Advance Tour golfers were preserved and may "
                "bypass the shuffled golfer gate; use a dedicated blank "
                "memory card for strict gating."
            )
        return None

    target_slot = paired_default_slots[0] if paired_default_slots else None
    if target_slot is None:
        target_slot = blank_slots[0] if blank_slots else None
    if target_slot is None:
        # A full retail card has no place for the captured default pair. The
        # selector exposes the first transfer pair as the two GBA golfers (the
        # Priority 4 card displayed Joshy/Sally from slot 1), so adopt that
        # pair without replacing it. Only the ownership mask below changes.
        target_slot = min(populated_slots) if populated_slots else None
    if target_slot is None:
        return "No usable Advance Tour transfer record was found."

    old_primary = primary_records[target_slot]
    old_mirror = mirror_records[target_slot]
    if any(old_primary):
        # Preserve retail-maintained history/stat bytes on a recognized managed
        # profile. Older tagged builds are migrated by restoring only the
        # original eight-byte header.
        record = bytearray(old_primary)
        if record.startswith(GBA_RECORD_MARKER):
            record[:8] = _GBA_RECORD_TEMPLATE[:8]
        if target_slot in paired_default_slots:
            # Repair the non-ownership bytes corrupted by the old sequential
            # three-byte encoding before installing the real retail masks.
            record[
                GBA_LEGACY_CORRUPTED_CLUB_OFFSET:
                GBA_LEGACY_CORRUPTED_CLUB_OFFSET + 3
            ] = _GBA_RECORD_TEMPLATE[
                GBA_LEGACY_CORRUPTED_CLUB_OFFSET:
                GBA_LEGACY_CORRUPTED_CLUB_OFFSET + 3
            ]
            record[
                GBA_NEIL_DISTANCE_OFFSET:GBA_NEIL_DISTANCE_OFFSET + 2
            ] = neil_distance.to_bytes(2, "big")
            record[
                GBA_ELLA_DISTANCE_OFFSET:GBA_ELLA_DISTANCE_OFFSET + 2
            ] = ella_distance.to_bytes(2, "big")
    else:
        record = bytearray(_GBA_RECORD_TEMPLATE)
        record[
            GBA_NEIL_DISTANCE_OFFSET:GBA_NEIL_DISTANCE_OFFSET + 2
        ] = neil_distance.to_bytes(2, "big")
        record[
            GBA_ELLA_DISTANCE_OFFSET:GBA_ELLA_DISTANCE_OFFSET + 2
        ] = ella_distance.to_bytes(2, "big")
    club_mask = custom_club_mask(counts)
    for offset in GBA_CUSTOM_CLUB_MASK_OFFSETS:
        record[offset:offset + 2] = club_mask
    primary_address = GBA_RECORD_TABLE + target_slot * GBA_RECORD_SIZE
    mirror_address = GBA_RECORD_MIRROR_TABLE + target_slot * GBA_RECORD_SIZE
    try:
        memory.write_bytes(primary_address, record)
        memory.write_bytes(mirror_address, record)
        if (
            memory.read_bytes(primary_address, GBA_RECORD_SIZE) != bytes(record)
            or memory.read_bytes(mirror_address, GBA_RECORD_SIZE) != bytes(record)
        ):
            raise IOError("Advance Tour record verification failed")
    except BaseException:
        # Best-effort rollback keeps a failed mirror write from leaving a slot
        # that retail will interpret as corrupt or half-transferred.
        memory.write_bytes(primary_address, old_primary)
        memory.write_bytes(mirror_address, old_mirror)
        raise

    if owns_golfers:
        # Refresh this state on every attachment. It can be reset independently
        # of the transfer records when returning to the title screen.
        memory.write_bytes(GBA_SELECTOR_STATE, GBA_SELECTOR_TEMPLATE)
        memory.write_bytes(GBA_SELECTOR_MIRROR_STATE, GBA_SELECTOR_TEMPLATE)
    return None
