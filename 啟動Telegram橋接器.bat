@echo off
chcp 65001 >nul
title Antigravity Telegram Bridge Daemon Launcher

echo 🚀 正在啟動 Antigravity Telegram 橋接器背景常駐...

:: 檢查是否已有正在運行的進程
for /f "tokens=2" %%i in ('tasklist /nh /fi "imagename eq python.exe" /fi "windowtitle eq AntigravityTelegramBridge*"') do (
    echo ⚠️ 橋接器已在背景運行中！
    pause
    exit /b
)

:: 啟動 Python 背景守護進程
start "AntigravityTelegramBridge" /min python "%~dp0antigravity_telegram_bridge.py"

echo.
echo =======================================================
echo 🎉 啟動成功！Bridge 正在背景默默守護與連線 Telegram！
echo 📱 請拿起手機 Telegram 隨意發送訊息測試！
echo =======================================================
timeout /t 3 >nul
