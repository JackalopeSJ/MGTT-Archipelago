from __future__ import annotations

from typing import Any, ClassVar

from BaseClasses import Tutorial
from worlds.AutoWorld import WebWorld, World
from worlds.LauncherComponents import Component, Type, components, launch

from . import regions, rules
from .data import (
    ADVANCE_TOUR_GOLFER_ITEM,
    APPROACH_PRACTICE_DIFFICULTY_ITEMS,
    APPROACH_PRACTICE_MODE_ITEM,
    ALL_LOCATION_DATA,
    CHARACTER_SPIN_ITEMS,
    CHARACTER_CLUB_ITEMS,
    CHARACTER_PUTTER_RANGE_ITEMS,
    CHARACTERS,
    CLUBS,
    BIRDIE_CHALLENGE_MODE_ITEM,
    BIRDIE_CHALLENGE_STAGE_ITEMS,
    CUSTOM_CLUB_SETS,
    GAME,
    GLOBAL_SPIN_ITEMS,
    ITEM_NAME_TO_ID,
    LOCATION_NAME_TO_ID,
    MODES,
    PER_CHARACTER_GOLFERS,
    APPROACH_SHOT_ITEM,
    PUTTER_RANGE_ITEMS,
    PUTTER_RANGE_FEET,
    PUTTING_PRACTICE_DIFFICULTY_ITEMS,
    PUTTING_PRACTICE_MODE_ITEM,
    SHOT_PRACTICE_MODE_ITEM,
    SHOT_PRACTICE_STAGE_ITEMS,
    POWER_SHOT_ITEM,
    PROGRESSIVE_TOURNAMENT_MODE_ITEM,
    PROGRESSIVE_CHARACTER_ITEMS,
    RANDOMIZABLE_MODES,
    REGULAR_TOURNAMENTS,
    STAR_TOURNAMENTS,
    WOODS,
    IRONS,
    WEDGES,
    STAR_TOURNAMENT_MODE_ITEM,
    character_item,
    character_club_item,
    character_putter_range_item,
    club_item,
    custom_club_set_item,
    mode_item,
    tournament_item,
)
from .items import MGTTItem, create_item
from .options import MGTTOptions


ADVANCE_TOUR_STAT_PROFILES = {
    "weak": (205, 200),
    "standard": (305, 300),
    "overpowered": (405, 400),
}

# Mulligans are useful consumable filler. Keep the native byte-sized inventory
# comfortably below its 255-copy limit while allowing every ordinary empty
# MGTT location in supported 1.0 configurations to become a Mulligan.
MAX_MULLIGAN_FILLER = 99

# Keep all six physical courses eligible at seed start while gently favoring
# the two forgiving opening courses identified through player testing.  The
# values are deliberately modest: hard-course starts remain possible instead
# of being silently converted into an easy-course guarantee.
STARTING_TOURNAMENT_WEIGHTS = {
    "Lakitu Cup": 3,
    "Blooper Open": 3,
    "Cheep Cheep Tournament": 2,
    "Sands Classic": 2,
    "Peach's Invitational": 1,
    "Bowser Championship": 1,
}
EARLY_TOURNAMENTS = ("Lakitu Cup", "Blooper Open")
HARD_TOURNAMENTS = ("Peach's Invitational", "Bowser Championship")


def _weighted_sample_without_replacement(
    random_source, population: tuple[str, ...], count: int
) -> list[str]:
    """Select distinct entries using the public starting-course weights."""

    remaining = list(population)
    selected: list[str] = []
    for _ in range(count):
        total_weight = sum(
            STARTING_TOURNAMENT_WEIGHTS[name] for name in remaining
        )
        ticket = random_source.randrange(total_weight)
        for index, name in enumerate(remaining):
            ticket -= STARTING_TOURNAMENT_WEIGHTS[name]
            if ticket < 0:
                selected.append(name)
                remaining.pop(index)
                break
    return selected


