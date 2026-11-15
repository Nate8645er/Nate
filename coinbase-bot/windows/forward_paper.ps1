# Forward paper trading on real Coinbase market data. Sends no real order.
# One pass:   powershell -ExecutionPolicy Bypass -File windows\forward_paper.ps1
# Continuous: powershell -ExecutionPolicy Bypass -File windows\forward_paper.ps1 -Loop
param([switch]$Loop, [int]$Interval = 300, [int]$Ticks = 1)
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
$py = if (Test-Path ".venv\Scripts\python.exe") { ".\.venv\Scripts\python.exe" } else { "python" }
$args = @("scripts\forward_paper.py", "--interval", $Interval)
if ($Loop) { $args += "--loop" } else { $args += @("--ticks", $Ticks) }
& $py @args
