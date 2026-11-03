# Inert native identifier compatibility registry

3 November 2026. The first v0.3 game boot reached the menu, but the retained installed MIOs/scripted effects still refer to native focus/decision/event identifiers whose gameplay files are intentionally excluded by the mod's loading configuration. The parent observed thousands of unresolved native-focus checks. This registry addresses identifier resolution without restoring 1936 national trees, decisions or event plots.

## Current state: generator authored, runtime outputs NOT generated

`tools/build_v03_compat.py --inspect` was run against `C:/Hearts of Iron IV`. Inspection parses and validates the proposed output **in memory**. It does not write any runtime script or manifest. The active debug process must not receive new files during this work. All five proposed runtime paths were confirmed absent after inspection.

Run `tools/build_v03_compat.py` **only after HOI4 is closed**, together with the planned map/content batch before a full restart. Default generation includes a native Windows process check and refuses to write if any `hoi4` process is running. This guard does not close the game or alter saves. It also refuses runtime generation on a host where that process check cannot run.

## Installed metadata extracted

| Database | Installed files parsed | Unique identifiers |
|---|---:|---:|
| National focus/shared/joint focus | 81 | 10,948 |
| Decisions, excluding category-definition folder | 88 | 4,148 |
| Events | 128 | 6,974 |
| Used event namespaces, from original declarations | — | 434 |
| Native focus-border style names | — | 22 |

Event types are retained: 6,251 country events, 677 news events, 33 unit-leader events, seven operative-leader events and six state events. There were no numeric-only event IDs in these installed files. Four original Missiolini IDs have `_north`/`_south` suffixes; these literal identifiers are preserved instead of converting them to invented numeric IDs. `MUN_czech.news` is an actual dotted native namespace. `BBA_Switzerland` is the original namespace declaration while its native event IDs use `BBA_switzerland`; original declaration spelling and original event-ID spelling are retained.

Extraction uses a small nested-block parser with quoted-string/comment tokenisation. Focus IDs are taken from actual `focus`, `shared_focus` and `joint_focus` definition blocks. Decisions are taken from direct decision definitions inside the top-level category blocks, not from nested triggers/effects or the separate category folder. Events are taken from top-level event-definition blocks; nested `country_event = { id = ... }` calls are not treated as definitions. No original prerequisites, effects, costs, plot text, AI logic or national assets are copied.

One installed-source parsing defect was observed: `common/national_focus/TSR_lingguang_incident_joint_branch.txt` has an extra final closing brace (line420 in the inspected file). Metadata extraction ignores that unmatched top-level brace and records a warning. It does not edit the installed file or reproduce its structural defect in the authored output. No other parser warnings were found.

## Generated behaviour

- All 10,948 native focus IDs are registered as inert dummy focuses in the non-default `aof_compatibility` tree, whose country factor is zero. Each has only its original ID, a generic installed icon, cost1 and `available = { always = no }`. There are no completion rewards, national conditions or prerequisites from the original trees. The registry is not a playable focus tree and is not assigned to any country.
- All 4,148 native decision IDs are placed in the unique `aof_legacy_compat` category. The category and every decision are both invisible and disallowed; individual decisions are also unavailable and have zero AI weight. There are no effects or native mission timers.
- All 6,974 events retain their native ID, original event type and an actually declared native namespace. They are hidden, triggered-only, have an always-false trigger, and a single effectless option. Even if a retained native caller refers to one, it cannot run an old plot. The hidden option's `aof_compatibility_noop` label is not presented as player content.
- The replaced focus folder also removed its native border-style definitions. `00_titlebar_styles.txt` therefore registers the 22 original style names with the installed generic unavailable/completed/available/current sprites. Only `default_style` is the default. This restores border metadata, not native country focus content or special joint-focus behaviour.

The source identifier registries have no duplicates either literally or ignoring letter case. The generator also checks against currently active mod definitions, excludes AoE-prefixed identifiers, validates every proposed output with the nested parser in memory, and rejects accidental gameplay-effect fields. It deduplicates definitions rather than generating two entries for one ID. Future installed patches or new mod files must be re-inspected instead of assuming these counts remain constant.

## Outputs when later generated with the game closed

1. `common/national_focus/aof_compatibility_registry.txt`
2. `common/national_focus/00_titlebar_styles.txt`
3. `common/decisions/aof_compatibility_registry.txt`
4. `common/decisions/categories/aof_compatibility_registry.txt`
5. `events/aof_compatibility_registry.txt`
6. `docs/design_v0_3/COMPATIBILITY_REGISTRY_MANIFEST.json` — exact source-path provenance for each identifier, namespace declarations, counts and parsing warnings.

The proposed runtime scripts total about three megabytes. This is intentionally inert compatibility metadata and must not be counted as newly implemented gameplay. No archived MVP or vanilla generic tree is reactivated. The mod's intentional replacement settings remain the parent's responsibility; removing those replacements would load active native definitions again and cause conflicts with this registry.

## Verification limits and next observation

The authoring script and all proposed output structures passed read-only static inspection; there are no source/mod ID collisions, missing declared namespace mappings or generated brace errors in that inspection. No runtime files were written, no game reload occurred, and no claim is made that the fresh game log is clean after this shim.

After the closed-game generation and full restart, inspect a fresh log to determine whether the retained MIO and scripted-effect focus references now resolve. Compare native baseline errors separately. Confirm the ordinary v0.3 trees and decisions remain the only playable content and that the compatibility tree/category never appear. Check for engine complaints specific to hidden non-country event types or metadata-only decisions. Registry identifiers can make `has_completed_focus` checks safely false; they do not recreate the economic or political effects those native scripts would have expected from a real 1936 campaign. Behavioural compatibility is deliberately not promised.
