# Known limitations — 1.0.0 RC1

The recommended YAML avoids every known unstable option.

- Native in-game Archipelago receipt popups are disabled. They can collide
  with retail result/save dialogs and cause invalid memory reads. The MGTT
  client displays received items and completed checks immediately.
- Spin is supported only with `spin_unlocks: vanilla`. Shuffled spin options
  remain parseable for development but are not part of the 1.0 support boundary.
- 3P and 4P Ring Attack are experimental. The recommended package enables 1P
  and 2P only. In multiplayer Ring Attack, Player 1 uses the AP bag while later
  local players retain unrestricted bags for stability.
- Some Ring Attack clears can display Shadow Mario's unlock graphic. The AP
  check and persistence are correct; this is cosmetic.
- Custom Advance Tour club selection can remain hidden until the supported
  Neil/Ella transfer state exists.
- Locked golfers remain visible and denial does not always play the intended
  unavailable sound. Use the PopTracker to see ownership clearly.
- The 300-yard-drive location is retired because it produced both false
  positives and missed real drives.
- Birdie Challenge Back 9/All 18 and Congo Canopy Back 9/All 18 AP checks are
  retired. Birdie Front 9 and Congo Front 9 are the supported checks.
- Speed Golf checks are optional and awaiting the final RC1 field test.
- Coin Attack totals are committed when a round settles or is exited; a
  cumulative 500-coin check may therefore appear at round exit rather than the
  instant the threshold is crossed.
- Use a fresh or dedicated memory card. Existing Advance Tour transfer data is
  preserved and can bypass the strict AP Neil/Ella presentation gate.
- The supported image is the exact USA `GFTE01` ISO documented in the setup
  guide. Other regions, revisions, RVZ files, and modified images are rejected.
