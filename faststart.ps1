Get-Process WindowsTerminal -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 1

$startPort = 8000
$numberOfNodes = 10  # Bạn muốn mở bao nhiêu node thì sửa ở đây

# Mở Tab đầu tiên
$cmd = "wt -p `"Windows PowerShell`" -d . powershell -NoExit -Command `"python server.py $startPort`""

# Vòng lặp bắt đầu từ 1 vì tab 0 đã mở ở trên
for ($i = 1; $i -lt $numberOfNodes; $i++) {
    $currentPort = $startPort + $i
    $cmd += " `; wt -p `"Windows PowerShell`" -d . powershell -NoExit -Command `"python server.py $currentPort`""
}

Invoke-Expression $cmd