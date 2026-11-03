# Grozny–Krasnodar river-rendered canal: source-only proposal

3 November 2026. Authoring output: `tools/build_v03_canal_visual.py`. Only read-only construction and labelled inspection-artifact generation were run. **No runtime bitmap, province definition, province pixel, naval adjacency, country history or verified-navigation flag was written.** The parent owns any later closed-game application and restart test.

## Observed native input

Installed `C:/Hearts of Iron IV/map/rivers.bmp` is 5632×2048, indexed modeP, 8bits per pixel, uncompressed, 40-byte BITMAPINFOHEADER, pixel offset1078 and row stride5632. The two palette-count header fields are zero. Its native data has two trailing bytes after the pixel plane. SHA-256: `4491190a65771592ebffdb3479eae519b3b5623bfaca41500b1e2e4a38caba71`.

Actual palette entries used by the candidate:

| Index | Actual RGB | Use in this proposal |
|---:|---|---|
| 0 | 0,255,0 | One technical rendering-source marker |
| 1 | 255,0,0 | Existing native red markers preserved, no new joins authored |
| 2 | 255,252,0 | Existing native yellow markers preserved, no new splits authored |
| 3 | 0,225,255 | Existing narrow river strokes and short artificial canal connectors |
| 4 | 0,200,255 | Native width retained where present |
| 6 | 0,100,255 | Native width retained where present |
| 7 | 0,0,255 | Native width retained where present |
| 254 | 122,122,122 | Existing water background |
| 255 | 255,255,255 | Existing land background; restored at the replaced bypass |

Other native width indices are9/10/11; no width indices or colours are invented. The installed files contain no river-format specification found in this inspection. An official Paradox wiki request returned unauthorized. The source-marker interpretation and orthogonal path checks use actual native components: all317 native green pixels have one river neighbour;315 of328 native orthogonally connected components have exactly one green marker. Existing red/yellow markers were inspected but their engine semantics are not guessed to create a new branching junction. The proposed combined channel is an unbranched simple path, so it needs no new red/yellow markers.

## Native rivers and new artificial works

The nearby eastern river is119 pixels, with source `(3473,661)` and Caspian-water terminal `(3560,650)` in water province1050. The western Kuban path is147 pixels, with source `(3468,661)` and terminal `(3385,628)` in coastal land6741. Directly below that terminal `(3385,629)` is **Black Sea8308**. Both native components are simple orthogonal one-pixel paths with two endpoints and no branches or cycles.

The city anchors come from actual native `map/unitstacks.txt` slot0, converted to top-left bitmap coordinates: Grozny province3672 is `(3518,662)`, and Krasnodar province3734 is `(3415,624)`. **Grozny3672 has zero native river pixels.** Krasnodar3734 already contains nine river pixels. The two river sources are only five pixels apart, allowing most existing river geometry to be reused.

The proposal makes these explicit artificial changes:

1. Connect the two headwaters along image y661 between x3468 and3473. Four previously white land pixels become blue index3; the two existing green head markers become blue.
2. Replace the short eastern-river bypass between hooks `(3516,655)` and `(3524,658)` with a narrow orthogonal detour via `(3516,662)` → **Grozny `(3518,662)`** → `(3524,662)`. Nine native bypass pixels are restored to white ground. This is newly authored canal excavation, not an existing river through the city.
3. Move the single technical green rendering marker to the existing Caspian endpoint `(3560,650)`. The resulting river-renderer graph is one unbranched channel from the Caspian to the Kuban's Black Sea mouth. This is not a claim that a natural river flows out of the Caspian; it is a technical orientation of the fictional canal's renderer.

The candidate contains278 continuous channel pixels, **257 reused native river pixels**, and33 changed bitmap bytes overall. It passes through the actual Grozny anchor and Krasnodar province, has exactly one green source and no branches, cycles, diagonal-only connections or thick 2×2 channel blocks. No other native rivers or markers are edited.

## Navigation versus the visible channel

This writes only `map/rivers.bmp`. It never turns the underlying land pixels into sea, adds province IDs, changes national borders, or authorises ship movement. Actual fleets/trade still need the separate native sea-to-sea canal adjacency, owned by the parent/Pacific map generator.

Historical inspection, superseded by the applied route below: the first adjacency ended at8334/land719, away from the native Kuban mouth8308/land6741. The current adjacency uses8308 and the31control provinces from the actual ordered river trace. This fixes the data alignment; actual naval passage remains unverified.

`rivers.bmp` is native technical map data, not a guaranteed cosmetic overlay. Altering its strokes may change river-crossing/combat or supply behaviour. Marker interpretation, animation, widths, actual appearance and stability remain **UNVERIFIED in-game**. A labelled data preview does not count as a screenshot or completed navigation test.

## Encoding preservation and inspection artifacts

The generator does not re-save the game bitmap through an image encoder. It verifies the original SHA-256, uses the actual indexed pixels to construct/check a candidate in memory, then patches only changed pixel-byte offsets in a copy of the original BMP. Every header byte, palette entry, row layout, resolution field and native trailing byte is retained. A decoder round trip confirms modeP, palette identity and exact proposed pixels.

Read-only command used:

```powershell
& 'C:/Users/maqsatto/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' tools/build_v03_canal_visual.py --inspect --report-dir docs/verification/canal_visual
```

