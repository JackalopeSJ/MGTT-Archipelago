from worlds.generic.Rules import set_rule

from .data import (
    ADVANCE_TOUR_GOLFER_ITEM,
    APPROACH_SHOT_ITEM,
    CHARACTER_MATCH_COURSE_LOCATIONS,
    CHARACTERS,
    CLUBS,
    GOAL_LOCATION_BY_VALUE,
    PER_CHARACTER_GOLFERS,
    PUTTER_RANGE_FEET,
    PUTTER_RANGE_ITEMS,
    WOODS,
    IRONS,
    WEDGES,
    character_club_item,
    character_item,
    character_putter_range_item,
    club_item,
)


def _requirements_rule(
    world,
    requires_all: tuple[str, ...],
    requires_any: tuple[str, ...],
    requires_counts: tuple[tuple[str, int], ...],
    requires_any_counts: tuple[tuple[str, int], ...],
    required_character: str | None,
    minimum_equipment_profile: str,
):
    player = world.player
    per_character_clubs = world.options.shuffle_clubs.value in (2, 3)
    per_character_putters = world.options.putter_range_scope.value == 1
    def has_golfer(state, character: str) -> bool:
        if character in CHARACTERS:
            return state.has(character_item(character), player)
        return state.has(ADVANCE_TOUR_GOLFER_ITEM, player)

    def has_equipment_profile(state, profile: str) -> bool:
        if profile == "none":
            return True

        def clubs_for(character: str | None) -> set[str]:
            if world.options.shuffle_clubs.value == 0:
                return set(CLUBS)
            if world.options.shuffle_clubs.value == 1:
                return {
                    club for club in CLUBS
                    if state.has(club_item(club), player)
                }
            assert character is not None
            return {
                club for club in CLUBS
                if state.has(character_club_item(character, club), player)
            }

        def putter_count(character: str | None) -> int:
            if world.options.putter_range_scope.value == 0:
                return sum(
                    state.has(item, player) for item in PUTTER_RANGE_ITEMS
                )
            assert character is not None
            return sum(
                state.has(
                    character_putter_range_item(character, feet), player
                )
                for feet in PUTTER_RANGE_FEET
            )

        def profile_ready(character: str | None) -> bool:
            owned = clubs_for(character)
            if profile == "couple":
                return len(owned) >= 2
            if profile == "two_putters":
                return putter_count(character) >= 2
            category_counts = tuple(
                len(owned.intersection(category))
                for category in (WOODS, IRONS, WEDGES)
            )
            if profile == "wood_putter":
                return category_counts[0] >= 1 and putter_count(character) >= 1
            if profile == "balanced":
                return all(count >= 1 for count in category_counts)
            if profile == "star_balanced":
                return (
                    character is not None
                    and character in CHARACTERS
                    and state.has(character_item(character), player, 2)
                    and all(count >= 1 for count in category_counts)
                )
            if profile == "expanded":
                return (
                    all(count >= 2 for count in category_counts)
                    and state.has(APPROACH_SHOT_ITEM, player)
                    and putter_count(character) >= 2
                )
            raise ValueError(f"Unknown equipment profile: {profile}")

        # Every equipment claim must belong to a golfer the slot can actually
        # select. This matters most for secret golfers and keeps global bags
        # from appearing usable before any corresponding golfer is owned.
        golfers = (
            (required_character,)
            if required_character
            else PER_CHARACTER_GOLFERS
        )
        return any(
            has_golfer(state, character) and profile_ready(character)
            for character in golfers
        )

    if not per_character_clubs and not per_character_putters:
        return lambda state: (
            state.has_all(requires_all, player)
            and (not requires_any or state.has_any(requires_any, player))
            and all(state.has(item, player, count) for item, count in requires_counts)
            and (
                not requires_any_counts
                or any(
                    state.has(item, player, count)
                    for item, count in requires_any_counts
                )
            )
            and has_equipment_profile(state, minimum_equipment_profile)
        )

    club_by_item = {club_item(club): club for club in CLUBS}
    putter_by_item = dict(zip(PUTTER_RANGE_ITEMS, PUTTER_RANGE_FEET))
    required_clubs = tuple(
        club_by_item[item]
        for item in requires_all
        if per_character_clubs and item in club_by_item
    )
    required_putters = tuple(
        putter_by_item[item]
        for item in requires_all
        if per_character_putters and item in putter_by_item
    )
    non_personal_requirements = tuple(
        item
        for item in requires_all
        if not (per_character_clubs and item in club_by_item)
        and not (per_character_putters and item in putter_by_item)
    )
    def has_usable_equipment(state) -> bool:
        if (
            not required_clubs
            and not required_putters
            and minimum_equipment_profile == "none"
        ):
            return True
        golfers = (
            (required_character,)
            if required_character
            else PER_CHARACTER_GOLFERS
        )

        return any(
            has_golfer(state, character)
            and all(
                state.has(character_club_item(character, club), player)
                for club in required_clubs
            )
            and all(
                state.has(
                    character_putter_range_item(character, feet), player
                )
                for feet in required_putters
            )
            for character in golfers
        )

    return lambda state: (
        state.has_all(non_personal_requirements, player)
        and (not requires_any or state.has_any(requires_any, player))
        and all(state.has(item, player, count) for item, count in requires_counts)
        and (
            not requires_any_counts
            or any(
                state.has(item, player, count)
                for item, count in requires_any_counts
            )
        )
        and has_usable_equipment(state)
        and has_equipment_profile(state, minimum_equipment_profile)
    )


def set_rules(world) -> None:
    for name, data in world.active_locations.items():
        requires_all = data.requires_all
        if (
            name in CHARACTER_MATCH_COURSE_LOCATIONS
            and world.options.character_match_course_access.value == 0
        ):
            # all_courses is enforced by the bridge independently of received
            # Tournament items. Mirror that choice in AP logic so these six
            # checks are not logically stranded behind unrelated progression.
            requires_all = tuple(
                item
                for item in requires_all
                if not item.startswith("Tournament - ")
            )
        set_rule(
            world.multiworld.get_location(name, world.player),
            _requirements_rule(
                world,
                requires_all,
                data.requires_any,
                data.requires_counts,
                data.requires_any_counts,
                data.required_character,
                data.minimum_equipment_profile,
            ),
        )

    goal_name = GOAL_LOCATION_BY_VALUE[world.options.goal.value]
    goal_location = world.multiworld.get_location(goal_name, world.player)
    goal_location.place_locked_item(world.create_event("Victory"))
    world.multiworld.completion_condition[world.player] = (
        lambda state: state.has("Victory", world.player)
    )
