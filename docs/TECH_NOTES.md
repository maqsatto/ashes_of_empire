# Технические заметки

## v0.3 Pacific event artwork
- Added original, AI-generated source illustrations at `art/source/aof_event_american_science.png` and `art/source/aof_event_japanese_orders.png` (1369×1149 PNG each). Their game exports are `gfx/event_pictures/aof_event_american_science.dds` and `gfx/event_pictures/aof_event_japanese_orders.dds` (210×176 RGBA DDS, exported to match the existing uncompressed event-picture DDS format). Registered in `interface/aof_v03_art.gfx` and selected for opening events `aof_v03_pacific.3` (USA) and `.4` (JAP) by `tools/build_v03_pacific.py`.
- The paintings depict generic 1920s researchers arriving at a US harbor and Japanese civilian ministers confronting officers over an unlabeled Far Eastern rail map. No known historical individuals or third-party assets were used. DDS dimensions/format and source PNG dimensions were inspected locally; no HOI4 launch or visual in-game check was performed for this art.

## Окружение и устройство
- Windows; корень проекта — фактическая локальная папка мода `Documents/Paradox Interactive/Hearts of Iron IV/mod/ashes_of_empires`. В начале содержался `descriptor.mod`, Git-репозиторий отсутствовал; Git установлен. Данные стартового архива извлечены без перезаписи существующего файла. Внешний `../ashes_of_empires.mod` уже существовал, его path сохранён, добавлен узкий `replace_path`.
- Игра: `C:/Hearts of Iron IV`, `launcher-settings.json`: Operation Postern **1.19.3.0.c01a (5632)**, rawVersion 1.19.3.0; журнал старого запуска указывает тот же билд, но другой checksum f379. Совместимость указана 1.19.3.0, не 1.19.4. Paradox Launcher 2026.13 доступен. Python в PATH — WindowsApps alias, не проверен как рабочий интерпретатор; git доступен.
- Исследованы bookmarks, defines, country tags, country/state histories, events, on_actions, локализация и default.map установленной игры. KAZ уже существует (`common/country_tags/00_countries.txt:102`). Карту и ID не изменяли.
- Ванильная история USA содержит безусловные данные и OOB 1936; состояние 1 имеет безусловного владельца FRA. Ранний старт поэтому не является реализацией геополитики 1924, а остальные даты и условия нуждаются в проверке. Эта временная конфигурация заведомо не каноническая.
- `replace_path="common/bookmarks"` скрывает стандартные сценарии и может конфликтовать с другими модами. Нужна проверка фактического поведения; другие каталоги не заменяются. Новые файлы локализации имеют UTF-8 BOM. Конец 1954, дата 1 сентября 1924 и выбор США — временные решения для запуска, не канон. `TENSION_TIME_SCALE_START_DATE` тоже временно изменён; баланс напряжённости предстоит пересмотреть.
- Событие вручную вызываемое, не подключено к on_actions. Эффект и изображение взяты по синтаксису и существующим ресурсам установленной игры. Игра может подгружать ванильные события и контент, несовместимые с эпохой.

## Проверки
- Лаунчер показал Ashes of Empires; создан отдельный игровой набор с одним модом. В `dlc_load.json` записан `mod/ashes_of_empires.mod`.
- Сохранён предыдущий error.log в `%TEMP%/aof-baseline-error-20261103.log`; он относится к другому набору, не чистая база. Для заключения о новых ошибках нужен отдельный запуск без модов с теми же DLC.
- Результаты непосредственного запуска см. в конце этого документа после завершения проверки. Состояния без отметки успешного выполнения не считаются проверенными.

## Открытые вопросы
Точная дата и условия мира, границы, столицы, режимы, устройство Каспия и будущие идеологии остаются TBD в LoreBook. Phase 2 не начинать до подтверждения старта, события и анализа журнала.

