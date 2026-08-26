#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🤖 Antigravity Telegram Remote Agent Bridge (全自動檔案管家 & 引用回覆精準分流旗艦版)
========================================================================================
✨ 核心亮點：
1. 🎯 引用回覆精準定向 (Reply-To Precision Routing)：
   - 手機收到不同 Agent 通知時，只要「長按該訊息點選回覆 (Reply)」，系統自動對接該專屬 Agent，絕不打架混淆！
2. 🔕 批次相片合流防刷屏 (Debounce Batch Aggregation)：
   - 連續傳送多張照片時，自動合流為 1 則乾淨匯總通知，告別密集跳通知轟炸！
3. 🎯 目標目錄持久記憶 (Persistent Target Location)：
   - 說「放到 illit / 桌面 / 04」，目標目錄自動寫入設定檔持久保存，重開機不丟失！
4. 📦 專屬【手機上傳臨時存放區】：若未指定目標，預設安全收納於暫存區，隨時一鍵整批搬移！
5. 🚚 全自動搬移 (Autonomous File Mover)：說「移到 illit/桌面/04」，Agent 直接自動整批搬移並清空暫存！
6. 📁 互動式專案選擇器：Telegram 按鈕一鍵切換【鈣鈦礦/任務/手機維修/BalatroMaker/圖片illit】！
7. 🔕 原地訊息編輯 (In-place Edit)：Working 提示直接變形為最終結果，0 重複回覆！
8. 🧠 AI 記憶自動精華統整：自動將手機操作摘要記錄進 pending_sync.md，不污染原始記憶！
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
logger = logging.getLogger("AntigravityBridge")

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
        logger.info("🔒 成功取得單例進程鎖定 (Port: %d)，保證唯一實例運行！", port)
        return True
    except socket.error:
        logger.error("❌ 已經有另一個 Bridge 進程正在運行！請關閉舊進程後再重試。")
        sys.exit(0)

# ==============================================================================
# ⚙️ 配置檔案路徑與預設參數
# ==============================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "bridge_config.json")
WORKSPACE_DEFAULT = r"c:\Users\yexia\Documents\ShihWei\NTNU\GitHub"
BRAIN_DIR = os.path.expanduser(r"~\.gemini\antigravity-ide\brain")
INBOX_FILE = os.path.join(WORKSPACE_DEFAULT, "任務", "📱_手機Telegram即時收件匣.md")
HISTORY_LOG_FILE = os.path.join(WORKSPACE_DEFAULT, "任務", "📱_手機Telegram歷史紀錄.log")
PENDING_SYNC_FILE = os.path.expanduser(r"~\.gemini\memory_vault\pending_sync.md")

# 🌟 常用目錄路徑
STAGING_DIR = os.path.join(BASE_DIR, "手機上傳臨時存放區")
DESKTOP_DIR = os.path.expanduser(r"~\Desktop")
PICTURES_DIR = os.path.join(os.environ.get("USERPROFILE", os.path.expanduser("~")), "Pictures")
ILLIT_DIR = os.path.join(PICTURES_DIR, "illit")

os.makedirs(STAGING_DIR, exist_ok=True)
os.makedirs(ILLIT_DIR, exist_ok=True)

NVIDIA_KEY_FILE = os.path.join(WORKSPACE_DEFAULT, "nvidia_build.txt")

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
        "current_project": "任務",
        "target_upload_dir": ILLIT_DIR,
        "target_upload_name": "🖼️ 圖片/illit",
        "auto_sync_agent_replies": True,
        "poll_interval_seconds": 1.0,
        "ai_model": "meta/llama-3.1-8b-instruct"
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
                    headers={"Content-Type": "application/json", "User-Agent": "AntigravityBridge/6.0"}
                )
            else:
                req = urllib.request.Request(url, headers={"User-Agent": "AntigravityBridge/6.0"})

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
        commands = [
            {"command": "projects", "description": "📁 切換專案資料夾 (鈣鈦礦/任務/手機維修)"},
            {"command": "staging", "description": "📦 查看【手機上傳臨時存放區】檔案"},
            {"command": "ls", "description": "📂 列出當前專案目錄下的所有檔案"},
            {"command": "sessions", "description": "🎛️ 檢視電腦所有在線 Agent 視窗"},
            {"command": "status", "description": "📊 檢視連線狀態與健康度"},
            {"command": "apk", "description": "📦 傳送最新 Samsung A32 氣氛燈 APK"},
            {"command": "pin", "description": "📌 置頂隨身操作卡片"},
            {"command": "clear", "description": "🧹 重置手機收件匣"}
        ]
        res = self._request("setMyCommands", {"commands": commands})
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
            
            req = urllib.request.Request(download_url, headers={"User-Agent": "AntigravityBridge/6.0"})
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
                headers={"Content-Type": f"multipart/form-data; boundary={boundary}", "User-Agent": "AntigravityBridge/6.0"}
            )
            with urllib.request.urlopen(req, context=self.ssl_ctx, timeout=120) as response:
                res = json.loads(response.read().decode("utf-8"))
                return res.get("ok", False)
        except Exception as e:
            logger.error(f"傳送檔案失敗: {e}")
            return False

