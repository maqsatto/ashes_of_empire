# Caspian navigation and Caucasian canal: read-only technical spike

3 November 2026. Target inspected: `C:/Hearts of Iron IV`, installed 1.19.3.0.c01a. This document records observed files and a proposed isolated map test. **No map, installed-game, state-history or DLC file was changed during this investigation. No game was launched.** A backup/isolated branch and full restart remain prerequisites to implementing the proposed map changes.

## Finding

The installed Caspian already has four distinct water provinces and its own strategic region. The immediate obstacle is explicit `lake` classification, not a missing bitmap or missing region. A minimal first spike can preserve every province ID, RGB colour and bitmap pixel, convert these four definition rows to navigable sea, mark their forty bordering land provinces coastal, and add a native sea-to-sea canal adjacency to the Black Sea. Whether the engine actually permits fleets, convoys, naval missions and trade through the resulting network must be tested. A drawing or a coastal flag does not prove any of these outcomes.

The native canal mechanism is real: installed Suez and Panama use **`sea`**, not a separate `canal` adjacency type, between sea provinces through a land province, with a named adjacency rule governing army/navy/submarine/trade passage. This supports the proposed method; it does not establish that a much longer invisible Caucasian shortcut will work without additional issues.

## Exact installed map data

`map/default.map` is 504 bytes. Its actual keys point to `definition.csv`, `provinces.bmp`, `positions.txt`, `terrain.bmp`, `rivers.bmp`, `heightmap.bmp`, `trees.bmp`, `continent.txt`, `adjacency_rules.txt`, `adjacencies.csv`, `ambient_object.txt` and `seasons.txt`. It contains **no** `lakes`, `sea_starts` or `impassable_seas` block. Do not insert settings copied from another Paradox game or an old example to solve this installation's lake classification.

`map/provinces.bmp` is 5632 × 2048 pixels. RGB boundary inspection used four-direction pixel neighbours, not colour-name guesses. The four installed `map/definition.csv` records are:

```text
843;4;40;248;lake;false;lakes;0
1050;5;40;232;lake;false;lakes;0
1271;6;40;236;lake;false;lakes;0
1496;7;40;240;lake;false;lakes;0
```

`map/strategicregions/70-Caspian Sea.txt` already contains exactly `843 1050 1271 1496`, ID 70, name `STRATEGICREGION_70`, and twelve weather periods. Installed English localisation calls region 70 “Caspian Sea”. There is no explicit `naval_terrain` assignment in this region. Bitmap contacts connect 843–1050, 1050–1271 and 1271–1496. These are one connected basin; no internal artificial adjacency should be necessary.

| Province | Bitmap bounding box, top-left origin | Calculated water centroid, map X/Z |
|---|---|---|
| 843 | x3552–3640, y589–655 | 3599.02 / 1432.27 |
| 1050 | x3540–3619, y621–715 | 3579.57 / 1380.62 |
| 1271 | x3576–3660, y669–736 | 3618.47 / 1345.78 |
| 1496 | x3569–3648, y718–787 | 3611.10 / 1294.47 |

Map X/Z values here are calculated as X = bitmap x, Z = 2048 − bitmap y. They are measured candidates for later nudge/visual checking, not engine-verified spawn positions. Installed nearby building/unitstack records are consistent with this bottom-origin convention.

Measured neighbouring **land/water pixel pairs** for the port and canal candidates (each pair is one four-direction step across the actual RGB boundary):

| Land province / state | Water province | Land pixel X/Z | Adjacent water pixel X/Z |
|---|---|---|---|
| 1517 / 587 (KAZ) | 1050 | 3612 / 1385 | 3612 / 1384 |
| 3618 / 406 (KAZ) | 843 | 3619 / 1457 | 3619 / 1456 |
| 3668 / 232 (CAU) | 1050 | 3553 / 1380 | 3554 / 1380 |
| 7661 / 229 (CAU) | 1271 | 3588 / 1331 | 3588 / 1330 |
| 772 / 231 (CAU) | 8334 | 3457 / 1363 | 3456 / 1363 |

These are exact observed boundary pixels. Port meshes, ship launch offsets and unit stack placements can require additional offset/nudge work; neither side of a one-pixel boundary is automatically a complete usable naval-base placement.

### Every land province bordering the Caspian