### Фактический запуск 3 ноября 2026
- Запуск `C:/Hearts of Iron IV/hoi4.exe -gdpr-compliant -debug_mode` после выбора отдельного набора: игра дошла до главного меню, версия в меню 1.19.3.0.c01a, checksum 8423. Лаунчер перед этим записал единственный мод в `dlc_load.json`.
- В меню показано сообщение о неудачном обновлении профиля и уведомление `Couldn't verify ownership of item(s)`; происхождение и влияние на DLC не установлены.
- В game.log зафиксирована загрузка истории до 1924.9.1.12. До меню свежий error.log имел 0 байт; это не тест карты или доказательство отсутствия ошибок в дальнейшем. Чистого запуска без модов с теми же DLC не было.
- Повторный запуск после выбора монитора в лаунчере: сценарий отображён с датой 1 сентября 1924, США вошли на карту, время продвинуто до 29 сентября. Ванильное событие США сработало. Консоль открыта пользователем, команда набрана, но автоматический Enter не сработал. Проверка события не завершена. Временный on_startup для дополнительного теста удалён после остановки компьютерного управления пользователем.
- Статически проверены парность скобок в двух скриптах и UTF-8 BOM обеих локализаций; значения ключей сверены с созданными файлами. Это не полноценный парсер движка. SHA-256 LoreBook совпал с содержимым исходного архива.

- При повторном тесте два экземпляра ненадолго одновременно писали общие журналы; оценка свежего error.log не заменяет чистое сравнение с ванилью. Игра после остановки управления могла остаться открытой.

### Console automation and event test
- The in-memory temporary startup hook from the preceding run triggered `aof_intro.1`: the Russian title, text, and option were visible; choosing it changed political power from 19 to 20 while paused. The hook had already been removed from disk. This verifies event display and the +1 effect in that run, not console invocation.
- With the console opened by the user, `Return` left `help` in the input line. Native Python `hoi4_enter.py --wait 2 --hold-ms 150` reported `SENT`; the input cleared and HOI4 displayed a list including `Audio.DebugMax` and `GUI.Wireframe`, visibly confirming help executed. A physical console-key scan code did not visibly open the console earlier. AHK was not needed or installed.
- `common/decisions/aof_debug.txt` was added after the active game loaded; it requires a full restart and a separate in-game test. The local debug script reads `error.log`, which was empty at inspection; the earlier overlapping processes and lack of an equivalent vanilla baseline prevent attributing absence or origin of all errors conclusively.
- Перезапуск через `dev.ps1 -Action start` выполнен; `setup.log` сообщил `common/decisions/aof_debug.txt` и 1 загруженное решение. Новая игра дошла до карты; в видимой части списка решений тест не обнаружен, выполнение самого решения не подтверждено. Причина неизвестна: требуется проверить категорию и `is_debug` для этой сборки. `error.log` после этого запуска — 0 байт; отдельной ванильной базы всё ещё нет.

### Starter v0.2 and generic focus pilot — 3 November 2026
- Imported the creator's v0.2 LoreBook unchanged (SHA-256 matches the archive), Americas proposals and startup prompt. Existing automation guidance was retained. The archive's proposed American borders and wars were not implemented.
- Added `aof_generic_pilot`, restricted to the existing BHU and CUB tags as a test, with six ordinary focuses and English/Russian localization. These are temporary test countries, not decisions about the setting. Selection of this tree by Cuba was observed; selection by Bhutan and preservation of other countries' trees remain unverified in game.
- On HOI4 1.19.3.0.c01a, a new 1924 game as Cuba reached the map. All six focus names appeared in Russian, including the coastal focus. The administration focus was selected and completed over 35 in-game days; the completion notification appeared. Political power rose from 49 on 24 September to 107 on 5 October, consistent with the +35 reward plus normal daily gain, though the reward was not isolated at the exact tick.
- The focus tree's landlocked branch hiding, independence condition, remaining rewards, English UI and AI behavior have not been tested in game. `allow_branch` conditions may be evaluated at tree load; the coastal focus also has an `available` check to prevent use if coast control is lost. Do not broaden the pilot until these cases are verified.
- Fresh `error.log` was 0 bytes after this run. There is still no comparable clean no-mod baseline with identical DLC; this is not proof that every behavior is correct.
- The scan-code console key visibly closed an already open console in this run; autonomous opening remains inconsistent and is not claimed reliable.

