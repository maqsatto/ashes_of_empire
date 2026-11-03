# v0.3 common framework: implementation record, 3 November 2026

This is an implementation record, not an addition to pre-campaign canon.

`tools/build_v03_core.py` generates 117 native shared focuses in one default focus tree. Countries with a bespoke tree retain that tree. The default tree must load without the vanilla default or the earlier pilot taking precedence. Its independent administration, industry, funding, schooling, politics, army, aviation, coastal and diplomacy branches do not require completing a political route first.

War recovery is selected by current war, `aof_war_exhausted`, or an owned state bearing `aof_war_damaged`. Other countries get peacetime conversion. These are contextual starting branches, not a diagnosis of damage automatically inferred from unapproved lore. Independent and subject diplomatic entries differ. Maritime focuses require an actual owned and controlled coastal state, and KAZ additionally requires global `aof_caspian_navigation_verified`. They never create a Caspian map or claim the canal works.

The regional column supplies FIN, MAN, FER, TRK, RAJ, PAK, CAN, GUA/HON/ELS/NIC/COS/PAN, BOL/PAR and VEN. FIN representation/security, TRK local/common government, RAJ civilian/emergency command, CAN oceanic/continental ties and VEN exports/technicians are event choices. MAN/FER/RAJ/PAK use the parent's reciprocal `aof_diplomacy` events; neighbours can decline cooperation and investment. Invitation focus completion does not imply agreement.

Six ideology groups are defined by the exact installed `00_ideologies.txt` filename override. The four original group keys and every installed subtype/rule are retained. Group display names become liberalism, revolutionary socialism, authoritarianism and radical nationalism. New groups are `aof_social_democracy` and `aof_conservatism`. All six groups have new prefixed subtypes, with compatibility aliases retained in the original families for vanilla character references. History files can set `ruling_party` and `set_popularities` using all six group keys. Generic political settlements actually enact liberal/conservative constitutional, social-democratic or authoritarian government with appropriate election rules. Revolutionary and radical-nationalist branches appear only with existing matching government or over 20 percent support, and require three prepared focuses before enactment. Existing leaders referring to legacy subtypes are intentionally not globally rewritten. Party/interface behaviour with additional groups needs an actual game test.

The research adaptation changes only 115 explicitly selected native technology start years in ten exact-filename overrides. `RESEARCH_DATE_MANIFEST.json` records installed and selected dates per key. Industry and extraction span 1924/1927/1931/1935/1938; communications, basic weapons, support companies, trucks, light armour, medium armour, aircraft and basic naval hulls/support receive staged dates. Both legacy and designer tank/aircraft variants are covered. `basic_light_tank` and `basic_light_tank_chassis` are 1924. Existing native nodes, effects, equipment, prerequisites, DLC visibility and positions are retained. A node lacking an explicit installed date receives one. This deliberately does not make every technology a 1924-era technology: advanced jets, nuclear technology, rockets, late modern equipment and most special-project unlocks retain installed dates. All staged research links were checked for prerequisite-date inversions; no new inverse links remain. The pre-existing native trucks-to-1914-armoured-car date inversion is retained. Unchanged native AI date heuristics and technology folder artwork can still show vanilla-era design assumptions. No comprehensive new research interface is claimed.

Installed 1.19 uses grand doctrines, subdoctrines, tracks and mastery. Ten military-school focus choices support those native systems through XP, limited doctrine-cost reductions and installed grand-doctrine mastery modifiers; the expeditionary school instead improves organisation and supply consumption. Three naval and three air routes give different mastery support. They neither replace the new doctrine database nor force the player's doctrine selection. There are 16 shared national spirits in total.

## Deliberate limits

- Central American territorial union is the optional final focus/event choice for GUA/HON/ELS/NIC/COS. Each peaceful independent receiver needs a prior accepted bilateral cooperation flag and explicitly accepts transfer of its own states and troops; both participants must control all their owned states. AI acceptance is weighted 1 versus refusal 99. Acceptance grants cores only on consenting receiver-owned states that were already that receiver’s cores, annexes only that receiver and applies cosmetic federation names for all six ideology families. A sovereign compact remains available. The explicit event warning explains that acceptance ends a separate campaign. No automatic historical union is claimed.
- The Turkestani regional event opens separation negotiations; the parent world package owns actual successor-state partition, if implemented.
- BOL/PAR can discuss Chaco and prepare supply; this package does not invent a limited-war peace script or transfer disputed provinces without an agreed map.
- Treaty/conference rewards currently consist of native opinion, stability, experience, reciprocal alliance proposals or negotiation flags. They are not an economic simulation.
- The concession path costs a civilian factory for two years. A rejected investment proposal can be funded domestically for political power; no foreign acceptance is silently assumed.
- No custom ideological icons, flag assets or interface widening have been authored. These need visual verification before claims about the six-family politics panel.

## Verification actually performed

Generated script braces were balanced for 15 files, ignoring strings/comments. All 117 focus IDs are unique, prerequisites/exclusions resolve inside the framework, all focus names have both localisations, and 22 triggered event definitions cover all `aof_v03_regions` references. Both localisation files have UTF-8 BOM and unique keys (438 entries per language). All selected technology IDs were found in the installed game. Repeat generation preserved bytes and modification times. Native focus icon and idea-picture names were inspected in installed interface definitions. Grand-doctrine IDs and mastery modifier formation were inspected in the installed doctrine database and its documentation.

No game was launched for this package. Launcher appearance, reaching the 1924 map, additional ideology UI, actual event scope/replies, military mastery effects, research dates displayed on screen and fresh error-log cleanliness remain UNVERIFIED. Static checks are not gameplay verification. History/map/new files/idea changes require one batched full restart under the repository's test instructions.

## Authored output files

- `common/national_focus/aof_v03_generic.txt`
- `common/ideas/aof_v03_core.txt`
- `common/ideologies/00_ideologies.txt`
- `common/opinion_modifiers/aof_v03_core.txt`
- `events/aof_v03_regions.txt`
- `localisation/english/aof_v03_core_l_english.yml`
- `localisation/russian/aof_v03_core_l_russian.yml`
- `common/technologies/industry.txt`
- `common/technologies/electronic_mechanical_engineering.txt`
- `common/technologies/infantry.txt`
- `common/technologies/artillery.txt`
- `common/technologies/NSB_armor.txt`
- `common/technologies/armor.txt`
- `common/technologies/bba_air_techs.txt`
- `common/technologies/air_techs.txt`
- `common/technologies/support.txt`
- `common/technologies/MTG_naval.txt`
- `docs/design_v0_3/RESEARCH_DATE_MANIFEST.json`
