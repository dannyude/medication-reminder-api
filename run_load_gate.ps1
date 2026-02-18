param(
    [string]$HostUrl = "http://localhost:8000",
    [int]$Users = 50,
    [int]$SpawnRate = 5,
    [string]$RunTime = "5m",
    [switch]$EnableSpike,
    [ValidateSet("heavy", "light")]
    [string]$AuthProfile = "heavy",
    [string]$LoadTestEmail = "",
    [string]$LoadTestPassword = ""
)

$ErrorActionPreference = "Stop"

if (-not (Get-Command locust -ErrorAction SilentlyContinue)) {
    Write-Host "locust command not found. Install with: pip install locust" -ForegroundColor Red
    exit 1
}

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$prefix = "loadgate_$timestamp"

if ($EnableSpike) {
    $env:SPIKE_TRAFFIC = "1"
} else {
    $env:SPIKE_TRAFFIC = "0"
}

$env:AUTH_PROFILE = $AuthProfile
if ($AuthProfile -eq "light") {
    if ([string]::IsNullOrWhiteSpace($LoadTestEmail) -or [string]::IsNullOrWhiteSpace($LoadTestPassword)) {
        Write-Host "AUTH_PROFILE=light requires -LoadTestEmail and -LoadTestPassword" -ForegroundColor Red
        exit 1
    }
    $env:LOAD_TEST_EMAIL = $LoadTestEmail
    $env:LOAD_TEST_PASSWORD = $LoadTestPassword
}

Write-Host "Running load gate..." -ForegroundColor Cyan
Write-Host "Host=$HostUrl Users=$Users SpawnRate=$SpawnRate RunTime=$RunTime Spike=$($env:SPIKE_TRAFFIC) AuthProfile=$($env:AUTH_PROFILE)" -ForegroundColor Gray

locust -f load_test.py --host=$HostUrl --users=$Users --spawn-rate=$SpawnRate --run-time=$RunTime --headless --only-summary --csv=$prefix

$statsFile = "$prefix`_stats.csv"
if (-not (Test-Path $statsFile)) {
    Write-Host "Could not find Locust stats file: $statsFile" -ForegroundColor Red
    exit 1
}

$rows = Import-Csv $statsFile
$agg = $rows | Where-Object { $_.Name -eq "Aggregated" } | Select-Object -First 1

if (-not $agg) {
    Write-Host "Aggregated row not found in $statsFile" -ForegroundColor Red
    exit 1
}

$totalReq = [double]$agg.'Request Count'
$failReq = [double]$agg.'Failure Count'
$p95 = [double]$agg.'95%'
$p99 = [double]$agg.'99%'

$failRate = 0.0
if ($totalReq -gt 0) {
    $failRate = ($failReq / $totalReq) * 100
}

$maxP95 = 400.0
$maxP99 = 1000.0
$maxFailRate = 1.0

$okP95 = $p95 -le $maxP95
$okP99 = $p99 -le $maxP99
$okFail = $failRate -le $maxFailRate
$go = $okP95 -and $okP99 -and $okFail

Write-Host ""
Write-Host "=== Load Gate Summary ===" -ForegroundColor Cyan
Write-Host ("Requests: {0}" -f [int]$totalReq)
Write-Host ("Failures: {0} ({1:N2}%)" -f [int]$failReq, $failRate)
Write-Host ("p95: {0} ms (target <= {1} ms)" -f [int]$p95, [int]$maxP95)
Write-Host ("p99: {0} ms (target <= {1} ms)" -f [int]$p99, [int]$maxP99)
Write-Host ""

if ($go) {
    Write-Host "GO: Meets performance gate." -ForegroundColor Green
    exit 0
}

Write-Host "NO-GO: Does not meet performance gate." -ForegroundColor Red
if (-not $okP95) { Write-Host "- p95 too high" -ForegroundColor Yellow }
if (-not $okP99) { Write-Host "- p99 too high" -ForegroundColor Yellow }
if (-not $okFail) { Write-Host "- failure rate too high" -ForegroundColor Yellow }
exit 2
