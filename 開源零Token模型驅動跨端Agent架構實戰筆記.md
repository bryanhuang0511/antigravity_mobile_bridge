# 🚀 開源零 Token 模型驅動跨端 Agent 架構實戰筆記 (Zero-Cost Mobile & Desktop Agent)

> 💡 **核心定位**：記錄如何利用免費開源模型（如 NVIDIA NIM / Llama 3.2）結合本機 Python 工具鏈，打造零 Token 費用、可隨身遙控電腦的自主智能體（Agent），並與 Roo Code、CodeWhale 及電腦端 Antigravity 旗艦大腦無縫聯動。

---

## 🌟 一、核心架構發現與底層原理

### 1. 什麼是 Agent？（打破「必須花大錢用閉源大模型」的迷思）
很多開發者誤以為只有 OpenAI GPT-4o 或 Claude 3.5 Sonnet 才能充當 Agent。但實戰證明，**Agent 的本質是「決策迴圈」而非單純的模型體積**：

$$\text{Agent (智能體)} = \text{開源 LLM 大腦 (意圖識別與決策)} + \text{本地程式手腳 (Tool Calling 工具鏈)}$$

### 2. 手機端 Telegram Mobile Agent 的運作機制
在 `Telegram_Agent_Bridge` 專案中，我們驗證了一套極度輕量、零成本且功能強大的架構：
1. **開源大腦**：採用 Meta 最新開源的多模態模型 **`meta/llama-3.2-11b-vision-instruct`**。
2. **算力後盾**：利用 NVIDIA Build (NVIDIA NIM) 提供的開發者免費推論端點（`https://integrate.api.nvidia.com/v1`），完全 **$0 元、無 Token 扣費**。
3. **本地 Python 工具鏈（手腳）**：
   * 📁 **檔案總管與樹狀圖**：`os.walk` + 演算法即時生成 ASCII 專案目錄樹與 Inline Keyboard 按鈕。
   * 🚚 **自動檔案搬移**：`shutil.move` 依自然語言指令將手機上傳的照片/文件搬入指定專案目錄。
   * ⚡ **終端遠端操盤**：`subprocess` 調用 PowerShell 執行 `git`、編譯命令或自動化測試腳本。
   * 🎙️ **多模態與語音**：即時下載 Telegram 語音與照片並納入上下文隊列。

---

## 🛠️ 二、如何將此免費開源模型接入 Roo Code / CodeWhale / Cline？

這套經由 NVIDIA NIM 驅動的開源模型端點，採用標準的 **OpenAI-Compatible API** 規範，可以直接填入各類 AI 編程工具中，達成 **100% 免 Token 費用的 Coding Agent**！

### 1. Roo Code / Cline 設定指南：
* **Provider**：選擇 `OpenAI Compatible`
* **Base URL**：`https://integrate.api.nvidia.com/v1`
* **API Key**：填入你的 NVIDIA 金鑰（存於 `nvidia_build.txt`）
* **Model ID 選拔**：
  * 輕量極速型：`meta/llama-3.2-11b-vision-instruct`（秒級回應，適合日常問答與代碼解讀）
  * 深度代碼重構型：`nvidia/llama-3.1-nemotron-70b-instruct` 或 `meta/llama-3.3-70b-instruct`（適合跨檔案架構重構）

### 2. CodeWhale / OpenClaw 設定指南：
在環境變數或設定檔中指定：
```bash
OPENAI_BASE_URL=https://integrate.api.nvidia.com/v1
OPENAI_API_KEY=nvapi-V4nvgNluNVjMchje...
MODEL_NAME=meta/llama-3.2-11b-vision-instruct
```

---

## ⚖️ 三、能力邊界與安全分工（開源 11B vs 電腦端 Gemini 3.7 Flash）

在實際開發中，必須清醒認識開源輕量模型與頂級旗艦模型的定位差異：

| 評估維度 | 📱 手機端 Llama 3.2 11B (隨身管家) | 💻 電腦端 Gemini 3.7 Flash (旗艦主腦) |
| :--- | :--- | :--- |
| **核心強項** | 秒回對話、目錄導航、檔案搬移、下達執行指令 | 跨多檔案架構設計、百萬 Context 依賴追蹤、重構完整 APP、自動解決編譯報錯 |
| **能力極限** | **無法獨立從零寫出複雜多檔案 APP 架構**（易產生依賴幻覺） | 具備全端工程師級別的自主編程與除錯能力 |
| **最佳角色** | 前線通訊兵、隨身檔案秘書、終端指令發送端 | 首席軟體架構師、重度代碼開發者 |

---

## 🔄 四、雙向中繼機制（手機 Telegram ⇄ 電腦 Gemini 3.7 Flash）

當需要進行大型 APP 開發或程式修改時，手機端會將任務自動「委派」給電腦端：

```
📱 手機 Telegram (語音 / 文字交辦任務)
        │
        ▼
📡 Telegram Bridge (背景守護進程)
   • 立即在手機顯示 Working 狀態（支援連續補充說明）
   • 寫入 ➔ 📱_手機Telegram即時收件匣.md
        │
        ▼
💻 電腦端 Antigravity IDE (Gemini 3.7 Flash)
   • 讀取收件匣，深度編寫專案代碼、修改多檔案
   • 執行 Gradle/Python 測試驗證，編譯產出 APK
        │
        ▼
📲 Telegram Bridge 自動將代碼報告與最新 .apk 檔案秒傳回手機！
```

---

## 🌟 五、如何切換為 Google 官方 Gemini Flash API？

如果希望手機端獨立問答也 100% 走 Google 官方的 Gemini Flash：
1. 前往 [Google AI Studio](https://aistudio.google.com) 免費申請一組 Gemini API Key。
2. 將 Key 填入 `google .env`（`GOOGLE_API_KEY=AIzaSy...`）或 `bridge_config.json`。
3. Bridge 即可直接直連 Google 官方 `gemini-2.0-flash` 或 `gemini-2.5-flash` 端點！
