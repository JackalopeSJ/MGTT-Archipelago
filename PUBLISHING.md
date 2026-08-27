# GitHub and wiki publishing guide

## Repository preparation

1. Extract `MGTT-Archipelago-1.0.0-RC1-Source.zip` and use the contained
   `mgtt-archipelago` folder as the repository root.
2. Review the author name in `mgtt/archipelago.json` and replace
   `MGTT Archipelago Team` with the preferred public credit if desired.
3. Add the eventual repository issue URL to `MGTTWeb.bug_report_page` in
   `mgtt/__init__.py` after the repository exists.
4. Commit the source, tag it `v1.0.0-rc1`, and create a GitHub prerelease.

The distributed APWorld must remain named exactly `mgtt.apworld`: Archipelago's
APWorld specification requires a lowercase archive name whose internal folder
has the matching `mgtt` name.

## RC1 release assets

Upload these files from the workspace output folder:

- `MGTT-Archipelago-1.0.0-RC1.zip`
- `mgtt.apworld`
- `MGTT-Archipelago-Patch-1.0.0-RC1.zip`
- `MGTT-PopTracker-1.0.0-RC1.zip`
- `MGTT-1.0.0-RC1-Item-and-Location-Catalog.xlsx`
- `MGTT-Archipelago-1.0.0-RC1-Source.zip`
- `MGTT-Archipelago-1.0.0-RC1-SHA256.txt`

Paste `RELEASE_NOTES_1.0.0-rc1.md` into the GitHub release description. Mark
the release as a prerelease until the Speed Golf acceptance pass is complete.
Never upload the clean or patched ISO.

## GitHub wiki

Enable the repository wiki and create pages using the files under `wiki/`:

- `Home.md`
- `Installation.md`
- `Options.md`
- `Goals-and-Checks.md`
- `Known-Limitations.md`
- `Troubleshooting.md`

The links in `Home.md` already use GitHub Wiki page names.

## Promote to final 1.0.0

After the Speed Golf checklist is accepted:

1. Change `world_version` and `build_version` in `mgtt/archipelago.json` to
   `1.0.0`.
2. Change the PopTracker's APWorld/build labels to `1.0.0`.
3. Regenerate the catalog and all release artifacts.
4. Run the full automated suite and archive scans again.
5. Tag `v1.0.0`, create a non-prerelease GitHub release, and upload the final
   assets. Do not overwrite RC1 assets in place.

Official references:

- APWorld specification: https://github.com/ArchipelagoMW/Archipelago/blob/main/docs/apworld%20specification.md
- Custom-world installation: https://archipelago.gg/tutorial/Archipelago/setup_en
