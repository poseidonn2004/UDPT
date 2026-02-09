# 1. Đóng Windows Terminal cũ
Get-Process WindowsTerminal -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 1

# 2. Chạy MỘT lệnh wt duy nhất chứa tất cả các lệnh con
# Chú ý: Tất cả các lệnh split-pane và move-focus phải nối đuôi nhau bằng `;`
wt -p "Windows PowerShell" -d . powershell -NoExit -Command "python server.py 8000" `; `
split-pane -V -d . powershell -NoExit -Command "python server.py 8001" `; `
split-pane -V -d . powershell -NoExit -Command "python server.py 8002" `; `
move-focus left `; `
move-focus left `; `
split-pane -H -d . powershell -NoExit -Command "python server.py 8003" `; `
move-focus right `; `
split-pane -H -d . powershell -NoExit -Command "python server.py 8004" `; `
move-focus right `; `
split-pane -H -d . powershell -NoExit -Command "python server.py 8005"