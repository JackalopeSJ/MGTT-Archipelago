# Development Status

> **Historical engineering log:** this file preserves capture findings and
> superseded release-candidate notes. It is not the current player-facing
> support matrix. Use `README.md`, `RELEASE_README.md`, and `KNOWN_ISSUES.md`
> for the supported 1.0 boundary.

> **August 11 0.9.20 RC:** the later Mario Ring Attack capture proves that 1P
> progress is a 24-golfer by six-course table beginning at `SAVE_BASE +
> 0x894`; the previous address was golfer row 16 rather than a global table.
> The client now ORs every golfer row when finding checks, then mirrors only
> server-confirmed checks across all rows after fresh native progress has been
> submitted. The same update restricts selected-golfer identity to the actual
> character-select overlay, applies course gating to Stroke Play, moves the
> Star Tournament presentation entitlement into the final capture-supported
> player row, and restores the retail Character Match Star shadow before mode
> selection can construct invitations. Ring Attack attribution/restoration and
> club identity have automated coverage; Star Tournament, invitation timing,
> final Power behavior, and popup-to-menu transitions still require controller
> acceptance.

> **August 11 0.9.19 RC:** the clean retail Power captures resolve the shared
> non-putter selector as `0 = Power`, `1 = Normal`, and `2 = Approach`.
> Previous clients wrote zero as their Normal fallback, directly causing the
> forced-Power/zero-capacity sound failure. The fallback is now one. This RC
> also adds a non-player Star Tournament UI entitlement, isolates AP Stars
> from retail Character Match invitations, translates compact course cursors,
> restores checked Ring Attack flags after restart, accepts the captured tee-lie
> value for 300-yard drives, lets the putter skip a locked middle range, and
> moves diagnostic capture reads off the client event loop. Locked native
> icons remain visible by design; arbitrary holes in retail's default roster
> table would invalidate cursor mapping and are deferred until after 1.0.

> **August 11 0.9.18 roster hotfix:** the owned-Koopa pair proves the roster
> guard executed once and allowed cursor 5. The retail selected count changed
> from 0 to 1 and its target at `0x8044B018` remained 1, yet the menu entered
> the 2P/3P/4P/CPU chain. The guard had preserved CR/LR and r3-r31 but not r0;
> r0 therefore held the BL return address at the following retail `cmpw`
> instead of the target count. Both roster return paths now save and restore
> r0 explicitly. No additional address capture is required.

> **August 10 0.9.17 follow-up:** the latest locked-Koopa pair identified a
> second one-player roster commit at `0x8040C448`; the next combined build
> guards it alongside `0x8040BE58`. A delayed AP Star observation that falsely
> awarded Star Petey and Lakitu Valley is now ignored outside a confirmed
> Character Match. A4 Neil/Ella, B1 main modes, and B2 Side Games are
> controller-confirmed; A2 and the A3 false-check case await one narrow retest.

> **Tournament availability follow-up:** C1 confirms the exact course guard:
> Sands Classic is owned/playable while visible Lakitu Cup is denied. All
> twelve course items remain shuffled. New rooms require at least one starting
> regular Tournament item (`starting_tournaments: 1..6`), ensuring Tournament
> mode is never received with no playable regular course.

This file distinguishes the generated Archipelago model from gameplay features
that have been verified against the NTSC-U (`GFTE01`) executable and save data.

**Version 0.9.4 is withdrawn. Version 0.9.11 is a focused controller-probe
release.** It isolates roster, main-mode, Putting-difficulty, spin, and
zero-capacity Power mutations into separately identified images. It is not a
competitive release.

The YAML/world model can generate randomized starting items, but that fact does
not by itself hide retail-default characters or prevent entry into a locked
mode. Those behaviors require separate native executable hooks.

## Implemented

- Two-copy progressive unlocks for all 16 native golfers. Copy one sets the
  base-golfer bit and copy two sets the Star-golfer bit.
- Incoming-item and completed-check messages display immediately in the
  desktop client. Native item notices optionally use strictly serialized
  delivery; redundant completed-check native messages are suppressed.
- Standard non-putter club gating; the putter remains available and one
  seed-randomized standard club is guaranteed at seed start.
- Optional per-character club gating for all 13 standard clubs and all 16
  native golfers. Every golfer starts with one independently randomized club;
  the captured selected-golfer name is retained into zero-based hole 1 and the
  rest of the round. Before an identity is available, the limiter uses the
  intersection of every bag instead of exposing their union.
- `/clubs [golfer]` reports current ownership in the client and through the
  native popup. Friendly spellings such as `Diddy`, `Diddy_Kong`, and
  `DiddyKong` resolve correctly. Offline commands no longer create stale
  popups when Dolphin reconnects.
- The desktop window is titled `Archipelago Mario Golf: Toadstool Tour Client`.
  `/mgtt_status`, `/mgtt_inventory`, `/mgtt_messages`, and
  `/mgtt_diagnostics` expose bridge, inventory, queue, and sanitized support
  state. The client warns when more than one MGTT APWorld is installed.
  Queue state and connection transitions print explicit MGTT game
  connected/disconnected messages.
- Doubles, Club Slots, and Training are purely local. Match Play and Skins
  Match are not Toadstool Tour modes. All four retired AP item IDs remain
  reserved, but new seeds neither place nor precollect them and the client
  filters them from old received-item lists.
