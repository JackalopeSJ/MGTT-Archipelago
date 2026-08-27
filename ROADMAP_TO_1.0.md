# Mario Golf: Toadstool Tour Archipelago — Roadmap to 1.0

Updated August 8, 2026 with the agreed 1.0 scope, defaults, and first location
expansion. This roadmap starts from the recovery baseline and supersedes the
old Priority 0–11 ordering.

## What 1.0 means

A player must be able to generate a supported world, patch a clean NTSC-U
`GFTE01` image, connect through the MGTT client on Archipelago 0.6.7, and
complete every generated location and goal without debug commands, a
pre-completed memory card, or entering retail passwords.

Every supported feature must pass three layers:

1. **World model:** correct items, locations, rules, counts, and YAML.
2. **Game bridge:** items enforce access and accomplishments report once.
3. **Controller verification:** the paired build works in Dolphin without
   crashes, stuck input, stale messages, or save corruption.

Anything that cannot pass all three will be disabled and marked experimental,
not left as an apparently functional but unreachable 1.0 option.

## Agreed 1.0 scope and defaults

- Per-character standard clubs are the core/default experience; global and
  vanilla scopes remain compatibility choices for now.
- Three of the 16 native golfers start unlocked by default.
- Shuffled Power Shot capacity accepts 1–9 and defaults to six; progressive
  copies can raise it to nine.
- Global putter ranges remain the default. Per-character putter ranges are an
  optional 1.0 bonus if their controller regression passes.
- Character Match begins with the one regular course supplied by the default
  starting Tournament item. Star Tournament is not a second shuffled mode;
  individual regular/Star courses remain Tournament items.
- The default goal is first place in all six regular and all six Star
  Tournaments.
- Trap items and password/special tournaments are post-1.0. The trap item ID
  architecture remains reserved; Gale Force Winds is the leading future trap.
- The locked-mode guard is accepted for 1.0 even though it currently plays the
  normal confirmation sound. Replacing that with the retail unavailable sound
  is post-1.0 interface polish and will not delay the release.
- Mulligans are capped at 99 per generated world and replace every otherwise-
  empty item slot in supported 1.0 configurations.
- Standard Tour, Short Tour, and Complete Tour YAML presets ship with 1.0.
- Coin Attack, Speed Golf, Congo Canopy Front 9, multiplayer Ring Attack, and
  native custom-club selection remain targeted for 1.0, but a failing optional
  subsystem may be disabled rather than delaying a stable release.

## Ownership key

- **Codex:** implementation, reverse engineering from captures, builds,
  automated tests, documentation, and release packaging.
- **Human tester:** natural gameplay, controller observations, captures, logs,
  and confirmation on Windows/Dolphin.
- **Shared:** Codex provides a focused build/checklist; the tester runs it;
  Codex analyzes the result and either accepts or revises it.

## Current position

### Accepted or substantially complete

- AP 0.6.7 authentication, Windows Dolphin connection, MGTT-branded client,
  connection messages, diagnostics, and capture commands.
- Global/per-character clubs, independently randomized starting clubs, putter,
  putter ranges, and removal of the temporary full first-hole bag.
- Immediate item inventory and seed-specific reused-save baselining.
- Tournament, Star Tournament, 1P/multiplayer Ring Attack, Speed Golf, and
  Near-Pin save readers. Best Badge still needs one known-hole remap.
- Confirmed Eagle, Birdie, Chip-In, Hit the Pin, 50-foot putt, 100-yard
  hole-out, and perfect Power Shot checks.
- Corrected Hole-in-One/Albatross identities; natural reproduction is optional.
- Mulligan receipt, Tournament use, consumption, and persistence.
- Neil/Ella injection, selection, gameplay identity, save/reload, per-character
  clubs, custom-club ownership layout, and YAML stat model.
- Putting/Approach Novice, Intermediate, and Expert plus Birdie Challenge
  Front 9 persistent readers.
- Correct Shot Practice categories: Tee Shot, Second Shot, Trouble Shot;
  persistent Tee/Second and capture-verified live Trouble completion readers.
- Corrected feet-based shot-distance thresholds, session-settled Coin Attack
  accumulation, Front 9 Congo threshold, six ten-minute Speed Golf checks, and
  the combined under-15/under-par check.
- Added 54 live golfer/course accomplishments: birdie or better and an
  18-hole -7 target for each of 18 golfers, plus all-par-3/4/5 birdie sweeps
  for every regular course. Character Match is excluded from round sweeps.
- Historical ID preservation and 239 passing automated tests.

### 1.0 blockers

