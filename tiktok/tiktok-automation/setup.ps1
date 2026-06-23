Write-Host "=== TikTok -> Facebook Auto-Poster Setup ===" -ForegroundColor Cyan
Write-Host ""

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ScriptPath = Join-Path $ScriptDir "tiktok_poster.py"
$ConfigPath = Join-Path $ScriptDir "config.json"
$TaskName = "TikTokFacebookPoster"

# Step 1: Check Python
Write-Host "[1/4] Checking Python..." -ForegroundColor Yellow
$PythonPath = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $PythonPath) {
    Write-Host "  Python not found. Install Python from https://python.org" -ForegroundColor Red
    exit 1
}
Write-Host "  Found: $PythonPath" -ForegroundColor Green

# Step 2: Install Python dependencies
Write-Host "[2/4] Installing dependencies..." -ForegroundColor Yellow
python -m pip install -r "$ScriptDir\requirements.txt"
if ($LASTEXITCODE -ne 0) {
    Write-Host "  pip install failed. Check your internet connection." -ForegroundColor Red
    exit 1
}
Write-Host "  Dependencies installed!" -ForegroundColor Green

# Step 3: Verify yt-dlp and ffmpeg
Write-Host "[3/4] Verifying tools..." -ForegroundColor Yellow

python -m yt_dlp --version
if ($LASTEXITCODE -ne 0) {
    Write-Host "  yt-dlp not found. Try running: python -m pip install yt-dlp" -ForegroundColor Red
    exit 1
}
Write-Host "  yt-dlp OK!" -ForegroundColor Green

ffmpeg -version > $null 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ffmpeg not found. Install it:" -ForegroundColor Yellow
    Write-Host "    winget install ffmpeg" -ForegroundColor Yellow
    Write-Host "    Or download from: https://ffmpeg.org" -ForegroundColor Yellow
    Write-Host "  Continuing anyway (videos may fail if ffmpeg is needed)." -ForegroundColor Yellow
}

# Step 4: Create scheduled task
Write-Host "[4/4] Creating scheduled task..." -ForegroundColor Yellow

$Action = New-ScheduledTaskAction -Execute $PythonPath -Argument "`"$ScriptPath`"" -WorkingDirectory $ScriptDir
$Trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 15)

$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -Hidden -ExecutionTimeLimit (New-TimeSpan -Hours 2)

$Principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType S4U -RunLevel Limited

try {
    Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal -Force | Out-Null
    Write-Host "  Scheduled task '$TaskName' created!" -ForegroundColor Green
} catch {
    Write-Host "  Error creating scheduled task. Try running PowerShell as Administrator." -ForegroundColor Red
    Write-Host "  Error: $_" -ForegroundColor Red
    exit 1
}

# Step 5: Warn if config still has placeholders
$config = Get-Content $ConfigPath -Raw
if ($config -match '@usuario_de_tiktok' -or $config -match 'ID_DE_TU_PAGINA' -or $config -match 'TOKEN_DE_ACCESO_DE_FACEBOOK') {
    Write-Host ""
    Write-Host "  WARNING: config.json still has placeholder values!" -ForegroundColor Yellow
    Write-Host "  Edit it with Notepad before the task runs." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== Setup complete! ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Edit config.json with your TikTok username, Facebook Page ID, and Access Token"
Write-Host "  2. The script checks every 15 minutes and posts when it's time"
Write-Host "  3. To test immediately, run: python tiktok_poster.py"