- Forty-six opt-in Coin Attack locations are modeled: separate 500-coin
  cumulative totals for Quick Cash and Cash Cup for all 16 native golfers,
  global and per-course 100-coin holes, and global and per-course 75-coin
  birdies. The client reports the feats from the capture-verified live result
  title and per-hole counter, and atomically persists cumulative settled
  results in seed/team/slot/golfer-specific Archipelago DataStorage counters.
- Eight opt-in Speed Golf locations are active: each course under 10 minutes,
  any hole under 15 seconds, and a round under 15 minutes and under par. The
  July 30 start/ten-second pair maps the live hole counter at `0x80523E30` to
  NTSC frames; a sub-900-frame candidate now reports on the scoring edge while
  the saved last-round table remains a fallback. The
  six published under-15 course IDs remain reserved and retired.
- One Near-Pin aggregate-distance location reads the retail Front 9, Back 9,
  and All 18 leaderboards. `near_pin_aggregate_feet` sets the maximum total
  distance in feet.
- Twelve opt-in practice/challenge locations are active: Novice,
  Intermediate, and Expert clears for Putting and Approach Practice; Tee Shot,
  Second Shot, and Trouble Shot clears for Shot Practice; and Front 9 in
  Birdie Challenge. All six Putting/Approach and all three Shot readers are
  implemented. Birdie Back 9/All 18 remain generated in the 0.9.20 capture RC
  so their final persistent values can be mapped; they will be implemented or
  disabled before 1.0. The three previously published but incorrect Shot
  Practice difficulty names remain reserved and are excluded from new worlds
  so their IDs cannot move.
- The opt-in Congo Canopy Front 9 Stroke Play score location uses live
  mode/course/start-hole/round-length/score identity and
  `congo_canopy_score_to_par`. Published Back 9/All 18 IDs remain reserved but
  are retired from new worlds.
- 30-foot, 100-foot, and 200-foot putter-range gating and Approach Shot gating;
  shuffled seeds precollect one putter range.
- Global and per-golfer spin item generation and permission masks.
- Progressive Power Shot inventory counts from one through nine, with a
  YAML-selected 1–9 starting capacity (default six), and the Archipelago-side
  capacity model.
- Stackable, single-use Player 1 Mulligans backed by the retail Mulligan
  counter. Consumption is persisted in Archipelago DataStorage so reconnecting
  or restarting cannot duplicate spent copies. Generation caps the pool at 99;
  every otherwise-empty slot in supported 1.0 configurations is a Mulligan.
- Regular and Star Tournament first-place checks from the full 40-row retail
  save tables. The August 6 Yoshi/Lakitu capture proves native golfer row 22
  and the 14-row prefix used to map all 16 native golfers.
- Optional tournament-win-per-golfer checks from the same corrected rows.
- All 36 single-player Ring Attack checks from retail save records.
- All 72 optional 2P, 3P, and 4P Ring Attack checks from retail save records.
- All 16 native Character Match Star checks are modeled. The August 5 paired
  letter-visible/letter-consumed captures disprove the old result-flag table:
  only the two-byte Star-golfer mask records the completed match. The client
  now samples that mask before restoring AP inventory and reports only newly
  rising character bits. The captured cycle was retail's first invitation,
  Star Koopa Troopa; its `0x0020` bit also proves that the Star mask follows
  character-select order rather than the separate internal golfer order.
- Live hole-in-one, eagle, albatross, birdie, chip-in, bunker chip-in, pin-hit,
  and five-consecutive-birdies checks. The native hook latches Hit the Pin in
  the same frame so desktop polling cannot miss it.
- Bogey-free, ten-under, and under-par-per-course round checks.
- Fifty-four 1.0 golfer/course accomplishments are modeled and live-read:
  birdie or better with every native/Advance Tour golfer; -7 or better over an
  18-hole Tournament/Stroke Play round with each golfer; and course-specific
  sweeps of every par 3, par 4, or par 5 at birdie or better. Character Match
  rounds are explicitly excluded from the round/sweep checks.
- Four goal choices: first place in all 12 regular/Star Tournaments, all 16 Pro
  Character Match opponents, all 36 single-player Ring Attacks, or all three
  complete categories.
  Bowser Championship alone is no longer a completion target.
- A byte-exact captured retail Advance Tour transfer record for Neil and Ella,
  with automated injection/migration tests. Unlock, selection, first-tee play,
  per-golfer club delivery, save, and reload persistence are controller-confirmed
  on the dedicated-card workflow.
- YAML-configurable AP-created Neil/Ella driving profiles: Weak 205/200,
  Standard 305/300 (default), Overpowered 405/400, or one seed-resolved Random
  choice. The resolved pair is serialized in slot data and can migrate an
  earlier AP-created profile without altering genuine full-card golfer stats.
- Independent ownership for all 15 Advance Tour custom club sets. Static
  analysis of the captured retail character-select overlay corrected the
  encoding to three 16-bit wood/iron/wedge masks at record offsets
  `0x27E/0x280/0x282`: normal clubs are bit 0 and the sets are bits 1-15 in
  every mask. Earlier AP builds incorrectly overwrote unrelated bytes at
  `0x267..0x269`; recognized managed records are now repaired. The X-selector,
  component selection, and restart persistence are controller-verified.
- Fifty-foot putt, 300-yard drive, 100-yard hole-out, and perfect Power Shot
  transient tracking.
