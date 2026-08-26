# 🤖 Antigravity Mobile Agent Bridge (Telegram ⇄ PC Agent)

> 🚀 **隨身操控開機中的電腦 Agent，徹底擺脫雲端 Spark 額度限制！**  
> 透過 Telegram 手機 App 直接下達指令、長按引用回覆精準分流多個 Agent、批次接收照片與 APK 檔案。

---

## 🌟 核心特色 (Key Features)

- 📱 **手機端無縫操作**：支援 iOS / Android Telegram 官方 App，出門在外隨時隨地交辦任務。
- 🎯 **長按引用回覆精準分流 (Reply-To Precision Routing)**：
  - 電腦端多個 Agent 同時運作並推播時，手機端只需「長按訊息點選回覆」，系統自動將指令送往該專屬 Agent（如鈣鈦礦、任務、手機維修等），絕不混淆！
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
antigravity_mobile_bridge/
├── Telegram_Agent_Bridge/
│   ├── antigravity_telegram_bridge.py   # 核心橋接器守護進程 (Python)
│   ├── bridge_config.template.json      # 配置檔範本 (複製為 bridge_config.json)
│   ├── 啟動Telegram橋接器.bat           # Windows 一鍵啟動背景守護腳本
│   ├── 使用指南_3分鐘極速啟用.md       # 詳細啟用指南
│   └── 手機上傳臨時存放區/             # 手機上傳照片/檔案之暫存目錄
├── Antigravity_VSCode擴充與手機遠端操控架構指南.md
└── README.md
```

---

## 🚀 快速開始 (Quick Start)

### 步驟 1：建立 Telegram Bot
1. 在 Telegram 搜尋 **`@BotFather`**。
2. 輸入 `/newbot` 建立機器人，取得專屬 **`HTTP API Token`**。

### 步驟 2：建立設定檔
在 `Telegram_Agent_Bridge/` 目錄下：
1. 將 `bridge_config.template.json` 複製並更名為 `bridge_config.json`。
2. 填入你的 Bot Token：
```json
{
    "bot_token": "YOUR_TELEGRAM_BOT_TOKEN_HERE",
    "allowed_user_id": 0,
    "workspace_root": "C:\\Your\\Workspace\\Path",
    "current_project": "任務",
    "auto_sync_agent_replies": true,
    "poll_interval_seconds": 1.0
}
```
*(首次在手機向 Bot 發送 `/start` 時，系統會自動鎖定並填入你的 Telegram User ID 作為白名單)*

### 步驟 3：啟動橋接器
- **Windows**：雙擊運行 `啟動Telegram橋接器.bat`（或在終端機執行）：
```powershell
python "Telegram_Agent_Bridge\antigravity_telegram_bridge.py"
```

---

## 💬 常用指令 (Bot Commands)

| 指令 | 說明 |
| :--- | :--- |
| `/start` 或 `/pin` | 重新發送並置頂隨身操作卡片 |
| `/projects` | 彈出互動資料夾按鈕，切換當前工作專案 |
| `/ls` | 列出當前專案目錄底下的檔案與資料夾 |
| `/staging` | 查看【手機上傳臨時存放區】中的暫存檔案 |
| `/status` | 檢視連線狀態、工作目錄與 Agent 健康度 |
| `/apk` | 傳送最新編譯之 APK 安裝包至手機 |
| `/clear` | 重置手機即時收件匣 |

---

## 🔒 隱私與安全性 (Privacy & Security)

- 所有的問答、日誌與上傳檔案均儲存於本機，不會經過第三方伺服器中轉。
- `.gitignore` 已預先排除敏感的 `bridge_config.json`、日誌記錄與個人暫存媒體，請放心維護與開源！

---

## 📄 License
MIT License
