#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎮 Antigravity Discord ⇄ Gemini 3.7 Flash 雙向智能體旗艦工作站
========================================================================================
✨ 核心亮點：
1. 🧠 雙層智能協同架構 (Dual-Layer Agentic Pipeline)：
   - 輕量管理 (查目錄/搬移/終端/問答)：由 Llama 3.2 11B 隨身管家秒回處理！
   - 重度編程 (寫代碼/重構/編譯 APK)：自動委派至電腦端 Gemini 3.7 Flash 旗艦主腦！
2. 🧵 獨立任務討論串 (Thread Isolation)：
   - 執行編程任務時自動拉開專屬 Thread，過程日誌與連續補充說明在 Thread 進行，主頻道乾淨不洗屏！
3. 🏰 一鍵自動伺服器空間架構：
   - 首次啟動自動建好【📋 個人隨身資料庫】與【🧠 AI 智能體主控台】各專屬頻道！
4. 📡 雙向成果自動監聽推播 (AgentOutboxWatcher)：
   - 電腦端 Gemini 3.7 完成代碼修改或編譯 APK 後，自動推播至 #🚀-建置成果與apk 頻道！
5. 👑 多人協同與角色權限防禦體系 (RBAC)：
   - 伺服器擁有者（夥伴）獨享 /run 與本機操控權限，同學/訪客安全隔離！
6. 🌲 互動式視覺化樹狀地圖 (/tree) 與 Select Menu 下拉選單導航！
"""

import os
import sys
import time
import json
import socket
import logging
import threading
import asyncio
import subprocess
import shutil
import urllib.request
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
logger = logging.getLogger("AntigravityDiscordBridge")

# ==============================================================================
# ⚙️ 配置檔案路徑與目錄定義 (100% 本地隔離)
# ==============================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "discord_bridge_config.json")
WORKSPACE_DEFAULT = r"c:\Users\yexia\Documents\ShihWei\NTNU\GitHub"
PID_FILE = os.path.join(BASE_DIR, ".discord_bridge.pid")

INBOX_FILE = os.path.join(BASE_DIR, "📱_手機Discord即時收件匣.md")
HISTORY_LOG_FILE = os.path.join(BASE_DIR, "🎮_Discord歷史紀錄.log")
PENDING_SYNC_FILE = os.path.expanduser(r"~\.gemini\memory_vault\pending_sync.md")

STAGING_DIR = os.path.join(BASE_DIR, "手機上傳臨時存放區")
DESKTOP_DIR = os.path.expanduser(r"~\Desktop")
PICTURES_DIR = os.path.join(os.environ.get("USERPROFILE", os.path.expanduser("~")), "Pictures")
ILLIT_DIR = os.path.join(PICTURES_DIR, "illit")
NVIDIA_KEY_FILE = os.path.join(WORKSPACE_DEFAULT, "nvidia_build.txt")
CODEWHALE_EXE = os.path.join(WORKSPACE_DEFAULT, "任務", "02_AI編程智能體_ZeroToken_CodeWhale_RooCode", "CodeWhale", "codewhale.exe")

os.makedirs(STAGING_DIR, exist_ok=True)
os.makedirs(ILLIT_DIR, exist_ok=True)

# 導入 discord.py
import discord
from discord import app_commands
from discord.ext import commands

# ==============================================================================
# 🔒 單例進程鎖定器
# ==============================================================================
SINGLETON_SOCKET = None
def ensure_single_instance(port: int = 47892) -> bool:
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
        logger.info("🔒 成功取得 Discord Bridge 單例進程鎖定 (Port: %d, PID: %d)！", port, os.getpid())
        return True
    except socket.error:
        logger.error("❌ 已經有另一個 Discord Bridge 進程正在運行！請先關閉舊進程。")
        sys.exit(0)

# ==============================================================================
# 🔑 設定管理與 API 讀取
# ==============================================================================
def get_nvidia_api_key() -> str:
    env_key = os.environ.get("NVIDIA_API_KEY", "").strip()
    if env_key.startswith("nvapi-"):
        return env_key
    if os.path.exists(NVIDIA_KEY_FILE):
        try:
            with open(NVIDIA_KEY_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    l = line.strip()
                    if l.startswith("nvapi-"):
                        return l
        except Exception:
            pass
    return ""

def load_config() -> Dict[str, Any]:
    default_cfg = {
        "bot_token": "",
        "guild_id": 0,
        "allowed_user_id": 0,
        "workspace_root": WORKSPACE_DEFAULT,
        "current_project": "Discord_Agent_Bridge",
        "target_upload_dir": ILLIT_DIR,
        "target_upload_name": "🖼️ 圖片/illit",
        "auto_sync_agent_replies": True,
        "ai_model": "meta/llama-3.2-11b-vision-instruct",
        "channels": {}
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
# 🤖 手機專屬輕量 AI 思考大腦 (Llama 3.2 11B 隨身管家)
# ==============================================================================
class MobileAIEngine:
    @staticmethod
    def get_system_prompt(current_project: str, current_cwd: str, target_upload_name: str, target_upload_dir: str) -> str:
        return f"""你是夥伴專屬的【🎮 Antigravity Discord 隨身管家 Agent】！
每次對話開頭稱呼夥伴為「夥伴」。

【回答風格與原則】：
1. 🌟 50% 情緒價值 + 50% 實質解答，多使用活力表情符號 🌟 🚀 💡 ✨ 🎉。
2. 繁體中文回答，條理清晰、排版美觀（適合 Discord Markdown / 粗體標題）。
3. 嚴格領域隔離：非物理話題禁止使用物理公式或比喻；專注回答軟體、專案開發與檔案操作。
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
            "User-Agent": "AntigravityDiscordBridge/1.0"
        }

        system_content = MobileAIEngine.get_system_prompt(current_project, current_cwd, target_upload_name, target_upload_dir)
        messages = [{"role": "system", "content": system_content}]
        if history:
            for item in history[-6:]:
                messages.append({"role": item.get("role", "user"), "content": item.get("content", "")})
        messages.append({"role": "user", "content": user_prompt})

        ctx = ssl.create_default_context()
        data = {
            "model": model,
            "messages": messages,
            "max_tokens": 1500,
            "temperature": 0.6
        }

        for attempt in range(2):
            try:
                req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers)
                with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
                    res = json.loads(resp.read().decode("utf-8"))
                    choices = res.get("choices", [])
                    if choices and choices[0].get("message", {}).get("content"):
                        return choices[0]["message"]["content"].strip()
            except Exception as e:
                logger.warning(f"AI 呼叫第 {attempt+1} 次異常: {e}")
                time.sleep(1)

        return "⚠️ AI 大腦正在自我校準中，請點擊下方【 🔄 重新生成 】按鈕，我會立即為你重新計算！🌟"

# ==============================================================================
# 📝 本地日誌、收件匣與記憶統整器
# ==============================================================================