- Putting Practice mode plus Novice, Intermediate, and Expert access items.
  The 10- and 25-foot practice checks require the corresponding access items.
- Password/code-only Part D checks are hard-disabled in generated worlds;
  their historical IDs/readers remain reserved for later work.
- Seed/slot-specific persistent-result baselining in Archipelago DataStorage.
  A reused memory card no longer grants checks that predate the current seed.
  Mulligan consumption and cumulative Coin totals are seed-specific as well.
  The MGTT context explicitly retains `RoomInfo.seed_name`, which Archipelago
  0.6.7 validates but does not copy onto `CommonContext`.
- YAML-generated randomized starting-golfer items and compact native roster,
  mode, and Putting Practice permission masks.
- Automatic club-inventory text queued on the course/level setup screen.

## Current capture-build fixes awaiting controller validation

- The native hook has been moved out of retail data/BSS into a zero-filled code
  cave at `0x80128000`. A clean boot, protocol initialization, and frame-hook
  execution were verified in Dolphin. This removes the 0.9.4 code/data
  collision responsible for invalid reads of PPC instruction words such as
  `0x38c10004`.
- Notification delivery records the latest popup slot for diagnostics and
  waits for its native state machine to reach the retired state before
  constructing another. The August 9 capture proved that treating the returned
  slot as an inline string buffer corrupted its header and prevented A/timer
  dismissal. The corrected hook never writes through or destroys the object,
  and drops its handle before a menu/save transition so retail remains the
  sole owner.
- Transient hole-result latching records albatross, hole-in-one, eagle,
  birdie, chip-in, and Hit the Pin in the frame hook so consecutive result
  states cannot be lost between desktop polls. Hole-in-One, Eagle, Birdie,
  Chip-In, and Hit the Pin are controller-confirmed. Albatross is corrected but
  remains opportunistic because intentionally producing it is difficult.
- Neil/Ella record injection is byte-exact and covered by save-record tests.
  Visibility, selection, persistence, and active gameplay identity have been
  confirmed. The supported progression workflow uses a fresh/dedicated AP
  card; arbitrary pre-existing transfer profiles are not a 1.0 blocker.

## Capture-derived native guards in the 0.9.8 telemetry build

- Character gating. Priority 1 captures identify the loaded character-grid A
  handler and cursor. The development hook now installs a signature-guarded
  branch there, denies unowned golfers, and calls the retail unavailable sound.
  Controller acceptance on a replacement ISO is still pending.
- Main-mode and Putting Practice difficulty gating. Priority 2 captures map the
  native main enum and common A handler; Priority 3 maps Putting Practice child
  code `0x0D` and Novice/Intermediate/Expert codes `0x11`–`0x13`. The
  development hook now guards both screens, honors the independent mode and
  difficulty YAML switches, and calls the retail unavailable sound. Doubles,
  Club Slots, and Training remain local by design. Controller acceptance is
  still pending.
- Spin gating. Static analysis found a late technique consumer at `0x8046A200`.
  The signature-guarded 0.9.8 stub substitutes normal spin for a locked
  technique and publishes denied/allowed telemetry. Controller acceptance is
  still required; the racy desktop and early-hook writes remain removed.
- Zero-capacity Power Shots. The retail selector enters a forced-Power state at
  zero and the August 5 sequence proves it restores the live counter from zero
  to one after the unintended shot. The focused Power native hook substitutes
  normal shot type while the counter is zero, and the bridge now rejects every
  in-round counter rise unless AP capacity increased or a new round began.
  The separate first-aim forced-Power behavior still needs its before-B/after-B
  capture before another native mutation is attempted.
- Native popup lifetime. 0.9.4 messages remained indefinitely and stacked.
  Priority 0 accepted retail-owned retirement; the bridge now limits native
  construction to the verified course/setup screen and retains queued requests
  for ten minutes.

## Current non-capture hardening

- The post-0.9.12 source adds opt-in per-character putter ranges without a new
  native hook. Each of 18 golfers receives independent 30/100/200-foot items;
  one range starts precollected per golfer and the other two enter the pool.
  The client composes the existing three-bit permission mask from the captured
  active golfer, while AP access rules translate global putter requirements to
  a usable golfer-specific range. Global scope remains the compatibility
  default. A small Mario/Luigi no-leak controller test remains for the next
  build; no new address-mapping capture set is expected.

- Every normal client read must return its exact requested size before data is
  interpreted. Every write is restricted at runtime to a named allowlist of
  the protocol block, verified save masks/Advance Tour records, and the small
  set of captured live equipment counters. The observed spin field is
  explicitly outside that allowlist. Mode gating runs inside the
  capture-derived native confirmation hook rather than through desktop writes
  to retail menu state.
- Malformed or fragmented Archipelago DataStorage replies fail closed instead
  of terminating the client or prematurely enabling cumulative Coin checks.
- Deterministic fuzz coverage exercises 48 additional cross-option worlds.
  Historical item/location maps were compared through every archived release
  from 0.5.0 onward with zero removed or renumbered published IDs.
- The sparse patch was applied from the clean legal dump and compared
  byte-for-byte with both the source patcher output and the diagnostic image.
- The native roster and mode guards now publish target/outcome telemetry in
  reserved protocol bytes. Both inline replacements preserve r3-r31, LR, and
  all non-CR0 condition state across the unavailable-sound call before
  recreating retail's A-button test.
- Server-backed debug item/check commands now require the explicit
  `enable_debug_commands` room option; normal/public YAMLs fail closed.