Artifacts:

- `docs/verification/canal_visual/canal_data_overlay.png` — explicitly labelled map-data preview; blue native rivers, orange changed/authored channel, red removed bypass, city anchors and province boundaries. Visually inspected as an annotation, not an in-game image.
- `docs/verification/canal_visual/canal_visual_inspection.json` — exact changed coordinates/indices, preserved encoding fields, native palette values, counts and risks.

## Later application: separate new backup, game closed

Both mutating modes require the exact `spike/caspian-navigation` branch and no running HOI4 process. `--prepare-backup` requires a fresh explicit absolute directory outside the repository/installation. It snapshots **all current mod map files**, both existing test-port histories and native river/province/definition/default-map inputs, with commit and SHA-256 hashes. It does not write mod runtime files.

Example for the parent's later batch:

```powershell
& 'C:/Users/maqsatto/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' tools/build_v03_canal_visual.py --prepare-backup C:/Users/maqsatto/.codex/backups/ashes_of_empires/canal-visual-20261103
& 'C:/Users/maqsatto/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' tools/build_v03_canal_visual.py --apply --backup-dir C:/Users/maqsatto/.codex/backups/ashes_of_empires/canal-visual-20261103
```

Apply verifies the backup, branch, baseline commit ancestry, unchanged installed inputs and unchanged backed-up map/history files, and refuses to overwrite an intervening river edit. It writes only the proposed river bitmap and an applied-report document. Complete the parent's other map changes **before** taking this new snapshot. Full restart/new-game and fresh-log comparison are still mandatory; the verified-navigation flag remains unset by this generator.

## Accepted source alignment: 31 control provinces, not the older eight-province shortcut

The parent accepted the33-byte visual proposal and requested the separate naval adjacency to follow the same river mouths. The updated **source** in `build_v03_caspian.py` now proposes:

```text
1050;8308;sea;3672;3551.5;1397.5;3385.5;1418.5;AOF_CAUCASIAN_CANAL;AoE Grozny-Krasnodar river-canal spike
```

The through/icon province is Grozny3672. Coordinate centres are computed from observed bitmap pixels as X=x+0.5 and Z=2048−y−0.5: eastern water1050 pixel3551/650 becomes3551.5/1397.5; western water8308 pixel3385/629 becomes3385.5/1418.5. Eastern bordering land is700 in state232, and western bordering land6741 is in state234. The two existing test bases remain KAZ1517/state587 and CAU3668/state232; this does not create additional bases.

All31 unique land provinces touched by the actual278-pixel channel are required for control. They lie in seven current provisional CAU-owned and CAU-controlled history states:

| State | Exact required land IDs |
|---:|---|
| 232 | 700, 6701, 3682, 6730, 683, 11632 |
| 821 | 3672 |
| 235 | 6702, 6733, 6718, 11633, 714, 11678, 11696, 9726 |
| 828 | 9647 |
| 827 | 685, 6674 |
| 233 | 9649, 11664, 6692 |
| 234 | 9694, 735, 9709, 11681, 6768, 3734, 9696, 3760, 11729, 6741 |

No channel land belongs to KAZ or state236. These statements describe inspected initial history files, not live wartime ownership read from game memory. The exact ordered trace contains71 land runs because river pixels repeatedly cross neighbouring province borders. The unique first-appearance ID order is **not** a contiguous linear province chain. The map generator now constructs the accepted visual path in memory and validates its actual ordered pixels/runs; it no longer tests adjacent pairs of the unique control list. `docs/verification/canal_visual/canal_actual_province_route.json` records the detailed pixel-run/state/owner inspection. The debug canal controls automatically require all31 provinces and all seven states, and their text now says31.

Read-only validation against the original prepared Caspian snapshot passed deterministic generation of eight proposed map/history outputs, the new native adjacency/rule,31 required IDs,71 ordered land runs,40 nudger spawns and native no-terminal-newline building format. Debug fixture generation also passed its native input checks against those proposed map bytes held in memory. **No runtime output was written during these source checks, and no canal movement/rendering success is claimed.**

The Caspian applier recognises previous output hashes from the same Caspian backup/base commit. It additionally recognises only `USER_STATE_EDITS_MANIFEST.json` and `KAZ_REGIONS_MANIFEST.json` outputs with the exact isolated branch and matching `upstream_caspian_backup_directory`/`upstream_caspian_base_commit`. Unknown intervening bytes still abort. This allows rebuilding an earlier pipeline stage; it does not preserve the later stage automatically. The parent must reapply user state edits and KAZ regions **after** Caspian so their authorised building-state remaps and regional histories remain final. Pacific confirmed port1517 stays anchored to retained state587.

For re-inspection after the original bases already exist, use the original immutable snapshot rather than current post-apply histories:

```powershell
& 'C:/Users/maqsatto/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' tools/build_v03_caspian.py --inspect --backup-dir C:/Users/maqsatto/.codex/backups/ashes_of_empires/caspian-e397dd0
```

The old snapshot lacks validation-only metadata for states233/234/235, which were outside the earliest eight-province proposal. The source now reads those three current history files only for owner/province-membership validation and records their hashes; it does not write those histories or infer that an old backup already contained them. The separate fresh visual-stage backup remains required before writing `rivers.bmp`.
