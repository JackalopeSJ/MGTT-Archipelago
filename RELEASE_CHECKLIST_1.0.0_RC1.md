# MGTT 1.0.0 RC1 release checklist

## Automated gates

- [ ] Compile every packaged Python file.
- [ ] Run the complete unit suite against Archipelago 0.6.7.
- [ ] Generate and restrictively fill every supported option-matrix case.
- [ ] Generate every bundled YAML and confirm its goal is beatable.
- [ ] Confirm all published item/location IDs are unchanged.
- [ ] Build the APWorld twice and compare hashes for determinism.
- [ ] Validate every ZIP and confirm no ISO, GCM, RVZ, WBFS, save, credential,
      diagnostic, or RAM capture is present.
- [ ] Apply the legal sparse patch to the supported clean ISO and verify the
      output hash against the patch manifest.
- [ ] Confirm the RC PopTracker and APWorld use world version 0.99.0. The final
      promotion must bump both to 1.0.0.

## Final human Speed Golf test

Use one room with `speed_golf_checks: true`, the matching RC1 APWorld/patch,
and a dedicated memory card.

1. Finish the first hole in **more than 15 seconds**. Confirm the fast-hole
   check does not report.
2. Finish a later hole in **under 15 seconds**. Confirm
   `Speed Golf - Finish a Hole Under 15 Seconds` reports once.
3. Finish the 18-hole round in **under 10 minutes** and **under par**.
4. Confirm both of these report once:
   - `Speed Golf - Finish <Course> Under 10 Minutes`
   - `Speed Golf - Finish a Round Under 15 Minutes and Under Par`
5. Restart Dolphin and reconnect. Confirm none of the three checks duplicates.

If any result is wrong, save `/mgtt_diagnostics speed-golf-rc1` while the final
scorecard is still visible and capture that screen. One course is sufficient;
automated coverage verifies the six course-index mappings.

## Promotion decision

- [ ] Speed Golf passes: promote the RC1 code unchanged and rebuild the
      manifest/artifact labels as 1.0.0.
- [ ] Speed Golf fails: keep the package disabled by default, document it as
      experimental, and promote the stable core without delaying 1.0.0.