- `/mgtt_debug_loadout <golfer>` grants a complete standard and short-game
  capture bag through real server `ReceivedItems`, avoiding another impossible
  Character Match test caused by a one-club randomized bag. It is covered by
  the same debug-only room gate.
- The Windows patch applicator discovers exactly one adjacent `.mgttpatch`
  instead of hardcoding an obsolete versioned filename.

## Client and persistence hardening retained in 0.9.8

- Normal Archipelago location submissions, goal status, persistent Mulligan
  use, cumulative Coin Attack totals, and reused-save baselining have been
  restored after identifying the real reconnect cause: AP 0.6.7's Kivy client
  hardcodes a log panel named `Archipelago`. The capture client now preserves
  that internal panel while keeping its MGTT-branded window title.
- Incoming `PrintJSON` rendering and UI command echo are isolated so a display
  failure cannot close the server websocket or prevent `/mgtt_capture` and
  `/mgtt_diagnostics` from executing. Both commands preserve labels containing
  spaces.
- Save-backed roster, Star, Tournament, and Advance Tour writes are disabled
  for the first five seconds after a valid MGAP hook appears. This lets the
  retail game finish memory-card validation before the desktop bridge changes
  any save-derived runtime data.
- AP 0.6.7 regression tests cover authentication, incoming item-message
  fallback, capture/diagnostic labels, UI commands without a Kivy panel, and
  startup suppression of every save-backed write. This branch is not being
  packaged over the current capture APWorld while evidence collection is in
  progress.

## August Priority 0 capture findings

- All nineteen uploaded capture archives pass their internal checksum and
  range validation. The idle, Tournament entry, and returned-menu captures
  retain the relocated hook and valid protocol state.
- The three notification sequences each show exactly one owned popup object
  while visible. Every expired capture clears the popup pointer and cooldown
  before the next message is constructed. Retail-owned popup retirement is
  therefore accepted at the memory/protocol level.
- The visible Birdie result disproves the old `0x8050F0EC` result word. It
  remained `0xFFFFFFFF`; the two surrounding aligned words at `0x8050F0E8`
  and `0x8050F0F0` both contained `4` and returned to `0xFFFFFFFF` after the
  result. The unreleased hook now latches both words, and desktop logic reports
  every distinct transient result while counting a paired hole score once.
  This supports Chip-In plus Eagle without requiring the tester to reproduce
  that difficult shot in a single capture.
- August 5 controller testing identifies retail result `0x02` as Albatross,
  not Hole-in-One; `0x01` is Hole-in-One. The desktop detector, frame-hook
  location bits, and round-score accounting now use that corrected pair. The
  older capture build had those two locations reversed; the current source and
  automated latch tests use the corrected mapping.
- The four owned-spin results identify `0x804ECD4C` as the technique selector:
  `1=Topspin`, `2=Super Topspin`, `3=Backspin`, and `4=Super Backspin`.
  The supplied seed had `spin_scope: 0` and all four spin items precollected,
  so none of these was a locked attempt. A setter/consumer denial hook remains
  unproven.
- The August 11 0.9.17 locked/owned Topspin pairs close that uncertainty for
  the current native probe: both attempts reached selection `1` and effect
  `2`, while `spin_outcome` remained `unseen`. The proposed `0x80469DE4`
  consumer is therefore disproven; disassembly places it in a player-ranking
  routine. Its installer has been removed from development source so the next
  patch cannot mutate unrelated retail state. The replacement needs the exact
  writer/consumer PC for the live technique state.
- The 0.9.17 capacity-one Power Shot test passed in both Stroke Play and
  Tournament: zero remained a normal retail exhausted state, normal shots
  stayed selectable, no repeating sound or phantom Power Shot occurred, and a
  new round restored the configured capacity. Supporting captures/video are
  pending upload.
- The capacity-nine H2 room exposed a later round-initialization race: AP
  published nine before retail finished writing its default six, after which
  the normal counter consumed six to five. Development source now waits one
  complete client poll after the live-session edge, then applies the AP
  capacity exactly once. It does not use a broad settling window that could
  mistake a legitimate 7-to-6 use for initialization and replenish it.
- Clearing the 1P Ring Attack `Ring Near Troubled Water` falsely reported
  `Character Match - Unlock Star Shadow Mario`. Ring Attack natively raises the
  Shadow Mario retail unlock bit, and the Character Match observer was using
  its prior-poll cached mode. It now samples the current native mode latch at
  the exact observation point and rejects a rising Star bit outside Character
  Match. The uploaded result capture is still needed to confirm the independent
  Ring Attack flag/name mapping.
- The 10-foot and 25-foot putt accomplishments passed in 0.9.17, confirming that the live
  distance tracker is active. A 300-yard drive did not report. The former
  reader sampled the lie only after the ball began moving, when retail could
  already replace the tee value, and unnecessarily required the 1W. It now
  preserves the last stable aiming lie and accepts any non-putter shot launched
  from the tee while keeping menu/course-load coordinates excluded.
- `Chip In from a Bunker` also passed in 0.9.17, confirming that the retained
  pre-result lie correctly distinguishes a bunker-origin chip-in.
- The Power pair confirms Player 1 changes from one remaining shot to zero
  while the ordinary shot-type word remains zero. It does not include the
  subsequent unintended “0th” shot, so the native selector/consumer that must
  be denied is still unidentified. Capacities 7–9 remain covered by bridge
  unit tests, but controller validation can wait until the zero-state path is
  solved.