### Follow-up: Bhutan and autonomous console, 3 November 2026
- From the paused Cuba test game, the Python scan-code helper opened the console. Computer Use entered `tag bhu`, the held Enter helper executed it, and the Bhutan flag and country UI visibly replaced Cuba. The helper then closed the console. No user keystroke was needed in this test.
- Bhutan's focus UI displayed five focuses; the coastal branch was absent, as intended. Administration was completed and industrial study was active at 7/35 days. This occurred under AI control before switching country, confirming basic AI selection, prerequisite progression and completion in this particular run. This supersedes the earlier unverified Bhutan/AI status, but is not a full balance or reward test.
- Current tested helper interpreter: `C:/Users/maqsatto/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe`. Verify this path exists in future sessions rather than using the WindowsApps alias.

### Kazakhstan implementation pending restart
Added a one-state KAZ prototype using installed state 586 and province 1591, a small infantry OOB, minimal country history, one military factory, bookmark selection and the existing generic focus pilot. Details and provisional assumptions are in MAP_PLAN.md. These changes have not yet been loaded in game; prior successful runs do not verify them.
- Full restart with the new history reached a new KAZ game on 1924.9.1.12: Alma-Ata capital, one infantry division and four total factories visibly present. Fresh error.log remained empty. This verifies boot only; production, research, save/load and the year-long campaign still need gameplay verification. The vanilla neutral name is Khanate; a narrow localization override to Kazakhstan was added afterwards and its reload remains unverified. Vanilla neutral flag and blank leader portrait are still prototype presentation. No historical ruler has been invented.

### Expanded MVP content in progress
The pilot now contains 18 focuses (three KAZ-only), four KAZ events and two national spirits using native effects. The industrial chain adds civilian production, infrastructure, technical education and standards; the army chain offers equipment research, training and a military factory. The KAZ chain represents resource surveys and lets the player choose civilian or arms production, ending in a development milestone. These are gameplay implementations of the approved broad themes, not new historical rulers, wars or treaty terms. Event text has EN/RU BOM localization. Repeat content generation was corrected to preserve braces. A fresh game test is required before declaring the expanded tree working.

### Event illustration assets — 3 November 2026
- Added two original, anonymous 1920s event illustrations: a weary postwar peace scene and a Kazakhstan geologists' workshop. Generated PNG sources are retained in `art/source/`; no leaders, flags, faction marks, or readable headlines were included. These images are presentation assets and do not add or assert lore.
- Exported DDS textures at 210x176, 32-bit BGRA, matching installed country-event report art (`report_event_generic_read_write.dds`, 147,968 bytes). The standard `EventWindow` icon is placed at x=5 while its option grid begins at x=215, so the report-art dimensions keep the option clear. Registered as `GFX_aof_event_world_peace_1924` and `GFX_aof_event_kazakhstan_development` in `interface/aof_eventpictures.gfx`.
- Verified source crops visually and checked DDS dimensions/header and byte size against the installed report-event sample. The earlier 397x153 export used news-event dimensions and overlapped the standard country-event option grid; it was replaced with the 210x176 report-event export. Game loading/display was not verified in this asset pass.

### Confirmed event and Enter, 3 November 2026
After activating HOI4 by clicking the visible console input, the existing held scan-code Enter method executed `event aof_kaz.1`. Console output showed Executed; the Russian event title, description, option and newly generated development illustration appeared. A prior attempt was correctly refused because ChatGPT was foreground. The foreground guard remains enabled. Exact workflow is now in AGENTS.md. Automatic MTTH delivery of the introduction did not appear during the observed September–October run and still requires fixing; manual execution does not verify automatic delivery.

