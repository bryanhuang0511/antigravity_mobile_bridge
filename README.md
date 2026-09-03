# 🎮 Antigravity Discord Agent Bridge (已封存 / Archived)

> 📦 **【專案狀態公告：已正式結案並封存備忘 (Archived & Sunset - 2026-09-03)】**  
> 本專案為 2026 年探索「手機端遠端操控電腦 Antigravity Agent」的高可用跨端橋接原型。隨著官方生態的演進與重大實測突破，本專案已圓滿達成歷史探索使命並正式歸檔留存。

---

## 💡 決策脈絡與封存原因 (Architecture Evolution & Decision Rationale)

### 1. 核心實測突破：雙版本完美並存
經過夥伴實際部署與深度驗證：
* **Antigravity 獨立桌面版 (2.0)** 與 **Antigravity IDE (VS Code 核心版本)** 在同一台 Windows 電腦上**可以 100% 同時存在、同時獨立運行**。
* 兩者安裝路徑獨立、通訊埠自動隔離、共用 `~/.gemini/config` 的全域自訂技能與規則，完全沒有資源衝突或覆蓋問題。

### 2. 官方 Web Remote 原生賦能 (`gravity.google.com`)
* 官方 Antigravity 2.0 原生提供了全新的 **Web Remote Control** 網頁介面。
* **PWA 與公網穿透**：手機端透過 Chrome / Brave「新增至主畫面」即可化身全螢幕 App，5G 行動網路免 VPN 直接穿透 Google 雲端中繼連回家中筆電。
* **實體磁碟讀寫與任務調度**：在手機端下達指令，電腦本機硬碟直接執行代碼修改、測試與終端機任務。

### 3. 開發者工作流之終極收斂
* **本機沉浸開發**：坐在電腦前時，使用 **Antigravity IDE** 享受極速代碼自動補全、`Ctrl+I` 行內重構與本機除錯。
* **隨身外出操控**：離開電腦時，後台常駐的 **Antigravity 2.0** 搭配手機 `gravity.google.com` PWA 隨身下達指令。
* **結論**：由於官方原生生態已完整覆蓋「手機外出操控電腦 Agent」之核心痛點，無需再額外維護常駐的 Discord Bot 進程、中繼伺服器與 Bot Token，因此本專案正式封存，作為經典架構原型留存於 GitHub。

---

## 🌟 原專案核心特色 (Key Features - Archive Reference)

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
├── discord_bridge_config.template.json # 橋接器設定檔範本 (Token、Guild ID、路徑與參數)
├── 啟動Discord橋接器.bat           # Windows 一鍵啟動背景守護腳本
├── 靜默啟動Discord橋接器.vbs       # Windows 背景無黑窗啟動腳本
├── 停止Discord橋接器.bat           # 一鍵安全停止背景守護進程
├── 使用指南_3分鐘極速啟用.md       # 詳細 Discord 啟用指南
├── Antigravity_VSCode擴充與手機遠端操控架構指南.md # 深度跨端架構研判指南
├── 開源零Token模型驅動跨端Agent架構實戰筆記.md # 零 Token 本地模型架構筆記
├── 手機上傳臨時存放區/             # 手機上傳照片/檔案之暫存目錄
├── 📱_手機Discord即時收件匣.md     # 電腦螢幕即時收件匣 (本機獨立)
└── README.md
```

---

## 💬 支援之 Slash 指令彙整 (Slash Commands)

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

## 🔒 隱私與安全規範 (Privacy & Security)

- 所有的問答、日誌與上傳檔案均儲存於本機，不經過任何第三方不可信伺服器中轉。
- `.gitignore` 已嚴密排除真實設定檔 (`discord_bridge_config.json`) 與本機敏感日誌，確保開源程式碼庫的安全無虞。

---

## 📄 License
MIT License
