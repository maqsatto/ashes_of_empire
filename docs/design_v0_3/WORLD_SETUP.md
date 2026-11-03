# Provisional 1924 playtest world

These are explicitly provisional fixtures, not approved historical geography, capitals, flags or personnel. The immutable lore is represented through separate independent Kazakhstan, Siberia, Caucasus and Turkestan; distinct Japanese dependencies are configured by the startup owner. No map geometry is changed.

The generator reads installed state history and preserves native resources, population, geometry and infrastructure. Only owner/controller, additional fixture-country cores, minimum capital industry and matching additional building slots change; Nanjing and Sind additionally receive one airbase level for their early fighter wings. Future-dated state blocks are removed from changed states so 1939 history cannot silently reverse the fixture. Detailed state IDs, installed names, source owners, capital provinces and troop placements are in WORLD_MANIFEST.json.

KAZ uses installed Soviet-owned Kazakh-core states. TRK uses installed Soviet-owned Uzbek, Turkmen, Tajik and Kyrgyz cores. CAU includes states 229–235, 821, 826–828 and one Turkish border region, state 354 (Trabzon). The owner explicitly limited the Turkish allocation to one or two adjacent border regions; the generator chooses the minimal one. Native provinces.bmp confirms that state 354 directly borders both Armenia 230 and Georgia 231: Ardahan province 10403 touches Gyumri 12441 and Georgian province 3656. State 354 contains Trabzon 9932, Kars 10472, Gümüşhane 3979 and Erzurum 11853. The previous state 353 allocation was an erroneous enclave: its filename says Erzurum, but its actual state name and victory points are Tunceli, Xarpêt and Erzîngan. The cold builder removes only its exact unmodified prior generated override, restoring native Turkish ownership and removing the added CAU core; independent edits cause a safe abort. State 355 is Samsun and does not border the Caucasian fixture. This limited-border instruction does not approve other provisional capitals or unspecified geography. SIB and FER use the reviewed explicit lists. Finland additionally owns Onega and Olonets, never Leningrad; Murmansk is retained by Soviet Russia because it is not Karelia. NAF combines French/Italian-owned Moroccan, Algerian, Tunisian and Libyan core territory, excludes Egypt and Spanish possessions. CMT temporarily occupies Togo state 777. Pakistan receives western native Pakistani cores; East Bengal 430 and contested North Kashmir 787 remain with India.

Eighteen named countries receive native six-battalion infantry formations placed in owned states; numbers and readiness are balance fixtures. Named 1936 historical leaders are replaced by localised generic institutional cabinets for all six political families. Initial research uses early native technology and small research-slot counts. USA receives the 1924 light tank technology, not a fabricated model designation. USA/Japan have compact original early naval fixtures with separate MTG/legacy definitions; these deliberately do not reproduce historical fleet sizes or import later-era ships. USA, Japan, China, India and Pakistan receive respectively 100, 80, 30, 40 and 20 early fighters, with separate BBA and legacy OOBs. Named equipment variants precede their OOB loads. All other countries retain installed history/OOB until separately curated.

Native foreign air OOBs still request USA variants P-6, P-26A and O2U: obsolete aliases with early modules preserve those references without endorsing their names as 1924 canon. Soviet Russia has a basic early light-chassis design and an obsolete same-module compatibility alias named "T-26TU mod. 1933", required by native Turkish OOB lookup; its name is not a 1924 historical assertion, and no 1933 improved modules or design bureau are imported. Procedural names for the five custom tags borrow native SOV/GEO/UZB/MOR/TOG personal-name pools; these technical defaults neither appoint historical leaders nor determine an approved population composition.

The owner separately authorised states 582 (Magnitogorsk), 652 (Orenburg) and 236 (Astrakhan) for Alash. Province corrections 4265/10185 to Ufa 651, 1334 to Zlatoust 573, and 3265/4324/227 to Kuybyshev 251 are applied by the isolated, backed-up state-edits stage after the world and Caspian generators. No other geography or capital is approved by that request. Astrakhan is distinct from Stavropol 235 and is outside the current canal corridor. Province IDs, railways and supply-node identities are retained.

Five custom tags use original geometric placeholder TGA flags in all sizes and political variants. Added ideology-family flags for native tags copy the corresponding democratic flag from this same local game installation; these are compatibility fallbacks, not approved vexillology. No third-party artwork or mods are used.

Parent startup owns national spirits, diplomatic dependencies, war setup and scenario-wide adjustments. This builder never edits on-actions. World files require a full game restart; no actual launch, load or error-log verification has been performed by this builder.

| Tag | Capital state | Infantry divisions | Research slots |
|---|---:|---:|---:|
| KAZ | 586 | 8 | 2 |
| SIB | 570 | 12 | 3 |
| CAU | 230 | 8 | 2 |
| TRK | 405 | 7 | 2 |
| NAF | 458 | 10 | 2 |
| CMT | 777 | 2 | 2 |
| FER | 408 | 7 | 2 |
| USA | 361 | 30 | 4 |
| JAP | 282 | 26 | 4 |
| SOV | 219 | 30 | 3 |
| MEX | 277 | 12 | 3 |
| BRA | 500 | 12 | 3 |
| ARG | 278 | 10 | 3 |
| CHI | 1035 | 24 | 3 |
| MAN | 328 | 9 | 2 |
| RAJ | 439 | 18 | 3 |
| PAK | 443 | 12 | 2 |
| FIN | 111 | 8 | 3 |

Static verification confirmed valid installed technology identifiers, province membership and owned capitals, unchanged state geometry/infrastructure, balanced braces, six-family popularity totals and flag dimensions. Repeated generation preserved bytes and modification times. These checks are not an in-game test.