All forty are currently `land;false` in installed definitions. Reclassifying only the water leaves the explicit land coastal flags inconsistent. Their state membership is observed, not invented:

| State ID | Installed state file | Bordering land province IDs | Current provisional mod owner |
|---|---|---|---|
| 229 | `229-baku.txt` | 1536 4458 4473 7495 7661 12434 | CAU |
| 232 | `232-Grozny.txt` | 700 3668 4463 6701 6748 7624 | CAU |
| 236 | `236-Astrakhan.txt` | 757 11736 | SOV |
| 237 | `237-Elista.txt` | 3726 6758 | SOV |
| 266 | `266-Persia.txt` | 4580 7602 10385 10768 | PER |
| 406 | `406-Krasnyy Yar.txt` | 464 615 3618 3622 9453 11578 | KAZ |
| 420 | `420-Gilan.txt` | 4609 4637 4901 | PER |
| 584 | `584-Turkmenistan.txt` | 1593 4563 7477 7563 10406 12359 | TRK |
| 587 | `587-Western Kazakstan.txt` | 475 642 1517 3593 11701 | KAZ |

Owner column reflects the mod's provisional playtest fixture read during this investigation, not approved geopolitical canon. Installed filenames may retain older place names; use actual IDs and current localisation when presenting a location.

## Exact native canal examples

The header in installed `map/adjacencies.csv` is:

```text
From;To;Type;Through;start_x;start_y;stop_x;stop_y;adjacency_rule_name;Comment
```

Installed examples, unchanged:

```text
8857;2284;sea;7617;1560;1009;1556;1016;PANAMA_CANAL;Panama
2729;2408;sea;6257;2949;1598;2962;1612;KIEL_CANAL;Kiel
5388;803;sea;1155;-1;-1;-1;-1;SUEZ_CANAL;Suez
```

Definition inspection confirms Panama's 8857 and 2284 and Suez's 5388 and 803 are sea provinces, while Panama through-province 7617 and Suez through-province 1155 are land. Ordinary land-to-land straits also use `sea`, so endpoint types must be checked rather than inferred from the adjacency word alone. There is no existing special adjacency involving the four Caspian IDs or Black Sea 8334. Preserve all installed rows and the final `-1;-1;;-1;-1;-1;-1;-1;-1` terminator when constructing an override; insert the new row before the terminator.

Installed `map/adjacency_rules.txt` explicitly says the rules control whether **army, navy or trade** can pass. Each rule has `contested`, `enemy`, `friend`, `neutral` blocks with `army`, `navy`, `submarine`, `trade` booleans, plus `required_provinces`, optional `is_disabled`, `icon`, and `offset`. The comments describe how control, war, alliance and military access select these blocks. Suez permits friend and neutral navy/submarine/trade, and denies all contested/enemy passage. Kiel permits neutral trade but denies neutral navy. This distinction is useful: trade access is not automatically naval access.

Suez's `required_provinces = { 12049 1155 4073 9947 }` and Kiel's `{ 317 3231 3368 6257 6389 }` show that rule control can depend on several land provinces even though the CSV has one `Through` value. Suez's `is_disabled` checks global and country flags; it is therefore a native precedent for scripted closure or country-specific transit conditions. Do not add a custom canal building for the first spike. The existing `canal_kiel`/`canal_panama` buildings and damage modifiers are dedicated vanilla content, not a requirement to copy for every new adjacency.

## Measured Caucasian candidate, not a final canal geography decision

Installed `map/strategicregions/30-Black Sea.txt` contains `5412 7906 8131 8256 8282 8308 8334`. Province **8334** is the eastern Black Sea and directly borders CAU's current coast in states 231, 233 and 826. Its definition is `8334;98;0;244;sea;true;ocean;0`.

A four-direction bitmap neighbour graph, restricted to the current CAU-owned fixture states, found this shortest land chain between western Caspian 1050 and eastern Black Sea 8334:

```text
1050 water
3668 — 3682                 state 232, current CAU
3672 — 670                  state 821, current CAU
11609                       state 828, current CAU
9632                        state 827, current CAU
654 — 772                   state 231, current CAU
8334 water
```

These are existing contiguous provinces. The path crosses mountain provinces 11609 and 9632. It establishes a control corridor in the current fixture; it is not a claim of historical engineering feasibility or a newly approved canal route.

