# 🚀 Antigravity 可移動執行與 VS Code 擴充整合架構指南

> 📌 **專案目錄**：`c:\Users\yexia\Documents\ShihWei\NTNU\GitHub\Telegram_Agent_Bridge\`  
> 🎯 **核心目標**：
> 1. **單一 IDE 體驗**：在標準 VS Code 中安裝擴充模組，直接對話並調用 Antigravity Agent，無需切換兩個 IDE。
> 2. **手機端 (vivo) 遠端操控電腦 Agent**：人離開房間時，透過手機遠端下指令給開機中的電腦，由電腦端 Agent 自動編寫程式、編譯 APK、執行測試並即時回報進度至手機，**徹底擺脫雲端 Spark 免費用量限制**！

---

## 🛠️ 第一部分：VS Code 擴充套件安裝與整合 (單一 IDE 方案)

若夥伴希望在平時慣用的 VS Code 中直接調用 Antigravity Agent，主要有以下 **3 種高效率整合途徑**：

```mermaid
graph LR
    subgraph VS Code 環境
        A[VS Code 編輯器] --> B1[擴充套件 1: Google Gemini Code Assist]
        A --> B2[擴充套件 2: Roo Code / Cline 轉接]
        A --> B3[擴充套件 3: 內建 Terminal 直連 agy CLI]
    end
    B1 --> C[Antigravity 雲端/本地 Agent 核心]
    B2 --> C
    B3 --> C
```

### 1. 方案 A（官方最穩）：安裝 Google Gemini Code Assist / Antigravity Extension
* **安裝方式**：
  1. 打開 VS Code ➔ 點擊左側「擴充套件 (Extensions)」圖示（或按 `Ctrl+Shift+X`）。
  2. 搜尋 **`Google Cloud Code`** 或 **`Gemini Code Assist`**。
  3. 點擊「安裝 (Install)」，並使用你的 Google 開發者帳號登入。
* **特性**：
  * 在 VS Code 側邊欄直接開啟對話面板。
  * 支援選取程式碼行內重構（`Ctrl+I`）、自動補全與診斷修復。

### 2. 方案 B（極客首選）：Roo Code / Cline 配置本地端點
* **安裝方式**：
  1. 在 VS Code 擴充市集搜尋安裝 **`Roo Code`** 或 **`Cline`**。
  2. 在設定中設定 API Provider 或本機代理端點，掛載相同的 `.agents` 規則與自定義技能。
* **特性**：
  * 擁有與 Antigravity 相同的高自主權（可自動執行終端指令、自動讀寫多檔案、自動修復報錯）。

### 3. 方案 C（極速輕量）：VS Code 內建 Terminal 直連 `agy` CLI
* **操作方式**：
  1. 在 VS Code 按下 `Ctrl + ~` 開啟內建終端機。
  2. 直接輸入 `agy` 啟動終端互動 Agent 模式。
  3. 支援所有 `/` 斜線指令與自定義 Skills。

---

## 📱 第二部分：手機端 (vivo) 遠端操控電腦 Agent（無額度限制架構）

當夥伴離開房間或出門在外時，只要家中電腦保持開機聯網，手機端（vivo）即可無縫下達指令，指揮電腦端 Agent 幹活並接收回報！

```mermaid
sequenceDiagram
    autonumber
    actor Partner as 夥伴 (vivo 手機)
    participant MobileApp as 手機端介面 (Telegram / Web / VSCode Web)
    participant CloudRelay as 免費安全中繼 (Bot API / Tailscale / Tunnel)
    participant PCServer as 家中電腦 (守護進程 + Antigravity Agent)
    participant Workspace as 本地專案與編譯環境 (Gradle / ADB)

    Partner->>MobileApp: 發送語音/文字任務指令 ("幫我修復 FB 去廣告並打包")
    MobileApp->>CloudRelay: 安全加密傳輸指令
    CloudRelay->>PCServer: 喚醒電腦 Agent 核心執行工作
    PCServer->>Workspace: 自動讀寫程式碼、編譯 APK、執行單元測試
    Workspace-->>PCServer: 產出最新 APK 與執行日誌
    PCServer->>CloudRelay: 回傳任務完成報告 + 截圖 + 安裝包
    CloudRelay-->>MobileApp: 即時推播通知
    MobileApp-->>Partner: 手機即時查看成果並下載 APK
