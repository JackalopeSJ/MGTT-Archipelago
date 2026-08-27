# Mario Golf: Toadstool Tour Archipelago

This is a revision-locked 1.0 release candidate for the NTSC-U GameCube release
(`GFTE01`). It includes an Archipelago world, a source-ISO patcher, and a
Dolphin bridge for macOS/Windows/Linux.

The supported 1.0 boundary uses client-window notifications, vanilla spin,
and 1P/2P Ring Attack. Rooms that enable experimental settings receive a clear
warning in the MGTT client when the slot authenticates.

## World model

- 458 defined item IDs and 477 location IDs. Previously published IDs for
  non-character items and locations remain stable; retired star-item IDs are
  intentionally unused.
- 164 unconditional core locations, six separately configurable Character
  Match course-win locations, 108 default per-hole Best Badge locations, 72
  optional 2P–4P Ring Attack checks, and 16 optional tournament-win-per-golfer
  checks.
- A YAML-configurable random starting roster of 1–16 native golfers. The
  capture-verified native guard independently checks base and Star permissions;
  locked/owned golfer denial and progression are controller-confirmed.
- A separately shuffled Neil-and-Ella pair backed by a byte-exact captured
  retail transfer record. Renamed identity, native cursor values, first-tee
  play, per-character equipment, unlock, and reload persistence have been
  controller-confirmed on the supported dedicated-card workflow.
- YAML-selected AP-created Neil/Ella driving profiles: Weak at 205/200 yards,
  Standard at 305/300 yards (default), Overpowered at 405/400 yards, or a
  seed-resolved Random choice among those three. Genuine transferred-golfer
  stats on populated cards remain untouched.
- Two copies of `Progressive <Golfer> Unlock` for every native golfer. The
  first copy grants the base golfer and the second grants that golfer's Star
  form. This includes Boo, Bowser Jr., Petey Piranha, and Shadow Mario.
- All 13 standard non-putter clubs, either global or shuffled separately for
  all 16 native golfers plus Neil and Ella. The putter itself is always available. Global mode
  starts with one random club; per-character mode starts every golfer with one
  independently randomized club. The captured character/setup name is retained
  into the round, so per-character bags apply correctly on zero-based hole 1.
- All 15 custom club sets transferable from Mario Golf: Advance Tour.
- Tournament courses and game modes. Mode shuffling starts with 1–3
  randomly selected modes so a shuffled seed always has a playable route.
  `starting_tournaments` chooses 1–6 random regular courses to precollect and
  defaults to one; every other physical course remains an Archipelago item.
  Each physical-course item authorizes the matching course in both regular and
  Star Tournament.
  Because retail shares regular-course access between Tournament and Character
  Match, `character_match_course_access: all_courses` precollects the six
  regular Tournament items. The new default, `follow_tournament_items`, links
  each Character Match course to its corresponding regular Tournament item.
  Doubles, Club Slots, and Training remain local. Match Play and Skins Match
  were retired because they are not Toadstool Tour modes; their numeric IDs
  remain reserved for compatibility.
  Tournament access is one progression item covering the complete Tournament
  feature. The integrated game hook exposes both Tournament menus, while the
  same six physical-course items gate their matching regular and Star events.
  The six former Star-event item IDs are retained only for older rooms.
- Progressive Power Shot capacity is enabled by default, starts at a
  YAML-selected value from 1–9 (default 6), and places exactly enough
  additional copies to reach nine.
- Stackable, single-use Player 1 Mulligans fill otherwise-unused item
  locations, up to 99 copies. Spent copies are persisted through Archipelago
  DataStorage. Supported 1.0 configurations therefore generate no `Nothing`
  items.
- Optional 30-foot, 100-foot, and 200-foot putter-range items plus Approach
  Shot. One putter range is precollected in shuffled seeds.
- Putting Practice plus separate Novice, Intermediate, and Expert difficulty
  items. Practice checks require the matching received access items.
