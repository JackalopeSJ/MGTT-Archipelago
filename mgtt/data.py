from __future__ import annotations

from dataclasses import dataclass


GAME = "Mario Golf: Toadstool Tour"
ITEM_ID_BASE = 8_617_000
LOCATION_ID_BASE = 8_618_000

BASE_CHARACTERS = (
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
    "Bowser",
    "Birdo",
)

# Their star forms are available as soon as the golfer is unlocked in retail.
SECRET_CHARACTERS = ("Boo", "Bowser Jr.", "Petey Piranha", "Shadow Mario")
CHARACTERS = BASE_CHARACTERS + SECRET_CHARACTERS
ADVANCE_TOUR_GOLFERS = ("Neil", "Ella")
PER_CHARACTER_GOLFERS = CHARACTERS + ADVANCE_TOUR_GOLFERS
STAR_ELIGIBLE_CHARACTERS = BASE_CHARACTERS

REGULAR_TOURNAMENTS = (
    "Lakitu Cup",
    "Cheep Cheep Tournament",
    "Sands Classic",
    "Blooper Open",
    "Peach's Invitational",
    "Bowser Championship",
)

STAR_TOURNAMENTS = (
    "Lakitu Star Cup",
    "Cheep Cheep Star Tournament",
    "Sands Star Classic",
    "Blooper Star Open",
    "Peach's Star Invitational",
    "Bowser Star Championship",
)

COURSES = (
    "Lakitu Valley",
    "Cheep Cheep Falls",
    "Shifting Sands",
    "Blooper Bay",
    "Peach's Castle Grounds",
    "Bowser Badlands",
)

# Modes that new Archipelago rooms may actually place. Doubles and Club Slots
# are native local modes, while "Match Play" and "Skins Match" are not MGTT
# modes at all. Their old numeric slots remain reserved below so updating the
# world never renumbers a published item.
MODES = (
    "Tournament",
    "Character Match",
    "Ring Attack",
    "Speed Golf",
    "Coin Attack",
    "Stroke Play",
    "Near-Pin",
    "Approach Practice",
    "Shot Practice",
    "Birdie Challenge",
)

RANDOMIZABLE_MODES = MODES

# Stable protocol order published before the native menu was capture-mapped.
# The four retired names are intentionally never generated or precollected.
PROTOCOL_MODES = (
    "Tournament",
    "Character Match",
    "Ring Attack",
    "Speed Golf",
    "Doubles",
    "Club Slots",
    "Coin Attack",
    "Stroke Play",
    "Match Play",
    "Skins Match",
    "Near-Pin",
    "Side Games",
)

CLUBS = (
    "1W",
    "3W",
    "4W",
    "3I",
    "4I",
    "5I",
    "6I",
    "7I",
    "8I",
    "9I",
    "PW",
    "AW",
    "SW",
)
WOODS = CLUBS[:3]
IRONS = CLUBS[3:10]
WEDGES = CLUBS[10:]

CUSTOM_CLUB_SETS = (
    "POW",
    "Low-Fly",
    "Straight",
    "Sweet",
    "Control",
    "Backspin",
    "Super Low-Fly",
    "Super Straight",
    "Super Sweet",
    "Super POW",
    "Low-Fly Spin",
    "Straight n' Low",
    "Sweet Control",
    "Risky",
    "Super Spin",
)

ADVANCE_TOUR_GOLFER_ITEM = "Advance Tour Golfers - Neil & Ella"
POWER_SHOT_ITEM = "Power Shot Capacity"
BASE_PUTTER_RANGE_ITEM = "Putter Range - 30 Feet"
SHORT_GAME_ITEMS = (
    "Putter Range - 100 Feet",
    "Putter Range - 200 Feet",
    "Approach Shot",
)
PUTTER_RANGE_ITEMS = (BASE_PUTTER_RANGE_ITEM,) + SHORT_GAME_ITEMS[:2]
PUTTER_RANGE_FEET = (30, 100, 200)
APPROACH_SHOT_ITEM = SHORT_GAME_ITEMS[2]
PUTTING_PRACTICE_MODE_ITEM = "Mode - Putting Practice"
APPROACH_PRACTICE_MODE_ITEM = "Mode - Approach Practice"
SHOT_PRACTICE_MODE_ITEM = "Mode - Shot Practice"
BIRDIE_CHALLENGE_MODE_ITEM = "Mode - Birdie Challenge"
STAR_TOURNAMENT_MODE_ITEM = "Mode - Star Tournament"
PROGRESSIVE_TOURNAMENT_MODE_ITEM = "Tournament and Star Tournament Modes"
LEGACY_PROGRESSIVE_TOURNAMENT_MODE_ITEM = "Progressive Tournament Mode"
PUTTING_PRACTICE_DIFFICULTY_ITEMS = (
    "Putting Practice Difficulty - Novice",
    "Putting Practice Difficulty - Intermediate",
    "Putting Practice Difficulty - Expert",
)
APPROACH_PRACTICE_DIFFICULTY_ITEMS = (
    "Approach Practice Difficulty - Intermediate",
    "Approach Practice Difficulty - Expert",
)
SHOT_PRACTICE_STAGE_ITEMS = (
    "Shot Practice Level - Second Shot",
    "Shot Practice Level - Trouble Shot",
)
BIRDIE_CHALLENGE_STAGE_ITEMS = (
    "Birdie Challenge Level - Back 9",
    "Birdie Challenge Level - All 18",
)
SPIN_TECHNIQUES = (
    "Topspin",
    "Backspin",
    "Super Topspin",
    "Super Backspin",
)
COIN_ATTACK_VARIANTS = ("Quick Cash", "Cash Cup")
# Import compatibility for clients and tools published through v0.9.5.2.6.
COIN_SHOOT_VARIANTS = COIN_ATTACK_VARIANTS
PRACTICE_GAMES = ("Putting Practice", "Approach Practice", "Shot Practice")
PRACTICE_DIFFICULTIES = ("Novice", "Intermediate", "Expert")
SHOT_PRACTICE_STAGES = ("Tee Shot", "Second Shot", "Trouble Shot")
BIRDIE_CHALLENGE_STAGES = ("Front 9", "Back 9", "All 18")
CONGO_CANOPY_ROUNDS = ("Front 9", "Back 9", "All 18")


def progressive_character_item(character: str) -> str:
    if character not in CHARACTERS:
        raise ValueError(f"{character} is not a native golfer")
    return f"Progressive {character} Unlock"


