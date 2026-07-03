# Script para iniciar ngrok y obtener la URL pública
# Ejecutar desde PowerShell con: & ".\start-ngrok.ps1"

$ngrokProcess = Start-Process -FilePath "ngrok" -ArgumentList "http", "5000", "--log=stdout" -RedirectStandardOutput "ngrok-output.txt" -WindowStyle Hidden -PassThru

Write-Host "Iniciando ngrok..." -ForegroundColor Green
Start-Sleep -Seconds 5

# Intentar leer la URL del log
try {
    $logContent = Get-Content "ngrok-output.txt" -ErrorAction SilentlyContinue
    Write-Host "Log de ngrok:" -ForegroundColor Cyan
    $logContent | ForEach-Object { Write-Host $_ }
} catch {
    Write-Host "Esperando que ngrok genere la URL..." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "ngrok está corriendo en segundo plano." -ForegroundColor Green
Write-Host "Para ver la URL pública, visita: http://localhost:4040/api/tunnels" -ForegroundColor Cyan
Write-Host "O revisa el archivo ngrok-output.txt" -ForegroundColor Cyan
