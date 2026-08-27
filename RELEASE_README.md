# Mario Golf: Toadstool Tour Archipelago 1.0.0 RC1

This package adds Archipelago multiworld progression to the USA GameCube
release of Mario Golf: Toadstool Tour. It does not contain the game.

## Included files

- `mgtt.apworld` — install this custom world through Archipelago Launcher.
- `MGTT-Archipelago-Patch-1.0.0-RC1.zip` — legal sparse patch and Windows/
  Python applicators. Supply your own clean ISO.
- `MGTT_1.0_Recommended.yaml` — recommended first-play settings.
- `MGTT_One_Club_Per_Golfer.yaml` — harder equipment-start alternative.
- `MGTT-PopTracker-1.0.0-RC1.zip` — optional visual tracker.
- `MGTT-1.0.0-RC1-Item-and-Location-Catalog.xlsx` — complete reference.
- `KNOWN_ISSUES.md` and `RELEASE_NOTES_1.0.0-rc1.md`.

## Required software and image

- Archipelago 0.6.7.
- Dolphin.
- A legally dumped, unmodified USA ISO with game ID `GFTE01`.
- ISO size: `1,459,978,240` bytes.
- ISO SHA-256: `08a1f0c1f7336418fa814a19907f2094d81062d5e7636ab096a43c41132410f0`.

The patcher checks all of these properties and refuses unknown images. Do not
distribute a clean or patched ISO.

## Quick start

1. Remove older MGTT APWorld files, then use Archipelago Launcher's
   **Install APWorld** action on the included lowercase `mgtt.apworld`.
2. Fully restart Archipelago Launcher.
3. Extract the patch ZIP and follow its `README.txt` to create a private
   patched ISO from your clean dump.
4. Copy `MGTT_1.0_Recommended.yaml` into Archipelago's `Players` folder, edit
   the player name, and generate the room locally.
5. Start the patched ISO in Dolphin.
6. Open **Mario Golf: Toadstool Tour Client**, connect to the room, and use the
   exact slot name from the YAML.

Detailed platform setup is in `mgtt/docs/setup_en.md` in the source archive and
in the repository wiki pages supplied with this release.

## Safety and support

Installed APWorlds execute code inside Archipelago. Download releases only
from the project's official repository and compare the supplied SHA-256 file.
When reporting a problem, include the version, platform, Dolphin version,
generated YAML, and `/mgtt_diagnostics <short-label>` output. Never post an ISO,
memory card containing personal data, server password, or unreviewed RAM dump.