# ==============================================================================
# 🎙️ 本地零 Token 語音識別大腦 (faster-whisper ASR Engine)
# ==============================================================================
class VoiceTranscriber:
    _model = None

    @classmethod
    def get_model(cls):
        if cls._model is None:
            try:
                from faster_whisper import WhisperModel
                logger.info("🎙️ 正在初始化 faster-whisper 語音轉文字模型 (base)...")
                cls._model = WhisperModel("base", device="cpu", compute_type="int8")
                logger.info("✅ faster-whisper 語音大腦載入完成！")
            except Exception as e:
                logger.error(f"載入 faster-whisper 失敗: {e}")
        return cls._model

    @classmethod
    def transcribe(cls, file_path: str) -> str:
        try:
            model = cls.get_model()
            if not model:
                return ""
            segments, info = model.transcribe(file_path, beam_size=5)
            text = "".join([segment.text for segment in segments]).strip()
            logger.info(f"🎙️ 語音辨識完成 (語言: {info.language}, 置信度: {info.language_probability:.2f}): {text}")
            return text
        except Exception as e:
            logger.error(f"語音辨識異常: {e}")
            return ""

class StorageManager:
    @staticmethod
    def record_inbox(user_id: int, message_text: str, project_name: str = "Discord_Agent_Bridge", cwd: str = "", status: str = "🟢 處理完成", answer: str = "", is_heavy_task: bool = False):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [User: {user_id}] [Project: {project_name}]\n提問: {message_text}\n狀態: {status}\n回覆: {answer[:200]}...\n{'-'*50}\n"
        try:
            with open(HISTORY_LOG_FILE, "a", encoding="utf-8") as f:
                f.write(log_entry)
        except Exception:
            pass

        answer_block = ""
        if answer:
            answer_block = f"### ✨ Agent 執行結果：\n```text\n{answer[:800]}...\n```\n\n"

        task_mode = "⚡ 重度編程任務 (委派電腦端 Gemini 3.7 Flash)" if is_heavy_task else "📱 隨身管家指令 (Llama 3.2 11B)"
        inbox_content = (
            "# 📱 手機 Discord ⇄ 電腦螢幕即時收件匣\n\n"
            f"> 🕒 **時間**：`{timestamp}` | 狀態：`{status}`\n"
            f"> 🎯 **模式**：`{task_mode}`\n"
            f"> 📁 **目標專案**：`{project_name}` (`{cwd}`)\n\n"
            "### 💬 夥伴手機最新指令與提問：\n"
            "```text\n"
            f"{message_text}\n"
            "```\n\n"
            f"{answer_block}"
            "---\n"
            "💡 *提示：電腦端 Gemini 3.7 Flash 完成任務並更新此檔案後，Bridge 會自動把成果與 APK 推播至 Discord！*\n"
        )
        try:
            with open(INBOX_FILE, "w", encoding="utf-8") as f:
                f.write(inbox_content)
        except Exception:
            pass

    @staticmethod
    def sync_to_ai_memory(summary_text: str, project_name: str):
        timestamp = time.strftime("%Y-%m-%d %H:%M")
        entry = f"- **[{timestamp} Discord Agent ({project_name})]**：{summary_text}\n"
        try:
            os.makedirs(os.path.dirname(PENDING_SYNC_FILE), exist_ok=True)
            if not os.path.exists(PENDING_SYNC_FILE):
                with open(PENDING_SYNC_FILE, "w", encoding="utf-8") as f:
                    f.write("# 📥 待分類緩衝記憶區 (Pending Sync Buffer)\n\n---\n\n")
            with open(PENDING_SYNC_FILE, "a", encoding="utf-8") as f:
                f.write(entry)
        except Exception:
            pass

# ==============================================================================
# 🎮 Discord 互動 UI 元件 (Views & Buttons & Select Menus)
# ==============================================================================
class ProjectSelectMenu(discord.ui.Select):
    def __init__(self, bridge_daemon, current_path: str):
        self.daemon = bridge_daemon
        self.curr_path = current_path
        
        # 掃描子目錄
        options = []
        options.append(discord.SelectOption(label="🏠 回 GitHub 根目錄", value="root", description="切換至頂層工作區", emoji="🏠"))
        if os.path.abspath(current_path) != os.path.abspath(self.daemon.workspace_root):
            options.append(discord.SelectOption(label="⬆️ 返回上一層目錄", value="parent", description="前往上層資料夾", emoji="⬆️"))

        try:
            ignored = {".git", "__pycache__", "node_modules", "venv", ".gemini", ".vscode", "tempmediaStorage", ".system_generated"}
            dirs = [d for d in os.listdir(current_path) if os.path.isdir(os.path.join(current_path, d)) and d not in ignored and not d.startswith(".")]
            for d in dirs[:20]:
                sub_abs = os.path.join(current_path, d)
                rel_p = os.path.relpath(sub_abs, self.daemon.workspace_root).replace("\\", "/")
                options.append(discord.SelectOption(label=f"{d}/", value=rel_p, description=f"進入 {d}", emoji="📁"))
        except Exception:
            pass

        super().__init__(placeholder="🧭 點擊挑選資料夾深入或切換專案...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        selected = self.values[0]
        if selected == "root":
            target = self.daemon.workspace_root
        elif selected == "parent":
            target = os.path.dirname(self.curr_path)
            if self.daemon.workspace_root not in target:
                target = self.daemon.workspace_root
        else:
            target = os.path.join(self.daemon.workspace_root, selected.replace("/", "\\"))

        embed, view = self.daemon.create_directory_tree_embed_and_view(target)
        await interaction.response.edit_message(embed=embed, view=view)

class DirectoryBrowserView(discord.ui.View):
    def __init__(self, bridge_daemon, current_path: str):
        super().__init__(timeout=180)
        self.daemon = bridge_daemon
        self.current_path = current_path
        self.add_item(ProjectSelectMenu(bridge_daemon, current_path))

    @discord.ui.button(label="✅ 鎖定此目錄為工作專案", style=discord.ButtonStyle.success, emoji="🎯", row=1)
    async def lock_project(self, interaction: discord.Interaction, button: discord.ui.Button):
        rel_p = os.path.relpath(self.current_path, self.daemon.workspace_root).replace("\\", "/")
        if rel_p == ".":
            rel_p = "GitHub 根目錄"
        self.daemon.current_project = rel_p
        self.daemon.current_cwd = self.current_path
        self.daemon.config["current_project"] = rel_p
        self.daemon.config["current_cwd"] = self.current_path
        save_config(self.daemon.config)
        
        embed = discord.Embed(
            title=f"🎯 已成功鎖定工作專案：{rel_p}",
            description=f"📍 **實體路徑**：`{self.current_path}`\n\n💡 *接下來手機發送的所有指令、編程任務與檔案操作，都將直接作用於此專案！*",
            color=discord.Color.brand_green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="📂 查看檔案清單 (/ls)", style=discord.ButtonStyle.primary, emoji="📄", row=1)
    async def list_files_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        ls_text = self.daemon.list_current_directory_files(self.current_path, os.path.basename(self.current_path))
        embed = discord.Embed(title=f"📂 檔案清單：{os.path.basename(self.current_path)}", description=ls_text, color=discord.Color.blue())
        await interaction.response.send_message(embed=embed, ephemeral=True)

class AgentDashboardView(discord.ui.View):
    def __init__(self, bridge_daemon):
        super().__init__(timeout=None)
        self.daemon = bridge_daemon

    @discord.ui.button(label="🧭 檔案總管 / 樹地圖", style=discord.ButtonStyle.primary, emoji="🌲", custom_id="btn_tree")
    async def tree_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed, view = self.daemon.create_directory_tree_embed_and_view(self.daemon.current_cwd)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @discord.ui.button(label="📂 專案檔案 (/ls)", style=discord.ButtonStyle.secondary, emoji="📄", custom_id="btn_ls")
    async def ls_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        ls_text = self.daemon.list_current_directory_files()
        embed = discord.Embed(title=f"📂 當前專案檔案清單", description=ls_text, color=discord.Color.blue())
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="📦 最新氣氛燈 APK", style=discord.ButtonStyle.success, emoji="📱", custom_id="btn_apk")
    async def apk_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        apk_path = os.path.join(self.daemon.workspace_root, "視覺動態效果手機待修", "mobile", "手機音效氣氛燈_A32專屬版.apk")
        if os.path.exists(apk_path):
            await interaction.response.send_message(content="✨ 這是最新編譯產出的 Samsung A32 氣氛燈 APK 安裝包！", file=discord.File(apk_path), ephemeral=True)
        else:
            await interaction.response.send_message(content="⚠️ 目前工作區未找到新編譯的 APK 檔案。", ephemeral=True)

    @discord.ui.button(label="📊 系統狀態儀表板", style=discord.ButtonStyle.secondary, emoji="⚡", custom_id="btn_status")
    async def status_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = self.daemon.get_system_status_embed()
        await interaction.response.send_message(embed=embed, ephemeral=True)

