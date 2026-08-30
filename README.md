# 🎮 Antigravity Discord Agent Bridge (Discord ⇄ PC Gemini 3.7 Flash 雙向智能體工作站)

> 🚀 **隨身掌控開機中的電腦 Agent，徹底釋放 Gemini 3.7 Flash 旗艦主腦！**  
> 透過 Discord 手機 / 電腦 App 隨身操控電腦、自動建立獨立任務討論串 (Thread)、動態資料夾樹狀圖 Select Menu 導航、跨端相片自動落地備份、遠端 PowerShell 指令操盤與最新 APK 自動推播。

---

## 🌟 核心特色 (Key Features)

- 🧠 **雙層智能協同架構 (Dual-Layer Agentic Pipeline)**：
  - 輕量管理 (查目錄/搬移/終端/問答)：由 Llama 3.2 11B 隨身管家秒回處理，0 消耗電腦對話 Token！
  - 重度編程 (寫代碼/重構/編譯 APK)：自動委派至電腦端 **Gemini 3.7 Flash** 旗艦主腦！
- 🧵 **獨立任務討論串 (Thread Isolation)**：
  - 執行 `/code` 編程任務時自動拉開專屬 Thread，過程日誌與連續補充說明在 Thread 進行，主頻道永遠乾淨不洗屏！
- 🏰 **一鍵自動伺服器空間架構**：
  - 首次啟動自動建好【📋 個人隨身資料庫】與【🧠 AI 智能體主控台】各專屬頻道與分類！
- 📡 **雙向成果自動監聽推播 (AgentOutboxWatcher)**：
  - 電腦端 Gemini 3.7 完成代碼修改或編譯 APK 後，自動推播至 `#🚀-建置成果與apk` 頻道！
- 👑 **多人協同與角色權限防禦體系 (RBAC)**：
  - 伺服器擁有者（夥伴）獨享 `/run` 與本機操控權限，同學/訪客安全隔離！
- 🌲 **互動式視覺化樹狀地圖 (`/tree`)**：
  - 動態 ASCII 樹狀圖搭配 Discord 原生 Select Menu 下拉選單，一鍵深入子目錄與切換專案！
- 📥 **相片跨端直達落地**：
  - 在 `#📥-相片傳送與落地` 發圖，自動下載存入電腦 `Pictures/illit`，支援一鍵整批搬移。

---

## 📂 專案結構 (Directory Structure)

```text
Discord_Agent_Bridge/
├── antigravity_discord_bridge.py   # 核心 Discord 雙向橋接器守護進程 (Python)
├── discord_bridge_config.json      # 橋接器設定檔 (Token、Guild ID、路徑與參數)
├── 啟動Discord橋接器.bat           # Windows 一鍵啟動背景守護腳本
├── 使用指南_3分鐘極速啟用.md       # 詳細 Discord 啟用指南
├── 手機上傳臨時存放區/             # 手機上傳照片/檔案之暫存目錄
├── 📱_手機Discord即時收件匣.md     # 電腦螢幕即時收件匣 (本機獨立)
├── 🎮_Discord歷史紀錄.log          # 手機端完整提問歷史 Log
└── README.md
```

---

## 🚀 快速開始 (Quick Start)

### 步驟 1：啟動橋接器
- **Windows**：雙擊運行 `啟動Discord橋接器.bat`（或在終端機執行）：
```powershell
python antigravity_discord_bridge.py
```

---

## 💬 常用 Slash 指令 (Slash Commands)

| 指令 | 說明 |
| :--- | :--- |
| `/code [需求]` | ⚡ 委派電腦端 **Gemini 3.7 Flash** 執行重度編程與改代碼 (自動開 Thread) |
| `/tree` | 🧭 檢視工作區資料夾樹狀圖，透過下拉選單切換專案 |
| `/cd [目錄]` | 🎯 切換當前工作專案與目錄 (`/cd 視覺動態效果/mobile`) |
| `/ls` | 📂 查看當前專案目錄檔案清單 |
| `/run [指令]` | 💻 遠端在電腦執行 PowerShell 指令 (夥伴專屬特權) |
| `/apk` | 📦 索取最新 Samsung A32 氣氛燈 APK 安裝包 |
| `/status` | 📊 查看電腦系統狀態與 Agent 健康度儀表板 |
| `/codewhale` | 🐳 調用本地 CodeWhale 零 Token 智能體執行指令 |
| `/init_server` | 🏰 一鍵自動在伺服器建立完整的分類與專屬頻道架構 |

---

## 🔒 隱私與安全性 (Privacy & Security)

- 所有的問答、日誌與上傳檔案均儲存於本機，不經過第三方伺服器中轉。
- `.gitignore` 已排除敏感的設定檔與日誌，請安心維護與開源！

---

## 📄 License
MIT License

