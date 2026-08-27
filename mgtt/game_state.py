from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
import math
import struct

from .data import (
    ADVANCE_TOUR_HOLE_THRESHOLDS,
    APPROACH_PRACTICE_DIFFICULTY_ITEMS,
    APPROACH_PRACTICE_MODE_ITEM,
    BEST_BADGE_HOLE_LOCATIONS,
    BIRDIE_CHALLENGE_MODE_ITEM,
    BOWSERS_BIG_BLAST_LOCATION,
    CHARACTER_MATCH_COURSE_LOCATIONS,
    CHARACTER_MATCH_PRO_LOCATIONS,
    CHARACTERS,
    CLUBS,
    COIN_100_GLOBAL_LOCATION,
    COIN_ATTACK_VARIANTS,
    COIN_BIRDIE_75_GLOBAL_LOCATION,
    COURSES,
    GOLFER_ROUND_SCORE_TARGET,
    HOLE_IN_ONE_CONTEST_LOCATION,
    MODES,
    MULTIPLAYER_RING_LOCATIONS,
    NEAR_PIN_AGGREGATE_LOCATION,
    ONE_ON_ONE_PUTT_LOCATION,
    APPROACH_SHOT_ITEM,
    POWER_SHOT_ITEM,
    PROGRESSIVE_TOURNAMENT_MODE_ITEM,
    PER_CHARACTER_GOLFERS,
    PUTTER_RANGE_FEET,
    PUTTER_RANGE_ITEMS,
    PUTTING_PRACTICE_DIFFICULTY_ITEMS,
    PUTTING_PRACTICE_MODE_ITEM,
    REGULAR_TOURNAMENTS,
    SINGLE_PLAYER_RING_LOCATIONS,
    SPEED_GOLF_COURSE_LOCATIONS,
    SPEED_GOLF_HOLE_LOCATION,
    SPEED_GOLF_UNDER_PAR_LOCATION,
    SECRET_CHARACTERS,
    SHOT_PRACTICE_STAGE_ITEMS,
    SHOT_PRACTICE_MODE_ITEM,
    STAR_TOURNAMENTS,
    STAR_TOURNAMENT_AGGREGATE_LOCATION,
    TOURNAMENT_CHARACTER_LOCATIONS,
    TOURNAMENT_FINISH_LOCATION,
    TOURNAMENT_TOP_THREE_LOCATIONS,
    TOURNAMENT_WIN_LOCATIONS,
    character_club_item,
    character_item,
    character_putter_range_item,
    club_item,
    coin_course_location,
    congo_canopy_score_location,
    course_menu_map,
    mode_item,
    spin_item,
    tournament_access_item,
    tournament_item,
    advance_tour_hole_location,
    birdie_challenge_location,
    course_par_sweep_location,
    golfer_birdie_location,
    golfer_round_score_location,
    practice_clear_location,
    character_match_pro_location,
)
from .advance_tour import (
    SELECTED_GOLFER_TEXT,
    SELECTED_GOLFER_TEXT_SIZE,
    active_advance_tour_identity,
    advance_tour_identity_for_name,
    apply_advance_tour_items,
    selected_golfer_display_name,
)


SAVE_BASE = 0x8022A3C8
# The August starter-roster video and runtime header resolve these two words:
# writing Birdo/Diddy stages to +0x04 displayed Star icons without exposing the
# four hidden retail golfers, while +0x06 remained zero. +0x04 is therefore the
# Star mask and +0x06 is the base/hidden-golfer mask, the reverse of the early
# prototype assumption.
STAR_GOLFER_UNLOCK_MASK = SAVE_BASE + 0x04
GOLFER_UNLOCK_MASK = SAVE_BASE + 0x06
# The August 10 Tournament captures and the loaded selector at 0x8041399C
# prove that the low byte of the former two-byte "golfer mask" is actually
# the five regular-course progression flags. Course zero is always present;
# bits 0..4 expose courses 1..5.  Writing a full 16-bit AP golfer mask here
# therefore made Mario/Luigi/Peach ownership expose three extra courses.
# Only the four hidden retail golfers need save-backed base bits (12..15).
# Ordinary roster ownership lives exclusively in the native protocol guard.
COURSE_UNLOCK_FLAGS = SAVE_BASE + 0x07

# Retail player blocks are 0x5204 bytes apart.  The byte is remaining shots,
# not an infinite-shot flag, so the bridge preserves decreases during play.
POWER_SHOT_REMAINING = (
    0x804F2070,
    0x804F7274,
    0x804FC478,
    0x8050167C,
)

# Retail stores each player's Mulligan count in the byte immediately following
# that player's Power Shot count.  Club Slots already supplies the complete
# retry UI and consumes one from this counter, so AP only needs to synchronize
# Player 1's stack and persist the number spent through Archipelago DataStorage.
MULLIGAN_REMAINING = tuple(address + 1 for address in POWER_SHOT_REMAINING)

# Shared live shot-selection state. The retail club limiter is a 14-bit mask in
# club order (1W through putter); bit 13 keeps the putter unconditional.
# The August Priority 0 result set identifies +0x4C as the selected technique:
# 1=Topspin, 2=Super Topspin, 3=Backspin, and 4=Super Backspin. +0xC4 remains
# the later effect/result state. Captures taken only after owned shots do not
# yet identify the consumer PC needed to reject a locked technique safely.
CURRENT_SPIN_SELECTION = 0x804ECD4C
CURRENT_SPIN = 0x804ECDC4
CURRENT_SHOT_TYPE = 0x804ECD50
CURRENT_CLUB = 0x804ECD58
POWER_SHOT_TYPE = 0
NORMAL_SHOT_TYPE = 1
APPROACH_SHOT_TYPE = 2
CLUB_LIMITER = 0x804ECE7C
# Each live player object is 0x5204 bytes. The August 13 2P Ring Attack pair
# captured P1's AP mask at the established address and P2's unrestricted
# 0x3FFF mask at exactly the next object slot. P3/P4 follow the same stride.
CLUB_LIMITER_PLAYER_STRIDE = 0x5204
CLUB_LIMITERS = tuple(
    CLUB_LIMITER + player * CLUB_LIMITER_PLAYER_STRIDE
    for player in range(4)
)
# The August 15 paired Character Match captures identify the active live-player
# object pointer. It is exactly P1's object on Shadow Mario's turn and advances
# by the established 0x5204 player stride on CPU Mario's turn.
ACTIVE_PLAYER_OBJECT_POINTER = 0x804ECDE0
PLAYER_ONE_LIVE_OBJECT = 0x804ECE70
BALL_LIE_PRIMARY = 0x804E364C
BALL_COORDINATES = 0x806CB4C4
# Priority 0 full-RAM captures place the visible P1 result codes in the two
# aligned words surrounding the old 0x8050F0EC candidate. Ordinary Birdie was
# present in both words at 0x8050F0E8 and 0x8050F0F0, while 0x8050F0EC stayed
# 0xFFFFFFFF throughout the result. Two slots also explain how a shot can
# display a Chip-In message and an Eagle score in the same result sequence.
RESULT_MESSAGE = 0x8050F0E8
RESULT_MESSAGE_SECONDARY = 0x8050F0F0
ACTIVE_GOLFER_FX = 0x8050F1B0
MODE_SELECTOR = 0x802B2A80
CURRENT_COURSE = 0x8044AFDC
CURRENT_HOLE = 0x804E68F8
CURRENT_PAR = 0x804E685F
GAMEPLAY_MARKER = 0x80445FE0
GAMEPLAY_MARKER_ACTIVE = 0x801E5F30
SELECTED_GOLFER_NAME = SELECTED_GOLFER_TEXT
SELECTED_GOLFER_NAME_SIZE = SELECTED_GOLFER_TEXT_SIZE
PUTTER_CLUB_INDEX = 13
PUTTER_CLUB_BIT = 1 << PUTTER_CLUB_INDEX

# Coin Attack copies its result title into this UI work area only while a
# Quick Cash or Cash Cup result is active. Pairing that signature with the
# captured per-hole coin counter avoids the false positives seen when the
# counter address is reused by unrelated modes.
COIN_RESULT_TEXT = 0x802CDA00
COIN_RESULT_TEXT_SIZE = 0x500
COIN_HOLE_COUNT = 0x8050F5AC
# August 6 Quick Cash captures retain the settled 321-coin round total here
# while COIN_HOLE_COUNT contains only the last hole's 38 coins.
COIN_ROUND_TOTAL = 0x80523F28
COIN_RESULT_SIGNATURES = (
    ("Quick Cash", b"COIN ATTACK - Quick Cash"),
    ("Cash Cup", b"COIN ATTACK - Cash Cup"),
)

# The main UI text arena retains active round/setup text into the final Results
# screen. Paired July captures use these strings to distinguish the
# code-unlocked Hole-in-One Contest and the captured Bowser's Big Blast
# Password Tournament without writing any menu state.
LIVE_UI_TEXT = 0x802CC000
LIVE_UI_TEXT_SIZE = 0x2000
HOLE_IN_ONE_SESSION_TEXT = 0x802D07E0
HOLE_IN_ONE_SESSION_TEXT_SIZE = 0x80
PRIMARY_COURSE_TEXT = 0x802CC930
PRIMARY_COURSE_TEXT_SIZE = 0x80
RESULTS_PASSWORD_SIGNATURE = b"Results Password"
CLEAR_SIGNATURE = b"Clear!"
HOLE_IN_ONE_CONTEST_SIGNATURE = b"Play two holes from the front"
BOWSERS_BIG_BLAST_SIGNATURE = b"Bowser's Big Blast"
STROKE_PLAY_SIGNATURE = b"STROKE PLAY"
TOURNAMENT_SIGNATURE = b"TOURNAMENT"

# Earlier builds treated MODE_SELECTOR as a retail mode signature. Full-RAM
# menu captures prove that it is unrelated changing state. The constants are
# retained for capture comparison and compatibility, but the client must never
# write to this address.
MODE_ACCESS_BY_PATTERN = {
    0x00000000: ("Tournament",),
    0xFFFFFFFF & 0xFFFFFFF5: ("Tournament",),
    0x0000AFF5: ("Character Match",),
    0x000000FF: ("Stroke Play",),
    0x0000AFFF: ("Doubles", "Side Games", "Match Play", "Skins Match"),
    0x0005FFF5: ("Ring Attack",),
    0xF5000000: ("Club Slots", "Speed Golf"),
    0x00FFF500: ("Coin Attack",),
    0x0000FFF5: ("Near-Pin",),
}
MODE_PATTERN_BY_NAME = {
    mode: pattern
    for pattern, modes in MODE_ACCESS_BY_PATTERN.items()
    for mode in modes
}
CHARACTER_MATCH_PATTERN = 0x0000AFF5
SHARED_MATCH_PATTERN = 0x0000AFFF
TRAINING_PATTERN = 0x000000FF

# Retail save/result rows and ball-effect IDs use this internal golfer order,
# which is not the same as the AP-facing roster order in data.py.
INTERNAL_GOLFER_ORDER = (
    "Mario",
    "Luigi",
    "Peach",
    "Waluigi",
    "Bowser",
    "Wario",
    "Shadow Mario",
    "Birdo",
    "Yoshi",
    "Donkey Kong",
    "Diddy Kong",
    "Koopa Troopa",
    "Petey Piranha",
    "Daisy",
    "Bowser Jr.",
    "Boo",
)
HIDDEN_GOLFER_SAVE_MASK = sum(
    1 << INTERNAL_GOLFER_ORDER.index(character)
    for character in SECRET_CHARACTERS
)

# The character-select grid uses a presentation order distinct from both the
# AP-facing roster and the retail save/result order. Paired Mario/Luigi and
# Shadow Mario captures identify the live cursor as 0, 1, and 14 respectively;
# the remaining positions follow the visible 8x2 retail grid.
CHARACTER_SELECT_ORDER = (
    "Mario",
    "Luigi",
    "Peach",
    "Daisy",
    "Yoshi",
    "Koopa Troopa",
    "Donkey Kong",
    "Diddy Kong",
    "Wario",
    "Waluigi",
    "Birdo",
    "Bowser",
    "Bowser Jr.",
    "Boo",
    "Shadow Mario",
    "Petey Piranha",
)

# The paired Koopa invitation captures establish that the Star mask uses the
# character-select order: completing retail's first match sets bit 5, Koopa's
# grid position. Do not reuse INTERNAL_GOLFER_ORDER here; that order remains
# correct for the separate base/hidden-golfer and result tables.
STAR_GOLFER_ORDER = CHARACTER_SELECT_ORDER
# Seven paired Priority 1 captures reduce the live presentation cursor to this
# exact byte. The adjacent words expose column/row, while +0x44 becomes one
# after a golfer is confirmed.
CHARACTER_SELECT_CURSOR = 0x8044BA4B
CHARACTER_SELECT_STAR_SELECTED = 0x8044BA6B
CHARACTER_SELECT_COLUMN = 0x8044BA10
CHARACTER_SELECT_ROW = 0x8044BA14
CHARACTER_SELECT_READY = 0x8044BA44
# The Priority 2 Petey pair exposes the live character-grid roster list. Its
# first 12 words are always the native base golfers 0..11; the four retail-
# hidden slots are -1 until vanilla's Star mask inserts IDs 12..15. AP writes
# those presentation slots from first-copy ownership so a hidden golfer can
# exist as a normal base form before the second progressive copy.
CHARACTER_SELECT_ROSTER_LIST = 0x80445CDC
CHARACTER_SELECT_ROSTER_COUNT = 16
CHARACTER_SELECT_HIDDEN_FIRST = 12
# Immutable words surrounding the two roster-confirmation instructions patched
# by the combined hook. Matching either set proves the character-select overlay
# is loaded without depending on the replaced center instruction itself.
CHARACTER_SELECT_OVERLAY_SIGNATURES = (
    (
        0x8040BE58,
        (0x8009B018, 0x93FCBA38, 0x7C0B0000),
    ),
    (
        0x8040C448,
        (0x38E00000, 0x93FBBA38, 0x7C0B0000),
    ),
)
MODE_SELECT_OVERLAY_SITE = 0x8041D93C
MODE_SELECT_OVERLAY_IMMUTABLE_WORDS = (
    0x48000208,
    0x41A2004C,
    0x3D208045,
)

# The August 10 Putting-Intermediate capture identifies the live difficulty
# menu after AP ownership was already present. Retail left a one-entry table:
# count 1, primary code 0x11, and parallel display/target code 0x17. The native
# constructor uses compact tables 0x11..0x13 and 0x17..0x19 for Putting, while
# Approach has a different parallel first code. This lets the client safely
# expose owned Putting difficulties without writing retail completion flags.
PUTTING_MENU_STATE = 0x8044C434
PUTTING_MENU_SELECTION = 0x8044C42C
PUTTING_MENU_COUNT = 0x8044C440
PUTTING_MENU_CODE_TABLE = 0x8044C50C
PUTTING_MENU_TARGET_TABLE = 0x8044C534
PUTTING_MENU_ACTIVE_STATE = 2
PUTTING_MENU_FIRST_CODE = 0x11
PUTTING_MENU_FIRST_TARGET = 0x17

# Priority 2 full-RAM pairs identify the native main-menu enum consumed by the
# confirmation handler. Permission bits deliberately use those native IDs so
# the PPC guard can test them without an unsafe lookup table. Doubles (3), Club
# Slots (5), and Training (8) are local and therefore absent. Near-Pin and
# Putting Practice is a separately shuffled Side Games child. Either its item
# or the parent Side Games item grants entry to the parent menu. A separate
# permission bit keeps the other three children closed when only Putting has
# been received.
NATIVE_MENU_MODE_IDS = {
    "Tournament": 0,
    "Character Match": 1,
    "Stroke Play": 2,
    "Ring Attack": 4,
    "Coin Attack": 6,
    "Speed Golf": 7,
    "Side Games": 9,
}
RESULT_LOCATION_BY_VALUE = {
    0x01: "Accomplishment - Make a Hole-in-One",
    0x02: "Accomplishment - Make an Albatross",
    0x03: "Accomplishment - Make an Eagle",
    0x04: "Accomplishment - Make a Birdie",
    0x11: "Accomplishment - Make a Chip-In",
    0x15: "Accomplishment - Hit the Pin",
}


