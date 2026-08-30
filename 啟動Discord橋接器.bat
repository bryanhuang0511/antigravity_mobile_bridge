@echo off
chcp 65001 >nul
title Antigravity Discord Bridge Daemon Launcher

echo 🚀 正在啟動 Antigravity Discord 橋接器背景常駐...

:: 檢查是否已有正在運行的進程
for /f "tokens=2" %%i in ('tasklist /nh /fi "imagename eq python.exe" /fi "windowtitle eq AntigravityDiscordBridge*"') do (
    echo ⚠️ Discord 橋接器已在背景運行中！
    pause
    exit /b
)

:: 啟動 Python 背景守護進程
start "AntigravityDiscordBridge" /min python "%~dp0antigravity_discord_bridge.py"

echo.
echo =======================================================
echo 🎉 啟動成功！Discord Bridge 正在背景守護並連線 Discord！
echo 📱 請打開手機/電腦 Discord 享受極致雙向 Agent 體驗！
echo =======================================================
timeout /t 3 >nul