- Checks for each tournament, every 1P Ring Attack level, Pro-difficulty wins
  against all 16 native Character Match opponents, Character Match wins on all
  six courses, requested shot/round feats, optional
  tournament wins per golfer, and optional 2P–4P Ring Attacks.
- Tournament placement checks include a Top 3 finish for each of the six
  regular and six Star tournaments, plus one early check for finishing any
  tournament regardless of placement.
- Ring Attack courses follow retail progression rather than AP course items:
  clearing all six levels on one course reveals the next, and confirmed AP
  clears restore those native records after reconnecting.
- Fifty-four always-available golfer/course accomplishments: birdie or better
  with each of the 18 supported golfers, an 18-hole score of -7 or better with
  each golfer, and birdie-or-better on every par 3, par 4, or par 5 on each
  regular course during an 18-hole Tournament or Stroke Play round.
- Optional Coin Attack checks: the global and per-course 100-coin-hole and
  75-coin-birdie checks report live. Quick Cash and Cash Cup results also add
  to separate seed-persistent 500-coin totals for each native golfer.
- Optional capture-backed Speed Golf checks for finishing each of the six
  courses under 10 minutes, any hole under 15 seconds, and a round under 15
  minutes while also finishing under par.
- A capture-backed Near-Pin aggregate-distance check. The YAML
  `near_pin_aggregate_feet` value applies to the best saved Front 9, Back 9,
  or All 18 result.
- Optional clears for Novice, Intermediate, and Expert Putting and Approach
  Practice; Tee Shot, Second Shot, and Trouble Shot Practice; and Birdie
  Challenge Front 9. The published Birdie Back 9/All 18 IDs remain reserved
  but are excluded from new worlds until their result readers are captured.
- Optional Congo Canopy Front 9 Stroke Play score check using the YAML
  score-to-par target. Previously published Back 9/All 18 IDs are retained but
  retired from new worlds.
- Goal choices for first place in all six regular and all six Star
  Tournaments, all 16 Pro Character Match opponents, all 36 single-player Ring
  Attacks, or all three complete categories. All Tournaments is the default.

## Integration status

