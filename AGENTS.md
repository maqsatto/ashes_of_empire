# AGENTS.md — Ashes of Empires HOI4 mod

## Priorities
1. Respect `docs/LOREBOOK.md`. `[CANON]` is immutable without explicit creator decision; `[PROPOSAL]` and `[TBD]` are not canon.
2. Keep the mod loadable and testable after each small change. Prefer vertically sliced increments over a large untested total conversion.
3. Inspect the **installed HOI4 game** for files/keys/state IDs/province IDs/country tags before writing mod data. Never invent IDs or assume a wiki example applies to the installed patch.
4. Do not edit the game's installation or DLC files. Work in this repository; install via copied mod or safe junction/symlink only when appropriate.
5. No third-party mod dependency or copied third-party assets without explicit permission.
6. Record uncertainty, tested behavior, and open questions in `docs/TECH_NOTES.md`; update `docs/LOREBOOK.md` changelog for any approved canon addition.
7. A game map edit (`map/`, provinces, sea zones, strategic regions) requires a separate commit/branch, backups, and a full restart test.

## Gameplay scope of the earlier boot MVP (superseded where noted below)
- Use **existing HOI4 game mechanics only** for present development: focus trees, events, decisions, national spirits, ordinary economy/resources/trade/diplomacy, research bonuses, and wars.
- Do not implement custom global economic, migration, federation, excavation or postwar-reconstruction systems. Represent lore with native effects and scripted content only.
- Additional ideology groups are deferred until explicit owner approval; do not edit ideology/AI/GUI systems for now.
- Build a logical **generic national focus tree**, using native `shared_focus`, contextual conditions, `available`, `bypass`, `ai_will_do`, plus regional branches where appropriate. Naval branches must not blindly appear for landlocked countries; recovery branches must reflect wartime condition.
- Lore and starting maps in the Americas are mostly **proposals** (`docs/AMERICAS_PROPOSALS.md`), not approved canon: do not make country borders or start wars based on them.
- The Caspian sea and Caucasian canal are still required by the setting, but are a separate technical map spike after the playable baseline; do not confuse map work with a new mechanics system.

## Current v0.3 implementation authorization
- The owner explicitly requested full implementation of `Ashes_of_Empires_Design_v0.3.zip` for playing/testing different countries. The archive's former discussion-only/no-code status is historical context, not an instruction to stop implementation.
- Implement its six ideological families/subtypes, general and national focus routes, native research/doctrine adaptation and reciprocal crises. This explicit authorization supersedes the earlier ban on ideology implementation and proposed-American-content implementation, but does not turn alternate future paths into fixed past history.
- Unspecified borders, capitals, country locations and governments are labelled provisional playtest fixtures in `docs/design_v0_3/WORLD_SETUP.md` and `WORLD_MANIFEST.json`. Never silently present them as CANON. Preserve source design documents intact.
- Use `tools/build_v03.py` with the game CLOSED; the former MVP generator is retired. Validate with `tools/check_mod.py`, then perform actual game checks. No gratuitous unit-test suite.
- Caspian geometry/navigation remains a separate backed-up branch and full-restart test; naval branches require `aof_caspian_navigation_verified` and a genuinely owned/controlled coast. Never set the flag just to expose an unimplemented route.

## Expected verification
- Local mod appears in Paradox Launcher with correct active game version.
- A 1924 bookmark can be selected and the game reaches the map.
- A prefixed unique test event runs with localisation.
- `error.log` has no newly introduced critical errors; report unrelated baseline errors separately.
- Do not claim any gameplay feature is tested if the actual game cannot be launched here.

## Implementation rules
- Prefer minimal overrides. Avoid broad `replace_path` unless required; verify its load behavior.
- Localisation `.yml` should use UTF-8 BOM and valid `l_english:` headers; copy actual formatting from game.
- Prefix custom IDs (`aof_`, `aof.`). Check tag, focus, idea, event, gfx ID collisions.
- Current desired era: 1924. Avoid writing vanilla 1936 geopolitical assumptions into canon.
- Kazakhstan and Siberia are first candidate playable region; Caspian/naval canal is a later isolated technical spike.
- Do not fabricate dynamic screenshots, completed tests, launch verification or file paths.

