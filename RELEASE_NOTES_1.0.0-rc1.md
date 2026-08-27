# Mario Golf: Toadstool Tour Archipelago 1.0.0 RC1

This is the release candidate for the first broadly playable MGTT Archipelago
release. All four goal choices have been completed successfully in controller
testing. RC1 keeps the stable 0.9.57 game hook and concentrates the final
changes in world logic, packaging, and documentation.

The RC APWorld manifest uses world version `0.99.0`. The final artifact will
use `1.0.0`, ensuring Archipelago reliably replaces RC1 when the same source is
promoted after the Speed Golf test.

## Release-candidate changes

- Ring Attack logic now matches the game: courses reveal sequentially after
  clearing all six levels on the previous course. Physical AP course items no
  longer appear as logical requirements for Ring Attack checks or its goal.
- The ten arbitrary Neil/Ella 1/3/6/9/18-hole checks are retired from new
  rooms. Their numeric IDs and client reader remain reserved for compatibility.
- The recommended YAML starts four golfers with one random wood, iron, wedge,
  and putter, three modes, one physical course, six Power Shots, per-golfer
  putter ranges, vanilla spin, and 1P+2P Ring Attack checks.
- Release packaging now uses the canonical lowercase `mgtt.apworld` filename,
  includes reproducible patching tools and source, and contains no disc image.
- Player documentation, known limitations, wiki pages, release checklist,
  PopTracker metadata, and the complete item/location catalog are refreshed.

## Confirmed release systems

- Progressive base/Star golfers, including all four secret golfers.
- Mode, physical-course, club, putter-range, Approach Shot, custom-club-set,
  Neil/Ella, Power Shot capacity, and Mulligan items.
- Regular and Star Tournament placements and victories.
- 1P and 2P Ring Attack checks and persistent retail course progression.
- Pro Character Match checks and goal.
- All Tournaments, all Pro matches, all 1P Ring Attacks, and All Three goals.
- PopTracker item, location, roster, and Star-golfer synchronization.

## Final RC acceptance item

Speed Golf remains optional and disabled in the recommended YAML. Before RC1
is promoted unchanged to 1.0.0, perform the focused positive/negative Speed
Golf test in `RELEASE_CHECKLIST_1.0.0_RC1.md`. A failure does not block the
core release; the package can keep Speed Golf disabled and label it
experimental in 1.0.0.