def live_result_values(memory) -> tuple[int, ...]:
    """Return distinct active P1 result codes from the captured result slots."""

    values = (
        int.from_bytes(memory.read_bytes(RESULT_MESSAGE, 4), "big"),
        int.from_bytes(
            memory.read_bytes(RESULT_MESSAGE_SECONDARY, 4), "big"
        ),
    )
    active = []
    for value in values:
        if not (1 <= value <= 0x1A or value == 0x29):
            continue
        if value not in active:
            active.append(value)
    return tuple(active)

# Single-player Ring Attack progress is stored per golfer, not globally. Retail's
# getter/setter at 0x80014984/0x800149EC indexes 24 six-byte golfer rows from
# SAVE_BASE + 0x894 through +0x923. Each row has one byte per course and bits
# 0..5 are the six levels. The earlier +0x8F4 candidate is merely row 16; it
# happened to change in the first positive capture and therefore made clears
# appear golfer-independent. The August 11 Mario level-select capture proves
# row zero contains 0x03 after clearing Lakitu levels 1 and 2 while row 16 is
# still zero. Archipelago locations are golfer-independent, so readers OR all
# rows and server-backed restoration publishes the global mask to every row.
RING_SHOT_1P_TABLE = SAVE_BASE + 0x894
RING_SHOT_1P_GOLFERS = 24
RING_SHOT_1P_STRIDE = 6
RING_SHOT_1P_TABLE_SIZE = RING_SHOT_1P_GOLFERS * RING_SHOT_1P_STRIDE
# Compatibility alias used by diagnostics and older tests/tools.
RING_SHOT_1P_FLAGS = RING_SHOT_1P_TABLE

# The retail Ring Attack getter/setter at 0x80014984/0x800149EC stores
# multiplayer results as six course bytes per player count. Bits 0..3 are the
# four levels. The August 11 2P before/after capture changed only the first 2P
# course byte at SAVE_BASE + 0x924 (1 -> 3). The following 3P and 4P tables are
# contiguous six-byte tables.
RING_SHOT_MULTIPLAYER_FLAGS = (
    SAVE_BASE + 0x924,
    SAVE_BASE + 0x92A,
    SAVE_BASE + 0x930,
)

# Two 40-golfer x 6-course byte tables. A clean save initializes each entry to
# 0x80, while first place is stored as 1. The first table is regular Tournament
# and the second is Star Tournament. Native result rows are not one contiguous
# range: the August 6 Yoshi/Lakitu capture writes row 22 (native index 8 plus
# 14), while the August 14 Petey/Shifting Sands capture writes row 12. Scan the
# complete table for course wins and use capture-proven per-golfer mappings for
# optional character wins.
TOURNAMENT_RESULT_TABLES = (
    SAVE_BASE + 0x174,
    SAVE_BASE + 0x438,
)
TOURNAMENT_RESULT_GOLFERS = 40
TOURNAMENT_RESULT_COURSES = 6
TOURNAMENT_RESULT_NATIVE_GOLFER_OFFSET = 14
TOURNAMENT_RESULT_FIRST_PLAYER_ROW = TOURNAMENT_RESULT_NATIVE_GOLFER_OFFSET
TOURNAMENT_RESULT_LAST_PLAYER_ROW_EXCLUSIVE = 37
FIRST_PLACE = 1
UNSET_TOURNAMENT_RESULT = 0x80
NOTIFICATION_SAFE_GAMEPLAY_POLLS = 20
# Result codes can clear before the score/achievement dialog releases the
# shared native text constructor. At the 100 ms client poll cadence, five
# seconds safely carries queued AP receipts past the retail result sequence.
NOTIFICATION_RESULT_COOLDOWN_POLLS = 50
TOURNAMENT_RESULT_ROW_BY_GOLFER = {
    golfer: TOURNAMENT_RESULT_NATIVE_GOLFER_OFFSET + index
    for index, golfer in enumerate(INTERNAL_GOLFER_ORDER)
}
# Retail's hidden-golfer result path uses Petey's raw golfer row rather than
# the +14 native block used by the ordinary roster. This exact byte changed
# from 0x80 to 1 during the captured 0.9.27 Shifting Sands victory and survived
# restart unchanged.
TOURNAMENT_RESULT_ROW_BY_GOLFER["Petey Piranha"] = 12

# One byte per native opponent.  The August 15 before/after capture of a Pro
# win over Mario changed only the first byte, at SAVE_BASE + 0x654, from 0x00
# to 0x08.  The four low bits are the retail difficulty-completion flags, so
# bit 3 is the Pro result required by the Archipelago locations.  This table
# is independent of both Progressive golfer items and retail Star invitations.
CHARACTER_MATCH_PRO_RESULT_TABLE = SAVE_BASE + 0x654
CHARACTER_MATCH_PRO_BIT = 0x08
# Retain the original public name for capture tooling and older diagnostics.
CHARACTER_MATCH_RESULT_FLAGS = CHARACTER_MATCH_PRO_RESULT_TABLE

# Six courses by 18 holes. Zero means no badge; any nonzero byte records the
# best-badge tier earned on that hole. This table was identified by comparing
# clean and completed retail saves (the completed reference has all 108 bytes
# populated).
BEST_BADGE_TABLE = SAVE_BASE + 0x528
BEST_BADGE_COUNT = 6 * 18

# Eighteen per-hole result bytes for the code-unlocked One-On One-Putt side
# game. Zero is uncleared; the completed reference save contains a nonzero
# result for every hole.
ONE_ON_ONE_PUTT_RESULTS = SAVE_BASE + 0x2BE
ONE_ON_ONE_PUTT_HOLES = 18

# The August 5–6 sequences identify the complete Putting/Approach progression
# flags in the settled runtime copy of the retail save record.  Intermediate
# and Expert share byte +0; Novice lives two bytes later. Shot Practice's first
# two clears are monotonic unlock flags in the preceding byte. Trouble Shot has
# no durable bit and is handled from its capture-verified result screen below.
PRACTICE_CLEAR_FLAG_LOCATIONS = (
    (0x80236116, 0x10, practice_clear_location("Putting Practice", "Novice")),
    (0x80236114, 0x20, practice_clear_location("Putting Practice", "Intermediate")),
    (0x80236114, 0x40, practice_clear_location("Putting Practice", "Expert")),
    (0x80236116, 0x02, practice_clear_location("Approach Practice", "Novice")),
    (0x80236114, 0x04, practice_clear_location("Approach Practice", "Intermediate")),
    (0x80236114, 0x08, practice_clear_location("Approach Practice", "Expert")),
    (0x80236113, 0x40, practice_clear_location("Shot Practice", "Tee Shot")),
    (0x80236113, 0x80, practice_clear_location("Shot Practice", "Second Shot")),
)
PRACTICE_CLEAR_FLAG_ADDRESSES = tuple(
    sorted({address for address, _flag, _location in PRACTICE_CLEAR_FLAG_LOCATIONS})
)

PRACTICE_RESULT_TEXT = 0x802CCC20
PRACTICE_RESULT_TEXT_SIZE = 0x80
PRACTICE_HINT_TEXT = 0x802D07E0
PRACTICE_HINT_TEXT_SIZE = 0x100
SHOT_PRACTICE_RESULT_SIGNATURE = b"Shot Practice"
PUTTING_PRACTICE_RESULT_SIGNATURE = b"Putting Practice"
APPROACH_PRACTICE_RESULT_SIGNATURE = b"Approach Practice"
PRACTICE_DIFFICULTY_HINT_LOCATIONS = (
    (
        (b"Practice novice putts.",),
        practice_clear_location("Putting Practice", "Novice"),
    ),
    (
        (b"Practice intermediate putts.",),
        practice_clear_location("Putting Practice", "Intermediate"),
    ),
    (
        (b"Practice expert putts.",),
        practice_clear_location("Putting Practice", "Expert"),
    ),
    (
        (b"Practice novice approach",),
        practice_clear_location("Approach Practice", "Novice"),
    ),
    (
        (b"Practice intermediate", b"approach shots."),
        practice_clear_location("Approach Practice", "Intermediate"),
    ),
    (
        (b"Practice expert approach",),
        practice_clear_location("Approach Practice", "Expert"),
    ),
)
SHOT_PRACTICE_HINT_LOCATIONS = (
    (b"Practice your tee shots.", practice_clear_location("Shot Practice", "Tee Shot")),
    (b"Practice your second shots.", practice_clear_location("Shot Practice", "Second Shot")),
    (b"Practice some difficult shots.", practice_clear_location("Shot Practice", "Trouble Shot")),
)

# Clearing the captured Birdie Challenge Front 9 changes this saved
# progression byte from 0x00 to 0x02 while displaying the retail Back 9 unlock
# message.  Later stage values still need paired captures.
BIRDIE_CHALLENGE_PROGRESS = SAVE_BASE + 0x1299
BIRDIE_CHALLENGE_FRONT_9_COMPLETE = 0x02

# Speed Golf stores the most recently completed round as eighteen big-endian
# centisecond values. The adjacent leaderboard has one 0x3C-byte category per
# retail course; each category begins with the three best total times. A
# captured Lakitu Valley round contained per-hole values totaling 80,066 and a
# matching best time of 80,066 (13:20.66), confirming both the units and
# layout. These records are monotonic enough to use with the client's
# seed-specific persistent baseline.
SPEED_GOLF_LAST_HOLE_TIMES = SAVE_BASE + 0xC08
SPEED_GOLF_HOLES = 18
# The July 30 paired Speed Golf captures advance this live counter from 48 to
# 644 across roughly ten seconds, while the adjacent primary copy is one frame
# ahead. Both reset on the result screen. Use the stable mirror to latch a
# sub-15-second candidate before retail clears it.
SPEED_GOLF_LIVE_HOLE_FRAMES = 0x80523E30
# The live timer's adjacent UI-state word is 0xFF while a Speed Golf hole is
# running.  Two independent result-screen captures change it to 0xC7 and 0xB3
# while the timer itself clears to zero.  This is the reliable settlement edge
# for an individual hole; Speed Golf does not always publish an ordinary
# birdie/par result code for the generic score-edge reader below.
SPEED_GOLF_RESULT_STATE = 0x80523E34
# The final 18-hole Speed Golf scoreboard publishes signed score-to-par here.
# The August 15 under-par capture contains -10; the July 30 completed control
# contains +16 at the same address. Read it only at the verified hole-17
# scoreboard boundary.
SPEED_GOLF_FINAL_SCORE_TO_PAR = 0x805240D0
SPEED_GOLF_COURSE_RECORDS = SAVE_BASE + 0xC2C
SPEED_GOLF_COURSE_RECORD_STRIDE = 0x3C
SPEED_GOLF_LEADERBOARD_ENTRIES = 3
SPEED_GOLF_COURSE_TARGET_CENTISECONDS = 10 * 60 * 100
SPEED_GOLF_UNDER_PAR_TARGET_CENTISECONDS = 15 * 60 * 100
SPEED_GOLF_HOLE_TARGET_CENTISECONDS = 15 * 100
SPEED_GOLF_SIGNATURE = b"SPEED GOLF"

# Near-Pin keeps three leaderboard totals for each of Front 9, Back 9, and
# All 18. Distances are stored in hundredths of a foot: a capture wrote 81,976
# for an 819.76-foot aggregate, while untouched entries use the 200,000
# (2,000-foot) sentinel. The maximum possible 18-hole off-green penalties are
# 1,800 feet, matching the option's upper bound.
NEAR_PIN_RECORDS = SAVE_BASE + 0x12E8
NEAR_PIN_ROUND_LENGTHS = 3
NEAR_PIN_RECORD_STRIDE = 0x18
NEAR_PIN_LEADERBOARD_ENTRIES = 3
NEAR_PIN_UNSET_CENTIFEET = 200_000


def _mask_for_items(
    counts: Counter[str], names: tuple[str, ...], item_name
) -> int:
    mask = 0
    for index, name in enumerate(names):
        if counts[item_name(name)]:
            mask |= 1 << index
    return mask


def club_inventory_text(
    received_names: list[str] | tuple[str, ...],
    club_scope: int,
    golfer: str | None = None,
) -> str:
    """Return the standard-club inventory shown by the client and game popup."""

    counts = Counter(received_names)
    if club_scope == 2:
        if golfer not in PER_CHARACTER_GOLFERS:
            return "Choose a golfer: " + ", ".join(PER_CHARACTER_GOLFERS)
        owned = [
            club
            for club in CLUBS
            if counts[character_club_item(golfer, club)]
        ]
        prefix = f"{golfer} clubs"
    else:
        owned = [club for club in CLUBS if counts[club_item(club)]]
        prefix = "Available clubs"
    return f"{prefix}: {', '.join((*owned, 'Putter'))}"


def spin_permission_mask(
    received_names: list[str] | tuple[str, ...],
    spin_scope: int,
    golfer: str | None = None,
) -> int:
    """Return bits 1..4 for the spin techniques the live golfer may use."""

    if spin_scope == 0:
        return 0x1E
    counts = Counter(received_names)
    techniques = ("Topspin", "Super Topspin", "Backspin", "Super Backspin")
    mask = 0
    for value, technique in enumerate(techniques, 1):
        if spin_scope == 1:
            item_name = spin_item(technique)
        elif spin_scope == 2 and golfer in PER_CHARACTER_GOLFERS:
            item_name = spin_item(technique, golfer)
        else:
            continue
        if counts[item_name]:
            mask |= 1 << value
    return mask


def putter_range_mask(
    received_names: list[str] | tuple[str, ...],
    putter_range_scope: int = 0,
    golfer: str | None = None,
) -> int:
    """Return bits 0..2 for the owned 30-, 100-, and 200-foot putters."""

    counts = Counter(received_names)
    mask = sum(
        (1 << index)
        for index, (global_item, feet) in enumerate(
            zip(PUTTER_RANGE_ITEMS, PUTTER_RANGE_FEET)
        )
        if counts[
            character_putter_range_item(golfer, feet)
            if putter_range_scope == 1 and golfer in PER_CHARACTER_GOLFERS
            else global_item
        ]
    )
    # Compatibility for old rooms and the brief setup interval before a
    # per-character golfer identity is known. Keep the safe short putter.
    return mask or 0x01


def roster_permission_mask(
    received_names: list[str] | tuple[str, ...],
) -> int:
    """Return native character-grid bits for each owned base golfer."""

    counts = Counter(received_names)
    return sum(
        1 << index
        for index, character in enumerate(CHARACTER_SELECT_ORDER)
        if counts[character_item(character)] >= 1
    )


def star_roster_permission_mask(
    received_names: list[str] | tuple[str, ...],
) -> int:
    """Return character-grid bits whose second progressive copy is owned.

    This protocol mask is deliberately separate from retail's Star save mask.
    The latter drives the fixed Character Match invitation chain and cannot
    safely represent out-of-sequence AP inventory.
    """

    counts = Counter(received_names)
    return sum(
        1 << index
        for index, character in enumerate(CHARACTER_SELECT_ORDER)
        if counts[character_item(character)] >= 2
    )


def tournament_permission_mask(
    received_names: list[str] | tuple[str, ...],
) -> int:
    """Return bits 0..5 for regular and 6..11 for Star courses.

    A physical-course item grants both variants. Retired Star-course items are
    still honored in the upper six bits so rooms generated by older APWorlds
    remain playable with a newer client.
    """

    counts = Counter(received_names)
    regular_mask = _mask_for_items(
        counts, REGULAR_TOURNAMENTS, tournament_item
    )
    legacy_star_mask = _mask_for_items(
        counts, STAR_TOURNAMENTS, tournament_item
    )
    return regular_mask | ((regular_mask | legacy_star_mask) << 6)


def mode_permission_mask(
    received_names: list[str] | tuple[str, ...],
) -> int:
    """Return native confirmation-guard bits for owned shuffled modes."""

    counts = Counter(received_names)
    # Doubles, Club Slots, and Training are native local entries rather than
    # Archipelago items.  Keep their native menu IDs allowed even when mode
    # shuffling is enabled; the guard must only deny shuffled entries.
    mask = (1 << 3) | (1 << 5) | (1 << 8)
    mask |= sum(
        1 << native_id
        for mode, native_id in NATIVE_MENU_MODE_IDS.items()
        if counts[mode_item(mode)]
    )
    child_modes = (
        PUTTING_PRACTICE_MODE_ITEM,
        APPROACH_PRACTICE_MODE_ITEM,
        SHOT_PRACTICE_MODE_ITEM,
        BIRDIE_CHALLENGE_MODE_ITEM,
    )
    if counts[mode_item("Near-Pin")] or any(counts[item] for item in child_modes):
        mask |= 1 << NATIVE_MENU_MODE_IDS["Side Games"]
    # Bit 10 is intentionally outside the native main-menu enum.  Priority 3
    # captures identify Side Games child code 0x0D as Putting Practice, and
    # the injected confirmation guard uses this bit for that child entry.
    if counts[PUTTING_PRACTICE_MODE_ITEM]:
        mask |= 1 << 10
    # Captured child codes: 0x09 Birdie Challenge, 0x0B Shot Practice, and
    # 0x0C Approach Practice. Preserve the retired broad Side Games item as a
    # legacy grant of all three, while new rooms use one bit per child.
    legacy_side_games = counts[mode_item("Side Games")]
    if counts[BIRDIE_CHALLENGE_MODE_ITEM] or legacy_side_games:
        mask |= 1 << 11
    if counts[SHOT_PRACTICE_MODE_ITEM] or legacy_side_games:
        mask |= 1 << 12
    if counts[APPROACH_PRACTICE_MODE_ITEM] or legacy_side_games:
        mask |= 1 << 13
    return mask