The **minimal engine-test candidate** is a single native sea-to-sea shortcut:

```text
1050;8334;sea;3668;3554;1380;3456;1363;AOF_CAUCASIAN_CANAL;AoE isolated Caucasian navigation spike
```

Start point 3554/1380 is an observed water-side boundary pixel between 1050 and 3668. End point 3456/1363 is an observed water-side boundary pixel between 8334 and 772. They are candidate drawing coordinates, not verified UI positions. A corresponding new, prefixed rule could require all eight land provinces:

```text
adjacency_rule = {
    name = "AOF_CAUCASIAN_CANAL"
    contested = { army = no navy = no submarine = no trade = no }
    enemy = { army = no navy = no submarine = no trade = no }
    friend = { army = yes navy = yes submarine = yes trade = yes }
    neutral = { army = yes navy = yes submarine = yes trade = yes }
    required_provinces = { 3668 3682 3672 670 11609 9632 654 772 }
    is_disabled = { has_global_flag = aof_caucasian_canal_closed }
    icon = 3668
    offset = { 0 0 0 }
}
```

This follows observed Suez syntax. The explicit country-policy integration can later use the already-authored `aof_caspian_agreement_accepted` flag to distinguish trade and military rights. The first rule above deliberately tests physical routing with Suez-like neutral permissions; it is **not** presented as the final diplomatic policy. Keep the closure flag unset for the open-route test, then set it to test denial. Required province control and wartime passage must be observed separately. No claim is made that a long shortcut's path length, visual line or mission routing will match its apparent geography.

## Coastal bases, terrain and supply work needed for a meaningful test

- Proposed definition changes preserve IDs/RGB/continent and change only each of the four rows' `lake;false;lakes` to `sea;true;ocean`, matching actual installed sea rows. Change the coastal boolean of all forty bordering land rows to `true`; preserve their terrain and continent. Do not turn a land province into water.
- Keep region 70's provinces and weather intact. `naval_terrain = water_shallow_sea` is a valid installed assignment, observed in regions 16, 170 and 173 and defined under `common/terrain/00_terrain.txt`. Choosing this for the Caspian is a proposed gameplay terrain, not an observed depth classification. Alternatively first test the default with no region terrain override. Do not assign two naval terrains or create a duplicate strategic region ID.
- KAZ needs an actual naval base, not just a shipyard or focus tooltip. Measured candidates are province **1517 / state587**, adjacent to water1050, or **3618 / state406**, adjacent to water843. Installed localisation names them Mangystau and Guryev. Neither current effective state history has a naval base. Neither province appears in installed railway segments or supply-node entries inspected here; an operational port's link to the capital must be checked or deliberately built, not assumed.
- CAU candidate **3668 / state232** touches water1050, already has supply-node entry `1 3668`, and occurs in native railway segments `1 3 3672 3682 3668`, `2 6 7661 7495 4458 7624 4463 3668`, and `1 8 3668 6701 700 6748 3726 6758 11706 9753`. CAU **7661 / state229** is Baku by installed localisation, borders water1271, and has supply-node entry `1 7661`. These are stronger first supply-test candidates than an arbitrary coastal pixel.
- CAU already has a Black Sea base: current effective state231 has province **3653** (Batumi) with `naval_base = 2`. Province **772** (Poti) is the measured Black Sea endpoint's bordering land, but is not a base in that state history. Reuse Batumi for fleet tests if no Poti base is authored.
- `common/buildings/00_buildings.txt` defines naval bases as `is_port = yes`, `spawn_point = naval_base_spawn`, `only_costal = yes`; its naval-base-spawn entry is province based. The misspelling `only_costal` is the installed key and must not be “corrected”. Adding state infrastructure or a dockyard does not substitute for a province-level port.
- Installed `map/buildings.txt` has **no** dockyard/naval spawn records for Caspian-border states229/232/236/237/266/406/420/584/587 inspected here. Author valid measured spawn placements in the mod override when adding bases. Native state231 examples are `231;naval_base_spawn;3458.00;9.60;1361.00;-1.43;8334` and `231;naval_base_spawn;3457.00;9.57;1355.00;-1.89;8334`; the final field identifies the water province. Do not use a state ID as that last field. Caspian water-side coordinate samples: 1517→1050 at3612/1384; 3618→843 at3619/1456; 7661→1271 at3588/1330. Placement height/rotation still need nudge or actual visual checking.
- Installed `map/positions.txt` is empty. Actual map unit placement records are in `map/unitstacks.txt` (10,335,662 bytes inspected). There are records for existing sea8334 and nearby land provinces, but none beginning with Caspian water IDs843/1050/1271/1496. This is a real additional placement risk. If the game reports missing sea unit positions, add measured water-only positions using native unitstack format; do not copy 8334's absolute coordinates into the Caspian. Rendering a fleet on a land pixel would not validate navigation.
- `map/supplyareas` contains a single installed legacy `1-SupplyArea.txt` with states5/85/763/807. It does not define the Caspian network. Current supply data to inspect are `map/supply_nodes.txt`, `map/railways.txt`, province-level naval bases and actual convoy routing. The lake conversion does not author a railway to KAZ's port.
- No new province pixels, heightmap, rivers, terrain bitmap, normal map, cities or strategic-region boundaries are necessary to attempt this minimal shortcut. Keep them unchanged on the first test. The existing lake's rendering/heightmap may still behave differently after sea classification; that is an observed-test question, not a guarantee that no bitmap work will ever be needed.