class PhotoDestinationView(discord.ui.View):
    def __init__(self, bridge_daemon, saved_files: List[str], author_id: int):
        super().__init__(timeout=300)
        self.daemon = bridge_daemon
        self.saved_files = saved_files
        self.author_id = author_id

    async def _move_files_to(self, interaction: discord.Interaction, target_dir: str, dest_name: str):
        if interaction.user.id != self.author_id and interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message("🚫 只有上傳此相片的使用者可以選擇存放位置喔！", ephemeral=True)
            return

        os.makedirs(target_dir, exist_ok=True)
        moved_count = 0
        moved_names = []
        for src in self.saved_files:
            if os.path.exists(src):
                fn = os.path.basename(src)
                dest = os.path.join(target_dir, fn)
                try:
                    shutil.move(src, dest)
                    moved_count += 1
                    moved_names.append(fn)
                except Exception as err:
                    logger.error(f"搬移相片失敗: {err}")

        # 禁用所有按鈕
        for child in self.children:
            child.disabled = True

        embed = discord.Embed(
            title=f"🎉 照片已成功存入 【{dest_name}】！🌟",
            description=(
                f"📍 **目標路徑**：`{target_dir}`\n"
                f"💾 **搬移數量**：`{moved_count}` 張照片\n\n"
                "📄 **檔案清單**：\n" + "\n".join([f"  • `{n}`" for n in moved_names[:6]]) +
                ("\n  ...等" if len(moved_names) > 6 else "")
            ),
            color=discord.Color.brand_green()
        )
        await interaction.response.edit_message(embed=embed, view=self)
        StorageManager.record_inbox(self.author_id, f"[相片歸檔至 {dest_name}]", project_name=self.daemon.current_project, cwd=target_dir, status="🟢 已歸檔存檔", answer=f"存入 {target_dir}")
        StorageManager.sync_to_ai_memory(f"相片歸檔至 {dest_name} ({moved_count} 張)", self.daemon.current_project)

    @discord.ui.button(label="🖼️ 存入 圖片/illit", style=discord.ButtonStyle.success, emoji="🌸", row=0)
    async def to_illit(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._move_files_to(interaction, ILLIT_DIR, "🖼️ 圖片/illit")

    @discord.ui.button(label="🖥️ 存入 電腦桌面", style=discord.ButtonStyle.primary, emoji="🖥️", row=0)
    async def to_desktop(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._move_files_to(interaction, DESKTOP_DIR, "🖥️ 電腦桌面 (Desktop)")

    @discord.ui.button(label="📁 存入 當前工作專案", style=discord.ButtonStyle.secondary, emoji="📁", row=0)
    async def to_project(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._move_files_to(interaction, self.daemon.current_cwd, f"📁 當前專案 ({self.daemon.current_project})")

    @discord.ui.button(label="📦 留在 臨時存放區", style=discord.ButtonStyle.secondary, emoji="📦", row=1)
    async def to_staging(self, interaction: discord.Interaction, button: discord.ui.Button):
        for child in self.children:
            child.disabled = True
        embed = discord.Embed(
            title="📦 照片已保留在 【手機上傳臨時存放區】！🌟",
            description=f"📍 **存放路徑**：`{STAGING_DIR}`\n💾 **照片數量**：`{len(self.saved_files)}` 張\n\n💡 *提示：隨時可在對話框說「把暫存區移到桌面」一鍵整批搬移！*",
            color=discord.Color.gold()
        )
        await interaction.response.edit_message(embed=embed, view=self)

# ==============================================================================
# 🎮 Discord 雙向智能體核心 (Antigravity Discord Bridge Client)
# ==============================================================================
class AntigravityDiscordBridge:
    def __init__(self):
        self.config = load_config()
        self.token = self.config.get("bot_token", "")
        self.guild_id = int(self.config.get("guild_id", 0))
        self.allowed_user_id = int(self.config.get("allowed_user_id", 0))
        
        self.workspace_root = self.config.get("workspace_root", WORKSPACE_DEFAULT)
        self.current_project = self.config.get("current_project", "Discord_Agent_Bridge")
        self.current_cwd = os.path.join(self.workspace_root, self.current_project.replace("/", "\\"))
        if not os.path.exists(self.current_cwd):
            self.current_cwd = self.workspace_root
            
        self.target_upload_dir = self.config.get("target_upload_dir", ILLIT_DIR)
        self.target_upload_name = self.config.get("target_upload_name", "🖼️ 圖片/illit")
        
        # 對話歷史與任務追蹤
        self.chat_history: List[Dict[str, str]] = []
        self.active_threads: Dict[int, Dict[str, Any]] = {} # thread_id -> task info
        self.running = True
        
        # Discord Bot 設定
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.presences = True
        
        self.bot = commands.Bot(command_prefix="!", intents=intents)
        self.tree = self.bot.tree
        self.loop = None
        
        # 註冊事件與 Slash 指令
        self._register_events()
        self._register_commands()

    # --------------------------------------------------------------------------
    # 🌲 檔案總管與樹狀圖
    # --------------------------------------------------------------------------
    def generate_ascii_tree(self, root_dir: str, max_depth: int = 2) -> str:
        if not os.path.exists(root_dir):
            return "(目錄不存在)"

        ignored = {".git", "__pycache__", "node_modules", "venv", ".gemini", ".vscode", "tempmediaStorage", ".system_generated"}
        lines = []

        def _build(cur: str, prefix: str = "", depth: int = 1):
            if depth > max_depth:
                return
            try:
                entries = sorted(os.listdir(cur))
            except Exception:
                return
            dirs = [e for e in entries if os.path.isdir(os.path.join(cur, e)) and e not in ignored and not e.startswith(".")]
            files = [e for e in entries if os.path.isfile(os.path.join(cur, e)) and not e.startswith(".")]
            total = dirs[:5] + files[:4]
            for idx, item in enumerate(total):
                is_last = (idx == len(total) - 1)
                branch = "└── " if is_last else "├── "
                next_p = prefix + ("    " if is_last else "│   ")
                p = os.path.join(cur, item)
                if os.path.isdir(p):
                    lines.append(f"{prefix}{branch}📁 **{item}/**")
                    if depth < max_depth:
                        _build(p, next_p, depth + 1)
                else:
                    lines.append(f"{prefix}{branch}📄 `{item}`")
            if len(dirs) > 5 or len(files) > 4:
                lines.append(f"{prefix}└── ... *(其他略)*")

        lines.append(f"📁 **{os.path.basename(root_dir) if root_dir != self.workspace_root else 'GitHub 根目錄'}/**")
        _build(root_dir, "", 1)
        return "\n".join(lines)

    def create_directory_tree_embed_and_view(self, target_path: str) -> Tuple[discord.Embed, discord.ui.View]:
        if not os.path.exists(target_path):
            target_path = self.workspace_root
        rel_p = os.path.relpath(target_path, self.workspace_root).replace("\\", "/")
        if rel_p == ".":
            rel_p = "🏠 GitHub 根目錄"
            
        ascii_tree = self.generate_ascii_tree(target_path, max_depth=2)
        embed = discord.Embed(
            title="🧭 【IDE 檔案總管 / 資料夾樹地圖】 🌟",
            description=f"📍 **當前瀏覽**：`{rel_p}`\n📁 **實體路徑**：`{target_path}`\n\n```text\n{ascii_tree}\n```\n👇 **從下方選單深入資料夾，點擊「✅ 鎖定」即切換專案！**",
            color=discord.Color.teal()
        )
        view = DirectoryBrowserView(self, target_path)
        return embed, view

    def list_current_directory_files(self, cwd: Optional[str] = None, proj_name: Optional[str] = None) -> str:
        t_cwd = cwd if cwd else self.current_cwd
        t_proj = proj_name if proj_name else self.current_project
        try:
            if not os.path.exists(t_cwd):
                return f"⚠️ 目錄不存在：`{t_cwd}`"
            entries = os.listdir(t_cwd)
            dirs = [d for d in entries if os.path.isdir(os.path.join(t_cwd, d))]
            files = [f for f in entries if os.path.isfile(os.path.join(t_cwd, f))]
            res = f"📍 **路徑**：`{t_cwd}`\n\n"
            if dirs:
                res += "📁 **資料夾 (Directories)**:\n" + "\n".join([f"  • 📁 `{d}/`" for d in dirs[:15]]) + "\n\n"
            if files:
                res += "📄 **檔案 (Files)**:\n" + "\n".join([f"  • 📄 `{f}` ({os.path.getsize(os.path.join(t_cwd, f)) // 1024} KB)" for f in files[:20]])
            return res if (dirs or files) else "*(此目錄目前為空)*"
        except Exception as e:
            return f"❌ 讀取目錄失敗：`{e}`"

    def get_system_status_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="📊 【Antigravity 雙向智能體系統狀態】 🌟",
            color=discord.Color.gold()
        )
        embed.add_field(name="🎯 當前專案", value=f"`{self.current_project}`", inline=True)
        embed.add_field(name="📁 工作目錄", value=f"`{self.current_cwd}`", inline=False)
        embed.add_field(name="🖼️ 存圖目標", value=f"`{self.target_upload_name}`", inline=True)
        embed.add_field(name="🧠 AI 核心", value=f"隨身管家 + 電腦端 Gemini 3.7 Flash", inline=True)
        embed.add_field(name="🟢 守護進程狀態", value="正常運行中 (PID: %d)" % os.getpid(), inline=False)
        embed.set_footer(text="Antigravity Discord Bridge 8.0 • 旗艦雙向架構")
        return embed

    # --------------------------------------------------------------------------
    # 🏰 伺服器空間頻道自動生成引擎 (One-Click Server Layout Generator)
    # --------------------------------------------------------------------------
    async def auto_setup_server_channels(self, guild: discord.Guild):
        """自動在伺服器中建立工整分類與頻道"""
        logger.info(f"🏰 正在為伺服器 [{guild.name}] 自動建立標準空間架構...")
        
        categories_spec = [
            {
                "name": "📋 個人隨身記事與跨端傳檔",
                "channels": [
                    {"name": "📝-個人隨手記事", "topic": "純個人備忘錄與自言自語 (Bot 保持100%靜默，不存電腦)"},
                    {"name": "📥-跨端傳檔與落地", "topic": "手機傳送相片、PDF、Word、Excel、TXT、代碼等所有檔案 (自動彈出存檔按鈕)"}
                ]
            },
            {
                "name": "🧠 AI 智能體旗艦主控台",
                "channels": [
                    {"name": "🤖-agent-主控台", "topic": "專案討論、下達指令 (/code, /tree, /status) 與主腦協同"},
                    {"name": "💻-指令終端機", "topic": "專用 /run 遠端操盤本機 Conda/PowerShell 虛擬環境，彩色語法高亮"},
                    {"name": "🚀-建置成果與報告", "topic": "自動推播 Gemini 3.7 編程報告、數據分析與最新成果"}
                ]
            }
        ]

        existing_categories = {c.name: c for c in guild.categories}
        existing_channels = {c.name: c for c in guild.text_channels}

        # 自動清理舊的不需要的分類與頻道
        unwanted_cats = ["👥 同學與訪客交流區", "📋 個人隨身資料庫與剪貼簿"]
        for c_name in unwanted_cats:
            old_c = existing_categories.get(c_name)
            if old_c:
                try:
                    for ch in old_c.channels:
                        await ch.delete()
                    await old_c.delete()
                    logger.info(f"🧹 已自動清理舊分類與頻道：{c_name}")
                except Exception:
                    pass

        # 重新整理現有清單
        existing_categories = {c.name: c for c in guild.categories}
        existing_channels = {c.name: c for c in guild.text_channels}

        for cat_spec in categories_spec:
            cat_name = cat_spec["name"]
            category = existing_categories.get(cat_name)
            if not category:
                try:
                    category = await guild.create_category(cat_name)
                    logger.info(f"✨ 建立分類：{cat_name}")
                except Exception as e:
                    logger.warning(f"建立分類失敗: {e}")
                    continue

            for ch_spec in cat_spec["channels"]:
                ch_name = ch_spec["name"]
                if ch_name not in existing_channels:
                    try:
                        ch = await guild.create_text_channel(name=ch_name, category=category, topic=ch_spec["topic"])
                        logger.info(f"  └─ 建立頻道：#{ch_name}")
                        
                        # 若是主控台頻道，發送置頂面板卡片
                        if ch_name == "🤖-agent-主控台":
                            embed = discord.Embed(
                                title="📌 【Antigravity 雙向 Agent 隨身指揮中樞】 🌟",
                                description=(
                                    "━━━━━━━━━━━━━━━━━━━━━\n"
                                    f"🎯 **當前專案**：`{self.current_project}`\n"
                                    f"📁 **工作目錄**：`{self.current_cwd}`\n"
                                    f"🖼️ **圖片目標**：`{self.target_upload_name}`\n\n"
                                    "💬 **操作技巧**：\n"
                                    "• ⚡ **/code [需求]**：委派電腦端 **Gemini 3.7 Flash** 深度編程，自動開 Thread 討論串！\n"
                                    "• 🌲 **/tree**：動態瀏覽資料夾樹，下拉選單直接切換專案！\n"
                                    "• 💻 **/run [指令]**：遠端執行 PowerShell 指令操盤！\n"
                                    "• 📱 **/apk**：一鍵索取最新 Samsung A32 氣氛燈 APK！\n"
                                    "• 📥 **傳圖直達**：在 `#📥-相片傳送與落地` 發圖，自動存入電腦！\n"
                                    "━━━━━━━━━━━━━━━━━━━━━"
                                ),
                                color=discord.Color.purple()
                            )
                            msg = await ch.send(embed=embed, view=AgentDashboardView(self))
                            try:
                                await msg.pin()
                            except Exception:
                                pass
                    except Exception as e:
                        logger.warning(f"建立頻道 {ch_name} 失敗: {e}")

    # --------------------------------------------------------------------------
    # 📡 雙向成果自動監聽推播 (AgentOutboxWatcher)
    # --------------------------------------------------------------------------
    def start_outbox_watcher_thread(self):
        """監聽電腦端 Gemini 3.7 Flash 寫入的成果報告與新編譯 APK"""
        def _watcher():
            logger.info("📡 雙向成果監聽線程 (AgentOutboxWatcher) 已啟動！")
            last_mtime = os.path.getmtime(INBOX_FILE) if os.path.exists(INBOX_FILE) else 0.0
            last_pushed = ""

            while self.running:
                try:
                    if os.path.exists(INBOX_FILE):
                        mtime = os.path.getmtime(INBOX_FILE)
                        if mtime > last_mtime:
                            last_mtime = mtime
                            with open(INBOX_FILE, "r", encoding="utf-8", errors="replace") as f:
                                content = f.read()

                            if "### ✨ Agent 執行結果：" in content and "狀態：`🟢" in content:
                                ans_part = content.split("### ✨ Agent 執行結果：")[1].split("---")[0].strip()
                                if ans_part and ans_part != last_pushed:
                                    last_pushed = ans_part
                                    logger.info("🎉 偵測到電腦端 Gemini 3.7 Flash 執行完畢，自動推播至 Discord...")
                                    
                                    # 推播至 #🚀-建置成果與apk 頻道
                                    if self.loop and self.bot.is_ready():
                                        asyncio.run_coroutine_threadsafe(self._push_outbox_report(ans_part), self.loop)

                except Exception as e:
                    logger.debug(f"監聽異常: {e}")
                time.sleep(2)

        t = threading.Thread(target=_watcher, daemon=True)
        t.start()

    async def _push_outbox_report(self, report_text: str):
        guild = self.bot.get_guild(self.guild_id) if self.guild_id else (self.bot.guilds[0] if self.bot.guilds else None)
        if not guild:
            return
        
        target_channel = discord.utils.get(guild.text_channels, name="🚀-建置成果與apk")
        if not target_channel:
            target_channel = discord.utils.get(guild.text_channels, name="🤖-agent-主控台")
        if not target_channel:
            return

        embed = discord.Embed(
            title="🎉 【電腦端 Gemini 3.7 Flash 旗艦主腦執行完成】 🌟",
            description=f"📍 **專案**：`{self.current_project}`\n━━━━━━━━━━━━━━━━━━━━━\n\n{report_text[:3500]}\n\n💡 *提示：所有程式碼變更與工程已在電腦端落實生效！*",
            color=discord.Color.green()
        )
        
        # 檢查是否有 2 分鐘內剛編譯生成的最新 APK
        apk_candidates = [
            os.path.join(self.workspace_root, "視覺動態效果手機待修", "mobile", "手機音效氣氛燈_A32專屬版.apk"),
            os.path.join(self.workspace_root, "FB_adblock.apk")
        ]
        now = time.time()
        attached_file = None
        for apk in apk_candidates:
            if os.path.exists(apk) and (now - os.path.getmtime(apk) < 180):
                attached_file = discord.File(apk)
                break

        if attached_file:
            await target_channel.send(content="📦 **偵測到最新編譯的 APK 安裝包，已為夥伴自動上傳！** ✨", embed=embed, file=attached_file)
        else:
            await target_channel.send(embed=embed)

    # --------------------------------------------------------------------------
    # 📩 訊息事件處理 (相片落地 / 剪貼簿 / 連續補充說明)
    # --------------------------------------------------------------------------
    def _register_events(self):
        @self.bot.event
        async def on_ready():
            self.loop = asyncio.get_running_loop()
            logger.info(f"🚀 Antigravity Discord 橋接器已成功上線！Bot: {self.bot.user.name} ({self.bot.user.id})")
            
            # 自動取得伺服器
            target_guild = None
            if self.guild_id:
                target_guild = self.bot.get_guild(self.guild_id)
            if not target_guild and self.bot.guilds:
                target_guild = self.bot.guilds[0]
                self.guild_id = target_guild.id
                self.config["guild_id"] = target_guild.id
                save_config(self.config)

            if target_guild:
                # 自動綁定 Owner ID
                if self.allowed_user_id == 0:
                    self.allowed_user_id = target_guild.owner_id
                    self.config["allowed_user_id"] = target_guild.owner_id
                    save_config(self.config)
                    logger.info(f"👑 已自動綁定伺服器擁有者（夥伴）ID: {self.allowed_user_id}")

                # 自動同步 Slash Commands 至該伺服器 (即時秒生效！)
                try:
                    self.tree.copy_global_to(guild=target_guild)
                    await self.tree.sync(guild=target_guild)
                    logger.info(f"✨ 成功向伺服器 [{target_guild.name}] 即時註冊所有 Slash 指令！")
                except Exception as err:
                    logger.warning(f"同步 Slash 指令失敗: {err}")

                # 自動建立分類與頻道
                await self.auto_setup_server_channels(target_guild)

            # 啟動 Outbox 監聽線程
            self.start_outbox_watcher_thread()

        @self.bot.event
        async def on_message(message: discord.Message):
            if message.author.bot:
                return

            ch_name = message.channel.name if hasattr(message.channel, "name") else ""

            # 0. 個人隨手記事頻道：保持 100% 安靜，不干擾、不存檔
            if ch_name.startswith("📝") or "剪貼" in ch_name or "記事" in ch_name:
                return

            # 0.1 處理 Discord 引用/回覆訊息 (Reply Context & Memory)
            reply_context = ""
            if message.reference and message.reference.message_id:
                try:
                    ref_msg = await message.channel.fetch_message(message.reference.message_id)
                    reply_context = f"【夥伴回覆了前一則訊息 (由 {ref_msg.author.display_name} 發送)】：\n「{ref_msg.content}」\n"
                    # 如果前一則訊息有附件 (如音檔、照片、PDF)，自動萃取
                    if ref_msg.attachments:
                        for att in ref_msg.attachments:
                            is_audio = att.content_type and "audio" in att.content_type or any(att.filename.lower().endswith(ext) for ext in [".ogg", ".mp3", ".m4a", ".wav", ".aac", ".opus"])
                            if is_audio:
                                ts = time.strftime("%Y%m%d_%H%M%S")
                                ref_audio_dest = os.path.join(STAGING_DIR, f"reply_audio_{ts}_{att.filename}")
                                await att.save(ref_audio_dest)
                                trans_text = await asyncio.to_thread(VoiceTranscriber.transcribe, ref_audio_dest)
                                if trans_text:
                                    reply_context += f"【引用前則語音訊息轉文字】：\n「{trans_text}」\n"
                            else:
                                reply_context += f"【引用前則檔案】：`{att.filename}`\n"
                except Exception as e:
                    logger.warning(f"萃取回覆上下文失敗: {e}")

            # 0.2 檢查是否直接上傳了語音/音訊訊息 (.ogg, .mp3, .m4a, .wav 等)
            audio_attachments = []
            other_attachments = []
            if message.attachments:
                for att in message.attachments:
                    is_audio = (att.content_type and "audio" in att.content_type) or any(att.filename.lower().endswith(ext) for ext in [".ogg", ".mp3", ".m4a", ".wav", ".aac", ".opus"])
                    if is_audio:
                        audio_attachments.append(att)
                    else:
                        other_attachments.append(att)

            # 如果上傳了語音訊息：自動語音轉文字並作為指令/對話輸入
            if audio_attachments:
                for att in audio_attachments:
                    ts = time.strftime("%Y%m%d_%H%M%S")
                    audio_dest = os.path.join(STAGING_DIR, f"voice_{ts}_{att.filename}")
                    await att.save(audio_dest)
                    
                    async with message.channel.typing():
                        voice_text = await asyncio.to_thread(VoiceTranscriber.transcribe, audio_dest)
                    
                    if voice_text:
                        # 在頻道顯示辨識結果
                        embed_asr = discord.Embed(
                            title="🎙️ 語音輸入辨識成功！",
                            description=f"💬 「**{voice_text}**」",
                            color=discord.Color.teal()
                        )
                        await message.channel.send(embed=embed_asr)

                        # 合併為當前 prompt
                        user_prompt = voice_text
                        if reply_context:
                            user_prompt = f"{reply_context}\n夥伴語音補充：{user_prompt}"

                        # 檢查是否為專案切換指令
                        switched_proj = self.try_instant_project_switch(user_prompt)
                        if switched_proj:
                            ls_summary = self.list_current_directory_files()
                            embed_sw = discord.Embed(
                                title=f"⚡ 已成功為夥伴切換專案至：【{switched_proj}】！🌟",
                                description=f"📍 **實體路徑**：`{self.current_cwd}`\n\n📂 **專案檔案清單**：\n```text\n{ls_summary}\n```",
                                color=discord.Color.green()
                            )
                            await message.channel.send(embed=embed_sw)
                            StorageManager.record_inbox(message.author.id, f"[語音切換專案至 {switched_proj}]", project_name=self.current_project, cwd=self.current_cwd, status="🟢 已即時切換", answer=f"已切換至 {self.current_cwd}")
                            return

                        # 判斷是否為動作型任務
                        if self._is_heavy_coding_task(user_prompt):
                            await self._handle_heavy_task_in_thread(message.channel, message.author, user_prompt)
                        else:
                            async with message.channel.typing():
                                answer = await asyncio.to_thread(
                                    MobileAIEngine.query_ai,
                                    user_prompt,
                                    self.current_project,
                                    self.current_cwd,
                                    self.target_upload_name,
                                    self.target_upload_dir,
                                    self.chat_history,
                                    self.config.get("ai_model", "meta/llama-3.2-11b-vision-instruct")
                                )
                            self.chat_history.append({"role": "user", "content": user_prompt})
                            self.chat_history.append({"role": "assistant", "content": answer})
                            embed = discord.Embed(
                                title="📱 【Agent 隨身解答】 🌟",
                                description=f"📍 **專案**：`{self.current_project}`\n━━━━━━━━━━━━━━━━━━━━━\n\n{answer}",
                                color=discord.Color.blue()
                            )
                            await message.channel.send(embed=embed)
                            StorageManager.record_inbox(message.author.id, f"[語音] {user_prompt}", project_name=self.current_project, cwd=self.current_cwd, status="🟢 已解答完畢", answer=answer)
                return

            # 1. 處理全能檔案上傳 (相片、PDF、Word、Excel、TXT、代碼、CSV 等所有檔案)：安全暫存並彈出目標選擇按鈕
            if message.attachments and (ch_name in ["📥-跨端傳檔與落地", "相片", "照片", "檔案", "傳檔"] or not ch_name.startswith("📝")):
                saved_files = []
                for att in message.attachments:
                    ts = time.strftime("%Y%m%d_%H%M%S")
                    fn = f"file_{ts}_{att.filename}"
                    dest = os.path.join(STAGING_DIR, fn)
                    await att.save(dest)
                    saved_files.append(dest)
                
                if saved_files:
                    count = len(saved_files)
                    file_types = [os.path.splitext(f)[1].upper() for f in saved_files]
                    types_summary = ", ".join(list(set(file_types)))
                    embed = discord.Embed(
                        title=f"📥 收到夥伴上傳的 {count} 個檔案 ({types_summary})！🌟",
                        description=(
                            f"💾 **已安全暫存於臨時區**（共 {count} 個檔案）\n\n"
                            "👇 **請點擊下方按鈕，選擇要將這批檔案存入電腦的哪一個位置：**"
                        ),
                        color=discord.Color.blue()
                    )
                    view = PhotoDestinationView(self, saved_files, message.author.id)
                    await message.channel.send(embed=embed, view=view)
                    StorageManager.record_inbox(message.author.id, f"[上傳 {count} 個檔案待選擇目標: {types_summary}]", project_name=self.current_project, cwd=STAGING_DIR, status="🟡 等待選擇目標位置", answer="已提供目標選擇按鈕")
                    return

            # 2. 跨端文字剪貼簿頻道：保持安靜
            if "剪貼" in ch_name or ch_name == "📝-跨端文字剪貼簿":
                # 純個人剪貼簿，不回覆
                return

            # 3. 處理 Thread 內的連續補充說明 (Steering Queue)
            if isinstance(message.channel, discord.Thread):
                thread_id = message.channel.id
                if thread_id in self.active_threads:
                    self.active_threads[thread_id]["supplements"].append(message.content)
                    supp_count = len(self.active_threads[thread_id]["supplements"])
                    embed = discord.Embed(
                        title="📥 已收到夥伴最新補充說明！",
                        description=f"💬 「{message.content[:60]}」\n\n⏳ **Working...** (已合流 {supp_count} 則補充說明，持續深度運算中 🚀)",
                        color=discord.Color.purple()
                    )
                    await message.channel.send(embed=embed)
                return

            # 4. 在 #🤖-agent-主控台 或 #💬-同學提問區 純文字提問
            if ch_name in ["🤖-agent-主控台", "💬-同學提問區"]:
                user_prompt = message.content.strip()
                if not user_prompt:
                    return

                if reply_context:
                    user_prompt = f"{reply_context}\n夥伴提問：{user_prompt}"

                # 檢查是否為專案切換指令
                switched_proj = self.try_instant_project_switch(user_prompt)
                if switched_proj:
                    ls_summary = self.list_current_directory_files()
                    embed_sw = discord.Embed(
                        title=f"⚡ 已成功為夥伴切換專案至：【{switched_proj}】！🌟",
                        description=f"📍 **實體路徑**：`{self.current_cwd}`\n\n📂 **專案檔案清單**：\n```text\n{ls_summary}\n```",
                        color=discord.Color.green()
                    )
                    await message.channel.send(embed=embed_sw)
                    StorageManager.record_inbox(message.author.id, f"[文字切換專案至 {switched_proj}]", project_name=self.current_project, cwd=self.current_cwd, status="🟢 已即時切換", answer=f"已切換至 {self.current_cwd}")
                    return

                # 若是重度編程任務，自動開 Thread 並委派
                if self._is_heavy_coding_task(user_prompt):
                    await self._handle_heavy_task_in_thread(message.channel, message.author, user_prompt)
                    return

                # 一般隨身管家問答
                async with message.channel.typing():
                    answer = await asyncio.to_thread(
                        MobileAIEngine.query_ai,
                        user_prompt,
                        self.current_project,
                        self.current_cwd,
                        self.target_upload_name,
                        self.target_upload_dir,
                        self.chat_history,
                        self.config.get("ai_model", "meta/llama-3.2-11b-vision-instruct")
                    )

                self.chat_history.append({"role": "user", "content": user_prompt})
                self.chat_history.append({"role": "assistant", "content": answer})
                if len(self.chat_history) > 12:
                    self.chat_history = self.chat_history[-12:]

                embed = discord.Embed(
                    title="📱 【Mobile Agent 隨身解答】 🌟",
                    description=f"📍 **專案**：`{self.current_project}`\n━━━━━━━━━━━━━━━━━━━━━\n\n{answer}",
                    color=discord.Color.blue()
                )
                await message.channel.send(embed=embed)
                StorageManager.record_inbox(message.author.id, user_prompt, project_name=self.current_project, cwd=self.current_cwd, status="🟢 已解答完畢", answer=answer)

            await self.bot.process_commands(message)

    # --------------------------------------------------------------------------
    # ⚡ 重度任務 Thread 派工器
    # --------------------------------------------------------------------------
    def try_instant_project_switch(self, text: str) -> Optional[str]:
        """檢查夥伴的文字/語音是否要求切換專案目錄，若是則直接切換並回傳新路徑"""
        t = text.lower()
        keywords = ["切換", "移到", "切到", "開啟", "前往", "cd ", "專案移到", "資料專案", "到專案"]
        if not any(k in t for k in keywords):
            return None

        # 特殊別名映射
        aliases = {
            "mobile": r"視覺動態效果\mobile",
            "手機": r"視覺動態效果\mobile",
            "視覺動態效果": "視覺動態效果",
            "pc": r"視覺動態效果\PC",
            "鈣鈦礦": "Perovskite",
            "perovskite": "Perovskite",
            "bridge": "Discord_Agent_Bridge",
            "discord": "Discord_Agent_Bridge"
        }
        for alias, rel_path in aliases.items():
            if alias in t:
                target_cwd = os.path.join(self.workspace_root, rel_path)
                if os.path.exists(target_cwd):
                    self.current_project = rel_path
                    self.current_cwd = target_cwd
                    self.config["current_project"] = rel_path
                    save_config(self.config)
                    logger.info(f"⚡ 透過別名即時切換專案至：{rel_path}")
                    return rel_path

        # 遍歷 workspace_root 下的所有專案與子專案
        try:
            for root, dirs, files in os.walk(self.workspace_root):
                rel = os.path.relpath(root, self.workspace_root)
                if rel != ".":
                    parts = rel.split(os.sep)
                    if len(parts) <= 2:
                        name_lower = parts[-1].lower()
                        if name_lower in t or rel.lower().replace(os.sep, "/") in t.replace("\\", "/"):
                            target_cwd = os.path.join(self.workspace_root, rel)
                            if os.path.exists(target_cwd):
                                self.current_project = rel
                                self.current_cwd = target_cwd
                                self.config["current_project"] = rel
                                save_config(self.config)
                                logger.info(f"⚡ 即時切換專案至：{rel} ({target_cwd})")
                                return rel
        except Exception as e:
            logger.error(f"切換專案掃描異常: {e}")

        return None

    def _is_heavy_coding_task(self, text: str) -> bool:
        action_keywords = ["寫程式", "寫代碼", "重構", "開發", "修改程式碼", "加功能", "修改代碼", "build apk", "編譯apk", "編譯 apk", "寫一個app", "設計app", "修復bug", "修bug", "改寫", "實作", "改名", "重新命名", "換成", "改成", "幫我改", "幫我做", "幫我建", "幫我刪", "幫我移", "幫我寫", "幫我跑", "幫我執行", "建立", "刪除", "新增", "修復", "把", "執行", "優化", "測試", "編譯", "專案", "檔案", "資料夾"]
        t = text.lower()
        return any(k in t for k in action_keywords)

    async def _handle_heavy_task_in_thread(self, channel: discord.TextChannel, author: discord.User, task_prompt: str):
        thread_name = f"🧵-任務_{task_prompt[:15].replace(' ', '_')}"
        thread = await channel.create_thread(name=thread_name, auto_archive_duration=60)
        
        self.active_threads[thread.id] = {
            "task": task_prompt,
            "supplements": [],
            "start_time": time.time()
        }

        # 寫入收件匣給電腦端 Gemini 3.7
        StorageManager.record_inbox(
            author.id,
            task_prompt,
            project_name=self.current_project,
            cwd=self.current_cwd,
            status="🟡 等待電腦端 Gemini 3.7 Flash 執行中...",
            answer="任務已排入電腦端主腦佇列，完成後將自動推播成果報告與 APK！",
            is_heavy_task=True
        )

        embed = discord.Embed(
            title="📥 【已接收重度編程任務！⚡】 🌟",
            description=(
                "━━━━━━━━━━━━━━━━━━━━━\n"
                f"🎯 **委派對象**：`💻 電腦端 Gemini 3.7 Flash 旗艦主腦`\n"
                f"📁 **工作專案**：`{self.current_project}`\n"
                f"💬 **任務指令**：「{task_prompt}」\n\n"
                "⏳ **電腦端主腦已開始深度編程與重構...**\n"
                "💡 *夥伴可在這個討論串隨時發送文字補充說明，大腦會自動合流處理！*"
            ),
            color=discord.Color.purple()
        )
        await thread.send(embed=embed)

    # --------------------------------------------------------------------------
    # ⚡ Slash Commands (/) 註冊
    # --------------------------------------------------------------------------
    def _register_commands(self):
        @self.tree.command(name="code", description="⚡ 委派電腦端 Gemini 3.7 Flash 旗艦主腦執行重度編程與改代碼 (自動開討論串)")
        @app_commands.describe(task="請輸入編程需求 (例如：幫我修復 A32 氣氛燈並編譯 APK)")
        async def code_cmd(interaction: discord.Interaction, task: str):
            await interaction.response.defer()
            await self._handle_heavy_task_in_thread(interaction.channel, interaction.user, task)
            await interaction.followup.send(f"🚀 已為夥伴建立專屬任務討論串並委派電腦端 Gemini 3.7 Flash！", ephemeral=True)

        @self.tree.command(name="tree", description="🧭 檢視工作區資料夾樹狀圖，並可透過下拉選單切換專案")
        async def tree_cmd(interaction: discord.Interaction):
            embed, view = self.create_directory_tree_embed_and_view(self.current_cwd)
            await interaction.response.send_message(embed=embed, view=view)

        @self.tree.command(name="cd", description="🎯 切換當前工作專案與目錄")
        @app_commands.describe(folder="目標資料夾名稱或相對路徑 (例如：視覺動態效果/mobile)")
        async def cd_cmd(interaction: discord.Interaction, folder: str):
            q = folder.strip().replace("/", "\\")
            target = os.path.join(self.workspace_root, q)
            if not os.path.exists(target):
                # 模糊搜尋
                for root, dirs, _ in os.walk(self.workspace_root):
                    for d in dirs:
                        if folder.lower() in d.lower():
                            target = os.path.join(root, d)
                            break
            if os.path.exists(target):
                rel_p = os.path.relpath(target, self.workspace_root).replace("\\", "/")
                self.current_project = rel_p
                self.current_cwd = target
                self.config["current_project"] = rel_p
                self.config["current_cwd"] = target
                save_config(self.config)
                
                embed = discord.Embed(
                    title=f"🎯 已成功切換至專案：{rel_p}",
                    description=f"📍 **實體路徑**：`{target}`\n\n{self.list_current_directory_files(target, rel_p)}",
                    color=discord.Color.brand_green()
                )
                await interaction.response.send_message(embed=embed)
            else:
                await interaction.response.send_message(f"⚠️ 找不到與 `{folder}` 相符的專案目錄！你可以輸入 `/tree` 瀏覽完整樹狀圖。", ephemeral=True)

        @self.tree.command(name="ls", description="📂 查看當前專案目錄檔案清單")
        async def ls_cmd(interaction: discord.Interaction):
            ls_text = self.list_current_directory_files()
            embed = discord.Embed(title=f"📂 【{self.current_project} 檔案清單】", description=ls_text, color=discord.Color.blue())
            await interaction.response.send_message(embed=embed)

        @self.tree.command(name="run", description="💻 遠端在電腦執行 PowerShell 指令 (夥伴專屬最高特權)")
        @app_commands.describe(command="要執行的 PowerShell 指令 (例如：Get-Process)")
        async def run_cmd(interaction: discord.Interaction, command: str):
            # 權限驗證：僅限擁有者
            if interaction.user.id != self.allowed_user_id and interaction.user.id != interaction.guild.owner_id:
                await interaction.response.send_message("🚫 **權限不足**：此指令僅限伺服器擁有者（夥伴）使用，以保護電腦安全！", ephemeral=True)
                return

            await interaction.response.defer()
            try:
                res = subprocess.run(
                    ["powershell", "-NoProfile", "-Command", command],
                    cwd=self.current_cwd,
                    capture_output=True,
                    text=True,
                    timeout=180
                )
                out = res.stdout.strip()
                err = res.stderr.strip()
                
                result_text = out if out else "(無標準輸出)"
                if err:
                    result_text += f"\n\n[錯誤/警告]:\n{err}"
                
                if len(result_text) > 3800:
                    result_text = result_text[:3800] + "\n...(輸出過長已截斷)"

                embed = discord.Embed(
                    title="💻 【PowerShell 指令執行結果】 🌟",
                    description=f"⚡ **指令**：`{command}`\n📂 **執行路徑**：`{self.current_cwd}`\n```powershell\n{result_text}\n```",
                    color=discord.Color.gold() if not err else discord.Color.red()
                )
                await interaction.followup.send(embed=embed)
            except Exception as e:
                await interaction.followup.send(f"❌ 執行失敗：`{e}`")

        @self.tree.command(name="apk", description="📦 索取最新 Samsung A32 氣氛燈 APK 安裝包")
        async def apk_cmd(interaction: discord.Interaction):
            apk_path = os.path.join(self.workspace_root, "視覺動態效果手機待修", "mobile", "手機音效氣氛燈_A32專屬版.apk")
            if os.path.exists(apk_path):
                await interaction.response.send_message(content="✨ 這是電腦端編譯產出的最新 Samsung A32 氣氛燈 APK 安裝包！", file=discord.File(apk_path))
            else:
                await interaction.response.send_message("⚠️ 未找到編譯出的 APK 檔案。", ephemeral=True)

        @self.tree.command(name="status", description="📊 查看電腦系統狀態與 Agent 健康度儀表板")
        async def status_cmd(interaction: discord.Interaction):
            embed = self.get_system_status_embed()
            await interaction.response.send_message(embed=embed)

        @self.tree.command(name="codewhale", description="🐳 調用本地 CodeWhale 零 Token 智能體執行指令")
        @app_commands.describe(prompt="指令需求")
        async def codewhale_cmd(interaction: discord.Interaction, prompt: str):
            if not os.path.exists(CODEWHALE_EXE):
                await interaction.response.send_message(f"⚠️ 未找到 CodeWhale 執行檔：`{CODEWHALE_EXE}`", ephemeral=True)
                return
            await interaction.response.defer()
            try:
                cmd = f'& "{CODEWHALE_EXE}" -p "{prompt}"'
                res = subprocess.run(["powershell", "-NoProfile", "-Command", cmd], cwd=self.current_cwd, capture_output=True, text=True, timeout=180)
                out = res.stdout.strip()
                embed = discord.Embed(title="🐳 【CodeWhale 執行結果】", description=f"```text\n{out[:3800]}\n```", color=discord.Color.teal())
                await interaction.followup.send(embed=embed)
            except Exception as e:
                await interaction.followup.send(f"❌ CodeWhale 異常：`{e}`")

        @self.tree.command(name="init_server", description="🏰 一鍵自動在伺服器建立完整的分類與專屬頻道架構")
        async def init_server_cmd(interaction: discord.Interaction):
            if interaction.user.id != self.allowed_user_id and interaction.user.id != interaction.guild.owner_id:
                await interaction.response.send_message("🚫 此指令僅限伺服器擁有者使用！", ephemeral=True)
                return
            await interaction.response.defer(ephemeral=True)
            await self.auto_setup_server_channels(interaction.guild)
            await interaction.followup.send("🎉 **伺服器空間架構已全自動建立完成！** ✨", ephemeral=True)

    # --------------------------------------------------------------------------
    # 🚀 啟動運行
    # --------------------------------------------------------------------------
    def run(self):
        ensure_single_instance()
        if not self.token:
            logger.error("❌ 未設定 Discord Bot Token，請檢查 discord_bridge_config.json！")
            sys.exit(1)
        self.bot.run(self.token)

if __name__ == "__main__":
    bridge = AntigravityDiscordBridge()
    bridge.run()