| Feature | Current status |
|---|---|
| Native incoming-item text | Disabled for 1.0 after repeated retail dialog-pointer crashes; receipts and checks remain immediate in the MGTT client window |
| macOS Dolphin connection | Live-tested through Dolphin's GDB stub |
| Windows connection | Live-tested through `dolphin-memory-engine` |
| Linux connection | Implemented through `dolphin-memory-engine` |
| Golfer and Tournament access | Ordinary golfers and six physical courses use independent native permission guards; each course grants both regular and Star Tournament variants, and hidden golfer presentation/course-list flags remain synchronized |
| Standard club set | Runtime limiter synchronized; putter always enabled |
| Per-character standard clubs | All 234 native/Advance Tour golfer-club items modeled; custom Joshy/Sally-style names resolve to Neil/Ella roles and remain identified through hole 1 |
| Coin Attack checks | Settled Quick Cash/Cash Cup round totals are session-attributed and accumulated separately per golfer/variant; live 100-coin-hole and 75-coin-birdie feats remain available |
| Speed Golf checks | Six under-10-minute course checks, a live 900-frame/15-second hole latch with saved-round fallback, and a live under-15/under-par check |
| Near-Pin | Configurable aggregate-distance check reads the three retail Front 9/Back 9/All 18 leaderboards |
| Practice/Birdie Challenge clears | All six Putting/Approach and all three Shot Practice readers implemented; Birdie Front 9 implemented; Back 9/All 18 pending |
| Congo Canopy Stroke Play | Front 9 threshold implemented; Back 9/All 18 historical IDs retired |
| Putter ranges and Approach Shot | Desktop gate plus native per-frame putter-length enforcement |
| Putting Practice and difficulties | Mode and Novice/Intermediate/Expert access synchronize independently; controller-confirmed |
| Global/per-golfer spin items | Item model remains available for development, but shuffled spin enforcement is outside the supported 1.0 boundary; use vanilla spin |
| Per-golfer putter ranges | Default supported scope; one random starting range and two shuffled ranges for each of 18 golfers |
| Progressive Power Shot capacity, 1–9 | Tournament/Stroke Play capacity and retail perfect-shot retention are controller-confirmed; non-capacity modes keep retail behavior |
| Mulligans | Native Player 1 counter plus server-persisted consumption implemented; receipt, Tournament use, and continued use after spending are controller-confirmed, with restart reconciliation still opportunistic |
| Regular/star tournament first-place checks | Read across all 40 rows of each retail table; the Yoshi/Lakitu capture proves native rows begin at 14 |
| Optional tournament win per golfer | Uses the controller-confirmed round golfer latch, a live result-table transition fallback, and final-score recovery; it never infers the golfer from an unchanged persistent row |
| All 36 single-player Ring Attack checks | Read from retail save records |
| Character Match opponent checks | Sixteen native opponent-result rows provide Pro-difficulty victory locations; persistence and a Pro win were controller-confirmed; invitations and Star awards are local-only and never complete AP checks |
| Hole-in-one, eagle, albatross, birdie, chip-in, pin hit | Hole-in-One, Eagle, Birdie, Chip-In, and Hit the Pin are controller-confirmed; Albatross identity is corrected and awaits opportunistic confirmation |
| Five consecutive birdies | Edge-tracked from live hole results |
| Bunker chip-in | Live chip-in result plus tracked sand lie |
| Bogey-free, ten-under, and under-par-per-course rounds | Edge-tracked from live hole and round-finish results |
| Game modes | The native guard denies locked shuffled modes while leaving Doubles, Club Slots, and Training local; mode access is controller-confirmed |
| Character Match course wins | A new opponent-result edge is attributed to the active regular course; focused acceptance remains |
| 2P–4P Ring Attacks | The default includes 2P; the opt-in full package adds 3P/4P. P1 uses the AP bag while P2–P4 intentionally retain full bags for 1.0 stability. |
| Password/code-only modes | Part D is deferred; all related locations are excluded from generated worlds even when an old YAML requests them |
| Advance Tour golfers/custom club sets | Part C is controller-verified: byte-exact Neil/Ella injection, Standard and Overpowered YAML profiles, cursor 16/17 identity, first-tee play, per-golfer club isolation, corrected custom-set masks, native X selection, save, and restart persistence. Strict progression supports a fresh/dedicated card; arbitrary third-party transfer profiles are out of scope |
| Advance Tour golfer stat profile | Generated slot data resolves Weak 205/200, Standard 305/300, Overpowered 405/400, or Random once per seed; the client applies it only to AP-created Neil/Ella records |
| Reused save handling | Seed/slot-specific DataStorage baseline suppresses persistent results that predate the seed; the client preserves the RoomInfo seed namespace on Archipelago 0.6.7 |
| Hook calibration | Read-only `/mgtt_capture <label>` command writes compressed Dolphin RAM snapshots to the Archipelago log folder; `/mgtt_diagnostics <label>` writes sanitized client/slot/bridge state without a RAM dump |
| Remaining transient feats | 50-foot putt, tee-only 300-yard drive, 100-yard hole-out, perfect Power Shot, match-margin and practice putts are live-tracked |
| Club inventory text | `/clubs [golfer]` accepts friendly spellings and answers immediately in the MGTT client window |
| All-Tournament/all-Pro-match/all-1P-Ring/all-three goals | All four are controller-confirmed and client-derived from all 12 durable first-place records, all 16 Pro opponent checks, and all 36 saved 1P Ring Attack clears; Bowser alone is not a goal |