## Isolated change set and verification

On a separate backed-up branch, prepare exact-path mod overrides for `map/definition.csv`, `map/adjacencies.csv`, `map/adjacency_rules.txt`, region70, and whichever map-building/unitstack placements prove necessary. Patch only the selected port levels in the mod's existing provisional histories or initial setup. Do not edit installed files. Do not use broad `replace_path = "map"` because this proposal intentionally relies on all the unchanged installed map data.

Batch those changes before **one full restart and a new test game**. Old saves are not a reliable map conversion test. The following checks are distinct:

1. Main menu, 1924 bookmark and map load without new critical map/province/strategic-region errors.
2. Region70 is a selectable naval region. KAZ's intended coastal states are genuinely coastal in engine terms; bases are on the selected provinces and fleet sprites/spawns are in water.
3. A real task force can enter all four Caspian water provinces and receive an ordinary mission there. A manually teleported fleet is insufficient.
4. A task force routes from the Caspian base through the candidate adjacency to the Black Sea and returns under permitted control/access conditions. Observe both the path and actual arrival.
5. A real convoy/supply route and a real overseas trade route use the connection. Check convoy demand, route geography, port capacity and supply rather than inferring trade from a naval move.
6. Closed-flag, hostile control and contested-control cases actually deny the intended trade/naval passages. Reopening restores them. Do not equate passing trade with passing military ships.
7. Compare fresh `error.log` against an identical-DLC no-mod run and the non-map v0.3 baseline. Record new errors separately. Check crashes, naval AI pathing and supply behaviour after advancing time.

Only after these actual observations should any normal setup set **`aof_caspian_navigation_verified`**. Existing KAZ and generic maritime gates depend on that flag **and actual coastal ownership/control**. Neither this document, a changed CSV nor a diplomatic agreement should set it automatically. The canal must not silently unlock the normal campaign before these tests.

## Installed-file fingerprints, read-only reference

SHA-256 computed during inspection; these can verify the inputs when creating the separate spike. They are not a claim of successful gameplay testing.

| Installed relative path | SHA-256 |
|---|---|
| `map/default.map` | `AF7037B4BE45C903FC3E136462DCE7071EB468EAC9A50F9D81C48DBF7D6A16F2` |
| `map/definition.csv` | `86846BE71198D6772C651638AA22E3656133198DE9B7C49C6234ED48CF33D87B` |
| `map/provinces.bmp` | `E131D30E5DCB13D9C2A8598F820A2DE0AE9828F3A24F2BDDC1BCFFF40F71660A` |
| `map/adjacencies.csv` | `26A26C3F42A4B01FB905C99659024E857FFC05E3172FCD9953395321FB76ED64` |
| `map/adjacency_rules.txt` | `9D430DEB495F4F4AD20CE4C773A36AED0E2083C7987CF29559FA5ED86A846452` |
| `map/strategicregions/70-Caspian Sea.txt` | `4ADA0E072169BE1EE571E9C1BED9309CFF0321E55FC7F3627B5C39932F4AF7EA` |
