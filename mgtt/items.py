from __future__ import annotations

from BaseClasses import Item, ItemClassification

from .data import (
    COURSES,
    GAME,
    ITEM_NAME_TO_ID,
    PROGRESSIVE_TOURNAMENT_MODE_ITEM,
)


class MGTTItem(Item):
    game = GAME


def classification(name: str) -> ItemClassification:
    if name == "Victory":
        return ItemClassification.progression
    # These unlock entire menus or physical courses and therefore expose the
    # largest portions of MGTT's location graph. The combined flags tell
    # Archipelago that they are both logically required and especially useful,
    # rather than ordinary quality-of-life upgrades.
    if (
        name in COURSES
        or name == PROGRESSIVE_TOURNAMENT_MODE_ITEM
        or name.startswith("Mode - ")
    ):
        return ItemClassification.progression | ItemClassification.useful
    if name == "Advance Tour Golfers - Neil & Ella":
        return ItemClassification.progression
    if name.startswith(
        (
            "Progressive ",
            "Tournament - ",
            "Putter Range - ",
            "Putting Practice Difficulty - ",
            "Approach Practice Difficulty - ",
            "Shot Practice Level - ",
            "Birdie Challenge Level - ",
            "Spin - ",
        )
    ) or name in {"Power Shot Capacity", "Approach Shot"}:
        return ItemClassification.progression
    if name.startswith("Club - "):
        club = name.rsplit(" - ", 1)[-1]
        if club in {"1W", "7I", "PW"}:
            # These three clubs are the common long/mid/short equipment gates
            # for Tournament, Ring Attack, and broad accomplishment logic.
            return ItemClassification.progression | ItemClassification.useful
        return ItemClassification.progression if club in {
            "3W", "4W", "SW",
        } else ItemClassification.useful
    if name.startswith("Custom Club Set - "):
        return ItemClassification.useful
    if name in {"Mulligan", "Power Shot Refill"}:
        return ItemClassification.useful
    if name == "Bogey Trap":
        return ItemClassification.trap
    return ItemClassification.filler


def create_item(name: str, player: int) -> MGTTItem:
    return MGTTItem(name, classification(name), ITEM_NAME_TO_ID[name], player)
