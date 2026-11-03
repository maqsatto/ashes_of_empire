param(
    [ValidateSet('start','logs')][string]$Action = 'logs',
    [string]$GamePath = 'C:\Hearts of Iron IV'
)
$log = Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'Paradox Interactive\Hearts of Iron IV\logs\error.log'
if ($Action -eq 'start') {
    $exe = Join-Path $GamePath 'hoi4.exe'
    if (!(Test-Path -LiteralPath $exe)) { throw "HOI4 not found: $exe" }
    if (Get-Process hoi4 -ErrorAction SilentlyContinue) { throw 'HOI4 is already running; do not start a second instance.' }
    Write-Host 'Launching with the current launcher playset. Confirm it contains only Ashes of Empires.'
    Start-Process -FilePath $exe -WorkingDirectory $GamePath -ArgumentList '-gdpr-compliant','-debug'
} else {
    if (!(Test-Path -LiteralPath $log)) { throw "Log not found: $log" }
    $item = Get-Item -LiteralPath $log
    Write-Host ("error.log: {0} bytes, updated {1}" -f $item.Length,$item.LastWriteTime)
    Get-Content -LiteralPath $log -Tail 150
}