- The accompanying character-select video and `save_header` bytes resolve the
  two retail golfer words that the prototype had reversed. The first copies
  for Birdo and Diddy Kong produced `0x0480` at `SAVE_BASE+0x04`, and those two
  displayed Star icons while the four hidden retail golfers stayed absent with
  `SAVE_BASE+0x06 == 0`. The unreleased branch now treats `+0x04` as the Star
  mask and `+0x06` as the base/hidden-golfer mask. A first progressive copy no
  longer grants the Star form, and a first copy for Boo, Bowser Jr., Shadow
  Mario, or Petey Piranha targets the retail visibility word.

## August Priority 1 capture findings

- All six full-MEM1 archives pass their internal checksum and range
  validation. Tournament return was also reported clean, closing the final
  Priority 0 evidence request.
- Seven character-select samples reduce the live grid cursor to one exact byte
  at `0x8044BA4B`: Mario=0, Luigi=1, Diddy Kong=7, Boo=13, and Shadow Mario=14.
  Row/column state at `0x8044BA10/+0x14` independently agrees with those
  presentation indices.
- The final locked-Mario before/after pair identifies `0x8040BCF4` as the
  A-button instruction that starts the accepting selection transition; retail
  later commits the selected-player count at `0x8040BE64`. The unreleased
  main-DOL hook now waits
  for a four-word overlay signature, installs a cache-flushed branch to a
  permanent guard stub, tests the protocol roster mask, clears A for a locked
  golfer, and plays the retail unavailable sound. An unloaded or unknown
  overlay is left untouched. This replaces the earlier disproven generic
  widget approach.
- The six-starter seed's first copies were Bowser, Yoshi, Bowser Jr., Daisy,
  Luigi, and Peach. Their exact internal bit mask `0x6116` appeared in the
  Star word in the old capture build, explaining both the Star icons and why
  the retail-default roster remained open. The corrected development client
  writes that mask to the base/hidden-golfer word and writes zero to Stars.
- The completed two-player Ring Attack set bit `0x04` in its retail multiplayer
  result row and triggered retail's Shadow Mario unlock presentation. The
  capture metadata still reports zero AP checks and the diagnostics baseline
  was not ready. The development client has already restored normal AP
  DataStorage initialization and persistent location submission; this needs
  validation on the replacement build, not another snapshot from 0.9.5.2.6.
- The current 0.9.20 RC patched-ISO SHA-256 is
  `908e898af3100f667d2139b047e8a7974eb8d684c3ad451570d3ec4c12bf434c`.
  All 270 AP 0.6.7 compatibility, generation, game-state, packaging, and
  patch-layout tests pass in the package test environment. The C protocol
  implementation also compiles with `-Wall -Wextra -Werror`.

## August Priority 2 capture findings

- All eleven uploaded archives pass their internal checksum and range
  validation. The capture pairs identify the native main-mode value at
  `0x80445FE0`, mirrored at `0x8044C414`, and the common confirmation handler
  at `0x8041D604`.
- The verified native enum is Tournament=0, Character Match=1, Stroke Play=2,
  Doubles=3, Ring Attack=4, Club Slots=5, Coin Attack=6, Speed Golf=7,
  Training=8, and Side Games=9. The development hook installs a
  signature-guarded branch at the A handler, suppresses A for a locked AP mode,
  and calls retail sound 2.
- Doubles, Club Slots, and Training are deliberately always allowed local
  modes. Match Play and Skins Match do not exist in Toadstool Tour and have
  been removed from new item pools. Their old numeric item IDs remain reserved.
  “Coin Shoot” has been corrected to “Coin Attack”; its two result variants
  remain Quick Cash and Cash Cup, with all numeric item/location IDs preserved.

## August Priority 3 capture findings

- All five uploaded archives pass their internal checksum and range
  validation. Side Games menu state 1 resolves child code `0x0D` as Putting
  Practice. Menu state 2 exposes codes `0x11`, `0x12`, and `0x13` for Novice,
  Intermediate, and Expert; active gameplay confirms difficulty values 0–2.
- The same native A handler used by the main menu owns these child screens.
  The development guard now checks the Putting Practice item and the selected
  difficulty bit, honors the independent `shuffle_modes` and
  `shuffle_putting_practice_difficulties` switches, suppresses A when locked,
  and plays the retail unavailable sound. Controller acceptance is pending.

## August Priority 4 capture findings

- All thirteen full-MEM1 archives and their diagnostic file pass checksum and
  range validation. The supplied save has four matching primary/mirror transfer
  slots: Joshy/Sally, Dax/Lyn, Tai/Kris, and Neil/Ella.
- The existing character confirmation path also owns transferred-golfer cursor
  values 16 and 17. The replacement hook now gates both behind the shuffled
  `Advance Tour Golfers - Neil & Ella` item and plays the retail unavailable
  sound when denied. Full cards now adopt only the first agreeing pair's three
  custom-club mask bytes so AP items can control the pair that retail exposes.
- Setup text at `0x802CC34C` starts directly with a renamed GBA name. Paired
  first-tee buffers at `0x804E5D84` and `0x804E6728` retain the same name during
  play. The client matches these names against agreeing primary/mirror records,
  so Joshy maps to the Neil role and Sally maps to the Ella role without
  assuming literal default names.
