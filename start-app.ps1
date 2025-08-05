# === Set paths ===
$root = (Resolve-Path "$PSScriptRoot").Path
$venvPath = "$root\venv"
$pythonPath = "$venvPath\Scripts\python.exe"
$redisExe = "C:\Program Files\Redis\redis-server.exe"
$redisConf = "C:\Program Files\Redis\redis.windows.conf"
$backendPath = "$root\backend"

# === Start Redis if not already running ===
# === Start Redis if not already running ===
$redisRunning = Get-Process redis-server -ErrorAction SilentlyContinue
if (-not $redisRunning) {
    Write-Host "Starting Redis..."
    Start-Process -NoNewWindow -FilePath "$redisExe" -ArgumentList "`"$redisConf`""
    Start-Sleep -Seconds 5
} else {
    Write-Host "Redis is already running."
}

# === Set environment PATH to use venv ===
$env:Path = "$venvPath\Scripts;" + $env:Path

# === Start Flask ===
Write-Host "Starting Flask..."
Start-Process powershell -ArgumentList "cd `"$backendPath`"; & '$pythonPath' run.py"

# === Start Celery ===
Write-Host "Starting Celery..."
Start-Process powershell -ArgumentList "cd `"$backendPath`"; & '$pythonPath' -m celery -A celery_worker.celery_app worker --loglevel=info"

# === Open browser ===
Start-Sleep -Seconds 2
Start-Process "http://127.0.0.1:5000/parse-json"

Write-Host "`nAll services launched successfully."