### Expanded tree gameplay run, 3 November 2026
- Current game PID 3708, window 1639544; game reached 27 June 1925. Administration, industrial study and transport links were selected by the player and completed under ordinary game time; notifications and gold completed nodes were visible. No focus autocomplete was used. Campaign remains paused with no current focus after transport.
- On-startup introduction still did not appear in this run when guarded by is_ai=no. The startup guard was removed on disk (only KAZ is targeted); this revision has not been restarted/tested. Do not claim automatic introduction works yet. The earlier manual event display and generated image loading are verified separately. Image sizes were corrected to 210x176 report format on disk and loaded by the current process; new event display still needs checking.
- Added `--pause-key` to the native helper (held Space, console must be closed). It toggled pause, visibly stopped date at 6 February and later 1 May / 27 June. A freshly observed screenshot must determine current pause state before using a toggle.
- Correction to the earlier empty-log observations: during the later run error.log grew to about 11 MB, beginning at 1925.03.31 with Invalid Scope (Country expected, State provided) in installed `common/scripted_localisation/00_scripted_localisation_countries_RU_loc.txt`. No aof path/ID appeared in the inspected search results, but this alone cannot attribute the problem to baseline. Saved the current log outside the project at `%TEMP%/aof-mvp-1925-ru-error.log`. Need reproduce the same state-building/tooltips in a no-mod run with the same DLC before making any baseline claim. Installation files remain untouched.

### Story chain verified in normal gameplay
- The game reached 1 December 1925, more than a year after the 1924 start, without a crash. No focus autocomplete was used. The resource-survey focus and development programme were completed in ordinary time. On 26 October 1925, the programme event appeared from the focus with two Russian options and the corrected 210x176 generated illustration. Selecting civilian production changed the visible total factory count from 4 to 5 while paused.
- The final focus completed by 1 December 1925: stability rose from 65% to 70%, the ending event appeared in Russian with the illustration, and the political-power reward was reflected in the total (daily income was also present, so not isolated at a single tick). The final event option has not yet been chosen at this observation.
- Earlier automatic-event absence may have been missed observation at maximum game speed: events can expire while many days advance between observations. The previous claim of a broken startup trigger is therefore unproven. Use short bounded run/pause intervals (8 seconds advanced about 12 days in this run) and verify the introduction near the first hours on a new game before further changes.

### Practical automation note
Ordinary Computer Use text entry/letters were ignored in the save-name field in this session, although digits and underscores entered. A separate test save was created as `__19251201.hoi4` and renamed locally (only this newly created file) to `aof_mvp_19251201.hoi4`; it appeared under the new name in HOI4's load list and was selected for reload. Existing user saves were not renamed or deleted. The native helper now has optional ASCII `--text` (types only, no Enter), but letters were also ignored in this particular save field; do not treat it as universally reliable. The save reload is in progress, not yet verified.
- Save/load completed: `aof_mvp_19251201.hoi4` (39,653,521 bytes) was created at 1 December 1925 10:00, loaded through the game UI, and returned to the map with 5 factories, 70% stability and 1348 political power. A short resumed run reached 4 December 1925 11:00, confirming continued game time. Choosing the ending event while paused changed PP from 1323 to 1348, isolating its +25 reward.

### Separate no-mod baseline
Launched the same installed game with `enabled_mods=[]`, `disabled_dlcs=[]`, same Russian language and debug arguments; main-menu checksum 5632. Started 1936, switched to Bhutan with the console and inspected vanilla construction/infrastructure focus reward windows. Ran to 25 February 1936; error.log remained 0 bytes and was copied to `%TEMP%/aof-vanilla-1936-baseline-error.log`. This reproducer did NOT reproduce the scope spam, so its origin cannot be dismissed as baseline. For mod building rewards, added vanilla-style country-level complete_tooltip and explicit option tooltip plus hidden actual effect, avoiding state-scoped automatic country-name localization without changing the actual building reward. This fix still needs verification in the final mod run. The baseline duration/date differs from the long 1924 run; comparison is limited.

### Final startup verification
Fresh mod process PID 19940, checksum ea99, new KAZ campaign: ran bounded intervals from 1924.9.1.12 to 20:00. aof_kaz.1 appeared automatically without console, with Russian localization and development illustration. The unconditional KAZ on_startup queue is verified. Earlier absence observations were inconclusive due long unattended time jumps. Game was paused at observation.


### Production and research check
PID 19940: two research slots visible; selected support weapons I (1918), 137 days, without MIO. Created basic infantry equipment production line, assigned the one military factory. By 1924.9.4.19 the line showed 4 units produced and 1.43/day. Fresh error.log still 0 bytes at this point. Introduction option changed paused PP from 3 to 28 (+25).


