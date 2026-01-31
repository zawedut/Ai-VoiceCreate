#!/usr/bin/env python3
# =============================================================================
# 🎬 AI VIDEO FACTORY - GOOGLE DRIVE CLOUD MODE
# =============================================================================
# ทำงานกับ Google Drive Cloud โดยตรง
# - อ่าน urls.txt จาก Drive
# - ดาวน์โหลดวิดีโอมา process ใน temp
# - อัพโหลด output กลับไป Drive
# - ไม่รกเครื่อง local!
#
# Usage:
#   python main_gdrive.py              # รัน factory
#   python main_gdrive.py --setup      # ตั้งค่า Google Drive ครั้งแรก

import sys
import argparse
import asyncio
import os
import time
import nest_asyncio
from pathlib import Path

nest_asyncio.apply()

from config.settings import (
    ensure_directories, get_config_summary,
    TEMP_DIR, DELAY_BETWEEN_CLIPS
)
from modules.downloader import download_single_video, sanitize_filename
from modules.gemini_brain import (
    test_api_keys, get_perfect_fit_script, reset_model_fallback,
    available_keys, MODEL_HIERARCHY
)
from modules.voice import generate_voice_sync
from modules.video_processor import process_video_pipeline, cleanup_temp_files
from modules.gdrive import GoogleDriveClient, is_gdrive_available, CREDENTIALS_FILE

# =============================================================================
# 🎯 MAIN FUNCTIONS
# =============================================================================

def show_banner():
    print("""
╔═══════════════════════════════════════════════════════════════╗
║             🎬 AI VIDEO FACTORY - GOOGLE DRIVE 🎬             ║
║          All files on Cloud - Keep your PC clean!            ║
╚═══════════════════════════════════════════════════════════════╝
    """)


def show_setup_guide():
    """แสดงวิธีตั้งค่า Google Drive API"""
    print("""
╔═══════════════════════════════════════════════════════════════╗
║                  📋 GOOGLE DRIVE SETUP                        ║
╚═══════════════════════════════════════════════════════════════╝

ทำตามขั้นตอนนี้ครั้งเดียว:

1. ไปที่ Google Cloud Console: https://console.cloud.google.com/
   
2. สร้าง Project ใหม่ (หรือใช้ที่มีอยู่)

3. เปิด Google Drive API:
   - ไปที่ APIs & Services > Library
   - ค้นหา "Google Drive API"
   - กด Enable

4. สร้าง OAuth Credentials:
   - ไปที่ APIs & Services > Credentials
   - กด Create Credentials > OAuth client ID
   - เลือก Desktop app
   - ดาวน์โหลด JSON

5. ย้ายไฟล์ JSON มาที่นี่:
   """)
    print(f"   {CREDENTIALS_FILE}")
    print("""
6. รัน setup อีกครั้ง:
   python main_gdrive.py --setup

7. Browser จะเปิดให้ login Google Account
   - Allow access to Google Drive

8. เสร็จ! พร้อมใช้งาน 🎉
    """)


def setup_gdrive():
    """ตั้งค่า Google Drive ครั้งแรก"""
    print("🔧 Setting up Google Drive...")
    
    if not CREDENTIALS_FILE.exists():
        show_setup_guide()
        return False
    
    client = GoogleDriveClient()
    if client.connect():
        folders = client.setup_folders()
        print("\n✅ Setup สำเร็จ!")
        print("\n📁 Folder structure in Google Drive:")
        print("   AI_Video_Factory/")
        print("   ├── 1_Input_Raw/     (สำหรับ input videos)")
        print("   ├── 2_Assets/        (avatar, cookies)")
        print("   └── 3_Output_Ready/  (output videos)")
        print("\n📝 ใส่ urls.txt ใน AI_Video_Factory/ ใน Drive ของคุณ")
        print("   แล้วรัน: python main_gdrive.py")
        return True
    
    return False


