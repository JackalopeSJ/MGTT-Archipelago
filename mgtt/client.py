from __future__ import annotations

import asyncio
import copy
import hashlib
import json
import platform
import re
import textwrap
import time
import zipfile
from collections import Counter, deque
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import Utils
from CommonClient import (
    ClientCommandProcessor,
    CommonContext,
    get_base_parser,
    gui_enabled,
    handle_url_arg,
    logger,
    server_loop,
)
from NetUtils import ClientStatus
from MultiServer import mark_raw

from .data import (
    APPROACH_SHOT_ITEM,
    ADVANCE_TOUR_GOLFER_ITEM,
    CLUBS,
    GAME,
    CHARACTERS,
    COIN_SHOOT_VARIANTS,
    COURSES,
    CHARACTER_MATCH_PRO_LOCATIONS,
    GOAL_ALL_PRO_CHARACTER_MATCHES,
    GOAL_ALL_RING_SHOTS,
    GOAL_ALL_TOURNAMENTS,
    GOAL_ALL_THREE,
    GOAL_LOCATION_BY_VALUE,
    ITEM_NAME_TO_ID,
    LOCATION_NAME_TO_ID,
    LEGACY_PROGRESSIVE_TOURNAMENT_MODE_ITEM,
    PER_CHARACTER_GOLFERS,
    PUTTER_RANGE_FEET,
    PUTTER_RANGE_ITEMS,
    PROGRESSIVE_CHARACTER_ITEMS,
    PROGRESSIVE_TOURNAMENT_MODE_ITEM,
    REGULAR_TOURNAMENTS,
    SINGLE_PLAYER_RING_LOCATIONS,
    STAR_TOURNAMENT_AGGREGATE_LOCATION,
    STAR_TOURNAMENTS,
    TOURNAMENT_WIN_LOCATIONS,
    character_item,
    character_club_item,
    character_putter_range_item,
    club_item,
    coin_character_location,
    mode_item,
    tournament_item,
)
from .protocol import AddressMap, ProtocolBlock
from .dolphin_gdb import DolphinGDBMemory
from .dolphin_status import game_id_error, is_expected_disconnect
from .memory_safety import GuardedMemory, WritableRange
from .game_state import (
    ACTIVE_PLAYER_OBJECT_POINTER,
    CHARACTER_SELECT_COLUMN,
    CHARACTER_SELECT_CURSOR,
    CHARACTER_SELECT_READY,
    CHARACTER_SELECT_ROSTER_LIST,
    CHARACTER_SELECT_ROW,
    CHARACTER_SELECT_STAR_SELECTED,
    CLUB_LIMITER,
    CLUB_LIMITERS,
    CURRENT_CLUB,
    CURRENT_SPIN,
    CURRENT_SPIN_SELECTION,
    CURRENT_SHOT_TYPE,
    GOLFER_UNLOCK_MASK,
    LiveGameState,
    MULLIGAN_REMAINING,
    NATIVE_MENU_MODE_IDS,
    PUTTING_MENU_CODE_TABLE,
    PUTTING_MENU_COUNT,
    PUTTING_MENU_TARGET_TABLE,
    POWER_SHOT_REMAINING,
    RING_SHOT_1P_FLAGS,
    RING_SHOT_1P_TABLE_SIZE,
    RING_SHOT_MULTIPLAYER_FLAGS,
    RESULT_MESSAGE,
    RESULT_MESSAGE_SECONDARY,
    SPEED_GOLF_LIVE_HOLE_FRAMES,
    SPEED_GOLF_FINAL_SCORE_TO_PAR,
    SPEED_GOLF_RESULT_STATE,
    STAR_GOLFER_UNLOCK_MASK,
    club_inventory_text,
    live_result_values,
    putter_range_mask,
    mode_permission_mask,
    putting_practice_difficulty_mask,
    roster_permission_mask,
    star_roster_permission_mask,
    spin_permission_mask,
    tournament_permission_mask,
)
from .advance_tour import (
    GBA_CUSTOM_CLUB_MASK_OFFSETS,
    GBA_RECORD_COUNT,
    GBA_RECORD_MIRROR_TABLE,
    GBA_RECORD_SIZE,
    GBA_RECORD_TABLE,
    GBA_SELECTOR_MIRROR_STATE,
    GBA_SELECTOR_STATE,
    GBA_SELECTOR_TEMPLATE,
)


NOTIFICATION_MIN_INTERVAL_SECONDS = 4.0
# Native popup construction is capture-safe only on the course/level setup
# screen. Preserve messages long enough for a player to finish a hole or menu
# sequence and reach that screen; inventory itself is still applied at once.
NOTIFICATION_DEFAULT_TTL_SECONDS = 600.0
NOTIFICATION_COMMAND_TTL_SECONDS = 600.0
MAX_PENDING_NOTIFICATIONS = 32
MAX_RECENT_GAME_MESSAGES = 20
CONNECTED_POLL_INTERVAL_SECONDS = 0.1
SAVE_MUTATION_GRACE_SECONDS = 5.0
CLIENT_BUILD_VERSION = "0.9.57"

RETIRED_DEBUG_ITEMS = {
    "Mode - Doubles",
    "Mode - Club Slots",
    "Mode - Match Play",
    "Mode - Skins Match",
}

LEGACY_REGULAR_TOURNAMENT_DEBUG_ALIASES = {
    f"Tournament - {tournament}": tournament_item(tournament)
    for tournament in REGULAR_TOURNAMENTS
}


def resolve_debug_name(
    requested: str, names: dict[str, int]
) -> tuple[str | None, tuple[str, ...]]:
    """Resolve an exact or unique-prefix debug name without guessing."""

    normalized = " ".join(requested.replace("_", " ").strip().lower().split())
    if not normalized:
        return None, ()
    normalized_names = {
        " ".join(name.lower().split()): name for name in names
    }
    exact = normalized_names.get(normalized)
    if exact is not None:
        return exact, (exact,)
    matches = tuple(
        sorted(
            name
            for key, name in normalized_names.items()
            if key.startswith(normalized)
        )
    )
    return (matches[0], matches) if len(matches) == 1 else (None, matches[:8])


def save_mutation_allowed(
    hook_ready_since: float | None,
    now: float | None = None,
) -> bool:
    """Wait for retail memory-card startup validation before save writes."""

    if hook_ready_since is None:
        return False
    current = time.monotonic() if now is None else now
    return current - hook_ready_since >= SAVE_MUTATION_GRACE_SECONDS


def _nonnegative_int(value) -> int:
    """Parse untrusted DataStorage values without letting replies kill the client."""

    if isinstance(value, bool):
        return 0
    try:
        parsed = int(value or 0)
    except (TypeError, ValueError, OverflowError):
        return 0
    return max(0, min(parsed, (1 << 63) - 1))


def _valid_location_id_set(values) -> set[int]:
    published_ids = set(LOCATION_NAME_TO_ID.values())
    result = set()
    for value in values:
        if isinstance(value, bool):
            continue
        try:
            location_id = int(value)
        except (TypeError, ValueError, OverflowError):
            continue
        if location_id in published_ids:
            result.add(location_id)
    return result


def client_writable_ranges(protocol_base: int) -> tuple[WritableRange, ...]:
    """Enumerate every emulated-memory range the desktop bridge may mutate."""

    return (
        WritableRange("MGAP protocol block", protocol_base, ProtocolBlock.TOTAL_SIZE),
        # Only the captured Star word (+0x04/+0x05) and the combined hidden-
        # golfer/course word (+0x06/+0x07) are writable. Older builds also
        # admitted +0x08/+0x09 for a disproven Tournament-mask mapping; keep
        # those unknown retail bytes outside the write boundary entirely.
        WritableRange("retail unlock masks", STAR_GOLFER_UNLOCK_MASK, 4),
        WritableRange(
            "character-select hidden roster slots",
            CHARACTER_SELECT_ROSTER_LIST + 12 * 4,
            4 * 4,
        ),
        WritableRange(
            "Advance Tour primary records",
            GBA_RECORD_TABLE,
            GBA_RECORD_COUNT * GBA_RECORD_SIZE,
        ),
        WritableRange(
            "Advance Tour mirror records",
            GBA_RECORD_MIRROR_TABLE,
            GBA_RECORD_COUNT * GBA_RECORD_SIZE,
        ),
        WritableRange(
            "Advance Tour selector state",
            GBA_SELECTOR_STATE,
            len(GBA_SELECTOR_TEMPLATE),
        ),
        WritableRange(
            "Advance Tour mirror selector state",
            GBA_SELECTOR_MIRROR_STATE,
            len(GBA_SELECTOR_TEMPLATE),
        ),
        *(
            WritableRange(f"player {index} club limiter", address, 4)
            for index, address in enumerate(CLUB_LIMITERS, 1)
        ),
        WritableRange("P1 club selector", CURRENT_CLUB, 4),
        WritableRange("shot type", CURRENT_SHOT_TYPE, 4),
        WritableRange(
            "single-player Ring Attack progress",
            RING_SHOT_1P_FLAGS,
            RING_SHOT_1P_TABLE_SIZE,
        ),
        *(
            WritableRange(
                f"{player_count}P Ring Attack progress",
                address,
                len(COURSES),
            )
            for player_count, address in enumerate(
                RING_SHOT_MULTIPLAYER_FLAGS, 2
            )
        ),
        *(
            WritableRange(f"player {index} Power Shots", address, 1)
            for index, address in enumerate(POWER_SHOT_REMAINING, 1)
        ),
        WritableRange("player 1 Mulligans", MULLIGAN_REMAINING[0], 1),
        WritableRange("Putting difficulty menu count", PUTTING_MENU_COUNT, 4),
        WritableRange(
            "Putting difficulty menu codes", PUTTING_MENU_CODE_TABLE, 12
        ),
        WritableRange(
            "Putting difficulty menu targets", PUTTING_MENU_TARGET_TABLE, 12
        ),
    )


def installed_mgtt_apworlds(directory: Path) -> tuple[Path, ...]:
    """Identify duplicate installed MGTT worlds without modifying them."""

    if not directory.is_dir():
        return ()
    matches = []
    for path in sorted(directory.glob("*.apworld")):
        try:
            with zipfile.ZipFile(path) as archive:
                manifests = [
                    name
                    for name in archive.namelist()
                    if name == "archipelago.json"
                    or name.endswith("/archipelago.json")
                ]
                if any(
                    json.loads(archive.read(name)).get("game") == GAME
                    for name in manifests
                ):
                    matches.append(path)
        except (OSError, zipfile.BadZipFile, KeyError, json.JSONDecodeError):
            continue
    return tuple(matches)


def warn_duplicate_installations() -> None:
    installed = installed_mgtt_apworlds(Path(Utils.user_path("custom_worlds")))
    if len(installed) > 1:
        logger.warning(
            "Multiple Mario Golf: Toadstool Tour APWorlds are installed: %s. "
            "Keep only the current mgtt.apworld, then restart Archipelago.",
            ", ".join(path.name for path in installed),
        )


@dataclass(frozen=True)
class PendingGameNotification:
    text: str
    queued_at: float
    expires_at: float


def resolve_native_golfer_name(value: str) -> str | None:
    """Resolve friendly /clubs spellings without making names ambiguous."""

    normalized = re.sub(r"[^a-z0-9]", "", value.casefold())
    if not normalized:
        return None
    aliases = {
        "dk": "Donkey Kong",
        "diddyk": "Diddy Kong",
        "bowserjunior": "Bowser Jr.",
        "petey": "Petey Piranha",
        "shadow": "Shadow Mario",
        "koopa": "Koopa Troopa",
    }
    if normalized in aliases:
        return aliases[normalized]
    exact = {
        re.sub(r"[^a-z0-9]", "", name.casefold()): name
        for name in PER_CHARACTER_GOLFERS
    }
    if normalized in exact:
        return exact[normalized]
    prefix_matches = [
        name for key, name in exact.items() if key.startswith(normalized)
    ]
    return prefix_matches[0] if len(prefix_matches) == 1 else None


class DolphinMemory:
    def __init__(self, engine):
        self.engine = engine

    def read_bytes(self, address: int, size: int) -> bytes:
        return self.engine.read_bytes(address, size)

    def write_bytes(self, address: int, data: bytes) -> None:
        self.engine.write_bytes(address, data)

    def close(self) -> None:
        if self.engine.is_hooked():
            self.engine.un_hook()


def close_dolphin_memory(memory) -> None:
    if memory is None:
        return
    close = getattr(memory, "close", None)
    if callable(close):
        close()