Per-character standard clubs are now the default. The default option set also
enables 1P and 2P Ring Attack locations by default; the opt-in full package
adds 3P and 4P so the larger item pool can accommodate expanded settings. The
default begins with four random native golfers, six Power Shots plus three
capacity upgrades in the item pool, per-character putter ranges, and one random
regular course. The default and complete YAMLs
shuffle six physical courses shared by regular and Star Tournament and keep
deferred Part D checks off. For
compatibility, the old `experimental_checks` key is still accepted, but the
world serializes it as false and never activates those locations.

Player-facing presets are included under `examples/`:

- `MGTT_1.0_Recommended.yaml`: recommended four-golfer tour; every golfer begins
  with one wood, one iron, one wedge, and a putter.
- `MGTT_One_Club_Per_Golfer.yaml`: harder alternative with one
  random standard club and a putter per golfer.
- `MGTT_Standard_Tour.yaml`: compact four-golfer, per-character-club tour.
- `MGTT_Short_Tour.yaml`: every base golfer/course starts open, with only 1P
  Ring Attack progression and fewer access-item delays.
- `MGTT_Complete_Tour.yaml`: every supported 1.0 item/location category, with
  development cheats disabled. Per-character putters remain a separate
  alternate preset because the full putter and spin catalogs cannot both fit.

`enable_debug_commands` is off by default. The complete/expanded development
profiles turn it on so `/mgtt_debug_item` and `/mgtt_debug_check` can exercise
normal server item/check paths. Public release rooms should leave it false.
In those dedicated rooms, `/mgtt_debug_loadout <golfer>` requests every
missing standard club, all three putter ranges, and Approach Shot as real
server-delivered items so capture work is not blocked by a one-club bag.

The progressive-character masks, item model, Advance Tour record injection,
result readers, save-table readers, and public presets have automated coverage.
Native controller behavior has also been exercised in extended multiplayer
testing. The remaining experimental options are deliberately outside the
recommended public configuration and are announced by the client when enabled.

Part D (One-On One-Putt, Hole-in-One Contest, and Password Tournaments) is
deferred until after 1.0. Its historical IDs/readers remain reserved in source,
but no player seed can activate the locations in this release.

Trap items are likewise unavailable in 1.0: there is no trap YAML option, no
trap slot-data setting, and no generated trap item. The historical `Bogey Trap`
ID remains reserved solely so previously published numeric IDs never move.
Gale Force Winds and other trap designs remain 1.1 work.

See `DEVELOPMENT_STATUS.md` for the exact completion boundary and the evidence
needed to finish the remaining reverse-engineering-dependent features.

## Supported image

```text
Game ID: GFTE01
Size:    1,459,978,240 bytes
SHA-256: 08a1f0c1f7336418fa814a19907f2094d81062d5e7636ab096a43c41132410f0
```

The patcher verifies both the full image and `main.dol`, refuses unknown
revisions, and never overwrites its input.

## Build and patch

Build the APWorld:

```sh
python3 tools/build_apworld.py
```

Build every deterministic release artifact:

```sh
python3 tools/build_release.py
```

The preferred release artifact is the sparse `.mgttpatch` plus its
PowerShell/Python applicators. It contains only verified replacement ranges and
creates a private patched copy from the exact supported legal dump. Exact patch
size and output hash are regenerated for each release.

For development, the source patcher can create the same output directly:

```sh
python3 tools/patch_iso.py "/path/to/Mario Golf - Toadstool Tour (USA).iso" \
  "/path/to/MGTT-Archipelago.iso" --profile roster
```

Do not distribute an original or patched disc image. Every player must supply
their own exact legal dump and create a private patched copy.

See `mgtt/docs/setup_en.md` for Dolphin/client setup and
`mgtt/docs/protocol.md` for the memory contract.

See `ROADMAP_TO_1.0.md` for the phased Codex/human ownership plan and
`COMPLETE_CAPTURE_CHECKLIST_TO_1.0.md` for the non-duplicative remaining
capture and controller-test requests.

## License

The original code in this package is MIT licensed. Mario Golf, Nintendo
GameCube, and all game assets are property of their respective owners.