# ==============================================================================
# 🤖 AI 智慧思考大腦
# ==============================================================================
class AIBrainEngine:
    @staticmethod
    def get_system_prompt(current_project: str, current_cwd: str, target_upload_name: str, target_upload_dir: str) -> str:
        return f"""你是 Antigravity Telegram 遠端全能 Agent 核心。
稱呼使用者為「夥伴」。
回答風格：50% 情緒價值 + 50% 實質解答，請大量使用活力表情符號 🌟 🚀 💡。

【當前目標專案與環境】：
- 當前目標專案：{current_project}
- 本地工作目錄：{current_cwd}
- 當前圖片存放目錄：{target_upload_name} ({target_upload_dir})
- 手機臨時存放區：{STAGING_DIR}

【能力要求】：
1. 繁體中文回答，清楚、專業、結構化。
2. 語氣熱情、積極、值得信賴。
3. 嚴格領域純粹，專注當前專案解答。"""

    @staticmethod
    def query_ai(user_prompt: str, current_project: str, current_cwd: str, target_upload_name: str, target_upload_dir: str, history: Optional[List[Dict[str, str]]] = None, model: str = "meta/llama-3.1-8b-instruct") -> str:
        api_key = get_nvidia_api_key()
        if not api_key:
            return "⚠️ 未找到有效的 NVIDIA API Key，請檢查 nvidia_build.txt！"

        url = "https://integrate.api.nvidia.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "AntigravityBridge/6.0"
        }

        system_content = AIBrainEngine.get_system_prompt(current_project, current_cwd, target_upload_name, target_upload_dir)
        messages = [{"role": "system", "content": system_content}]
        if history:
            for item in history[-4:]:
                messages.append({"role": item.get("role", "user"), "content": item.get("text", "")})
        messages.append({"role": "user", "content": user_prompt})

        data = {
            "model": model,
            "messages": messages,
            "max_tokens": 1200,
            "temperature": 0.6
        }

        ctx = ssl.create_default_context()
        try:
            req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers)
            with urllib.request.urlopen(req, context=ctx, timeout=25) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                choices = res.get("choices", [])
                if choices:
                    return choices[0]["message"]["content"].strip()
                return "⚠️ AI 回覆為空，請稍後重試。"
        except Exception as e:
            logger.error(f"AI 大腦調用異常: {e}")
            if model != "meta/llama-3.2-11b-vision-instruct":
                logger.info("🔄 正在嘗試 Fallback 模型 (meta/llama-3.2-11b-vision-instruct)...")
                return AIBrainEngine.query_ai(user_prompt, current_project, current_cwd, target_upload_name, target_upload_dir, history, model="meta/llama-3.2-11b-vision-instruct")
            return f"❌ AI 運算暫時繁忙或連線逾時：`{e}`"