- Neil and Ella now participate in per-character standard-club and spin item
  generation: 26 new club items and eight new spin items, all appended after
  published IDs. Each receives one independently randomized starting club.
  Ten checks reward completing 1, 3, 6, 9, and 18 holes as each golfer.
- The custom-club selection captures confirm three zero-based selectors at
  `0x8044BB08`, `0x8044BB0C`, and `0x8044BB10` for Wood, Iron, and Wedge. The
  selected values in the all-three capture are 2/1/3 and each corresponds to a
  set bit in Joshy's record mask `07 0e 39`, validating the existing three-byte
  AP ownership layout.
- Reload changes only transfer-record byte `+0x27B` for Joshy (`00` to `24`).
  The updater preserves that retail play-history byte and, on a full card,
  changes only Joshy/Sally's three custom-club mask bytes. The shared selector
  template was corrected to the captured 28 zeroes, six `3F` bytes, and final
  zero. Blank-slot injection itself still needs controller acceptance because
  the supplied save had no blank slot.

## Priority 5–11 prior-evidence audit

- The earlier Password Tournament sequence already supports the experimental
  Bowser's Big Blast detector, but one event cannot safely decode or launch all
  seven events or establish their separate score thresholds.
- The previous Club Slots prompt establishes the Player 1 Mulligan counter
  already used by the client. It does not identify a safe way to construct that
  prompt in modes where retail omits it.
- The Hole-in-One Contest sequence already backs its experimental completion
  detector. It contains no locked/unlocked entry pair, and there is no prior
  One-On One-Putt entry sequence, so those native gates remain pending.
- The August 5 practice captures identify saved Putting Novice (`0x10`) and
  Approach Novice (`0x02`) completion bits at `0x80236116`. They also identify
  the Birdie Challenge Front 9 progression at `SAVE_BASE + 0x1299`: clearing
  Front 9 changes it from zero to `0x02` while unlocking Back 9. These three
  checks reconcile through the reused-save baseline. This historical note is
  superseded by the August 6 Part A mapping below.

## August 6 Part A findings

- All 47 full-MEM1 archives validated. Putting/Approach Intermediate/Expert
  persistent bits and Tee/Second Shot persistent bits are mapped; Trouble Shot
  uses its capture-verified live clear screen.
- Shot coordinates are feet. The 10/25/50-foot putts, 100-yard hole-out, and
  300-yard drive thresholds have been corrected accordingly.
- Quick Cash/Cash Cup accumulation now uses the settled round total and a
  latched session golfer/variant instead of the last-hole counter.
- Congo Canopy Front 9 uses live Stroke Play course, start-hole, round-length,
  and score identity. Back 9/All 18 IDs are retired from new worlds.
- Speed Golf course checks now target ten minutes, with a new combined
  under-15-minutes-and-under-par location. Near-Pin defaults to 300 feet.
- Repeated live result submissions are latched locally. Native item messages
  are serialized against sequence and the retail popup's native retirement;
  redundant check-complete messages are not sent to the game.

## Modeled but not yet enforced or reported

- Making the native Mulligan prompt available outside the retail modes that
  normally expose Mulligans.
- One-On One-Putt, Hole-in-One Contest, Password Tournaments, and Bowser's Big
  Blast are deferred beyond 1.0. Their historical IDs/readers remain reserved,
  but generation hard-disables them even if an old YAML requests experimental
  checks.
- A fingerprint stored inside the retail memory-card record itself. Reconnect
  reconciliation is implemented server-side without mutating unknown save
  bytes.
- Automatically showing the correct golfer's club summary directly while
  highlighting golfers. The safe fallback now displays it on the following
  course/level setup screen.
- Reporting Birdie Challenge Back 9/All 18. Character Match per-course wins
  now use the capture-proven rising Star-match edge plus the active regular
  course, but still need controller acceptance. Best Badge needs one known-hole
  remap. Congo Back 9/All 18 and the old Speed Golf 15-minute course IDs are
  deliberately retired from new worlds.
- Special-mode/password work has no 1.0 capture request and is not part of the
  current release gate.
- Configurable early-sphere item weighting is deferred until after 1.0. Course
  access, golfers, modes, and essential equipment remain progression items;
  a later option may bias these useful unlocks earlier without changing their
  IDs or guaranteeing exact placements.

## Evidence needed for the remaining hooks

The fastest safe route is the paired `/mgtt_capture` set in the final capture
checklist. The roster, main-mode, Putting Practice, and late spin paths are
instrumented in 0.9.8 and need controller acceptance. The highest remaining
hook priority is the zero-capacity Power Shot transition. Remaining reverse
engineering covers confirmation of the preliminary per-course Character Match
reader, Birdie Challenge Back 9/All 18, and the optional universal retail
Mulligan prompt.

## August 9 0.9.15 focused retest

- Top-level shuffled-mode denial is controller-confirmed: a locked mode no
  longer advances. The game still plays its normal confirmation sound rather
  than the unavailable sound. This is tracked as post-1.0 quality-of-life
  polish and is not a release blocker.
- Character denial remains unaccepted. Shadow Mario appeared correctly as the
  room's owned non-Star starter, but locked Mario advanced normally and no
  unavailable sound played. The associated before/after captures and roster
  diagnostics are pending analysis.