def _run_client_process(*args: str) -> None:
    """Windows-safe child target with a visible failure path."""

    try:
        from .client import main

        main(*args)
    except BaseException as error:
        import logging
        import traceback
        import Utils

        logging.getLogger("Client").error(
            "MGTT client failed to launch:\n%s", traceback.format_exc()
        )
        try:
            Utils.messagebox(
                "MGTT Client launch failed",
                f"{type(error).__name__}: {error}\n\n"
                "See the Archipelago log folder for the full traceback.",
                error=True,
            )
        finally:
            raise


def run_client(*args: str) -> None:
    launch(_run_client_process, name="MGTTClient", args=args)


components.append(
    Component(
        "Mario Golf: Toadstool Tour Client",
        func=run_client,
        component_type=Type.CLIENT,
        game_name=GAME,
        supports_uri=True,
        description="Connect Mario Golf: Toadstool Tour in Dolphin to Archipelago.",
    )
)


class MGTTWeb(WebWorld):
    theme = "partyTime"
    tutorials = [
        Tutorial(
            "Multiworld Setup Guide",
            "Install the APWorld and connect Dolphin to the multiworld bridge.",
            "English",
            "setup_en.md",
            "setup/en",
            ["MGTT Archipelago prototype"],
        )
    ]


class MGTTWorld(World):
    """Randomized golf progression for Mario Golf: Toadstool Tour."""

    game: ClassVar[str] = GAME
    options_dataclass = MGTTOptions
    options: MGTTOptions
    web = MGTTWeb()
    item_name_to_id = ITEM_NAME_TO_ID
    location_name_to_id = LOCATION_NAME_TO_ID
    item_name_groups = {
        "Characters": set(PROGRESSIVE_CHARACTER_ITEMS),
        "Progressive Characters": set(PROGRESSIVE_CHARACTER_ITEMS),
        "Star Characters": set(PROGRESSIVE_CHARACTER_ITEMS),
        "Clubs": {club_item(name) for name in CLUBS} | set(CHARACTER_CLUB_ITEMS),
        "Global Clubs": {club_item(name) for name in CLUBS},
        "Per-Character Clubs": set(CHARACTER_CLUB_ITEMS),
        "Advance Tour Custom Club Sets": {
            custom_club_set_item(name) for name in CUSTOM_CLUB_SETS
        },
        "Advance Tour Golfers": {ADVANCE_TOUR_GOLFER_ITEM},
        "Tournaments": {
            tournament_item(name) for name in REGULAR_TOURNAMENTS
        },
        "Legacy Star Tournament Courses": {
            tournament_item(name) for name in STAR_TOURNAMENTS
        },
        "Modes": {mode_item(name) for name in RANDOMIZABLE_MODES}
        | {PUTTING_PRACTICE_MODE_ITEM, PROGRESSIVE_TOURNAMENT_MODE_ITEM},
        "Spin Techniques": set(GLOBAL_SPIN_ITEMS) | set(CHARACTER_SPIN_ITEMS),
        "Short Game": set(PUTTER_RANGE_ITEMS)
        | set(CHARACTER_PUTTER_RANGE_ITEMS)
        | {APPROACH_SHOT_ITEM},
        "Per-Character Putter Ranges": set(CHARACTER_PUTTER_RANGE_ITEMS),
        "Putting Practice Difficulties": set(PUTTING_PRACTICE_DIFFICULTY_ITEMS),
        "Approach Practice Difficulties": set(APPROACH_PRACTICE_DIFFICULTY_ITEMS),
        "Shot Practice Levels": set(SHOT_PRACTICE_STAGE_ITEMS),
        "Birdie Challenge Levels": set(BIRDIE_CHALLENGE_STAGE_ITEMS),
    }
    required_client_version = (0, 6, 7)

    starting_character_names: list[str]
    starting_club_item: str
    starting_character_club_items: list[str]
    starting_tournament_names: list[str]
    early_course_safety_item: str | None
    starting_mode_names: list[str]
    starting_putter_range_item: str
    starting_character_putter_range_items: list[str]
    starting_putting_practice_items: list[str]
    advance_tour_stat_profile: str
    advance_tour_golfer_distances: tuple[int, int]
    active_locations: dict

    def generate_early(self) -> None:
        if bool(self.options.shuffle_characters) != bool(
            self.options.shuffle_star_characters
        ):
            raise ValueError(
                "Progressive character pairs require shuffle_characters and "
                "shuffle_star_characters to use the same value."
            )
        requested_count = self.options.starting_characters.value
        # A multiplayer Ring Attack seed must be locally playable without
        # waiting for golfer items. Keep the user's configured value intact in
        # the option object, but guarantee the four-golfer public-beta roster
        # whenever either multiplayer package is enabled.
        ring_player_count = self.options.ring_shot_player_counts.value
        count = max(
            requested_count,
            4 if ring_player_count in {1, 2} else 1,
        )
        self.starting_character_names = sorted(self.random.sample(CHARACTERS, count))
        # The exact choice belongs to the generated seed, not the client.
        # Serializing it below keeps reconnects and every player installation
        # on the same non-putter starting club.
        self.starting_club_item = club_item(self.random.choice(CLUBS))
        self.starting_character_club_items = []
        if self.options.shuffle_clubs.value in (2, 3):
            starting_categories = (
                (CLUBS,)
                if self.options.shuffle_clubs.value == 2
                else (WOODS, IRONS, WEDGES)
            )
            self.starting_character_club_items = [
                character_club_item(character, self.random.choice(category))
                for character in PER_CHARACTER_GOLFERS
                for category in starting_categories
            ]
        if self.options.shuffle_modes:
            # Always begin with at least one substantial progression mode.
            # A seed that rolled only a practice/side mode could be logically
            # beatable yet offer very little meaningful play while waiting for
            # another game to send access. Randomize which core mode anchors
            # the start, then fill the remaining configured slots normally.
            core_start = self.random.choice(("Tournament", "Ring Attack"))
            remaining_modes = tuple(
                mode for mode in RANDOMIZABLE_MODES if mode != core_start
            )
            self.starting_mode_names = sorted(
                (
                    core_start,
                    *self.random.sample(
                        remaining_modes,
                        self.options.starting_modes.value - 1,
                    ),
                )
            )
        else:
            self.starting_mode_names = list(MODES)
        if (
            self.options.shuffle_tournaments
            and self.options.character_match_course_access.value != 0
        ):
            self.starting_tournament_names = sorted(
                _weighted_sample_without_replacement(
                    self.random,
                    REGULAR_TOURNAMENTS,
                    self.options.starting_tournaments.value,
                )
            )
        elif self.options.shuffle_tournaments:
            self.starting_tournament_names = list(REGULAR_TOURNAMENTS)
        else:
            self.starting_tournament_names = list(REGULAR_TOURNAMENTS)
        self.early_course_safety_item = None
        if (
            self.options.shuffle_tournaments
            and self.options.character_match_course_access.value != 0
            and self.starting_tournament_names
            and set(self.starting_tournament_names) <= set(HARD_TOURNAMENTS)
        ):
            # A hard-only opening remains a legitimate random result. Place a
            # randomly selected forgiving course in an early sphere so that it
            # becomes relief rather than an immediate free starting unlock.
            self.early_course_safety_item = tournament_item(
                self.random.choice(EARLY_TOURNAMENTS)
            )
        self.starting_putter_range_item = self.random.choice(PUTTER_RANGE_ITEMS)
        self.starting_character_putter_range_items = [
            character_putter_range_item(
                character, self.random.choice(PUTTER_RANGE_FEET)
            )
            for character in PER_CHARACTER_GOLFERS
        ]
        self.starting_putting_practice_items = []
        if not self.options.shuffle_modes:
            self.starting_putting_practice_items.append(PUTTING_PRACTICE_MODE_ITEM)
        if not self.options.shuffle_putting_practice_difficulties:
            self.starting_putting_practice_items.extend(
                PUTTING_PRACTICE_DIFFICULTY_ITEMS[1:]
            )
        requested_stat_profile = self.options.advance_tour_golfer_stats.current_key
        # Archipelago's reserved Choice value `random` has already resolved to
        # one of these three concrete keys before world generation. Serialize
        # only that result so clients and reconnects cannot reroll it.
        self.advance_tour_stat_profile = requested_stat_profile
        self.advance_tour_golfer_distances = ADVANCE_TOUR_STAT_PROFILES[
            requested_stat_profile
        ]
        self.active_locations = {
            name: data
            for name, data in ALL_LOCATION_DATA.items()
            if (
                data.optional_group is None
                or (
                    data.optional_group == "tournament_character_wins"
                    and self.options.tournament_character_checks
                )
                or (
                    data.optional_group == "character_match_course_wins"
                    and self.options.character_match_course_checks
                )
                or (
                    data.optional_group == "multiplayer_ring_shots"
                    and (
                        self.options.ring_shot_player_counts.value == 1
                        or (
                            self.options.ring_shot_player_counts.value == 2
                            and name.startswith("Ring Attack (2P)")
                        )
                    )
                )
                or (
                    data.optional_group == "individual_best_badges"
                    and self.options.individual_best_badge_checks
                )
                or (
                    data.optional_group == "coin_shoot_checks"
                    and self.options.coin_shoot_checks
                )
                or (
                    data.optional_group == "speed_golf_checks"
                    and self.options.speed_golf_checks
                )
                or (
                    data.optional_group == "practice_challenge_checks"
                    and self.options.practice_challenge_checks
                )
                or (
                    data.optional_group == "congo_canopy_score_checks"
                    and self.options.congo_canopy_score_checks
                )
                # Password-only special modes are deliberately withheld from
                # player seeds until native, password-free entry exists.
                # Keep their published IDs/readers reserved for a future
                # compatible release, but never make those locations active.
            )
        }

    def create_regions(self) -> None:
        regions.create_regions(self)

    def create_item(self, name: str) -> MGTTItem:
        return create_item(name, self.player)

    def create_event(self, name: str) -> MGTTItem:
        # Goal checks are real, addressable checks reported by the game client.
        # Use a code-bearing, local-only locked Victory item so Archipelago can
        # serialize that check without mistaking it for a virtual event location.
        return self.create_item(name)

    def _precollect(self, names) -> None:
        for name in names:
            self.multiworld.push_precollected(self.create_item(name))

    def create_items(self) -> None:
        start_items = {character_item(name) for name in self.starting_character_names}
        self._precollect(sorted(start_items))
        start_modes = {
            mode_item(name)
            for name in self.starting_mode_names
            if name != "Tournament"
        }

        pool_names: list[str] = []

        if self.options.shuffle_characters:
            for character in CHARACTERS:
                item = character_item(character)
                copies = 1 if item in start_items else 2
                pool_names.extend([item] * copies)
        else:
            for character in CHARACTERS:
                item = character_item(character)
                copies = 1 if item in start_items else 2
                self._precollect([item] * copies)

        # Retail club selection can enter an invalid state with only the putter.
        # Global shuffling starts with one club; per-character shuffling starts
        # every native and Advance Tour golfer with either one independently
        # selected club or the balanced wood/iron/wedge trio.
        club_scope = self.options.shuffle_clubs.value
        if club_scope in (2, 3):
            self._precollect(self.starting_character_club_items)
            starting_character_clubs = set(self.starting_character_club_items)
            pool_names.extend(
                character_club_item(character, club)
                for character in PER_CHARACTER_GOLFERS
                for club in CLUBS
                if character_club_item(character, club)
                not in starting_character_clubs
            )
        else:
            self._precollect([self.starting_club_item])
        if club_scope == 1:
            pool_names.extend(
                club_item(name)
                for name in CLUBS
                if club_item(name) != self.starting_club_item
            )
        elif club_scope == 0:
            self._precollect(
                club_item(name)
                for name in CLUBS
                if club_item(name) != self.starting_club_item
            )
        # Retail uses the same six availability bits for regular Tournament
        # courses and Character Match courses. The default links both menus to
        # each shuffled regular Tournament item. The explicit all_courses
        # compatibility choice necessarily exposes both menus and precollects
        # all six regular items. Each physical course item also authorizes its
        # corresponding Star Tournament variant.
        starting_tournament_items = {
            tournament_item(name) for name in self.starting_tournament_names
        }
        if self.options.character_match_course_access.value == 0:
            starting_tournament_items.update(
                tournament_item(name) for name in REGULAR_TOURNAMENTS
            )
        self._precollect(sorted(starting_tournament_items))
        all_tournament_items = {
            tournament_item(name) for name in REGULAR_TOURNAMENTS
        }
        shuffled_tournaments = sorted(
            all_tournament_items - starting_tournament_items
        )

        categories = (
            (
                self.options.shuffle_custom_club_sets,
                [custom_club_set_item(name) for name in CUSTOM_CLUB_SETS],
            ),
            (
                self.options.shuffle_modes,
                [
                    mode_item(name)
                    for name in RANDOMIZABLE_MODES
                    if name != "Tournament"
                    if mode_item(name) not in start_modes
                ],
            ),
        )
        for shuffled, names in categories:
            if shuffled:
                pool_names.extend(names)
            else:
                self._precollect(names)
        if self.options.shuffle_tournaments:
            pool_names.extend(shuffled_tournaments)
            if self.early_course_safety_item is not None:
                if self.early_course_safety_item not in shuffled_tournaments:
                    raise ValueError(
                        "MGTT early-course safety item was not placed in the "
                        "shuffled Tournament pool"
                    )
                self.multiworld.early_items[self.player][
                    self.early_course_safety_item
                ] = 1
        else:
            self._precollect(shuffled_tournaments)
        self._precollect(sorted(start_modes))
        # Doubles, Club Slots, Match Play, and Skins Match are deliberately
        # outside the AP mode pool. Their published numeric IDs remain reserved
        # for old rooms, but new seeds must not place or precollect them.

        if self.options.shuffle_modes:
            pool_names.append(PUTTING_PRACTICE_MODE_ITEM)
        else:
            self._precollect([PUTTING_PRACTICE_MODE_ITEM])
        practice_child_items = (
            APPROACH_PRACTICE_DIFFICULTY_ITEMS
            + SHOT_PRACTICE_STAGE_ITEMS
        )
        if self.options.shuffle_modes:
            pool_names.extend(practice_child_items)
        else:
            self._precollect(practice_child_items)
        # Tournament access uses one AP item. Star Tournament is deliberately
        # left to retail progression after all six regular tournaments are
        # won. Legacy second-copy and Mode - Star Tournament IDs remain
        # loadable for old rooms/debugging but are not generated in new rooms.
        tournament_starts_owned = "Tournament" in self.starting_mode_names
        if self.options.shuffle_modes:
            if tournament_starts_owned:
                self._precollect([PROGRESSIVE_TOURNAMENT_MODE_ITEM])
            else:
                pool_names.append(PROGRESSIVE_TOURNAMENT_MODE_ITEM)
        else:
            self._precollect([PROGRESSIVE_TOURNAMENT_MODE_ITEM])

        if self.options.shuffle_advance_tour_golfers:
            pool_names.append(ADVANCE_TOUR_GOLFER_ITEM)
        else:
            self._precollect([ADVANCE_TOUR_GOLFER_ITEM])

        if self.options.shuffle_power_shots:
            # Retail behaves unstably when its four counters are initialized
            # to zero. The configured 1..9 starting capacity keeps the selector
            # valid; remaining progressive copies still reach the cap of nine.
            starting_capacity = self.options.starting_power_shot_capacity.value
            self._precollect([POWER_SHOT_ITEM] * starting_capacity)
            pool_names.extend([POWER_SHOT_ITEM] * (9 - starting_capacity))
        else:
            self._precollect([POWER_SHOT_ITEM] * 6)

        per_character_putters = self.options.putter_range_scope.value == 1
        if self.options.shuffle_short_game:
            if per_character_putters:
                self._precollect(self.starting_character_putter_range_items)
                starting_putters = set(
                    self.starting_character_putter_range_items
                )
                pool_names.extend(
                    item
                    for item in CHARACTER_PUTTER_RANGE_ITEMS
                    if item not in starting_putters
                )
            else:
                self._precollect([self.starting_putter_range_item])
                pool_names.extend(
                    item
                    for item in PUTTER_RANGE_ITEMS
                    if item != self.starting_putter_range_item
                )
            pool_names.append(APPROACH_SHOT_ITEM)
        else:
            self._precollect(
                CHARACTER_PUTTER_RANGE_ITEMS
                if per_character_putters
                else PUTTER_RANGE_ITEMS
            )
            self._precollect([APPROACH_SHOT_ITEM])

        if self.options.shuffle_putting_practice_difficulties:
            # Novice is the mode's baseline difficulty. Keep its published ID
            # reserved for old rooms, but new worlds shuffle only the two
            # upgrades; receiving Putting Practice itself grants Novice.
            pool_names.extend(PUTTING_PRACTICE_DIFFICULTY_ITEMS[1:])
        else:
            self._precollect(PUTTING_PRACTICE_DIFFICULTY_ITEMS[1:])

        spin_scope = self.options.spin_unlocks.value
        if spin_scope == 0:
            self._precollect(GLOBAL_SPIN_ITEMS)
        elif spin_scope == 1:
            pool_names.extend(GLOBAL_SPIN_ITEMS)
        else:
            pool_names.extend(CHARACTER_SPIN_ITEMS)

        location_count = len(self.multiworld.get_unfilled_locations(self.player)) - 1
        # One active location becomes the locked Victory event in set_rules.
        if len(pool_names) > location_count:
            per_character_putter_hint = (
                " Per-character putters add 36 randomized items; use global "
                "spins, disable another shuffled category, or increase "
                "starting unlock counts if the full catalog still cannot fit."
                if per_character_putters
                else ""
            )
            raise ValueError(
                f"MGTT has {len(pool_names)} progression items but only "
                f"{location_count} randomizable locations. Enable the expanded "
                "Ring Attack or per-character tournament checks, increase starting "
                "characters, or reduce shuffled categories."
                + per_character_putter_hint
            )

        filler_count = location_count - len(pool_names)
        mulligan_count = min(filler_count, MAX_MULLIGAN_FILLER)
        pool_names.extend(["Mulligan"] * mulligan_count)
        pool_names.extend(["Nothing"] * (filler_count - mulligan_count))

        self.multiworld.itempool += [self.create_item(name) for name in pool_names]

    def set_rules(self) -> None:
        rules.set_rules(self)

    def get_filler_item_name(self) -> str:
        return "Mulligan"

    def fill_slot_data(self) -> dict[str, Any]:
        starting_putters = (
            self.starting_character_putter_range_items
            if self.options.putter_range_scope.value == 1
            else [self.starting_putter_range_item]
        )
        stability_warnings: list[str] = []
        if self.options.spin_unlocks.value != 0:
            stability_warnings.append(
                "Shuffled spin inputs are experimental; use spin_unlocks: "
                "vanilla for the supported 1.0 ruleset."
            )
        if self.options.ring_shot_player_counts.value == 1:
            stability_warnings.append(
                "3P and 4P Ring Attack checks are experimental; 1P and 2P "
                "are the supported 1.0 player counts."
            )
        optional_check_groups = (
            (self.options.coin_shoot_checks, "Coin Attack"),
            (self.options.speed_golf_checks, "Speed Golf"),
            (self.options.practice_challenge_checks, "practice/challenge"),
            (self.options.congo_canopy_score_checks, "Congo Canopy score"),
        )
        enabled_optional_groups = [
            label for option, label in optional_check_groups if option.value
        ]
        if enabled_optional_groups:
            stability_warnings.append(
                "Optional check groups still need wider beta coverage: "
                + ", ".join(enabled_optional_groups)
                + "."
            )
        if self.options.character_match_course_checks.value:
            stability_warnings.append(
                "Per-course Character Match checks are experimental; Pro "
                "opponent wins are the supported 1.0 Character Match checks."
            )
        if self.options.native_popup_delivery.value == 1:
            stability_warnings.append(
                "Native in-game Archipelago popups are forced off for safety; "
                "messages will appear in the MGTT client window."
            )
        if self.options.enable_debug_commands.value:
            stability_warnings.append(
                "Debug commands are enabled and can permanently alter this room."
            )
        return {
            "protocol_version": 2,
            "starting_characters": self.starting_character_names,
            "starting_character_count": len(self.starting_character_names),
            "configured_starting_character_count": (
                self.options.starting_characters.value
            ),
            "starting_modes": self.starting_mode_names,
            "starting_mode_count": self.options.starting_modes.value,
            "starting_tournament_names": self.starting_tournament_names,
            "starting_tournament_count": len(self.starting_tournament_names),
            "early_course_safety_item": self.early_course_safety_item,
            "starting_equipment": [
                *(
                    self.starting_character_club_items
                    if self.options.shuffle_clubs.value in (2, 3)
                    else [self.starting_club_item]
                ),
                *starting_putters,
            ],
            # Both per-character generation choices use the same live bag
            # enforcement. Value 3 changes only the seed's precollected clubs.
            "club_scope": (
                2 if self.options.shuffle_clubs.value == 3
                else self.options.shuffle_clubs.value
            ),
            "putter_range_scope": self.options.putter_range_scope.value,
            # Before the selected-golfer name has appeared once, the client
            # exposes this one temporary safety club rather than leaving the
            # retail selector with only a putter or taking the union of all
            # per-character inventories.
            "fallback_club": self.starting_club_item.removeprefix("Club - "),
            "starting_putting_practice_items": self.starting_putting_practice_items,
            "putter_always_available": True,
            "base_putter_range_feet": int(
                self.starting_putter_range_item.removeprefix(
                    "Putter Range - "
                ).removesuffix(" Feet")
            ),
            "starting_power_shot_capacity": (
                self.options.starting_power_shot_capacity.value
                if self.options.shuffle_power_shots
                else 6
            ),
            "vanilla_power_shot_capacity": 6,
            "maximum_power_shot_capacity": 9,
            "stability_warnings": stability_warnings,
            "advance_tour_characters_included": True,
            "character_match_course_access": (
                self.options.character_match_course_access.current_key
            ),
            "regular_tournaments_precollected_for_character_match_courses": (
                self.options.character_match_course_access.value == 0
            ),
            "advance_tour_stat_profile": self.advance_tour_stat_profile,
            "advance_tour_golfer_distances": {
                "Neil": self.advance_tour_golfer_distances[0],
                "Ella": self.advance_tour_golfer_distances[1],
            },
            **self.options.as_dict(
                "shuffle_characters",
                "shuffle_star_characters",
                "shuffle_clubs",
                "shuffle_custom_club_sets",
                "shuffle_advance_tour_golfers",
                "advance_tour_golfer_stats",
                "shuffle_tournaments",
                "starting_tournaments",
                "shuffle_modes",
                "shuffle_power_shots",
                "shuffle_short_game",
                "putter_range_scope",
                "shuffle_putting_practice_difficulties",
                "spin_unlocks",
                "tournament_character_checks",
                "character_match_course_checks",
                "character_match_course_access",
                "ring_shot_player_counts",
                "individual_best_badge_checks",
                "coin_shoot_checks",
                "speed_golf_checks",
                "practice_challenge_checks",
                "congo_canopy_score_checks",
                "congo_canopy_score_to_par",
                "near_pin_aggregate_feet",
                "native_popup_delivery",
                "enable_debug_commands",
                "goal",
            ),
            # Native retail popups share a text constructor with score,
            # tournament-confirmation, save, and transition dialogs. Multiple
            # capture rounds proved that serialization and cooldowns cannot
            # make that ownership safe. Preserve the YAML option parser for
            # compatibility but force client-window delivery for 1.0 rooms.
            "native_popup_delivery": 0,
            # Older YAML files may still contain experimental_checks: true.
            # Explicitly serialize false so every matching client knows that
            # password-dependent Part D checks are absent from this seed.
            "experimental_checks": 0,
        }