def character_item(character: str) -> str:
    return progressive_character_item(character)


def club_item(club: str) -> str:
    return f"Club - {club}"


def character_club_item(character: str, club: str) -> str:
    if character not in PER_CHARACTER_GOLFERS:
        raise ValueError(f"{character} is not a supported golfer")
    if club not in CLUBS:
        raise ValueError(f"{club} is not a standard club")
    return f"Club - {character} - {club}"


def character_putter_range_item(character: str, feet: int) -> str:
    if character not in PER_CHARACTER_GOLFERS:
        raise ValueError(f"{character} is not a supported golfer")
    if feet not in PUTTER_RANGE_FEET:
        raise ValueError(f"{feet} is not a supported putter range")
    return f"Putter Range - {character} - {feet} Feet"


def custom_club_set_item(club_set: str) -> str:
    return f"Custom Club Set - {club_set}"


def tournament_item(tournament: str) -> str:
    if tournament in REGULAR_TOURNAMENTS:
        return COURSES[REGULAR_TOURNAMENTS.index(tournament)]
    return f"Tournament - {tournament}"


def tournament_access_item(tournament: str) -> str:
    """Return the physical-course item that permits a Tournament entry.

    New 1.0 rooms use one item per physical course for both the regular and
    Star Tournament variants.  ``tournament_item`` remains unchanged so the
    six retired Star-course item names keep their published IDs for older
    rooms.
    """

    if tournament in REGULAR_TOURNAMENTS:
        return tournament_item(tournament)
    if tournament in STAR_TOURNAMENTS:
        return tournament_item(
            REGULAR_TOURNAMENTS[STAR_TOURNAMENTS.index(tournament)]
        )
    raise ValueError(f"Unknown Tournament: {tournament}")


def course_menu_map(tournament_permissions: int) -> tuple[int, ...]:
    """Map compact visible course-menu indices to native course IDs."""

    physical_courses = (
        tournament_permissions | (tournament_permissions >> 6)
    ) & 0x3F
    # Retail keeps Lakitu Valley visible as an unselectable placeholder even
    # when its AP course item is not owned.
    physical_courses |= 0x01
    return tuple(
        index for index in range(6) if physical_courses & (1 << index)
    )


def mode_item(mode: str) -> str:
    if mode == "Coin Shoot":
        mode = "Coin Attack"
    return f"Mode - {mode}"


def spin_item(technique: str, character: str | None = None) -> str:
    if character is None:
        return f"Spin - {technique}"
    return f"Spin - {character} - {technique}"


def ring_shot_location(player_count: int, course: str, level: int) -> str:
    return f"Ring Attack ({player_count}P) - {course} - Level {level}"


def character_match_pro_location(character: str) -> str:
    return f"Character Match - Defeat {character} (Pro Difficulty)"


def tournament_character_location(character: str) -> str:
    return f"Character Tournament Win - {character}"


def best_badge_hole_location(course: str, hole: int) -> str:
    return f"Best Badge - {course} - Hole {hole}"


def coin_character_location(variant: str, character: str) -> str:
    return f"Coin Attack - {variant} - Collect 500 Coins - {character}"


def coin_course_location(feat: str, course: str) -> str:
    return f"Coin Attack - {feat} - {course}"


def practice_clear_location(game: str, difficulty: str) -> str:
    return f"Side Games - Clear {game} - {difficulty}"


def birdie_challenge_location(stage: str) -> str:
    return f"Side Games - Clear Birdie Challenge - {stage}"


def congo_canopy_score_location(round_length: str) -> str:
    return f"Stroke Play - Congo Canopy - {round_length} Score Target"


def golfer_birdie_location(golfer: str) -> str:
    return f"Tournament/Stroke Play - Birdie or Better - {golfer}"


GOLFER_ROUND_SCORE_TARGET = -7


def golfer_round_score_location(golfer: str) -> str:
    return f"Golfer Accomplishment - Shoot 7 Under or Better - {golfer}"


def course_par_sweep_location(course: str, par: int) -> str:
    return (
        f"Course Accomplishment - {course} - "
        f"Birdie or Better on Every Par {par}"
    )


GLOBAL_SPIN_ITEMS = tuple(spin_item(technique) for technique in SPIN_TECHNIQUES)
NATIVE_CHARACTER_SPIN_ITEMS = tuple(
    spin_item(technique, character)
    for character in CHARACTERS
    for technique in SPIN_TECHNIQUES
)
ADVANCE_TOUR_SPIN_ITEMS = tuple(
    spin_item(technique, character)
    for character in ADVANCE_TOUR_GOLFERS
    for technique in SPIN_TECHNIQUES
)
CHARACTER_SPIN_ITEMS = NATIVE_CHARACTER_SPIN_ITEMS + ADVANCE_TOUR_SPIN_ITEMS
PROGRESSIVE_CHARACTER_ITEMS = tuple(
    progressive_character_item(character)
    for character in CHARACTERS
)
NATIVE_CHARACTER_CLUB_ITEMS = tuple(
    character_club_item(character, club)
    for character in CHARACTERS
    for club in CLUBS
)
ADVANCE_TOUR_CHARACTER_CLUB_ITEMS = tuple(
    character_club_item(character, club)
    for character in ADVANCE_TOUR_GOLFERS
    for club in CLUBS
)
CHARACTER_CLUB_ITEMS = (
    NATIVE_CHARACTER_CLUB_ITEMS + ADVANCE_TOUR_CHARACTER_CLUB_ITEMS
)
CHARACTER_PUTTER_RANGE_ITEMS = tuple(
    character_putter_range_item(character, feet)
    for character in PER_CHARACTER_GOLFERS
    for feet in PUTTER_RANGE_FEET
)


@dataclass(frozen=True)
class LocationData:
    region: str
    requires_all: tuple[str, ...] = ()
    requires_any: tuple[str, ...] = ()
    optional_group: str | None = None
    requires_counts: tuple[tuple[str, int], ...] = ()
    required_character: str | None = None
    # At least one counted alternative must be owned. This models gates such
    # as "any Star golfer" without requiring every progressive character to
    # reach its second copy.
    requires_any_counts: tuple[tuple[str, int], ...] = ()
    # Equipment profiles deliberately avoid favoring a particular golfer or
    # exact club. Profiles describe practical readiness; the minimum drives AP
    # logic while the recommendation drives the tracker's HARD/GO distinction.
    minimum_equipment_profile: str = "none"
    recommended_equipment_profile: str = "none"