- Reliable character and Putting-difficulty denial. Top-level shuffled-mode
  denial is controller-confirmed; its incorrect confirmation sound is deferred
  polish rather than a 1.0 blocker.
- A true visible non-Star first stage for Boo, Bowser Jr., Petey Piranha, and
  Shadow Mario; retail currently reveals these hidden slots only with a Star
  bit, so this is part of the focused roster-native work.
- Spin denial at the final consumer. The 0.9.17 locked/owned pair disproved
  the current hook site; the unsafe installer is removed and the exact native
  writer/consumer PC still needs to be mapped.
- Capacity one passed in Stroke Play and Tournament, including the zero
  transition and new-round replenishment. Capacity nine exposed a separate
  initialization-order race and displayed six; the development client now
  delays its one-time round synchronization until retail has written that
  default. A 7–9 retest is required on the next build.
- The strictly serialized native-message path passed the 0.9.17 queue and
  reconnect tests: one popup at a time, normal retirement, and no overlap.
- Readers for all enabled Character Match course, practice, Birdie Challenge,
  and Congo Canopy locations.
- A complete clean-card Windows/AP 0.6.7 regression with no invalid accesses.

## Phase 1 — Recovery baseline

| Owner | Tasks |
|---|---|
| Codex | Kept unsafe 0.9.8 guards withdrawn; integrated capture-backed practice readers; corrected Shot Practice names; audited the Part A memory states. **Complete.** |
| Human tester | Confirmed Putting and Approach begin at 0/10, advance to 1/10, and do not clear early. **Complete.** |
| Codex after handoff | Accepted the restored counters. Exact retail early-fail-after-three-misses behavior is optional parity work and needs a vanilla/patched comparison only if retained for 1.0. |

**Complete when:** Recovery has normal ten-attempt practice behavior and stable
ordinary menus/save flow.

## Phase 2 — Isolated native-guard probes

Only one new native mutation will be enabled per paired probe build. This
prevents one bad hook from obscuring another.

### 2A. Character and Advance Tour golfer gating

| Owner | Tasks |
|---|---|
| Codex | Build a roster-only probe using the captured grid cursor and confirmation consumer; preserve registers; call retail unavailable sound; publish telemetry. |
| Human tester | Test owned and locked native golfers, one hidden golfer, progressive base then Star copies, and locked/owned Neil/Ella. |
| Codex after handoff | Verify telemetry and memory safety, revise if needed, then merge only the accepted guard. |

### 2B. Main modes and Putting Practice

| Owner | Tasks |
|---|---|
| Codex | Build a mode-only probe, then a separate child Putting/difficulty probe; keep Doubles, Club Slots, and Training local; let Star Tournament follow Tournament ownership. |
| Human tester | Test one owned and locked main mode, local modes, Star Tournament access through owned Tournament mode, Putting Practice, and locked/owned Intermediate and Expert. Record sound and cursor behavior. |
| Codex after handoff | Accept or revise each guard independently before combining them. |

### 2C. Spin enforcement

| Owner | Tasks |
|---|---|
| Codex | Remove the disproven `0x80469DE4` installer, map the exact live technique writer/consumer, and create a probe that substitutes normal/no spin for a locked technique without desktop writes. |
| Human tester | **0.9.17 G1 complete and failed:** locked and owned Topspin behaved identically. No more ordinary spin captures are needed until Codex supplies a replacement probe; a Dolphin write-breakpoint PC may be requested if static analysis cannot resolve the writer. |
| Codex after handoff | Confirm the consumer, remove unnecessary telemetry, and merge only after effects match ownership. |

### 2D. Power Shot initial and zero states

| Owner | Tasks |
|---|---|
| Codex | Instrument the automatic first-aim selection and the transition after the final legitimate Power Shot; move AP capacity application to round initialization/replenishment and avoid interfering with retail's in-round counter and selector. |
| Human tester | **Retail baseline and 0.9.17 H1 accepted:** capacity one passed in Stroke Play and Tournament through final use, zero, ordinary follow-up shot, menu return, and replenishment. Smoke capacities 6–9 when practical. |
| Codex after handoff | Preserve the accepted retail-owned in-round lifecycle; retain automated coverage for 1–9 and use human H2 only as the final 6–9 session smoke. |

### 2E. Native notification queue