Final process: opened civilian and military factory focus reward windows and hover tooltips; both displayed capital Alma-Ata and +1 slot/building, with error.log 0 bytes. Army training completed under ordinary time by 21 October 1924, granting 10 army XP (visible). No autocomplete used.


By 25 November 1924, infantry equipment focus completed under ordinary time. error.log now 310 bytes: two installed events/BFTB_Turkey.txt:253 has_war_support value20 invalid comparisons. Source is installed vanilla; not modified here and not observed in the shorter clean baseline, so baseline reproduction remains unconfirmed.


By 31 December 1924, defence workshops completed naturally and total factories increased from 4 to 5. Thus the military factory reward is verified in game. Vanilla world news still fire (e.g. London naval treaty mentioning 1935 during 1924); global historical content has not been converted and must not be presented as lore-complete.


By 5 February 1925 officer courses completed normally; army XP changed 10 to25, confirming +15. Army branch all four focuses now completed in ordinary game time in this process.


### Scope issue reproduced after tooltip revision
Latest run still produced 3122 scripted-localisation errors per evaluation at 1925.01.19.08, 1925.01.22.02 and 1925.02.01.01 (GetNameRuPrep in State scope); 1,814,604 bytes by 5 February. Therefore the earlier tooltip change did NOT resolve the issue and must not be claimed as a fix. Saved reproduction to TEMP/aof-final-mod-scope-reproduction-error.log. Root caller remains unidentified; actual baseline ran only through February1936. Support weapons I completed under ordinary time, with its completion notification visible.


Hypothesis for next bounded test: automatic localization of state-scoped building rewards may be evaluated during AI focus handling. Changed only the three building/infrastructure focus rewards to explicit country-level custom tooltips plus hidden actual capital effects, matching the event reward presentation. Removed the ineffective complete_tooltip experiment. Gameplay rewards unchanged. This is a hypothesis, not a confirmed fix; reload and fresh-log verification pending. Manual programme military option in PID19940 changed factories5 to6 while paused, without growing the existing error log.


The edited existing focus file did not update its visible reward text in process19940. Thus automatic reload was not verified with -debug_mode. Changed dev.ps1 to -debug for the next combined restart; debug decision visibility/reload still pending. Binary string inspection found debug but no debug_mode; this supports, but alone does not prove, the argument diagnosis.


### Actual debug mode diagnosis
Process20108 uses -debug (verified process command line). Main menu now shows (D)(S), checksum5c15; error.log explicitly records national_focus/bookmarks database reloading with no errors. The previous -debug_mode runs lacked this proof. Debug text.log exposed a real aof_production_standards focus/idea localization collision; renamed only the idea and its localization keys to aof_production_standards_spirit. The deliberate KAZ_neutrality name overrides remain documented duplicates of vanilla names.


Actual-debug live regeneration reloaded ideas and produced34 Unexpected token errors in installed economic/trade/manpower law files. This run is invalid for clean gameplay comparison after that reload; no game files were edited. Corrected generator to write only byte-changed files, preventing unchanged ideas/events/on_actions from triggering unrelated reloads. Another clean restart is required after the idea rename; this is recorded as an avoidable workflow error, not a successful test.


Static check after tooltip/idea-key changes:12 Clausewitz/Lua/GFX files balanced after excluding quoted strings and comments; 68 unique mod-localization keys per language, UTF8 BOM and matching language headers;18 focus IDs plus1 tree ID unique. This is not an engine parser or proof of gameplay rewards. No unit-test suite added.


### Developer decision verified
Clean actual-debug process4724, window7800582, checksumbe95, new KAZ game. Debug category and aof_debug_intro_event visible. Clicking its action and running to1September15:00 delivered aof_intro.1 without console; Russian title/text/option and original peace illustration displayed correctly at210x176. Fresh log before time advance contained only the intentional KAZ-name localization collision notice, no law-parser errors. This supersedes earlier unverified decision visibility.


Developer intro option chosen while paused: PP3 to4, confirming +1 with current peace picture. Current clean debug run now exercising AI/time after hidden capital-effect tooltip revision; long-run result pending.


