#Requires AutoHotkey v2.0
#SingleInstance Force

; A background helper for HOI4 debug-console testing.
; Codex writes ONE command to hoi4_queue.txt while the HOI4 console is open.
; This helper waits for HOI4 to be the active window, types the command, and
; sends a held Enter scan-code. It does not change focus or elevate privileges.
; This is NOT an OS command runner; commands are typed into HOI4 only.

queueFile := A_ScriptDir "\hoi4_queue.txt"
ackFile := A_ScriptDir "\hoi4_queue_ack.log"
SetKeyDelay(45, 35)
SetTimer(ProcessQueue, 250)

ProcessQueue() {
    global queueFile, ackFile
    if !FileExist(queueFile)
        return
    if !WinActive("ahk_exe hoi4.exe")
        return

    try cmd := Trim(FileRead(queueFile, "UTF-8"), " `t`r`n")
    catch
        return

    ; A single-line ASCII console command is the only supported payload.
    if (cmd = "" || InStr(cmd, "`n") || InStr(cmd, "`r")) {
        FileAppend("REJECTED malformed command`n", ackFile, "UTF-8")
        try FileDelete(queueFile)
        return
    }

    ; The console must already be open. This does not verify that it is open.
    SendText(cmd)
    Sleep(100)
    SendEvent("{sc01C down}")
    Sleep(100)
    SendEvent("{sc01C up}")

    FileAppend("SENT " FormatTime(, "yyyy-MM-dd HH:mm:ss") " " cmd "`n", ackFile, "UTF-8")
    try FileDelete(queueFile)
}
