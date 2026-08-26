# 📱 Antigravity Mobile Agent Bridge (Telegram ⇄ PC Dedicated Agent)

> 🚀 **隨身操控開機中的電腦 Agent，徹底擺脫雲端 Spark 額度限制！**  
> 透過 Telegram 手機 App 直接下達指令、手機專屬獨立 Agent 深度對話、視覺化資料夾樹狀圖導航、批次接收照片與 APK 檔案。

---

## 🌟 核心特色 (Key Features)

- 📱 **手機端專屬獨立 Agent (Dedicated Mobile Agent)**：
  - 手機端具備獨立的多輪對話記憶與專屬視窗，問答純淨直達，不與電腦端其他視窗衝突！
- 📦 **100% 本地路徑隔離 (Clean Local Storage Isolation)**：
  - 即時收件匣、歷史紀錄 Log、手機上傳臨時存放區全面收納於本專案目錄內，不污染 `任務` 或其他專案！
- 🧭 **互動式視覺化樹狀地圖 (`/tree`)**：
  - 動態生成 ASCII 樹狀圖，搭配 Telegram Inline Keyboard 實現一鍵層層深入子資料夾、返回上一層與切換專案！
- 🔕 **相片批次合流防刷屏 (Debounce Buffer)**：
  - 手機連傳多張照片時，自動合流為 1 則乾淨匯總卡片，杜絕通知轟炸。
- 🚚 **自動檔案搬移與目標記憶**：
  - 支援口語化設定「*放到 illit / 桌面 / 04*」，或「*把暫存區移到桌面*」一鍵搬移並清空。
- 🔒 **隱私安全與單例防護**：
  - 專屬 User ID 白名單防護，他人無法存取；單例進程鎖定（Port 47890）防止重複啟動與連線衝突。
- ⚡ **0 API 額度消耗**：完全利用家中電腦本機算力與 Antigravity IDE / 本地 Agent，無用量上限。

---

## 📂 專案結構 (Directory Structure)

```text
Telegram_Agent_Bridge/
├── antigravity_telegram_bridge.py   # 核心橋接器守護進程 (Python)
├── bridge_config.json               # 橋接器設定檔 (Token、路徑與參數)
├── bridge_config.template.json      # 配置檔範本
├── 啟動Telegram橋接器.bat           # Windows 一鍵啟動背景守護腳本
├── 使用指南_3分鐘極速啟用.md       # 詳細啟用指南
├── 手機上傳臨時存放區/             # 手機上傳照片/檔案之暫存目錄
├── 📱_手機Telegram即時收件匣.md     # 電腦螢幕即時收件匣 (本機獨立)
├── 📱_手機Telegram歷史紀錄.log     # 手機端完整提問歷史 Log
├── Antigravity_VSCode擴充與手機遠端操控架構指南.md
└── README.md
```

---

## 🚀 快速開始 (Quick Start)

### 步驟 1：建立 Telegram Bot
1. 在 Telegram 搜尋 **`@BotFather`**。
2. 輸入 `/newbot` 建立機器人，取得專屬 **`HTTP API Token`**。

### 步驟 2：設定設定檔
1. 在 `bridge_config.json` 填入你的 Bot Token：
```json
{
    "bot_token": "YOUR_TELEGRAM_BOT_TOKEN_HERE",
    "allowed_user_id": 0,
    "workspace_root": "c:\\Users\\yexia\\Documents\\ShihWei\\NTNU\\GitHub",
    "current_project": "Telegram_Agent_Bridge",
    "auto_sync_agent_replies": false,
    "poll_interval_seconds": 1.0
}
```
*(首次在手機向 Bot 發送 `/start` 時，系統會自動鎖定並填入你的 Telegram User ID 作為白名單)*

### 步驟 3：啟動橋接器
- **Windows**：雙擊運行 `啟動Telegram橋接器.bat`（或在終端機執行）：
```powershell
python antigravity_telegram_bridge.py
```

---

## 💬 常用指令 (Bot Commands)

| 指令 | 說明 |
| :--- | :--- |
| `/tree` | 🧭 瀏覽 IDE 資料夾樹地圖 / 檔案總管 (點擊按鈕層層深入與切換) |
| `/cd` | 🎯 切換工作專案或目錄 (`/cd <關鍵字>` 或 `/cd ..`) |
| `/ls` | 📂 查看當前專案目錄底下的檔案與資料夾清單 |
| `/pwd` | 📍 檢視當前工作位置與圖片上傳目標路徑 |
| `/staging` | 📦 查看【手機上傳臨時存放區】中的暫存檔案 |
| `/status` | 📊 檢視手機專屬 Agent 狀態與連線健康度 |
| `/clear` | 🧹 重置手機即時收件匣與對話記憶 |
| `/apk` | 📦 傳送最新編譯之 APK 安裝包至手機 |
| `/pin` | 📌 重新發送並置頂專屬隨身操作面板卡片 |

---

## 🔒 隱私與安全性 (Privacy & Security)

- 所有的問答、日誌與上傳檔案均儲存於本機，不會經過第三方伺服器中轉。
- `.gitignore` 已預先排除敏感的 `bridge_config.json`、日誌記錄與個人暫存媒體，請放心維護與開源！

---

## 📄 License
MIT License