def putting_practice_difficulty_mask(
    received_names: list[str] | tuple[str, ...],
) -> int:
    """Return Novice/Intermediate/Expert access bits for Putting Practice."""

    counts = Counter(received_names)
    # Novice is native baseline access granted by the Putting Practice mode.
    # Its stable compatibility item remains recognized for old rooms, but new
    # worlds place only Intermediate and Expert upgrades.
    mask = 0x01 if counts[PUTTING_PRACTICE_MODE_ITEM] else 0
    return mask | sum(
        1 << index
        for index, item_name in enumerate(
            PUTTING_PRACTICE_DIFFICULTY_ITEMS
        )
        if counts[item_name]
    )


def sync_putting_practice_difficulty_menu(
    memory,
    received_names: list[str] | tuple[str, ...],
) -> bool:
    """Populate captured Putting/Approach/Shot child menus from AP items.

    This intentionally touches only the transient front-end table. Using the
    native practice-clear flags would falsely complete AP locations and make a
    later legitimate clear indistinguishable from an inventory write.

    All three selectors reuse the same count and entry arrays. Paired vanilla
    captures identify each selector by its first code/target pair:
    Putting=0x11/0x17, Approach=0x11/0x12, Shot=0x0E/0x0F.
    """

    state = int.from_bytes(memory.read_bytes(PUTTING_MENU_STATE, 4), "big")
    if state != PUTTING_MENU_ACTIVE_STATE:
        return False
    first_code = int.from_bytes(
        memory.read_bytes(PUTTING_MENU_CODE_TABLE, 4), "big"
    )
    first_target = int.from_bytes(
        memory.read_bytes(PUTTING_MENU_TARGET_TABLE, 4), "big"
    )
    profiles = {
        (PUTTING_MENU_FIRST_CODE, PUTTING_MENU_FIRST_TARGET): tuple(
            (item_name, index)
            for index, item_name in enumerate(
                PUTTING_PRACTICE_DIFFICULTY_ITEMS[1:], start=1
            )
        ),
        (0x11, 0x12): tuple(
            (item_name, index)
            for index, item_name in enumerate(
                APPROACH_PRACTICE_DIFFICULTY_ITEMS, start=1
            )
        ),
        (0x0E, 0x0F): tuple(
            (item_name, index)
            for index, item_name in enumerate(
                SHOT_PRACTICE_STAGE_ITEMS, start=1
            )
        ),
    }
    upgrades = profiles.get((first_code, first_target))
    if upgrades is None:
        return False

    counts = Counter(received_names)
    # Reaching the selector guarantees its native first level. Higher levels
    # are independent AP items and need not be received in order.
    difficulties = [0] + [
        index for item_name, index in upgrades if counts[item_name]
    ]
    primary = b"".join(
        (first_code + index).to_bytes(4, "big")
        for index in difficulties
    ).ljust(12, b"\0")
    targets = b"".join(
        (first_target + index).to_bytes(4, "big")
        for index in difficulties
    ).ljust(12, b"\0")
    memory.write_bytes(
        PUTTING_MENU_COUNT, len(difficulties).to_bytes(4, "big")
    )
    memory.write_bytes(PUTTING_MENU_CODE_TABLE, primary)
    memory.write_bytes(PUTTING_MENU_TARGET_TABLE, targets)
    return True


def _overlay_matches_immutable_words(
    memory, site: int, expected: tuple[int, int, int]
) -> bool:
    for displacement, word in zip((-4, 4, 8), expected):
        raw = memory.read_bytes(site + displacement, 4)
        if len(raw) != 4 or int.from_bytes(raw, "big") != word:
            return False
    return True