## HOI4 development automation
- For tests, use the separate Ashes of Empires playset and the previously selected second monitor. Do not launch a second HOI4 instance or overwrite saves.
- Start and inspect logs with `tools/console_automation/dev.ps1 -Action start` / `-Action logs`. The script starts the current launcher playset; verify it first. Use `-debug`, verified by `(D)` in the menu and database reload entries; the previous `-debug_mode` recommendation is superseded. Full restart/new game remains necessary for history, map, newly added files, idea database edits, and any change whose reload behavior is unverified.
- Prefer the `is_debug`-guarded `aof_debug_intro_event` decision for testing the introduction. Other development decisions must also exclude AI and be guarded by `is_debug`; do not claim a reload succeeded without checking in-game.
- For console commands: verify the console and input line are visible and the correct command is present, use Computer Use `Return` where it works; for this installation, invoke `hoi4_enter.py --wait 2 --hold-ms 150` with native Windows Python, then verify HOI4’s actual output/state. `SENT` is not proof of execution. Do not send keys if HOI4 is not foreground, or type into a closed console. If observation cannot verify output, record UNVERIFIED. Avoid running the AHK queue unless needed; it cannot verify that the console is open.
- Inspect fresh `error.log` after each run, compare with a separate no-mod run using identical DLC, and document both actual findings and limitations in `docs/TECH_NOTES.md`.

### Confirmed console sequence — use this first
1. Inspect the game screenshot: the console must be open and the exact command visible. For underscores through Computer Use use `shift+minus`; the bare `underscore` key produced a hyphen here.
2. Click inside the visible console input using the bound HOI4 Computer Use window. This activates the game. A screenshot alone does not guarantee foreground focus. ChatGPT receiving focus between tool calls caused a legitimate refusal; reactivate the game and retry, without removing the foreground check.
3. Immediately run native Python: `C:/Users/maqsatto/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe tools/console_automation/hoi4_enter.py --wait 2 --hold-ms 150`. Verify the interpreter still exists.
4. Inspect the screenshot for command processing. On 3 November 2026 `event aof_kaz.1` cleared the line, console printed Executed, and the Russian event with the generated development illustration appeared. This is confirmed execution, not just SENT.
5. `--console-key --wait 2 --hold-ms 150` opened and closed the console in this session. Always inspect before typing. `--clear-line --wait 2` sends held Backspace pulses and was visibly verified to clear the input. It does not execute commands. Ordinary Computer Use BackSpace was ignored here.

### Owner preference: minimize restarts
- The only target installation is `C:/Hearts of Iron IV`. Loading is slow even on SSD. Batch new files/history/graphics changes before a single full restart. For edits to existing events/focuses prefer the installed debug reload mechanism when its behavior has been observed; inspect both game output and logs. Do not restart just to recheck unchanged files. A full restart remains required for history/map/new files or unverified reload behavior.
- Keep practical UI/automation findings here when they affect future work (foreground activation, held Enter, correct report-image size). Do not ask the owner to press Enter or switch windows repeatedly; use the verified helper and inspect actual execution.

### Keyboard layout diagnosis
The missing letters / question marks were reproduced in a clean game. Sending `alt+shift` through Computer Use switched the game input to English; native helper `--text 'tag bhu'` then visibly produced the exact ASCII command and held Enter switched to Bhutan. Thus the helper text path works with English layout; inspect the actual line and switch layout if it shows question marks or drops letters. Do not execute a visibly garbled command. This supersedes the earlier undiagnosed save-field text limitation.

### Debug argument correction
The previous launcher-derived -debug_mode argument did not demonstrate live script reload or debug decision visibility. Use the actual game argument -debug via dev.ps1 going forward; verify is_debug decisions and a visible existing-file change before claiming hot reload. This supersedes the earlier -debug_mode recommendation. New files/history/map still need a restart.


### Hot reload limits found on 3 November
With actual -debug, existing national_focus and event edits produced explicit reload/no-errors log entries. Regenerating ideas triggered a database reload followed by 34 parser errors in installed economic/manpower laws; do not treat that live state as a clean test. Batch idea changes before a restart. Content generator must leave byte-identical files untouched to avoid unrelated reloads.


Actual -debug test confirmed: debug category and 'Тест: Война окончена' visible and its action delivered aof_intro.1 with art at first-day15:00. Prefer this tested decision for the intro test; no console/Enter is needed. Existing-file national focus/event reloads were explicitly logged as no errors.


Generator writes now compare byte output, using LF for generated files. The first run after changing the writer normalized eight CRLF outputs and triggered live reloads; subsequent identical runs were verified to preserve bytes and mtimes. Run generator with the game closed when changing its writer or output format. Do not assume a first migration is a no-op.