def process_single_video_gdrive(url: str, index: int, total: int, gdrive: GoogleDriveClient, output_folder_id: str) -> bool:
    """Process วิดีโอ 1 คลิป แล้ว upload ไป Drive"""
    print(f"\n{'='*60}")
    print(f"[{index}/{total}] : {url}")
    print(f"{'='*60}")
    
    reset_model_fallback()
    
    # Step 1: Download to temp
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    video_path = download_single_video(url, TEMP_DIR)
    if not video_path:
        print("Download Failed")
        return False
    
    try:
        # Get video duration
        from moviepy.editor import VideoFileClip
        clip = VideoFileClip(video_path)
        duration = clip.duration
        clip.close()
        
        # Step 2: Generate Script (AI)
        title, script = get_perfect_fit_script(video_path, duration)
        
        # ตรวจสอบว่า script ไม่ว่าง
        if not script or len(script.strip()) < 10:
            print("    ❌ Script ว่างเปล่าหรือสั้นเกินไป - ข้ามคลิปนี้")
            print("       (อาจเป็นเพราะ API quota หมดทุก keys)")
            return False
        
        print(f"\n    Script ({len(script.split())} คำ): {script[:80]}...\n")
        
        # Step 3: Generate Voice
        voice_path = str(TEMP_DIR / "temp_voice.mp3")
        generate_voice_sync(script, voice_path)
        
        # ตรวจสอบว่าไฟล์เสียงถูกสร้างและมีขนาด
        if not Path(voice_path).exists() or Path(voice_path).stat().st_size < 1000:
            print("    ❌ ไม่สามารถสร้างไฟล์เสียงได้ - ข้ามคลิปนี้")
            return False
        
        # Step 4: Process Video - output ไปที่ TEMP_DIR
        from modules.video_processor import (
            resize_for_shorts, sync_audio_to_video, render_final_video,
            prepare_avatar_with_chromakey
        )
        from moviepy.editor import AudioFileClip
        
        source_clip = VideoFileClip(video_path)
        audio_clip = AudioFileClip(voice_path)
        
        # Sync audio
        synced_audio = sync_audio_to_video(audio_clip, duration)
        synced_audio_path = TEMP_DIR / "synced_audio.mp3"
        synced_audio.write_audiofile(str(synced_audio_path), logger=None)
        final_audio = AudioFileClip(str(synced_audio_path))
        
        # Resize video
        resized_clip = resize_for_shorts(source_clip)
        
        # Prepare avatar
        has_avatar = prepare_avatar_with_chromakey(duration)
        
        # Output to TEMP (not OUTPUT_DIR)
        safe_title = sanitize_filename(title) or f"Clip_{int(time.time())}"
        output_path = TEMP_DIR / f"{safe_title}.mp4"
        
        # Render
        result = render_final_video(resized_clip, final_audio, output_path, add_avatar=has_avatar)
        
        # Cleanup clips
        source_clip.close()
        audio_clip.close()
        final_audio.close()
        
        if result and os.path.exists(result):
            # Step 5: Upload to Google Drive
            print("    ☁️ Uploading to Google Drive...")
            gdrive.upload_file(result, output_folder_id)
            
            # Delete local output after upload
            os.remove(result)
            print("    ✅ Upload สำเร็จ + ลบไฟล์ local แล้ว")
            
            return True
        else:
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Cleanup temp files
        temp_files = [
            video_path, 
            str(TEMP_DIR / "temp_voice.mp3"),
            str(TEMP_DIR / "synced_audio.mp3"),
        ]
        for f in temp_files:
            try:
                if os.path.exists(f):
                    os.remove(f)
            except:
                pass


def run_factory_gdrive():
    """รัน factory กับ Google Drive"""
    ensure_directories()
    
    # Check Google Drive
    if not is_gdrive_available():
        print("Google Drive not configured. Run with --setup first")
        return
    
    gdrive = GoogleDriveClient()
    if not gdrive.connect():
        return
    
    folders = gdrive.setup_folders()
    
    # Download Avatar จาก Drive ถ้ามี
    avatar_file_id = gdrive.find_file("avatar_talking.mp4", folders['assets'])
    if avatar_file_id:
        from config.settings import ASSETS_DIR
        ASSETS_DIR.mkdir(parents=True, exist_ok=True)
        local_avatar = ASSETS_DIR / "avatar_talking.mp4"
        if not local_avatar.exists():
            print("📥 กำลังดาวน์โหลด Avatar จาก Drive...")
            gdrive.download_file(avatar_file_id, str(local_avatar))
            print("✅ ดาวน์โหลด Avatar สำเร็จ")
        else:
            print("✅ Avatar พร้อมใช้งาน")
    
    # Test API keys
    try:
        test_api_keys()
    except ValueError as e:
        print(f"\n{e}")
        return
    
    # Get URLs from Drive
    urls = gdrive.read_urls_file(folders['main'])
    
    if not urls:
        print("\nNo URLs found in urls.txt on Google Drive")
        print("   Upload urls.txt to AI_Video_Factory/ folder")
        return
    
    print(f"\nProcessing {len(urls)} videos")
    print(f"Models: {', '.join(MODEL_HIERARCHY)}")
    print(f"API Keys: {len(available_keys)}\n")
    
    success_count = 0
    fail_count = 0
    remaining_urls = urls.copy()
    
    for i, url in enumerate(urls, 1):
        if process_single_video_gdrive(url, i, len(urls), gdrive, folders['output']):
            success_count += 1
            remaining_urls.remove(url)
            # Update urls.txt on Drive (remove processed)
            gdrive.update_urls_file(remaining_urls, folders['main'])
        else:
            fail_count += 1
        
        # Delay between clips
        if i < len(urls):
            print(f"\n    Wait {DELAY_BETWEEN_CLIPS}s...")
            time.sleep(DELAY_BETWEEN_CLIPS)
    
    # Cleanup local temp
    cleanup_temp_files()
    
    # Summary
    print(f"\n{'='*60}")
    print(f"Done!")
    print(f"   Success: {success_count}")
    print(f"   Failed: {fail_count}")
    print(f"   Output: Google Drive > AI_Video_Factory > 3_Output_Ready")
    print(f"{'='*60}")


# =============================================================================
# 🚀 CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="AI Video Factory - Google Drive Cloud Mode",
    )
    
    parser.add_argument(
        '--setup', '-s',
        action='store_true',
        help='Setup Google Drive'
    )
    parser.add_argument(
        '--test', '-t',
        action='store_true',
        help='Test API keys'
    )
    
    args = parser.parse_args()
    
    show_banner()
    
    if args.setup:
        setup_gdrive()
        return
    
    if args.test:
        ensure_directories()
        try:
            test_api_keys()
            print("\nAPI Keys OK!")
        except ValueError as e:
            print(f"\n{e}")
        return
    
    # Run factory
    run_factory_gdrive()


if __name__ == "__main__":
    main()