DEFAULT_CAPTURE_RANGES = ((0x80000000, 0x01800000),)
GDB_CAPTURE_RANGES = (
    (0x80220000, 0x00020000),
    (0x802A0000, 0x00040000),
    (0x804E0000, 0x00040000),
    (0x806C0000, 0x00020000),
)
CAPTURE_KNOWN_FIELDS = {
    "save_header": (0x8022A3C8, 16),
    "mode_selector": (0x802B2A80, 4),
    "current_course": (0x8044AFDC, 4),
    "ball_lie": (0x804E364C, 4),
    "current_hole": (0x804E68F8, 1),
    "speed_golf_live_hole_frames": (SPEED_GOLF_LIVE_HOLE_FRAMES, 4),
    "speed_golf_final_score_to_par": (SPEED_GOLF_FINAL_SCORE_TO_PAR, 4),
    "speed_golf_result_state": (SPEED_GOLF_RESULT_STATE, 4),
    "spin_selection": (CURRENT_SPIN_SELECTION, 4),
    "spin_effect": (CURRENT_SPIN, 4),
    "current_shot_type": (0x804ECD50, 4),
    "current_club": (CURRENT_CLUB, 4),
    "active_player_object_pointer": (ACTIVE_PLAYER_OBJECT_POINTER, 4),
    "result_message_primary": (RESULT_MESSAGE, 4),
    "result_message_secondary": (RESULT_MESSAGE_SECONDARY, 4),
    "ring_shot_1p_flags_by_golfer": (
        RING_SHOT_1P_FLAGS,
        RING_SHOT_1P_TABLE_SIZE,
    ),
    "ring_shot_2p_flags": (RING_SHOT_MULTIPLAYER_FLAGS[0], 6),
    "ring_shot_3p_flags": (RING_SHOT_MULTIPLAYER_FLAGS[1], 6),
    "ring_shot_4p_flags": (RING_SHOT_MULTIPLAYER_FLAGS[2], 6),
    "player_1_club_limiter": (CLUB_LIMITERS[0], 4),
    "player_2_club_limiter": (CLUB_LIMITERS[1], 4),
    "player_3_club_limiter": (CLUB_LIMITERS[2], 4),
    "player_4_club_limiter": (CLUB_LIMITERS[3], 4),
    "ball_coordinates": (0x806CB4C4, 12),
    "selected_golfer_text": (0x802CC34C, 28),
    "active_gba_golfer_name_primary": (0x804E5D84, 32),
    "active_gba_golfer_name_mirror": (0x804E6728, 32),
    "gba_slot_1_custom_club_masks": (
        GBA_RECORD_TABLE + GBA_CUSTOM_CLUB_MASK_OFFSETS[0], 6
    ),
    "gba_slot_1_custom_club_masks_mirror": (
        GBA_RECORD_MIRROR_TABLE + GBA_CUSTOM_CLUB_MASK_OFFSETS[0], 6
    ),
    "gba_custom_selector_eligible": (0x8044BAB8, 4),
    "gba_custom_selector_choice_counts": (0x8044BC14, 12),
    "character_grid_cursor": (CHARACTER_SELECT_CURSOR, 1),
    "character_grid_star_selected": (CHARACTER_SELECT_STAR_SELECTED, 1),
    "character_grid_column": (CHARACTER_SELECT_COLUMN, 4),
    "character_grid_row": (CHARACTER_SELECT_ROW, 4),
    "character_grid_ready": (CHARACTER_SELECT_READY, 4),
    "protocol_header": (0x802D6800, 0x40),
    "protocol_probe_permissions": (
        0x802D6800 + ProtocolBlock.NATIVE_PROFILE_OFFSET,
        8,
    ),
    "notification_sequences": (0x802D6A00, 8),
    # Retail's own frame-managed popup path at 0x80018F90..0x80019150 keeps
    # its object pointer and last state in small data. A future native-message
    # renderer can piggyback on this owner instead of allocating an orphan AP
    # popup. These read-only fields let controller captures validate that
    # lifecycle without enabling native AP messages.
    "retail_popup_owner_pointer": (0x802C7E10, 4),
    "retail_popup_last_state": (0x802C7E18, 4),
    "retail_popup_target_state": (0x80137CA8, 4),
}


