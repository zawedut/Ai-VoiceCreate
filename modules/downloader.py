# =============================================================================
# 📥 DOWNLOADER MODULE
# =============================================================================
# จัดการการดาวน์โหลดวิดีโอจาก YouTube / TikTok

import re
import os
import yt_dlp
from pathlib import Path
from config.settings import URL_FILE, INPUT_DIR, COOKIES_FILE

__all__ = [
    'get_urls',
    'remove_url_from_file',
    'add_urls_to_file',
    'sanitize_filename',
    'download_single_video',
]

# =============================================================================
# 📝 URL FILE MANAGEMENT
# =============================================================================

def get_urls() -> list:
    """อ่าน URLs จากไฟล์"""
    if not URL_FILE.exists():
        return []
    with open(URL_FILE, "r", encoding='utf-8') as f:
        return [line.strip() for line in f.readlines() if line.strip()]


def remove_url_from_file(target_url: str) -> None:
    """ลบ URL ที่ทำเสร็จแล้วออกจากไฟล์"""
    urls = get_urls()
    with open(URL_FILE, "w", encoding='utf-8') as f:
        for url in urls:
            if url != target_url:
                f.write(url + "\n")


def add_urls_to_file(urls: list) -> None:
    """เพิ่ม URLs ลงในไฟล์ (append)"""
    existing = get_urls()
    with open(URL_FILE, "a", encoding='utf-8') as f:
        for url in urls:
            url = url.strip()
            if url and url not in existing:
                f.write(url + "\n")


def clear_urls_file() -> None:
    """ล้างไฟล์ URLs ทั้งหมด"""
    with open(URL_FILE, "w", encoding='utf-8') as f:
        f.write("")


# =============================================================================
# 🔧 HELPERS
# =============================================================================

def sanitize_filename(name: str) -> str:
    """ทำชื่อไฟล์ให้ปลอดภัย (ลบอักขระพิเศษ)"""
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    name = name.strip().replace(" ", "_")
    return name[:50]  # จำกัดความยาว


# =============================================================================
# ⬇️ VIDEO DOWNLOAD
# =============================================================================

def download_single_video(url: str, output_dir: Path = None) -> str | None:
    """
    ดาวน์โหลดวิดีโอจาก YouTube/TikTok
    
    Args:
        url: URL ของวิดีโอ
        output_dir: โฟลเดอร์ปลายทาง (default: INPUT_DIR)
        
    Returns:
        Path ของไฟล์ที่ดาวน์โหลด หรือ None ถ้าล้มเหลว
    """
    if output_dir is None:
        output_dir = INPUT_DIR
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"    ⬇️ กำลังโหลด: {url}")
    
    # ใช้ format ที่มี video+audio รวมกันแล้ว (ไม่ต้อง merge ด้วย ffmpeg)
    ydl_opts = {
        'format': 'best[ext=mp4]/best',  # เลือก mp4 ที่ดีที่สุดที่มี video+audio
        'outtmpl': str(output_dir / '%(title).100s.%(ext)s'),
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'restrictfilenames': True,
        'nocheckcertificate': True,
        'merge_output_format': None,  # ไม่ merge
    }
    
    # เพิ่ม cookies ถ้ามี
    if COOKIES_FILE.exists():
        ydl_opts['cookiefile'] = str(COOKIES_FILE)
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filepath = ydl.prepare_filename(info)
            print(f"    ✅ ดาวน์โหลดสำเร็จ: {Path(filepath).name}")
            return filepath
            
    except Exception as e:
        print(f"    ⚠️ Download Error: {e}")
        return None


def get_video_info(url: str) -> dict | None:
    """ดึงข้อมูลวิดีโอโดยไม่ดาวน์โหลด"""
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=False)
    except:
        return None
