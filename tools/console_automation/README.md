# HOI4 ↔ Codex: Enter and console automation

Target: Windows, Hearts of Iron IV in-game console, Codex / Computer Use.

## First checks

1. Start HOI4 with `-debug`, in a non-Ironman game, with the console open.
2. Try restoring focus by Alt+Tab out and back once. An old HOI4 console report describes Enter returning after this.
3. If Codex Computer Use exposes `press_key`, have Codex try the key name `Return` (or the documented Enter representation) rather than injecting a newline with `type_text`.
4. A return value from an input API is **not** proof that HOI4 executed the command. Confirm by a visible game-state change or console output.

## Option A: Python / WinAPI (simple, no dependencies)

Once Codex has typed a command into HOI4's open console and kept the HOI4 window foreground:

```powershell
python .\hoi4_enter.py --wait 8 --hold-ms 90
```

Use `--numpad` to try the extended numpad Enter scan-code if ordinary Enter fails.

Requirements: native Windows Python 3.10+; a real interactive Windows desktop; HOI4 foreground; the game and Python process at compatible integrity levels. No administrator rights recommended. The script refuses to send input to another foreground application. Its success message means only that Windows accepted the generated input events.

If Codex cannot execute the helper due to sandbox restrictions, use Option B instead.

## Option B: AutoHotkey v2 queue bridge (best for repeated unattended tests)

Install AutoHotkey v2 from <https://www.autohotkey.com/>. Start `hoi4_queue.ahk` once in your interactive Windows user session (Codex can launch it as an ordinary user if its permissions allow). It remains running in the notification area. Keep HOI4 in the foreground with its developer console already open.

Codex can then **submit a console command by writing a file**:

```powershell
# Run from the folder containing this README and the AHK script.
Set-Content -Path .\hoi4_queue.txt -Value 'help' -Encoding utf8
```

The helper checks every 250 ms and sends the command + a held Enter scan-code when `hoi4.exe` is active. It appends `SENT ...` to `hoi4_queue_ack.log`, then deletes `hoi4_queue.txt`. Codex should wait for this ack before writing the next command. `SENT` only means keystrokes were issued; inspect the game window for actual results.

**Important:** run only one command at a time, and do not write the queue file while the console is closed. If the console is not open, the text could be typed into gameplay. Keep the game foreground while testing. The helper does not change window focus or bypass Windows permissions.

## Avoid the console when feasible

HOI4 `-debug` automatically reloads changes to many **existing** mod-script files, while certain new files and map changes need a restart. For most event/focus tests, create a developer-only decision or `on_startup` test hook that triggers the event without any console input. Codex can edit files and examine the game's error logs, without sending Enter at all.

## Troubleshooting

- `ERROR: HOI4 is not the active window`: Codex needs to activate HOI4 and focus the console; do not suppress this safety check.
- `SendInput returned 0`: check the agent's sandbox constraints and integrity level; run HOI4 normally, without elevation, and use the external AHK helper.
- Script reports `SENT`, but game ignores Enter: try Alt+Tab and return, borderless-windowed mode, an alternate Enter (`--numpad`), or use debug decisions instead.
- AHK typed letters but Enter did nothing: first confirm the console actually has keyboard focus, then try `SendEvent("{Enter}")` instead of the scan-code variant.
- `SENT` isn't an execution guarantee. Validate the actual console output or game-state change.

## Verified local workflow (3 November 2026)
- The extracted Python helper ran with the bundled Python 3.12 and confirmed the foreground process. With `help` visibly in the HOI4 console, Computer Use `Return` left it in the input line; `hoi4_enter.py --wait 2 --hold-ms 150` cleared the line and HOI4 visibly displayed the help list. This proves this specific test, not arbitrary commands.
- The console was opened by the user. A first attempt to open it using `--console-key` (scan code 0x29) was accepted by Windows but did not visibly open it; this option is experimental and is not a reliable autonomous console opener on this machine. Always inspect the window before typing.
- `dev.ps1 -Action start` launches the current launcher playset in the installed launcher’s `-debug_mode`; `-Action logs` reads the latest error log. The script refuses to start a second game. The `aof_debug_intro_event` decision is available only in debug for a human player, and queues the intro event after one in-game hour. Restart and verify it after adding the file; the decision itself has not yet been tested in-game.
- The existing AHK queue is not installed or verified, and only reports keystrokes, not game execution. It must not be used while the console is closed.
- After a full restart, the game log reports that it loaded one decision from `aof_debug.txt`. The decision was not seen in the inspected portion of the decisions list and has not been executed; verify the category and `is_debug` behavior before relying on it.