### Final bounded clean run
Process4724 (-debug), window7800582, checksumbe95, fresh KAZ campaign reached1925.04.16.08 and is paused. Passed previous problematic dates Jan19/Jan22/Feb1 and Mar31 without scripted_localisation scope spam after explicit custom tooltip + hidden capital-effect changes. error.log1598 bytes: deliberate KAZ name overrides notice, two installed BFTB_Turkey has_war_support comparisons and11 invalid order_assign_command AI messages. No aof script errors or law reload parser errors. Copied to TEMP/aof-final-debug-through-19250416-error.log. This verifies absence of the symptom in this run, not a proven root cause or every future situation. Existing save/load test predates spirit-key rename; use a new campaign for latest build. Remaining unplayed branches and full-world conversion are listed in MVP_STATUS.md.


Final generator idempotence check: first execution of new byte-writing implementation normalized eight generated files from Windows newline output to LF, triggering another idea hot reload and its known34 installed-law errors after the already-recorded April16 gameplay test. Pristine1598-byte run log had been copied BEFORE this check; post-reload log saved separately to TEMP/aof-final-after-newline-reload-error.log. A second execution changed neither bytes nor timestamps across18 common/event/localization files. LoreBook compared byte-exact to the creator v0.2 archive again. Closing this invalidated live process; do not represent the post-reload session as clean. Game-script logic was not changed by the newline normalization.


### v0.3 first engine boot and cold repair batch — 3 November 2026
Process9788, -debug, checksum0dad(D)(S), sole AoE mod: new KAZ campaign reached paused1924.9.1.12. Three starting spirits assigned; their pictures were question marks. India-Pakistan war notification appeared. New KAZ tree opened but camera showed a wide/mostly blank section rather than its root; no focus completion tested. Six-party pie/list appeared, while vanilla Democracy/Soviet Union localisation still overrode desired names. error.log had14920 entries, mostly native MIO/scripted-trigger references to removed1936 focus IDs. This was a real integration failure, not an unrelated baseline. Log preserved at docs/verification/v03-first-boot/error.log.

Closed game via its menu before regeneration. Cold repairs authored/generated: explicit verified native sprites for national spirits, priority localisation/replace files,32bpp placeholder flags, inert unavailable native identifier registry. Static checks after initial map/debug batch:215scripts,412focuses,83events,1848keys/language PASS. This is not an engine result. Map experiment backed up outside repository and applied only after git baseline e397dd0 on spike/caspian-navigation; four existing water IDs, forty coastal flags, native-style shortcut/rule, region70 naval terrain, two port histories/spawns and water unitstacks. Navigation flag remains unset. Full restart, fleet motion, trade/supply and denial tests remain pending.

### Second map boot — PID10352, checksum144b(D)(S)
After adding all40 nudger shoreline spawns, pixel-centred coordinates and no blank final buildings row, a new1924 KAZ campaign reached the map without the prior immediate crash. Missing-port and empty-row errors no longer appeared in this run. Native identifier mission/tree fixes removed the previous parser groups. Remaining initial65 entries included foreign aircraft/tank variant references, missing custom procedural name pools and vanilla SOV AI advisor checks; source repairs are pending the next closed batch.

Observed in actual UI: KAZ three spirits now have valid native icons; Liberalism and Soviet Russia names apply; short government labels fit; institutional silhouette portraits display. Focus tree root now appears centrally after nonnegative X translation. Started 'Созвать общий съезд' (35days,shown+40PP); completion NOT observed. Clicked debug-only fleet decision and observed one real KAZ DEBUG Escort in the Mangystau/Ust-Yurt naval base1517, with correct early-escort equipment and a fleet/task force. A right-click order was visibly accepted toward Caspian Sea; actual arrival, all-four-water coverage, canal transit, trade, supply and denial remain UNVERIFIED. The navigation-verification flag remains unset.

Computer Use was stopped by the owner's physical Escape key. No further desktop control was performed after that stop. Subsequent creator border/oblast/city requests are prepared in generator sources; do not describe them as applied to the still-running game. The current owner may be playing the test session; do not terminate or overwrite it to force a rebuild.

