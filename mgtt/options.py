from dataclasses import dataclass

from Options import Choice, DefaultOnToggle, PerGameCommonOptions, Range, Toggle


class StartingCharacters(Range):
    """Number of randomly selected non-GBA golfers available when the seed starts."""

    display_name = "Starting Characters"
    range_start = 1
    range_end = 16
    default = 4


class ShuffleCharacters(DefaultOnToggle):
    """Shuffle two progressive copies per golfer: base first, then star."""

    display_name = "Shuffle Progressive Characters"


class ShuffleStarCharacters(DefaultOnToggle):
    """Compatibility partner for Shuffle Characters; both values must match."""

    display_name = "Shuffle Progressive Star Stages"


class ShuffleClubs(Choice):
    """Choose vanilla, global, or one of two per-golfer club distributions."""

    display_name = "Shuffle Clubs"
    option_vanilla = 0
    option_global = 1
    option_per_character = 2
    # Every golfer starts with one independently selected wood, iron, and
    # wedge. Their remaining ten standard clubs stay in the item pool.
    option_per_character_balanced = 3
    # Per-golfer bags are the intended MGTT experience.  Keep the global mode
    # available for smaller seeds and compatibility with older YAML files.
    default = 2

    @classmethod
    def from_any(cls, data):
        # Rooms and YAMLs published through v0.8.4 used a boolean toggle.
        if isinstance(data, bool):
            return cls(cls.option_global if data else cls.option_vanilla)
        if isinstance(data, str) and data.lower() in {"true", "false"}:
            return cls(
                cls.option_global if data.lower() == "true" else cls.option_vanilla
            )
        return super().from_any(data)


class ShuffleCustomClubSets(DefaultOnToggle):
    """Shuffle all 15 club sets transferable from Mario Golf: Advance Tour."""

    display_name = "Shuffle Advance Tour Custom Club Sets"


class ShuffleAdvanceTourGolfers(DefaultOnToggle):
    """Shuffle one item that adds default Neil and Ella transfer profiles."""

    display_name = "Shuffle Advance Tour Golfers (Neil and Ella)"


class AdvanceTourGolferStats(Choice):
    """Choose the driving-distance profile for AP-created Neil and Ella."""

    display_name = "Advance Tour Golfer Stats"
    option_weak = 0
    option_standard = 1
    option_overpowered = 2
    default = 1


class ShuffleTournaments(DefaultOnToggle):
    """Shuffle the six physical courses used by both Tournament menus."""

    display_name = "Shuffle Tournaments"


class StartingTournaments(Range):
    """Number of random regular courses available at seed start.

    A course item grants that course in regular Tournament, Star Tournament,
    Stroke Play, Speed Golf, and Character Match. Ring Attack retains its
    vanilla sequential course progression. At least one physical course is
    always available at seed start.
    """

    display_name = "Starting Regular Courses"
    range_start = 1
    range_end = 6
    default = 1


class ShuffleModes(DefaultOnToggle):
    """Shuffle game-mode access, including Putting Practice."""

    display_name = "Shuffle Modes"


class StartingModes(Range):
    """Number of modes available when mode shuffling is on.

    The starting selection always includes Tournament or Ring Attack.
    """

    display_name = "Starting Modes"
    range_start = 1
    range_end = 3
    default = 3


class ShufflePowerShots(Toggle):
    """Shuffle Tournament and Stroke Play Power Shot capacity above the start."""

    display_name = "Shuffle Power Shot Capacity"
    default = 1


class StartingPowerShotCapacity(Range):
    """Tournament and Stroke Play starting capacity when capacity is shuffled."""

    display_name = "Starting Power Shot Capacity"
    range_start = 1
    range_end = 9
    default = 6


class ShuffleShortGame(Toggle):
    """Start with one putter range; shuffle the other ranges and Approach Shot."""

    display_name = "Shuffle Putter Ranges and Approach Shot"


class PutterRangeScope(Choice):
    """Choose whether shuffled putter lengths are global or owned per golfer."""

    display_name = "Putter Range Unlock Scope"
    option_global = 0
    option_per_character = 1
    # Per-golfer equipment progression is the intended/default experience.
    # Global ranges remain available for smaller pools and compatibility.
    default = 1


class ShufflePuttingPracticeDifficulties(DefaultOnToggle):
    """Shuffle Novice, Intermediate, and Expert Putting Practice access."""

    display_name = "Shuffle Putting Practice Difficulties"


class SpinUnlocks(Choice):
    """Choose whether spin inputs are vanilla, globally shuffled, or per golfer."""

    display_name = "Spin Unlocks"
    option_vanilla = 0
    option_global = 1
    option_per_character = 2
    default = 0


class TournamentCharacterChecks(Toggle):
    """Add one check for winning any tournament with each of the 16 golfers."""

    display_name = "Tournament Win Per Character Checks"


class CharacterMatchCourseChecks(DefaultOnToggle):
    """Add one check for winning a Character Match on each regular course.

    These six published locations are enabled by default for compatibility
    with existing option sets, several of which use the full core location
    capacity. They can be disabled when a seed has enough other enabled
    locations; the client will not report them until the result mapping is
    validated from captures.
    """

    display_name = "Character Match Win Per Course Checks"


