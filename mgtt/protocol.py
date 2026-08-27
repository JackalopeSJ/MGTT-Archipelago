from __future__ import annotations

import json
import struct
from collections import Counter
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Protocol

from .data import PROTOCOL_ITEM_NAMES, PROTOCOL_LOCATION_NAMES, course_menu_map


MAGIC = b"MGAP"
PROTOCOL_VERSION = 2


class Memory(Protocol):
    def read_bytes(self, address: int, size: int) -> bytes: ...
    def write_bytes(self, address: int, data: bytes) -> None: ...


@dataclass(frozen=True)
class AddressMap:
    game_id: str
    revision: str
    protocol_base: int
    verified: bool
    notes: str = ""

    @classmethod
    def load(cls, path: str | Path) -> "AddressMap":
        path_text = str(path)
        if path_text.startswith("builtin:"):
            resource_name = path_text.removeprefix("builtin:")
            if not resource_name or any(
                character not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-"
                for character in resource_name
            ):
                raise ValueError(f"invalid built-in address map: {resource_name!r}")
            raw_text = (
                resources.files(__package__)
                .joinpath("address_maps", f"{resource_name}.json")
                .read_text(encoding="utf-8")
            )
        else:
            raw_text = Path(path).read_text(encoding="utf-8")
        raw = json.loads(raw_text)
        base = raw["protocol_base"]
        if isinstance(base, str):
            base = int(base, 0)
        return cls(
            game_id=raw["game_id"],
            revision=raw["revision"],
            protocol_base=base,
            verified=bool(raw["verified"]),
            notes=raw.get("notes", ""),
        )