_NON_CHARACTER_ITEM_NAMES = (
    tuple(club_item(name) for name in CLUBS)
    + tuple(custom_club_set_item(name) for name in CUSTOM_CLUB_SETS)
    + tuple(tournament_item(name) for name in REGULAR_TOURNAMENTS + STAR_TOURNAMENTS)
    + tuple(mode_item(name) for name in PROTOCOL_MODES)
    + (POWER_SHOT_ITEM,)
    + SHORT_GAME_ITEMS
    + GLOBAL_SPIN_ITEMS
    + NATIVE_CHARACTER_SPIN_ITEMS
    + (
        "Mulligan",
        "Power Shot Refill",
        "Nothing",
        "Bogey Trap",
        "Victory",
        ADVANCE_TOUR_GOLFER_ITEM,
    )
)

PROTOCOL_ITEM_NAMES = (
    PROGRESSIVE_CHARACTER_ITEMS
    + _NON_CHARACTER_ITEM_NAMES
    # Append new names so every item ID published through 0.7.4 remains stable.
    + (BASE_PUTTER_RANGE_ITEM, PUTTING_PRACTICE_MODE_ITEM)
    + PUTTING_PRACTICE_DIFFICULTY_ITEMS
)
POST_PROTOCOL_ITEM_NAMES = (
    NATIVE_CHARACTER_CLUB_ITEMS
    + ADVANCE_TOUR_CHARACTER_CLUB_ITEMS
    + ADVANCE_TOUR_SPIN_ITEMS
    # Appended after every previously published item so existing IDs remain
    # stable. Star Tournament is a child entry of Tournament, not a golfer
    # state. This legacy ID is retained for older rooms but new rooms use the
    # single Tournament feature item plus retail's six-win reveal.
    + (STAR_TOURNAMENT_MODE_ITEM,)
    # Per-golfer putter permissions are client-composed into the existing
    # three-bit native mask, so they do not consume legacy protocol count
    # slots. Append them after every item published through 0.9.12.
    + CHARACTER_PUTTER_RANGE_ITEMS
    # Appended for 0.9.26. The former broad Mode - Side Games item keeps its
    # stable legacy ID but is retired from new generation. Each native child
    # now has its own mode item and two higher-level progression items.
    + (
        APPROACH_PRACTICE_MODE_ITEM,
        SHOT_PRACTICE_MODE_ITEM,
        BIRDIE_CHALLENGE_MODE_ITEM,
    )
    + APPROACH_PRACTICE_DIFFICULTY_ITEMS
    + SHOT_PRACTICE_STAGE_ITEMS
    + BIRDIE_CHALLENGE_STAGE_ITEMS
    # Appended for the post-invitation Character Match/Tournament redesign.
    # New 1.0 rooms place one copy for regular Tournament. Star Tournament is
    # revealed by retail after all six regular tournaments have been won; the
    # legacy second copy and mode items retain their published IDs for old
    # rooms, but are not generated as progression in new rooms.
    + (PROGRESSIVE_TOURNAMENT_MODE_ITEM,)
)
ITEM_NAMES = PROTOCOL_ITEM_NAMES + POST_PROTOCOL_ITEM_NAMES

# Preserve every previously published numeric ID after the character range.
# The twelve former base-character IDs now name their progressive replacements;
# the former star-character IDs (offsets 16..27) remain intentionally unused.
_ITEM_ID_OFFSETS = (
    tuple(range(16))
    + tuple(range(28, 163))
    + tuple(range(163, 163 + len(POST_PROTOCOL_ITEM_NAMES)))
)
assert len(ITEM_NAMES) == len(_ITEM_ID_OFFSETS)
ITEM_NAME_TO_ID = {
    name: ITEM_ID_BASE + offset
    for name, offset in zip(ITEM_NAMES, _ITEM_ID_OFFSETS)
}