| Owner | Tasks |
|---|---|
| Codex | Implemented strict serialization around one genuine retail popup. The producer waits for the prior sequence and native popup retirement; the hook never overwrites or destroys the object, removes redundant check-complete popups, and clears unsent backlog on scene exit. Added `native_popup_delivery: serialized/client_only`. |
| Human tester | **0.9.15 failed:** only one popup was visible, but A and the native timer did not retire it. It survived multiple hole transitions and permanently blocked later messages. The client discarded one queued stale message without removing the visible retail object. Upload the associated before-A/after-A/next-hole captures for lifecycle analysis. |
| Codex after handoff | Identify a capture-proven dismissal/transition consumer and retest it without object corruption. Accept serialized delivery only with no overlap, stuck text, invalid accesses, or menu/save freeze. Otherwise make `client_only` the 1.0 default. |

**Complete when:** each probe passes separately, then all accepted guards pass
together for two full rounds and repeated menu exits.

## Phase 3 — Complete location reporting

### 3A. Core persistent checks

| Owner | Tasks |
|---|---|
| Human tester | Spot-test regular/Star Tournament, 1P/multiplayer Ring Attack, Star Character Match, and correct-hole best badges. Capture two Character Match wins on different courses. |
| Codex | Map per-course Character Match results, implement readers/baselining, and verify all goal derivations. Keep all Character Match courses available by default. |

### 3B. Practice and Birdie Challenge

| Owner | Tasks |
|---|---|
| Human tester | Putting/Approach Intermediate/Expert and all Shot Practice captures are **complete**. Retry only Birdie Back 9/All 18 after notification safety is accepted. |
| Codex | Implemented the four durable Putting/Approach flags, durable Tee/Second Shot flags, and live Trouble Shot completion edge. |
| Shared decision | Shot Practice access remains separate polish: Tee Shot local; progressive AP copies may unlock Second then Trouble, matching retail order. |

### 3C. Coin Attack, Speed Golf, and Near-Pin

| Owner | Tasks |
|---|---|
| Human tester | Verify the corrected Quick Cash cumulative total and one Cash Cup total; retry the 100-coin-hole check, capturing the exact result only if it still fails. Confirm the new ten-minute Speed Golf course check and Near-Pin default 300. |
| Codex | Implemented session-latched, settled-round Coin Attack credits; corrected Speed Golf course target to ten minutes; added under-15/under-par; changed Near-Pin to 1–901/default 300. Immediate sub-15-second-hole reporting still needs a result/next-tee pair. |

### 3D. Congo Canopy

| Owner | Tasks |
|---|---|
| Human tester | Front 9 failing and passing sequences are **complete**. No Back 9/All 18 Congo captures are requested. |
| Codex | Implemented Front 9 from live course/mode/start-hole/round-length/score identity. Preserved the two published long-round IDs but retired them from new worlds. |

### 3E. Remaining feats

| Owner | Tasks |
|---|---|
| Human tester | Recheck 300-yard tee drive and 10/25/50-foot putts in an ordinary golf mode after the feet conversion fix. Capture only failures. Putting Practice distance awards need a separate known-distance result triple. |
| Codex | Corrected every distance conversion. Keep Hole-in-One/Albatross accepted through native latches plus tests. Best Badge still needs one exact known-hole triple. |

### 3F. Golfer and course accomplishments

| Owner | Tasks |
|---|---|
| Codex | Implemented all 54 locations, per-character logic rules, live golfer attribution, 18-hole -7 aggregation, par-type sweep tracking, and Tournament/Stroke Play qualification. Automated tests reject Character Match awards. |
| Human tester | In the next combined build, make one birdie with a native golfer, complete one qualifying -7 round, and complete one course/par sweep. A single 18-birdie test round may confirm all three paths. Optionally spot-test Neil or Ella attribution. |
| Codex after handoff | Accept the readers if each reports once with the expected golfer/course and no Character Match leakage. |

**Complete when:** every location available under supported options is naturally
obtainable, reports once, survives reconnect, and respects reused-save baseline.

## Phase 4 — Advance Tour and inventory polish

| Owner | Tasks |
|---|---|
| Human tester | Standard and Overpowered profiles, per-golfer club isolation, Super Sweet selection, and reload persistence are **complete**. |
| Codex | Corrected the retail three-mask custom-set encoding and legacy managed-record repair. Advance Tour Part C is **complete**. |
| Codex | Keep `/clubs` as the reliable inventory display. Character-select overlay text is polish, not a blocker, unless a safe retail-owned widget is identified. |

**Complete when:** a blank card can unlock, configure, play, save, and reload
Neil/Ella without altering unrelated card data.

## Phase 5 — Deferred special modes

One-On One-Putt, Hole-in-One Contest, Password Tournaments, and Bowser's Big
Blast are outside the 1.0 scope. Their historical IDs and readers remain
reserved for compatibility, but no option can place these checks or their
access items in a generated world. No Part D captures are requested for 1.0.