- Notification serialization prevents stacking but does not provide a valid
  lifecycle. The first AP popup ignored A and the apparent native timer,
  survived later holes, and blocked every later item popup. A scene change
  discarded one unpublished client request but did not remove the visible
  retail object. The current `+0x26A == 0` retirement assumption is therefore
  disproved for this constructor path; serialized native delivery remains a
  1.0 blocker pending capture-backed dismissal work or a `client_only`
  fallback.
- The `/mgtt_debug_power_sync off` control succeeds: a fresh round initializes
  six retail Power Shots and behaves normally through depletion. The native
  six-to-zero lifecycle is therefore accepted. Remaining Power work is scoped
  to AP capacity initialization/replenishment and must not continuously fight
  retail's live counter or shot selector.
- Full-memory notification comparison proves the popup body, state `4`, and
  field `+0x260 == 200` remain unchanged across a hole transition. Retail
  callers explicitly clean these objects through `0x80024C98`; the hook now
  uses that routine after a bounded 180-frame AP display window or a live-hole
  transition request. Menu teardown still abandons the handle without touching
  potentially reclaimed UI memory.
- Ordinary diagnostics now retain the latest native gate/gameplay trace and
  Power-sync status. The supplied roster files were diagnostics rather than
  full-memory captures, so a safe character-confirm relocation still needs one
  locked before-A/after-A `/mgtt_capture` pair.

## August 6 Tournament-win findings

- Both uploaded full-MEM1 Tournament-win archives pass checksum and range
  validation and identify Yoshi as the active golfer.
- Compared with the earlier clean `0x80` tables, Lakitu Cup first place is
  stored as `1` at regular Tournament table row 22, course 0. Yoshi is internal
  golfer index 8, proving a 14-row prefix before the native roster.
- The earlier client scanned only rows 0 through 15, so it could miss both the
  overall Tournament win and the optional per-character win. The reader now
  scans all 40 rows and maps native character checks through rows 14 through
  29.
- The captured room exposed all six regular courses for Character Match but
  did not own `Tournament - Lakitu Cup`. Retail uses the same availability bits
  for both menus. New `all_courses` worlds therefore precollect all six regular
  Tournament items; older rooms using that setting are accepted by the client
  when a physically playable win appears in the corrected table.
- Player YAMLs now default to `follow_tournament_items`, making every regular
  and Star Tournament course an AP access item. One random regular course is
  precollected by default through the configurable `starting_tournaments: 1`;
  values from 0 through 6 are supported. A regular course item also opens the
  matching Character Match course because the retail save has only one shared
  six-bit availability field.

Use a copy of the memory card. Do not provide or distribute the disc image.

`/mgtt_capture <label>` creates a read-only, checksummed ZIP in Archipelago's
log folder, so these samples can be collected without installing a debugger or
manually locating addresses.

`/mgtt_diagnostics <label>` creates a small sanitized JSON report in the same
log folder. Send it with each capture batch; it omits the server address and
password.

## August 10 0.9.16 Tournament-course findings

- The supplied Sands/Blooper transition pairs identify `0x804148C0` as the
  shared captured course-confirmation A test. A signature-guarded native check
  now uses the stable course index, confirmed top-level mode, and retained
  Star-form selector to enforce twelve independent AP Tournament permissions.
- The front-end course builder proves `SAVE_BASE + 0x07` is a five-bit course
  progression byte, not an ordinary-golfer unlock byte. Mario/Luigi/Peach
  ownership had written `0x07` there and exposed exactly three extra courses.
  Ordinary golfers are now protocol-only; only hidden golfers use save-backed
  base bits, and physical course presentation is synchronized separately.
- The capture's received Sands item is the Star tournament, not the regular
  Sands tournament. Exact gating therefore denies that non-Star selection as
  well as the locked Blooper selection. Lakitu is the owned regular control.
- The missing-invitation sample came from the user's new, test-only memory
  card. Its Advance Tour/custom-club data was AP-injected, while its nonzero
  result bytes reflect the testing the user had already described; neither is
  evidence of an advanced retail save. The missing invitation is a genuine
  supported-workflow failure.
- The same capture has a zero retail Star mask, ruling out stray AP Star
  ownership as the immediate cause. Older builds also wrote ordinary golfer
  ownership across the course byte at `SAVE_BASE + 0x07` and wrote an obsolete
  tournament mask at `SAVE_BASE + 0x08/+0x09`. Those writes are removed or
  separated in current development code. The initial Koopa invitation must be
  retested in the next build and is not yet claimed fixed.
- The complete suite passes 256 tests; the protocol C layout also compiles
  cleanly under `-Wall -Wextra -Werror`.

## August 11 Ring Attack findings

- The later Mario Lakitu-level-2 capture corrects the initial 1P interpretation:
  the result table begins at `0x8022AC5C` (`SAVE_BASE + 0x894`) and contains 24
  six-byte golfer rows. The old `0x8022ACBC` (`+0x8F4`) candidate is only row
  16; it happened to change in the first positive before/after pair. Mario's
  row contains `0x03` after clearing Lakitu levels 1 and 2 while row 16 remains
  zero. The reader now ORs all golfer rows so the AP locations remain global.
- Server-confirmed 1P Ring Attack masks are ORed into every golfer row after
  fresh native progress has been read and submitted. This makes colored stars
  persistent and golfer-independent without allowing client-authored state to
  fabricate a new check. The client never clears native progress.