TOURNAMENT_WIN_LOCATIONS = tuple(
    f"{tournament} - First Place"
    for tournament in REGULAR_TOURNAMENTS + STAR_TOURNAMENTS
)
TOURNAMENT_TOP_THREE_LOCATIONS = tuple(
    f"{tournament} - Top 3 Finish"
    for tournament in REGULAR_TOURNAMENTS + STAR_TOURNAMENTS
)
TOURNAMENT_FINISH_LOCATION = "Tournament - Finish Any Tournament"
STAR_MATCH_LOCATIONS = tuple(
    f"Character Match - Unlock Star {character}"
    for character in CHARACTERS
)
CHARACTER_MATCH_PRO_LOCATIONS = tuple(
    character_match_pro_location(character) for character in CHARACTERS
)
SINGLE_PLAYER_RING_LOCATIONS = tuple(
    ring_shot_location(1, course, level)
    for course in COURSES
    for level in range(1, 7)
)
MULTIPLAYER_RING_LOCATIONS = tuple(
    ring_shot_location(player_count, course, level)
    for player_count in (2, 3, 4)
    for course in COURSES
    for level in range(1, 5)
)
TOURNAMENT_CHARACTER_LOCATIONS = tuple(
    tournament_character_location(character) for character in CHARACTERS
)
CHARACTER_MATCH_COURSE_LOCATIONS = tuple(
    f"Character Match Course Win - {course}" for course in COURSES
)
ONE_ON_ONE_PUTT_LOCATION = "Side Games - Clear One-On One-Putt"
HOLE_IN_ONE_CONTEST_LOCATION = "Side Games - Clear Hole-in-One Contest"
BOWSERS_BIG_BLAST_LOCATION = (
    "Special Tournament - Clear Bowser's Big Blast"
)
COIN_CHARACTER_LOCATIONS = tuple(
    coin_character_location(variant, character)
    for variant in COIN_ATTACK_VARIANTS
    for character in CHARACTERS
)
COIN_100_GLOBAL_LOCATION = "Coin Attack - Collect 100 Coins on One Hole"
COIN_BIRDIE_75_GLOBAL_LOCATION = (
    "Coin Attack - Make a Birdie While Collecting 75 Coins"
)
COIN_COURSE_LOCATIONS = tuple(
    coin_course_location(feat, course)
    for feat in (
        "Collect 100 Coins on One Hole",
        "Make a Birdie While Collecting 75 Coins",
    )
    for course in COURSES
)
COIN_SHOOT_LOCATIONS = (
    COIN_CHARACTER_LOCATIONS
    + (COIN_100_GLOBAL_LOCATION, COIN_BIRDIE_75_GLOBAL_LOCATION)
    + COIN_COURSE_LOCATIONS
)
LEGACY_SPEED_GOLF_COURSE_LOCATIONS = tuple(
    f"Speed Golf - Finish {course} Under 15 Minutes"
    for course in COURSES
)
SPEED_GOLF_COURSE_LOCATIONS = tuple(
    f"Speed Golf - Finish {course} Under 10 Minutes"
    for course in COURSES
)
SPEED_GOLF_HOLE_LOCATION = "Speed Golf - Finish a Hole Under 15 Seconds"
SPEED_GOLF_UNDER_PAR_LOCATION = (
    "Speed Golf - Finish a Round Under 15 Minutes and Under Par"
)
SPEED_GOLF_LOCATIONS = SPEED_GOLF_COURSE_LOCATIONS + (
    SPEED_GOLF_HOLE_LOCATION,
    SPEED_GOLF_UNDER_PAR_LOCATION,
)
PRACTICE_CLEAR_LOCATIONS = tuple(
    practice_clear_location(game, difficulty)
    for game in PRACTICE_GAMES
    for difficulty in PRACTICE_DIFFICULTIES
)
SHOT_PRACTICE_LOCATIONS = tuple(
    practice_clear_location("Shot Practice", stage)
    for stage in SHOT_PRACTICE_STAGES
)
BIRDIE_CHALLENGE_LOCATIONS = tuple(
    birdie_challenge_location(stage) for stage in BIRDIE_CHALLENGE_STAGES
)
PRACTICE_CHALLENGE_LOCATIONS = (
    tuple(
        practice_clear_location(game, difficulty)
        for game in ("Putting Practice", "Approach Practice")
        for difficulty in PRACTICE_DIFFICULTIES
    )
    + SHOT_PRACTICE_LOCATIONS
    + BIRDIE_CHALLENGE_LOCATIONS
)
CONGO_CANOPY_SCORE_LOCATIONS = tuple(
    congo_canopy_score_location(round_length)
    for round_length in CONGO_CANOPY_ROUNDS
)
GOLFER_BIRDIE_LOCATIONS = tuple(
    golfer_birdie_location(golfer) for golfer in PER_CHARACTER_GOLFERS
)
GOLFER_ROUND_SCORE_LOCATIONS = tuple(
    golfer_round_score_location(golfer) for golfer in PER_CHARACTER_GOLFERS
)
COURSE_PAR_SWEEP_LOCATIONS = tuple(
    course_par_sweep_location(course, par)
    for course in COURSES
    for par in (3, 4, 5)
)
STAR_TOURNAMENT_AGGREGATE_LOCATION = (
    "Star Tournament - Win Any Star Tournament"
)
NEAR_PIN_AGGREGATE_LOCATION = (
    "Near-Pin - Meet Aggregate Distance Target"
)
ADVANCE_TOUR_HOLE_THRESHOLDS = (1, 3, 6, 9, 18)


def advance_tour_hole_location(golfer: str, holes: int) -> str:
    noun = "Hole" if holes == 1 else "Holes"
    return f"Advance Tour - Complete {holes} {noun} as {golfer}"


ADVANCE_TOUR_HOLE_LOCATIONS = tuple(
    advance_tour_hole_location(golfer, holes)
    for golfer in ADVANCE_TOUR_GOLFERS
    for holes in ADVANCE_TOUR_HOLE_THRESHOLDS
)

SPECIAL_ACCOMPLISHMENT_LOCATIONS = (
    "Accomplishment - Sink a Putt from 10 Feet or More",
    "Accomplishment - Sink a Putt from 25 Feet or More",
    "Accomplishment - Sink a Putt from 50 Feet or More",
    "Accomplishment - Make a Hole-in-One",
    "Accomplishment - Make an Eagle",
    "Accomplishment - Complete a Bogey-Free Round",
    "Accomplishment - Make a Chip-In",
    "Accomplishment - Chip In from a Bunker",
    "Accomplishment - Make an Albatross",
    "Accomplishment - Drive 300 Yards",
    "Accomplishment - Make a Birdie",
    "Accomplishment - Make 5 Consecutive Birdies",
    "Accomplishment - Hole Out from 100 Yards or More",
    "Accomplishment - Hit the Pin",
    "Accomplishment - Execute a Perfect Power Shot",
    "Accomplishment - Win a Character Match 5 Up",
    "Accomplishment - Shoot 10 Under Par in a Round",
)

BEST_BADGE_LOCATIONS = tuple(
    f"Best Badges - Collect {count}" for count in (10, 25, 50, 75, 100)
)
BEST_BADGE_HOLE_LOCATIONS = tuple(
    best_badge_hole_location(course, hole)
    for course in COURSES
    for hole in range(1, 19)
)
UNDER_PAR_LOCATIONS = tuple(
    f"Under Par Round - {course}" for course in COURSES
)

GOAL_ALL_STAR_CHARACTERS = "Goal - Unlock All Star Characters"
GOAL_ALL_RING_SHOTS = "Goal - Clear All Single-Player Ring Attacks"
LEGACY_GOAL_BOWSER_ALL_THREE = "Goal - Bowser, Stars, and Ring Attacks"
GOAL_ALL_TOURNAMENTS = "Goal - Win All Regular and Star Tournaments"
LEGACY_GOAL_ALL_THREE = "Goal - Tournaments, Stars, and Ring Attacks"
GOAL_ALL_PRO_CHARACTER_MATCHES = (
    "Goal - Defeat All Character Match Opponents (Pro Difficulty)"
)
GOAL_ALL_THREE = (
    "Goal - Tournaments, Pro Character Matches, and Ring Attacks"
)
SYNTHETIC_GOAL_LOCATIONS = (
    GOAL_ALL_TOURNAMENTS,
    GOAL_ALL_PRO_CHARACTER_MATCHES,
    GOAL_ALL_RING_SHOTS,
    GOAL_ALL_THREE,
)
GOAL_LOCATION_BY_VALUE = (
    GOAL_ALL_TOURNAMENTS,
    GOAL_ALL_PRO_CHARACTER_MATCHES,
    GOAL_ALL_RING_SHOTS,
    GOAL_ALL_THREE,
)


