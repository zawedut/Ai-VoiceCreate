# =============================================================================
# 🔧 CONFIG & SETTINGS
# =============================================================================
# โหลดจาก .env file หรือใช้ค่า default

import os
from pathlib import Path
from dotenv import load_dotenv

# โหลด .env file
load_dotenv()

# =============================================================================
# 📁 PATHS
# =============================================================================
# Base directory (ใช้ project root ถ้าไม่ได้กำหนด)
PROJECT_ROOT = Path(__file__).parent.parent
BASE_DIR = Path(os.getenv("BASE_DIR", PROJECT_ROOT))

# Working directories
INPUT_DIR = Path(os.getenv("INPUT_DIR", BASE_DIR / "1_Input_Raw"))
ASSETS_DIR = Path(os.getenv("ASSETS_DIR", BASE_DIR / "2_Assets"))
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", BASE_DIR / "3_Output_Ready"))
TEMP_DIR = BASE_DIR / "temp"

# Files
URL_FILE = BASE_DIR / "urls.txt"
COOKIES_FILE = ASSETS_DIR / "cookies.txt"
AVATAR_FILE = ASSETS_DIR / "avatar_talking.mp4"
AVATAR_LOOPED_TEMP = TEMP_DIR / "avatar_looped_ready.mp4"
AVATAR_CHROMA_TEMP = TEMP_DIR / "avatar_no_green.mov"

# =============================================================================
# 🔑 GEMINI API CONFIG
# =============================================================================
def get_api_keys() -> list:
    """โหลด API keys จาก .env (คั่นด้วย comma)"""
    keys_str = os.getenv("GEMINI_API_KEYS", "")
    if not keys_str:
        return []
    return [k.strip() for k in keys_str.split(",") if k.strip()]

API_KEYS = get_api_keys()

# Model hierarchy - ใช้แต่ model เก่งๆ
MODEL_HIERARCHY = [
    "gemini-2.5-flash",       # เก่งสุด
    "gemini-3.0-flash",       # รุ่นเก่ากว่า
]

# =============================================================================
# 🎤 VOICE CONFIG
# =============================================================================
VOICE_NAME = os.getenv("VOICE_NAME", "th-TH-NiwatNeural")
VOICE_RATE = os.getenv("VOICE_RATE", "+5%")
VOICE_PITCH = os.getenv("VOICE_PITCH", "+3Hz")
VOICE_VOLUME = os.getenv("VOICE_VOLUME", "+10%")

# =============================================================================
# ⚙️ PROCESSING CONFIG
# =============================================================================
# Video output settings
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
VIDEO_FPS = 30
VIDEO_BITRATE = "5000k"
VIDEO_PRESET = "medium"

# Timing settings
WORDS_PER_SECOND = 2.2  # ปรับใหม่ให้แม่นขึ้น
SYNC_TOLERANCE = 10.0   # ยอมรับความต่าง +/- 10 วินาที (เน้นเนื้อหาครบ)
DELAY_BETWEEN_CLIPS = 10  # พักระหว่างคลิป (วินาที)

# Retry settings
MAX_UPLOAD_ATTEMPTS = 5
MAX_SCRIPT_ATTEMPTS = 3   # ลองแค่ 3 รอบ แล้วเอาอันที่ดีที่สุด
ATTEMPTS_PER_MODEL = 3    # ใช้ model เดียว 3 รอบ

# =============================================================================
# 🛠️ HELPER FUNCTIONS
# =============================================================================
def ensure_directories():
    """สร้าง directories ที่จำเป็นทั้งหมด"""
    for d in [INPUT_DIR, ASSETS_DIR, OUTPUT_DIR, TEMP_DIR]:
        d.mkdir(parents=True, exist_ok=True)

def get_config_summary() -> dict:
    """สรุป config ปัจจุบัน (ไม่รวม secrets)"""
    return {
        "base_dir": str(BASE_DIR),
        "gemini_keys_count": len(API_KEYS),
        "voice": VOICE_NAME,
        "models": MODEL_HIERARCHY,
    }