### Resumed full map campaign — PID19736, checksum ac1c(D)(S)

The owner explicitly resumed control and authorized closing without saving. The composed oblast/city/border/river package was applied with the game closed. First oblast boot (PID13708, c27d) reported seven states spanning strategic areas; those areas were repaired without moving water provinces. That failed attempt is preserved in `verification/v03-oblast-first-boot/error.log`.

The following fresh KAZ campaign, PID19736/ac1c, reached paused1924.9.1.12 with20KAZ states (17oblasts plus three separately authorized extras),7factories and95.99K available manpower. Actual UI showed Алматы, Акмола, Караганды, Экибастуз and the new oblast labels. This confirms map loading and displayed labels, not historical exactness or every border. Debug decisions created one early escort docked in Mangystau and20convoys. No actual ship arrival/canal passage/trade/supply result was observed. `aof_caspian_navigation_verified` remains unset.

Console `help` was actually executed: English text was inspected first, native held Enter sent with foreground guard, command list appeared and input cleared. `goto_province 1517` then printed `Centering to province.` and moved the camera. An earlier Russian-layout attempt was cleared and is not counted as success. The latest build therefore needs no manual Enter from the owner.

Fresh error.log has34entries, preserved in `verification/v03-full-first-boot/error.log`: invalid autonomy effect, nine model-state membership warnings, missing visual air/rocket/gun sites after oblast splits, and one exact-name foreign Soviet tank request. These are mod integration defects, not excused as baseline. Source repairs are being combined before the next cold boot; no claim of their engine success yet. Model sampling is now based on the nine observed engine provinces: image_y=H-1-floor(Z). The Soviet compatibility alias retains early modules despite its native requested name. CMT pending diplomatic requests now expire/close safely, and negotiated autonomy explicitly preserves unrelated wars.

On the owner's renewed explicit restart authorization, PID19736 was closed through the in-game Quit confirmation without saving. Normal saves were not overwritten. Next test must use a new campaign after the combined rebuild.


### Combined closed-game repair build

Applied all prepared source repairs after PID19736 exited. Static validator PASS:232scripts,417focuses,105events,2110keys/language;1086unique states,10272land provinces exactly once, allVP/capital/OOB ownership checks and304strategic-area membership. Model sampling matches nine observed engine provinces. All17oblasts have all seven required native state-level visual sites plus normal/facility/supply placement classes. Added48visual rows without adding actual building levels;40Caspian shoreline spawns preserved. Fresh external backup canal-visual-20261103-r2 captures this final model/strategic input. This is a build/static result; cold-engine confirmation pending.

### Handoff update: cold boot4996 and actual naval movement

PID2136/checksum4996(D)(S) loaded a new KAZ1924.9.1campaign with initial error.log0bytes. Previous34errors did not recur. Repeated full build changed0of2277runtimefiles before the later railway reward edit. KAZentry1 completed in normal35daytime, reward+40PP and completion notification observed. Refused reciprocal industrial partnership onOct8: PP140→155. Debug intro aof_intro.1 delivered Russian text/art and+1PP(164→165). One escort and20convoys created; real northernCaspian arrivalOct11, BlackSea holding positionOct29, returnCaspian holding positionNov12. All-four-water/mission/trade/supply/denial criteria not completed; navigationflag remainsunset.

Ship fuel tooltip showed8/dayrequired,0received; neither1591capital nor1517homebase connects to native railways. Added two verified guarded level1spurs to existing KAZentry2 reward, preserving capital infrastructure. Selective refresh changed only existing KAZfocus and nationalRU/ENlocalisation; parser reload noerrors. BUT national_focus hotreload resetcompletedfocusstatus, so subsequent session is an accelerated isolatedrewardtest, not normal progression. Enabled Focus.AutoComplete, repeatedroot atpause(PP258→298); entry2 availablebutnotstarted. Railwayconstruction, fuelreplenishment and shorterdescriptionUI still UNVERIFIED. Stopped on ownerrequest. Full exact paths, remainingtasks and new-PC installation/build caveats: CODEX_HANDOFF.md. This entry supersedes older pending-restart/latest-run summaries without rewriting their historical results.