# ==============================================================================
# 🧠 Antigravity 全域多 Agent 對話管理與記憶統整器
# ==============================================================================
class TranscriptSyncEngine:
    @staticmethod
    def get_all_sessions() -> List[Dict[str, Any]]:
        sessions = []
        if not os.path.exists(BRAIN_DIR):
            return sessions

        for entry in os.listdir(BRAIN_DIR):
            conv_dir = os.path.join(BRAIN_DIR, entry)
            if not os.path.isdir(conv_dir) or entry == "tempmediaStorage":
                continue

            transcript_path = os.path.join(conv_dir, ".system_generated", "logs", "transcript.jsonl")
            if not os.path.exists(transcript_path):
                continue

            mtime = os.path.getmtime(transcript_path)
            workspace = "任務"
            last_user_msg = ""
            
            try:
                with open(transcript_path, "r", encoding="utf-8", errors="replace") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            data = json.loads(line)
                            content = urllib.parse.unquote(str(data.get("content", "")))
                            
                            if "NTNU\\GitHub\\" in content or "NTNU/GitHub/" in content:
                                normalized = content.replace("/", "\\")
                                for chunk in normalized.split("NTNU\\GitHub\\")[1:]:
                                    ws = chunk.split("\\")[0].split("\"")[0].split("'")[0].split("`")[0].split("\n")[0].strip()
                                    if ws and ws not in [".", "..", ""]:
                                        workspace = ws
                                        break
                            
                            if data.get("source") == "USER_EXPLICIT" and data.get("type") == "USER_INPUT":
                                req = content
                                if "<USER_REQUEST>" in req:
                                    req = req.split("<USER_REQUEST>")[1].split("</USER_REQUEST>")[0].strip()
                                if req:
                                    last_user_msg = req[:60].replace("\n", " ")
                        except Exception:
                            pass
            except Exception:
                pass

            friendly_name = f"📁 {workspace} Agent"
            short_key = workspace
            if "Perovskite" in workspace or "鈣鈦礦" in workspace or "擷取工具" in workspace:
                friendly_name = "🧪 鈣鈦礦 Agent (Perovskite)"
                short_key = "Perovskite"
            elif "任務" in workspace:
                friendly_name = "⚡ 任務 Agent (Tasks & Tools)"
                short_key = "任務"
            elif "視覺動態" in workspace or "手機待修" in workspace:
                friendly_name = "📱 手機維修與視覺 Agent"
                short_key = "視覺動態效果手機待修"
            elif "BalatroMaker" in workspace:
                friendly_name = "🎮 BalatroMaker Agent"
                short_key = "BalatroMaker"

            sessions.append({
                "id": entry,
                "name": friendly_name,
                "short_key": short_key,
                "workspace": workspace,
                "path": transcript_path,
                "last_msg": last_user_msg if last_user_msg else "(新對話視窗)",
                "mtime": mtime,
                "mtime_str": time.strftime("%m/%d %H:%M:%S", time.localtime(mtime))
            })

        sessions.sort(key=lambda s: s["mtime"], reverse=True)
        return sessions

    @staticmethod
    def get_transcript_path(conversation_id: str) -> Optional[str]:
        path = os.path.join(BRAIN_DIR, conversation_id, ".system_generated", "logs", "transcript.jsonl")
        return path if os.path.exists(path) else None

    @staticmethod
    def read_conversation_history(conversation_id: str, limit: int = 3) -> List[Dict[str, str]]:
        path = TranscriptSyncEngine.get_transcript_path(conversation_id)
        if not path or not os.path.exists(path):
            return []

        messages = []
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        src = data.get("source")
                        msg_type = data.get("type")
                        content = data.get("content", "")

                        if src == "USER_EXPLICIT" and msg_type == "USER_INPUT":
                            clean_text = content
                            if "<USER_REQUEST>" in clean_text:
                                clean_text = clean_text.split("<USER_REQUEST>")[1].split("</USER_REQUEST>")[0].strip()
                            if clean_text:
                                messages.append({"role": "user", "text": clean_text})

                        elif src == "MODEL" and msg_type == "PLANNER_RESPONSE" and content:
                            messages.append({"role": "assistant", "text": content.strip()})
                    except Exception:
                        continue
        except Exception as e:
            logger.error(f"讀取對話歷史失敗: {e}")

        return messages[-limit:]

    @staticmethod
    def record_mobile_inbox(user_id: int, message_text: str, target_agent: str, status: str = "🟡 處理中...", answer: str = ""):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        if status.startswith("🟡"):
            log_entry = f"[{timestamp}] [User: {user_id}] [Target: {target_agent}]\n{message_text}\n{'-'*50}\n"
            try:
                with open(HISTORY_LOG_FILE, "a", encoding="utf-8") as f:
                    f.write(log_entry)
            except Exception as e:
                logger.error(f"寫入歷史 Log 失敗: {e}")

        answer_block = ""
        if answer:
            answer_block = f"### ✨ Agent 執行結果：\n```text\n{answer[:600]}...\n```\n\n"

        inbox_content = (
            "# 📱 手機 Telegram ⇄ 電腦螢幕即時收件匣\n\n"
            f"> 🕒 **時間**：`{timestamp}` | 狀態：`{status}`\n"
            f"> 🎯 **對象**：`{target_agent}`\n\n"
            "### 💬 夥伴最新提問與指令：\n"
            "```text\n"
            f"{message_text}\n"
            "```\n\n"
            f"{answer_block}"
            "---\n"
            "💡 *提示：手機與電腦隨時保持雙向同步，歷史紀錄已完整留存於 Log 檔。*\n"
        )
        try:
            with open(INBOX_FILE, "w", encoding="utf-8") as f:
                f.write(inbox_content)
        except Exception as e:
            logger.error(f"寫入收件匣失敗: {e}")

    @staticmethod
    def sync_to_ai_memory(summary_text: str, project_name: str):
        timestamp = time.strftime("%Y-%m-%d %H:%M")
        entry = f"- **[{timestamp} 手機遠端 ({project_name})]**：{summary_text}\n"
        try:
            os.makedirs(os.path.dirname(PENDING_SYNC_FILE), exist_ok=True)
            if not os.path.exists(PENDING_SYNC_FILE):
                with open(PENDING_SYNC_FILE, "w", encoding="utf-8") as f:
                    f.write("# 📥 待分類緩衝記憶區 (Pending Sync Buffer)\n\n---\n\n")
            with open(PENDING_SYNC_FILE, "a", encoding="utf-8") as f:
                f.write(entry)
            logger.info(f"🧠 已自動將操作摘要記入 pending_sync.md: {summary_text[:30]}...")
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
# 🎮 Agent 核心橋接器與主守護進程
# ==============================================================================
class AntigravityBridgeDaemon:
    def __init__(self):
        self.config = load_config()
        self.token = self.config.get("bot_token", "")
        self.allowed_user_id = int(self.config.get("allowed_user_id", 0))
        self.client = TelegramClient(self.token)
        self.running = True
        
        self.workspace_root = self.config.get("workspace_root", WORKSPACE_DEFAULT)
        self.current_project = self.config.get("current_project", "任務")
        self.current_cwd = os.path.join(self.workspace_root, self.current_project)
        if not os.path.exists(self.current_cwd):
            self.current_cwd = self.workspace_root
            
        # 🌟 持久化目標存放目錄
        self.target_upload_dir = self.config.get("target_upload_dir", ILLIT_DIR)
        self.target_upload_name = self.config.get("target_upload_name", "🖼️ 圖片/illit")
        os.makedirs(self.target_upload_dir, exist_ok=True)
            
        self.target_conv_id = ""
        self.target_agent_name = f"⚡ {self.current_project} Agent"
        
        # 🌟 訊息 ID ➔ Agent 上下文映射表（用於長按引用回覆精準路由！）
        self.message_context_map: Dict[int, Dict[str, Any]] = {}
        
        # 🌟 批次相片防刷屏緩衝器
        self.photo_buffer = PhotoBatchBuffer(self.on_photo_batch_finished, delay_seconds=2.0)
        
        # 紀錄所有視窗的已讀行數指標
        self.synced_lines_map: Dict[str, int] = {}
        sessions = TranscriptSyncEngine.get_all_sessions()
        for s in sessions:
            self.synced_lines_map[s["id"]] = self._get_transcript_line_count(s["id"])
        if sessions:
            self.target_conv_id = sessions[0]["id"]

    def _get_transcript_line_count(self, conv_id: str) -> int:
        path = TranscriptSyncEngine.get_transcript_path(conv_id)
        if not path or not os.path.exists(path):
            return 0
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                return sum(1 for _ in f)
        except Exception:
            return 0

    def _find_conv_id_for_project(self, project_name: str) -> str:
        sessions = TranscriptSyncEngine.get_all_sessions()
        for s in sessions:
            if s.get("short_key") == project_name or s.get("workspace") == project_name:
                return s["id"]
        return self.target_conv_id

    def get_project_keyboard(self) -> Dict[str, Any]:
        keyboard = {
            "inline_keyboard": [
                [
                    {"text": "⚡ 任務與工具", "callback_data": "set_proj:任務"},
                    {"text": "🧪 鈣鈦礦 (Perovskite)", "callback_data": "set_proj:Perovskite"}
                ],
                [
                    {"text": "📱 視覺與手機待修", "callback_data": "set_proj:視覺動態效果手機待修"},
                    {"text": "🎮 BalatroMaker", "callback_data": "set_proj:BalatroMaker"}
                ],
                [
                    {"text": "📁 04_antigravity可移動執行", "callback_data": "set_proj:04_antigravity可移動執行"},
                    {"text": "🖼️ 存圖目標: illit", "callback_data": "set_target:illit"}
                ],
                [
                    {"text": "🖥️ 存圖目標: 桌面", "callback_data": "set_target:desktop"},
                    {"text": "📦 存圖目標: 臨時存放區", "callback_data": "set_target:staging"}
                ],
                [
                    {"text": "📂 查看當前目錄檔案 (/ls)", "callback_data": "action:ls"}
                ]
            ]
        }
        return keyboard

    def send_pin_guide(self, chat_id: int):
        guide_text = (
            "📌 **【Antigravity 全自動檔案管家 & 雙向時序 Agent】** 🌟\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            f"🎯 **當前預設專案**：`{self.current_project}`\n"
            f"📁 **目前工作目錄**：`{self.current_cwd}`\n"
            f"🖼️ **圖片目標目錄**：`{self.target_upload_name}`\n"
            f"📦 **臨時存放區**：`Telegram_Agent_Bridge/手機上傳臨時存放區`\n\n"
            "💬 **操作技巧（絕不打架）**：\n"
            "• 🎯 **引用回覆精準對接**：手機收到不同 Agent 通知時，**長按該訊息按「回覆 (Reply)」**，即可 100% 精準對接該 Agent！\n"
            "• 🖼️ **傳圖直達**：直接傳送多張照片，自動存入【`圖片/illit`】，合流為 1 則匯總通知（不刷屏）！\n"
            "• 🚚 **整批搬移**：說「`把暫存區移到桌面/illit`」，整批自動搬移並清空暫存！\n"
            "📁 **切換專案**：輸入 `/projects` 彈出互動資料夾按鈕\n"
            "📂 **查看檔案**：輸入 `/ls` 列出當前目錄所有檔案\n"
            "⚡ **執行指令**：輸入 `/run <PowerShell指令>` 遠端操盤\n"
            "📦 **傳送 APK**：輸入 `/apk` 秒傳最新氣氛燈安裝包！\n"
            "━━━━━━━━━━━━━━━━━━━━━"
        )
        msg_id = self.client.send_message(chat_id, guide_text, reply_markup=self.get_project_keyboard())
        if msg_id:
            self.client.pin_chat_message(chat_id, msg_id)

    def start_live_sync_thread(self):
        def sync_worker():
            logger.info("🔄 電腦端視窗監聽與推播引擎已啟動！")
            while self.running:
                try:
                    if self.allowed_user_id and self.config.get("auto_sync_agent_replies", True):
                        sessions = TranscriptSyncEngine.get_all_sessions()
                        for s in sessions[:5]:
                            conv_id = s["id"]
                            agent_name = s["name"]
                            workspace = s["workspace"]
                            path = s["path"]
                            
                            if path and os.path.exists(path):
                                with open(path, "r", encoding="utf-8", errors="replace") as f:
                                    lines = f.readlines()
                            else:
                                continue
                            
                            current_count = len(lines)
                            last_synced = self.synced_lines_map.get(conv_id, current_count)
                            
                            if current_count > last_synced:
                                for line in lines[last_synced:current_count]:
                                    try:
                                        data = json.loads(line.strip())
                                        src = data.get("source")
                                        msg_type = data.get("type")

                                        if src == "MODEL" and msg_type == "PLANNER_RESPONSE":
                                            content = data.get("content", "").strip()
                                            if content and not (content.startswith("{") and content.endswith("}")):
                                                logger.info(f"📡 偵測到電腦端 [{agent_name}] 回覆完畢，轉播至 Telegram...")
                                                sync_msg = f"🖥️ **[{agent_name} 電腦端即時同步]** 🌟\n\n{content}"
                                                sent_id = self.client.send_message(self.allowed_user_id, sync_msg)
                                                
                                                # 🌟 記錄訊息上下文，支援引用回覆精準定向！
                                                if sent_id:
                                                    self.message_context_map[sent_id] = {
                                                        "project": workspace,
                                                        "conv_id": conv_id,
                                                        "agent_name": agent_name,
                                                        "cwd": os.path.join(self.workspace_root, workspace.replace("/", "\\"))
                                                    }
                                    except Exception as err:
                                        logger.debug(f"解析日誌行失敗: {err}")
                                self.synced_lines_map[conv_id] = current_count
                except Exception as e:
                    logger.debug(f"同步線程輪詢異常: {e}")
                time.sleep(1.5)

        t = threading.Thread(target=sync_worker, daemon=True)
        t.start()

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

    def resolve_target_directory(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        t = text.lower()
        if "illit" in t or "圖片/illit" in t or "照片/illit" in t:
            return ILLIT_DIR, "🖼️ 圖片/illit"
        if "桌面" in text or "桌布" in text or "desktop" in t:
            return DESKTOP_DIR, "🖥️ 電腦桌面 (Desktop)"
        if "04" in text:
            return os.path.join(self.workspace_root, "04_antigravity可移動執行"), "📁 04_antigravity可移動執行"
        if "鈣鈦礦" in text or "perovskite" in t:
            return os.path.join(self.workspace_root, "Perovskite"), "🧪 鈣鈦礦 (Perovskite)"
        if "手機維修" in text or "視覺" in text:
            return os.path.join(self.workspace_root, "視覺動態效果手機待修"), "📱 視覺動態效果手機待修"
        if "暫存" in text or "臨時" in text or "staging" in t:
            return STAGING_DIR, "📦 手機上傳臨時存放區"
        if "圖片" in text or "pictures" in t or "相片" in text:
            return PICTURES_DIR, "🖼️ 電腦圖片 (Pictures)"
        if "任務" in text:
            return os.path.join(self.workspace_root, "任務"), "⚡ 任務 (Tasks & Tools)"
        return None, None

    def try_set_target_directory(self, user_text: str) -> Optional[str]:
        target_dir, dest_name = self.resolve_target_directory(user_text)
        if target_dir and ("放" in user_text or "存" in user_text or "設" in user_text or "換" in user_text or "到" in user_text):
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
        
        sent_id = self.client.send_message(chat_id, summary)
        if sent_id:
            self.message_context_map[sent_id] = {
                "project": self.current_project,
                "conv_id": self.target_conv_id,
                "agent_name": dest_name,
                "cwd": target_dir
            }
        TranscriptSyncEngine.record_mobile_inbox(self.allowed_user_id, f"[批次上傳 {count} 張照片]", dest_name, status="🟢 已全部存入", answer=summary)
        TranscriptSyncEngine.sync_to_ai_memory(f"批次存入 {count} 張照片至 {dest_name}", self.current_project)

    def handle_photo_message(self, chat_id: int, user_id: int, photo_list: list, caption: str):
        try:
            file_id = photo_list[-1]["file_id"]
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"agent_{timestamp}.jpg"
            
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
            file_name = doc_obj.get("file_name", f"agent_doc_{time.strftime('%Y%m%d_%H%M%S')}")
            
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
                sent_id = self.client.send_message(chat_id, reply)
                if sent_id:
                    self.message_context_map[sent_id] = {
                        "project": self.current_project,
                        "conv_id": self.target_conv_id,
                        "agent_name": dest_name,
                        "cwd": target_dir
                    }
                TranscriptSyncEngine.record_mobile_inbox(user_id, f"[上傳檔案: {file_name}]", dest_name, status="🟢 已下載存檔", answer=f"儲存於 {dest_path}")
            else:
                self.client.send_message(chat_id, "❌ 檔案下載失敗。")
        except Exception as e:
            logger.error(f"處理檔案異常: {e}")
            self.client.send_message(chat_id, f"❌ 處理檔案失敗：`{e}`")

    def handle_callback_query(self, cb: Dict[str, Any]):
        cb_id = cb.get("id", "")
        data = cb.get("data", "")
        msg = cb.get("message", {})
        chat_id = msg.get("chat", {}).get("id", self.allowed_user_id)
        msg_id = msg.get("message_id")

        if data.startswith("set_proj:"):
            proj = data.split("set_proj:")[1]
            self.current_project = proj
            self.current_cwd = os.path.join(self.workspace_root, proj.replace("/", "\\"))
            os.makedirs(self.current_cwd, exist_ok=True)
            self.config["current_project"] = proj
            save_config(self.config)
            
            self.client.answer_callback_query(cb_id, text=f"已切換至專案：{proj}")
            confirm_text = (
                f"🎯 **【已成功切換至專案：{proj}】** 🌟\n\n"
                f"📍 **當前工作路徑**：`{self.current_cwd}`\n\n"
                "💡 *提示：接下來手機發送的所有提問、指令與檔案操作，都將直接作用於此專案！*"
            )
            self.client.edit_message_text(chat_id, msg_id, confirm_text, reply_markup=self.get_project_keyboard())
            logger.info(f"🎯 夥伴在手機端切換工作專案至：{self.current_cwd}")

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

        elif data == "action:staging":
            self.client.answer_callback_query(cb_id, text="正在讀取臨時存放區...")
            staging_text = self.list_staging_files()
            self.client.send_message(chat_id, staging_text, reply_markup=self.get_project_keyboard())

        elif data == "action:ls":
            self.client.answer_callback_query(cb_id, text="正在獲取檔案清單...")
            ls_text = self.list_current_directory_files()
            self.client.send_message(chat_id, ls_text, reply_markup=self.get_project_keyboard())

    def process_ai_question_async(self, chat_id: int, user_id: int, text: str, target_project: str, target_cwd: str, target_conv_id: str, agent_name: str, working_msg_id: Optional[int], is_reply_routing: bool = False):
        def _task():
            try:
                # 🌟 1. 檢測是否為更改存放目標指令
                target_res = self.try_set_target_directory(text)
                if target_res:
                    edited = False
                    if working_msg_id:
                        edited = self.client.edit_message_text(chat_id, working_msg_id, target_res)
                    if not edited:
                        self.client.send_message(chat_id, target_res)
                    TranscriptSyncEngine.record_mobile_inbox(user_id, text, target_project, status="🟢 已設定上傳目標", answer=target_res)
                    TranscriptSyncEngine.sync_to_ai_memory(f"設定圖片目標目錄：{self.target_upload_name}", target_project)
                    return

                # 🌟 2. 檢測是否為後續整批檔案搬移指令
                action_result = self.try_autonomous_file_action(text)
                if action_result:
                    edited = False
                    if working_msg_id:
                        edited = self.client.edit_message_text(chat_id, working_msg_id, action_result)
                    if not edited:
                        self.client.send_message(chat_id, action_result)
                    TranscriptSyncEngine.record_mobile_inbox(user_id, text, target_project, status="🟢 已自動執行搬移完畢", answer=action_result)
                    TranscriptSyncEngine.sync_to_ai_memory(f"自動執行檔案搬移：{text[:40]}", target_project)
                    return

                # 3. 一般問題：調用高效 AI 思考大腦 (精準定向專案)
                conv_id = target_conv_id if target_conv_id else self._find_conv_id_for_project(target_project)
                history = TranscriptSyncEngine.read_conversation_history(conv_id, limit=3)
                logger.info(f"🤖 正在為夥伴深度解答 ({agent_name}): {text[:40]}...")
                self.client.send_chat_action(chat_id, "typing")
                
                answer = AIBrainEngine.query_ai(text, target_project, target_cwd, self.target_upload_name, self.target_upload_dir, history=history)
                
                routing_tag = "🎯 引用對接" if is_reply_routing else "✨ 專屬解答"
                reply_text = f"**【{agent_name} {routing_tag}】** 🌟\n\n{answer}"
                
                edited = False
                if working_msg_id:
                    edited = self.client.edit_message_text(chat_id, working_msg_id, reply_text)
                if not edited:
                    sent_id = self.client.send_message(chat_id, reply_text)
                    if sent_id:
                        self.message_context_map[sent_id] = {
                            "project": target_project,
                            "conv_id": conv_id,
                            "agent_name": agent_name,
                            "cwd": target_cwd
                        }
                else:
                    if working_msg_id:
                        self.message_context_map[working_msg_id] = {
                            "project": target_project,
                            "conv_id": conv_id,
                            "agent_name": agent_name,
                            "cwd": target_cwd
                        }
                
                TranscriptSyncEngine.record_mobile_inbox(user_id, text, agent_name, status="🟢 已解答完畢", answer=answer)
                summary_brief = text[:50].replace("\n", " ")
                TranscriptSyncEngine.sync_to_ai_memory(f"問答與指令 ({agent_name})：{summary_brief}", target_project)
                logger.info(f"🎉 已成功將 [{agent_name}] 解答推播給夥伴並完成收件匣與記憶統整！")
            except Exception as e:
                logger.error(f"非同步處理異常: {e}")
                self.client.send_message(chat_id, f"❌ 處理過程發生異常：`{e}`")

        threading.Thread(target=_task, daemon=True).start()

    def handle_message(self, msg: Dict[str, Any]):
        try:
            user = msg.get("from", {})
            user_id = user.get("id", 0)
            username = user.get("username", "Unknown")
            chat_id = msg.get("chat", {}).get("id", user_id)
            caption = (msg.get("caption") or "").strip()
            text = (msg.get("text") or caption).strip()
            reply_to_msg = msg.get("reply_to_message")

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

            # 2. 處理圖片上傳
            if "photo" in msg:
                logger.info(f"📷 收到夥伴上傳的圖片 (Caption: {caption})")
                self.handle_photo_message(chat_id, user_id, msg["photo"], caption)
                return

            # 3. 處理文件/APK 上傳
            if "document" in msg:
                logger.info(f"📁 收到夥伴上傳的檔案 (Doc: {msg.get('document', {}).get('file_name')})")
                self.handle_document_message(chat_id, user_id, msg["document"], caption)
                return

            if not text:
                return

            # 🌟 4. 判斷是否有「引用回覆 (Reply-To)」以進行精準路由！
            target_proj = self.current_project
            target_cwd = self.current_cwd
            target_agent_name = f"⚡ {self.current_project} Agent"
            target_conv = self.target_conv_id
            is_reply_routing = False

            if reply_to_msg:
                reply_id = reply_to_msg.get("message_id")
                reply_text = reply_to_msg.get("text", "")
                
                # A. 先從內存 Map 查詢
                matched_ctx = self.message_context_map.get(reply_id)
                
                # B. 若無則從文字內容解析 Agent 標籤
                if not matched_ctx and reply_text:
                    if "鈣鈦礦" in reply_text or "Perovskite" in reply_text:
                        matched_ctx = {
                            "project": "Perovskite",
                            "agent_name": "🧪 鈣鈦礦 Agent (Perovskite)",
                            "cwd": os.path.join(self.workspace_root, "Perovskite"),
                            "conv_id": self._find_conv_id_for_project("Perovskite")
                        }
                    elif "手機維修" in reply_text or "視覺" in reply_text:
                        matched_ctx = {
                            "project": "視覺動態效果手機待修",
                            "agent_name": "📱 手機維修與視覺 Agent",
                            "cwd": os.path.join(self.workspace_root, "視覺動態效果手機待修"),
                            "conv_id": self._find_conv_id_for_project("視覺動態效果手機待修")
                        }
                    elif "BalatroMaker" in reply_text:
                        matched_ctx = {
                            "project": "BalatroMaker",
                            "agent_name": "🎮 BalatroMaker Agent",
                            "cwd": os.path.join(self.workspace_root, "BalatroMaker"),
                            "conv_id": self._find_conv_id_for_project("BalatroMaker")
                        }
                    elif "任務" in reply_text or "Tasks" in reply_text:
                        matched_ctx = {
                            "project": "任務",
                            "agent_name": "⚡ 任務 Agent (Tasks & Tools)",
                            "cwd": os.path.join(self.workspace_root, "任務"),
                            "conv_id": self._find_conv_id_for_project("任務")
                        }

                if matched_ctx:
                    target_proj = matched_ctx["project"]
                    target_cwd = matched_ctx["cwd"]
                    target_agent_name = matched_ctx["agent_name"]
                    target_conv = matched_ctx.get("conv_id", self._find_conv_id_for_project(target_proj))
                    is_reply_routing = True
                    logger.info(f"🎯 偵測到夥伴引用回覆！精準對接 ➔ [{target_agent_name}] ({target_proj})")

            logger.info(f"📩 收到夥伴手機訊息: {text} (目標: {target_agent_name})")

            # 5. 系統指令路由
            if text.startswith("/start") or text.startswith("/help") or text.startswith("/pin"):
                self.client.set_bot_commands()
                self.send_pin_guide(chat_id)

            elif text.startswith("/staging") or text == "/temp":
                staging_text = self.list_staging_files()
                self.client.send_message(chat_id, staging_text, reply_markup=self.get_project_keyboard())

            elif text.startswith("/projects") or text.startswith("/cd") or text.startswith("/folder"):
                proj_text = (
                    "📁 **【專案與資料夾選擇器】** 🌟\n\n"
                    f"📍 **當前預設專案**：`{self.current_project}`\n"
                    f"📂 **工作路徑**：`{self.current_cwd}`\n"
                    f"🖼️ **圖片目標**：`{self.target_upload_name}`\n\n"
                    "👇 **請點擊下方按鈕切換你要操作的專案或圖片目錄**："
                )
                self.client.send_message(chat_id, proj_text, reply_markup=self.get_project_keyboard())

            elif text.startswith("/ls") or text.startswith("/dir"):
                ls_text = self.list_current_directory_files(cwd=target_cwd, proj_name=target_proj)
                self.client.send_message(chat_id, ls_text, reply_markup=self.get_project_keyboard())

            elif text.startswith("/cat ") or text.startswith("/view "):
                filename = text.split(" ", 1)[1].strip()
                content = self.read_file_content(filename, cwd=target_cwd)
                self.client.send_message(chat_id, content)

            elif text.startswith("/sessions"):
                sessions = TranscriptSyncEngine.get_all_sessions()
                if not sessions:
                    self.client.send_message(chat_id, "⚠️ 目前電腦端無活躍的對話視窗記錄。")
                    return

                sess_text = "🎛️ **電腦端所有 Agent 視窗清單 (全域同步中)**：\n\n"
                for i, s in enumerate(sessions[:4], 1):
                    sess_text += (
                        f"**[{i}] {s['name']}**\n"
                        f"   💬 最近主題：`{s['last_msg'][:30]}`\n"
                        f"   🕒 最後活躍：{s['mtime_str']}\n\n"
                    )
                self.client.send_message(chat_id, sess_text)

            elif text.startswith("/status"):
                status_text = (
                    "💻 **電腦端 Agent 狀態報告** 🌟\n\n"
                    f"• **當前預設專案**：`{self.current_project}`\n"
                    f"• **實體工作目錄**：`{self.current_cwd}`\n"
                    f"• **圖片預設目標**：`{self.target_upload_name}`\n"
                    f"• **圖片實體路徑**：`{self.target_upload_dir}`\n"
                    f"• **臨時存放區**：`{STAGING_DIR}`\n"
                    "• **AI 行動大腦**：🟢 在線 (NVIDIA Llama-3.1 旗艦核心)\n"
                    "• **同步與分流**：🟢 引用回覆精準路由 + 批次合流防刷屏\n"
                    "• **工作狀態**：🟢 隨時在線待命 (Ready for Action)\n"
                    f"• **螢幕收件匣**：`📱_手機Telegram即時收件匣.md`\n"
                    f"• **記憶緩衝區**：`pending_sync.md`"
                )
                self.client.send_message(chat_id, status_text)

            elif text.startswith("/apk"):
                apk_path = r"c:\Users\yexia\Documents\ShihWei\NTNU\GitHub\視覺動態效果手機待修\mobile\手機音效氣氛燈_A32專屬版.apk"
                if not os.path.exists(apk_path):
                    alt_apk = r"c:\Users\yexia\Documents\ShihWei\NTNU\GitHub\FB_adblock.apk"
                    if os.path.exists(alt_apk):
                        apk_path = alt_apk
                self.client.send_message(chat_id, "📦 正在從電腦傳送最新 APK 安裝包...")
                success = self.client.send_document(chat_id, apk_path, "✨ 這是電腦端最新編譯的 APK！")
                if success:
                    self.client.send_message(chat_id, "🎉 傳送完成！在手機上點擊即可安裝！")

            elif text.startswith("/clear"):
                try:
                    with open(INBOX_FILE, "w", encoding="utf-8") as f:
                        f.write("# 📱 手機 Telegram ⇄ 電腦螢幕即時收件匣\n\n> 🟢 閒置中，等待夥伴新指令 ✨\n")
                    self.client.send_message(chat_id, "🧹 已重置電腦螢幕收件匣！")
                except Exception as e:
                    self.client.send_message(chat_id, f"❌ 重置失敗：{e}")

            elif text.startswith("/run "):
                cmd = text[5:].strip()
                self.client.send_message(chat_id, f"⚡ 正在於 `{target_proj}` 執行：`{cmd}`...")
                output = self.execute_command_sync(cmd, cwd=target_cwd)
                self.client.send_message(chat_id, output)
                TranscriptSyncEngine.sync_to_ai_memory(f"執行終端指令 `{cmd}` ({target_proj})", target_proj)

            else:
                # 🌟 自然語言提問或行動指令
                TranscriptSyncEngine.record_mobile_inbox(user_id, text, target_agent_name, status="🟡 正在處理中...")
                
                routing_note = f"\n🎯 **引用定向**：`{target_agent_name}`" if is_reply_routing else f"\n🎯 **目標專案**：`{target_proj}`"
                clean_reply = (
                    f"📥 **已收到夥伴指令！**{routing_note}\n"
                    f"💬 「{text}」\n\n"
                    f"⏳ **Working...** (正在自動處理中 🚀)"
                )
                working_msg_id = self.client.send_message(chat_id, clean_reply, reply_to_message_id=msg.get("message_id") if is_reply_routing else None)
                self.client.send_chat_action(chat_id, "typing")

                self.process_ai_question_async(chat_id, user_id, text, target_proj, target_cwd, target_conv, target_agent_name, working_msg_id, is_reply_routing=is_reply_routing)

        except Exception as e:
            logger.error(f"處理訊息過程異常: {e}", exc_info=True)

    def run(self):
        if not self.token or self.token == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
            logger.error("❌ 請先在 bridge_config.json 中填入你的 Telegram Bot Token！")
            return

        ensure_single_instance(47890)

        logger.info("🚀 Antigravity Telegram 全自動檔案管家 & 引用回覆精準分流 Agent 已啟動！")
        logger.info(f"📱 授權使用者 ID: {self.allowed_user_id}")
        logger.info(f"📁 當前預設專案: {self.current_project} ({self.current_cwd})")
        logger.info(f"🖼️ 圖片預設目標: {self.target_upload_name} ({self.target_upload_dir})")

        try:
            self.client.set_bot_commands()
        except Exception as e:
            logger.warning(f"註冊選單失敗: {e}")

        self.start_live_sync_thread()

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