This work may resume after 1.0 only when password-free native entry and
independent event identity can be implemented without destabilizing the retail
menus.

## Confirmed 1.1 backlog

The following ideas are explicitly welcome but cannot hold the 1.0 release:

- Optional Ring Attack course progression. Keep retail progression as the 1.0
  default: clearing all six levels on a course reveals the next course. Add a
  post-1.0 YAML choice that instead makes each regular Archipelago course item
  reveal that course's Ring Attack levels, matching the course access used by
  the other modes. This will require focused work on Ring Attack's distinct
  level-select construction and must preserve existing clear flags, multiplayer
  results, and the supported vanilla-progression path.
- Safe native receipt messages through a retail-owned message manager rather
  than AP-owned popup construction.
- Menu/character-select club summaries, locked-golfer portrait shading, and
  the retail unavailable sound on every denial path.
- Stable shuffled spin enforcement and an optional per-golfer Approach Shot.
- Recommended 3P/4P Ring Attack plus optional Player 2–4 equipment gating.
- Custom-club-set selection that does not depend on creating the supported
  Neil/Ella transfer state.
- Birdie Challenge Back 9/All 18 and Congo Canopy Back 9/All 18 readers.
- Character Match win-with-each-golfer, hole-win, and additional margin checks;
  investigate Neil/Ella only if a safe non-native-opponent model is chosen.
- Item and location difficulty/category metadata.
- Named location groups after their organization has been designed.
- Gale Force Winds and any other accepted trap items.
- Course Double Crown checks for winning the regular and Star event associated
  with each course.
- Aggregate Tournament wins with 3, 6, and 12 unique golfers.
- Golfer Versatility checks for birdie-or-better on a par 3, par 4, and par 5
  with the same golfer.

The final August 26 scope decision defers every wishlist addition above until
after 1.0, including per-golfer Approach Shot, Congo Canopy Back 9/All 18,
Birdie Challenge Back 9/All 18, and adding 2P clears to the Ring Attack goal.
The existing confirmed 1P goal remains the 1.0 behavior. Future 1P+2P goal
design may treat 2P as a solo-compatible challenge because Toadstool Tour lets
all local golfers share one controller. AP-course Ring Attack progression also
remains post-1.0 because retail exposes courses through sequential clear flags
rather than a mapped independent visibility table.

## Phase 6 — Release-candidate integration

| Owner | Tasks |
|---|---|
| Codex | Produce deterministic default, complete per-character, restrictive roster/mode, and Neil/Ella seeds with matching patch/APWorld and expected-inventory manifests. |
| Human tester | Run the complete regression on Windows/AP 0.6.7 from a blank card; test disconnect/reconnect, save/exit, two rounds, ten items, ten checks, and each goal. Repeat the high-risk subset once. |
| Codex | Analyze logs, fix defects, rerun all automated tests, and issue a new RC only when changes require it. |

**Complete when:** two consecutive regression passes have no invalid accesses,
crashes, stuck input, duplicate checks, unreachable locations, or stale messages.

## Phase 7 — 1.0 packaging

| Owner | Tasks |
|---|---|
| Codex | Produce `mgtt.apworld`, versioned `.mgttpatch`, Windows/cross-platform instructions, complete/default YAMLs, item/location spreadsheet, README, troubleshooting guide, and SHA-256 manifest. Run AP 0.6.7 generation/fill/reachability, historical-ID, patch, archive, and secret/ISO scans. |
| Human tester | Apply the final patch outside Codex and perform a short clean-install smoke test using the published instructions. |
| Codex | Publish the corrected package. No patched ISO is distributed. |

## Go/no-go list

- [ ] Actual selectable roster matches randomized starting inventory.
- [ ] Progressive base/Star and hidden golfers behave correctly.
- [x] Locked shuffled main modes reject selection; local modes stay open.
- [ ] Character and Putting-difficulty denial pass controller testing.
- [ ] Clubs, putters, Approach, spins, Power, and Mulligans are enforced.
- [ ] No first-hole leakage, stuck Power/input, or incorrect golfer attribution.
- [ ] Messages neither stack nor crash menus.
- [ ] Every generated location reports exactly once and all goals complete.
- [x] Neil/Ella/custom clubs pass the supported clean-card workflow.
- [ ] Default and complete YAMLs generate and are honestly documented.
- [ ] Windows/AP 0.6.7 passes twice from a blank card.
- [ ] Final deliverables contain a legal patch, not a disc image.