- The corresponding 2P capture changed only `0x8022ACEC`
  (`SAVE_BASE + 0x924`) from `0x01` to `0x03`. Multiplayer results are three
  contiguous six-course tables beginning at `+0x924`, `+0x92A`, and `+0x930`
  for 2P, 3P, and 4P respectively.
- The former client offsets were displaced (`-0x30` for 1P and `-0x04` for
  multiplayer), explaining both missed checks. The readers and diagnostic
  capture fields now use the capture-backed addresses, with absolute-address
  regression assertions.
- August 26 controller testing confirms that retail Ring Attack course
  progression works: clearing the six levels on the current course reveals the
  next course. This is the supported 1.0 behavior and is no longer a release
  blocker. A separate post-1.0 YAML mode may make regular Archipelago course
  items reveal the corresponding Ring Attack course; that alternative is
  deferred because Ring Attack uses a distinct level-select menu and must not
  disturb the confirmed retail path.

## August 26 0.9.57 release acceptance

- Progressive Power Shot Capacity items, five consecutive birdies, finishing a
  Tournament outside the Top 3, regular Top 3 placement, first place, and the
  per-golfer Tournament win path are controller-confirmed.
- `Win Any Star Tournament`, the All Tournaments goal, the All 1P Ring Attacks
  goal, and the All Pro Character Matches goal are controller-confirmed.
- PopTracker reconnect/inventory synchronization and retail Ring Attack course
  progression are controller-confirmed.
- Star Tournament Top 3 has not been reproduced directly. It is accepted for
  1.0 by shared-path inference because regular Top 3 uses the same placement
  reader and Star Tournament completion/result attribution is independently
  confirmed. It is a non-blocking public-beta observation item.
- The combined `all_three` goal is now controller-confirmed through its normal
  underlying durable checks. All four supported goal choices have therefore
  passed. The earlier attempt to manufacture the combined result by granting
  only the three synthetic component-goal checks was a debug-path limitation,
  not a failure of the playable goal.

## August 11 0.9.18.1 acceptance and course-menu findings

- Roster denial/restoration, Putting Practice difficulty unlocks, serialized
  native notifications, and Custom Club Set item/label mapping are
  controller-confirmed passes. Custom Club mapping is frozen while the
  remaining hooks are repaired.
- The paired Lakitu Valley/Bowser Badlands Character Match captures prove that
  `CURRENT_COURSE` is a compact visible-entry cursor: Lakitu is `0` and Bowser
  is `1` when those are the only visible courses. The protocol now publishes a
  six-byte visible-index-to-native-course map, and the PPC guard translates
  through it before testing the regular course permission.
- Regular course-access items are player-facing course names (`Lakitu Valley`
  through `Bowser Badlands`) and grant the matching course in both Tournament
  and Character Match. Their six numeric IDs remain unchanged. Star Tournament
  course items retain their existing `Tournament - ... Star ...` names and IDs.
- Ring Attack testing confirms the forced Power selection and invalid zero-th
  Power Shot state occur together there too. The power repair must restore the
  global retail shot selector and only synchronize AP capacity at a safe round
  boundary.
- A 1P Ring Attack clear reports the correct Archipelago location and delivers
  its item, so the corrected 1P reader is controller-confirmed. Retail still
  displays a Shadow Mario unlock logo during the clear sequence; this is
  cosmetic unless later testing shows it mutates golfer ownership.
- A 2P Ring Attack clear likewise reports the correct Archipelago location, but
  constructing its received-item popup over the native Shadow Mario-style
  clear dialog caused invalid reads at `0x800246c8/0x800246cc`. Ring Attack is
  now excluded from native-popup-safe scenes; receipts wait for the next live
  hole in another mode. This retains serialized delivery without overlapping
  the native clear UI.
- Restarting after AP Star Mario/Yoshi had been displayed falsely reported
  both Star-character checks and the Lakitu Valley Character Match course
  check. The last-selected-mode byte can be stale across restart, so it is no
  longer sufficient evidence. The hook now publishes a dedicated successful
  top-level-mode generation byte; Character Match checks arm only after the
  client observes a new allowed Character Match entry.
- Server-checked 1P--4P Ring Attack locations now restore their exact native
  result bits after startup validation. This repairs native progression lost
  when a post-clear crash or interrupted save prevented retail persistence,
  while never setting an unchecked level.
- `Accomplishment - Drive 300 Yards` remains a controller-confirmed reader
  failure in 0.9.18.1. The current tee-lie/distance sampler needs the supplied
  long-drive state evidence before its tee-shot predicate is broadened; the
  earlier false 300-yard report makes an unconditional threshold unsafe.
- Vanilla-ISO testing with an AP-used memory card confirms that the former Star
  presentation strategy could persist AP-owned Star bits into retail save
  progression. The client now recognizes the immutable character-select and
  mode-select overlay signatures: AP Star bits exist only while those UI
  overlays need them, while gameplay/result/save screens receive the preserved
  retail-only shadow. An already-contaminated card still requires an untouched
  backup for a valid vanilla comparison because genuine and formerly AP-owned
  bits cannot be distinguished after the fact.
- The Shadow Mario unlock animation did not overwrite the Ring Attack clear. Its
  false Character Match report is handled separately by requiring the live
  native mode latch to be Character Match before accepting a rising Star bit.
- The supplied room used `ring_shot_player_counts: single_player_only`, so its
  2P native result was not expected to submit an AP location. The consolidated
  `all_player_counts` room remains the required multiplayer acceptance test.