class CharacterMatchCourseAccess(Choice):
    """Choose whether regular Character Match courses start open.

    Toadstool Tour uses the same six availability bits for Character Match and
    regular Tournament courses. The default links both menus to the shuffled
    regular Tournament items. The compatibility choice exposes all six in both
    modes and therefore precollects all six regular Tournament access items.
    """

    display_name = "Character Match Course Access"
    option_all_courses = 0
    option_follow_tournament_items = 1
    default = 1


class RingShotPlayerCounts(Choice):
    """Choose which Ring Attack player-count checks are included."""

    display_name = "Ring Attack Player Counts"
    option_single_player_only = 0
    # Preserve the published numeric value for all_player_counts. The new
    # public-beta middle choice is appended at value two.
    option_all_player_counts = 1
    option_one_and_two_player = 2
    default = 2


class IndividualBestBadgeChecks(DefaultOnToggle):
    """Add one local check for birdie-or-better on each regular course hole."""

    display_name = "Individual Best Badge Checks (108)"


class CoinShootChecks(Toggle):
    """Add per-golfer cumulative and per-hole Coin Attack checks."""

    display_name = "Coin Attack Checks"


class SpeedGolfChecks(Toggle):
    """Add course-under-10, fast-hole, and under-15/under-par checks."""

    display_name = "Speed Golf Time Checks"


class PracticeChallengeChecks(Toggle):
    """Add supported Practice clears and Birdie Challenge Front 9."""

    display_name = "Practice and Birdie Challenge Clear Checks"


class CongoCanopyScoreChecks(Toggle):
    """Add the supported Congo Canopy Front 9 Stroke Play score check."""

    display_name = "Congo Canopy Stroke Play Score Checks"


class CongoCanopyScoreToPar(Range):
    """Required score relative to par for each enabled Congo Canopy check."""

    display_name = "Congo Canopy Required Score to Par"
    range_start = -9
    range_end = 9
    default = 0


class NearPinAggregateFeet(Range):
    """Maximum saved total distance for the aggregate Near-Pin check."""

    display_name = "Near-Pin Aggregate Distance Target (Feet)"
    range_start = 1
    range_end = 901
    default = 300


class ExperimentalChecks(Toggle):
    """Reserved compatibility option; Part D checks are deferred and never generated."""

    display_name = "Deferred Special-Mode Checks (Unavailable)"


class NativePopupDelivery(Choice):
    """Reserved native-popup preference; delivery is disabled for 1.0 safety.

    Repeated controller testing proved that even one serialized AP receipt can
    collide with a retail score/result dialog at 0x800246c8/0x800246cc. Keep
    the historical choice value parseable for old YAML files, but generation
    and the client force crash-safe client-only delivery until a native-owned
    message implementation is available after 1.0.
    """

    display_name = "Native In-Game Unlock Messages"
    option_client_only = 0
    option_serialized = 1
    default = 0


class EnableDebugCommands(Toggle):
    """Allow server-backed item and location cheat commands for testing."""

    display_name = "Enable Development Debug Commands"


class Goal(Choice):
    """Choose the accomplishments that complete this Archipelago slot."""

    display_name = "Goal"
    option_all_tournaments = 0
    # Older YAML files used this name for numeric goal value zero. Keep the
    # spelling loadable while applying the stronger all-tournaments target.
    alias_bowser_championship = 0
    option_all_pro_character_matches = 1
    # Compatibility spelling used by pre-1.0 YAMLs.
    alias_all_star_characters = 1
    option_all_single_player_ring_shots = 2
    option_all_three = 3
    # All four goal variants are derived from bridged, monotonic checks/items.
    default = 0


@dataclass
class MGTTOptions(PerGameCommonOptions):
    starting_characters: StartingCharacters
    shuffle_characters: ShuffleCharacters
    shuffle_star_characters: ShuffleStarCharacters
    shuffle_clubs: ShuffleClubs
    shuffle_custom_club_sets: ShuffleCustomClubSets
    shuffle_advance_tour_golfers: ShuffleAdvanceTourGolfers
    advance_tour_golfer_stats: AdvanceTourGolferStats
    shuffle_tournaments: ShuffleTournaments
    starting_tournaments: StartingTournaments
    shuffle_modes: ShuffleModes
    starting_modes: StartingModes
    shuffle_power_shots: ShufflePowerShots
    starting_power_shot_capacity: StartingPowerShotCapacity
    shuffle_short_game: ShuffleShortGame
    putter_range_scope: PutterRangeScope
    shuffle_putting_practice_difficulties: ShufflePuttingPracticeDifficulties
    spin_unlocks: SpinUnlocks
    tournament_character_checks: TournamentCharacterChecks
    character_match_course_checks: CharacterMatchCourseChecks
    character_match_course_access: CharacterMatchCourseAccess
    ring_shot_player_counts: RingShotPlayerCounts
    individual_best_badge_checks: IndividualBestBadgeChecks
    coin_shoot_checks: CoinShootChecks
    speed_golf_checks: SpeedGolfChecks
    practice_challenge_checks: PracticeChallengeChecks
    congo_canopy_score_checks: CongoCanopyScoreChecks
    congo_canopy_score_to_par: CongoCanopyScoreToPar
    near_pin_aggregate_feet: NearPinAggregateFeet
    experimental_checks: ExperimentalChecks
    native_popup_delivery: NativePopupDelivery
    enable_debug_commands: EnableDebugCommands
    goal: Goal