```

---

### 🌟 4 大實作方案深度對比與評估

| 方案名稱 | 連線方式 | 手機端操作體驗 | 網路要求 | 免費度與額度限制 | 推薦指數 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **🥇 方案 1：Telegram Bot 私人專屬控制台** | 官方 Bot API | 像跟朋友傳訊息一樣，支援手機語音、圖片、推播 | 任何行動網路皆可 | 100% 完全免費、零用量上限 | ⭐⭐⭐⭐⭐ (最強推薦) |
| **🥈 方案 2：VS Code Remote Tunnels** | 微軟官方隧道 | 手機瀏覽器直接打開完整 VS Code 網頁版 | 登入 GitHub 即連 | 100% 完全免費 | ⭐⭐⭐⭐☆ |
| **🥉 方案 3：Tailscale + Agent Web UI** | Mesh VPN 虛擬區網 | 手機瀏覽器開啟專屬網頁控制台 | 需安裝 Tailscale App | 100% 完全免費 (個人 100 台設備) | ⭐⭐⭐⭐☆ |
| **🏅 方案 4：Termux + SSH 終端** | SSH 金鑰連線 | 手機文字終端操作 | 需虛擬區網或穿透 | 100% 完全免費 | ⭐⭐⭐☆☆ |

---

### 🥇 方案 1 詳細實作步驟：Telegram Bot 私人助理（最推薦）

* **為什麼最適合夥伴？**
  1. **零額度限制**：使用電腦本地算力與 Antigravity 核心，絕不扣除 Spark 額度。
  2. **支援語音輸入**：夥伴在外面走路、通勤時，直接對 Telegram 按住說話，電腦端自動將語音轉文字並執行 Agent 任務。
  3. **自動回傳檔案與截圖**：電腦端編譯好 APK 或完成截圖，Bot 會直接把 `.apk` 與 `.png` 傳回你的 Telegram 聊天室，在手機上點擊即可安裝！
* **架構組成**：
  * **電腦端**：常駐一隻輕量 Python 腳本（`antigravity_mobile_bridge.py`）。
  * **手機端**：官方 Telegram App（私聊機器人，僅授權夥伴的 Telegram User ID，100% 絕對安全）。

---

### 🥈 方案 2 詳細實作步驟：VS Code Remote Tunnels（極簡零配置）

* **操作步驟**：
  1. **電腦端**：
     * 打開 VS Code 終端機，執行：
       ```powershell
       code tunnel
       ```
     * 依照提示使用 GitHub 帳號登入授權，取得專屬隧道網址（例如 `https://vscode.dev/tunnel/my-pc`）。
  2. **手機端 (vivo)**：
     * 打開手機 Chrome 瀏覽器，進入 `https://vscode.dev` 並登入同一個 GitHub 帳號。
     * 手機畫面上會直接出現你家中電腦的完整 VS Code 檔案樹，側邊欄即可直接與 Agent 對話與修改程式碼！

---

## 🌐 第三部分：官方 Web Remote (`gravity.google.com`) 發現與 Discord Bridge 雙軌定位研判 (2026-09-03)

### 1. 2026-09-03 重大技術發現
* **發現背景**：夥伴在實驗筆電安裝 Antigravity 2.0 獨立桌面版後，發現官方提供全新的 **Web Remote Control** 網頁介面（`gravity.google.com`）。
* **實測核心能力**：
  1. **免安裝原生 App**：支援標準 PWA（可直接從手機 Chrome/Brave「新增至主畫面」化身為全螢幕 App）。
  2. **跨公網穿透**：經 5G 行動網路實測，無需在同一個區域網路（無需同一 WiFi），手機直接穿透 Google 雲端中繼連回家中/實驗室筆電。
  3. **多裝置與專案切換**：頂端具備設備下拉選單（`laptop-xxx... ▼`），支援切換多台筆電與選擇不同 Workspace 專案。
  4. **硬碟實體檔案讀寫**：手機下達 Prompt，電腦端本機硬碟實際執行程式碼讀寫、測試與終端機指令。

### 2. 核心架構解析：為什麼 IDE 版沒有，但無 IDE 的 2.0 版卻有？
* **Antigravity IDE (VS Code 核心)**：以「本機沉浸人機協同」為初衷，專注游標補全、Ctrl+I 行內編輯與本機除錯，其 Agent 引擎為 VS Code 外掛子進程，不開放外部中繼以免產生編輯器未存檔衝突 (Dirty Buffer Overwrite)。
* **Antigravity 2.0 (獨立案頭版)**：無傳統編輯器負擔，定位為「自主 Agent 調度中心」，以常駐 Daemon 運作並原生啟用 `--remote-control` 協議與 Google 雲端配對。
* **本機共存性驗證**：兩者在同一台電腦上**100% 原生相容共存**（安裝路徑獨立、共用 `~/.gemini/config` 規則與自訂技能、通訊埠隨機隔離無衝突）。

### 3. 官方 Web 版 vs Discord Agent Bridge 雙軌互補評估

| 核心維度 | 官方 Web Remote (`gravity.google.com`) | 本專案 Discord Agent Bridge |
| :--- | :--- | :--- |
| **推播通知 (Push)** | ❌ 網頁在手機背景極易被系統殺後台，無原生系統震動通知 | 🌟 **原生系統推播**！任務完成、出錯、需授權時即時彈窗通知 |
| **連線穿透穩定性** | 依賴長連線 WebSocket，受限於校園/特定防火牆限制 | 走標準 Discord 雲端伺服器，**穿透力 100% 絕對穩健** |
| **隨身操作體驗** | 手機小螢幕操作網頁設定與瀏覽 Diff 較繁瑣 | **支援按住隨手發語音（轉文字）、拍照傳圖**，直覺如傳訊息 |
| **客製化自動化** | 僅限官方 UI 功能 | 支援自訂指令（查電腦負載、GPU 狀態、自訂工作流） |

* **架構定位結論**：
  * **官方 `gravity.google.com`**：作為「深層重度操作看板」（坐下時檢視完整程式碼 Diff、Artifacts 與模型調整）。
  * **Discord Bridge**：作為「隨身輕量推播與語音遙控器」（人在外面時的即時推播提醒、快速派工、一鍵授權）。

---

## 📝 當前狀態與後續推進決策 (2026-09-03 封存結案)

1. **現況留存備忘**：本次討論與技術研判已完整收錄存檔於本架構指南與 AI-Memory 本地記憶中樞。
2. **專案正式封存 (Archived)**：
   * 經實測驗證，**Antigravity 2.0 獨立桌面版** 與 **Antigravity IDE** 在同一台 Windows 電腦可完美同時共存並行。
   * 官方 Web Remote（`gravity.google.com`）已能完全滿足手機在外遠端連線電腦的需求。
   * 因此本 Discord Agent Bridge 專案圓滿達成技術探索與原型設計之使命，正式完成封存推播至 GitHub 典藏。日後若有更高階的客製化推播需求，可直接參考本專案之開源代碼與技術架構！🌟

