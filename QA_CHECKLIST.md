# Release QA

`RELEASE_CHECKLIST_1.0.0_RC1.md` is the authoritative promotion checklist.
This file defines the broader regression suite for later maintenance releases.

## Automated requirements

- Compile all APWorld, client, patcher, PopTracker, and test source.
- Run the full suite against the supported Archipelago 0.6.7 source tree.
- Run the supported option matrix, every bundled YAML, restrictive fill, and
  all-state reachability/goal checks.
- Preserve every published item and location ID, including retired IDs.
- Validate the APWorld container, lowercase filename, manifest version, and
  packaged `GFTE01` address map.
- Regenerate the protocol header without a diff and compile the reference C
  protocol with warnings treated as errors.
- Verify deterministic APWorld, PopTracker, patch, source, and release ZIPs.
- Scan every public archive for disc images, captures, diagnostics, saves,
  credentials, and temporary caches.

## Core controller smoke test

Use `MGTT_1.0_Recommended.yaml` and a dedicated memory card.

1. Launch the MGTT client from Archipelago and connect to the patched game.
2. Confirm an owned golfer advances and a locked golfer is denied.
3. Confirm owned modes/courses advance and locked selections are denied.
4. Receive base/Star golfer stages, a golfer-specific club, a putter range,
   Approach Shot, Power Shot Capacity, a physical course, and a mode.
5. Confirm the active golfer receives only their equipment and can use a new
   club on the next ordinary shot.
6. Confirm Power Shots retain on a perfect execution and decrement on a miss.
7. Complete a regular Tournament, Star Tournament, 1P Ring Attack, 2P Ring
   Attack, and Pro Character Match; confirm the correct checks and persistence.
8. Confirm Ring Attack reveals the next course only after all six retail levels
   on the current course are clear.
9. Spend a Mulligan, reconnect, and confirm the spent inventory remains spent.
10. Connect the PopTracker and confirm received golfers, Stars, equipment,
    modes, courses, and completed locations synchronize after reconnect.

## Optional-package smoke tests

- Coin Attack: live 100-coin and 75-coin+birdie checks plus a settled 500-coin
  per-golfer total.
- Speed Golf: follow the focused positive/negative RC checklist.
- Practice: Putting/Approach difficulties, three Shot Practice stages, and
  Birdie Challenge Front 9.
- Congo Canopy: Front 9 target only.
- Near-Pin: saved aggregate target.

Native popup delivery, shuffled spin, 3P/4P Ring Attack, special/password
modes, and retired long-round checks are outside the supported 1.0 boundary.
