# Native Message Research

The supported 1.0 configuration keeps Archipelago messages in the MGTT client.
This document describes the isolated post-1.0 research path; none of it changes
the stable native hook or enables popups in ordinary rooms.

## Why the earlier popup queue could still crash

The old hook called the retail constructor at `0x80024F1C`, retained the
returned object, and later called the destructor at `0x80024C98`. Queue
serialization prevented two AP objects from stacking, but it did not give that
object a native screen owner. Retail result, save, Ring Attack-clear, and menu
transition code could free or traverse the same UI allocation independently.
The resulting stale text/object pointers match the repeated invalid reads at
`0x800246C8` and `0x800246CC`.

Shorter timers and larger cooldowns reduce the collision window but cannot
prove ownership, so they are not a complete fix.

## Promising alternative: piggyback on a retail-owned message

Read-only DOL analysis found a retail frame manager at
`0x80018F90..0x80019150`. It:

1. owns its popup pointer at `0x802C7E10`;
2. compares the previous and requested message states;
3. destroys the old object itself at `0x80019064`;
4. constructs the replacement at `0x80019148`; and
5. immediately stores the new object back into its own pointer slot.

An experimental renderer can replace the text only when that retail manager is
already constructing a message. It would advance one AP queue entry after the
constructor returns, while leaving creation, lifetime, transition cleanup, and
destruction entirely under retail control. This is safer than creating an
additional popup from the AP frame hook.

Tradeoffs:

- delivery waits for a suitable retail message event;
- the AP text temporarily replaces that native message;
- the call site must be controller-verified across normal play, results, and
  transitions before it is exposed as a YAML option.

## Capture support added

`/mgtt_capture <label>` now records these read-only fields:

- `retail_popup_owner_pointer`
- `retail_popup_last_state`
- `retail_popup_target_state`

The standalone `tools/analyze_popup_callers.py` script lists every direct
constructor/destructor caller and can disassemble a selected runtime range.

## Focused capture sequence

Use the normal stable APWorld/ISO with native AP popups disabled:

1. At an ordinary live tee with no retail message visible, run
   `/mgtt_capture message-owner-idle`.
2. When the game displays a normal one-line gameplay/help message, remain on
   that frame and run `/mgtt_capture message-owner-visible`.
3. After it disappears naturally, run
   `/mgtt_capture message-owner-retired`.
4. Trigger a native score/result message and run
   `/mgtt_capture message-owner-result` while it is visible.
5. Return to a menu and run `/mgtt_capture message-owner-menu`.

If the owner pointer is nonzero only for the ordinary managed message and
returns to zero on retirement/transition, the next step is a separately named
piggyback probe ISO. It must never be merged into the 1.0 patch before that
probe survives queued receipts, results, save-and-exit, and Ring Attack.
