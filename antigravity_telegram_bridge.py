#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📱 Antigravity Telegram ⇄ Gemini 3.7 Flash 雙向智能體旗艦橋接器
========================================================================================
✨ 核心亮點升級：
1. 🧠 雙層智能協同架構 (Dual-Layer Agentic Pipeline)：
   - 輕量管理 (查目錄/搬移/終端/問答)：由手機端 Llama 3.2 11B 隨身管家秒回處理！
   - 重度編程 (寫代碼/重構/編譯 APK)：自動委派至電腦端 Gemini 3.7 Flash 旗艦主腦，代碼零改壞！
2. 📡 雙向成果自動監聽推播 (AgentOutboxWatcher)：
   - 電腦端 Gemini 3.7 Flash 完成代碼修改與編譯後，自動將成果報告與最新 .apk 檔案秒傳回手機 Telegram！
3. 🐳 本地零 Token 輕量工具協同 (CodeWhale Integration)：
   - 支援 /codewhale 指令直接調用本機 codewhale.exe，完全 0 Token 支出！
4. 🔄 一鍵重新生成 / 重試按鈕 (One-Click Retry)：
   - 每個回覆下方均附帶 [ 🔄 重新生成 / 重試 ] 按鈕，隨時一鍵重新呼叫大腦！
5. 💬 工作中連續補充說明 (Continuous Steering Queue)：
   - 在 Agent Working 時，夥伴可隨時發送文字或語音進行「補充說明」，系統自動合流納入當前大腦處理！
6. 🌲 互動式視覺化樹狀地圖 (/tree)：
   - 動態 ASCII 資料夾樹狀圖與 Telegram Inline Keyboard 自由深入、返回與切換專案！
"""

import os
import sys
import time
import json
import socket
import logging
import threading
import subprocess
import shutil
import urllib.request
import urllib.parse
import ssl
from typing import Dict, Any, Optional, List, Tuple

# 設定 Windows 控制台 UTF-8 編碼
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("AntigravityDualBridge")

# ==============================================================================
# ⚙️ 配置檔案路徑與目錄定義 (100% 本地隔離)
# ==============================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "bridge_config.json")
WORKSPACE_DEFAULT = r"c:\Users\yexia\Documents\ShihWei\NTNU\GitHub"
PID_FILE = os.path.join(BASE_DIR, ".bridge.pid")

# 🌟 本地收件匣與日誌 (完全獨立於 Telegram_Agent_Bridge 目錄內)
INBOX_FILE = os.path.join(BASE_DIR, "📱_手機Telegram即時收件匣.md")
HISTORY_LOG_FILE = os.path.join(BASE_DIR, "📱_手機Telegram歷史紀錄.log")
PENDING_SYNC_FILE = os.path.expanduser(r"~\.gemini\memory_vault\pending_sync.md")

# 🌟 常用目錄路徑
STAGING_DIR = os.path.join(BASE_DIR, "手機上傳臨時存放區")
DESKTOP_DIR = os.path.expanduser(r"~\Desktop")
PICTURES_DIR = os.path.join(os.environ.get("USERPROFILE", os.path.expanduser("~")), "Pictures")
ILLIT_DIR = os.path.join(PICTURES_DIR, "illit")
NVIDIA_KEY_FILE = os.path.join(WORKSPACE_DEFAULT, "nvidia_build.txt")
CODEWHALE_EXE = os.path.join(WORKSPACE_DEFAULT, "任務", "02_AI編程智能體_ZeroToken_CodeWhale_RooCode", "CodeWhale", "codewhale.exe")

os.makedirs(STAGING_DIR, exist_ok=True)
os.makedirs(ILLIT_DIR, exist_ok=True)

# ==============================================================================
# 🔒 單例進程鎖定器
# ==============================================================================
SINGLETON_SOCKET = None
def ensure_single_instance(port: int = 47890) -> bool:
    global SINGLETON_SOCKET
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('127.0.0.1', port))
        s.listen(1)
        SINGLETON_SOCKET = s
        try:
            with open(PID_FILE, "w", encoding="utf-8") as f:
                f.write(str(os.getpid()))
        except Exception:
            pass
        logger.info("🔒 成功取得單例進程鎖定 (Port: %d, PID: %d)！", port, os.getpid())
        return True
    except socket.error:
        logger.error("❌ 已經有另一個 Bridge 進程正在運行！請關閉舊進程後再重試。")
        sys.exit(0)

# ==============================================================================
# 🔑 API Key 與設定檔管理
# ==============================================================================
def get_nvidia_api_key() -> str:
    """自動讀取 NVIDIA API Key (支援環境變數、配置檔與本地密鑰檔)"""
    env_key = os.environ.get("NVIDIA_API_KEY", "").strip()
    if env_key.startswith("nvapi-"):
        return env_key
    if os.path.exists(NVIDIA_KEY_FILE):
        try:
            with open(NVIDIA_KEY_FILE, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f if line.strip()]
                for l in lines:
                    if l.startswith("nvapi-"):
                        return l
        except Exception as e:
            logger.debug(f"讀取 nvidia_build.txt 失敗: {e}")
    return ""

def load_config() -> Dict[str, Any]:
    default_cfg = {
        "bot_token": "YOUR_TELEGRAM_BOT_TOKEN_HERE",
        "allowed_user_id": 0,
        "workspace_root": WORKSPACE_DEFAULT,
        "current_project": "Telegram_Agent_Bridge",
        "target_upload_dir": ILLIT_DIR,
        "target_upload_name": "🖼️ 圖片/illit",
        "auto_sync_agent_replies": True,
        "poll_interval_seconds": 1.0,
        "ai_model": "meta/llama-3.2-11b-vision-instruct"
    }
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                default_cfg.update(saved)
                return default_cfg
        except Exception as e:
            logger.error(f"讀取設定檔失敗: {e}")
    return default_cfg

def save_config(cfg: Dict[str, Any]):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=4, ensure_ascii=False)
    except Exception as e:
        logger.error(f"儲存設定檔失敗: {e}")

# ==============================================================================
# 📡 Telegram Bot API 客戶端
# ==============================================================================
class TelegramClient:
    def __init__(self, token: str):
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.ssl_ctx = ssl.create_default_context()

    def _request(self, endpoint: str, data: Optional[Dict[str, Any]] = None, silent_fail: bool = False, timeout: int = 35) -> Optional[Dict[str, Any]]:
        url = f"{self.base_url}/{endpoint}"
        try:
            if data is not None:
                json_data = json.dumps(data).encode("utf-8")
                req = urllib.request.Request(
                    url,
                    data=json_data,
                    headers={"Content-Type": "application/json", "User-Agent": "AntigravityDualBridge/8.0"}
                )
            else:
                req = urllib.request.Request(url, headers={"User-Agent": "AntigravityDualBridge/8.0"})

            with urllib.request.urlopen(req, context=self.ssl_ctx, timeout=timeout) as response:
                res_body = response.read().decode("utf-8")
                res_json = json.loads(res_body)
                if res_json.get("ok"):
                    return res_json.get("result")
                else:
                    if not silent_fail:
                        logger.error(f"Telegram API 報錯 ({endpoint}): {res_json}")
        except urllib.error.HTTPError as e:
            if e.code == 409:
                if not silent_fail:
                    logger.warning("Telegram 409 Conflict，等待連線就緒...")
                time.sleep(2)
            else:
                if not silent_fail:
                    logger.error(f"HTTP Error ({endpoint}): {e}")
        except Exception as e:
            if not silent_fail:
                logger.error(f"連線 Telegram API 異常 ({endpoint}): {e}")
        return None

    def get_updates(self, offset: int = 0, timeout: int = 20) -> list:
        res = self._request("getUpdates", {"offset": offset, "timeout": timeout}, timeout=timeout + 10)
        return res if res is not None else []

    def set_bot_commands(self) -> bool:
        """設定手機端專屬簡潔指令清單"""
        commands = [
            {"command": "tree", "description": "🧭 IDE 檔案總管 / 資料夾樹地圖 (點擊切換)"},
            {"command": "cd", "description": "🎯 切換工作專案或目錄 (/cd <關鍵字>)"},
            {"command": "ls", "description": "📂 查看當前專案目錄檔案清單"},
            {"command": "pwd", "description": "📍 檢視當前工作位置與上傳目標"},
            {"command": "staging", "description": "📦 查看【手機上傳臨時存放區】檔案"},
            {"command": "status", "description": "📊 檢視手機專屬 Agent 狀態與健康度"},
            {"command": "codewhale", "description": "🐳 本機零 Token 智能體執行指令"},
            {"command": "clear", "description": "🧹 重置手機即時收件匣與對話記憶"},
            {"command": "apk", "description": "📦 傳送最新 Samsung A32 氣氛燈 APK"},
            {"command": "pin", "description": "📌 置頂手機專屬操作面板卡片"}
        ]
        res = self._request("setMyCommands", {"commands": commands})
        if res:
            logger.info("✨ 成功向 Telegram 註冊最新手機專屬指令選單！")
        return res is not None

    def answer_callback_query(self, callback_query_id: str, text: str = ""):
        self._request("answerCallbackQuery", {"callback_query_id": callback_query_id, "text": text}, silent_fail=True)

    def send_chat_action(self, chat_id: int, action: str = "typing") -> bool:
        res = self._request("sendChatAction", {"chat_id": chat_id, "action": action}, silent_fail=True)
        return res is not None

    def pin_chat_message(self, chat_id: int, message_id: int) -> bool:
        res = self._request("pinChatMessage", {"chat_id": chat_id, "message_id": message_id, "disable_notification": True})
        return res is not None

    def send_message(self, chat_id: int, text: str, reply_markup: Optional[Dict[str, Any]] = None, parse_mode: Optional[str] = "Markdown", reply_to_message_id: Optional[int] = None) -> Optional[int]:
        if not text:
            return None
        max_chunk = 3600
        chunks = [text[i:i+max_chunk] for i in range(0, len(text), max_chunk)]
        
        last_msg_id = None
        for idx, chunk in enumerate(chunks):
            payload = {
                "chat_id": chat_id,
                "text": chunk
            }
            if parse_mode:
                payload["parse_mode"] = parse_mode
            if idx == len(chunks) - 1 and reply_markup:
                payload["reply_markup"] = reply_markup
            if idx == 0 and reply_to_message_id:
                payload["reply_to_message_id"] = reply_to_message_id
            
            res = self._request("sendMessage", payload, silent_fail=True)
            if res is None and parse_mode:
                payload.pop("parse_mode", None)
                res = self._request("sendMessage", payload, silent_fail=False)
            
            if res and isinstance(res, dict):
                last_msg_id = res.get("message_id")
                
        return last_msg_id

    def edit_message_text(self, chat_id: int, message_id: int, text: str, reply_markup: Optional[Dict[str, Any]] = None, parse_mode: Optional[str] = "Markdown") -> bool:
        if not text or not message_id:
            return False
        payload = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text[:3800]
        }
        if parse_mode:
            payload["parse_mode"] = parse_mode
        if reply_markup:
            payload["reply_markup"] = reply_markup

        res = self._request("editMessageText", payload, silent_fail=True)
        if res is None and parse_mode:
            payload.pop("parse_mode", None)
            res = self._request("editMessageText", payload, silent_fail=False)
        return res is not None

    def download_file(self, file_id: str, dest_path: str) -> bool:
        try:
            res = self._request("getFile", {"file_id": file_id})
            if not res or not res.get("file_path"):
                return False
            file_path = res["file_path"]
            download_url = f"https://api.telegram.org/file/bot{self.token}/{file_path}"
            
            req = urllib.request.Request(download_url, headers={"User-Agent": "AntigravityDualBridge/8.0"})
            os.makedirs(os.path.dirname(os.path.abspath(dest_path)), exist_ok=True)
            
            with urllib.request.urlopen(req, context=self.ssl_ctx, timeout=60) as resp:
                with open(dest_path, "wb") as f:
                    f.write(resp.read())
            return True
        except Exception as e:
            logger.error(f"下載 Telegram 檔案失敗: {e}")
            return False

    def send_document(self, chat_id: int, file_path: str, caption: str = "") -> bool:
        if not os.path.exists(file_path):
            self.send_message(chat_id, f"❌ 檔案不存在：{file_path}", parse_mode=None)
            return False

        url = f"{self.base_url}/sendDocument"
        boundary = "----WebKitFormBoundaryAntigravityBridge"
        filename = os.path.basename(file_path)

        body = bytearray()
        body.extend(f"--{boundary}\r\nContent-Disposition: form-data; name=\"chat_id\"\r\n\r\n{chat_id}\r\n".encode("utf-8"))
        if caption:
            body.extend(f"--{boundary}\r\nContent-Disposition: form-data; name=\"caption\"\r\n\r\n{caption}\r\n".encode("utf-8"))
        body.extend(f"--{boundary}\r\nContent-Disposition: form-data; name=\"document\"; filename=\"{filename}\"\r\nContent-Type: application/octet-stream\r\n\r\n".encode("utf-8"))
        with open(file_path, "rb") as f:
            body.extend(f.read())
        body.extend(f"\r\n--{boundary}--\r\n".encode("utf-8"))

        try:
            req = urllib.request.Request(
                url,
                data=body,
                headers={"Content-Type": f"multipart/form-data; boundary={boundary}", "User-Agent": "AntigravityDualBridge/8.0"}
            )
            with urllib.request.urlopen(req, context=self.ssl_ctx, timeout=120) as response:
                res = json.loads(response.read().decode("utf-8"))
                return res.get("ok", False)
        except Exception as e:
            logger.error(f"傳送檔案失敗: {e}")
            return False

# ==============================================================================
# 🤖 手機專屬輕量 AI 思考大腦 (Llama-3.2-Vision 隨身管家)
# ==============================================================================
class MobileAIEngine:
    @staticmethod
    def get_system_prompt(current_project: str, current_cwd: str, target_upload_name: str, target_upload_dir: str) -> str:
        return f"""你是夥伴專屬的【📱 Antigravity 手機隨身管家 Agent】！