# These are design assumptions, not claims about a mathematically required
# bag. Lakitu Valley and Blooper Bay are the forgiving early-play anchors
# identified in testing; the middle pair asks for a little more flexibility,
# and the two final courses are treated as late-game challenges.
COURSE_EQUIPMENT_PROFILES = {
    "Lakitu Valley": ("none", "wood_putter"),
    "Blooper Bay": ("none", "wood_putter"),
    "Cheep Cheep Falls": ("none", "balanced"),
    "Shifting Sands": ("none", "balanced"),
    "Peach's Castle Grounds": ("none", "star_balanced"),
    "Bowser Badlands": ("none", "star_balanced"),
}


def course_equipment_profiles(course: str) -> tuple[str, str]:
    """Return (AP minimum, practical recommendation) for a course."""

    return COURSE_EQUIPMENT_PROFILES[course]


def ring_equipment_profiles(course: str, level: int) -> tuple[str, str]:
    """Ring Attack inherits the selected course's readiness model."""

    return course_equipment_profiles(course)


def _locations() -> dict[str, LocationData]:
    rows: dict[str, LocationData] = {}
    any_star_golfer = tuple(
        (character_item(character), 2) for character in CHARACTERS
    )

    rows["Accomplishment - Sink a Putt from 10 Feet or More"] = LocationData(
        "Accomplishments",
    )
    rows["Accomplishment - Sink a Putt from 25 Feet or More"] = LocationData(
        "Accomplishments",
    )
    rows["Accomplishment - Sink a Putt from 50 Feet or More"] = LocationData(
        "Accomplishments"
    )

    all_regular_tournament_items = tuple(
        tournament_item(name) for name in REGULAR_TOURNAMENTS
    )
    for tournament in REGULAR_TOURNAMENTS + STAR_TOURNAMENTS:
        tournament_index = (
            REGULAR_TOURNAMENTS.index(tournament)
            if tournament in REGULAR_TOURNAMENTS
            else STAR_TOURNAMENTS.index(tournament)
        )
        course = COURSES[tournament_index]
        minimum_profile, recommended_profile = course_equipment_profiles(course)
        if tournament in STAR_TOURNAMENTS:
            minimum_profile = "star_balanced"
            recommended_profile = "star_balanced"
        rows[f"{tournament} - First Place"] = LocationData(
            "Star Tournament" if tournament in STAR_TOURNAMENTS else "Tournament",
            (
                PROGRESSIVE_TOURNAMENT_MODE_ITEM,
                tournament_access_item(tournament),
            ),
            requires_any_counts=(
                any_star_golfer
                if tournament_index >= 4
                else ()
            ),
            minimum_equipment_profile=minimum_profile,
            recommended_equipment_profile=recommended_profile,
        )

    for character in STAR_ELIGIBLE_CHARACTERS:
        rows[f"Character Match - Unlock Star {character}"] = LocationData(
            "Character Match",
            (
                mode_item("Character Match"),
                character_item(character),
                club_item("1W"),
            ),
            optional_group="retired_character_match_invitation_checks",
        )

    course_tournament = dict(zip(COURSES, REGULAR_TOURNAMENTS))
    for course in COURSES:
        rows[f"Character Match Course Win - {course}"] = LocationData(
            "Character Match",
            (
                mode_item("Character Match"),
                tournament_item(course_tournament[course]),
            ),
            optional_group="character_match_course_wins",
            minimum_equipment_profile="balanced",
            recommended_equipment_profile="expanded",
        )

    for course in COURSES:
        for level in range(1, 7):
            minimum_profile, recommended_profile = ring_equipment_profiles(course, level)
            rows[ring_shot_location(1, course, level)] = LocationData(
                "Ring Attack",
                (mode_item("Ring Attack"),),
                requires_any_counts=(
                    any_star_golfer
                    if course in COURSES[-2:]
                    else ()
                ),
                minimum_equipment_profile=minimum_profile,
                recommended_equipment_profile=recommended_profile,
            )
        for player_count in (2, 3, 4):
            for level in range(1, 5):
                minimum_profile, recommended_profile = ring_equipment_profiles(course, level)
                rows[ring_shot_location(player_count, course, level)] = LocationData(
                    "Ring Attack",
                    (mode_item("Ring Attack"),),
                    optional_group="multiplayer_ring_shots",
                    requires_any_counts=(
                        any_star_golfer
                        if course in COURSES[-2:]
                        else ()
                    ),
                    minimum_equipment_profile=minimum_profile,
                    recommended_equipment_profile=recommended_profile,
                )

    for character in CHARACTERS:
        rows[tournament_character_location(character)] = LocationData(
            "Accomplishments",
            (
                PROGRESSIVE_TOURNAMENT_MODE_ITEM,
                character_item(character),
            ),
            optional_group="tournament_character_wins",
            required_character=character,
            minimum_equipment_profile="balanced",
            recommended_equipment_profile="expanded",
        )

    rows["Accomplishment - Make a Hole-in-One"] = LocationData(
        "Accomplishments", (club_item("7I"),)
    )
    rows["Accomplishment - Make an Eagle"] = LocationData(
        "Accomplishments", (club_item("1W"), club_item("7I"))
    )
    rows["Accomplishment - Complete a Bogey-Free Round"] = LocationData(
        "Accomplishments",
        (club_item("1W"), club_item("PW")),
        (PROGRESSIVE_TOURNAMENT_MODE_ITEM, mode_item("Stroke Play")),
    )
    rows["Accomplishment - Make a Chip-In"] = LocationData(
        "Accomplishments", (club_item("PW"),)
    )
    rows["Accomplishment - Chip In from a Bunker"] = LocationData(
        "Accomplishments", (club_item("SW"),)
    )
    rows["Accomplishment - Make an Albatross"] = LocationData(
        "Accomplishments", (club_item("1W"), club_item("3W"))
    )
    rows["Accomplishment - Drive 300 Yards"] = LocationData(
        "Accomplishments",
        (club_item("1W"),),
        optional_group="retired_unreliable_300_yard_check",
    )
    rows["Accomplishment - Make a Birdie"] = LocationData("Accomplishments")
    rows["Accomplishment - Make 5 Consecutive Birdies"] = LocationData(
        "Accomplishments",
        (mode_item("Stroke Play"), club_item("1W"), club_item("PW")),
    )
    rows["Accomplishment - Hole Out from 100 Yards or More"] = LocationData(
        "Accomplishments",
        (club_item("3W"), club_item("7I")),
    )
    rows["Accomplishment - Hit the Pin"] = LocationData("Accomplishments")
    rows["Accomplishment - Execute a Perfect Power Shot"] = LocationData(
        "Accomplishments",
        (POWER_SHOT_ITEM, club_item("1W")),
    )
    rows["Accomplishment - Win a Character Match 5 Up"] = LocationData(
        "Accomplishments",
        (mode_item("Character Match"),),
        minimum_equipment_profile="balanced",
        recommended_equipment_profile="expanded",
    )
    rows["Accomplishment - Shoot 10 Under Par in a Round"] = LocationData(
        "Accomplishments",
        (club_item("1W"), club_item("PW")),
        (PROGRESSIVE_TOURNAMENT_MODE_ITEM, mode_item("Stroke Play")),
    )

    for count in (10, 25, 50, 75, 100):
        rows[f"Best Badges - Collect {count}"] = LocationData(
            "Accomplishments",
            (PROGRESSIVE_TOURNAMENT_MODE_ITEM,),
        )

    for course in COURSES:
        rows[f"Under Par Round - {course}"] = LocationData(
            "Accomplishments",
            (
                tournament_item(course_tournament[course]),
                club_item("1W"),
                club_item("PW"),
            ),
            (PROGRESSIVE_TOURNAMENT_MODE_ITEM, mode_item("Stroke Play")),
        )

    rows[GOAL_ALL_STAR_CHARACTERS] = LocationData(
        "Accomplishments",
        (mode_item("Character Match"), club_item("1W"))
        + tuple(character_item(name) for name in STAR_ELIGIBLE_CHARACTERS),
        requires_counts=tuple(
            (progressive_character_item(name), 2)
            for name in CHARACTERS
        ),
        optional_group="retired_all_star_goal",
    )
    rows[GOAL_ALL_RING_SHOTS] = LocationData(
        "Accomplishments",
        (mode_item("Ring Attack"),),
        minimum_equipment_profile="balanced",
        recommended_equipment_profile="expanded",
    )
    # Preserve the published pre-1.0 location ID but retire its Bowser-only
    # semantics. The replacement all-three goal is appended below so no
    # existing location ID moves.
    rows[LEGACY_GOAL_BOWSER_ALL_THREE] = LocationData(
        "Accomplishments",
        (
            PROGRESSIVE_TOURNAMENT_MODE_ITEM,
            mode_item("Character Match"),
            mode_item("Ring Attack"),
            tournament_item("Bowser Championship"),
            club_item("1W"),
            club_item("7I"),
            club_item("PW"),
        )
        + tuple(character_item(name) for name in STAR_ELIGIBLE_CHARACTERS),
        requires_counts=tuple(
            (progressive_character_item(name), 2)
            for name in CHARACTERS
        ),
        optional_group="retired_bowser_goal",
    )

    # Keep the original 185 location IDs stable by appending the four newly
    # modeled secret-golfer Character Match checks after every existing row.
    for character in SECRET_CHARACTERS:
        rows[f"Character Match - Unlock Star {character}"] = LocationData(
            "Character Match",
            (
                mode_item("Character Match"),
                character_item(character),
                club_item("1W"),
            ),
            optional_group="retired_character_match_invitation_checks",
        )

    # Append the individual holes so all location IDs published through 0.6.0
    # remain stable. A nonzero retail Best Badge entry means birdie or better;
    # these are locations only and never create badge items in the multiworld.
    for course in COURSES:
        access = tournament_item(course_tournament[course])
        minimum_profile, recommended_profile = course_equipment_profiles(course)
        for hole in range(1, 19):
            rows[best_badge_hole_location(course, hole)] = LocationData(
                "Tournament",
                (
                    PROGRESSIVE_TOURNAMENT_MODE_ITEM,
                    access,
                ),
                optional_group="individual_best_badges",
                requires_any_counts=(
                    any_star_golfer
                    if course in COURSES[-2:]
                    else ()
                ),
                minimum_equipment_profile=minimum_profile,
                recommended_equipment_profile=recommended_profile,
            )

    # The retail save keeps one result byte for each of the 18 One-On
    # One-Putt holes. This remains opt-in while the separate native menu gate
    # for the code-unlocked side game is still being mapped.
    rows[ONE_ON_ONE_PUTT_LOCATION] = LocationData(
        "Side Games",
        (
            mode_item("Side Games"),
            club_item("7I"),
            BASE_PUTTER_RANGE_ITEM,
        ),
        optional_group="experimental_checks",
    )

    for variant in COIN_ATTACK_VARIANTS:
        for character in CHARACTERS:
            rows[coin_character_location(variant, character)] = LocationData(
                "Coin Attack",
                (
                    mode_item("Coin Attack"),
                    character_item(character),
                    club_item("1W"),
                ),
                optional_group="coin_shoot_checks",
                required_character=character,
            )

    rows[COIN_100_GLOBAL_LOCATION] = LocationData(
        "Coin Attack",
        (mode_item("Coin Attack"), club_item("1W")),
        optional_group="coin_shoot_checks",
    )
    rows[COIN_BIRDIE_75_GLOBAL_LOCATION] = LocationData(
        "Coin Attack",
        (mode_item("Coin Attack"), club_item("1W"), club_item("PW")),
        optional_group="coin_shoot_checks",
    )
    course_tournament = dict(zip(COURSES, REGULAR_TOURNAMENTS))
    for course in COURSES:
        access = tournament_item(course_tournament[course])
        rows[coin_course_location("Collect 100 Coins on One Hole", course)] = (
            LocationData(
                "Coin Attack",
                (mode_item("Coin Attack"), access, club_item("1W")),
                optional_group="coin_shoot_checks",
            )
        )
        rows[
            coin_course_location(
                "Make a Birdie While Collecting 75 Coins", course
            )
        ] = LocationData(
            "Coin Attack",
            (
                mode_item("Coin Attack"),
                access,
                club_item("1W"),
                club_item("PW"),
            ),
            optional_group="coin_shoot_checks",
        )

        rows[f"Speed Golf - Finish {course} Under 15 Minutes"] = LocationData(
            "Speed Golf",
            (
                mode_item("Speed Golf"),
                access,
                club_item("1W"),
                club_item("PW"),
            ),
            optional_group="retired_speed_golf_15_minute_checks",
        )
    rows[SPEED_GOLF_HOLE_LOCATION] = LocationData(
        "Speed Golf",
        (mode_item("Speed Golf"), club_item("1W")),
        optional_group="speed_golf_checks",
    )

    # Putting and Approach use Novice/Intermediate/Expert.  The August 5
    # captures show that Shot Practice is a sequence of shot categories rather
    # than the same three-difficulty model.  Keep the three already-published
    # Shot Practice names/IDs reserved for protocol compatibility, but do not
    # place them in new worlds while the real sequence is being mapped.
    # Birdie Challenge exposes Front 9, Back 9, and All 18. Front 9 already has
    # a capture-verified reader; keep the later two in generated worlds so the
    # tester can obtain the paired captures needed to finish their reader.
    for difficulty_index, difficulty in enumerate(PRACTICE_DIFFICULTIES):
        putting_requirements = [PUTTING_PRACTICE_MODE_ITEM]
        if difficulty_index:
            putting_requirements.append(
                PUTTING_PRACTICE_DIFFICULTY_ITEMS[difficulty_index]
            )
        rows[
            practice_clear_location("Putting Practice", difficulty)
        ] = LocationData(
            "Practice Range",
            tuple(putting_requirements),
            optional_group="practice_challenge_checks",
            recommended_equipment_profile="two_putters",
        )
        rows[
            practice_clear_location("Approach Practice", difficulty)
        ] = LocationData(
            "Practice Range",
            tuple(
                [APPROACH_PRACTICE_MODE_ITEM]
                + (
                    [APPROACH_PRACTICE_DIFFICULTY_ITEMS[difficulty_index - 1]]
                    if difficulty_index
                    else []
                )
                + [APPROACH_SHOT_ITEM]
            ),
            optional_group="practice_challenge_checks",
            minimum_equipment_profile="none",
            recommended_equipment_profile="wood_putter",
        )
        rows[
            practice_clear_location("Shot Practice", difficulty)
        ] = LocationData(
            "Practice Range",
            (
                mode_item("Side Games"),
                club_item("1W"),
                club_item("7I"),
            ),
            optional_group="retired_shot_practice_difficulty_checks",
        )

    for stage in BIRDIE_CHALLENGE_STAGES:
        stage_index = BIRDIE_CHALLENGE_STAGES.index(stage)
        rows[birdie_challenge_location(stage)] = LocationData(
            "Side Games",
            (
                BIRDIE_CHALLENGE_MODE_ITEM,
                BASE_PUTTER_RANGE_ITEM,
            ),
            # Front 9 has a capture-verified persistent flag. Back 9 and All
            # 18 now progress locally through vanilla and remain reserved
            # until their distinct result bits are captured after 1.0.
            optional_group=(
                "practice_challenge_checks"
                if stage_index == 0
                else "retired_unmapped_birdie_challenge_checks"
            ),
            minimum_equipment_profile="balanced",
            recommended_equipment_profile="expanded",
        )

    for round_length in CONGO_CANOPY_ROUNDS:
        rows[congo_canopy_score_location(round_length)] = LocationData(
            "Accomplishments",
            (
                mode_item("Stroke Play"),
                club_item("7I"),
                club_item("PW"),
                BASE_PUTTER_RANGE_ITEM,
            ),
            optional_group=(
                "congo_canopy_score_checks"
                if round_length == "Front 9"
                else "retired_congo_canopy_long_round_checks"
            ),
        )
    rows[NEAR_PIN_AGGREGATE_LOCATION] = LocationData(
        "Side Games",
        (mode_item("Near-Pin"),),
        minimum_equipment_profile="none",
        recommended_equipment_profile="wood_putter",
    )
    # Append these capture-backed client checks after every previously
    # published location ID. Neither check attempts to write a native menu
    # selector or unlock its retail entry.
    rows[HOLE_IN_ONE_CONTEST_LOCATION] = LocationData(
        "Side Games",
        (
            mode_item("Side Games"),
            club_item("7I"),
            BASE_PUTTER_RANGE_ITEM,
        ),
        optional_group="experimental_checks",
    )
    rows[BOWSERS_BIG_BLAST_LOCATION] = LocationData(
        "Tournament",
        (
            PROGRESSIVE_TOURNAMENT_MODE_ITEM,
            tournament_item("Bowser Championship"),
            club_item("1W"),
            club_item("PW"),
            BASE_PUTTER_RANGE_ITEM,
        ),
        optional_group="experimental_checks",
    )
    # Preserve the ten published IDs and their client reader for old rooms,
    # but retire them from new 1.0 seeds. Placement checks added later in the
    # beta provide enough pool capacity without asking players to grind an
    # arbitrary 1/3/6/9/18 holes as Neil and Ella.
    for location in ADVANCE_TOUR_HOLE_LOCATIONS:
        rows[location] = LocationData(
            "Accomplishments",
            (ADVANCE_TOUR_GOLFER_ITEM,),
            optional_group="retired_advance_tour_hole_counts",
        )
    # Appended after every previously published location. This aggregate is
    # derived from the same persistent first-place table as the individual
    # Star Tournament checks. Reaching all six Star events requires the shared
    # physical-course items plus the single Tournament feature item.
    rows[STAR_TOURNAMENT_AGGREGATE_LOCATION] = LocationData(
        "Star Tournament",
        (
            PROGRESSIVE_TOURNAMENT_MODE_ITEM,
            club_item("1W"),
        ) + all_regular_tournament_items,
    )
    # Correct Shot Practice categories discovered from the retail progression
    # text. Append them after every existing location so the three retired
    # difficulty-model IDs and all other published IDs remain stable.
    for stage in SHOT_PRACTICE_STAGES:
        stage_index = SHOT_PRACTICE_STAGES.index(stage)
        rows[practice_clear_location("Shot Practice", stage)] = LocationData(
            "Practice Range",
            tuple(
                [SHOT_PRACTICE_MODE_ITEM]
                + (
                    [SHOT_PRACTICE_STAGE_ITEMS[stage_index - 1]]
                    if stage_index
                    else []
                )
            ),
            optional_group="practice_challenge_checks",
            minimum_equipment_profile="none",
            recommended_equipment_profile="wood_putter",
        )
    # August 6 testing requested a ten-minute per-course target. Append the
    # corrected names and the combined time/score feat after all published
    # locations; the six old 15-minute IDs above remain reserved and inactive.
    for course, access in zip(COURSES, REGULAR_TOURNAMENTS):
        rows[f"Speed Golf - Finish {course} Under 10 Minutes"] = LocationData(
            "Speed Golf",
            (
                mode_item("Speed Golf"),
                tournament_item(access),
                club_item("1W"),
                club_item("PW"),
            ),
            optional_group="speed_golf_checks",
        )
    rows[SPEED_GOLF_UNDER_PAR_LOCATION] = LocationData(
        "Speed Golf",
        (mode_item("Speed Golf"), club_item("1W"), club_item("PW")),
        optional_group="speed_golf_checks",
    )
    # Append the new completion targets after every published location. These
    # are client-derived from completed checks and never consume native hook
    # bitfield capacity.
    all_tournament_requirements = tuple(
        tournament_item(name) for name in REGULAR_TOURNAMENTS
    )
    rows[GOAL_ALL_TOURNAMENTS] = LocationData(
        "Accomplishments",
        (
            PROGRESSIVE_TOURNAMENT_MODE_ITEM,
        )
        + all_tournament_requirements,
        requires_any_counts=any_star_golfer,
        minimum_equipment_profile="balanced",
        recommended_equipment_profile="expanded",
    )
    rows[LEGACY_GOAL_ALL_THREE] = LocationData(
        "Accomplishments",
        (
            PROGRESSIVE_TOURNAMENT_MODE_ITEM,
            mode_item("Character Match"),
            mode_item("Ring Attack"),
            club_item("1W"),
            club_item("7I"),
            club_item("PW"),
        )
        + all_tournament_requirements
        + tuple(character_item(name) for name in STAR_ELIGIBLE_CHARACTERS),
        requires_counts=tuple(
            (progressive_character_item(name), 2)
            for name in CHARACTERS
        ),
        optional_group="retired_all_star_goal",
    )

    # Append the first 1.0 location expansion after every previously published
    # ID. These checks are live, seed-scoped accomplishments rather than retail
    # save-table flags, so they do not consume native protocol bitfield space.
    for golfer in PER_CHARACTER_GOLFERS:
        golfer_access = (
            character_item(golfer)
            if golfer in CHARACTERS
            else ADVANCE_TOUR_GOLFER_ITEM
        )
        rows[golfer_birdie_location(golfer)] = LocationData(
            "Accomplishments",
            (golfer_access,),
            (PROGRESSIVE_TOURNAMENT_MODE_ITEM, mode_item("Stroke Play")),
            required_character=golfer,
        )
        rows[golfer_round_score_location(golfer)] = LocationData(
            "Accomplishments",
            (golfer_access,),
            (PROGRESSIVE_TOURNAMENT_MODE_ITEM, mode_item("Stroke Play")),
            required_character=golfer,
            minimum_equipment_profile="balanced",
            recommended_equipment_profile="expanded",
        )

    for course, access in zip(COURSES, REGULAR_TOURNAMENTS):
        for par in (3, 4, 5):
            rows[course_par_sweep_location(course, par)] = LocationData(
                "Accomplishments",
                (
                    tournament_item(access),
                ),
                (PROGRESSIVE_TOURNAMENT_MODE_ITEM, mode_item("Stroke Play")),
                minimum_equipment_profile="balanced",
                recommended_equipment_profile="expanded",
            )

    # Invitation letters and retail Star awards are deliberately independent
    # of Archipelago progression. The durable Character Match result table is
    # instead exposed as one Pro-difficulty opponent victory per native golfer.
    # Neil and Ella are omitted for 1.0 because they have no native opponent
    # rows; their playable golfer unlock remains fully supported.
    for character in CHARACTERS:
        rows[character_match_pro_location(character)] = LocationData(
            "Character Match",
            (mode_item("Character Match"),),
            minimum_equipment_profile="balanced",
            recommended_equipment_profile="expanded",
        )

    rows[GOAL_ALL_PRO_CHARACTER_MATCHES] = LocationData(
        "Accomplishments",
        (mode_item("Character Match"),),
        minimum_equipment_profile="balanced",
        recommended_equipment_profile="expanded",
    )
    rows[GOAL_ALL_THREE] = LocationData(
        "Accomplishments",
        (
            PROGRESSIVE_TOURNAMENT_MODE_ITEM,
            mode_item("Character Match"),
            mode_item("Ring Attack"),
        )
        + all_tournament_requirements,
        requires_any_counts=any_star_golfer,
        minimum_equipment_profile="balanced",
        recommended_equipment_profile="expanded",
    )

    # Append placement checks after every previously published location ID.
    # Retail retains the best finishing position for each regular and Star
    # tournament, so these remain durable without another native hook.
    rows[TOURNAMENT_FINISH_LOCATION] = LocationData(
        "Tournament",
        (PROGRESSIVE_TOURNAMENT_MODE_ITEM,),
        requires_any=all_regular_tournament_items,
        recommended_equipment_profile="wood_putter",
    )
    for tournament in REGULAR_TOURNAMENTS + STAR_TOURNAMENTS:
        tournament_index = (
            REGULAR_TOURNAMENTS.index(tournament)
            if tournament in REGULAR_TOURNAMENTS
            else STAR_TOURNAMENTS.index(tournament)
        )
        course = COURSES[tournament_index]
        minimum_profile, recommended_profile = course_equipment_profiles(course)
        if tournament in STAR_TOURNAMENTS:
            minimum_profile = "star_balanced"
            recommended_profile = "star_balanced"
        rows[f"{tournament} - Top 3 Finish"] = LocationData(
            "Star Tournament" if tournament in STAR_TOURNAMENTS else "Tournament",
            (
                PROGRESSIVE_TOURNAMENT_MODE_ITEM,
                tournament_access_item(tournament),
            ),
            requires_any_counts=(
                any_star_golfer if tournament_index >= 4 else ()
            ),
            minimum_equipment_profile=minimum_profile,
            recommended_equipment_profile=recommended_profile,
        )
    return rows


ALL_LOCATION_DATA = _locations()
# Protocol v2 and the v0.8.0 ISO patch expose the 298 locations published
# through v0.8.5. Later client-derived checks are reported directly by the
# desktop bridge and must not expand into the fixed 40-byte PPC bitfield.
PROTOCOL_LOCATION_NAMES = tuple(ALL_LOCATION_DATA)[:298]
assert len(PROTOCOL_LOCATION_NAMES) == 298
assert PROTOCOL_LOCATION_NAMES[-1] == ONE_ON_ONE_PUTT_LOCATION
LOCATION_NAME_TO_ID = {
    name: LOCATION_ID_BASE + index for index, name in enumerate(ALL_LOCATION_DATA)
}
