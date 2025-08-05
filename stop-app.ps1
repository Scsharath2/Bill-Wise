Write-Host "`n🛑 Stopping Flask, Celery, and Redis..."

# Kill Flask (run.py)
try {
    Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" |
        Where-Object { $_.CommandLine -like "*run.py*" } |
        ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
    Write-Host "✔ Flask stopped."
} catch {
    Write-Host "ℹ Flask already stopped or not found."
}

# Kill Celery
try {
    Get-Process celery -ErrorAction SilentlyContinue | Stop-Process -Force
    Write-Host "✔ Celery stopped."
} catch {
    Write-Host "ℹ Celery already stopped or not found."
}

# Kill Redis
try {
    Get-Process redis-server -ErrorAction SilentlyContinue | Stop-Process -Force
    Write-Host "✔ Redis stopped."
} catch {
    Write-Host "ℹ Redis already stopped or not found."
}

Write-Host "`n✅ All services terminated."