每次對話稱呼夥伴為「夥伴」。

【回答風格與原則】：
1. 🌟 50% 情緒價值 + 50% 實質解答，多使用活力表情符號 🌟 🚀 💡 ✨ 🎉。
2. 繁體中文回答，條理分明、簡潔精準，適合手機螢幕快速閱讀。
3. 嚴格領域隔離：非物理話題禁止使用物理公式或比喻；專注回答夥伴當前交辦的軟體、檔案或工程任務。
4. 軟體安全守則：絕不在未經夥伴明確授權下刪除重要系統檔案或軟體。

【當前環境】：
- 當前工作專案：{current_project}
- 本地實體目錄：{current_cwd}
- 預設存圖目標：{target_upload_name} ({target_upload_dir})
- 手機臨時存放區：{STAGING_DIR}
"""

    @staticmethod
    def query_ai(user_prompt: str, current_project: str, current_cwd: str, target_upload_name: str, target_upload_dir: str, history: Optional[List[Dict[str, str]]] = None, model: str = "meta/llama-3.2-11b-vision-instruct") -> str:
        api_key = get_nvidia_api_key()
        if not api_key:
            return "⚠️ 未找到有效的 NVIDIA API Key，請檢查 nvidia_build.txt！"

        url = "https://integrate.api.nvidia.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "AntigravityDualBridge/8.0"
        }

        system_content = MobileAIEngine.get_system_prompt(current_project, current_cwd, target_upload_name, target_upload_dir)
        messages = [{"role": "system", "content": system_content}]
        if history:
            for item in history[-6:]:
                messages.append({"role": item.get("role", "user"), "content": item.get("content", "")})
        messages.append({"role": "user", "content": user_prompt})

        candidate_models = [model, "meta/llama-3.2-11b-vision-instruct"]
        seen = set()
        models_to_try = [m for m in candidate_models if not (m in seen or seen.add(m))]

        ctx = ssl.create_default_context()

        for cur_model in models_to_try:
            data = {
                "model": cur_model,
                "messages": messages,
                "max_tokens": 1200,
                "temperature": 0.6
            }

            for attempt in range(2):
                try:
                    req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers)
                    with urllib.request.urlopen(req, context=ctx, timeout=25) as resp:
                        res = json.loads(resp.read().decode("utf-8"))
                        choices = res.get("choices", [])
                        if choices and choices[0].get("message", {}).get("content"):
                            return choices[0]["message"]["content"].strip()
                except Exception as e:
                    logger.warning(f"模型 {cur_model} 第 {attempt+1} 次嘗試異常: {e}")
                    time.sleep(1)

        return "⚠️ AI 大腦正在自我校準中，請點擊下方【 🔄 重新生成 / 重試 】按鈕，我會立即為你重新計算！🌟"

# ==============================================================================
# 📝 本地日誌、收件匣與記憶統整器
# ==============================================================================
class MobileStorageManager:
    @staticmethod
    def record_inbox(user_id: int, message_text: str, project_name: str = "Telegram_Agent_Bridge", cwd: str = "", status: str = "🟢 處理完成", answer: str = "", is_heavy_task: bool = False):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        
        # 寫入歷史 Log 檔
        log_entry = f"[{timestamp}] [User: {user_id}] [Project: {project_name}]\n提問: {message_text}\n狀態: {status}\n回覆: {answer[:200]}...\n{'-'*50}\n"
        try:
            with open(HISTORY_LOG_FILE, "a", encoding="utf-8") as f:
                f.write(log_entry)
        except Exception as e:
            logger.error(f"寫入歷史 Log 失敗: {e}")

        # 寫入電腦螢幕即時收件匣
        answer_block = ""
        if answer:
            answer_block = f"### ✨ Agent 執行結果：\n```text\n{answer[:800]}...\n```\n\n"

        task_mode = "⚡ 重度編程任務 (委派電腦端 Gemini 3.7 Flash)" if is_heavy_task else "📱 隨身管家指令 (Llama-3.2-Vision)"

        inbox_content = (
            "# 📱 手機 Telegram ⇄ 電腦螢幕即時收件匣\n\n"
            f"> 🕒 **時間**：`{timestamp}` | 狀態：`{status}`\n"
            f"> 🎯 **模式**：`{task_mode}`\n"
            f"> 📁 **目標專案**：`{project_name}` (`{cwd}`)\n\n"
            "### 💬 夥伴手機最新指令與提問：\n"
            "```text\n"
            f"{message_text}\n"
            "```\n\n"
            f"{answer_block}"
            "---\n"
            "💡 *提示：電腦端 Gemini 3.7 Flash 完成任務並更新此檔案後，Bridge 會自動把成果與 APK 秒傳回手機！*\n"
        )
        try:
            with open(INBOX_FILE, "w", encoding="utf-8") as f:
                f.write(inbox_content)
        except Exception as e:
            logger.error(f"寫入收件匣失敗: {e}")

    @staticmethod
    def sync_to_ai_memory(summary_text: str, project_name: str):
        timestamp = time.strftime("%Y-%m-%d %H:%M")
        entry = f"- **[{timestamp} 手機專屬 Agent ({project_name})]**：{summary_text}\n"
        try:
            os.makedirs(os.path.dirname(PENDING_SYNC_FILE), exist_ok=True)
            if not os.path.exists(PENDING_SYNC_FILE):
                with open(PENDING_SYNC_FILE, "w", encoding="utf-8") as f:
                    f.write("# 📥 待分類緩衝記憶區 (Pending Sync Buffer)\n\n---\n\n")
            with open(PENDING_SYNC_FILE, "a", encoding="utf-8") as f:
                f.write(entry)
            logger.info(f"🧠 已自動將手機操作摘要記入 pending_sync.md: {summary_text[:30]}...")
        except Exception as e:
            logger.debug(f"寫入 pending_sync.md 失敗: {e}")

# ==============================================================================
# 🔕 批次相片合流防刷屏緩衝器 (Photo Batch Debounce Buffer)
# ==============================================================================
class PhotoBatchBuffer:
    def __init__(self, flush_callback, delay_seconds: float = 2.0):
        self.flush_callback = flush_callback
        self.delay_seconds = delay_seconds
        self.items: List[Dict[str, Any]] = []
        self.timer: Optional[threading.Timer] = None
        self.lock = threading.Lock()

    def add(self, item: Dict[str, Any]):
        with self.lock:
            self.items.append(item)
            if self.timer:
                self.timer.cancel()
            self.timer = threading.Timer(self.delay_seconds, self._flush)
            self.timer.start()

    def _flush(self):
        with self.lock:
            batch = list(self.items)
            self.items.clear()
            self.timer = None
        if batch:
            self.flush_callback(batch)

# ==============================================================================
# 🎮 雙向智能體橋接核心 (Antigravity Dual Bridge Daemon)
# ==============================================================================
class AntigravityBridgeDaemon:
    def __init__(self):
        self.config = load_config()
        self.token = self.config.get("bot_token", "")
        self.allowed_user_id = int(self.config.get("allowed_user_id", 0))
        self.client = TelegramClient(self.token)
        self.running = True
        
        self.workspace_root = self.config.get("workspace_root", WORKSPACE_DEFAULT)
        self.current_project = self.config.get("current_project", "Telegram_Agent_Bridge")
        self.current_cwd = os.path.join(self.workspace_root, self.current_project.replace("/", "\\"))
        if not os.path.exists(self.current_cwd):
            self.current_cwd = os.path.join(self.workspace_root, "Telegram_Agent_Bridge")
            if not os.path.exists(self.current_cwd):
                self.current_cwd = self.workspace_root
            
        # 🌟 持久化目標存放目錄
        self.target_upload_dir = self.config.get("target_upload_dir", ILLIT_DIR)
        self.target_upload_name = self.config.get("target_upload_name", "🖼️ 圖片/illit")
        os.makedirs(self.target_upload_dir, exist_ok=True)
        
        # 🌟 手機專屬獨立對話歷史
        self.mobile_chat_history: List[Dict[str, str]] = []
        
        # 🌟 最近一次夥伴提問
        self.last_user_query: Dict[int, str] = {}
        
        # 🌟 正在運行的任務狀態與補充說明隊列
        self.active_working_tasks: Dict[int, Dict[str, Any]] = {}
        self.task_lock = threading.Lock()
        
        # 🌟 收件匣監聽最後記錄 (用於自動推播 Gemini 3.7 執行成果)
        self.last_inbox_mtime = 0.0
        self.last_pushed_answer = ""
        
        # 🌟 批次相片防刷屏緩衝器
        self.photo_buffer = PhotoBatchBuffer(self.on_photo_batch_finished, delay_seconds=2.0)

    # --------------------------------------------------------------------------
    # 📡 雙向成果監聽線程 (AgentOutboxWatcher)
    # --------------------------------------------------------------------------
    def start_outbox_watcher_thread(self):
        """背景持續監聽電腦端 Gemini 3.7 Flash 寫入的成果報告與新編譯 APK"""
        def _watcher():
            logger.info("📡 雙向成果監聽線程 (AgentOutboxWatcher) 已啟動！")
            if os.path.exists(INBOX_FILE):
                self.last_inbox_mtime = os.path.getmtime(INBOX_FILE)

            while self.running:
                try:
                    if self.allowed_user_id and os.path.exists(INBOX_FILE):
                        mtime = os.path.getmtime(INBOX_FILE)
                        if mtime > self.last_inbox_mtime:
                            self.last_inbox_mtime = mtime
                            with open(INBOX_FILE, "r", encoding="utf-8", errors="replace") as f:
                                content = f.read()

                            # 檢測是否有電腦端 Agent 剛寫入的完成結果
                            if "### ✨ Agent 執行結果：" in content and "狀態：`🟢" in content:
                                try:
                                    ans_part = content.split("### ✨ Agent 執行結果：")[1].split("---")[0].strip()
                                    if ans_part and ans_part != self.last_pushed_answer:
                                        self.last_pushed_answer = ans_part
                                        logger.info("🎉 偵測到電腦端 Gemini 3.7 Flash 執行完畢，自動推播至手機 Telegram...")
                                        
                                        push_text = (
                                            "🎉 **【電腦端 Gemini 3.7 Flash 旗艦主腦執行完成】** 🌟\n"
                                            "━━━━━━━━━━━━━━━━━━━━━\n"
                                            f"📍 **專案**：`{self.current_project}`\n\n"
                                            f"{ans_part}\n\n"
                                            "💡 *提示：所有程式碼與工程變更已在電腦端落實生效！*"
                                        )
                                        self.client.send_message(self.allowed_user_id, push_text, reply_markup=self.get_reply_action_keyboard())
                                        
                                        # 自動檢查是否有 2 分鐘內剛編譯生成的最新 APK
                                        self._auto_check_and_send_new_apk(self.allowed_user_id)
                                except Exception as err:
                                    logger.debug(f"解析收件匣成果失敗: {err}")

                except Exception as e:
                    logger.debug(f"監聽線程輪詢異常: {e}")
                time.sleep(2)

        t = threading.Thread(target=_watcher, daemon=True)
        t.start()

    def _auto_check_and_send_new_apk(self, chat_id: int):
        """自動掃描工作區是否有剛剛編譯出的 APK 並秒傳手機"""
        try:
            apk_candidates = [
                os.path.join(self.workspace_root, "視覺動態效果手機待修", "mobile", "手機音效氣氛燈_A32專屬版.apk"),
                os.path.join(self.workspace_root, "FB_adblock.apk")
            ]
            now = time.time()
            for apk in apk_candidates:
                if os.path.exists(apk):
                    apk_mtime = os.path.getmtime(apk)
                    if now - apk_mtime < 120:  # 2 分鐘內新產生的 APK
                        logger.info(f"📦 偵測到最新編譯的 APK ({apk})，自動傳送至 Telegram...")
                        self.client.send_document(chat_id, apk, "✨ 這是電腦端 Gemini 3.7 Flash 剛剛編譯產出的最新 APK 安裝包！")
                        break
        except Exception as e:
            logger.debug(f"自動傳送 APK 失敗: {e}")

    # --------------------------------------------------------------------------
    # 🌲 視覺化樹狀圖生成與導航按鈕
    # --------------------------------------------------------------------------
    def generate_ascii_tree(self, root_dir: str, max_depth: int = 2) -> str:
        """動態生成美觀清晰的 ASCII 資料夾與檔案樹狀結構"""
        if not os.path.exists(root_dir):
            return "(目錄不存在)"

        ignored = {".git", "__pycache__", "node_modules", "venv", ".gemini", ".vscode", "tempmediaStorage", ".system_generated"}
        lines = []

        def _build_tree(current_path: str, prefix: str = "", depth: int = 1):
            if depth > max_depth:
                return
            try:
                entries = sorted(os.listdir(current_path))
            except Exception:
                return

            dirs = [e for e in entries if os.path.isdir(os.path.join(current_path, e)) and e not in ignored and not e.startswith(".")]
            files = [e for e in entries if os.path.isfile(os.path.join(current_path, e)) and not e.startswith(".")]

            total_items = dirs[:5] + files[:4]
            count = len(total_items)

            for idx, item in enumerate(total_items):
                is_last = (idx == count - 1)
                branch = "└── " if is_last else "├── "
                next_prefix = prefix + ("    " if is_last else "│   ")
                
                item_path = os.path.join(current_path, item)
                if os.path.isdir(item_path):
                    lines.append(f"{prefix}{branch}📁 **{item}/**")
                    if depth < max_depth:
                        _build_tree(item_path, next_prefix, depth + 1)
                else:
                    lines.append(f"{prefix}{branch}📄 `{item}`")

            if len(dirs) > 5 or len(files) > 4:
                lines.append(f"{prefix}└── ... *(其他項略)*")

        lines.append(f"📁 **{os.path.basename(root_dir) if root_dir != self.workspace_root else 'GitHub 根目錄'}/**")
        _build_tree(root_dir, "", 1)
        return "\n".join(lines)

    def get_directory_browser_keyboard(self, target_path: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
        """動態生成 IDE 風格檔案總管 / 資料夾樹地圖 (包含 ASCII 樹狀預覽與互動按鈕)"""
        curr = target_path if target_path and os.path.exists(target_path) else self.current_cwd
        if not os.path.exists(curr):
            curr = self.workspace_root
            
        rel_curr = os.path.relpath(curr, self.workspace_root).replace("\\", "/")
        if rel_curr == ".":
            rel_curr = "🏠 GitHub 根目錄 (Workspace Root)"
            
        entries = []
        try:
            ignored = {".git", "__pycache__", "node_modules", "venv", ".gemini", ".vscode", "tempmediaStorage", ".system_generated"}
            entries = [d for d in os.listdir(curr) if os.path.isdir(os.path.join(curr, d)) and d not in ignored and not d.startswith(".")]
        except Exception:
            entries = []
            
        keyboard_buttons = []
        
        # 1. 子資料夾按鈕 (每行 2 個)
        row = []
        for d in entries[:10]:
            sub_abs = os.path.join(curr, d)
            sub_rel = os.path.relpath(sub_abs, self.workspace_root).replace("\\", "/")
            row.append({"text": f"📁 {d}", "callback_data": f"nav_dir:{sub_rel}"})
            if len(row) == 2:
                keyboard_buttons.append(row)
                row = []
        if row:
            keyboard_buttons.append(row)
            
        # 2. 導航控制列 (上一層 / 回根目錄)
        nav_row = []
        if os.path.abspath(curr) != os.path.abspath(self.workspace_root):
            parent_abs = os.path.dirname(curr)
            parent_rel = os.path.relpath(parent_abs, self.workspace_root).replace("\\", "/")
            nav_row.append({"text": "⬆️ 返回上一層", "callback_data": f"nav_dir:{parent_rel}"})
            nav_row.append({"text": "🏠 回根目錄", "callback_data": "nav_dir:."})
        if nav_row:
            keyboard_buttons.append(nav_row)
            
        # 3. 動作控制列
        curr_rel_code = os.path.relpath(curr, self.workspace_root).replace("\\", "/")
        keyboard_buttons.append([
            {"text": "✅ 鎖定此目錄為工作專案", "callback_data": f"set_proj:{curr_rel_code}"},
            {"text": "📂 查看檔案清單 (/ls)", "callback_data": f"action_ls:{curr_rel_code}"}
        ])
        keyboard_buttons.append([
            {"text": "🖼️ 設為圖片目標", "callback_data": f"set_target_dir:{curr_rel_code}"},
            {"text": "📦 查看暫存區", "callback_data": "action:staging"}
        ])

        # 生成 ASCII 樹狀圖
        ascii_tree = self.generate_ascii_tree(curr, max_depth=2)
        
        text = (
            "🧭 **【IDE 檔案總管 / 資料夾樹地圖】** 🌟\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            f"📍 **當前瀏覽**：`{rel_curr}`\n"
            f"📁 **實體路徑**：`{curr}`\n\n"
            f"🌲 **樹狀結構預覽**：\n"
            f"{ascii_tree}\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "👇 **點擊下方按鈕即可層層深入，點擊「✅ 鎖定」即切換至該專案！**"
        )
        return text, {"inline_keyboard": keyboard_buttons}

    def get_reply_action_keyboard(self) -> Dict[str, Any]:
        """生成每則回覆下方的快捷操作按鈕"""
        return {
            "inline_keyboard": [
                [
                    {"text": "🔄 重新生成 / 重試", "callback_data": "action:retry"},
                    {"text": "🧭 資料夾樹 (/tree)", "callback_data": "action:tree"}
                ],
                [
                    {"text": "📂 查看檔案 (/ls)", "callback_data": "action:ls"},
                    {"text": "📌 操作面板", "callback_data": "action:pin"}
                ]
            ]
        }

    def get_project_keyboard(self) -> Dict[str, Any]:
        keyboard = {
            "inline_keyboard": [
                [
                    {"text": "🧭 檔案總管 / 樹地圖 (/tree)", "callback_data": "action:tree"},
                    {"text": "📂 查看當前檔案 (/ls)", "callback_data": "action:ls"}
                ],
                [
                    {"text": "🤖 Telegram Bridge (本專案)", "callback_data": "set_proj:Telegram_Agent_Bridge"},
                    {"text": "📱 視覺動態效果/mobile", "callback_data": "set_proj:視覺動態效果/mobile"}
                ],
                [
                    {"text": "🧪 鈣鈦礦 (Perovskite)", "callback_data": "set_proj:Perovskite"},
                    {"text": "🎮 BalatroMaker", "callback_data": "set_proj:BalatroMaker"}
                ],
                [
                    {"text": "🖼️ 存圖: illit", "callback_data": "set_target:illit"},
                    {"text": "🖥️ 存圖: 桌面", "callback_data": "set_target:desktop"},
                    {"text": "📦 存圖: 暫存區", "callback_data": "set_target:staging"}
                ]
            ]
        }
        return keyboard

    def send_pin_guide(self, chat_id: int):
        guide_text = (
            "📌 **【Antigravity 雙向 Agent 隨身指揮中樞】** 🌟\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            f"🎯 **當前專案**：`{self.current_project}`\n"
            f"📁 **工作目錄**：`{self.current_cwd}`\n"
            f"🖼️ **圖片目標**：`{self.target_upload_name}`\n"
            f"📦 **臨時存放區**：`Telegram_Agent_Bridge/手機上傳臨時存放區`\n\n"
            "💬 **操作技巧**：\n"
            "• ⚡ **重度編程**：說「幫我重構/寫程式/加功能」，自動委派電腦端 **Gemini 3.7 Flash** 執行！\n"
            "• 📱 **隨身管家**：直接傳送問答、語音或搬移指令，秒級自治完成！\n"
            "• 🌲 **樹狀地圖**：輸入 `/tree` 瀏覽完整資料夾樹，點擊按鈕自由切換！\n"
            "• 🖼️ **傳圖直達**：直接傳送多張照片，自動存入【`圖片/illit`】並合流通知！\n"
            "• 🚚 **整批搬移**：說「`把暫存區移到桌面`」或「`移到 illit`」，一鍵整批搬移！\n"
            "• 📂 **查看檔案**：輸入 `/ls` 列出當前專案所有檔案\n"
            "• ⚡ **執行指令**：輸入 `/run <PowerShell指令>` 遠端操盤\n"
            "• 🐳 **CodeWhale**：輸入 `/codewhale <指令>` 調用本機零 Token 智能體！\n"
            "• 📦 **傳送 APK**：輸入 `/apk` 秒傳最新安裝包！\n"
            "━━━━━━━━━━━━━━━━━━━━━"
        )
        msg_id = self.client.send_message(chat_id, guide_text, reply_markup=self.get_project_keyboard())
        if msg_id:
            self.client.pin_chat_message(chat_id, msg_id)

    # --------------------------------------------------------------------------
    # 🔍 智慧目錄比對與切換
    # --------------------------------------------------------------------------
    def get_all_workspace_directories(self) -> List[Tuple[str, str]]:
        """掃描 workspace_root 下的所有有效專案與子目錄 (絕對路徑, 相對路徑)"""
        results = []
        if not os.path.exists(self.workspace_root):
            return results
        
        ignored = {".git", "__pycache__", "node_modules", "venv", ".gemini", ".vscode", "tempmediaStorage", ".system_generated"}
        for root, dirs, _ in os.walk(self.workspace_root):
            dirs[:] = [d for d in dirs if d not in ignored and not d.startswith(".")]
            for d in dirs:
                abs_p = os.path.join(root, d)
                rel_p = os.path.relpath(abs_p, self.workspace_root).replace("\\", "/")
                results.append((abs_p, rel_p))
        return results

    def find_best_matching_directory(self, query_text: str) -> Tuple[Optional[str], Optional[str]]:
        """模糊智慧搜尋工作區資料夾 (支援多層子目錄如 視覺動態效果/mobile)"""
        q = query_text.strip().lower().replace("\\", "/")
        if not q:
            return None, None
        
        all_dirs = self.get_all_workspace_directories()
        
        # 1. 完整相對路徑比對
        for abs_p, rel_p in all_dirs:
            if rel_p.lower() == q:
                return abs_p, rel_p
                
        # 2. 結尾目錄完全比對
        for abs_p, rel_p in all_dirs:
            folder_name = os.path.basename(abs_p).lower()
            if folder_name == q:
                return abs_p, rel_p
                
        # 3. 關鍵字複合比對
        tokens = [t for t in q.replace("/", " ").replace("\\", " ").split() if len(t) > 1]
        if tokens:
            for abs_p, rel_p in all_dirs:
                rel_lower = rel_p.lower()
                if all(t in rel_lower for t in tokens):
                    return abs_p, rel_p
                    
        # 4. 部分包含比對
        for abs_p, rel_p in all_dirs:
            rel_lower = rel_p.lower()
            folder_name = os.path.basename(abs_p).lower()
            if q in rel_lower or q in folder_name:
                return abs_p, rel_p
                
        return None, None

    def try_switch_working_directory(self, user_text: str) -> Optional[str]:
        """自然語言與語音智慧辨識切換工作專案與目錄"""
        t = user_text.strip()
        nav_verbs = ["切到", "切換", "開", "移到", "進入", "去", "打開", "跳到", "到", "在", "層", "資料夾", "專案", "修補", "做", "前往", "cd "]
        has_nav_intent = any(v in t for v in nav_verbs) or t.startswith("/") or "mobile" in t.lower() or "視覺" in t or "鈣鈦礦" in t or "bridge" in t.lower()
        
        cleaned = t
        for v in nav_verbs:
            cleaned = cleaned.replace(v, " ")
        cleaned = cleaned.strip()

        matched_dir, rel_name = self.find_best_matching_directory(cleaned)
        if not matched_dir:
            matched_dir, rel_name = self.find_best_matching_directory(t)

        if matched_dir and (has_nav_intent or t.lower() == rel_name.lower() or t.lower() == os.path.basename(matched_dir).lower()):
            self.current_cwd = matched_dir
            self.current_project = rel_name
            self.config["current_project"] = rel_name
            self.config["current_cwd"] = matched_dir
            save_config(self.config)
            logger.info(f"🎯 夥伴切換工作專案至：{rel_name} ({matched_dir})")
            
            ls_preview = self.list_current_directory_files(cwd=matched_dir, proj_name=rel_name)
            res = (
                f"🎯 **【已成功切換至專案與目錄：{rel_name}】** 🌟\n"
                f"📍 **實體路徑**：`{matched_dir}`\n"
                "━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"{ls_preview}\n\n"
                "💡 *提示：接下來手機發送的所有指令、提問與程式碼編寫，都將直接作用於此目錄！*"
            )
            return res
        return None

    def resolve_target_directory(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        t = text.lower()
        if "illit" in t or "圖片/illit" in t or "照片/illit" in t:
            return ILLIT_DIR, "🖼️ 圖片/illit"
        if "桌面" in text or "桌布" in text or "desktop" in t:
            return DESKTOP_DIR, "🖥️ 電腦桌面 (Desktop)"
        if "telegram" in t or "bridge" in t or "橋接" in text or "04" in text:
            return os.path.join(self.workspace_root, "Telegram_Agent_Bridge"), "🤖 Telegram_Agent_Bridge"
        if "暫存" in text or "臨時" in text or "staging" in t:
            return STAGING_DIR, "📦 手機上傳臨時存放區"
        if "圖片" in text or "pictures" in t or "相片" in text:
            return PICTURES_DIR, "🖼️ 電腦圖片 (Pictures)"
            
        matched_dir, rel_name = self.find_best_matching_directory(text)
        if matched_dir:
            return matched_dir, f"📁 {rel_name}"
            
        return None, None

    def try_set_target_directory(self, user_text: str) -> Optional[str]:
        target_dir, dest_name = self.resolve_target_directory(user_text)
        if target_dir and ("放" in user_text or "存" in user_text or "設" in user_text or "換" in user_text or "到" in user_text or "目標" in user_text):
            os.makedirs(target_dir, exist_ok=True)
            self.target_upload_dir = target_dir
            self.target_upload_name = dest_name
            self.config["target_upload_dir"] = target_dir
            self.config["target_upload_name"] = dest_name
            save_config(self.config)
            
            logger.info(f"🎯 夥伴設定上傳目標為：{dest_name} ({target_dir})")
            res = (
                f"🎯 **【已成功設定上傳目標：{dest_name}】** 🌟\n\n"
                f"📂 **完整路徑**：`{target_dir}`\n\n"
                "📥 **接下來你在手機傳送的所有照片**，都會直接自動存入此資料夾，並自動合流為 1 則匯總通知！\n\n"
                "💡 *夥伴請直接開始傳圖吧！✨*"
            )
            return res
        return None

    def try_autonomous_file_action(self, user_text: str) -> Optional[str]:
        is_clean_staging = ("清空" in user_text or "刪除暫存" in user_text or "移除暫存" in user_text) and ("暫存" in user_text or "存放區" in user_text)
        if is_clean_staging:
            count = 0
            if os.path.exists(STAGING_DIR):
                for f in os.listdir(STAGING_DIR):
                    p = os.path.join(STAGING_DIR, f)
                    if os.path.isfile(p):
                        os.remove(p)
                        count += 1
            return f"🧹 **已成功清空【手機上傳臨時存放區】！共移除 {count} 個暫存檔案。**"

        target_dir, dest_name = self.resolve_target_directory(user_text)
        if target_dir and ("移" in user_text or "搬" in user_text or "丟" in user_text):
            if not os.path.exists(STAGING_DIR):
                return "⚠️ 臨時存放區不存在，目前無檔案可移動。"
            
            staging_files = [f for f in os.listdir(STAGING_DIR) if os.path.isfile(os.path.join(STAGING_DIR, f))]
            if not staging_files:
                return "⚠️ **【手機上傳臨時存放區】目前沒有檔案！**\n請先在手機 Telegram 上傳照片或檔案後，再叫我幫你搬移喔！"

            os.makedirs(target_dir, exist_ok=True)
            moved_list = []
            for f in staging_files:
                src_path = os.path.join(STAGING_DIR, f)
                dest_path = os.path.join(target_dir, f)
                try:
                    shutil.move(src_path, dest_path)
                    moved_list.append(f)
                except Exception as err:
                    logger.error(f"搬移 {f} 失敗: {err}")

            logger.info(f"🚚 成功將 {len(moved_list)} 個檔案從暫存區整批搬移至：{target_dir}")
            res_text = (
                f"🎉 **已自動幫你將 {len(moved_list)} 個檔案整批搬移完成！** 🌟\n\n"
                f"📍 **目標位置**：`{dest_name}`\n"
                f"📂 **路徑**：`{target_dir}`\n"
                f"📄 **搬移清單**：\n"
            )
            for mf in moved_list[:8]:
                res_text += f"  • `{mf}`\n"
            if len(moved_list) > 8:
                res_text += f"  ...等共 {len(moved_list)} 個檔案\n"
            res_text += "\n🧹 **暫存清理**：已自動從臨時存放區清空！✨"
            return res_text

        return None

    # --------------------------------------------------------------------------
    # 📂 目錄與檔案操作
    # --------------------------------------------------------------------------
    def list_staging_files(self) -> str:
        try:
            if not os.path.exists(STAGING_DIR):
                return "📦 **【手機上傳臨時存放區】目前為空。**"
            files = [f for f in os.listdir(STAGING_DIR) if os.path.isfile(os.path.join(STAGING_DIR, f))]
            if not files:
                return "📦 **【手機上傳臨時存放區】目前為空。**\n*(上傳新照片或檔案將自動暫存於此 ✨)*"
            
            res = f"📦 **【手機上傳臨時存放區】(共 {len(files)} 個檔案)** 🌟\n"
            res += f"📍 路徑：`{STAGING_DIR}`\n\n"
            for f in files:
                sz = os.path.getsize(os.path.join(STAGING_DIR, f)) // 1024
                mtime = time.strftime("%m/%d %H:%M", time.localtime(os.path.getmtime(os.path.join(STAGING_DIR, f))))
                res += f"  • 📄 `{f}` ({sz} KB, {mtime})\n"
            res += "\n💡 *你可以直接對我說：「幫我把圖片移到桌面」或「移到 illit」，我會直接整批搬移並清空暫存！*"
            return res
        except Exception as e:
            return f"❌ 讀取臨時存放區失敗：`{e}`"

    def list_current_directory_files(self, cwd: Optional[str] = None, proj_name: Optional[str] = None) -> str:
        target_cwd = cwd if cwd else self.current_cwd
        target_proj = proj_name if proj_name else self.current_project
        try:
            if not os.path.exists(target_cwd):
                return f"⚠️ 目錄不存在：`{target_cwd}`"
            entries = os.listdir(target_cwd)
            dirs = [d for d in entries if os.path.isdir(os.path.join(target_cwd, d))]
            files = [f for f in entries if os.path.isfile(os.path.join(target_cwd, f))]
            
            res = f"📂 **【{target_proj} 目錄檔案清單】** 🌟\n"
            res += f"📍 路徑：`{target_cwd}`\n\n"
            if dirs:
                res += "📁 **資料夾 (Directories)**:\n"
                for d in dirs[:15]:
                    res += f"  • 📁 `{d}/`\n"
                if len(dirs) > 15:
                    res += f"  ... 共 {len(dirs)} 個資料夾\n"
                res += "\n"
            if files:
                res += "📄 **檔案 (Files)**:\n"
                for f in files[:20]:
                    sz = os.path.getsize(os.path.join(target_cwd, f)) // 1024
                    res += f"  • 📄 `{f}` ({sz} KB)\n"
                if len(files) > 20:
                    res += f"  ... 共 {len(files)} 個檔案\n"
            if not dirs and not files:
                res += "*(此目錄目前為空)*\n"
            return res
        except Exception as e:
            return f"❌ 讀取目錄失敗：`{e}`"

    def read_file_content(self, filename: str, cwd: Optional[str] = None) -> str:
        target_cwd = cwd if cwd else self.current_cwd
        target = os.path.join(target_cwd, filename)
        if not os.path.exists(target):
            target = os.path.join(self.workspace_root, filename)
        if not os.path.exists(target):
            return f"❌ 找不到檔案：`{filename}`"
        try:
            with open(target, "r", encoding="utf-8", errors="replace") as f:
                content = f.read(3000)
            return f"📄 **【檔案內容: {os.path.basename(target)}】**\n```\n{content}\n```"
        except Exception as e:
            return f"❌ 讀取檔案失敗：`{e}`"

    def execute_command_sync(self, cmd: str, cwd: Optional[str] = None) -> str:
        exec_cwd = cwd if cwd else self.current_cwd
        try:
            res = subprocess.run(
                ["powershell", "-NoProfile", "-Command", cmd],
                cwd=exec_cwd,
                capture_output=True,
                text=True,
                timeout=180
            )
            out = res.stdout.strip()
            err = res.stderr.strip()
            if err:
                return f"⚠️ **執行輸出 (含警告/錯誤)**:\n```\n{out}\n{err}\n```"
            return f"✅ **執行成功**:\n```\n{out if out else '(無文字輸出)'}\n```"
        except subprocess.TimeoutExpired:
            return "⏱️ **執行超時**（超過 180 秒，已轉為背景執行）。"
        except Exception as e:
            return f"❌ **執行發生異常**: `{e}`"

    def execute_codewhale_sync(self, query: str) -> str:
        """調用本地 CodeWhale 智能體執行輕量任務"""
        if not os.path.exists(CODEWHALE_EXE):
            return f"⚠️ 未找到 CodeWhale 執行檔：`{CODEWHALE_EXE}`\n你可以直接使用 `/run <指令>` 或交由電腦端 Gemini 3.7 主腦處理！"
        
        try:
            logger.info(f"🐳 正在調用本地 CodeWhale 執行: {query[:30]}...")
            cmd = f'& "{CODEWHALE_EXE}" -p "{query}"'
            return self.execute_command_sync(cmd, cwd=self.current_cwd)
        except Exception as e:
            return f"❌ CodeWhale 執行異常：`{e}`"

    # --------------------------------------------------------------------------
    # 📷 相片與檔案處理
    # --------------------------------------------------------------------------
    def on_photo_batch_finished(self, batch: List[Dict[str, Any]]):
        if not batch:
            return
        
        chat_id = batch[0]["chat_id"]
        dest_name = batch[0]["dest_name"]
        target_dir = batch[0]["target_dir"]
        count = len(batch)
        
        total_kb = sum(b.get("size_kb", 0) for b in batch)
        
        summary = (
            f"🎉 **已成功接收並存入 {count} 張照片！** 🌟\n\n"
            f"📍 **存放位置**：`{dest_name}`\n"
            f"📂 **資料夾路徑**：`{target_dir}`\n"
            f"💾 **總檔案大小**：`{total_kb} KB`\n\n"
            "📄 **檔案清單**：\n"
        )
        for b in batch[:8]:
            summary += f"  • `{b['filename']}` ({b['size_kb']} KB)\n"
        if count > 8:
            summary += f"  ...等共 {count} 個檔案\n"
            
        summary += "\n💡 *提示：所有圖片已安全落地電腦，你可以隨時在電腦開啟或下指令操作！*"
        
        self.client.send_message(chat_id, summary, reply_markup=self.get_reply_action_keyboard())
        MobileStorageManager.record_inbox(self.allowed_user_id, f"[批次上傳 {count} 張照片]", project_name=self.current_project, cwd=target_dir, status="🟢 已全部存入", answer=summary)
        MobileStorageManager.sync_to_ai_memory(f"批次存入 {count} 張照片至 {dest_name}", self.current_project)

    def handle_photo_message(self, chat_id: int, user_id: int, photo_list: list, caption: str):
        try:
            file_id = photo_list[-1]["file_id"]
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"mobile_{timestamp}.jpg"
            
            target_dir = self.target_upload_dir
            dest_name = self.target_upload_name
            
            if caption:
                cap_dir, cap_name = self.resolve_target_directory(caption)
                if cap_dir:
                    target_dir = cap_dir
                    dest_name = cap_name

            os.makedirs(target_dir, exist_ok=True)
            dest_path = os.path.join(target_dir, filename)
            
            success = self.client.download_file(file_id, dest_path)
            if success:
                size_kb = os.path.getsize(dest_path) // 1024
                logger.info(f"📷 圖片下載成功: {dest_path} ({size_kb} KB)")
                self.photo_buffer.add({
                    "chat_id": chat_id,
                    "filename": filename,
                    "dest_path": dest_path,
                    "dest_name": dest_name,
                    "target_dir": target_dir,
                    "size_kb": size_kb
                })
            else:
                self.client.send_message(chat_id, "❌ 下載圖片失敗，請檢查網路連線。")
        except Exception as e:
            logger.error(f"處理上傳圖片異常: {e}")
            self.client.send_message(chat_id, f"❌ 處理圖片失敗：`{e}`")

    def handle_document_message(self, chat_id: int, user_id: int, doc_obj: dict, caption: str):
        try:
            file_id = doc_obj.get("file_id")
            file_name = doc_obj.get("file_name", f"mobile_doc_{time.strftime('%Y%m%d_%H%M%S')}")
            
            target_dir = self.target_upload_dir
            dest_name = self.target_upload_name
            
            os.makedirs(target_dir, exist_ok=True)
            dest_path = os.path.join(target_dir, file_name)
            
            self.client.send_chat_action(chat_id, "upload_document")
            success = self.client.download_file(file_id, dest_path)
            if success:
                size_kb = os.path.getsize(dest_path) // 1024
                reply = (
                    "🎉 **檔案已成功下載！** 🌟\n\n"
                    f"📄 **檔案名稱**：`{file_name}`\n"
                    f"📍 **存放位置**：`{dest_name}`\n"
                    f"📂 **路徑**：`{dest_path}`\n"
                    f"💾 **檔案大小**：`{size_kb} KB`"
                )
                self.client.send_message(chat_id, reply, reply_markup=self.get_reply_action_keyboard())
                MobileStorageManager.record_inbox(user_id, f"[上傳檔案: {file_name}]", project_name=self.current_project, cwd=target_dir, status="🟢 已下載存檔", answer=f"儲存於 {dest_path}")
            else:
                self.client.send_message(chat_id, "❌ 檔案下載失敗。")
        except Exception as e:
            logger.error(f"處理檔案異常: {e}")
            self.client.send_message(chat_id, f"❌ 處理檔案失敗：`{e}`")

    def handle_voice_message(self, chat_id: int, user_id: int, voice_obj: dict):
        """處理 Telegram 語音訊息"""
        try:
            file_id = voice_obj.get("file_id")
            duration = voice_obj.get("duration", 0)
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            voice_filename = f"voice_{timestamp}.oga"
            voice_path = os.path.join(STAGING_DIR, voice_filename)

            self.client.send_chat_action(chat_id, "record_voice")
            success = self.client.download_file(file_id, voice_path)
            if success:
                logger.info(f"🎙️ 成功下載夥伴語音訊息: {voice_path} (時長: {duration}s)")
                voice_text = f"[語音訊息指令 (時長 {duration} 秒)]"
                
                with self.task_lock:
                    is_active = user_id in self.active_working_tasks
                
                if is_active:
                    with self.task_lock:
                        if user_id in self.active_working_tasks:
                            self.active_working_tasks[user_id]["supplements"].append(f"夥伴補充語音訊息 (檔案: {voice_filename})")
                            w_msg_id = self.active_working_tasks[user_id].get("working_msg_id")
                            if w_msg_id:
                                supp_count = len(self.active_working_tasks[user_id]["supplements"])
                                update_text = (
                                    f"📥 **已收到夥伴指令！**\n"
                                    f"🎯 **目標專案**：`{self.current_project}`\n\n"
                                    f"⏳ **Working...** (已接收最新語音補充說明 🎙️ 共 {supp_count} 則，持續運算中 🚀)"
                                )
                                self.client.edit_message_text(chat_id, w_msg_id, update_text)
                    return
                else:
                    self.last_user_query[user_id] = voice_text
                    MobileStorageManager.record_inbox(user_id, voice_text, project_name=self.current_project, cwd=self.current_cwd, status="🟡 語音正在處理中...")
                    
                    working_text = (
                        f"🎙️ **已收到夥伴語音訊息！** (時長: {duration} 秒)\n"
                        f"🎯 **目標專案**：`{self.current_project}`\n\n"
                        f"⏳ **Working...** (手機專屬 Agent 正在深度解析與處理中 🚀)"
                    )
                    w_msg_id = self.client.send_message(chat_id, working_text)
                    self.process_ai_question_async(chat_id, user_id, f"夥伴傳送了一段 {duration} 秒的語音指令，請提供協助與解答！", w_msg_id)
            else:
                self.client.send_message(chat_id, "❌ 下載語音訊息失敗。")
        except Exception as e:
            logger.error(f"處理語音訊息異常: {e}")
            self.client.send_message(chat_id, f"❌ 處理語音失敗：`{e}`")

    # --------------------------------------------------------------------------
    # 🎛️ Inline Keyboard 點擊回呼處理
    # --------------------------------------------------------------------------
    def handle_callback_query(self, cb: Dict[str, Any]):
        cb_id = cb.get("id", "")
        data = cb.get("data", "")
        msg = cb.get("message", {})
        chat_id = msg.get("chat", {}).get("id", self.allowed_user_id)
        msg_id = msg.get("message_id")
        user_id = cb.get("from", {}).get("id", self.allowed_user_id)

        if data == "action:retry":
            last_q = self.last_user_query.get(user_id, "")
            if not last_q:
                self.client.answer_callback_query(cb_id, text="⚠️ 找不到上一次的提問內容")
                return
            
            self.client.answer_callback_query(cb_id, text="🔄 正在為你重新呼叫 AI 大腦運算...")
            retry_working_text = (
                f"🔄 **正在為夥伴重新生成回答...** 🌟\n"
                f"💬 「{last_q[:60]}」\n\n"
                f"⏳ **Working...** (AI 大腦急速重算中 🚀)"
            )
            self.client.edit_message_text(chat_id, msg_id, retry_working_text)
            self.process_ai_question_async(chat_id, user_id, last_q, msg_id, is_retry=True)

        elif data.startswith("nav_dir:"):
            rel_path = data.split("nav_dir:")[1]
            if rel_path == "." or not rel_path:
                target_abs = self.workspace_root
            else:
                target_abs = os.path.join(self.workspace_root, rel_path.replace("/", "\\"))
            self.client.answer_callback_query(cb_id, text=f"瀏覽：{rel_path}")
            tree_text, kb = self.get_directory_browser_keyboard(target_abs)
            self.client.edit_message_text(chat_id, msg_id, tree_text, reply_markup=kb)

        elif data.startswith("set_proj:"):
            proj = data.split("set_proj:")[1]
            if proj == "." or not proj:
                self.current_project = "GitHub 根目錄"
                self.current_cwd = self.workspace_root
            else:
                self.current_project = proj
                self.current_cwd = os.path.join(self.workspace_root, proj.replace("/", "\\"))
            os.makedirs(self.current_cwd, exist_ok=True)
            self.config["current_project"] = self.current_project
            self.config["current_cwd"] = self.current_cwd
            save_config(self.config)
            
            self.client.answer_callback_query(cb_id, text=f"✅ 已切換至專案：{self.current_project}")
            ls_preview = self.list_current_directory_files(cwd=self.current_cwd, proj_name=self.current_project)
            confirm_text = (
                f"🎯 **【已成功切換至專案與目錄：{self.current_project}】** 🌟\n"
                f"📍 **當前工作路徑**：`{self.current_cwd}`\n"
                "━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"{ls_preview}\n\n"
                "💡 *提示：接下來手機發送的所有提問、指令與檔案操作，都將直接作用於此專案！*"
            )
            _, kb = self.get_directory_browser_keyboard(self.current_cwd)
            self.client.edit_message_text(chat_id, msg_id, confirm_text, reply_markup=kb)
            logger.info(f"🎯 夥伴在手機端切換工作專案至：{self.current_cwd}")

        elif data.startswith("action_ls:"):
            rel_path = data.split("action_ls:")[1]
            target_abs = self.workspace_root if rel_path in [".", ""] else os.path.join(self.workspace_root, rel_path.replace("/", "\\"))
            self.client.answer_callback_query(cb_id, text="正在獲取檔案清單...")
            ls_text = self.list_current_directory_files(cwd=target_abs, proj_name=rel_path)
            _, kb = self.get_directory_browser_keyboard(target_abs)
            self.client.edit_message_text(chat_id, msg_id, ls_text, reply_markup=kb)

        elif data.startswith("set_target_dir:"):
            rel_path = data.split("set_target_dir:")[1]
            target_abs = self.workspace_root if rel_path in [".", ""] else os.path.join(self.workspace_root, rel_path.replace("/", "\\"))
            dest_name = f"📁 {rel_path}"
            self.target_upload_dir = target_abs
            self.target_upload_name = dest_name
            self.config["target_upload_dir"] = target_abs
            self.config["target_upload_name"] = dest_name
            save_config(self.config)
            
            self.client.answer_callback_query(cb_id, text=f"已設定存圖目標：{dest_name}")
            confirm_text = (
                f"🎯 **【已成功設定上傳目標：{dest_name}】** 🌟\n\n"
                f"📂 **目標目錄**：`{target_abs}`\n\n"
                "📥 **接下來你在手機傳送的所有照片**，都會直接自動存入此資料夾，並自動合流為 1 則匯總通知！✨"
            )
            self.client.send_message(chat_id, confirm_text, reply_markup=self.get_project_keyboard())

        elif data.startswith("set_target:"):
            target_key = data.split("set_target:")[1]
            if target_key == "illit":
                self.target_upload_dir = ILLIT_DIR
                self.target_upload_name = "🖼️ 圖片/illit"
            elif target_key == "desktop":
                self.target_upload_dir = DESKTOP_DIR
                self.target_upload_name = "🖥️ 電腦桌面 (Desktop)"
            elif target_key == "staging":
                self.target_upload_dir = STAGING_DIR
                self.target_upload_name = "📦 手機上傳臨時存放區"
                
            self.config["target_upload_dir"] = self.target_upload_dir
            self.config["target_upload_name"] = self.target_upload_name
            save_config(self.config)
            
            self.client.answer_callback_query(cb_id, text=f"已設定存圖目標：{self.target_upload_name}")
            confirm_text = (
                f"🎯 **【已成功設定上傳目標：{self.target_upload_name}】** 🌟\n\n"
                f"📂 **目標目錄**：`{self.target_upload_dir}`\n\n"
                "📥 **接下來你在手機傳送的所有照片**，都會直接自動存入此資料夾，並自動合流為 1 則匯總通知！✨"
            )
            self.client.send_message(chat_id, confirm_text, reply_markup=self.get_project_keyboard())

        elif data == "action:tree":
            self.client.answer_callback_query(cb_id, text="正在載入檔案總管樹狀圖...")
            tree_text, kb = self.get_directory_browser_keyboard(self.current_cwd)
            self.client.edit_message_text(chat_id, msg_id, tree_text, reply_markup=kb)

        elif data == "action:staging":
            self.client.answer_callback_query(cb_id, text="正在讀取臨時存放區...")
            staging_text = self.list_staging_files()
            self.client.send_message(chat_id, staging_text, reply_markup=self.get_project_keyboard())

        elif data == "action:ls":
            self.client.answer_callback_query(cb_id, text="正在獲取檔案清單...")
            ls_text = self.list_current_directory_files()
            self.client.send_message(chat_id, ls_text, reply_markup=self.get_project_keyboard())

        elif data == "action:pin":
            self.client.answer_callback_query(cb_id, text="正在傳送操作面板...")
            self.send_pin_guide(chat_id)

    # --------------------------------------------------------------------------
    # 🤖 雙層任務處理 (隨身管家 vs 電腦端 Gemini 3.7 重度編程委派)
    # --------------------------------------------------------------------------
    def is_heavy_coding_task(self, text: str) -> bool:
        """智慧判斷是否為重度代碼編程/APP開發任務"""
        heavy_keywords = [
            "寫程式", "寫代碼", "重構", "開發", "修改程式碼", "加功能", "修改代碼",
            "build apk", "編譯apk", "編譯 apk", "寫一個app", "寫一個 app", "設計app",
            "修復bug", "修bug", "改寫", "實作", "寫入檔案", "建立專案"
        ]
        t = text.lower()
        return any(k in t for k in heavy_keywords)

    def process_ai_question_async(self, chat_id: int, user_id: int, text: str, working_msg_id: Optional[int], is_retry: bool = False):
        # 登記活躍任務
        with self.task_lock:
            self.active_working_tasks[user_id] = {
                "initial_text": text,
                "supplements": [],
                "working_msg_id": working_msg_id,
                "start_time": time.time()
            }

        def _task():
            try:
                # 🌟 1. 優先檢測是否為切換工作目錄 / 專案指令
                switch_res = self.try_switch_working_directory(text)
                if switch_res:
                    if working_msg_id:
                        self.client.edit_message_text(chat_id, working_msg_id, switch_res, reply_markup=self.get_reply_action_keyboard())
                    else:
                        self.client.send_message(chat_id, switch_res, reply_markup=self.get_reply_action_keyboard())
                    MobileStorageManager.record_inbox(user_id, text, project_name=self.current_project, cwd=self.current_cwd, status="🟢 已切換工作專案與目錄", answer=switch_res)
                    MobileStorageManager.sync_to_ai_memory(f"切換專案與目錄至：{self.current_project}", self.current_project)
                    return

                # 🌟 2. 檢測是否為更改存圖目標指令
                target_res = self.try_set_target_directory(text)
                if target_res:
                    if working_msg_id:
                        self.client.edit_message_text(chat_id, working_msg_id, target_res, reply_markup=self.get_reply_action_keyboard())
                    else:
                        self.client.send_message(chat_id, target_res, reply_markup=self.get_reply_action_keyboard())
                    MobileStorageManager.record_inbox(user_id, text, project_name=self.current_project, cwd=self.current_cwd, status="🟢 已設定上傳目標", answer=target_res)
                    MobileStorageManager.sync_to_ai_memory(f"設定圖片目標目錄：{self.target_upload_name}", self.current_project)
                    return

                # 🌟 3. 檢測是否為後續整批檔案搬移指令
                action_result = self.try_autonomous_file_action(text)
                if action_result:
                    if working_msg_id:
                        self.client.edit_message_text(chat_id, working_msg_id, action_result, reply_markup=self.get_reply_action_keyboard())
                    else:
                        self.client.send_message(chat_id, action_result, reply_markup=self.get_reply_action_keyboard())
                    MobileStorageManager.record_inbox(user_id, text, project_name=self.current_project, cwd=self.current_cwd, status="🟢 已自動執行搬移完畢", answer=action_result)
                    MobileStorageManager.sync_to_ai_memory(f"自動執行檔案搬移：{text[:40]}", self.current_project)
                    return

                # 🌟 4. 判斷是否為「重度編程任務」：自動委派電腦端 Gemini 3.7 Flash 主腦！
                if self.is_heavy_coding_task(text):
                    logger.info(f"⚡ 識別為重度編程任務，自動委派至電腦端 Gemini 3.7 Flash: {text[:40]}...")
                    
                    with self.task_lock:
                        supps = list(self.active_working_tasks.get(user_id, {}).get("supplements", []))
                    
                    full_prompt = text
                    if supps:
                        full_prompt += "\n\n【夥伴追加的補充說明】：\n" + "\n".join([f"- {s}" for s in supps])

                    # 寫入收件匣，標記為等待電腦端 Gemini 3.7 執行
                    MobileStorageManager.record_inbox(
                        user_id,
                        full_prompt,
                        project_name=self.current_project,
                        cwd=self.current_cwd,
                        status="🟡 等待電腦端 Gemini 3.7 Flash 執行中...",
                        answer="任務已排入電腦端主腦佇列，編程完成後將自動回傳代碼報告與 APK！",
                        is_heavy_task=True
                    )
                    
                    delegate_msg = (
                        "📥 **【已接收重度編程任務！⚡】** 🌟\n"
                        "━━━━━━━━━━━━━━━━━━━━━\n"
                        f"🎯 **委派對象**：`💻 電腦端 Gemini 3.7 Flash 旗艦主腦`\n"
                        f"📁 **工作專案**：`{self.current_project}`\n"
                        f"💬 **任務指令**：「{full_prompt[:80]}」\n\n"
                        "⏳ **電腦端主腦已開始深度編程與處理...**\n"
                        "💡 *完成後會自動將代碼報告與最新編譯出的 .apk 秒傳回手機！* 🚀"
                    )
                    if working_msg_id:
                        self.client.edit_message_text(chat_id, working_msg_id, delegate_msg, reply_markup=self.get_reply_action_keyboard())
                    else:
                        self.client.send_message(chat_id, delegate_msg, reply_markup=self.get_reply_action_keyboard())
                    return

                # 🌟 5. 一般隨身管家問答 (Llama 3.2 Vision 核心秒回)
                logger.info(f"🤖 隨身管家正在為夥伴解答: {text[:40]}...")
                self.client.send_chat_action(chat_id, "typing")
                
                with self.task_lock:
                    supps = list(self.active_working_tasks.get(user_id, {}).get("supplements", []))
                
                full_prompt = text
                if supps:
                    full_prompt += "\n\n【夥伴在思考期間追加的補充說明】：\n" + "\n".join([f"- {s}" for s in supps])

                answer = MobileAIEngine.query_ai(
                    full_prompt,
                    self.current_project,
                    self.current_cwd,
                    self.target_upload_name,
                    self.target_upload_dir,
                    history=self.mobile_chat_history,
                    model=self.config.get("ai_model", "meta/llama-3.2-11b-vision-instruct")
                )
                
                self.mobile_chat_history.append({"role": "user", "content": full_prompt})
                self.mobile_chat_history.append({"role": "assistant", "content": answer})
                if len(self.mobile_chat_history) > 12:
                    self.mobile_chat_history = self.mobile_chat_history[-12:]

                header = (
                    f"📍 **【當前專案與目錄】**：`{self.current_project}`\n"
                    f"📂 `{self.current_cwd}`\n"
                    "━━━━━━━━━━━━━━━━━━━━━\n\n"
                )
                reply_text = f"**【📱 Mobile Agent 隨身解答】** 🌟\n\n{header}{answer}"
                
                if working_msg_id:
                    self.client.edit_message_text(chat_id, working_msg_id, reply_text, reply_markup=self.get_reply_action_keyboard())
                else:
                    self.client.send_message(chat_id, reply_text, reply_markup=self.get_reply_action_keyboard())
                
                MobileStorageManager.record_inbox(user_id, full_prompt, project_name=self.current_project, cwd=self.current_cwd, status="🟢 已解答完畢", answer=answer)
                summary_brief = full_prompt[:50].replace("\n", " ")
                MobileStorageManager.sync_to_ai_memory(f"手機提問與指令：{summary_brief}", self.current_project)
                logger.info(f"🎉 專屬 Mobile Agent 已成功將解答回傳給夥伴！")
            except Exception as e:
                logger.error(f"非同步處理異常: {e}", exc_info=True)
                err_text = f"⚠️ 處理過程遇到狀況：`{e}`\n\n💡 夥伴可以點擊下方【 🔄 重新生成 / 重試 】按鈕，我會立即為你重新執行！"
                if working_msg_id:
                    self.client.edit_message_text(chat_id, working_msg_id, err_text, reply_markup=self.get_reply_action_keyboard())
                else:
                    self.client.send_message(chat_id, err_text, reply_markup=self.get_reply_action_keyboard())
            finally:
                with self.task_lock:
                    self.active_working_tasks.pop(user_id, None)

        threading.Thread(target=_task, daemon=True).start()

    # --------------------------------------------------------------------------
    # 📩 訊息分發與指令解析器
    # --------------------------------------------------------------------------
    def handle_message(self, msg: Dict[str, Any]):
        try:
            user = msg.get("from", {})
            user_id = user.get("id", 0)
            username = user.get("username", "Unknown")
            chat_id = msg.get("chat", {}).get("id", user_id)
            caption = (msg.get("caption") or "").strip()
            text = (msg.get("text") or caption).strip()

            # 1. 首次配對與白名單驗證
            if self.allowed_user_id == 0:
                self.allowed_user_id = user_id
                self.config["allowed_user_id"] = user_id
                save_config(self.config)
                logger.info(f"🌟 已自動鎖定夥伴的專屬 Telegram ID: {user_id} (@{username})")
                self.client.set_bot_commands()
                self.send_pin_guide(chat_id)
                return

            if user_id != self.allowed_user_id:
                logger.warning(f"🚫 拒絕未授權的使用者存取: {user_id} (@{username})")
                return

            # 2. 處理語音訊息 (Voice Message)
            if "voice" in msg:
                logger.info(f"🎙️ 收到夥伴的語音訊息")
                self.handle_voice_message(chat_id, user_id, msg["voice"])
                return

            if "audio" in msg:
                logger.info(f"🎵 收到夥伴的音訊檔案")
                self.handle_voice_message(chat_id, user_id, msg["audio"])
                return

            # 3. 處理圖片上傳
            if "photo" in msg:
                logger.info(f"📷 收到夥伴上傳的圖片 (Caption: {caption})")
                self.handle_photo_message(chat_id, user_id, msg["photo"], caption)
                return

            # 4. 處理文件/APK 上傳
            if "document" in msg:
                logger.info(f"📁 收到夥伴上傳的檔案 (Doc: {msg.get('document', {}).get('file_name')})")
                self.handle_document_message(chat_id, user_id, msg["document"], caption)
                return

            if not text:
                return

            logger.info(f"📩 收到夥伴手機訊息: {text}")

            # 🌟 5. 判斷是否有正在進行中的 Working 任務（支援連續補充說明 Steering！）
            with self.task_lock:
                is_working = user_id in self.active_working_tasks

            if is_working and not text.startswith("/"):
                with self.task_lock:
                    if user_id in self.active_working_tasks:
                        self.active_working_tasks[user_id]["supplements"].append(text)
                        w_msg_id = self.active_working_tasks[user_id].get("working_msg_id")
                        if w_msg_id:
                            supp_count = len(self.active_working_tasks[user_id]["supplements"])
                            update_text = (
                                f"📥 **已收到夥伴指令！**\n"
                                f"🎯 **目標專案**：`{self.current_project}`\n\n"
                                f"⏳ **Working...** (已接收最新補充說明 💡「{text[:30]}」共 {supp_count} 則，持續運算中 🚀)"
                            )
                            self.client.edit_message_text(chat_id, w_msg_id, update_text)
                return

            # 記錄最新提問 (支援一鍵重新生成按鈕)
            if not text.startswith("/"):
                self.last_user_query[user_id] = text

            # 6. 手機專屬斜線指令路由
            if text.startswith("/start") or text.startswith("/help") or text.startswith("/pin"):
                self.client.set_bot_commands()
                self.send_pin_guide(chat_id)

            elif text.startswith("/staging") or text == "/temp":
                staging_text = self.list_staging_files()
                self.client.send_message(chat_id, staging_text, reply_markup=self.get_project_keyboard())

            elif text.startswith("/tree") or text.startswith("/explorer"):
                tree_text, kb = self.get_directory_browser_keyboard(self.current_cwd)
                self.client.send_message(chat_id, tree_text, reply_markup=kb)

            elif text.startswith("/cd"):
                parts = text.split(" ", 1)
                if len(parts) > 1 and parts[1].strip():
                    target_arg = parts[1].strip()
                    if target_arg in ["..", "../", "上一層"]:
                        parent_abs = os.path.dirname(self.current_cwd)
                        if self.workspace_root in parent_abs or parent_abs == self.workspace_root:
                            self.current_cwd = parent_abs
                            self.current_project = os.path.relpath(parent_abs, self.workspace_root).replace("\\", "/")
                            if self.current_project == ".":
                                self.current_project = "GitHub 根目錄"
                            self.config["current_project"] = self.current_project
                            self.config["current_cwd"] = self.current_cwd
                            save_config(self.config)
                            ls_preview = self.list_current_directory_files(cwd=self.current_cwd, proj_name=self.current_project)
                            _, kb = self.get_directory_browser_keyboard(self.current_cwd)
                            self.client.send_message(chat_id, f"🎯 **已返回上一層目錄：{self.current_project}**\n📍 `{self.current_cwd}`\n\n{ls_preview}", reply_markup=kb)
                        else:
                            self.client.send_message(chat_id, "⚠️ 已到達工作區最頂層目錄。")
                    elif target_arg in ["/", "\\", "~", "root"]:
                        self.current_cwd = self.workspace_root
                        self.current_project = "GitHub 根目錄"
                        self.config["current_project"] = self.current_project
                        self.config["current_cwd"] = self.current_cwd
                        save_config(self.config)
                        ls_preview = self.list_current_directory_files(cwd=self.current_cwd, proj_name=self.current_project)
                        _, kb = self.get_directory_browser_keyboard(self.current_cwd)
                        self.client.send_message(chat_id, f"🎯 **已切換至根目錄：{self.current_project}**\n📍 `{self.current_cwd}`\n\n{ls_preview}", reply_markup=kb)
                    else:
                        switch_res = self.try_switch_working_directory(target_arg)
                        if switch_res:
                            _, kb = self.get_directory_browser_keyboard(self.current_cwd)
                            self.client.send_message(chat_id, switch_res, reply_markup=kb)
                        else:
                            self.client.send_message(chat_id, f"⚠️ 找不到與 `{target_arg}` 相符的資料夾！你可以輸入 `/tree` 瀏覽完整樹狀圖。")
                else:
                    tree_text, kb = self.get_directory_browser_keyboard(self.current_cwd)
                    self.client.send_message(chat_id, tree_text, reply_markup=kb)

            elif text.startswith("/pwd") or text.startswith("/where"):
                rel_p = os.path.relpath(self.current_cwd, self.workspace_root).replace("\\", "/")
                pwd_text = (
                    "📍 **【當前工作位置與專案】** 🌟\n"
                    "━━━━━━━━━━━━━━━━━━━━━\n"
                    f"🎯 **專案名稱**：`{self.current_project}`\n"
                    f"📁 **實體路徑**：`{self.current_cwd}`\n"
                    f"🌐 **相對於根目錄**：`{rel_p}`\n"
                    f"🖼️ **圖片上傳目標**：`{self.target_upload_name}` (`{self.target_upload_dir}`)\n\n"
                    "💡 *如需切換，可直接點選下方按鈕或輸入 `/cd <目錄名>` / `/tree`*"
                )
                _, kb = self.get_directory_browser_keyboard(self.current_cwd)
                self.client.send_message(chat_id, pwd_text, reply_markup=kb)

            elif text.startswith("/projects") or text.startswith("/folder"):
                tree_text, kb = self.get_directory_browser_keyboard(self.current_cwd)
                self.client.send_message(chat_id, tree_text, reply_markup=kb)

            elif text.startswith("/ls") or text.startswith("/dir"):
                ls_text = self.list_current_directory_files(cwd=self.current_cwd, proj_name=self.current_project)
                self.client.send_message(chat_id, ls_text, reply_markup=self.get_project_keyboard())

            elif text.startswith("/cat ") or text.startswith("/view "):
                filename = text.split(" ", 1)[1].strip()
                content = self.read_file_content(filename, cwd=self.current_cwd)
                self.client.send_message(chat_id, content)

            elif text.startswith("/codewhale "):
                cmd_query = text[11:].strip()
                self.client.send_message(chat_id, f"🐳 正在調用本地 CodeWhale 執行：`{cmd_query}`...")
                output = self.execute_codewhale_sync(cmd_query)
                self.client.send_message(chat_id, output, reply_markup=self.get_reply_action_keyboard())
                MobileStorageManager.sync_to_ai_memory(f"CodeWhale 執行 `{cmd_query}` ({self.current_project})", self.current_project)

            elif text.startswith("/status"):
                status_text = (
                    "📱 **Antigravity 雙向 Agent 狀態報告** 🌟\n\n"
                    f"• **當前工作專案**：`{self.current_project}`\n"
                    f"• **實體工作目錄**：`{self.current_cwd}`\n"
                    f"• **圖片預設目標**：`{self.target_upload_name}`\n"
                    f"• **圖片實體路徑**：`{self.target_upload_dir}`\n"
                    f"• **臨時存放區**：`{STAGING_DIR}`\n"
                    "• **隨身管家大腦**：🟢 在線 (Llama-3.2 Vision 核心)\n"
                    "• **重度編程主腦**：🟢 電腦端 Gemini 3.7 Flash 聯動中\n"
                    "• **雙向成果推播**：🟢 AgentOutboxWatcher 即時監聽\n"
                    "• **連續溝通機制**：🟢 支援 Working 期間文字/語音補充說明\n"
                    "• **重試機制**：🟢 支援 [ 🔄 重新生成 / 重試 ] 一鍵重跑\n"
                    "• **工作狀態**：🟢 隨時在線待命 (Ready for Action)\n"
                    f"• **即時收件匣**：`Telegram_Agent_Bridge/📱_手機Telegram即時收件匣.md`\n"
                    f"• **歷史紀錄**：`Telegram_Agent_Bridge/📱_手機Telegram歷史紀錄.log`"
                )
                self.client.send_message(chat_id, status_text, reply_markup=self.get_reply_action_keyboard())

            elif text.startswith("/apk"):
                apk_path = os.path.join(self.workspace_root, "視覺動態效果手機待修", "mobile", "手機音效氣氛燈_A32專屬版.apk")
                if not os.path.exists(apk_path):
                    alt_apk = os.path.join(self.workspace_root, "FB_adblock.apk")
                    if os.path.exists(alt_apk):
                        apk_path = alt_apk
                self.client.send_message(chat_id, "📦 正在從電腦傳送最新 APK 安裝包...")
                success = self.client.send_document(chat_id, apk_path, "✨ 這是電腦端最新編譯的 APK！")
                if success:
                    self.client.send_message(chat_id, "🎉 傳送完成！在手機上點擊即可安裝！")

            elif text.startswith("/clear"):
                try:
                    self.mobile_chat_history.clear()
                    self.last_user_query.clear()
                    with open(INBOX_FILE, "w", encoding="utf-8") as f:
                        f.write("# 📱 手機 Telegram ⇄ 電腦螢幕即時收件匣\n\n> 🟢 閒置中，等待夥伴新指令 ✨\n")
                    self.client.send_message(chat_id, "🧹 已重置手機即時收件匣與對話記憶！")
                except Exception as e:
                    self.client.send_message(chat_id, f"❌ 重置失敗：{e}")

            elif text.startswith("/run "):
                cmd = text[5:].strip()
                self.client.send_message(chat_id, f"⚡ 正在於 `{self.current_project}` 執行：`{cmd}`...")
                output = self.execute_command_sync(cmd, cwd=self.current_cwd)
                self.client.send_message(chat_id, output, reply_markup=self.get_reply_action_keyboard())
                MobileStorageManager.sync_to_ai_memory(f"執行終端指令 `{cmd}` ({self.current_project})", self.current_project)

            else:
                # 🌟 自然語言提問或行動指令
                is_heavy = self.is_heavy_coding_task(text)
                MobileStorageManager.record_inbox(user_id, text, project_name=self.current_project, cwd=self.current_cwd, status="🟡 正在處理中...", is_heavy_task=is_heavy)
                
                target_desc = "💻 電腦端 Gemini 3.7 主腦" if is_heavy else "📱 隨身管家 Agent"
                clean_reply = (
                    f"📥 **已收到夥伴指令！**\n"
                    f"🎯 **處理模式**：`{target_desc}`\n"
                    f"📁 **目標專案**：`{self.current_project}`\n"
                    f"💬 「{text}」\n\n"
                    f"⏳ **Working...** (正在為你處理中 🚀)"
                )
                working_msg_id = self.client.send_message(chat_id, clean_reply)
                self.client.send_chat_action(chat_id, "typing")

                self.process_ai_question_async(chat_id, user_id, text, working_msg_id)

        except Exception as e:
            logger.error(f"處理訊息過程異常: {e}", exc_info=True)

    def run(self):
        if not self.token or self.token == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
            logger.error("❌ 請先在 bridge_config.json 中填入你的 Telegram Bot Token！")
            return

        ensure_single_instance(47890)

        logger.info("🚀 Antigravity Telegram ⇄ Gemini 3.7 雙向智能體橋接器已啟動！")
        logger.info(f"📱 授權使用者 ID: {self.allowed_user_id}")
        logger.info(f"📁 當前工作專案: {self.current_project} ({self.current_cwd})")
        logger.info(f"🖼️ 圖片預設目標: {self.target_upload_name} ({self.target_upload_dir})")

        try:
            self.client.set_bot_commands()
        except Exception as e:
            logger.warning(f"註冊選單失敗: {e}")

        # 啟動雙向成果監聽線程
        self.start_outbox_watcher_thread()

        offset = 0
        while self.running:
            try:
                updates = self.client.get_updates(offset=offset, timeout=20)
                for update in updates:
                    offset = update.get("update_id", 0) + 1
                    if "message" in update:
                        self.handle_message(update["message"])
                    elif "edited_message" in update:
                        self.handle_message(update["edited_message"])
                    elif "callback_query" in update:
                        self.handle_callback_query(update["callback_query"])
            except Exception as e:
                logger.error(f"輪詢更新異常: {e}")
                time.sleep(2)

if __name__ == "__main__":
    daemon = AntigravityBridgeDaemon()
    daemon.run()
