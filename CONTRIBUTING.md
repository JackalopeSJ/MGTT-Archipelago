# Contributing

Bug reports and controller-test results are welcome. Include the release
version, platform, Archipelago version, Dolphin version, YAML options, exact
reproduction steps, and a sanitized `/mgtt_diagnostics` file when possible.

For code contributions:

1. Preserve every published item and location ID.
2. Add automated coverage for changes to generation, memory reads/writes, or
   option behavior.
3. Run the full suite against Archipelago 0.6.7.
4. Do not commit game images, patched images, save files, RAM captures,
   credentials, or copyrighted game data.
5. Keep the recommended YAML inside the documented stable support boundary.

Reverse-engineering captures should be shared privately with the maintainer
until they have been reviewed for credentials and unrelated memory contents.