def capture_memory_snapshot(
    memory,
    label: str,
    *,
    ranges: tuple[tuple[int, int], ...] | None = None,
    destination: Path | None = None,
    extra_metadata: dict | None = None,
) -> Path:
    """Write a read-only Dolphin RAM snapshot for MGTT hook calibration."""

    clean_label = re.sub(r"[^A-Za-z0-9_-]+", "-", label).strip("-")
    clean_label = clean_label[:48] or "snapshot"
    if destination is None:
        stamp = time.strftime("%Y%m%d-%H%M%S")
        base_destination = Path(
            Utils.user_path("logs", f"MGTT-capture-{stamp}-{clean_label}.zip")
        )
        destination = base_destination
        suffix = 2
        while destination.exists() or destination.with_suffix(
            destination.suffix + ".partial"
        ).exists():
            destination = base_destination.with_name(
                f"{base_destination.stem}-{suffix}{base_destination.suffix}"
            )
            suffix += 1
    if destination.exists():
        raise FileExistsError(f"capture destination already exists: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_suffix(destination.suffix + ".partial")
    if partial.exists():
        raise FileExistsError(f"partial capture already exists: {partial}")
    selected_ranges = ranges or (
        GDB_CAPTURE_RANGES
        if isinstance(memory, DolphinGDBMemory)
        else DEFAULT_CAPTURE_RANGES
    )
    chunk_size = 0x400 if isinstance(memory, DolphinGDBMemory) else 0x100000

    def read_exact(address: int, size: int) -> bytes:
        data = memory.read_bytes(address, size)
        if len(data) != size:
            raise IOError(
                f"short Dolphin capture read at 0x{address:08X}: "
                f"received {len(data)}, expected {size}"
            )
        return data

    known_state = {
        name: read_exact(address, size).hex()
        for name, (address, size) in CAPTURE_KNOWN_FIELDS.items()
    }
    protocol_header = bytes.fromhex(known_state["protocol_header"])
    notification_sequences = bytes.fromhex(
        known_state["notification_sequences"]
    )
    popup_offset = ProtocolBlock.ACTIVE_NOTIFICATION_PTR_OFFSET
    active_popup_pointer = int.from_bytes(
        protocol_header[popup_offset:popup_offset + 4], "big"
    )
    notification_state = {
        "write_sequence": int.from_bytes(
            notification_sequences[0:4], "big"
        ),
        "read_sequence": int.from_bytes(
            notification_sequences[4:8], "big"
        ),
        "cooldown_frames": protocol_header[
            ProtocolBlock.NOTIFICATION_COOLDOWN_OFFSET
        ],
        "active_popup_pointer": f"{active_popup_pointer:08x}",
        "retail_owner_pointer": known_state[
            "retail_popup_owner_pointer"
        ],
        "retail_last_state": int.from_bytes(
            bytes.fromhex(known_state["retail_popup_last_state"]), "big"
        ),
        "retail_target_state": int.from_bytes(
            bytes.fromhex(known_state["retail_popup_target_state"]), "big"
        ),
    }
    probe_permissions = bytes.fromhex(
        known_state["protocol_probe_permissions"]
    )

    class _CaptureTraceMemory:
        def read_bytes(self, address, size):
            probe_start = ProtocolBlock.NATIVE_PROFILE_OFFSET
            probe_end = probe_start + len(probe_permissions)
            if probe_start <= address and address + size <= probe_end:
                offset = address - probe_start
                return probe_permissions[offset:offset + size]
            return protocol_header[address:address + size]

    trace_memory = _CaptureTraceMemory()
    native_gate_trace = ProtocolBlock(trace_memory, 0).native_gate_trace()
    native_gameplay_trace = ProtocolBlock(
        trace_memory, 0
    ).native_gameplay_trace()
    native_profile = ProtocolBlock(trace_memory, 0).native_profile()
    if (
        protocol_header[:4] == b"MGAP"
        and 0x80000000 <= active_popup_pointer < 0x817FFD90
        and active_popup_pointer % 4 == 0
    ):
        popup = read_exact(active_popup_pointer, 0x270)
        notification_state.update(
            {
                "popup_child_pointer": f"{int.from_bytes(popup[0x254:0x258], 'big'):08x}",
                "popup_timer": int.from_bytes(popup[0x260:0x262], "big"),
                "popup_state": popup[0x26A],
            }
        )

    metadata = {
        "format": 2,
        "label": clean_label,
        "game_id": read_exact(0x80000000, 6).decode(
            "ascii", errors="replace"
        ),
        "ranges": [
            {"address": address, "size": size}
            for address, size in selected_ranges
        ],
        "known_state": known_state,
        "notification_state": notification_state,
        "native_gate_trace": native_gate_trace,
        "native_gameplay_trace": native_gameplay_trace,
        "native_profile": native_profile,
        "ap_star_roster_permissions": int.from_bytes(
            probe_permissions[2:4], "big"
        ),
        "ap_tournament_permissions": int.from_bytes(
            probe_permissions[6:8], "big"
        ),
    }
    if extra_metadata:
        metadata["client"] = extra_metadata
    checksums = {}
    try:
        with zipfile.ZipFile(
            partial, "w", zipfile.ZIP_DEFLATED, compresslevel=6
        ) as archive:
            archive.writestr(
                "metadata.json",
                json.dumps(metadata, indent=2, sort_keys=True) + "\n",
            )
            for address, size in selected_ranges:
                member_name = f"mem-{address:08X}-{address + size:08X}.bin"
                digest = hashlib.sha256()
                with archive.open(member_name, "w") as output:
                    offset = 0
                    while offset < size:
                        amount = min(chunk_size, size - offset)
                        data = read_exact(address + offset, amount)
                        output.write(data)
                        digest.update(data)
                        offset += amount
                checksums[member_name] = {
                    "size": size,
                    "sha256": digest.hexdigest(),
                }
            archive.writestr(
                "checksums.json",
                json.dumps(checksums, indent=2, sort_keys=True) + "\n",
            )
        partial.replace(destination)
    except BaseException:
        partial.unlink(missing_ok=True)
        raise
    return destination


class MGTTCommandProcessor(ClientCommandProcessor):
    def _cmd_dolphin(self) -> None:
        """Display the current Dolphin connection status."""

        self.output(f"Dolphin Status: {self.ctx.dolphin_status}")

    def _cmd_mgtt_status(self) -> None:
        """Show MGTT server, game bridge, active golfer, and popup status."""

        if not isinstance(self.ctx, MGTTContext):
            return
        server_status = (
            f"slot {self.ctx.slot}" if self.ctx.slot is not None else "not connected"
        )
        golfer = (
            self.ctx.live_game_state.active_golfer_display_name
            or self.ctx.live_game_state.active_native_golfer
            or self.ctx.live_game_state.active_advance_tour_golfer
            or "not detected"
        )
        self.output(
            "MGTT Status: Archipelago %s; Dolphin %s; active golfer %s; "
            "%d in-game message(s) queued."
            % (
                server_status,
                self.ctx.dolphin_status,
                golfer,
                len(self.ctx.pending_notifications),
            )
        )

    def _cmd_mgtt_inventory(self) -> None:
        """Summarize the MGTT inventory currently applied to Dolphin."""

        if not isinstance(self.ctx, MGTTContext):
            return
        if self.ctx.slot is None:
            self.output("Connect to an MGTT Archipelago slot first.")
            return
        counts = Counter(self.ctx.effective_received_item_names())
        base_golfers = sum(
            counts[item_name] >= 1 for item_name in PROGRESSIVE_CHARACTER_ITEMS
        )
        star_golfers = sum(
            counts[item_name] >= 2 for item_name in PROGRESSIVE_CHARACTER_ITEMS
        )
        modes = sorted(
            name.removeprefix("Mode - ")
            for name in counts
            if name.startswith("Mode - ") and counts[name]
        )
        regular_courses = [
            course
            for course, tournament in zip(COURSES, REGULAR_TOURNAMENTS)
            if counts[tournament_item(tournament)]
        ]
        self.output(
            "MGTT Inventory: %d base golfer(s), %d Star golfer(s), Power capacity %d, "
            "%d Mulligan(s), modes: %s; courses (regular + Star Tournament): %s."
            % (
                base_golfers,
                star_golfers,
                min(counts["Power Shot Capacity"], 9),
                counts["Mulligan"],
                ", ".join(modes) or "none",
                ", ".join(regular_courses) or "none",
            )
        )

    def _cmd_mgtt_messages(self) -> None:
        """List recent receipts and any pending native-display requests."""

        if not isinstance(self.ctx, MGTTContext):
            return
        self.ctx.prune_game_notifications()
        recent = tuple(getattr(self.ctx, "recent_game_messages", ()))
        if recent:
            self.output("MGTT recent messages: " + " | ".join(recent))
        else:
            self.output("MGTT has no recent item or command messages.")
        if self.ctx.pending_notifications:
            self.output(
                "MGTT pending native-display requests: "
                + " | ".join(
                    entry.text.replace("\x01", " / ")
                    for entry in self.ctx.pending_notifications
                )
            )
        else:
            self.output("MGTT native-display request queue is empty.")

    @mark_raw
    def _cmd_mgtt_debug_item(self, item_name: str = "") -> bool:
        """Ask the AP server to cheat in one real received item."""

        if not isinstance(self.ctx, MGTTContext):
            return False
        if not getattr(self.ctx, "debug_commands_enabled", False):
            self.output(
                "MGTT debug commands are disabled for this room. Set "
                "enable_debug_commands: true in a dedicated test YAML."
            )
            return False
        if self.ctx.slot is None:
            self.output("Connect to an MGTT Archipelago slot first.")
            return False
        requested_item = item_name.strip()
        item_name = LEGACY_REGULAR_TOURNAMENT_DEBUG_ALIASES.get(
            requested_item, requested_item
        )
        resolved, choices = resolve_debug_name(item_name, ITEM_NAME_TO_ID)
        if resolved is None:
            if not item_name.strip():
                self.output(
                    "Usage: /mgtt_debug_item <exact item name>, for example "
                    "/mgtt_debug_item Mode - Putting Practice"
                )
            elif choices:
                self.output("Ambiguous item name; matches: " + ", ".join(choices))
            else:
                self.output(f"Unknown MGTT item: {item_name.strip()!r}")
            return False
        if resolved in RETIRED_DEBUG_ITEMS:
            self.output(f"{resolved} is retired/local and cannot be granted.")
            return False
        Utils.async_start(
            self.ctx.send_msgs(
                [{"cmd": "Say", "text": f"!getitem {resolved}"}]
            ),
            name="MGTT server debug item request",
        )
        if not hasattr(self.ctx, "pending_debug_item_receipts"):
            self.ctx.pending_debug_item_receipts = deque()
        self.ctx.pending_debug_item_receipts.append(
            (resolved, time.monotonic() + 60.0)
        )
        self.output(
            f"Requested server debug item: {resolved}. The server will either "
            "send it as a real ReceivedItems entry or report that cheating is disabled."
        )
        return True

    @mark_raw
    def _cmd_mgtt_debug_check(self, location_name: str = "") -> bool:
        """Permanently complete one active MGTT location on the AP server."""

        if not isinstance(self.ctx, MGTTContext):
            return False
        if not getattr(self.ctx, "debug_commands_enabled", False):
            self.output(
                "MGTT debug commands are disabled for this room. Set "
                "enable_debug_commands: true in a dedicated test YAML."
            )
            return False
        if self.ctx.slot is None:
            self.output("Connect to an MGTT Archipelago slot first.")
            return False
        resolved, choices = resolve_debug_name(
            location_name, LOCATION_NAME_TO_ID
        )
        if resolved is None:
            if not location_name.strip():
                self.output(
                    "Usage: /mgtt_debug_check <exact location name>, for example "
                    "/mgtt_debug_check Accomplishment - Make a Chip-In"
                )
            elif choices:
                self.output(
                    "Ambiguous location name; matches: " + ", ".join(choices)
                )
            else:
                self.output(f"Unknown MGTT location: {location_name.strip()!r}")
            return False
        location_id = LOCATION_NAME_TO_ID[resolved]
        if location_id in self.ctx.checked_locations:
            self.output(f"Location is already checked: {resolved}")
            return True
        if location_id not in self.ctx.missing_locations:
            self.output(
                f"Location is not active in this seed: {resolved}. Enable its "
                "optional YAML group and regenerate if needed."
            )
            return False
        Utils.async_start(
            self.ctx.send_msgs(
                [{"cmd": "LocationChecks", "locations": [location_id]}]
            ),
            name="MGTT server debug location check",
        )
        self.output(
            f"Submitted permanent debug check: {resolved}. Archipelago will "
            "release the item placed at that location."
        )
        return True

    @mark_raw
    def _cmd_mgtt_debug_loadout(self, golfer: str = "") -> bool:
        """Grant a full standard/short-game test bag through ReceivedItems."""

        if not isinstance(self.ctx, MGTTContext):
            return False
        if not getattr(self.ctx, "debug_commands_enabled", False):
            self.output(
                "MGTT debug commands are disabled for this room. Set "
                "enable_debug_commands: true in a dedicated test YAML."
            )
            return False
        if self.ctx.slot is None:
            self.output("Connect to an MGTT Archipelago slot first.")
            return False

        requested = golfer.strip()
        resolved_golfer: str | None = None
        putter_range_scope = getattr(self.ctx, "putter_range_scope", 0)
        needs_golfer = (
            self.ctx.club_scope == 2 or putter_range_scope == 1
        )
        if needs_golfer:
            resolved_golfer = resolve_native_golfer_name(requested) or None
            if resolved_golfer not in PER_CHARACTER_GOLFERS:
                self.output(
                    "Usage: /mgtt_debug_loadout <golfer>, for example "
                    "/mgtt_debug_loadout Luigi or /mgtt_debug_loadout Neil"
                )
                return False
        if self.ctx.club_scope == 2:
            club_items = [
                character_club_item(resolved_golfer, club) for club in CLUBS
            ]
        else:
            club_items = [club_item(club) for club in CLUBS]

        putter_items = (
            [
                character_putter_range_item(resolved_golfer, feet)
                for feet in PUTTER_RANGE_FEET
            ]
            if putter_range_scope == 1
            else list(PUTTER_RANGE_ITEMS)
        )
        desired = [*club_items, *putter_items, APPROACH_SHOT_ITEM]
        owned = Counter(self.ctx.effective_received_item_names())
        missing = [item_name for item_name in desired if not owned[item_name]]
        if not missing:
            suffix = f" for {resolved_golfer}" if resolved_golfer else ""
            self.output(f"Full MGTT test loadout is already owned{suffix}.")
            return True

        Utils.async_start(
            self.ctx.send_msgs(
                [
                    {"cmd": "Say", "text": f"!getitem {item_name}"}
                    for item_name in missing
                ]
            ),
            name="MGTT server debug loadout request",
        )
        suffix = f" for {resolved_golfer}" if resolved_golfer else ""
        self.output(
            f"Requested {len(missing)} real AP loadout item(s){suffix}. "
            "Wait for ReceivedItems delivery before starting the capture."
        )
        return True

    @mark_raw
    def _cmd_mgtt_debug_power_sync(self, setting: str = "status") -> bool:
        """Temporarily disable AP Power writes for retail-baseline captures."""

        if not isinstance(self.ctx, MGTTContext):
            return False
        if not getattr(self.ctx, "debug_commands_enabled", False):
            self.output(
                "MGTT debug commands are disabled for this room. Set "
                "enable_debug_commands: true in a dedicated test YAML."
            )
            return False
        normalized = setting.strip().lower()
        if normalized in ("status", ""):
            status = "on" if self.ctx.power_sync_enabled else "off"
            self.output(f"MGTT Power capacity synchronization is {status}.")
            return True
        if normalized not in ("on", "off"):
            self.output("Usage: /mgtt_debug_power_sync on|off|status")
            return False
        self.ctx.power_sync_enabled = normalized == "on"
        self.ctx.live_game_state.last_power_values = [None, None, None, None]
        self.ctx.live_game_state.last_power_capacity = None
        if self.ctx.power_sync_enabled:
            self.output(
                "MGTT Power capacity synchronization enabled; AP inventory "
                "will be applied on the next live poll."
            )
        else:
            self.output(
                "MGTT Power capacity synchronization disabled for this "
                "session; retail now owns the live counters."
            )
        return True

    @mark_raw
    def _cmd_mgtt_diagnostics(self, label: str = "diagnostics") -> bool:
        """Write a sanitized MGTT client-state report to the AP logs folder."""

        if not isinstance(self.ctx, MGTTContext):
            return False
        try:
            destination = self.ctx.write_diagnostic_report(label)
        except Exception as error:
            logger.exception("MGTT diagnostic report failed")
            self.output(f"Could not write MGTT diagnostics: {error}")
            return False
        self.output(f"MGTT diagnostics saved to {destination}")
        return True

    @mark_raw
    def _cmd_mgtt_capture(self, label: str = "snapshot") -> bool:
        """Queue a read-only diagnostic RAM capture with a short label."""

        if not isinstance(self.ctx, MGTTContext):
            return False
        if self.ctx.dolphin_status != "Connected":
            self.output(
                "MGTT capture was not queued because the game hook is not "
                f"connected ({self.ctx.dolphin_status})."
            )
            return False
        if self.ctx.capture_request is not None:
            self.output("An MGTT capture is already queued.")
            return False
        if self.ctx.capture_in_progress is not None:
            self.output(
                f"MGTT capture {self.ctx.capture_in_progress!r} is already "
                "being written."
            )
            return False
        self.ctx.capture_request = label
        self.ctx.capture_requested_at = time.monotonic()
        self.ctx.capture_last_status = f"queued {label!r}"
        self.output(
            f"Queued MGTT capture {label!r}; keep the game on this screen."
        )
        return True

    @mark_raw
    def _cmd_mgtt_capture_status(self) -> bool:
        """Report whether a queued diagnostic capture has started or ended."""

        if not isinstance(self.ctx, MGTTContext):
            return False
        if self.ctx.capture_in_progress is not None:
            self.output(
                f"MGTT capture {self.ctx.capture_in_progress!r} is in progress."
            )
        elif self.ctx.capture_request is not None:
            age = max(
                0.0,
                time.monotonic() - (self.ctx.capture_requested_at or 0.0),
            )
            self.output(
                f"MGTT capture {self.ctx.capture_request!r} has been queued "
                f"for {age:.1f} seconds; Dolphin status: "
                f"{self.ctx.dolphin_status}."
            )
        else:
            self.output(f"MGTT capture status: {self.ctx.capture_last_status}.")
        return True

    @mark_raw
    def _cmd_clubs(self, golfer: str = "") -> bool:
        """Show owned clubs here and in the game's native popup."""

        if not isinstance(self.ctx, MGTTContext):
            return False
        if self.ctx.slot is None:
            self.output("Connect to the MGTT Archipelago slot first.")
            return False
        requested = golfer.strip()
        if self.ctx.club_scope == 2:
            if not requested:
                requested = (
                    self.ctx.live_game_state.active_native_golfer
                    or self.ctx.live_game_state.active_advance_tour_golfer
                    or ""
                )
            requested = resolve_native_golfer_name(requested) or ""
            if not requested:
                self.output(
                    "Unknown golfer. Try /clubs \"Diddy Kong\", /clubs Diddy, "
                    "or /clubs Neil."
                )
                return False
        summary = club_inventory_text(
            self.ctx.effective_received_item_names(),
            self.ctx.club_scope,
            requested or None,
        )
        self.output(summary)
        if self.ctx.dolphin_status == "Connected":
            self.ctx.queue_game_notification(
                summary, ttl=NOTIFICATION_COMMAND_TTL_SECONDS
            )
            self.output(
                "Queued in-game; it will appear during the next active hole. "
                "Inventory is already active."
            )
        else:
            self.output(
                "Dolphin is not connected; the summary was not queued in-game."
            )
        return True


class MGTTContext(CommonContext):
    game = GAME
    items_handling = 0b111
    command_processor = MGTTCommandProcessor

    def __init__(self, server_address: Optional[str], password: Optional[str]):
        super().__init__(server_address, password)
        self.dolphin_status = "Waiting for Dolphin"
        self.native_hook_profile = "unknown"
        self.address_map: Optional[AddressMap] = None
        self.allow_unverified = False
        self.goal = 0
        self.pending_notifications: deque[PendingGameNotification] = deque()
        # Keep a small client-owned inbox independently of the experimental
        # native renderer. Public rooms disable native popups, but players and
        # diagnostics should still be able to review recent real receipts.
        self.recent_game_messages: deque[str] = deque(
            maxlen=MAX_RECENT_GAME_MESSAGES
        )
        # !getitem produces a genuine ReceivedItems packet but WebHost does
        # not emit the normal ItemSend PrintJSON packet that feeds native
        # notification wording. Track only explicit debug requests and create
        # their notification after the matching inventory receipt arrives.
        self.pending_debug_item_receipts: deque[tuple[str, float]] = deque()
        self.next_notification_time = 0.0
        # August 6 controller testing links every repeated/multi-check crash to
        # retail's native popup object path (0x800246c8/0x800246cc). Keep the
        # MGTT client log authoritative until an isolated notification probe
        # proves a safe constructor and lifetime.
        self.native_game_notifications_enabled = False
        self.native_notification_scene_token: tuple[int, int] | None = None
        self.last_native_gate_trace: dict = {
            "sequence": 0,
            "roster_outcome": "unseen",
            "roster_target": None,
            "mode_outcome": "unseen",
            "mode_target": None,
            "course_outcome": "unseen",
            "course_target": None,
            "course_index": None,
            "course_is_star": None,
        }
        self.last_native_gameplay_trace: dict = {
            "spin_outcome": "unseen",
            "spin_technique": None,
            "power_outcome": "unseen",
            "power_shot_type": None,
        }
        self.submitted_location_ids: set[int] = set()
        self.dolphin_backend = "auto"
        self.gdb_host = "127.0.0.1"
        self.gdb_port = 55000
        self.tournament_character_checks = False
        self.unlock_all_character_match_courses = True
        self.ring_shot_max_players = 1
        self.gate_modes = False
        self.gate_roster = False
        self.gate_advance_tour = False
        self.gate_putting_difficulties = False
        self.debug_commands_enabled = False
        self.power_sync_enabled = True
        self.club_scope = 1
        self.putter_range_scope = 0
        self.fallback_club: str | None = None
        self.spin_scope = 0
        self.near_pin_aggregate_feet = 300
        self.congo_canopy_score_to_par = 0
        # Old rooms predate the YAML stat option and retain 0.9.7's weak pair.
        self.advance_tour_stat_profile = "weak"
        self.advance_tour_golfer_distances = (205, 200)
        self.starting_character_names: tuple[str, ...] = ()
        self.starting_mode_names: tuple[str, ...] = ()
        self.starting_tournament_names: tuple[str, ...] = ()
        self.starting_equipment_items: tuple[str, ...] = ()
        self.starting_putting_practice_items: tuple[str, ...] = ()
        self.mulligans_spent: int | None = None
        self.pending_mulligans_spent = 0
        self.coin_totals_ready = False
        self.coin_totals: dict[tuple[str, str], int] = {}
        self.pending_coin_credits: Counter[tuple[str, str]] = Counter()
        self.persistent_baseline_ready = False
        self.persistent_check_baseline: set[int] | None = None
        self.initial_persistent_snapshot: set[int] | None = None
        self.persistent_quarantined_location_ids: set[int] = set()
        self.capture_request: str | None = None
        self.capture_requested_at: float | None = None
        self.capture_in_progress: str | None = None
        self.capture_last_status = "no capture requested this session"
        self.current_item_names: tuple[str, ...] = ()
        self.live_game_state = LiveGameState()
        self.coin_storage_keys_received: set[str] = set()
        self.last_stability_warnings: tuple[str, ...] = ()
        # PopTracker cannot rely on every AP host replaying historic
        # ReceivedItems callbacks after reconnecting. Publish an authoritative
        # 0/1/2 (locked/base/Star) roster snapshot through DataStorage instead.
        self.last_tracker_golfer_snapshot: tuple[int, ...] | None = None

    async def send_msgs(self, msgs: list) -> None:
        """Log command names without exposing addresses, passwords, or data."""

        commands = [
            str(message.get("cmd", "<missing>"))
            for message in msgs
            if isinstance(message, dict)
        ]
        if commands:
            logger.debug("MGTT AP send: %s", ", ".join(commands))
        await super().send_msgs(msgs)

    def make_gui(self):
        """Return an MGTT-branded Archipelago 0.6.7 client window."""

        from kvui import GameManager

        class MGTTManager(GameManager):
            # AP 0.6.7's GameManager.print_json and on_ui_command paths
            # address log_panels["Archipelago"] directly. Renaming the sole
            # panel caused KeyError('Archipelago'), aborted UI commands before
            # their processors ran, and let incoming PrintJSON tear down the
            # websocket loop. Keep the required internal/display panel name;
            # the branded window title still identifies the MGTT client.
            logging_pairs = [("Client", "Archipelago")]
            base_title = "Archipelago Mario Golf: Toadstool Tour Client"

        return MGTTManager

    def on_ui_command(self, command: str) -> None:
        """Echo commands without relying on Kivy's hardcoded JSON panel."""

        logger.info("> %s", command)

    def update_dolphin_status(self, status: str, reason: str = "") -> None:
        """Set bridge state and announce clear connect/disconnect transitions."""

        previous = self.dolphin_status
        if previous == status:
            return
        self.dolphin_status = status
        if status == "Connected":
            logger.info(
                "MGTT game connected: Dolphin and the patched game bridge are ready."
            )
            if getattr(self, "slot", None) is not None:
                Utils.async_start(
                    self.publish_tracker_golfer_snapshot(force=True),
                    name="MGTT PopTracker golfer refresh on game connection",
                )
        elif previous == "Connected":
            detail = reason or status
            logger.info("MGTT game disconnected from Dolphin: %s", detail)
            # Never replay menu summaries or old check popups from a previous
            # Dolphin process. New AP items received while disconnected may be
            # queued afterward and remain eligible until their normal expiry.
            self.clear_game_notifications()

    def clear_game_notifications(self, *, clear_history: bool = False) -> None:
        self.pending_notifications.clear()
        self.next_notification_time = 0.0
        if clear_history:
            self.recent_game_messages.clear()

    def update_notification_scene(
        self, scene_token: tuple[int, int] | None
    ) -> int:
        """Defer queued display requests when a live-hole scene ends.

        This never touches the retail popup object.  The game remains its sole
        owner and retires an already-visible message naturally. Desktop
        requests that have not yet been published remain queued for the next
        verified safe gameplay scene; discarding them here caused multi-check
        result events to lose every message while the new result quarantine
        correctly waited through the hole transition.
        """

        previous = self.native_notification_scene_token
        deferred = 0
        if previous is not None and scene_token != previous:
            deferred = len(self.pending_notifications)
            self.next_notification_time = 0.0
            if deferred:
                logger.info(
                    "Deferred %d in-game unlock message%s until the next "
                    "safe gameplay scene.",
                    deferred,
                    "" if deferred == 1 else "s",
                )
        self.native_notification_scene_token = scene_token
        return deferred

    def diagnostic_report(self) -> dict:
        """Return support information without server addresses or passwords."""

        self.prune_game_notifications()
        counts = Counter(self.effective_received_item_names())
        address_map = self.address_map
        return {
            "format": 1,
            "client_build": CLIENT_BUILD_VERSION,
            "platform": platform.platform(),
            "archipelago": {
                "connected": self.slot is not None,
                "team": self.team,
                "slot": self.slot,
                "seed_name": self.seed_name or "",
                "seed_storage_namespace": self.seed_storage_namespace,
                "received_item_count": len(self.items_received),
                "checked_location_count": len(self.checked_locations),
                "missing_location_count": len(self.missing_locations),
                "completed_character_match_checks": sorted(
                    name
                    for name, location_id in LOCATION_NAME_TO_ID.items()
                    if location_id in self.checked_locations
                    and name.startswith("Character Match - Defeat ")
                ),
            },
            "dolphin": {
                "status": self.dolphin_status,
                "backend": self.dolphin_backend,
                "game_id": address_map.game_id if address_map else None,
                "revision": address_map.revision if address_map else None,
                "protocol_base": (
                    f"0x{address_map.protocol_base:08X}" if address_map else None
                ),
                "address_map_verified": (
                    address_map.verified if address_map else None
                ),
                "native_hook_profile": self.native_hook_profile,
            },
            "slot_options": {
                "goal": self.goal,
                "gate_roster": self.gate_roster,
                "gate_advance_tour": self.gate_advance_tour,
                "gate_modes": self.gate_modes,
                "gate_putting_difficulties": self.gate_putting_difficulties,
                "character_match_course_access": (
                    "all_courses"
                    if self.unlock_all_character_match_courses
                    else "follow_tournament_items"
                ),
                "club_scope": self.club_scope,
                "putter_range_scope": self.putter_range_scope,
                "spin_scope": self.spin_scope,
                "ring_shot_max_players": self.ring_shot_max_players,
                "near_pin_aggregate_feet": self.near_pin_aggregate_feet,
                "advance_tour_stat_profile": self.advance_tour_stat_profile,
                "advance_tour_golfer_distances": {
                    "Neil": self.advance_tour_golfer_distances[0],
                    "Ella": self.advance_tour_golfer_distances[1],
                },
                "starting_characters": list(self.starting_character_names),
                "starting_modes": list(self.starting_mode_names),
                "starting_tournaments": list(self.starting_tournament_names),
                "starting_equipment": list(self.starting_equipment_items),
                "starting_putting_practice_items": list(
                    self.starting_putting_practice_items
                ),
            },
            "inventory": {
                "effective_count": sum(counts.values()),
                "distinct_count": len(counts),
                "power_shot_capacity": min(counts["Power Shot Capacity"], 9),
                "power_sync_enabled": self.power_sync_enabled,
                "mulligans_received": counts["Mulligan"],
                "mulligans_spent": self.mulligans_spent,
            },
            "live_state": {
                "active_native_golfer": self.live_game_state.active_native_golfer,
                "active_live_player_index": (
                    self.live_game_state.active_live_player_index
                ),
                "active_advance_tour_golfer": (
                    self.live_game_state.active_advance_tour_golfer
                ),
                "active_golfer_display_name": (
                    self.live_game_state.active_golfer_display_name
                ),
                "shared_equipment_golfer": (
                    self.live_game_state.first_confirmed_round_golfer
                ),
                "resumable_round_golfer": (
                    self.live_game_state.resumable_round_golfer
                ),
                "active_coin_course": self.live_game_state.active_coin_course,
                "verified_gameplay_active": (
                    self.live_game_state.verified_gameplay_active
                ),
                "last_completed_shot_distance_feet": round(
                    self.live_game_state.last_completed_shot_distance, 2
                ),
                "last_completed_shot_lie": (
                    self.live_game_state.last_completed_shot_lie
                ),
                "last_completed_shot_club": (
                    self.live_game_state.last_completed_shot_club
                ),
                "round_holes": self.live_game_state.round_holes,
                "round_score_to_par": (
                    self.live_game_state.round_score_to_par
                ),
                "round_golfer": self.live_game_state.round_golfer,
                "round_golfer_consistent": (
                    self.live_game_state.round_golfer_consistent
                ),
                "standard_round_scoreboard_reported": (
                    self.live_game_state.standard_round_scoreboard_reported
                ),
                "power_shots_remaining": [
                    int(value)
                    for value in self.live_game_state.last_power_values
                    if value is not None
                ],
                "power_round_start_sync_active": (
                    self.live_game_state.power_round_start_sync_active
                ),
                "pending_power_refund_hole": (
                    self.live_game_state.pending_power_refund_hole
                ),
                "pending_power_refund_expected": (
                    self.live_game_state.pending_power_refund_expected
                ),
                "pending_power_refund_polls": (
                    self.live_game_state.pending_power_refund_polls
                ),
                "character_match_session_active": (
                    self.live_game_state.character_match_session_active
                ),
                "ring_attack_session_active": (
                    self.live_game_state.ring_attack_session_active
                ),
                "speed_golf_candidate_hole": (
                    self.live_game_state.speed_golf_candidate_hole
                ),
                "speed_golf_candidate_frames": (
                    self.live_game_state.speed_golf_candidate_frames
                ),
                "speed_golf_round_frames": (
                    self.live_game_state.speed_golf_round_frames
                ),
                "speed_golf_round_timed_holes": (
                    self.live_game_state.speed_golf_round_timed_holes
                ),
                "speed_golf_round_course": (
                    self.live_game_state.speed_golf_round_course
                ),
                "retail_character_match_star_mask": (
                    f"0x{(self.live_game_state.retail_character_match_star_mask or 0):04X}"
                ),
                "last_character_match_star_mask": (
                    None
                    if self.live_game_state.last_character_match_star_mask is None
                        else f"0x{self.live_game_state.last_character_match_star_mask:04X}"
                ),
                "star_tournament_progression": (
                    "constructor_forced"
                    if self.native_hook_profile
                    in {"star_menu", "star_state", "combined"}
                    else "retail_six_regular_wins"
                ),
                "notification_screen_safe": (
                    self.live_game_state.notification_screen_safe
                ),
                "notification_live_stable_polls": (
                    self.live_game_state.notification_live_stable_polls
                ),
                "notification_result_cooldown_polls": (
                    self.live_game_state.notification_result_cooldown_polls
                ),
                "native_notifications_enabled": (
                    self.native_game_notifications_enabled
                ),
                "last_hole": self.live_game_state.last_hole,
            },
            "persistence": {
                "mulligans_ready": self.mulligans_spent is not None,
                "coin_totals_ready": self.coin_totals_ready,
                "coin_keys_received": len(self.coin_storage_keys_received),
                "persistent_baseline_ready": self.persistent_baseline_ready,
            },
            "notifications": [
                {
                    "text": entry.text.replace("\x01", " / "),
                    "seconds_remaining": max(
                        0.0, entry.expires_at - time.monotonic()
                    ),
                }
                for entry in self.pending_notifications
            ],
            "recent_game_messages": list(self.recent_game_messages),
            "native_trace": {
                "gate": self.last_native_gate_trace,
                "gameplay": self.last_native_gameplay_trace,
            },
        }

    def write_diagnostic_report(self, label: str = "diagnostics") -> Path:
        clean_label = re.sub(r"[^A-Za-z0-9_-]+", "-", label).strip("-")
        clean_label = clean_label[:48] or "diagnostics"
        stamp = time.strftime("%Y%m%d-%H%M%S")
        base = Path(
            Utils.user_path(
                "logs", f"MGTT-diagnostics-{stamp}-{clean_label}.json"
            )
        )
        destination = base
        suffix = 2
        while destination.exists() or destination.with_suffix(
            destination.suffix + ".partial"
        ).exists():
            destination = base.with_name(f"{base.stem}-{suffix}{base.suffix}")
            suffix += 1
        destination.parent.mkdir(parents=True, exist_ok=True)
        partial = destination.with_suffix(destination.suffix + ".partial")
        try:
            partial.write_text(
                json.dumps(self.diagnostic_report(), indent=2, sort_keys=True)
                + "\n",
                encoding="utf-8",
            )
            partial.replace(destination)
        except BaseException:
            partial.unlink(missing_ok=True)
            raise
        return destination

    def effective_received_item_names(self) -> list[str]:
        """Return the slot inventory even when Dolphin is not attached."""

        return effective_item_names(
            [
                self.item_names.lookup_in_game(network_item.item)
                for network_item in self.items_received
            ],
            self.starting_character_names,
            self.starting_mode_names,
            (
                *self.starting_equipment_items,
                *self.starting_putting_practice_items,
                *(
                    tournament_item(name)
                    for name in self.starting_tournament_names
                ),
            ),
        )

    @property
    def seed_storage_namespace(self) -> str:
        seed = (self.seed_name or "unknown-seed").encode("utf-8")
        return hashlib.sha256(seed).hexdigest()[:16]

    @property
    def mulligan_storage_key(self) -> str:
        return (
            f"mgtt_{self.seed_storage_namespace}_mulligans_spent_"
            f"{self.team}_{self.slot}"
        )

    @property
    def persistent_baseline_storage_key(self) -> str:
        return (
            f"mgtt_{self.seed_storage_namespace}_persistent_baseline_"
            f"{self.team}_{self.slot}"
        )

    def coin_storage_key(self, variant: str, character: str) -> str:
        variant_index = COIN_SHOOT_VARIANTS.index(variant)
        character_index = CHARACTERS.index(character)
        return (
            f"mgtt_{self.seed_storage_namespace}_coin_"
            f"{self.team}_{self.slot}_{variant_index}_{character_index}"
        )

    @property
    def all_coin_storage_keys(self) -> dict[tuple[str, str], str]:
        return {
            (variant, character): self.coin_storage_key(variant, character)
            for variant in COIN_SHOOT_VARIANTS
            for character in CHARACTERS
        }

    @property
    def tracker_golfer_storage_key(self) -> str:
        """Room-local key shared with the MGTT PopTracker pack."""

        return f"mgtt_tracker_golfers_{self.team}_{self.slot}"

    def tracker_golfer_snapshot(self) -> tuple[int, ...]:
        """Return exact locked/base/Star stages in canonical roster order."""

        counts = Counter(self.effective_received_item_names())
        return tuple(
            min(2, max(0, counts[character_item(character)]))
            for character in CHARACTERS
        )

    async def publish_tracker_golfer_snapshot(
        self, *, force: bool = False
    ) -> None:
        """Make the complete golfer inventory available to PopTracker.

        A replacement operation is intentional: unlike incremental item
        callbacks this corrects stale tracker state after changing rooms,
        reconnecting, or starting the game after items were already received.
        """

        snapshot = self.tracker_golfer_snapshot()
        if not force and snapshot == self.last_tracker_golfer_snapshot:
            return
        storage_value = {
            "version": 1,
            # PopTracker item callbacks carry this zero-based inventory index.
            # Publishing the covered count prevents an AP item and the
            # authoritative snapshot from counting the same golfer twice when
            # their two websocket connections process packets in either order.
            "received_item_count": len(getattr(self, "items_received", ())),
            "stages": list(snapshot),
        }
        await self.send_msgs(
            [
                {
                    "cmd": "Set",
                    "key": self.tracker_golfer_storage_key,
                    "default": {
                        "version": 1,
                        "received_item_count": 0,
                        "stages": [0] * len(CHARACTERS),
                    },
                    "want_reply": False,
                    "operations": [
                        {"operation": "replace", "value": storage_value}
                    ],
                }
            ]
        )
        self.last_tracker_golfer_snapshot = snapshot

    def server_goal_is_complete(self) -> bool:
        """Return whether confirmed AP checks satisfy this slot's goal."""

        goal_location = GOAL_LOCATION_BY_VALUE[self.goal]
        derived = add_derived_accomplishments(
            checked_location_names(self.checked_locations)
        )
        return goal_location in derived

    async def reconcile_server_goal(self) -> bool:
        """Submit a completed meta-goal without requiring Dolphin to run."""

        if getattr(self, "finished_game", False):
            return False
        if not self.server_goal_is_complete():
            return False
        # Latch before awaiting. CommonContext resends a latched goal during a
        # later Connected packet if the socket closes during this send.
        self.finished_game = True
        await self.send_msgs(
            [
                {
                    "cmd": "StatusUpdate",
                    "status": ClientStatus.CLIENT_GOAL,
                }
            ]
        )
        logger.info(
            "MGTT goal complete from Archipelago's confirmed check history: %s",
            GOAL_LOCATION_BY_VALUE[self.goal],
        )
        return True

    async def reconcile_server_derived_checks(self) -> set[str]:
        """Submit meta-locations derived entirely from confirmed AP checks."""

        checked_names = checked_location_names(self.checked_locations)
        derived_names = add_derived_accomplishments(checked_names)
        new_names = {
            name
            for name in derived_names - checked_names
            if name in LOCATION_NAME_TO_ID
            and LOCATION_NAME_TO_ID[name] in self.missing_locations
            and LOCATION_NAME_TO_ID[name] not in self.submitted_location_ids
        }
        if new_names:
            location_ids = {
                LOCATION_NAME_TO_ID[name] for name in new_names
            }
            self.submitted_location_ids.update(location_ids)
            await self.send_msgs(
                [
                    {
                        "cmd": "LocationChecks",
                        "locations": sorted(location_ids),
                    }
                ]
            )
            for name in sorted(new_names):
                logger.info("Server-derived check complete: %s", name)
        await self.reconcile_server_goal()
        return new_names

    async def server_auth(self, password_requested: bool = False) -> None:
        if password_requested and not self.password:
            await super().server_auth(password_requested)
        # Archipelago 0.6.7 stores a connection-link username on
        # ``ctx.username``.  Promote it to ``auth`` (or prompt when absent)
        # before sending Connect.  Merely calling the base server_auth does
        # not do this and leaves URI-launched clients stuck before login.
        await self.get_username()
        logger.info("Submitting MGTT slot authentication for %r.", self.auth)
        # Send the exact registered game. Archipelago 0.6.7 permits an empty
        # game only when a non-game client tag such as TextOnly is also sent;
        # using the generic client's empty-game value without that tag causes
        # the server to correctly return InvalidGame.
        await self.send_connect()

    async def initialize_seed_storage(self, identity: tuple) -> None:
        """Subscribe to seed storage in small 0.6.7-safe packets.

        Cumulative Coin Attack added enough keys that sending SetNotify and Get
        together during Connected made WebHost failures indistinguishable from
        authentication failures.  A short deferral and bounded batches keep
        the login packet path minimal and make any storage failure non-fatal.
        """

        await asyncio.sleep(1.0)
        if identity != (self.seed_name, self.team, self.slot):
            return
        keys = [
            self.mulligan_storage_key,
            self.persistent_baseline_storage_key,
            *self.all_coin_storage_keys.values(),
        ]
        try:
            for offset in range(0, len(keys), 16):
                batch = keys[offset:offset + 16]
                await self.send_msgs([{"cmd": "SetNotify", "keys": batch}])
                await self.send_msgs([{"cmd": "Get", "keys": batch}])
                await asyncio.sleep(0)
            logger.info(
                "MGTT persistent storage initialized (%d keys).", len(keys)
            )
            await self.publish_tracker_golfer_snapshot(force=True)
        except Exception:
            # Storage-backed consumables/totals remain unavailable for this
            # connection, but a support feature must never tear down the AP
            # gameplay connection or cause an automatic reconnect loop.
            logger.exception(
                "MGTT persistent storage initialization failed; "
                "continuing without storage-backed counters."
            )

    def on_package(self, cmd: str, args: dict) -> None:
        if cmd in {
            "Connected",
            "ReceivedItems",
            "Retrieved",
            "SetReply",
            "InvalidPacket",
            "ConnectionRefused",
        }:
            logger.debug("MGTT AP received: %s", cmd)
        if cmd == "RoomInfo":
            # Archipelago 0.6.7 validates RoomInfo's seed name but does not
            # copy it onto CommonContext.  Our persistent Mulligan, save
            # baseline, and cumulative Coin Attack keys are seed-scoped, so
            # retain it before Connected constructs those DataStorage keys.
            room_seed_name = args.get("seed_name")
            if isinstance(room_seed_name, str) and room_seed_name:
                self.seed_name = room_seed_name
        elif cmd == "Connected":
            self.submitted_location_ids.clear()
            self.last_tracker_golfer_snapshot = None
            # `/mgtt_debug_power_sync off` is a temporary capture aid. Do not
            # let it leak into another authentication, where a configured
            # 7..9 capacity would silently remain at retail's six.
            self.power_sync_enabled = True
            self.live_game_state.last_power_values = [None, None, None, None]
            self.live_game_state.last_power_capacity = None
            self.live_game_state.power_round_sync_delay_polls = 0
            slot_info = self.slot_info.get(self.slot)
            slot_game = getattr(slot_info, "game", None)
            if slot_game is None and slot_info is not None:
                try:
                    slot_game = slot_info[1]
                except (IndexError, TypeError):
                    slot_game = None
            if slot_game != GAME:
                self.disconnected_intentionally = True
                raise RuntimeError(
                    f"Authenticated slot belongs to {slot_game!r}, expected {GAME!r}."
                )
            logger.info(
                "MGTT Archipelago slot authenticated: team %s, slot %s.",
                self.team,
                self.slot,
            )
            # A reconnect can attach this process to a different seed or slot.
            # Discard messages derived from the previous authenticated state.
            self.clear_game_notifications(clear_history=True)
            self.pending_debug_item_receipts.clear()
            self.native_notification_scene_token = None
            slot_data = args.get("slot_data", {})
            stability_warnings = tuple(
                str(warning)
                for warning in slot_data.get("stability_warnings", ())
                if isinstance(warning, str) and warning.strip()
            )
            if stability_warnings != self.last_stability_warnings:
                for warning in stability_warnings:
                    logger.warning("MGTT room setting warning: %s", warning)
                self.last_stability_warnings = stability_warnings
            self.goal = int(slot_data.get("goal", 1))
            self.tournament_character_checks = bool(
                slot_data.get("tournament_character_checks", False)
            )
            course_access = slot_data.get(
                "character_match_course_access", "all_courses"
            )
            self.unlock_all_character_match_courses = course_access in (
                0,
                "all_courses",
            )
            ring_player_option = int(
                slot_data.get("ring_shot_player_counts", 0)
            )
            # Published numeric values are 0=1P only, 1=1P--4P, and the newer
            # value 2=1P+2P.  Preserve that order for old rooms while giving
            # the persistence reader an exact upper boundary.
            self.ring_shot_max_players = {
                0: 1,
                1: 4,
                2: 2,
            }.get(ring_player_option, 1)
            self.gate_modes = bool(slot_data.get("shuffle_modes", False))
            self.gate_roster = bool(
                slot_data.get("shuffle_characters", False)
            )
            self.gate_advance_tour = bool(
                slot_data.get("shuffle_advance_tour_golfers", False)
            )
            self.gate_putting_difficulties = bool(
                slot_data.get(
                    "shuffle_putting_practice_difficulties", False
                )
            )
            self.debug_commands_enabled = bool(
                slot_data.get("enable_debug_commands", False)
            )
            requested_native_popups = (
                int(slot_data.get("native_popup_delivery", 0)) == 1
            )
            self.native_game_notifications_enabled = False
            if requested_native_popups:
                logger.warning(
                    "Native MGTT Archipelago popups are disabled for 1.0 "
                    "stability; received items and checks remain visible in "
                    "the MGTT client window."
                )
            self.club_scope = int(
                slot_data.get(
                    "club_scope",
                    int(bool(slot_data.get("shuffle_clubs", True))),
                )
            )
            self.putter_range_scope = int(
                slot_data.get("putter_range_scope", 0)
            )
            fallback_club = str(slot_data.get("fallback_club", ""))
            self.fallback_club = fallback_club if fallback_club else None
            self.spin_scope = int(slot_data.get("spin_unlocks", 0))
            self.near_pin_aggregate_feet = int(
                slot_data.get("near_pin_aggregate_feet", 300)
            )
            self.congo_canopy_score_to_par = int(
                slot_data.get("congo_canopy_score_to_par", 0)
            )
            stat_distances = slot_data.get("advance_tour_golfer_distances")
            if isinstance(stat_distances, dict):
                try:
                    resolved_distances = (
                        int(stat_distances["Neil"]),
                        int(stat_distances["Ella"]),
                    )
                except (KeyError, TypeError, ValueError):
                    resolved_distances = (205, 200)
            else:
                resolved_distances = (205, 200)
            supported_distances = {
                (205, 200): "weak",
                (305, 300): "standard",
                (405, 400): "overpowered",
            }
            self.advance_tour_stat_profile = supported_distances.get(
                resolved_distances, "weak"
            )
            self.advance_tour_golfer_distances = (
                resolved_distances
                if resolved_distances in supported_distances
                else (205, 200)
            )
            starting_characters = slot_data.get("starting_characters", ())
            starting_modes = slot_data.get("starting_modes", ())
            starting_tournaments = slot_data.get(
                "starting_tournament_names", ()
            )
            starting_equipment = slot_data.get("starting_equipment", ())
            starting_putting_practice = slot_data.get(
                "starting_putting_practice_items", ()
            )
            # Older generated rooms accidentally serialized these as counts.
            # Accept them without crashing; their precollected items still
            # arrive through ReceivedItems.
            self.starting_character_names = (
                tuple(str(name) for name in starting_characters)
                if isinstance(starting_characters, (list, tuple))
                else ()
            )
            self.starting_mode_names = (
                tuple(str(name) for name in starting_modes)
                if isinstance(starting_modes, (list, tuple))
                else ()
            )
            self.starting_tournament_names = (
                tuple(str(name) for name in starting_tournaments)
                if isinstance(starting_tournaments, (list, tuple))
                else ()
            )
            self.starting_equipment_items = (
                tuple(str(name) for name in starting_equipment)
                if isinstance(starting_equipment, (list, tuple))
                else ()
            )
            self.starting_putting_practice_items = (
                tuple(str(name) for name in starting_putting_practice)
                if isinstance(starting_putting_practice, (list, tuple))
                else ()
            )
            self.mulligans_spent = None
            self.coin_totals_ready = False
            self.coin_totals = {}
            self.coin_storage_keys_received.clear()
            self.pending_coin_credits.clear()
            self.persistent_baseline_ready = False
            self.persistent_check_baseline = None
            self.initial_persistent_snapshot = None
            self.persistent_quarantined_location_ids.clear()
            Utils.async_start(
                self.initialize_seed_storage(
                    (self.seed_name, self.team, self.slot)
                ),
                name="MGTT persistent storage initialization",
            )
            Utils.async_start(
                self.reconcile_server_derived_checks(),
                name="MGTT server-backed derived-check reconciliation",
            )
        elif cmd == "ReceivedItems":
            self.queue_confirmed_debug_item_receipts(args)
            Utils.async_start(
                self.publish_tracker_golfer_snapshot(),
                name="MGTT PopTracker golfer refresh after item receipt",
            )
        elif cmd == "Retrieved":
            keys = args.get("keys", {})
            if self.mulligan_storage_key in keys:
                stored = keys[self.mulligan_storage_key]
                self.mulligans_spent = (
                    _nonnegative_int(stored) + self.pending_mulligans_spent
                )
                self._flush_pending_mulligans()
            if self.persistent_baseline_storage_key in keys:
                stored = keys[self.persistent_baseline_storage_key]
                self.persistent_check_baseline = (
                    _valid_location_id_set(stored)
                    if isinstance(stored, (list, tuple))
                    else None
                )
                self.persistent_baseline_ready = True
            storage_keys = self.all_coin_storage_keys
            returned_coin_keys = {
                key for key in storage_keys.values() if key in keys
            }
            if returned_coin_keys:
                self.coin_storage_keys_received.update(returned_coin_keys)
                for identity, key in storage_keys.items():
                    if key in keys:
                        self.coin_totals[identity] = _nonnegative_int(
                            keys.get(key)
                        )
                if len(self.coin_storage_keys_received) == len(storage_keys):
                    self.coin_totals_ready = True
                    self._flush_pending_coin_credits()
        elif cmd == "SetReply":
            if args.get("key") == self.mulligan_storage_key:
                self.mulligans_spent = _nonnegative_int(args.get("value"))
            elif args.get("key") == self.persistent_baseline_storage_key:
                stored = args.get("value")
                if isinstance(stored, (list, tuple)):
                    self.persistent_check_baseline = _valid_location_id_set(stored)
                    self.persistent_baseline_ready = True
            else:
                storage_keys = self.all_coin_storage_keys
                identity = next(
                    (
                        identity
                        for identity, key in storage_keys.items()
                        if key == args.get("key")
                    ),
                    None,
                )
                if identity is not None:
                    self.coin_totals[identity] = _nonnegative_int(
                        args.get("value")
                    )
        elif cmd == "RoomUpdate" and args.get("checked_locations"):
            Utils.async_start(
                self.reconcile_server_derived_checks(),
                name="MGTT derived-check reconciliation after server update",
            )

    def queue_confirmed_debug_item_receipts(
        self, args: dict, *, now: float | None = None
    ) -> tuple[str, ...]:
        """Queue notices for !getitem receipts that lack ItemSend PrintJSON.

        Initial synchronization and ordinary inventory traffic are ignored.
        Only a still-pending explicit `/mgtt_debug_item` request can match,
        ensuring a disabled cheat command cannot fabricate an unlock popup.
        """

        if now is None:
            now = time.monotonic()
        pending = deque(
            entry
            for entry in self.pending_debug_item_receipts
            if entry[1] > now
        )
        self.pending_debug_item_receipts = pending
        start = args.get("index")
        raw_items = args.get("items", ())
        if (
            not isinstance(start, int)
            or isinstance(start, bool)
            or start <= 0
            or not isinstance(raw_items, (list, tuple))
        ):
            return ()
        delivered = self.items_received[start:start + len(raw_items)]
        queued: list[str] = []
        for network_item in delivered:
            item_name = self.item_names.lookup_in_game(network_item.item)
            match = next(
                (entry for entry in pending if entry[0] == item_name),
                None,
            )
            if match is None:
                continue
            pending.remove(match)
            if item_name == "Nothing":
                continue
            self.queue_game_notification(f"Received {item_name} (debug item)")
            queued.append(item_name)
        return tuple(queued)

    def spend_mulligans(self, count: int) -> None:
        if count <= 0:
            return
        if self.mulligans_spent is None:
            self.pending_mulligans_spent += count
            return
        self.mulligans_spent += count
        Utils.async_start(
            self.send_msgs(
                [
                    {
                        "cmd": "Set",
                        "key": self.mulligan_storage_key,
                        "default": 0,
                        "want_reply": True,
                        "operations": [{"operation": "add", "value": count}],
                    }
                ]
            )
        )

    def _flush_pending_mulligans(self) -> None:
        count = self.pending_mulligans_spent
        if count <= 0:
            return
        self.pending_mulligans_spent = 0
        Utils.async_start(
            self.send_msgs(
                [
                    {
                        "cmd": "Set",
                        "key": self.mulligan_storage_key,
                        "default": 0,
                        "want_reply": True,
                        "operations": [{"operation": "add", "value": count}],
                    }
                ]
            )
        )

    def record_coin_credit(
        self, variant: str, character: str, coins: int
    ) -> None:
        """Persist one observed Coin Attack result without reconnect credit."""

        if (
            variant not in COIN_SHOOT_VARIANTS
            or character not in CHARACTERS
            or coins <= 0
        ):
            return
        identity = (variant, character)
        if not self.coin_totals_ready:
            self.pending_coin_credits[identity] += coins
            return
        self.coin_totals[identity] = self.coin_totals.get(identity, 0) + coins
        Utils.async_start(
            self.send_msgs(
                [
                    {
                        "cmd": "Set",
                        "key": self.coin_storage_key(*identity),
                        "default": 0,
                        "want_reply": True,
                        "operations": [
                            {"operation": "add", "value": coins}
                        ],
                    }
                ]
            )
        )

    def _flush_pending_coin_credits(self) -> None:
        if not self.coin_totals_ready or not self.pending_coin_credits:
            return
        pending = self.pending_coin_credits
        self.pending_coin_credits = Counter()
        for (variant, character), coins in pending.items():
            self.record_coin_credit(variant, character, coins)

    def completed_coin_total_checks(self) -> set[str]:
        if not self.coin_totals_ready:
            return set()
        return {
            coin_character_location(variant, character)
            for (variant, character), total in self.coin_totals.items()
            if total >= 500
        }

    def reconcile_persistent_checks(self, names: set[str]) -> set[str]:
        """Suppress retail-save accomplishments that predate this AP seed.

        On the first attachment for a seed/slot, the current monotonic retail
        result tables become a server-backed baseline. Later additions remain
        reportable, while reconnects preserve the same baseline. This prevents
        a completed or reused memory card from auto-checking a new multiworld.
        """

        location_ids = {
            LOCATION_NAME_TO_ID[name]
            for name in names
            if name in LOCATION_NAME_TO_ID
        }
        # Capture the first Dolphin observation immediately, even while the
        # server-backed baseline request is in flight. If the player completes
        # a persistent check during that request, it must be compared against
        # this attachment-time snapshot instead of being folded into the
        # baseline and lost.
        if self.initial_persistent_snapshot is None:
            self.initial_persistent_snapshot = set(location_ids)
        if not self.persistent_baseline_ready:
            return set()
        if self.persistent_check_baseline is None:
            self.persistent_check_baseline = set(
                self.initial_persistent_snapshot
            )
            Utils.async_start(
                self.send_msgs(
                    [
                        {
                            "cmd": "Set",
                            "key": self.persistent_baseline_storage_key,
                            "default": [],
                            "want_reply": True,
                            "operations": [
                                {
                                    "operation": "replace",
                                    "value": sorted(
                                        self.persistent_check_baseline
                                    ),
                                }
                            ],
                        }
                    ]
                )
            )
        candidates = {
            name
            for name in names
            if LOCATION_NAME_TO_ID.get(name) not in self.persistent_check_baseline
            and LOCATION_NAME_TO_ID.get(name)
            not in self.persistent_quarantined_location_ids
        }
        # A player can clear only one Ring Attack level at a time. Six or more
        # previously-unreported 1P records appearing in a single poll is a
        # corrupt/stale-table signature, not gameplay. The August 13 safety
        # incident presented all 36 levels together plus an unrelated
        # character-tournament record. Quarantine the whole new persistent
        # burst before derived goals or LocationChecks can be emitted.
        missing = getattr(self, "missing_locations", set())
        checked = getattr(self, "checked_locations", set())
        submitted = getattr(self, "submitted_location_ids", set())
        unreported = {
            name
            for name in candidates
            if LOCATION_NAME_TO_ID[name] in missing
            and LOCATION_NAME_TO_ID[name] not in checked
            and LOCATION_NAME_TO_ID[name] not in submitted
        }
        new_ring_records = unreported.intersection(
            SINGLE_PLAYER_RING_LOCATIONS
        )
        if len(new_ring_records) >= 6:
            quarantined_ids = {
                LOCATION_NAME_TO_ID[name] for name in unreported
            }
            self.persistent_quarantined_location_ids.update(quarantined_ids)
            # The quarantined checks never reach the server, so they cannot
            # release an item burst. Also disable the native queue for the
            # remainder of this connection as defense in depth; client-log
            # messages continue normally and reconnecting a clean process can
            # restore the room's serialized preference.
            self.native_game_notifications_enabled = False
            self.clear_game_notifications()
            logger.error(
                "MGTT safety quarantine: suppressed %d persistent checks "
                "after %d 1P Ring Attack records appeared in one poll. "
                "Close Dolphin without saving and use a clean memory card.",
                len(unreported),
                len(new_ring_records),
            )
            return set()
        return candidates

    def on_print_json(self, args: dict) -> None:
        logger.debug("MGTT AP received: PrintJSON")
        suppress_native_nothing = self.suppress_native_nothing(args)
        try:
            if args.get("type") == "ItemSend":
                item = args.get("item")
                receiving = args.get("receiving")
                if (
                    receiving is not None
                    and item is not None
                    and (
                        self.slot_concerns_self(receiving)
                        or self.slot_concerns_self(item.player)
                    )
                ):
                    text = self.rawjsontotextparser(
                        copy.deepcopy(args["data"])
                    )
                    # Preserve Archipelago's complete ItemSend wording for
                    # every item, including progressive golfers.  Replacing
                    # only those items with "Unlocked Yoshi" made native
                    # messages inconsistent and hid the sending player and
                    # location that the tester explicitly wants to see.
                    if not suppress_native_nothing:
                        self.queue_game_notification(text)
            super().on_print_json(args)
        except Exception as error:
            # AP 0.6.7 may label precollected/start-inventory item text with
            # player 0's pseudo-game, "Archipelago". If that name table is
            # absent, the standard JSON parser raises KeyError and would let a
            # cosmetic message terminate server_loop. Preserve the connection
            # and show a content-only fallback instead.
            logger.warning(
                "MGTT PrintJSON formatting failed (%s: %s); using plain text.",
                type(error).__name__,
                error,
            )
            parts = args.get("data", ())
            fallback = "".join(
                str(part.get("text", ""))
                for part in parts
                if isinstance(part, dict)
            )
            fallback = " ".join(fallback.split())
            if fallback:
                logger.info("%s", fallback)
                if (
                    args.get("type") == "ItemSend"
                    and not suppress_native_nothing
                ):
                    self.queue_game_notification(fallback)

    def suppress_native_nothing(self, args: dict) -> bool:
        """Retain the compatibility hook while displaying every receipt.

        Earlier capture builds suppressed Nothing to conserve retail UI time.
        The serialized queue now has bounded cleanup, and player testing
        explicitly prefers confirmation for every Archipelago receipt.
        """

        return False

    def queue_game_notification(
        self,
        text: str,
        *,
        ttl: float = NOTIFICATION_DEFAULT_TTL_SECONDS,
        now: float | None = None,
    ) -> None:
        clean = " ".join(text.replace("\x1b", " ").split())
        if not clean:
            return
        history = getattr(self, "recent_game_messages", None)
        if history is None:
            history = deque(maxlen=MAX_RECENT_GAME_MESSAGES)
            self.recent_game_messages = history
        history.append(clean)
        if not getattr(self, "native_game_notifications_enabled", True):
            logger.debug("Native MGTT popup suppressed: %s", text)
            return
        lines = textwrap.wrap(clean, width=38, break_long_words=False)
        notification = "\x01".join(lines[:3])[:127]
        if now is None:
            now = time.monotonic()
        self.prune_game_notifications(now)
        if any(entry.text == notification for entry in self.pending_notifications):
            return
        while len(self.pending_notifications) >= MAX_PENDING_NOTIFICATIONS:
            self.pending_notifications.popleft()
        self.pending_notifications.append(
            PendingGameNotification(notification, now, now + max(0.0, ttl))
        )

    def prune_game_notifications(self, now: float | None = None) -> int:
        """Drop expired popup requests and return the number discarded."""

        if now is None:
            now = time.monotonic()
        retained = deque(
            entry
            for entry in self.pending_notifications
            if entry.expires_at > now
        )
        removed = len(self.pending_notifications) - len(retained)
        self.pending_notifications = retained
        return removed

    def flush_game_notification(
        self, protocol: ProtocolBlock, now: float | None = None
    ) -> bool:
        """Send at most one popup after the previous popup's display window."""

        if not self.pending_notifications:
            return False
        if now is None:
            now = time.monotonic()
        self.prune_game_notifications(now)
        if not self.pending_notifications:
            return False
        if now < self.next_notification_time:
            return False
        if not protocol.enqueue_notification(self.pending_notifications[0].text):
            return False
        self.pending_notifications.popleft()
        self.next_notification_time = now + NOTIFICATION_MIN_INTERVAL_SECONDS
        return True


def add_derived_accomplishments(
    checked_names: set[str], received_names: list[str] | tuple[str, ...] = ()
) -> set[str]:
    """Add meta-accomplishments that are derived from monotonic retail checks."""

    derived = set(checked_names)
    # Best Badges are the retail game's monotonic record of birdie-or-better.
    # Derive the generic transient accomplishment from a newly observed badge
    # so a short result popup cannot cause the birdie check to be missed.
    if any(name.startswith("Best Badge - ") for name in derived):
        derived.add("Accomplishment - Make a Birdie")
    all_pro_character_matches = set(CHARACTER_MATCH_PRO_LOCATIONS).issubset(
        derived
    )
    all_ring_shots = set(SINGLE_PLAYER_RING_LOCATIONS).issubset(derived)
    all_tournaments = set(TOURNAMENT_WIN_LOCATIONS).issubset(derived)
    star_tournament_wins = set(
        TOURNAMENT_WIN_LOCATIONS[len(REGULAR_TOURNAMENTS):]
    )
    if star_tournament_wins.intersection(derived):
        derived.add(STAR_TOURNAMENT_AGGREGATE_LOCATION)
    if all_tournaments:
        derived.add(GOAL_ALL_TOURNAMENTS)
    if all_pro_character_matches:
        derived.add(GOAL_ALL_PRO_CHARACTER_MATCHES)
    if all_ring_shots:
        derived.add(GOAL_ALL_RING_SHOTS)
    if all_tournaments and all_pro_character_matches and all_ring_shots:
        derived.add(GOAL_ALL_THREE)
    return derived


def checked_location_names(location_ids: set[int]) -> set[str]:
    """Resolve authoritative AP check history back to MGTT location names."""

    return {
        name
        for name, location_id in LOCATION_NAME_TO_ID.items()
        if location_id in location_ids
    }


def effective_item_names(
    received_names: list[str] | tuple[str, ...],
    starting_characters: tuple[str, ...] = (),
    starting_modes: tuple[str, ...] = (),
    starting_items: tuple[str, ...] = (),
) -> list[str]:
    """Return inventory with seed start-state items guaranteed exactly once.

    Archipelago normally includes precollected items in ``ReceivedItems``.
    Slot data is also authoritative, however, and can arrive before that list
    is populated after a reconnect.  Adding only missing first copies avoids
    accidentally promoting a starting golfer directly to their Star form.
    """

    # Retired mode items keep their published numeric IDs but are not part of
    # MGTT's Archipelago model. Normalize terminology corrections so rooms
    # generated by older APWorlds still grant the same native access.
    retired_modes = {
        "Mode - Doubles",
        "Mode - Club Slots",
        "Mode - Match Play",
        "Mode - Skins Match",
    }
    result = []
    for name in received_names:
        if name in retired_modes:
            continue
        if name == "Mode - Coin Shoot":
            name = "Mode - Coin Attack"
        elif name == LEGACY_PROGRESSIVE_TOURNAMENT_MODE_ITEM:
            name = PROGRESSIVE_TOURNAMENT_MODE_ITEM
        result.append(name)
    counts = Counter(result)
    progressive_tournament_copies = counts[PROGRESSIVE_TOURNAMENT_MODE_ITEM]
    # One combined item exposes both Tournament menus. Preserve older rooms
    # and debug grants that used either retired standalone mode name.
    if progressive_tournament_copies == 0 and counts[mode_item("Tournament")]:
        progressive_tournament_copies = 1
    if progressive_tournament_copies == 0 and counts["Mode - Star Tournament"]:
        progressive_tournament_copies = 1
    if progressive_tournament_copies >= 1 and not counts[mode_item("Tournament")]:
        result.append(mode_item("Tournament"))
        counts[mode_item("Tournament")] = 1
    guaranteed = [
        *(character_item(name) for name in starting_characters),
        *(
            PROGRESSIVE_TOURNAMENT_MODE_ITEM
            if name == "Tournament"
            else mode_item(name)
            for name in starting_modes
        ),
        *(
            "Mode - Coin Attack" if name == "Mode - Coin Shoot" else name
            for name in starting_items
            if name not in retired_modes
        ),
    ]
    for item_name in guaranteed:
        if counts[item_name] == 0:
            result.append(item_name)
            counts[item_name] = 1
    # Starting Tournament is the first progressive stage even while the
    # server's PrecollectedItems packet is still arriving.
    if (
        "Tournament" in starting_modes
        and counts[mode_item("Tournament")] == 0
    ):
        result.append(mode_item("Tournament"))
    return result


async def dolphin_sync(ctx: MGTTContext) -> None:
    hooked = False
    memory = None
    last_error = ""
    hook_wait_started: float | None = None
    hook_ready_since: float | None = None
    save_writes_announced = False
    try:
        while not ctx.exit_event.is_set():
            try:
                if not hooked:
                    backend = ctx.dolphin_backend
                    if backend == "auto":
                        backend = "gdb" if platform.system() == "Darwin" else "dme"
                    if backend == "gdb":
                        memory = DolphinGDBMemory(ctx.gdb_host, ctx.gdb_port)
                        memory.connect()
                        hooked = True
                    else:
                        try:
                            import dolphin_memory_engine as dme
                        except ImportError as error:
                            raise RuntimeError(
                                "dolphin-memory-engine is not installed; use "
                                "--dolphin-backend gdb or install mgtt/requirements.txt"
                            ) from error
                        dme.hook()
                        hooked = dme.is_hooked()
                        if hooked:
                            memory = DolphinMemory(dme)
                    if not hooked or memory is None:
                        ctx.update_dolphin_status("Waiting for Dolphin")
                        await asyncio.sleep(2)
                        continue

                assert ctx.address_map is not None
                if not ctx.address_map.verified and not ctx.allow_unverified:
                    ctx.update_dolphin_status("Address map is unverified")
                    if last_error != ctx.dolphin_status:
                        logger.error(
                            "Refusing an unverified MGTT address map. Calibrate the "
                            "game-side hook, mark the map verified, or pass "
                            "--allow-unverified for development."
                        )
                        last_error = ctx.dolphin_status
                    await asyncio.sleep(5)
                    continue

                raw_game_id = memory.read_bytes(0x80000000, 6)
                mismatch = game_id_error(raw_game_id, ctx.address_map.game_id)
                if mismatch:
                    raise RuntimeError(mismatch)

                guarded_memory = GuardedMemory(
                    memory,
                    client_writable_ranges(ctx.address_map.protocol_base),
                )
                protocol = ProtocolBlock(
                    guarded_memory, ctx.address_map.protocol_base
                )
                valid, reason = protocol.validate()
                if not valid:
                    hook_ready_since = None
                    save_writes_announced = False
                    if hook_wait_started is None:
                        hook_wait_started = time.monotonic()
                    # Dolphin's GDB stub accepts the bridge before the patched
                    # DOL has run. Keep this one-shot connection alive while
                    # waiting for the game hook to initialize.
                    if (
                        time.monotonic() - hook_wait_started >= 15
                        and "MGAP hook magic" in reason
                    ):
                        status = (
                            "GFTE01 is running, but its MGAP hook is absent. "
                            "Launch the patched Archipelago ISO, not the retail ISO."
                        )
                    else:
                        status = f"Waiting for game hook: {reason}"
                    ctx.update_dolphin_status(status, reason)
                    if status != last_error:
                        logger.warning(status)
                        last_error = status
                    await asyncio.sleep(0.5)
                    continue

                hook_wait_started = None
                if hook_ready_since is None:
                    hook_ready_since = time.monotonic()
                observed_profile = protocol.native_profile()
                ctx.last_native_gate_trace = protocol.native_gate_trace()
                ctx.last_native_gameplay_trace = (
                    protocol.native_gameplay_trace()
                )
                if observed_profile != ctx.native_hook_profile:
                    ctx.native_hook_profile = observed_profile
                    logger.info(
                        "MGTT native hook profile: %s.", observed_profile
                    )
                ctx.update_dolphin_status("Connected")
                last_error = ""
                if ctx.capture_request is not None:
                    capture_label = ctx.capture_request
                    ctx.capture_request = None
                    ctx.capture_requested_at = None
                    ctx.capture_in_progress = capture_label
                    ctx.capture_last_status = f"writing {capture_label!r}"
                    logger.info(
                        "MGTT diagnostic capture %r started; keep the game "
                        "on this screen.",
                        capture_label,
                    )
                    try:
                        capture_path = await asyncio.to_thread(
                            capture_memory_snapshot,
                            memory,
                            capture_label,
                            extra_metadata={
                                "platform": platform.system(),
                                "seed_name": ctx.seed_name or "",
                                "seed_storage_namespace": (
                                    ctx.seed_storage_namespace
                                ),
                                "slot": ctx.slot,
                                "received_items": len(ctx.items_received),
                                "effective_item_names": sorted(
                                    ctx.current_item_names
                                ),
                                "active_native_golfer": (
                                    ctx.live_game_state.active_native_golfer
                                ),
                                "active_advance_tour_golfer": (
                                    ctx.live_game_state.active_advance_tour_golfer
                                ),
                                "active_golfer_display_name": (
                                    ctx.live_game_state.active_golfer_display_name
                                ),
                                "active_coin_course": (
                                    ctx.live_game_state.active_coin_course
                                ),
                                "checked_locations": len(
                                    ctx.checked_locations
                                ),
                                "dolphin_status": ctx.dolphin_status,
                                "pending_notifications": [
                                    entry.text
                                    for entry in ctx.pending_notifications
                                ],
                                "recent_game_messages": list(
                                    ctx.recent_game_messages
                                ),
                                "club_scope": ctx.club_scope,
                                "spin_scope": ctx.spin_scope,
                                "gate_roster": ctx.gate_roster,
                                "gate_advance_tour": (
                                    ctx.gate_advance_tour
                                ),
                                "gate_modes": ctx.gate_modes,
                                "gate_putting_difficulties": (
                                    ctx.gate_putting_difficulties
                                ),
                            },
                        )
                    except Exception:
                        ctx.capture_last_status = f"failed {capture_label!r}"
                        logger.exception(
                            "MGTT diagnostic capture %r failed",
                            capture_label,
                        )
                    else:
                        ctx.capture_last_status = (
                            f"saved {capture_label!r} to {capture_path}"
                        )
                        logger.info(
                            "MGTT diagnostic capture saved to %s",
                            capture_path,
                        )
                    finally:
                        ctx.capture_in_progress = None
                if ctx.slot is not None:
                    item_names = ctx.effective_received_item_names()
                    active_tournament_permissions = tournament_permission_mask(
                        item_names
                    )
                    if ctx.unlock_all_character_match_courses:
                        active_tournament_permissions |= 0x3F
                    protocol.write_item_counts(item_names)
                    ctx.current_item_names = tuple(item_names)
                    allow_save_writes = save_mutation_allowed(
                        hook_ready_since
                    )
                    if allow_save_writes and not save_writes_announced:
                        logger.info(
                            "MGTT startup validation grace elapsed; "
                            "save-backed unlock synchronization is enabled."
                        )
                        save_writes_announced = True
                    # Observe retail's Star-match bit before applying the AP
                    # inventory.  The latter intentionally restores the
                    # progressive Star mask and would otherwise erase the win
                    # before the location detector can see it.
                    character_match_names = (
                        ctx.live_game_state.completed_character_matches(
                            guarded_memory,
                            native_selected_mode=(
                                protocol.native_selected_mode()
                            ),
                            native_mode_confirm_sequence=(
                                protocol.native_mode_confirm_sequence()
                            ),
                            tournament_permissions=(
                                active_tournament_permissions
                            ),
                            confirmed_course_index=(
                                ctx.last_native_gate_trace.get("course_index")
                                if (
                                    ctx.last_native_gate_trace.get(
                                        "course_outcome"
                                    )
                                    == "allowed"
                                    and not ctx.last_native_gate_trace.get(
                                        "course_is_star"
                                    )
                                )
                                else None
                            ),
                        )
                    )
                    newly_spent_mulligans = (
                        ctx.live_game_state.apply_received_items(
                            guarded_memory,
                            item_names,
                            club_scope=ctx.club_scope,
                            fallback_club=ctx.fallback_club,
                            putter_range_scope=ctx.putter_range_scope,
                            spin_scope=ctx.spin_scope,
                            gate_modes=ctx.gate_modes,
                            unlock_all_character_match_courses=(
                                ctx.unlock_all_character_match_courses
                            ),
                            advance_tour_golfer_distances=(
                                ctx.advance_tour_golfer_distances
                            ),
                            # Do not carry the disproven counter-decrease
                            # heuristic across sessions. ReceivedItems is the
                            # authority until a real mulligan-use edge is mapped.
                            mulligans_spent=0,
                            allow_save_writes=allow_save_writes,
                            # Invitations remain optional vanilla presentation
                            # only. Never swap AP-owned progressive Stars for a
                            # retail invitation shadow inside Character Match.
                            preserve_character_match_invitations=False,
                            completed_character_match_checks=None,
                            native_selected_mode=(
                                protocol.native_selected_mode()
                            ),
                            confirmed_roster_golfer=(
                                ctx.last_native_gate_trace.get("roster_target")
                                if ctx.last_native_gate_trace.get(
                                    "roster_outcome"
                                ) == "allowed"
                                else None
                            ),
                            confirmed_roster_sequence=(
                                ctx.last_native_gate_trace.get("sequence")
                            ),
                            # Configured AP capacity applies only to regular
                            # Tournament, Star Tournament (which shares the
                            # Tournament top-level trace), and Stroke Play.
                            # Other modes retain retail's native counters and
                            # perfect-impact refund behavior.
                            sync_power_capacity=(
                                ctx.power_sync_enabled
                                and protocol.native_selected_mode()
                                in (
                                    NATIVE_MENU_MODE_IDS["Tournament"],
                                    NATIVE_MENU_MODE_IDS["Stroke Play"],
                                )
                            ),
                        )
                    )
                    # The current counter-decrease heuristic also fires during
                    # menu/round transitions and falsely persisted legitimate
                    # mulligans as spent. Until the actual use event is mapped,
                    # consumption is session-local and reconnect/reload restores
                    # the number of received Mulligan items.
                    advance_tour_warning = (
                        ctx.live_game_state.take_advance_tour_warning()
                    )
                    if advance_tour_warning:
                        logger.warning(advance_tour_warning)
                    club_notice = (
                        ctx.live_game_state.take_club_inventory_notice()
                    )
                    if club_notice:
                        ctx.queue_game_notification(club_notice)
                    protocol.set_gameplay_permissions(
                        spin_permission_mask(
                            item_names,
                            ctx.spin_scope,
                            (
                                ctx.live_game_state.active_native_golfer
                                or ctx.live_game_state.active_advance_tour_golfer
                            ),
                        ),
                        putter_range_mask(
                            item_names,
                            ctx.putter_range_scope,
                            (
                                ctx.live_game_state.active_native_golfer
                                or ctx.live_game_state.active_advance_tour_golfer
                            ),
                        ),
                    )
                    protocol.set_menu_permissions(
                        gate_roster=ctx.gate_roster,
                        gate_advance_tour=ctx.gate_advance_tour,
                        gate_modes=ctx.gate_modes,
                        gate_putting_difficulties=(
                            ctx.gate_putting_difficulties
                        ),
                        roster_permissions=roster_permission_mask(item_names),
                        star_roster_permissions=(
                            star_roster_permission_mask(item_names)
                        ),
                        advance_tour_permission=(
                            ADVANCE_TOUR_GOLFER_ITEM in item_names
                        ),
                        mode_permissions=mode_permission_mask(item_names),
                        putting_difficulties=(
                            putting_practice_difficulty_mask(item_names)
                        ),
                        tournament_permissions=(
                            active_tournament_permissions
                        ),
                        retail_character_match_star_mask=(
                            ctx.live_game_state.retail_character_match_star_mask
                            or 0
                        ),
                        star_tournament_native_unlocked=(
                            observed_profile
                            in {"star_menu", "star_state", "combined"}
                            or ctx.live_game_state.retail_regular_tournaments_complete(
                                guarded_memory
                            )
                            or all(
                                LOCATION_NAME_TO_ID[name]
                                in ctx.checked_locations
                                or LOCATION_NAME_TO_ID[name]
                                in ctx.submitted_location_ids
                                for name in TOURNAMENT_WIN_LOCATIONS[
                                    :len(REGULAR_TOURNAMENTS)
                                ]
                            )
                        ),
                    )
                    protocol.set_client_ready(True)
                    protocol.write_seed_fingerprint(ctx.seed_name or "")
                    previous_notification_scene = (
                        ctx.native_notification_scene_token
                    )
                    current_notification_scene = (
                        ctx.live_game_state.notification_scene_token
                    )
                    ctx.update_notification_scene(current_notification_scene)
                    if (
                        previous_notification_scene is not None
                        and current_notification_scene
                        != previous_notification_scene
                    ):
                        protocol.discard_notifications()
                    # Queue construction is permitted only during a verified
                    # live hole. Menu/save captures show that the prior setup
                    # heuristic could corrupt retail dialog objects.
                    if (
                        ctx.native_game_notifications_enabled
                        and ctx.live_game_state.notification_screen_safe
                        # Retail's own score/result dialog owns the same text
                        # constructor path. A four-check birdie/chip-in burst
                        # proved that constructing an AP popup during this
                        # window can leave an ASCII text pointer at
                        # 0x800246c8/0x800246cc. Keep receipts queued until
                        # both native result slots return to idle.
                        and not live_result_values(guarded_memory)
                    ):
                        ctx.flush_game_notification(protocol)

                    checked_names = protocol.checked_location_names()
                    # The same retail tables that back unlock synchronization
                    # can be zeroed, stale, or only partly copied while the
                    # memory-card record is being validated. Reading them too
                    # early could establish an empty reused-save baseline and
                    # then report every completed record as a new AP check.
                    persistent_names: set[str] = set()
                    if allow_save_writes:
                        persistent_names |= (
                            ctx.live_game_state.completed_ring_shots(
                                guarded_memory,
                                max_player_count=ctx.ring_shot_max_players,
                            )
                        )
                        persistent_names |= character_match_names
                        persistent_names |= (
                            ctx.live_game_state.completed_best_badges(
                                guarded_memory
                            )
                        )
                        persistent_names |= (
                            ctx.live_game_state.completed_one_on_one_putt(
                                guarded_memory
                            )
                        )
                        persistent_names |= (
                            ctx.live_game_state.completed_practice_checks(
                                guarded_memory
                            )
                        )
                        persistent_names |= (
                            ctx.live_game_state.completed_speed_golf(
                                guarded_memory
                            )
                        )
                        persistent_names |= (
                            ctx.live_game_state.completed_near_pin(
                                guarded_memory,
                                ctx.near_pin_aggregate_feet,
                            )
                        )
                    checked_names |= (
                        ctx.live_game_state.completed_live_accomplishments(
                            guarded_memory,
                            item_names,
                            ctx.congo_canopy_score_to_par,
                            native_selected_mode=(
                                protocol.native_selected_mode()
                            ),
                            selected_course_index=(
                                ctx.last_native_gate_trace.get("course_index")
                                if ctx.last_native_gate_trace.get(
                                    "course_outcome"
                                ) == "allowed"
                                else None
                            ),
                            selected_course_is_star=(
                                ctx.last_native_gate_trace.get("course_is_star")
                                if ctx.last_native_gate_trace.get(
                                    "course_outcome"
                                ) == "allowed"
                                else None
                            ),
                            confirmed_round_golfer=(
                                ctx.last_native_gate_trace.get("roster_target")
                                if ctx.last_native_gate_trace.get(
                                    "roster_outcome"
                                ) == "allowed"
                                else None
                            ),
                        )
                    )
                    checked_names |= (
                        ctx.live_game_state.completed_coin_shoot(
                            guarded_memory
                        )
                    )
                    coin_credit = ctx.live_game_state.take_coin_credit()
                    if coin_credit is not None:
                        variant, character, coins = coin_credit
                        ctx.record_coin_credit(variant, character, coins)
                    checked_names |= ctx.completed_coin_total_checks()
                    checked_names |= (
                        ctx.live_game_state.completed_special_modes(
                            guarded_memory
                        )
                    )
                    checked_names |= (
                        ctx.live_game_state.completed_live_practice_checks(
                            guarded_memory
                        )
                    )
                    if allow_save_writes:
                        persistent_names |= (
                            ctx.live_game_state.completed_tournament_placement_checks(
                                guarded_memory,
                                received_names=(
                                    None
                                    if ctx.unlock_all_character_match_courses
                                    else item_names
                                ),
                            )
                        )
                        persistent_names |= (
                            ctx.live_game_state.completed_tournament_checks(
                                guarded_memory,
                                include_character_checks=(
                                    ctx.tournament_character_checks
                                ),
                                # Exposing all Character Match courses uses
                                # retail's same six regular-course bits and
                                # therefore physically exposes those regular
                                # tournaments too. New worlds precollect their
                                # access items; accept a win from older rooms
                                # that used the same all-courses behavior.
                                received_names=(
                                    None
                                    if ctx.unlock_all_character_match_courses
                                    else item_names
                                ),
                                native_selected_mode=(
                                    protocol.native_selected_mode()
                                ),
                                confirmed_round_golfer=(
                                    ctx.last_native_gate_trace.get(
                                        "roster_target"
                                    )
                                    if ctx.last_native_gate_trace.get(
                                        "roster_outcome"
                                    ) == "allowed"
                                    else None
                                ),
                            )
                        )
                        checked_names |= ctx.reconcile_persistent_checks(
                            persistent_names
                        )
                    # Synthetic goals must use the server's complete monotonic
                    # check history as well as this poll's game-memory results.
                    # Previously, checks submitted through /mgtt_debug_check or
                    # completed in an earlier session existed only in
                    # ``ctx.checked_locations`` and could never satisfy an
                    # all-tournaments/all-matches/all-rings goal.
                    checked_names |= checked_location_names(
                        ctx.checked_locations
                    )
                    checked_names = add_derived_accomplishments(
                        checked_names, item_names
                    )
                    new_check_names = {
                        name
                        for name in checked_names
                        if name in LOCATION_NAME_TO_ID
                        and LOCATION_NAME_TO_ID[name] in ctx.missing_locations
                        and LOCATION_NAME_TO_ID[name] not in ctx.checked_locations
                        and LOCATION_NAME_TO_ID[name]
                        not in ctx.submitted_location_ids
                    }
                    if new_check_names:
                        for name in sorted(new_check_names):
                            logger.info("Check complete: %s", name)
                        location_ids = {
                            LOCATION_NAME_TO_ID[name]
                            for name in new_check_names
                        }
                        # Latch before awaiting the socket so the fast Dolphin
                        # poll cannot enqueue the same transient result again.
                        ctx.submitted_location_ids.update(location_ids)
                        await ctx.send_msgs(
                            [{
                                "cmd": "LocationChecks",
                                "locations": sorted(location_ids),
                            }]
                        )

                    # Read and submit fresh native Ring Attack progress before
                    # writing anything back. Once observed, mirror only the
                    # server-confirmed checks across every golfer row so the
                    # colored stars remain globally consistent after changing
                    # golfers, reconnecting, or restarting. The restore is
                    # strictly OR-only and therefore cannot erase a local clear
                    # while its LocationChecks packet is awaiting acceptance.
                    if allow_save_writes:
                        checked_server_names = {
                            name
                            for name, location_id in LOCATION_NAME_TO_ID.items()
                            if location_id in ctx.checked_locations
                        }
                        ctx.live_game_state.restore_ring_shot_progress(
                            guarded_memory,
                            checked_server_names,
                            max_player_count=ctx.ring_shot_max_players,
                        )

                    goal_location = GOAL_LOCATION_BY_VALUE[ctx.goal]
                    if goal_location in checked_names and not ctx.finished_game:
                        await ctx.send_msgs(
                            [{
                                "cmd": "StatusUpdate",
                                "status": ClientStatus.CLIENT_GOAL,
                            }]
                        )
                        ctx.finished_game = True
                else:
                    # The PPC hook uses this flag to keep randomized character
                    # access locked while no authenticated slot is attached.
                    protocol.set_client_ready(False)
            except Exception as error:
                if is_expected_disconnect(error):
                    report = "Dolphin closed; waiting for it to restart."
                    ctx.update_dolphin_status("Waiting for Dolphin", report)
                    if report != last_error:
                        logger.info(report)
                        last_error = report
                else:
                    status = f"Disconnected: {error}"
                    ctx.update_dolphin_status(status, str(error))
                    if status != last_error:
                        logger.warning(status)
                        last_error = status
                try:
                    close_dolphin_memory(memory)
                except Exception:
                    pass
                memory = None
                hooked = False
                hook_wait_started = None
                hook_ready_since = None
                save_writes_announced = False
            await asyncio.sleep(CONNECTED_POLL_INTERVAL_SECONDS)
    finally:
        try:
            close_dolphin_memory(memory)
        except Exception:
            pass


async def _async_main(args) -> None:
    ctx = MGTTContext(args.connect, args.password)
    ctx.auth = args.name
    ctx.address_map = AddressMap.load(args.address_map)
    ctx.allow_unverified = args.allow_unverified
    ctx.dolphin_backend = args.dolphin_backend
    ctx.gdb_host = args.gdb_host
    ctx.gdb_port = args.gdb_port
    ctx.server_task = asyncio.create_task(server_loop(ctx), name="Server")
    if gui_enabled:
        ctx.run_gui()
    ctx.run_cli()
    sync_task = asyncio.create_task(dolphin_sync(ctx), name="Dolphin sync")
    await ctx.exit_event.wait()
    sync_task.cancel()
    with suppress(asyncio.CancelledError):
        await sync_task
    await ctx.shutdown()


def parse_client_args(raw_args: tuple[str, ...] = ()):
    parser = get_base_parser(description="Mario Golf: Toadstool Tour Archipelago Client")
    parser.add_argument(
        "url",
        nargs="?",
        help="Archipelago connection URI supplied by the Launcher/WebHost",
    )
    # Installed APWorlds are ZIP imports on Windows, not unpacked directories.
    # AddressMap.load resolves this package-resource URI through importlib
    # instead of opening the archive member as a normal filesystem path.
    default_map = "builtin:GFTE01"
    parser.add_argument("--name", help="Archipelago slot name")
    parser.add_argument(
        "--address-map", default=default_map, help="JSON address map"
    )
    parser.add_argument(
        "--allow-unverified",
        action="store_true",
        help="development only: use an address map that has not passed hardware tests",
    )
    parser.add_argument(
        "--dolphin-backend",
        choices=("auto", "gdb", "dme"),
        default="auto",
        help="Dolphin memory connection (auto uses GDB on macOS)",
    )
    parser.add_argument("--gdb-host", default="127.0.0.1")
    parser.add_argument("--gdb-port", type=int, default=55000)
    args = handle_url_arg(parser.parse_args(raw_args or None), parser)
    if args.url:
        # 0.6.7's helper leaves username/password inside ``url.netloc`` and
        # copies that whole value to --connect. websockets rejects common
        # username-without-password links before CommonClient can authenticate.
        # Credentials already live in args.name/args.password, so pass only
        # host and port to the socket layer.
        host = args.url.hostname or ""
        if ":" in host and not host.startswith("["):
            host = f"[{host}]"
        args.connect = f"{host}:{args.url.port}" if args.url.port else host
    return args


def main(*raw_args: str) -> None:
    Utils.init_logging("Mario Golf Toadstool Tour Client")
    warn_duplicate_installations()
    args = parse_client_args(raw_args)
    asyncio.run(_async_main(args))


if __name__ == "__main__":
    main()
