@echo off
chcp 65001 >nul
echo 正在為夥伴設定「Windows 開機自動無感靜默啟動」...
set "TARGET=%~dp0靜默啟動Discord橋接器.vbs"
set "SHORTCUT=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\DiscordAgentBridge.vbs"
copy /Y "%TARGET%" "%SHORTCUT%" >nul
echo ? 設定完成！以後每次開機，Discord 橋接器就會在背景默默守護，完全不用手動開啟終端機！??
pause