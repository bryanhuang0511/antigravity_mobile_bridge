@echo off
chcp 65001 >nul
echo 正在停止 Discord 橋接器...
powershell -Command "Get-Process python* -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowTitle -eq '' -or $_.Path -like '*Python312*' } | Stop-Process -Force -ErrorAction SilentlyContinue"
echo ?? Discord 橋接器已停止！
pause