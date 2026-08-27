from BaseClasses import Region

from .data import ALL_LOCATION_DATA, LOCATION_NAME_TO_ID
from .locations import MGTTLocation


REGIONS = (
    "Menu",
    "Practice Range",
    "Tournament",
    "Star Tournament",
    "Character Match",
    "Ring Attack",
    "Speed Golf",
    "Coin Attack",
    "Side Games",
    "Accomplishments",
)


def create_regions(world) -> None:
    regions = {name: Region(name, world.player, world.multiworld) for name in REGIONS}
    world.multiworld.regions.extend(regions.values())

    for region_name in REGIONS[1:]:
        regions["Menu"].connect(regions[region_name])

    for name, data in world.active_locations.items():
        regions[data.region].locations.append(
            MGTTLocation(world.player, name, LOCATION_NAME_TO_ID[name], regions[data.region])
        )