@dataclass
class LiveGameState:
    last_power_capacity: int | None = None
    last_power_values: list[int | None] = field(
        default_factory=lambda: [None, None, None, None]
    )
    # Retail writes its six-shot default shortly after the live-hole marker
    # appears. AP can therefore publish 7..9 on the first observed gameplay
    # poll and have retail overwrite it back to six on the next poll. Delay the
    # one-time AP round synchronization by one complete client poll so retail
    # initializes first. Unlike a settling window, this cannot mistake a
    # legitimate 7->6 use for a late retail write and replenish it.
    power_round_sync_delay_polls: int = 0
    # Tournament can write its retail six-shot default to P1 several seconds
    # after the ordinary two-poll round initialization. Keep repairing only
    # that exact late default while the opening ball remains at rest, then
    # permanently disengage on the first movement so real consumption is
    # never replenished.
    power_round_start_sync_active: bool = False
    last_ball_lie: int | None = None
    last_result_message: int = 0xFFFFFFFF
    consecutive_birdies: int = 0
    last_hole: int | None = None
    round_holes: int = 0
    round_score_to_par: int = 0
    round_had_bogey: bool = False
    round_first_hole: int | None = None
    round_golfer: str | None = None
    round_golfer_consistent: bool = True
    round_par_type_seen: set[int] = field(default_factory=set)
    round_par_type_all_birdie: dict[int, bool] = field(
        default_factory=lambda: {3: True, 4: True, 5: True}
    )
    last_ball_position: tuple[float, float, float] | None = None
    aim_power_remaining: int = 0
    aim_ball_lie: int | None = None
    shot_origin: tuple[float, float, float] | None = None
    shot_club: int | None = None
    shot_type: int | None = None
    shot_lie: int | None = None
    shot_course: int | None = None
    shot_hole: int | None = None
    shot_power_before: int = 0
    # A perfect Power Shot has an unchanged net counter; a miss loses one.
    # Retail can internally expose a provisional consume-then-refund sequence,
    # so retain that timing evidence when sampled while also preserving the
    # stable pre-shot value for the ordinary net-result test.
    shot_power_was_consumed: bool = False
    shot_live_player_index: int | None = None
    perfect_power_refund_observed: bool = False
    pending_power_refund_hole: int | None = None
    pending_power_refund_expected: int = 0
    pending_power_refund_polls: int = 0
    shot_max_distance: float = 0.0
    shot_stationary_polls: int = 0
    last_completed_shot_distance: float = 0.0
    last_completed_shot_lie: int | None = None
    last_completed_shot_club: int | None = None
    last_completed_shot_player_index: int | None = None
    last_live_club: int | None = None
    last_mulligan_value: int | None = None
    last_mulligan_received: int = 0
    advance_tour_warning: str | None = None
    reported_advance_tour_warning: str | None = None
    active_native_golfer: str | None = None
    active_advance_tour_golfer: str | None = None
    active_golfer_display_name: str | None = None
    advance_tour_holes_completed: dict[str, int] = field(
        default_factory=lambda: {"Neil": 0, "Ella": 0}
    )
    selected_golfer_visible: bool = False
    character_select_was_active: bool = False
    first_confirmed_round_golfer: str | None = None
    last_confirmed_round_golfer: str | None = None
    resumable_round_golfer: str | None = None
    last_roster_confirm_sequence: int | None = None
    last_tournament_result_tables: tuple[bytes, ...] | None = None
    notification_screen_safe: bool = False
    notification_live_stable_polls: int = 0
    notification_result_cooldown_polls: int = 0
    notification_scene_token: tuple[int, int] | None = None
    gameplay_marker_observed: bool = False
    verified_gameplay_active: bool = False
    last_character_match_star_mask: int | None = None
    last_character_match_result_flags: bytes | None = None
    retail_character_match_star_mask: int | None = None
    character_match_session_active: bool = False
    character_match_session_armed: bool = False
    ring_attack_session_active: bool = False
    last_mode_confirm_sequence: int | None = None
    isolate_character_match_invitations: bool = False
    last_hole_score_result: int | None = None
    last_scored_hole: int | None = None
    last_club_notice_key: tuple | None = None
    club_inventory_notice: str | None = None
    club_notice_screen_was_safe: bool = False
    active_coin_course: str | None = None
    coin_session_active: bool = False
    coin_session_variant: str | None = None
    coin_session_character: str | None = None
    pending_coin_credit: tuple[str, str, int] | None = None
    hole_in_one_contest_active: bool = False
    bowsers_big_blast_active: bool = False
    special_clear_visible: bool = False
    hole_in_one_contest_reported: bool = False
    bowsers_big_blast_reported: bool = False
    live_practice_clear_visible: bool = False
    speed_golf_under_par_pending: bool = False
    speed_golf_candidate_hole: int | None = None
    speed_golf_candidate_frames: int | None = None
    speed_golf_result_screen_visible: bool = False
    speed_golf_round_frames: int = 0
    speed_golf_round_timed_holes: int = 0
    speed_golf_round_course: int | None = None
    speed_golf_last_settled_hole: int | None = None
    standard_round_scoreboard_reported: bool = False
    active_live_player_index: int | None = None

    def apply_received_items(
        self,
        memory,
        received_names: list[str],
        *,
        club_scope: int = 1,
        fallback_club: str | None = None,
        putter_range_scope: int = 0,
        spin_scope: int = 0,
        gate_modes: bool = False,
        unlock_all_character_match_courses: bool = False,
        advance_tour_golfer_distances: tuple[int, int] = (305, 300),
        mulligans_spent: int | None = None,
        allow_save_writes: bool = True,
        preserve_character_match_invitations: bool = False,
        completed_character_match_checks: set[str] | None = None,
        native_selected_mode: int | None = None,
        confirmed_roster_golfer: str | None = None,
        confirmed_roster_sequence: int | None = None,
        sync_power_capacity: bool = True,
    ) -> int:
        """Apply AP inventory and return newly consumed Player 1 Mulligans.

        ``mulligans_spent`` is loaded from room DataStorage.  Until that value
        is available the counter is deliberately left alone, preventing an
        attach/reconnect race from duplicating already-used consumables.
        """

        counts = Counter(received_names)
        golfer_mask = 0
        for index, character in enumerate(INTERNAL_GOLFER_ORDER):
            if counts[character_item(character)] >= 1:
                golfer_mask |= 1 << index
        star_golfer_mask = 0
        for index, character in enumerate(STAR_GOLFER_ORDER):
            if counts[character_item(character)] >= 2:
                star_golfer_mask |= 1 << index
        sync_putting_practice_difficulty_menu(memory, received_names)
        character_select_active = any(
            _overlay_matches_immutable_words(memory, site, signature)
            for site, signature in CHARACTER_SELECT_OVERLAY_SIGNATURES
        )
        mode_select_active = _overlay_matches_immutable_words(
            memory,
            MODE_SELECT_OVERLAY_SITE,
            MODE_SELECT_OVERLAY_IMMUTABLE_WORDS,
        )
        # The native top-level trace correctly reports Ring Attack when it is
        # first confirmed, but multiplayer setup later runs through the
        # Doubles player-count path and overwrites the same trace with mode 3.
        # The August 14 F2 capture caught that later state: P1 was restricted,
        # P2 had initialized to 0x3FFF, and the trace said Doubles. Latch the
        # original Ring Attack confirmation through setup/gameplay; entering a
        # different mode from the verified top-level overlay clears it.
        if native_selected_mode == NATIVE_MENU_MODE_IDS["Ring Attack"]:
            self.ring_attack_session_active = True
        elif mode_select_active:
            self.ring_attack_session_active = False
        if allow_save_writes:
            self.advance_tour_warning = apply_advance_tour_items(
                memory, counts, advance_tour_golfer_distances
            )
        else:
            self.advance_tour_warning = None
        current_hole = memory.read_bytes(CURRENT_HOLE, 1)[0]

        # Character-grid state is transient presentation data, not durable
        # progression. Publish it immediately once the exact overlay is
        # verified instead of waiting for the memory-card startup grace used
        # by permanent save mutations. Without this fast path, a restart could
        # construct the first grid from stale retail Star/hidden-golfer state;
        # leaving and re-entering character select then appeared to "fix" it.
        if character_select_active and not allow_save_writes:
            memory.write_bytes(
                STAR_GOLFER_UNLOCK_MASK, star_golfer_mask.to_bytes(2, "big")
            )
            self.last_character_match_star_mask = star_golfer_mask
            roster_prefix = memory.read_bytes(
                CHARACTER_SELECT_ROSTER_LIST,
                CHARACTER_SELECT_HIDDEN_FIRST * 4,
            )
            expected_prefix = b"".join(
                index.to_bytes(4, "big")
                for index in range(CHARACTER_SELECT_HIDDEN_FIRST)
            )
            if roster_prefix == expected_prefix:
                memory.write_bytes(
                    CHARACTER_SELECT_ROSTER_LIST
                    + CHARACTER_SELECT_HIDDEN_FIRST * 4,
                    b"".join(
                        (
                            golfer_id.to_bytes(4, "big")
                            if counts[
                                character_item(
                                    CHARACTER_SELECT_ORDER[golfer_id]
                                )
                            ]
                            else b"\xFF\xFF\xFF\xFF"
                        )
                        for golfer_id in range(
                            CHARACTER_SELECT_HIDDEN_FIRST,
                            CHARACTER_SELECT_ROSTER_COUNT,
                        )
                    ),
                )

        if allow_save_writes:
            tournament_mask = tournament_permission_mask(received_names)
            if unlock_all_character_match_courses:
                # Retail reuses its six regular-tournament availability bits
                # for Character Match course access. Expose those courses so
                # Character Match locations cannot be stranded by AP item
                # order. New all-courses worlds precollect the matching six
                # regular Tournament items because the two menus cannot be
                # separated with the captured retail state alone.
                tournament_mask |= (1 << len(REGULAR_TOURNAMENTS)) - 1
            # Preserve retail-owned middle bits, synchronize only the four
            # genuinely hidden golfers, and expose a course when either its
            # regular or Star Tournament item is owned. The native course
            # guard below distinguishes regular from Star ownership at A.
            current_golfer_course = int.from_bytes(
                memory.read_bytes(GOLFER_UNLOCK_MASK, 2), "big"
            )
            # Retail never normally exposes Boo/Bowser Jr./Petey/Shadow Mario
            # as base-only golfers: their native unlock also grants the Star.
            # The August 14 missing-Koopa-letter capture had a correctly
            # isolated zero Star mask but Petey's synthetic base bit (0x1000)
            # remained present while Character Match built its opponent list.
            # A known-positive Koopa invitation had no hidden-golfer bits.
            # Hide AP's base-only compatibility bits during that front-end
            # construction and restore them automatically everywhere else.
            character_match_frontend_active = (
                preserve_character_match_invitations
                and native_selected_mode
                == NATIVE_MENU_MODE_IDS["Character Match"]
                and (character_select_active or mode_select_active)
            )
            hidden_golfers = (
                0
                if character_match_frontend_active
                else golfer_mask & HIDDEN_GOLFER_SAVE_MASK
            )
            physical_courses = (
                tournament_mask | (tournament_mask >> len(REGULAR_TOURNAMENTS))
            ) & 0x3F
            course_flags = (physical_courses >> 1) & 0x1F
            golfer_course = (
                current_golfer_course
                & ~(HIDDEN_GOLFER_SAVE_MASK | 0x001F)
                | hidden_golfers
                | course_flags
            )
            memory.write_bytes(
                GOLFER_UNLOCK_MASK, golfer_course.to_bytes(2, "big")
            )
            self.isolate_character_match_invitations = (
                preserve_character_match_invitations
            )
            if preserve_character_match_invitations:
                current_retail_star_mask = int.from_bytes(
                    memory.read_bytes(STAR_GOLFER_UNLOCK_MASK, 2), "big"
                )
                server_character_match_mask = None
                if completed_character_match_checks is not None:
                    server_character_match_mask = sum(
                        1 << index
                        for index, character in enumerate(STAR_GOLFER_ORDER)
                        if f"Character Match - Unlock Star {character}"
                        in completed_character_match_checks
                    )
                if self.retail_character_match_star_mask is None:
                    # AP Star display bits are written into the retail save
                    # word outside Character Match and can survive a client
                    # restart. They are not invitation progress. Remove every
                    # currently owned AP Star on first attachment so a prior
                    # display write cannot permanently consume retail letters.
                    # A genuine non-AP retail Star remains preserved.
                    self.retail_character_match_star_mask = (
                        server_character_match_mask
                        if server_character_match_mask is not None
                        else current_retail_star_mask & ~star_golfer_mask
                    )
                elif server_character_match_mask is not None:
                    # Archipelago checks are the durable invitation authority.
                    # Preserve a newly observed native win until its LocationChecks
                    # packet is acknowledged, while allowing reconnects to rebuild
                    # the chain without consulting AP-owned Star golfer bits.
                    self.retail_character_match_star_mask |= (
                        server_character_match_mask
                    )
                native_menu_mode = (
                    native_selected_mode
                    if native_selected_mode is not None
                    else int.from_bytes(
                        memory.read_bytes(GAMEPLAY_MARKER, 4), "big"
                    )
                )
                # Character select is an explicit front-end boundary.  The
                # native selected-mode latch is cleared while that overlay is
                # active, so leaving Character Match used to preserve a stale
                # ``character_match_session_active`` value and display the
                # retail invitation mask (for example Koopa) instead of the
                # AP-owned Star roster.  Always leave the isolated Character
                # Match session before presenting the character grid.
                if (
                    character_select_active
                    and native_selected_mode
                    != NATIVE_MENU_MODE_IDS["Character Match"]
                ):
                    self.character_match_session_active = False
                # The native guard records the last mode actually confirmed.
                # Direct unit callers and old hooks retain the legacy marker
                # fallback, but the combined client no longer mistakes the
                # character-select overlay's reset value for Tournament.
                elif 0 <= native_menu_mode <= 9:
                    self.character_match_session_active = (
                        native_menu_mode == NATIVE_MENU_MODE_IDS["Character Match"]
                    )
                # AP Star bits are presentation state, not retail save
                # progression. Expose them only on character select. Restore
                # the retail-only shadow as soon as mode select opens, before
                # Character Match constructs its invitation roster. Keeping AP
                # bits present through mode select created a polling race: the
                # native confirmation hook restored the retail shadow, then a
                # desktop poll could reapply the AP mask before the letter was
                # built. The chosen base/Star form already lives in the player
                # selection object by this point and does not require the save
                # word to remain contaminated.
                if (
                    character_select_active
                    and native_selected_mode
                    != NATIVE_MENU_MODE_IDS["Character Match"]
                    and not self.character_match_session_active
                ):
                    applied_star_mask = star_golfer_mask
                else:
                    applied_star_mask = self.retail_character_match_star_mask
            else:
                applied_star_mask = star_golfer_mask
            memory.write_bytes(
                STAR_GOLFER_UNLOCK_MASK, applied_star_mask.to_bytes(2, "big")
            )
            # The client itself owns this write. Advance the observer baseline
            # immediately so a later poll cannot reinterpret an AP-delivered
            # second progressive copy as a retail Character Match victory.
            # Genuine wins still rise between polls and are sampled before
            # this synchronization in dolphin_sync.
            self.last_character_match_star_mask = applied_star_mask
            roster_prefix = memory.read_bytes(
                CHARACTER_SELECT_ROSTER_LIST,
                CHARACTER_SELECT_HIDDEN_FIRST * 4,
            )
            expected_prefix = b"".join(
                index.to_bytes(4, "big")
                for index in range(CHARACTER_SELECT_HIDDEN_FIRST)
            )
            if roster_prefix == expected_prefix:
                hidden_slots = b"".join(
                    (
                        golfer_id.to_bytes(4, "big")
                        if counts[
                            character_item(CHARACTER_SELECT_ORDER[golfer_id])
                        ]
                        else b"\xFF\xFF\xFF\xFF"
                    )
                    for golfer_id in range(
                        CHARACTER_SELECT_HIDDEN_FIRST,
                        CHARACTER_SELECT_ROSTER_COUNT,
                    )
                )
                memory.write_bytes(
                    CHARACTER_SELECT_ROSTER_LIST
                    + CHARACTER_SELECT_HIDDEN_FIRST * 4,
                    hidden_slots,
                )

        selected_name = selected_golfer_display_name(memory) or ""
        selected_golfer = (
            selected_name if selected_name in CHARACTERS else None
        )
        selected_advance_tour_golfer = (
            advance_tour_identity_for_name(memory, selected_name)
            if selected_golfer is None
            else None
        )
        visible_golfer = selected_golfer or selected_advance_tour_golfer
        self.selected_golfer_visible = visible_golfer is not None
        gameplay_marker = int.from_bytes(
            memory.read_bytes(GAMEPLAY_MARKER, 4), "big"
        )
        gameplay_marker_is_active = (
            gameplay_marker == GAMEPLAY_MARKER_ACTIVE
        )
        if character_select_active and not self.character_select_was_active:
            # A fresh character-select visit begins a new player roster. Do
            # not latch the initially highlighted portrait; wait for the
            # native A-confirmation trace below.
            self.first_confirmed_round_golfer = None
            self.last_confirmed_round_golfer = None
        roster_confirmation_changed = (
            confirmed_roster_sequence is not None
            and self.last_roster_confirm_sequence is not None
            and confirmed_roster_sequence != self.last_roster_confirm_sequence
        )
        attached_during_active_round = (
            confirmed_roster_sequence is not None
            and self.last_roster_confirm_sequence is None
            and gameplay_marker_is_active
        )
        if confirmed_roster_sequence is not None:
            self.last_roster_confirm_sequence = confirmed_roster_sequence
        if (
            (
                character_select_active and roster_confirmation_changed
            )
            or attached_during_active_round
        ) and (
            confirmed_roster_golfer in CHARACTERS
        ):
            # Keep both ends of the confirmation sequence. Multiplayer Ring
            # Attack needs the first accepted golfer as its shared P1 bag, but
            # a single-player user can confirm Boo, press B, and then confirm
            # Bowser without leaving this overlay. Using only the first value
            # leaked Boo's clubs into Bowser's first round until the player
            # exited and re-entered the mode.
            if self.first_confirmed_round_golfer is None:
                self.first_confirmed_round_golfer = confirmed_roster_golfer
            self.last_confirmed_round_golfer = confirmed_roster_golfer
        self.character_select_was_active = character_select_active
        was_gameplay_active = self.verified_gameplay_active
        self.gameplay_marker_observed = True
        self.verified_gameplay_active = (
            gameplay_marker == GAMEPLAY_MARKER_ACTIVE
        )
        gameplay_session_started = (
            self.verified_gameplay_active and not was_gameplay_active
        )
        if (
            gameplay_session_started
            and self.first_confirmed_round_golfer is None
            and self.last_confirmed_round_golfer is None
            and self.resumable_round_golfer in CHARACTERS
        ):
            # Choosing Continue resumes the saved round without producing a
            # new character-confirmation sequence. A visit to character select
            # immediately beforehand can leave its highlighted portrait in the
            # shared name buffer (for example Mario) even though the saved
            # round still belongs to Petey Piranha. Restore the last golfer
            # proven during live play before applying per-character equipment.
            self.first_confirmed_round_golfer = self.resumable_round_golfer
            self.last_confirmed_round_golfer = self.resumable_round_golfer
        if self.verified_gameplay_active:
            self.notification_live_stable_polls = min(
                self.notification_live_stable_polls + 1,
                NOTIFICATION_SAFE_GAMEPLAY_POLLS,
            )
        else:
            self.notification_live_stable_polls = 0
        # Native Eagle/Chip-In/Best-Badge and similar result dialogs share the
        # same constructor as AP popups. The August 14 Eagle+pin+chip failure
        # reached 0x800246c8/0x800246cc even though the live-hole marker had
        # been stable for minutes: the item receipts arrived while that result
        # dialog was retiring. Observe both native result slots here and keep
        # the Python queue intact until five seconds after they become idle.
        if live_result_values(memory):
            self.notification_result_cooldown_polls = (
                NOTIFICATION_RESULT_COOLDOWN_POLLS
            )
        elif self.notification_result_cooldown_polls > 0:
            self.notification_result_cooldown_polls -= 1
        # Selected-golfer text and the old 0..9 setup marker are both reused by
        # menu/save dialogs. The supplied freeze captures prove they cannot
        # authorize native popup construction. Only the exact live-hole marker
        # is safe enough for this recovery build.
        # Ring Attack keeps the ordinary live-hole marker active while its clear
        # sequence constructs the native golfer-unlock-style dialog. Creating
        # an AP popup during that overlap corrupts the retail text path at
        # 0x800246c8/0x800246cc. Keep receipts queued until the player reaches
        # a live hole in another mode.
        self.notification_screen_safe = (
            self.verified_gameplay_active
            and self.notification_live_stable_polls
            >= NOTIFICATION_SAFE_GAMEPLAY_POLLS
            and self.notification_result_cooldown_polls == 0
            and native_selected_mode != NATIVE_MENU_MODE_IDS["Ring Attack"]
        )
        self.notification_scene_token = (
            (gameplay_marker, current_hole)
            if self.notification_screen_safe
            else None
        )
        # This UI buffer is trustworthy only while the captured character-grid
        # overlay is loaded. Later menus reuse it for prose such as "Luigi's to
        # the pin", which previously changed an active Mario round to Luigi and
        # applied a newly received per-character club to the wrong bag until a
        # later refresh happened to repair the identity.
        character_match_active = (
            native_selected_mode == NATIVE_MENU_MODE_IDS["Character Match"]
        )
        if (
            character_match_active
            and confirmed_roster_golfer in CHARACTERS
        ):
            # Character Match keeps the native P1 confirmation latched while
            # constructing the opponent and playing the match.  It is more
            # authoritative than ``first_confirmed_round_golfer``, which can
            # survive from an earlier ordinary/multiplayer session when the
            # reused character-grid overlay never produces a clean leave/enter
            # edge.  The August 13 Petey/Koopa capture demonstrated that stale
            # Mario state by publishing a PW-only 0x2400 limiter even though
            # the native trace had confirmed Petey.  Replace the shared owner
            # at Character Match entry; Ring Attack retains its separate P1
            # shared-bag behavior because it never enters this branch.
            self.first_confirmed_round_golfer = confirmed_roster_golfer
            self.last_confirmed_round_golfer = confirmed_roster_golfer
        if (
            character_match_active
            and (
                self.first_confirmed_round_golfer in CHARACTERS
                or confirmed_roster_golfer in CHARACTERS
            )
        ):
            # Character Match reuses the character-select golfer-name buffer
            # while constructing the CPU opponent.  The Donkey Kong/Koopa
            # captures show that trusting that second name routes P1 clubs and
            # golfer accomplishments to Koopa.  The native roster-confirmation
            # trace remains latched to the human golfer for the whole match,
            # so it is the authoritative identity in this mode.
            self.active_native_golfer = (
                confirmed_roster_golfer or self.first_confirmed_round_golfer
            )
            self.active_advance_tour_golfer = None
            self.active_golfer_display_name = self.active_native_golfer
        elif (
            self.first_confirmed_round_golfer in CHARACTERS
            or self.last_confirmed_round_golfer in CHARACTERS
            or (
                self.verified_gameplay_active
                and confirmed_roster_golfer in CHARACTERS
            )
        ):
            # Ring Attack deliberately shares P1's restricted bag with its
            # human players. The local Doubles/Club Slots selectors can also
            # collect multiple roster confirmations. Ordinary single-player
            # modes instead use the final accepted golfer so backing out of an
            # earlier choice cannot leak that golfer's clubs into the round.
            shared_multiplayer_roster = (
                self.ring_attack_session_active
                or native_selected_mode in (3, 5)
            )
            active_confirmed_golfer = (
                self.first_confirmed_round_golfer
                if shared_multiplayer_roster
                else (
                    self.last_confirmed_round_golfer
                    or confirmed_roster_golfer
                    or self.first_confirmed_round_golfer
                )
            )
            self.active_native_golfer = active_confirmed_golfer
            self.active_advance_tour_golfer = None
            self.active_golfer_display_name = self.active_native_golfer
        elif selected_golfer is not None and character_select_active:
            # The character/setup screen exposes the exact P1 golfer name at
            # this address. During play the buffer is reused for help text, so
            # retain the last verified name into the round. The former
            # ball-effect inference mapped Luigi to Waluigi and was also
            # unavailable on zero-based hole 1.
            self.active_native_golfer = selected_golfer
            self.active_advance_tour_golfer = None
            self.active_golfer_display_name = selected_name
        elif selected_advance_tour_golfer is not None and character_select_active:
            self.active_native_golfer = None
            self.active_advance_tour_golfer = selected_advance_tour_golfer
            self.active_golfer_display_name = selected_name

        if self.verified_gameplay_active:
            active_advance = active_advance_tour_identity(memory)
            if active_advance is not None:
                self.active_native_golfer = None
                (
                    self.active_advance_tour_golfer,
                    self.active_golfer_display_name,
                ) = active_advance
            elif self.active_native_golfer in CHARACTERS:
                self.resumable_round_golfer = self.active_native_golfer

        # Do not automatically enqueue club summaries. The 0.9.8 captures show
        # that menu/setup text and markers are reused during save dialogs, and
        # repeated bag refreshes were a major source of the stacked messages.
        # `/clubs` remains available as an explicit request and is displayed in
        # game only when the exact live-hole marker is active.
        self.club_notice_screen_was_safe = self.notification_screen_safe

        # The addresses below belong to live-round objects and are reused by
        # unrelated UI screens. Writing them while viewing Records can corrupt
        # a UI pointer (the reported crash read from the end of MEM1). The
        # paired setup/gameplay captures provide this fail-closed marker.
        if self.gameplay_marker_observed and not self.verified_gameplay_active:
            return 0

        active_per_character_golfer = (
            self.active_native_golfer or self.active_advance_tour_golfer
        )
        active_player_object = int.from_bytes(
            memory.read_bytes(ACTIVE_PLAYER_OBJECT_POINTER, 4), "big"
        )
        active_player_offset = active_player_object - PLAYER_ONE_LIVE_OBJECT
        if (
            active_player_offset >= 0
            and active_player_offset % CLUB_LIMITER_PLAYER_STRIDE == 0
            and active_player_offset // CLUB_LIMITER_PLAYER_STRIDE < 4
        ):
            self.active_live_player_index = (
                active_player_offset // CLUB_LIMITER_PLAYER_STRIDE
            )
        else:
            self.active_live_player_index = None
        club_mask = PUTTER_CLUB_BIT
        for index, club in enumerate(CLUBS):
            if club_scope == 2 and active_per_character_golfer is not None:
                available = counts[
                    character_club_item(active_per_character_golfer, club)
                ]
            elif club_scope == 2:
                # Before the live golfer identity is populated, expose one
                # seed-defined safety club. The old union fallback exposed
                # nearly the entire bag on hole 1, while requiring a common
                # precollected club made every golfer's randomized starter the
                # same.
                available = club == fallback_club
            else:
                available = counts[club_item(club)]
            if available:
                club_mask |= 1 << index
        memory.write_bytes(CLUB_LIMITER, club_mask.to_bytes(4, "big"))

        # Multiplayer Ring Attack constructs independent live player objects.
        # P1 uses the Archipelago limiter above. For the 1.0 public beta,
        # P2-P4 deliberately retain their retail full bags: repeated captures
        # showed that their objects are initialized after the top-level Ring
        # Attack trace has already been replaced by the shared Doubles setup
        # trace. Polling those transient objects was not reliable enough to
        # justify delaying or destabilizing multiplayer checks.

        current_club = int.from_bytes(memory.read_bytes(CURRENT_CLUB, 4), "big")
        player_one_selector_safe = (
            self.active_live_player_index == 0
            or (
                self.active_live_player_index is None
                and not character_match_active
            )
        )
        if (
            player_one_selector_safe
            and 0 <= current_club < len(CLUBS)
            and not (club_mask & (1 << current_club))
        ):
            # Retail recommends a lie-appropriate club before consulting the
            # AP limiter. Correct that temporary illegal selection only while
            # the captured live-object pointer proves this is P1's turn; the
            # same selector is shared with Character Match's CPU.
            owned_standard_clubs = [
                index
                for index in range(len(CLUBS))
                if club_mask & (1 << index)
            ]
            legal_clubs = owned_standard_clubs or [PUTTER_CLUB_INDEX]
            current_club = min(
                legal_clubs,
                key=lambda index: (abs(index - current_club), index),
            )
            memory.write_bytes(CURRENT_CLUB, current_club.to_bytes(4, "big"))
        shot_type = int.from_bytes(
            memory.read_bytes(CURRENT_SHOT_TYPE, 4), "big"
        )
        # Retail reuses this selector: on the putter it means 30/100/200 feet.
        # On an ordinary club the captured final-Power baseline resolves
        # 0=Power, 1=Normal, and 2=Approach. Earlier builds treated 1 as
        # Approach and repeatedly rewrote Normal to Power, causing the forced
        # Power/constant-sound bug whenever Approach was locked.
        # A gated putter range can otherwise leak into the next club and leave
        # every club visibly locked to Power. Clear only that exact transition;
        # later player-selected Power and Approach states remain untouched.
        if player_one_selector_safe:
            if (
                current_club != PUTTER_CLUB_INDEX
                and self.last_live_club == PUTTER_CLUB_INDEX
            ):
                shot_type = NORMAL_SHOT_TYPE
                memory.write_bytes(
                    CURRENT_SHOT_TYPE,
                    NORMAL_SHOT_TYPE.to_bytes(4, "big"),
                )
            # This is P1 transition history. Character Match's CPU shares the
            # selector and club fields, but must never advance this state or a
            # CPU club change can be mistaken for P1 leaving the putter.
            self.last_live_club = current_club
        capacity = min(counts[POWER_SHOT_ITEM], 9)
        if (
            current_club == PUTTER_CLUB_INDEX
            and player_one_selector_safe
        ):
            owned_ranges = [
                # Retail's selector is reversed: 0=200 ft, 1=100 ft, 2=30 ft.
                2 - index
                for index, (global_item, feet) in enumerate(
                    zip(PUTTER_RANGE_ITEMS, PUTTER_RANGE_FEET)
                )
                if counts[
                    character_putter_range_item(
                        active_per_character_golfer, feet
                    )
                    if putter_range_scope == 1
                    and active_per_character_golfer in PER_CHARACTER_GOLFERS
                    else global_item
                ]
            ]
            # Rooms generated before 0.8.0 have no explicit 30-foot item;
            # retain their retail default instead of disabling the putter.
            if not owned_ranges:
                owned_ranges = [2]
            if shot_type not in owned_ranges:
                lower_ranges = [
                    range_index
                    for range_index in owned_ranges
                    if range_index < shot_type
                ]
                fallback = max(lower_ranges) if lower_ranges else min(owned_ranges)
                memory.write_bytes(
                    CURRENT_SHOT_TYPE, fallback.to_bytes(4, "big")
                )
        elif (
            player_one_selector_safe
            and current_club != PUTTER_CLUB_INDEX
            and shot_type == APPROACH_SHOT_TYPE
            and not counts[APPROACH_SHOT_ITEM]
        ):
            memory.write_bytes(
                CURRENT_SHOT_TYPE,
                NORMAL_SHOT_TYPE.to_bytes(4, "big"),
            )
        # Do not continuously rewrite the non-putter Power Shot selector.
        # The captured zero-capacity screen showed that fighting retail's
        # selector makes it repeatedly toggle during the swing. The four
        # remaining-shot counters below are the authoritative gameplay gate
        # and stay clamped to the received AP capacity.

        # The captured spin value is set and consumed after both the desktop
        # polling point and the current frame-hook point. Clearing it here made
        # locked spins intermittent without reliably suppressing their effect.
        # Keep publishing the compact permission mask, but do not mutate live
        # spin state until the actual retail setter/consumer hook is mapped.

        if gate_modes:
            self.enforce_mode_unlocks(memory, counts)

        # Do not infer popup ownership from the ball-effect field. It can hold
        # transient/sentinel values between turns, which previously produced
        # unsolicited notices for the wrong golfer. Automatic summaries above
        # use only the captured selected-golfer name on a verified-safe setup
        # screen.
        hole_reset = (
            self.last_hole is not None
            and current_hole <= 1
            and current_hole < self.last_hole
        )
        hole_changed = (
            self.last_hole is not None and current_hole != self.last_hole
        )
        if sync_power_capacity:
            if gameplay_session_started or hole_reset:
                self.power_round_sync_delay_polls = 2
                self.power_round_start_sync_active = (
                    capacity > 6
                    and native_selected_mode
                    in (
                        NATIVE_MENU_MODE_IDS["Tournament"],
                        NATIVE_MENU_MODE_IDS["Stroke Play"],
                    )
                )
            if (
                self.power_round_start_sync_active
                and self.last_ball_position is not None
            ):
                raw_position = memory.read_bytes(BALL_COORDINATES, 12)
                current_position = struct.unpack(">fff", raw_position)
                if all(
                    math.isfinite(value) and abs(value) < 1_000_000
                    for value in current_position
                ) and (
                    self._horizontal_distance(
                        self.last_ball_position, current_position
                    ) > 0.05
                    or abs(
                        self.last_ball_position[1] - current_position[1]
                    ) > 0.05
                ):
                    self.power_round_start_sync_active = False
            delayed_round_sync = self.power_round_sync_delay_polls
            for player, address in enumerate(POWER_SHOT_REMAINING):
                current = memory.read_bytes(address, 1)[0]
                previous = self.last_power_values[player]

                capacity_gain = (
                    self.last_power_capacity is not None
                    and capacity > self.last_power_capacity
                )
                if capacity == 0:
                    # Legacy/debug zero-capacity rooms need the authoritative
                    # counter clamp immediately; they do not have a valid
                    # retail opening capacity to preserve during the delay.
                    target = 0
                elif delayed_round_sync > 1:
                    # Let retail finish writing its six-shot round default.
                    target = current
                elif delayed_round_sync == 1:
                    # Apply the AP capacity once, after retail initialization.
                    target = capacity
                elif (
                    player == 0
                    and self.power_round_start_sync_active
                    and current == 6
                    and capacity > 6
                ):
                    # Tournament and Stroke Play both run a later P1-only
                    # initializer: P1 is reset to six while P2-P4 retain the
                    # synchronized AP capacity. Repair that retail default
                    # until the opening shot starts.
                    target = capacity
                elif previous is None:
                    target = capacity
                elif capacity_gain:
                    target = min(
                        capacity,
                        current + capacity - self.last_power_capacity,
                    )
                elif current > previous:
                    active_power_refund = (
                        player == 0
                        and current == previous + 1
                        and current <= capacity
                        and self.shot_origin is not None
                        and self.shot_type == POWER_SHOT_TYPE
                        and self.shot_power_before == current
                        and self.shot_power_was_consumed
                        and self.shot_live_player_index in (None, 0)
                        and self.shot_hole == current_hole
                    )
                    pending_power_refund = (
                        player == 0
                        and current == previous + 1
                        and current <= capacity
                        and self.pending_power_refund_polls > 0
                        and self.pending_power_refund_hole == current_hole
                        and self.pending_power_refund_expected == current
                    )
                    if active_power_refund or pending_power_refund:
                        # This is useful evidence for the accomplishment
                        # reader, but retail itself owns the refund. Never
                        # synthesize or reject the counter transition here.
                        self.perfect_power_refund_observed = True
                        self.pending_power_refund_hole = None
                        self.pending_power_refund_expected = 0
                        self.pending_power_refund_polls = 0

                    if (
                        player == 0
                        and hole_changed
                        and not hole_reset
                        and current == 6
                    ):
                        # Tournament rewrites P1 to its ordinary six-shot
                        # opening value at the front-nine/back-nine boundary.
                        # That is not a shot refund or AP item receipt, so keep
                        # the consumed value from the preceding hole.
                        target = previous
                    else:
                        # Retail owns ordinary in-shot counter behavior. In
                        # particular, a perfect impact may expose a temporary
                        # decrement followed by a +1 refund. Accept the value
                        # instead of racing that native lifecycle; AP only
                        # supplies the capacity ceiling.
                        target = min(current, capacity)
                else:
                    # Ordinary use remains consumed and values above the owned
                    # capacity remain unavailable.
                    target = min(current, capacity)
                    if (
                        player == 0
                        and previous is not None
                        and current == previous - 1
                        and current_club != PUTTER_CLUB_INDEX
                        and shot_type == POWER_SHOT_TYPE
                        and self.verified_gameplay_active
                        and player_one_selector_safe
                        and self.last_hole == current_hole
                        and native_selected_mode
                        in (
                            NATIVE_MENU_MODE_IDS["Tournament"],
                            NATIVE_MENU_MODE_IDS["Stroke Play"],
                        )
                    ):
                        # Retail can consume and refund a perfect Power Shot
                        # entirely before the first observable ball movement.
                        # At that point the shot tracker has no origin yet, so
                        # remember this exact P1/same-hole decrement briefly.
                        # A subsequent +1 back to the pre-shot value is the
                        # native perfect-impact refund; a miss simply leaves
                        # the lower count in place and this candidate expires.
                        self.pending_power_refund_hole = current_hole
                        self.pending_power_refund_expected = previous
                        self.pending_power_refund_polls = 30

                if target != current:
                    memory.write_bytes(address, bytes((target,)))
                self.last_power_values[player] = target

            self.last_power_capacity = capacity
            if self.power_round_sync_delay_polls:
                self.power_round_sync_delay_polls -= 1
            if (
                self.pending_power_refund_hole is not None
                and self.pending_power_refund_hole != current_hole
            ):
                self.pending_power_refund_hole = None
                self.pending_power_refund_expected = 0
                self.pending_power_refund_polls = 0
            elif self.pending_power_refund_polls:
                self.pending_power_refund_polls -= 1

        newly_spent_mulligans = 0
        if mulligans_spent is not None:
            received_mulligans = counts["Mulligan"]
            available_mulligans = max(
                0, min(received_mulligans - mulligans_spent, 0xFF)
            )
            current_mulligans = memory.read_bytes(
                MULLIGAN_REMAINING[0], 1
            )[0]
            previous_mulligans = self.last_mulligan_value
            received_gain = max(
                0, received_mulligans - self.last_mulligan_received
            )

            if previous_mulligans is None or hole_reset:
                target_mulligans = available_mulligans
            elif received_gain:
                target_mulligans = min(
                    available_mulligans,
                    current_mulligans + received_gain,
                )
            elif current_mulligans < previous_mulligans:
                newly_spent_mulligans = min(
                    previous_mulligans - current_mulligans,
                    available_mulligans,
                )
                target_mulligans = current_mulligans
            else:
                target_mulligans = min(
                    current_mulligans, available_mulligans
                )

            if target_mulligans != current_mulligans:
                memory.write_bytes(
                    MULLIGAN_REMAINING[0], bytes((target_mulligans,))
                )
            self.last_mulligan_value = target_mulligans
            self.last_mulligan_received = received_mulligans

        self.last_hole = current_hole
        return newly_spent_mulligans

    def take_club_inventory_notice(self) -> str | None:
        notice = self.club_inventory_notice
        self.club_inventory_notice = None
        return notice

    def take_advance_tour_warning(self) -> str | None:
        """Return each current transfer warning once until the state changes."""

        if self.advance_tour_warning is None:
            self.reported_advance_tour_warning = None
            return None
        if self.advance_tour_warning == self.reported_advance_tour_warning:
            return None
        self.reported_advance_tour_warning = self.advance_tour_warning
        return self.advance_tour_warning

    def enforce_mode_unlocks(self, memory, counts: Counter[str]) -> None:
        """Leave the disproven legacy mode field untouched.

        The July full-RAM captures show unrelated values at MODE_SELECTOR on
        every paired setup screen, including identical values for an allowed
        and a locked entry. Writing the old signatures can corrupt live state.
        The client still publishes compact protocol permissions for the
        replacement native guard. The two disproven 0.9.4 widget patches were
        removed, so no mode is natively denied until the real confirmation
        path is mapped; desktop writes here must remain disabled.
        """

        return

    def completed_live_accomplishments(
        self,
        memory,
        received_names: list[str] | tuple[str, ...] = (),
        congo_canopy_score_to_par: int = 0,
        selected_course_index: int | None = None,
        selected_course_is_star: bool | None = None,
        native_selected_mode: int | None = None,
        confirmed_round_golfer: str | None = None,
    ) -> set[str]:
        results = live_result_values(memory)
        scoring_results = tuple(
            value
            for value in results
            if 0x01 <= value <= 0x0F
            or value in (0x18, 0x19, 0x1A, 0x29)
        )
        # Prefer the actual hole score when the companion slot carries a
        # transient Chip-In/Hit-the-Pin message. This counts the hole once
        # while still reporting every distinct accomplishment below.
        result = (
            scoring_results[0]
            if scoring_results
            else results[0]
            if results
            else 0xFFFFFFFF
        )
        completed = self._completed_shot_accomplishments(
            memory,
            result,
            Counter(received_names),
            native_selected_mode=native_selected_mode,
        )
        live_text = memory.read_bytes(LIVE_UI_TEXT, LIVE_UI_TEXT_SIZE)
        current_hole = memory.read_bytes(CURRENT_HOLE, 1)[0]
        speed_golf_active = (
            self.verified_gameplay_active
            and (
                native_selected_mode == NATIVE_MENU_MODE_IDS["Speed Golf"]
                or SPEED_GOLF_SIGNATURE in live_text
            )
        )
        if speed_golf_active:
            live_frames = int.from_bytes(
                memory.read_bytes(SPEED_GOLF_LIVE_HOLE_FRAMES, 4), "big"
            )
            result_state = int.from_bytes(
                memory.read_bytes(SPEED_GOLF_RESULT_STATE, 4), "big"
            )
            # Retail clears the counter to zero/FFFFFFFF on result/menu
            # screens. Preserve the last live verdict until the score edge.
            if 0 < live_frames < 0x7FFFFFFF:
                if self.speed_golf_candidate_hole != current_hole:
                    # Speed Golf's full-round route begins at native hole 0.
                    # Reset the client accumulator there rather than relying
                    # on ordinary golf score messages, which the captured
                    # Speed Golf scoreboard does not publish.
                    if current_hole == 0:
                        self.speed_golf_round_frames = 0
                        self.speed_golf_round_timed_holes = 0
                        self.speed_golf_round_course = None
                        self.speed_golf_last_settled_hole = None
                    self.speed_golf_candidate_hole = current_hole
                    self.speed_golf_candidate_frames = None
                # Polling can observe the counter more than once. Retain the
                # greatest live value for this hole so the full-round timer is
                # the sum of eighteen final per-hole counters rather than the
                # first value seen after each tee transition. The live counter
                # can briefly expose smaller transition values, so it is not
                # authoritative for the individual under-15-second check.
                # That check is read from retail's completed-round centisecond
                # table in completed_speed_golf().
                self.speed_golf_candidate_frames = max(
                    self.speed_golf_candidate_frames or 0,
                    live_frames,
                )
                self.speed_golf_result_screen_visible = False
            result_screen_visible = (
                live_frames == 0 and 0 < result_state < 0xFF
            )
            if (
                result_screen_visible
                and not self.speed_golf_result_screen_visible
                and self.speed_golf_candidate_hole == current_hole
            ):
                candidate_frames = self.speed_golf_candidate_frames
                if (
                    candidate_frames is not None
                    and self.speed_golf_last_settled_hole != current_hole
                ):
                    self.speed_golf_round_frames += candidate_frames
                    self.speed_golf_round_timed_holes += 1
                    self.speed_golf_last_settled_hole = current_hole
                    if (
                        self.speed_golf_round_course is None
                        and selected_course_index is not None
                        and 0 <= selected_course_index < len(COURSES)
                    ):
                        self.speed_golf_round_course = selected_course_index
                    if (
                        current_hole == SPEED_GOLF_HOLES - 1
                        and self.speed_golf_round_timed_holes
                        == SPEED_GOLF_HOLES
                        and int.from_bytes(
                            memory.read_bytes(
                                SPEED_GOLF_FINAL_SCORE_TO_PAR, 4
                            ),
                            "big",
                            signed=True,
                        )
                        < 0
                    ):
                        # Pair the score verdict with retail's authoritative
                        # completed-round centisecond table below. The sampled
                        # live timer can expose transition values and must not
                        # decide either full-round time check.
                        self.speed_golf_under_par_pending = True
                # Retire the candidate at the captured scoreboard edge.  The
                # ordinary scoring-message path remains as a fallback for
                # screens that publish a birdie/par result first.
                self.speed_golf_candidate_hole = None
                self.speed_golf_candidate_frames = None
            self.speed_golf_result_screen_visible = result_screen_visible
        else:
            self.speed_golf_result_screen_visible = False
        active_result_object = int.from_bytes(
            memory.read_bytes(ACTIVE_PLAYER_OBJECT_POINTER, 4), "big"
        )
        active_result_offset = active_result_object - PLAYER_ONE_LIVE_OBJECT
        active_result_player_index = (
            active_result_offset // CLUB_LIMITER_PLAYER_STRIDE
            if (
                active_result_offset >= 0
                and active_result_offset % CLUB_LIMITER_PLAYER_STRIDE == 0
                and active_result_offset // CLUB_LIMITER_PLAYER_STRIDE < 4
            )
            else None
        )
        # Character Match can advance the active-player pointer to the next
        # turn before a native result popup becomes visible. The CPU's Hit the
        # Pin message was therefore attributed to P1 when the pointer had
        # already wrapped back to the human. Prefer the player captured while
        # the shot was moving/settling; use the live result pointer only when
        # no shot ownership evidence was observed.
        result_shot_player_index = (
            self.shot_live_player_index
            if self.shot_live_player_index is not None
            else self.last_completed_shot_player_index
            if self.last_completed_shot_player_index is not None
            else active_result_player_index
        )
        ap_result_owned = not (
            native_selected_mode == NATIVE_MENU_MODE_IDS["Character Match"]
            and result_shot_player_index not in (None, 0)
        )
        if ap_result_owned:
            for value in results:
                location = RESULT_LOCATION_BY_VALUE.get(value)
                if location is not None:
                    completed.add(location)
        if ap_result_owned and 0x11 in results and self.last_ball_lie == 3:
            completed.add("Accomplishment - Chip In from a Bunker")

        # 0xFFFFFFFF is the retail idle value. Capture the lie before a result
        # replaces the active-shot message so a subsequent chip-in can identify
        # an ordinary sand-bunker origin.
        if not results:
            self.last_ball_lie = int.from_bytes(
                memory.read_bytes(BALL_LIE_PRIMARY, 4), "big"
            )

        # The result value remains visible for many bridge polls. Count only
        # the edge into a new scoring message so one birdie cannot become an
        # entire streak. Retail score messages 0x01..0x0F cover albatross
        # through the over-par results.
        result_edge = result != self.last_result_message
        ap_result_edge = result_edge and ap_result_owned
        # Tournament's capture-proven victory edge is 0x29. Attribute the
        # course and golfer from the native confirmation trace rather than
        # relying exclusively on retail's split golfer-result rows. This is
        # valid for every native golfer, including hidden unlockables whose
        # persistent result rows do not follow the ordinary +14 mapping.
        if (
            ap_result_edge
            and result == 0x29
            and native_selected_mode == NATIVE_MENU_MODE_IDS["Tournament"]
            and selected_course_index is not None
            and 0 <= selected_course_index < len(REGULAR_TOURNAMENTS)
        ):
            tournament_index = selected_course_index
            if selected_course_is_star:
                tournament_index += len(REGULAR_TOURNAMENTS)
            completed.add(TOURNAMENT_WIN_LOCATIONS[tournament_index])
            # First place necessarily satisfies both new placement checks.
            # Report these at the captured victory edge rather than waiting
            # for the result table to be committed during save/exit.
            completed.add(TOURNAMENT_TOP_THREE_LOCATIONS[tournament_index])
            completed.add(TOURNAMENT_FINISH_LOCATION)
            # The roster trace is useful at selection time but can be stale by
            # the final scoreboard. Prefer the golfer latched for this round.
            # This also keeps hidden golfers such as Shadow Mario out of the
            # ambiguous retail result-row mapping used below for course wins.
            winning_golfer = (
                self.last_confirmed_round_golfer
                if self.last_confirmed_round_golfer in CHARACTERS
                else confirmed_round_golfer
                if confirmed_round_golfer in CHARACTERS
                else self.active_native_golfer
            )
            if winning_golfer in CHARACTERS:
                completed.add(
                    f"Character Tournament Win - {winning_golfer}"
                )
            # A Tournament victory is necessarily the end of its full round.
            # Use the final scoreboard value directly here so missed/combined
            # per-hole result messages cannot suppress the score locations.
            final_score_to_par = int.from_bytes(
                memory.read_bytes(SPEED_GOLF_FINAL_SCORE_TO_PAR, 4),
                "big",
                signed=True,
            )
            if -100 <= final_score_to_par < 0:
                completed.add(
                    f"Under Par Round - {COURSES[selected_course_index]}"
                )
            if -100 <= final_score_to_par <= -10:
                completed.add("Accomplishment - Shoot 10 Under Par in a Round")
            if (
                -100 <= final_score_to_par <= GOLFER_ROUND_SCORE_TARGET
                and winning_golfer in CHARACTERS
            ):
                completed.add(golfer_round_score_location(winning_golfer))
        if ap_result_edge and 0x01 <= result <= 0x0F:
            if result == 0x04:
                self.consecutive_birdies += 1
                if self.consecutive_birdies >= 5:
                    completed.add(
                        "Accomplishment - Make 5 Consecutive Birdies"
                    )
            else:
                self.consecutive_birdies = 0

        # Hole score messages are edge-triggered and provide enough information
        # for round-wide bogey-free/under-par accomplishments without modifying
        # retail save data.
        score_by_result = {
            0x02: -3,
            0x03: -2,
            0x04: -1,
            0x05: 0,
            0x06: 1,
            0x07: 2,
            0x08: 3,
            0x09: 4,
            0x0A: 5,
            0x0B: 6,
            0x0C: 7,
            0x0D: 8,
            0x0E: 9,
            0x0F: 10,
            0x18: 2,
            0x19: 3,
        }
        if ap_result_edge and result == 0x01:
            par = memory.read_bytes(CURRENT_PAR, 1)[0]
            score_delta = 1 - par if 3 <= par <= 5 else -2
        else:
            score_delta = (
                score_by_result.get(result) if ap_result_edge else None
            )
        if score_delta is not None:
            scored_hole = current_hole
            # Result dialogs briefly reuse/clear the selected-golfer UI state.
            # The August 14 Shifting Sands capture consequently reported the
            # exact Petey Best Badge while dropping Petey's per-golfer birdie
            # location.  The native roster-confirmation trace remains latched
            # for the whole round, so prefer it for native golfers at the
            # scoring edge. Advance Tour identity is still authoritative for
            # Neil/Ella because they do not use the native roster IDs.
            active_golfer = self.active_advance_tour_golfer
            if active_golfer is None:
                active_golfer = (
                    confirmed_round_golfer
                    if confirmed_round_golfer in CHARACTERS
                    else self.active_native_golfer
                )
            if (
                self.speed_golf_candidate_hole == scored_hole
                and self.speed_golf_candidate_frames is not None
            ):
                if self.round_holes == 0:
                    self.speed_golf_round_frames = 0
                    self.speed_golf_round_timed_holes = 0
                    self.speed_golf_round_course = None
                self.speed_golf_round_frames += self.speed_golf_candidate_frames
                self.speed_golf_round_timed_holes += 1
                if (
                    self.speed_golf_round_course is None
                    and selected_course_index is not None
                    and 0 <= selected_course_index < len(COURSES)
                ):
                    self.speed_golf_round_course = selected_course_index
            self.speed_golf_candidate_hole = None
            self.speed_golf_candidate_frames = None
            if self.round_holes == 0:
                self.round_first_hole = scored_hole
                self.round_golfer = active_golfer
                self.round_golfer_consistent = active_golfer is not None
                self.round_par_type_seen.clear()
                self.round_par_type_all_birdie = {3: True, 4: True, 5: True}
            elif active_golfer != self.round_golfer:
                self.round_golfer_consistent = False

            par = memory.read_bytes(CURRENT_PAR, 1)[0]
            if par in self.round_par_type_all_birdie:
                self.round_par_type_seen.add(par)
                if score_delta > -1:
                    self.round_par_type_all_birdie[par] = False

            live_text = memory.read_bytes(LIVE_UI_TEXT, LIVE_UI_TEXT_SIZE)
            # The mode-confirmation hook remains latched for the entire round,
            # whereas the UI text arena is routinely replaced by lie/result
            # prose before the scoring edge reaches the desktop client.  The
            # August 13 Star Petey capture had an authoritative Stroke Play
            # latch but no uppercase STROKE PLAY string and consequently lost
            # both the golfer Birdie-or-Better and individual Best Badge. Use
            # the native latch first and retain text only for older patches and
            # direct callers that do not publish a native mode.
            standard_scoring_hole = native_selected_mode in (
                NATIVE_MENU_MODE_IDS["Tournament"],
                NATIVE_MENU_MODE_IDS["Stroke Play"],
            ) or (
                native_selected_mode is None
                and (
                    STROKE_PLAY_SIGNATURE in live_text
                    or TOURNAMENT_SIGNATURE in live_text
                )
            )
            if (
                standard_scoring_hole
                and score_delta <= -1
                and active_golfer in PER_CHARACTER_GOLFERS
            ):
                completed.add(golfer_birdie_location(active_golfer))
            # The assumed persistent Best Badge table has never survived a
            # known-course/known-hole controller comparison. The live scoring
            # edge already supplies authoritative course, hole, and score data,
            # so report the individual badge here and let the AP server make it
            # durable. Tournament names map to their physical course names.
            if (
                standard_scoring_hole
                and score_delta <= -1
                and selected_course_index is not None
                and 0 <= selected_course_index < len(COURSES)
                and 0 <= scored_hole < 18
            ):
                completed.add(
                    BEST_BADGE_HOLE_LOCATIONS[
                        selected_course_index * 18 + scored_hole
                    ]
                )
            self.round_holes += 1
            self.round_score_to_par += score_delta
            self.round_had_bogey |= score_delta > 0
            self.last_hole_score_result = result
            self.last_scored_hole = scored_hole
            if self.active_advance_tour_golfer is not None:
                golfer = self.active_advance_tour_golfer
                self.advance_tour_holes_completed[golfer] += 1
                completed.update(
                    advance_tour_hole_location(golfer, threshold)
                    for threshold in ADVANCE_TOUR_HOLE_THRESHOLDS
                    if self.advance_tour_holes_completed[golfer] >= threshold
                )

        live_text = memory.read_bytes(LIVE_UI_TEXT, LIVE_UI_TEXT_SIZE)
        standard_scoring_round = native_selected_mode in (
            NATIVE_MENU_MODE_IDS["Tournament"],
            NATIVE_MENU_MODE_IDS["Stroke Play"],
        ) or (
            native_selected_mode is None
            and (
                STROKE_PLAY_SIGNATURE in live_text
                or TOURNAMENT_SIGNATURE in live_text
            )
        )
        # The August 15 Boo tournament capture proves the final scoreboard can
        # leave both generic result-message words at 0xFFFFFFFF; consequently
        # the old result==0x1A-only settlement never ran. The same captured
        # scoreboard state used by Speed Golf publishes the authoritative
        # signed final score-to-par at 0x805240D0. Wait until all eighteen hole
        # edges have been accumulated, then accept this screen as an alternate
        # round settlement without depending on a transient message.
        standard_round_scoreboard_visible = (
            self.verified_gameplay_active
            and standard_scoring_round
            and current_hole == 17
            and int.from_bytes(
                memory.read_bytes(SPEED_GOLF_LIVE_HOLE_FRAMES, 4), "big"
            )
            == 0
            and 0
            < int.from_bytes(
                memory.read_bytes(SPEED_GOLF_RESULT_STATE, 4), "big"
            )
            < 0xFF
        )
        if not standard_round_scoreboard_visible:
            self.standard_round_scoreboard_reported = False
        scoreboard_round_settlement = (
            standard_round_scoreboard_visible
            and not self.standard_round_scoreboard_reported
            and self.round_holes == 18
        )
        if scoreboard_round_settlement:
            self.standard_round_scoreboard_reported = True

        if (ap_result_edge and result == 0x1A) or scoreboard_round_settlement:
            speed_golf_round = (
                native_selected_mode == NATIVE_MENU_MODE_IDS["Speed Golf"]
                or (
                    native_selected_mode is None
                    and SPEED_GOLF_SIGNATURE in live_text
                )
            )
            settled_score_to_par = self.round_score_to_par
            captured_score_to_par = int.from_bytes(
                memory.read_bytes(SPEED_GOLF_FINAL_SCORE_TO_PAR, 4),
                "big",
                signed=True,
            )
            if (
                -100 <= captured_score_to_par <= 100
                and (
                    scoreboard_round_settlement
                    or current_hole in (8, 17)
                )
            ):
                settled_score_to_par = captured_score_to_par
            if (
                self.round_holes == 9
                and self.round_first_hole == 0
                and self.round_score_to_par <= congo_canopy_score_to_par
                and b"Congo Canopy" in live_text
                and STROKE_PLAY_SIGNATURE in live_text
            ):
                completed.add(congo_canopy_score_location("Front 9"))
            if (
                self.round_holes >= 9
                and self.round_score_to_par < 0
                and speed_golf_round
            ):
                self.speed_golf_under_par_pending = True
            if self.round_holes >= 9 and not self.round_had_bogey:
                completed.add("Accomplishment - Complete a Bogey-Free Round")
            if self.round_holes >= 9 and settled_score_to_par <= -10:
                completed.add("Accomplishment - Shoot 10 Under Par in a Round")
            memory_course = int.from_bytes(
                memory.read_bytes(CURRENT_COURSE, 4), "big"
            )
            course = (
                selected_course_index
                if selected_course_index is not None
                and 0 <= selected_course_index < len(COURSES)
                else memory_course
            )
            if (
                standard_scoring_round
                and self.round_holes == 18
                and self.round_golfer_consistent
                and self.round_golfer in PER_CHARACTER_GOLFERS
                and settled_score_to_par <= GOLFER_ROUND_SCORE_TARGET
            ):
                completed.add(
                    golfer_round_score_location(self.round_golfer)
                )
            if (
                standard_scoring_round
                and self.round_holes == 18
                and 0 <= course < len(COURSES)
            ):
                for par in (3, 4, 5):
                    if (
                        par in self.round_par_type_seen
                        and self.round_par_type_all_birdie[par]
                    ):
                        completed.add(
                            course_par_sweep_location(COURSES[course], par)
                        )
            completed_round_length = (
                self.round_holes >= 9 or current_hole in (8, 17)
            )
            if (
                completed_round_length
                and settled_score_to_par < 0
                and 0 <= course < len(COURSES)
            ):
                completed.add(f"Under Par Round - {COURSES[course]}")
            self.round_holes = 0
            self.round_score_to_par = 0
            self.round_had_bogey = False
            self.round_first_hole = None
            self.round_golfer = None
            self.round_golfer_consistent = True
            self.round_par_type_seen.clear()
            self.round_par_type_all_birdie = {3: True, 4: True, 5: True}
            self.speed_golf_round_frames = 0
            self.speed_golf_round_timed_holes = 0
            self.speed_golf_round_course = None

        # Do not derive course-specific or margin checks from the former mode
        # and course fields. The uploaded full-RAM captures prove both legacy
        # addresses are unrelated live state. Character Match star checks use
        # the verified result table plus a 0x29 win edge; granular checks wait
        # for a paired victory capture.
        self.last_result_message = result
        return completed

    def completed_coin_shoot(self, memory) -> set[str]:
        """Return live Coin Attack feats and one settled round-total credit."""

        # The course label is visible before the Coin result panel replaces
        # it. Retain that identity across the transition instead of reading the
        # disproven legacy course field.
        course_text = memory.read_bytes(
            PRIMARY_COURSE_TEXT, PRIMARY_COURSE_TEXT_SIZE
        )
        for course in COURSES:
            if course.encode("ascii") in course_text:
                self.active_coin_course = course
                break

        result_text = memory.read_bytes(
            COIN_RESULT_TEXT, COIN_RESULT_TEXT_SIZE
        )
        active_variant = next(
            (
                variant
                for variant, signature in COIN_RESULT_SIGNATURES
                if signature in result_text
            ),
            None,
        )
        gameplay_active = int.from_bytes(
            memory.read_bytes(GAMEPLAY_MARKER, 4), "big"
        ) == GAMEPLAY_MARKER_ACTIVE
        coins = int.from_bytes(memory.read_bytes(COIN_HOLE_COUNT, 4), "big")
        if (
            gameplay_active
            and active_variant is not None
            and self.active_native_golfer in CHARACTERS
        ):
            self.coin_session_active = True
            self.coin_session_variant = active_variant
            self.coin_session_character = self.active_native_golfer
        elif self.coin_session_active and not gameplay_active:
            round_total = int.from_bytes(
                memory.read_bytes(COIN_ROUND_TOTAL, 4), "big"
            )
            if (
                self.coin_session_variant in COIN_ATTACK_VARIANTS
                and self.coin_session_character in CHARACTERS
                and round_total > 0
            ):
                self.pending_coin_credit = (
                    self.coin_session_variant,
                    self.coin_session_character,
                    round_total,
                )
            self.coin_session_active = False
            self.coin_session_variant = None
            self.coin_session_character = None

        # Coin Attack's title is not continuously present during every hole.
        # Once a session is armed, retain its verified variant and keep its
        # golfer aligned with the native P1 identity corrected above. This is
        # especially important after Continue, where an earlier poll may have
        # briefly inherited the character-select highlight.
        if (
            gameplay_active
            and self.coin_session_active
            and self.active_native_golfer in CHARACTERS
        ):
            self.coin_session_character = self.active_native_golfer
        effective_variant = active_variant
        if effective_variant is None and self.coin_session_active:
            effective_variant = self.coin_session_variant

        completed: set[str] = set()
        if gameplay_active and effective_variant is not None and coins >= 100:
            completed.add(COIN_100_GLOBAL_LOCATION)
            if self.active_coin_course is not None:
                completed.add(
                    coin_course_location(
                        "Collect 100 Coins on One Hole",
                        self.active_coin_course,
                    )
                )
        current_hole = memory.read_bytes(CURRENT_HOLE, 1)[0]
        if (
            gameplay_active
            and effective_variant is not None
            and coins >= 75
            and self.last_hole_score_result == 0x04
            and self.last_scored_hole == current_hole
        ):
            completed.add(COIN_BIRDIE_75_GLOBAL_LOCATION)
            if self.active_coin_course is not None:
                completed.add(
                    coin_course_location(
                        "Make a Birdie While Collecting 75 Coins",
                        self.active_coin_course,
                    )
                )
        return completed

    def take_coin_credit(self) -> tuple[str, str, int] | None:
        """Return the newest settled Coin Attack result exactly once."""

        credit = self.pending_coin_credit
        self.pending_coin_credit = None
        return credit

    def completed_special_modes(self, memory) -> set[str]:
        """Return capture-verified code/special-mode clear checks.

        The active-session booleans deliberately fail closed if the bridge is
        attached only after reaching Results. This avoids confusing an
        ordinary clear screen with either special mode.
        """

        text = memory.read_bytes(LIVE_UI_TEXT, LIVE_UI_TEXT_SIZE)
        hole_in_one_text = memory.read_bytes(
            HOLE_IN_ONE_SESSION_TEXT, HOLE_IN_ONE_SESSION_TEXT_SIZE
        )
        is_clear_result = (
            CLEAR_SIGNATURE in text
            and RESULTS_PASSWORD_SIGNATURE in text
        )
        if not is_clear_result:
            if (
                not self.hole_in_one_contest_reported
                and HOLE_IN_ONE_CONTEST_SIGNATURE in hole_in_one_text
            ):
                self.hole_in_one_contest_active = True
            if (
                not self.bowsers_big_blast_reported
                and BOWSERS_BIG_BLAST_SIGNATURE in text
            ):
                self.bowsers_big_blast_active = True
            self.special_clear_visible = False
            return set()
        if self.special_clear_visible:
            return set()
        self.special_clear_visible = True

        completed: set[str] = set()
        if is_clear_result and self.hole_in_one_contest_active:
            completed.add(HOLE_IN_ONE_CONTEST_LOCATION)
            self.hole_in_one_contest_active = False
            self.hole_in_one_contest_reported = True
        if (
            is_clear_result
            and self.bowsers_big_blast_active
            and STROKE_PLAY_SIGNATURE in text
        ):
            completed.add(BOWSERS_BIG_BLAST_LOCATION)
            self.bowsers_big_blast_active = False
            self.bowsers_big_blast_reported = True
        return completed

    @staticmethod
    def _horizontal_distance(
        start: tuple[float, float, float],
        end: tuple[float, float, float],
    ) -> float:
        return math.hypot(end[0] - start[0], end[2] - start[2])

    def _completed_shot_accomplishments(
        self,
        memory,
        result: int,
        counts: Counter[str],
        *,
        native_selected_mode: int | None = None,
    ) -> set[str]:
        """Track P1 shot travel for feats that retail does not persist.

        Captured controller distances show that horizontal coordinates use
        feet, not yards. A shot begins on the first movement away
        from the stable address and ends after two stationary bridge polls.
        The launch club, lie, shot type, and Power Shot count are captured
        before retail changes the selection HUD.
        """

        completed: set[str] = set()
        if self.perfect_power_refund_observed:
            completed.add("Accomplishment - Execute a Perfect Power Shot")
            self.perfect_power_refund_observed = False
        if self.gameplay_marker_observed and not self.verified_gameplay_active:
            # Shared coordinates and lie values are repopulated while courses
            # and menus load. Never seed a shot origin from those teleports.
            self.last_ball_position = None
            self.aim_ball_lie = None
            self.shot_origin = None
            self.shot_club = None
            self.shot_type = None
            self.shot_lie = None
            self.shot_course = None
            self.shot_hole = None
            self.shot_power_was_consumed = False
            self.shot_live_player_index = None
            self.last_completed_shot_player_index = None
            self.shot_max_distance = 0.0
            self.shot_stationary_polls = 0
            return completed

        raw = memory.read_bytes(BALL_COORDINATES, 12)
        position = struct.unpack(">fff", raw)
        if not all(math.isfinite(value) and abs(value) < 1_000_000 for value in position):
            return completed

        current_power = memory.read_bytes(POWER_SHOT_REMAINING[0], 1)[0]
        if self.last_ball_position is None:
            self.last_ball_position = position
            self.aim_power_remaining = current_power
            self.aim_ball_lie = int.from_bytes(
                memory.read_bytes(BALL_LIE_PRIMARY, 4), "big"
            )
            return completed

        frame_motion = self._horizontal_distance(self.last_ball_position, position)
        vertical_motion = abs(self.last_ball_position[1] - position[1])
        moved = frame_motion > 0.05 or vertical_motion > 0.05

        if self.shot_origin is None:
            origin_is_loaded = any(abs(value) > 0.01 for value in self.last_ball_position)
            if (
                moved
                and origin_is_loaded
                and result == 0xFFFFFFFF
                and self.last_result_message == 0xFFFFFFFF
            ):
                self.shot_origin = self.last_ball_position
                self.shot_club = int.from_bytes(
                    memory.read_bytes(CURRENT_CLUB, 4), "big"
                )
                self.shot_type = int.from_bytes(
                    memory.read_bytes(CURRENT_SHOT_TYPE, 4), "big"
                )
                current_lie = int.from_bytes(
                    memory.read_bytes(BALL_LIE_PRIMARY, 4), "big"
                )
                # Retail can replace the tee lie as soon as the ball begins
                # moving, before the desktop client observes that first
                # coordinate delta. Preserve the last stable aiming lie.
                self.shot_lie = (
                    self.aim_ball_lie
                    if self.aim_ball_lie is not None
                    else current_lie
                )
                self.shot_course = int.from_bytes(
                    memory.read_bytes(CURRENT_COURSE, 4), "big"
                )
                self.shot_hole = memory.read_bytes(CURRENT_HOLE, 1)[0]
                self.shot_power_before = self.aim_power_remaining
                live_player_object = int.from_bytes(
                    memory.read_bytes(ACTIVE_PLAYER_OBJECT_POINTER, 4), "big"
                )
                live_player_offset = (
                    live_player_object - PLAYER_ONE_LIVE_OBJECT
                )
                self.shot_live_player_index = (
                    live_player_offset // CLUB_LIMITER_PLAYER_STRIDE
                    if (
                        live_player_offset >= 0
                        and live_player_offset % CLUB_LIMITER_PLAYER_STRIDE == 0
                        and live_player_offset // CLUB_LIMITER_PLAYER_STRIDE < 4
                    )
                    else None
                )
                self.shot_power_was_consumed = (
                    self.shot_type == POWER_SHOT_TYPE
                    and current_power < self.shot_power_before
                )
                self.shot_max_distance = self._horizontal_distance(
                    self.shot_origin, position
                )
                self.shot_stationary_polls = 0
            elif not moved:
                # Retail may provisionally decrement a selected Power Shot
                # before the first observable ball movement. Preserve the
                # greatest stable count seen while aiming so a miss is judged
                # against the real pre-shot value (9 -> 8), not against the
                # already-decremented value (8 -> 8). A perfect shot's public
                # rule is simply that the final count remains unchanged.
                if int.from_bytes(
                    memory.read_bytes(CURRENT_SHOT_TYPE, 4), "big"
                ) == POWER_SHOT_TYPE:
                    self.aim_power_remaining = max(
                        self.aim_power_remaining,
                        current_power,
                    )
                else:
                    self.aim_power_remaining = current_power
                self.aim_ball_lie = int.from_bytes(
                    memory.read_bytes(BALL_LIE_PRIMARY, 4), "big"
                )
        else:
            current_course = int.from_bytes(
                memory.read_bytes(CURRENT_COURSE, 4), "big"
            )
            current_hole = memory.read_bytes(CURRENT_HOLE, 1)[0]
            if (
                current_course != self.shot_course
                or current_hole != self.shot_hole
            ):
                # Loading a new course/hole can teleport the shared ball
                # coordinates hundreds of yards. Never interpret that load as
                # a completed shot.
                self.shot_origin = None
                self.shot_club = None
                self.shot_type = None
                self.shot_lie = None
                self.shot_course = None
                self.shot_hole = None
                self.shot_power_before = current_power
                self.shot_power_was_consumed = False
                self.shot_live_player_index = None
                self.last_completed_shot_player_index = None
                self.shot_max_distance = 0.0
                self.shot_stationary_polls = 0
                self.aim_power_remaining = current_power
                self.aim_ball_lie = int.from_bytes(
                    memory.read_bytes(BALL_LIE_PRIMARY, 4), "big"
                )
                self.last_ball_position = position
                return completed
            self.shot_max_distance = max(
                self.shot_max_distance,
                self._horizontal_distance(self.shot_origin, position),
            )
            if moved:
                self.shot_stationary_polls = 0
            else:
                self.shot_stationary_polls += 1

            if (
                self.shot_type == POWER_SHOT_TYPE
                and current_power < self.shot_power_before
            ):
                self.shot_power_was_consumed = True

            result_edge = result != self.last_result_message
            shot_owned_by_ap_player = not (
                native_selected_mode
                == NATIVE_MENU_MODE_IDS["Character Match"]
                and self.shot_live_player_index not in (None, 0)
            )
            hole_out = result_edge and shot_owned_by_ap_player and (
                result == 0x11
                or 0x01 <= result <= 0x0F
                or result in (0x18, 0x19)
            )
            if hole_out:
                if (
                    self.shot_club == PUTTER_CLUB_INDEX
                    and self.shot_max_distance >= 50.0
                ):
                    completed.add(
                        "Accomplishment - Sink a Putt from 50 Feet or More"
                    )
                if self.shot_club == PUTTER_CLUB_INDEX:
                    # These are general putting accomplishments. They apply in
                    # every mode and do not require Putting Practice access.
                    if self.shot_max_distance >= 10.0:
                        completed.add(
                            "Accomplishment - Sink a Putt from 10 Feet or More"
                        )
                    if self.shot_max_distance >= 25.0:
                        completed.add(
                            "Accomplishment - Sink a Putt from 25 Feet or More"
                        )
                if (
                    self.shot_club != PUTTER_CLUB_INDEX
                    and self.shot_max_distance >= 300.0
                ):
                    completed.add(
                        "Accomplishment - Hole Out from 100 Yards or More"
                    )

            if self.shot_stationary_polls >= 2:
                self.last_completed_shot_distance = self.shot_max_distance
                self.last_completed_shot_lie = self.shot_lie
                self.last_completed_shot_club = self.shot_club
                self.last_completed_shot_player_index = (
                    self.shot_live_player_index
                )
                if (
                    self.shot_club != PUTTER_CLUB_INDEX
                    and self.shot_type == POWER_SHOT_TYPE
                    and self.shot_power_before > 0
                    and self.shot_live_player_index in (None, 0)
                    and current_power == self.shot_power_before
                ):
                    # Player-facing retail behavior is net-based: a perfect
                    # Power Shot leaves the count unchanged, while every miss
                    # costs one. The bridge does not need to observe retail's
                    # optional provisional consume/refund frames as long as
                    # the stable pre-shot baseline and final value match.
                    completed.add(
                        "Accomplishment - Execute a Perfect Power Shot"
                    )
                # Retail normally refunds a perfect Power Shot during flight,
                # but some result sequences publish the +1 only after the
                # ball has settled. Keep the exact expected value and hole for
                # a short window so the capacity synchronizer does not reject
                # that delayed native refund as an unrelated in-round reset.
                if (
                    self.shot_type == POWER_SHOT_TYPE
                    and self.shot_power_before > 0
                    and self.shot_power_was_consumed
                    and self.shot_live_player_index in (None, 0)
                    and current_power < self.shot_power_before
                ):
                    self.pending_power_refund_hole = self.shot_hole
                    self.pending_power_refund_expected = self.shot_power_before
                    self.pending_power_refund_polls = 30
                self.shot_origin = None
                self.shot_club = None
                self.shot_type = None
                self.shot_lie = None
                self.shot_course = None
                self.shot_hole = None
                self.shot_power_before = current_power
                self.shot_power_was_consumed = False
                self.shot_live_player_index = None
                self.shot_max_distance = 0.0
                self.shot_stationary_polls = 0
                self.aim_power_remaining = current_power
                self.aim_ball_lie = int.from_bytes(
                    memory.read_bytes(BALL_LIE_PRIMARY, 4), "big"
                )

        self.last_ball_position = position
        return completed

    def completed_best_badges(self, memory) -> set[str]:
        badges = memory.read_bytes(BEST_BADGE_TABLE, BEST_BADGE_COUNT)
        count = sum(value != 0 for value in badges)
        completed = {
            f"Best Badges - Collect {threshold}"
            for threshold in (10, 25, 50, 75, 100)
            if count >= threshold
        }
        completed.update(
            BEST_BADGE_HOLE_LOCATIONS[index]
            for index, value in enumerate(badges)
            if value != 0
        )
        return completed

    def completed_one_on_one_putt(self, memory) -> set[str]:
        results = memory.read_bytes(
            ONE_ON_ONE_PUTT_RESULTS, ONE_ON_ONE_PUTT_HOLES
        )
        if all(results):
            return {ONE_ON_ONE_PUTT_LOCATION}
        return set()

    def completed_practice_checks(self, memory) -> set[str]:
        """Return only capture-verified persistent practice completions."""

        flags_by_address = {
            address: memory.read_bytes(address, 1)[0]
            for address in PRACTICE_CLEAR_FLAG_ADDRESSES
        }
        completed = {
            location
            for address, flag, location in PRACTICE_CLEAR_FLAG_LOCATIONS
            if flags_by_address[address] & flag
        }
        birdie_progress = memory.read_bytes(
            BIRDIE_CHALLENGE_PROGRESS, 1
        )[0]
        if birdie_progress & BIRDIE_CHALLENGE_FRONT_9_COMPLETE:
            completed.add(birdie_challenge_location("Front 9"))
        return completed

    def completed_live_practice_checks(self, memory) -> set[str]:
        """Return an edge-triggered Practice clear from the native result UI."""

        result_text = memory.read_bytes(
            PRACTICE_RESULT_TEXT, PRACTICE_RESULT_TEXT_SIZE
        )
        hint_text = memory.read_bytes(
            PRACTICE_HINT_TEXT, PRACTICE_HINT_TEXT_SIZE
        )
        is_clear = CLEAR_SIGNATURE in result_text
        if not is_clear:
            self.live_practice_clear_visible = False
            return set()
        if self.live_practice_clear_visible:
            return set()
        # The result box itself usually contains only ``Clear!``. Retail keeps
        # the selected practice description in the adjacent hint buffer; the
        # August 5-6 captures identify each Putting/Approach difficulty there.
        # Read that first so replaying an already-completed retail difficulty
        # still reports its AP location instead of depending on a save bit to
        # transition for a second time.
        location = next(
            (
                hint_location
                for signatures, hint_location in PRACTICE_DIFFICULTY_HINT_LOCATIONS
                if all(signature in hint_text for signature in signatures)
            ),
            None,
        )
        persistent = self.completed_practice_checks(memory)
        if location is None:
            for signature, game in (
                (PUTTING_PRACTICE_RESULT_SIGNATURE, "Putting Practice"),
                (APPROACH_PRACTICE_RESULT_SIGNATURE, "Approach Practice"),
            ):
                if signature not in result_text:
                    continue
                location = next(
                    (
                        practice_clear_location(game, difficulty)
                        for difficulty in ("Novice", "Intermediate", "Expert")
                        if practice_clear_location(game, difficulty)
                        not in persistent
                    ),
                    None,
                )
                break
        if location is None and SHOT_PRACTICE_RESULT_SIGNATURE in result_text:
            location = next(
                (
                    shot_location
                    for signature, shot_location in SHOT_PRACTICE_HINT_LOCATIONS
                    if signature in hint_text
                ),
                None,
            )
        if location is None:
            return set()
        self.live_practice_clear_visible = True
        return {location}

    def completed_speed_golf(self, memory) -> set[str]:
        """Return capture-verified Speed Golf time accomplishments."""

        completed: set[str] = set()
        course_records: list[tuple[int, ...]] = []
        for course_index, location in enumerate(
            SPEED_GOLF_COURSE_LOCATIONS
        ):
            raw = memory.read_bytes(
                SPEED_GOLF_COURSE_RECORDS
                + course_index * SPEED_GOLF_COURSE_RECORD_STRIDE,
                SPEED_GOLF_LEADERBOARD_ENTRIES * 4,
            )
            records = struct.unpack(
                f">{SPEED_GOLF_LEADERBOARD_ENTRIES}I", raw
            )
            course_records.append(records)
            if any(
                0 < value < SPEED_GOLF_COURSE_TARGET_CENTISECONDS
                for value in records
            ):
                completed.add(location)

        raw_holes = memory.read_bytes(
            SPEED_GOLF_LAST_HOLE_TIMES, SPEED_GOLF_HOLES * 2
        )
        hole_times = struct.unpack(f">{SPEED_GOLF_HOLES}H", raw_holes)
        round_total = sum(hole_times)
        round_matches_leaderboard = all(hole_times) and any(
            round_total in records for records in course_records
        )
        if (
            self.speed_golf_under_par_pending
            and round_matches_leaderboard
            and round_total < SPEED_GOLF_UNDER_PAR_TARGET_CENTISECONDS
        ):
            completed.add(SPEED_GOLF_UNDER_PAR_LOCATION)
        # Match the last-round scorecard to a saved Speed Golf leaderboard
        # total before interpreting its halfwords as times. This prevents
        # unrelated modes that reuse nearby save scratch space from granting
        # the global fast-hole check.
        if (
            round_matches_leaderboard
            and any(
                value < SPEED_GOLF_HOLE_TARGET_CENTISECONDS
                for value in hole_times
            )
        ):
            completed.add(SPEED_GOLF_HOLE_LOCATION)
        return completed

    def completed_near_pin(
        self, memory, aggregate_target_feet: int
    ) -> set[str]:
        """Return the configurable aggregate Near-Pin distance check."""

        target_centifeet = aggregate_target_feet * 100
        for round_index in range(NEAR_PIN_ROUND_LENGTHS):
            raw = memory.read_bytes(
                NEAR_PIN_RECORDS
                + round_index * NEAR_PIN_RECORD_STRIDE,
                NEAR_PIN_LEADERBOARD_ENTRIES * 4,
            )
            records = struct.unpack(
                f">{NEAR_PIN_LEADERBOARD_ENTRIES}I", raw
            )
            if any(
                0 < value < NEAR_PIN_UNSET_CENTIFEET
                and value <= target_centifeet
                for value in records
            ):
                return {NEAR_PIN_AGGREGATE_LOCATION}
        return set()

    def completed_ring_shots(
        self,
        memory,
        *,
        max_player_count: int = 1,
        include_multiplayer: bool | None = None,
    ) -> set[str]:
        """Read only the Ring Attack tables enabled by this seed.

        ``include_multiplayer`` remains as a compatibility spelling for older
        callers/tests: true means every 2P--4P table.  New callers pass the
        exact YAML boundary so the default 1P+2P package cannot accidentally
        report an opt-in 3P or 4P clear.
        """

        if include_multiplayer is not None:
            max_player_count = 4 if include_multiplayer else 1
        max_player_count = max(1, min(int(max_player_count), 4))
        table = memory.read_bytes(RING_SHOT_1P_TABLE, RING_SHOT_1P_TABLE_SIZE)
        flags = bytearray(len(COURSES))
        for golfer_index in range(RING_SHOT_1P_GOLFERS):
            row = golfer_index * RING_SHOT_1P_STRIDE
            for course_index in range(len(COURSES)):
                flags[course_index] |= table[row + course_index]
        completed: set[str] = set()
        location_index = 0
        for course_flags in flags:
            for level in range(6):
                if course_flags & (1 << level):
                    completed.add(SINGLE_PLAYER_RING_LOCATIONS[location_index])
                location_index += 1

        if max_player_count >= 2:
            location_index = 0
            for player_index, address in enumerate(
                RING_SHOT_MULTIPLAYER_FLAGS, start=2
            ):
                if player_index > max_player_count:
                    break
                flags = memory.read_bytes(address, len(COURSES))
                for course_flags in flags:
                    for level in range(4):
                        if course_flags & (1 << level):
                            completed.add(
                                MULTIPLAYER_RING_LOCATIONS[location_index]
                            )
                        location_index += 1
        return completed

    def completed_character_matches(
        self,
        memory,
        *,
        native_selected_mode: int | None = None,
        native_mode_confirm_sequence: int | None = None,
        tournament_permissions: int | None = None,
        confirmed_course_index: int | None = None,
    ) -> set[str]:
        """Return durable Pro opponent victories from the retail table.

        Invitation letters and the Star-golfer mask are no longer Archipelago
        progression. Retail's 16-byte Character Match result table is zero on
        a clean card and stores one difficulty bitmask per native opponent.
        Bit 3 is set by a captured Pro victory. These rows back the 1.0
        Pro-difficulty opponent locations; Neil and Ella have no native rows.
        """

        flags = memory.read_bytes(CHARACTER_MATCH_RESULT_FLAGS, len(CHARACTERS))
        completed = {
            character_match_pro_location(character)
            for index, character in enumerate(INTERNAL_GOLFER_ORDER[:len(CHARACTERS)])
            if flags[index] & CHARACTER_MATCH_PRO_BIT
        }
        previous = self.last_character_match_result_flags
        self.last_character_match_result_flags = flags
        newly_completed = (
            previous is not None
            and any(
                current & CHARACTER_MATCH_PRO_BIT
                and not prior & CHARACTER_MATCH_PRO_BIT
                for current, prior in zip(flags, previous)
            )
        )
        # Preserve the optional per-course location on the live rising edge.
        # Static/reused save data can recover opponent checks but cannot safely
        # claim which course produced an old win.
        if (
            newly_completed
            and native_selected_mode == NATIVE_MENU_MODE_IDS["Character Match"]
        ):
            course = confirmed_course_index
            if course is None:
                course = int.from_bytes(
                    memory.read_bytes(CURRENT_COURSE, 4), "big"
                )
            if (
                confirmed_course_index is None
                and tournament_permissions is not None
            ):
                visible_courses = course_menu_map(tournament_permissions)
                course = (
                    visible_courses[course]
                    if 0 <= course < len(visible_courses)
                    else -1
                )
            if 0 <= course < len(CHARACTER_MATCH_COURSE_LOCATIONS):
                completed.add(CHARACTER_MATCH_COURSE_LOCATIONS[course])
        return completed

    def restore_ring_shot_progress(
        self,
        memory,
        checked_names: set[str],
        *,
        max_player_count: int = 1,
        include_multiplayer: bool | None = None,
    ) -> None:
        """Restore native Ring Attack flags from server-authoritative checks."""

        if include_multiplayer is not None:
            max_player_count = 4 if include_multiplayer else 1
        max_player_count = max(1, min(int(max_player_count), 4))

        authoritative = bytearray(len(COURSES))
        for index, location in enumerate(SINGLE_PLAYER_RING_LOCATIONS):
            if location in checked_names:
                authoritative[index // 6] |= 1 << (index % 6)

        # Retain every local clear and publish server-confirmed global progress
        # to every golfer row. Never clear a bit: a newly completed level must
        # remain observable during the poll before its LocationChecks packet is
        # acknowledged by the server.
        one_player = bytearray(
            memory.read_bytes(RING_SHOT_1P_TABLE, RING_SHOT_1P_TABLE_SIZE)
        )
        original = bytes(one_player)
        for golfer_index in range(RING_SHOT_1P_GOLFERS):
            row = golfer_index * RING_SHOT_1P_STRIDE
            for course_index, server_bits in enumerate(authoritative):
                one_player[row + course_index] |= server_bits
        if bytes(one_player) != original:
            memory.write_bytes(RING_SHOT_1P_TABLE, bytes(one_player))

        if max_player_count < 2:
            return
        locations_per_player_count = len(COURSES) * 4
        for player_index, address in enumerate(RING_SHOT_MULTIPLAYER_FLAGS):
            if player_index + 2 > max_player_count:
                break
            flags = bytearray(memory.read_bytes(address, len(COURSES)))
            if len(flags) != len(COURSES):
                continue
            original = bytes(flags)
            start = player_index * locations_per_player_count
            for local_index, location in enumerate(
                MULTIPLAYER_RING_LOCATIONS[
                    start:start + locations_per_player_count
                ]
            ):
                if location in checked_names:
                    flags[local_index // 4] |= 1 << (local_index % 4)
            if bytes(flags) != original:
                memory.write_bytes(address, bytes(flags))

    def completed_tournament_checks(
        self,
        memory,
        *,
        include_character_checks: bool,
        received_names: tuple[str, ...] | list[str] | None = None,
        native_selected_mode: int | None = None,
        confirmed_round_golfer: str | None = None,
    ) -> set[str]:
        tables = [
            bytearray(memory.read_bytes(
                address,
                TOURNAMENT_RESULT_GOLFERS * TOURNAMENT_RESULT_COURSES,
            ))
            for address in TOURNAMENT_RESULT_TABLES
        ]
        previous_tables = self.last_tournament_result_tables
        self.last_tournament_result_tables = tuple(bytes(table) for table in tables)
        completed: set[str] = set()
        received = Counter(received_names) if received_names is not None else None

        def course_is_owned(tournament: str) -> bool:
            if received is None:
                return True
            if received[tournament_access_item(tournament)]:
                return True
            # Compatibility for rooms generated before physical course items
            # began granting both regular and Star Tournament variants.
            return bool(
                tournament in STAR_TOURNAMENTS
                and received[tournament_item(tournament)]
            )

        for table_index, table in enumerate(tables):
            for course in range(TOURNAMENT_RESULT_COURSES):
                if any(
                    table[golfer * TOURNAMENT_RESULT_COURSES + course] == FIRST_PLACE
                    for golfer in range(TOURNAMENT_RESULT_GOLFERS)
                ):
                    tournament_index = (
                        table_index * TOURNAMENT_RESULT_COURSES + course
                    )
                    tournament = (REGULAR_TOURNAMENTS + STAR_TOURNAMENTS)[
                        tournament_index
                    ]
                    if course_is_owned(tournament):
                        completed.add(TOURNAMENT_WIN_LOCATIONS[tournament_index])

        if any(
            table[golfer * TOURNAMENT_RESULT_COURSES + course] == FIRST_PLACE
            and (
                course_is_owned(STAR_TOURNAMENTS[course])
            )
            for table in tables[1:]
            for golfer in range(TOURNAMENT_RESULT_GOLFERS)
            for course in range(TOURNAMENT_RESULT_COURSES)
        ):
            completed.add(STAR_TOURNAMENT_AGGREGATE_LOCATION)

        # Do not infer the golfer from the persistent result row. Retail uses
        # overlapping/nonlinear rows for hidden golfers: a captured Shadow
        # Mario Lakitu win occupied the same row formerly attributed to Yoshi.
        # Instead, detect the persistent table's transition during the active
        # Tournament session and attribute it to the golfer latched at roster
        # confirmation. The live 0x29 result edge remains the primary path;
        # this catches a win when desktop polling misses that short-lived code.
        new_first_place = previous_tables is not None and any(
            current_value == FIRST_PLACE
            and previous_tables[table_index][offset] != FIRST_PLACE
            for table_index, table in enumerate(tables)
            for offset, current_value in enumerate(table)
        )
        winning_golfer = (
            self.last_confirmed_round_golfer
            if self.last_confirmed_round_golfer in CHARACTERS
            else confirmed_round_golfer
            if confirmed_round_golfer in CHARACTERS
            else self.active_native_golfer
        )
        if (
            include_character_checks
            and new_first_place
            and native_selected_mode == NATIVE_MENU_MODE_IDS["Tournament"]
            and winning_golfer in CHARACTERS
        ):
            completed.add(f"Character Tournament Win - {winning_golfer}")
            # This transition can outlive the short 0x29 victory message. The
            # final scoreboard score remains authoritative at the save-table
            # commit, so recover the two score-based locations at the same
            # edge without depending on all eighteen desktop polls.
            final_score_to_par = int.from_bytes(
                memory.read_bytes(SPEED_GOLF_FINAL_SCORE_TO_PAR, 4),
                "big",
                signed=True,
            )
            if -100 <= final_score_to_par <= -10:
                completed.add("Accomplishment - Shoot 10 Under Par in a Round")
            if -100 <= final_score_to_par <= GOLFER_ROUND_SCORE_TARGET:
                completed.add(golfer_round_score_location(winning_golfer))

        return completed

    def completed_tournament_placement_checks(
        self,
        memory,
        *,
        received_names: tuple[str, ...] | list[str] | None = None,
    ) -> set[str]:
        """Return durable tournament completion and Top 3 locations.

        Retail initializes each result entry to 0x80 and stores a one-based
        finishing position after a completed tournament. Any recorded position
        completes the participation check; positions 1 through 3 additionally
        complete that tournament's Top 3 location.
        """

        received = Counter(received_names) if received_names is not None else None

        def course_is_owned(tournament: str) -> bool:
            if received is None:
                return True
            if received[tournament_access_item(tournament)]:
                return True
            # Compatibility with rooms that placed distinct Star course items.
            return bool(
                tournament in STAR_TOURNAMENTS
                and received[tournament_item(tournament)]
            )

        completed: set[str] = set()
        tournaments = REGULAR_TOURNAMENTS + STAR_TOURNAMENTS
        for table_index, address in enumerate(TOURNAMENT_RESULT_TABLES):
            table = memory.read_bytes(
                address,
                TOURNAMENT_RESULT_GOLFERS * TOURNAMENT_RESULT_COURSES,
            )
            for course in range(TOURNAMENT_RESULT_COURSES):
                tournament_index = (
                    table_index * TOURNAMENT_RESULT_COURSES + course
                )
                tournament = tournaments[tournament_index]
                if not course_is_owned(tournament):
                    continue
                recorded = tuple(
                    table[golfer * TOURNAMENT_RESULT_COURSES + course]
                    for golfer in range(TOURNAMENT_RESULT_GOLFERS)
                    if 0
                    < table[golfer * TOURNAMENT_RESULT_COURSES + course]
                    < UNSET_TOURNAMENT_RESULT
                )
                if not recorded:
                    continue
                completed.add(TOURNAMENT_FINISH_LOCATION)
                if min(recorded) <= 3:
                    completed.add(
                        TOURNAMENT_TOP_THREE_LOCATIONS[tournament_index]
                    )
        return completed

    def retail_regular_tournaments_complete(self, memory) -> bool:
        """Return retail's six-regular-tournament completion condition.

        Star Tournament is a retail child of Tournament, inserted at the
        front of the mode menu once every regular course has a first-place
        result. Reading the native table here lets the hook normalize that
        shifted menu immediately after the sixth win and also supports a
        legitimately completed retail test card without fabricating results.
        """

        table = memory.read_bytes(
            TOURNAMENT_RESULT_TABLES[0],
            TOURNAMENT_RESULT_GOLFERS * TOURNAMENT_RESULT_COURSES,
        )
        return all(
            any(
                table[golfer * TOURNAMENT_RESULT_COURSES + course]
                == FIRST_PLACE
                for golfer in range(TOURNAMENT_RESULT_GOLFERS)
            )
            for course in range(TOURNAMENT_RESULT_COURSES)
        )