class ProtocolBlock:
    """Shared-memory contract between the Dolphin client and injected PPC hook.

    The PPC hook owns the magic/version and location bits. The desktop client
    owns received item counts and the seed fingerprint. All integers are
    big-endian to match the GameCube CPU.
    """

    HEADER_SIZE = 0x10
    LOCATION_BITS_OFFSET = 0x10
    LOCATION_BITS_SIZE = 0x28
    ITEM_COUNTS_OFFSET = 0x40
    ITEM_COUNT_SIZE = 2
    SEED_FINGERPRINT_OFFSET = 0x180
    SEED_FINGERPRINT_SIZE = 0x20
    NOTIFICATION_WRITE_OFFSET = 0x200
    NOTIFICATION_READ_OFFSET = 0x204
    NOTIFICATION_SLOTS_OFFSET = 0x220
    NOTIFICATION_SLOT_SIZE = 0x80
    NOTIFICATION_SLOT_COUNT = 8
    TOTAL_SIZE = 0x620
    CLIENT_READY_OFFSET = 0x06
    SPIN_PERMISSIONS_OFFSET = 0x07
    PUTTER_RANGES_OFFSET = 0x08
    NOTIFICATION_COOLDOWN_OFFSET = 0x0F
    ACTIVE_NOTIFICATION_PTR_OFFSET = 0x38
    ADVANCE_TOUR_PERMISSION_OFFSET = 0x3C
    # Item counts end at 0x16E. The small gap before the seed fingerprint is
    # reserved for focused-probe identity and AP-owned Star permissions.
    NATIVE_PROFILE_OFFSET = 0x16E
    STAR_ROSTER_PERMISSIONS_OFFSET = 0x170
    NATIVE_SELECTED_MODE_OFFSET = 0x172
    NATIVE_TRACE_COURSE_OFFSET = 0x173
    TOURNAMENT_PERMISSIONS_OFFSET = 0x174
    RETAIL_CHARACTER_MATCH_STAR_MASK_OFFSET = 0x176
    # The course menu compacts visible courses into indices 0..5. Publish the
    # corresponding native course IDs so the PPC A-button guard can test the
    # correct regular/Star permission bit.
    COURSE_MENU_MAP_OFFSET = 0x178
    COURSE_MENU_MAP_SIZE = 6
    NATIVE_MODE_CONFIRM_SEQUENCE_OFFSET = 0x17E
    LAST_PUTTER_SELECTOR_OFFSET = 0x17F
    # Client-owned mirror of the native Star Tournament menu insertion. Keep
    # this after the 0x180..0x19F seed fingerprint so connecting cannot
    # overwrite it. Integrated constructor profiles set it immediately; retail
    # fallback profiles set it after the six regular Tournament wins.
    STAR_TOURNAMENT_NATIVE_UNLOCKED_OFFSET = 0x1A0
    NATIVE_TRACE_SPIN_OFFSET = 0x36
    NATIVE_TRACE_POWER_OFFSET = 0x37
    NATIVE_TRACE_SEQUENCE_OFFSET = 0x3D
    NATIVE_TRACE_ROSTER_OFFSET = 0x3E
    NATIVE_TRACE_MODE_OFFSET = 0x3F
    MENU_GATE_FLAGS_OFFSET = 0x09
    ROSTER_PERMISSIONS_OFFSET = 0x0A
    MODE_PERMISSIONS_OFFSET = 0x0C
    PUTTING_DIFFICULTIES_OFFSET = 0x0E

    NATIVE_PROFILE_NAMES = {
        0: "recovery",
        1: "roster",
        2: "modes",
        3: "putting",
        4: "spin",
        5: "power",
        6: "combined",
        7: "star_menu",
        8: "star_state",
    }

    def __init__(self, memory: Memory, base: int):
        self.memory = memory
        self.base = base

    def validate(self) -> tuple[bool, str]:
        header = self.memory.read_bytes(self.base, self.HEADER_SIZE)
        if len(header) != self.HEADER_SIZE:
            return False, "short protocol header read"
        if header[:4] != MAGIC:
            return False, f"missing MGAP hook magic (read {header[:4]!r})"
        version = struct.unpack_from(">H", header, 4)[0]
        if version != PROTOCOL_VERSION:
            return False, f"protocol version {version}, expected {PROTOCOL_VERSION}"
        return True, "ok"

    def checked_location_names(self) -> set[str]:
        bits = self.memory.read_bytes(
            self.base + self.LOCATION_BITS_OFFSET, self.LOCATION_BITS_SIZE
        )
        names = PROTOCOL_LOCATION_NAMES
        return {
            name
            for index, name in enumerate(names)
            if index // 8 < len(bits) and bits[index // 8] & (1 << (index % 8))
        }

    def native_gate_trace(self) -> dict[str, int | str | bool | None]:
        """Decode the capture-only native roster/mode guard trace."""

        raw = self.memory.read_bytes(
            self.base + self.NATIVE_TRACE_SEQUENCE_OFFSET, 3
        )
        if len(raw) != 3:
            return {
                "sequence": 0,
                "roster_target": None,
                "roster_outcome": "unseen",
                "mode_target": None,
                "mode_outcome": "unseen",
                "course_target": None,
                "course_index": None,
                "course_is_star": None,
                "course_outcome": "unseen",
            }

        def decode(value: int, targets: tuple[str, ...]):
            outcome = (
                "denied" if value & 0x80
                else "allowed" if value & 0x40
                else "entered" if value
                else "unseen"
            )
            encoded_target = value & 0x3F
            index = encoded_target - 1
            target = targets[index] if 0 <= index < len(targets) else None
            return target, outcome

        roster_targets = (
            "Mario", "Luigi", "Peach", "Daisy", "Yoshi", "Koopa Troopa",
            "Donkey Kong", "Diddy Kong", "Wario", "Waluigi", "Birdo",
            "Bowser", "Bowser Jr.", "Boo", "Shadow Mario", "Petey Piranha",
            "Advance Tour Golfer 1", "Advance Tour Golfer 2",
        )
        mode_targets = (
            "Tournament", "Character Match", "Stroke Play", "Doubles",
            "Ring Attack", "Club Slots", "Coin Attack", "Speed Golf",
            "Training", "Side Games", "Putting Practice",
            "Putting Practice - Novice", "Putting Practice - Intermediate",
            "Putting Practice - Expert", "Birdie Challenge", "Shot Practice",
            "Approach Practice",
        )
        roster_target, roster_outcome = decode(raw[1], roster_targets)
        mode_target, mode_outcome = decode(raw[2], mode_targets)
        course_raw = self.memory.read_bytes(
            self.base + self.NATIVE_TRACE_COURSE_OFFSET, 1
        )
        course_value = course_raw[0] if len(course_raw) == 1 else 0
        course_index = (course_value & 0x1F) - 1
        course_target = None
        if 0 <= course_index < 6:
            course_target = (
                "Star " if course_value & 0x20 else "Regular "
            ) + f"course {course_index + 1}"
        course_outcome = (
            "denied" if course_value & 0x80
            else "allowed" if course_value & 0x40
            else "unseen"
        )
        return {
            "sequence": raw[0],
            "roster_target": roster_target,
            "roster_outcome": roster_outcome,
            "mode_target": mode_target,
            "mode_outcome": mode_outcome,
            "course_target": course_target,
            "course_index": course_index if course_target is not None else None,
            "course_is_star": (
                bool(course_value & 0x20) if course_target is not None else None
            ),
            "course_outcome": course_outcome,
        }

    def native_gameplay_trace(self) -> dict[str, int | str | None]:
        """Decode late spin-consumer and zero-Power observation telemetry."""

        raw = self.memory.read_bytes(
            self.base + self.NATIVE_TRACE_SPIN_OFFSET, 2
        )
        if len(raw) != 2:
            raw = b"\0\0"
        spin_names = (
            None,
            "Topspin",
            "Super Topspin",
            "Backspin",
            "Super Backspin",
        )
        spin_value = raw[0] & 0x3F
        spin_outcome = (
            "denied" if raw[0] & 0x80
            else "allowed" if raw[0] & 0x40
            else "unseen"
        )
        power_outcome = (
            "selected_at_zero" if raw[1] & 0x80
            else "selected_with_remaining" if raw[1] & 0x40
            else "unseen"
        )
        return {
            "spin_technique": (
                spin_names[spin_value]
                if 0 <= spin_value < len(spin_names)
                else None
            ),
            "spin_outcome": spin_outcome,
            "power_outcome": power_outcome,
            "power_shot_type": (raw[1] & 0x3F) - 1 if raw[1] else None,
        }

    def native_profile(self) -> str:
        """Return the self-identified focused hook profile."""

        raw = self.memory.read_bytes(
            self.base + self.NATIVE_PROFILE_OFFSET, 1
        )
        if len(raw) != 1:
            return "unknown"
        return self.NATIVE_PROFILE_NAMES.get(raw[0], f"unknown-{raw[0]}")

    def native_selected_mode(self) -> int | None:
        """Return the last top-level mode confirmed by the native guard."""

        raw = self.memory.read_bytes(
            self.base + self.NATIVE_SELECTED_MODE_OFFSET, 1
        )
        # Native stores selector + 1 so a zero-filled protocol block means the
        # main-mode confirmation hook has not run yet.
        if len(raw) != 1 or raw[0] == 0 or raw[0] > 10:
            return None
        return raw[0] - 1

    def native_mode_confirm_sequence(self) -> int | None:
        """Return the dedicated successful top-level mode entry generation."""

        raw = self.memory.read_bytes(
            self.base + self.NATIVE_MODE_CONFIRM_SEQUENCE_OFFSET, 1
        )
        return raw[0] if len(raw) == 1 else None

    def write_item_counts(self, received_names: list[str]) -> None:
        counts = Counter(received_names)
        # Protocol v2 has fixed space for the 151 items published through
        # v0.8.4. New client-enforced items remain in ReceivedItems but are not
        # mirrored into the legacy PPC count table.
        payload = bytearray(len(PROTOCOL_ITEM_NAMES) * self.ITEM_COUNT_SIZE)
        for index, name in enumerate(PROTOCOL_ITEM_NAMES):
            struct.pack_into(">H", payload, index * 2, min(counts[name], 0xFFFF))
        self.memory.write_bytes(self.base + self.ITEM_COUNTS_OFFSET, bytes(payload))

    def set_client_ready(self, ready: bool) -> None:
        self.memory.write_bytes(
            self.base + self.CLIENT_READY_OFFSET, bytes((int(ready),))
        )

    def set_gameplay_permissions(
        self, spin_permissions: int, putter_ranges: int
    ) -> None:
        """Publish compact permissions consumed by the per-frame PPC hook."""

        if not 0 <= spin_permissions <= 0xFF:
            raise ValueError("spin permissions must fit in one byte")
        if not 0 <= putter_ranges <= 0xFF:
            raise ValueError("putter ranges must fit in one byte")
        self.memory.write_bytes(
            self.base + self.SPIN_PERMISSIONS_OFFSET,
            bytes((spin_permissions, putter_ranges)),
        )

    def set_menu_permissions(
        self,
        *,
        gate_roster: bool,
        gate_advance_tour: bool,
        gate_modes: bool,
        gate_putting_difficulties: bool,
        roster_permissions: int,
        star_roster_permissions: int,
        advance_tour_permission: bool,
        mode_permissions: int,
        putting_difficulties: int,
        tournament_permissions: int,
        retail_character_match_star_mask: int,
        star_tournament_native_unlocked: bool,
    ) -> None:
        """Publish fail-closed permissions for the native A-button guard."""

        if not 0 <= roster_permissions <= 0xFFFF:
            raise ValueError("roster permissions must fit in two bytes")
        if not 0 <= star_roster_permissions <= 0xFFFF:
            raise ValueError("star roster permissions must fit in two bytes")
        if not 0 <= mode_permissions <= 0xFFFF:
            raise ValueError("mode permissions must fit in two bytes")
        if not 0 <= putting_difficulties <= 0xFF:
            raise ValueError("putting difficulties must fit in one byte")
        if not 0 <= tournament_permissions <= 0x0FFF:
            raise ValueError("tournament permissions must fit in twelve bits")
        if not 0 <= retail_character_match_star_mask <= 0xFFFF:
            raise ValueError(
                "retail Character Match Star mask must fit in two bytes"
            )
        flags = (
            int(gate_roster)
            | (int(gate_modes) << 1)
            | (int(gate_putting_difficulties) << 2)
            | (int(gate_advance_tour) << 3)
        )
        self.memory.write_bytes(
            self.base + self.MENU_GATE_FLAGS_OFFSET,
            struct.pack(
                ">BHHB",
                flags,
                roster_permissions,
                mode_permissions,
                putting_difficulties,
            ),
        )
        self.memory.write_bytes(
            self.base + self.ADVANCE_TOUR_PERMISSION_OFFSET,
            bytes((int(advance_tour_permission),)),
        )
        self.memory.write_bytes(
            self.base + self.STAR_ROSTER_PERMISSIONS_OFFSET,
            struct.pack(">H", star_roster_permissions),
        )
        self.memory.write_bytes(
            self.base + self.TOURNAMENT_PERMISSIONS_OFFSET,
            struct.pack(">H", tournament_permissions),
        )
        self.memory.write_bytes(
            self.base + self.RETAIL_CHARACTER_MATCH_STAR_MASK_OFFSET,
            struct.pack(">H", retail_character_match_star_mask),
        )
        self.memory.write_bytes(
            self.base + self.STAR_TOURNAMENT_NATIVE_UNLOCKED_OFFSET,
            bytes((int(star_tournament_native_unlocked),)),
        )
        visible_course_ids = bytes(course_menu_map(tournament_permissions))
        self.memory.write_bytes(
            self.base + self.COURSE_MENU_MAP_OFFSET,
            visible_course_ids
            + bytes((0xFF,))
            * (self.COURSE_MENU_MAP_SIZE - len(visible_course_ids)),
        )

    def write_seed_fingerprint(self, seed_name: str) -> None:
        encoded = seed_name.encode("ascii", "replace")[: self.SEED_FINGERPRINT_SIZE - 1]
        payload = encoded + bytes(self.SEED_FINGERPRINT_SIZE - len(encoded))
        self.memory.write_bytes(
            self.base + self.SEED_FINGERPRINT_OFFSET, payload
        )

    def enqueue_notification(self, text: str) -> bool:
        """Queue one native in-game notification.

        The client publishes the slot payload before advancing the sequence
        number. Keep only one queue entry in flight. The hook owns one retail
        popup at a time and lets retail retire it through its normal A/timer
        state machine. False means the game has not consumed the previous
        entry or its popup is still active.
        """
        counters = self.memory.read_bytes(
            self.base + self.NOTIFICATION_WRITE_OFFSET, 8
        )
        if len(counters) != 8:
            return False
        write_sequence, read_sequence = struct.unpack(">II", counters)
        if write_sequence != read_sequence:
            return False
        active_pointer = self.memory.read_bytes(
            self.base + self.ACTIVE_NOTIFICATION_PTR_OFFSET, 4
        )
        if len(active_pointer) != 4:
            return False
        if active_pointer != bytes(4):
            return False

        normalized = text.replace("\r", " ").replace("\n", "\x01")
        encoded = normalized.encode("ascii", "replace")[: self.NOTIFICATION_SLOT_SIZE - 1]
        payload = encoded + bytes(self.NOTIFICATION_SLOT_SIZE - len(encoded))
        slot = write_sequence % self.NOTIFICATION_SLOT_COUNT
        self.memory.write_bytes(
            self.base
            + self.NOTIFICATION_SLOTS_OFFSET
            + slot * self.NOTIFICATION_SLOT_SIZE,
            payload,
        )
        self.memory.write_bytes(
            self.base + self.NOTIFICATION_WRITE_OFFSET,
            struct.pack(">I", (write_sequence + 1) & 0xFFFFFFFF),
        )
        return True

    def discard_notifications(self) -> None:
        """Discard native entries not consumed before a scene transition."""

        counters = self.memory.read_bytes(
            self.base + self.NOTIFICATION_WRITE_OFFSET, 8
        )
        if len(counters) != 8:
            return
        write_sequence = counters[:4]
        self.memory.write_bytes(
            self.base + self.NOTIFICATION_READ_OFFSET, write_sequence
        )
        self.memory.write_bytes(
            self.base + self.NOTIFICATION_COOLDOWN_OFFSET, b"\0"
        )
