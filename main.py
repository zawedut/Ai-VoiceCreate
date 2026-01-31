#!/usr/bin/env python3
# =============================================================================
# 🎬 AI VIDEO FACTORY - MAIN ENTRY POINT
# =============================================================================
# กดรันทีเดียว ทำให้หมด! แค่ใส่ลิงก์ YouTube ใน urls.txt
#
# Usage:
#   python main.py              # รัน factory เต็ม pipeline
#   python main.py --add-urls   # เพิ่ม URLs แล้วรัน
#   python main.py --test       # ทดสอบ API keys
#   python main.py --status     # ดู config status

import sys
import argparse
import asyncio
import nest_asyncio

# Apply nest_asyncio for Jupyter/async compatibility
nest_asyncio.apply()

from config.settings import (
    ensure_directories, get_config_summary,
    URL_FILE, OUTPUT_DIR, DELAY_BETWEEN_CLIPS
)
from modules.downloader import (
    get_urls, remove_url_from_file, add_urls_to_file, 
    download_single_video
)
from modules.gemini_brain import (
    test_api_keys, get_perfect_fit_script, reset_model_fallback,
    available_keys, MODEL_HIERARCHY
)
from modules.voice import generate_voice_sync
from modules.video_processor import process_video_pipeline, cleanup_temp_files

import time
import os

# =============================================================================
# 🎯 MAIN FUNCTIONS
# =============================================================================

def show_banner():
    """แสดง banner เริ่มต้น"""
    print("""
╔═══════════════════════════════════════════════════════════════╗
║                   🎬 AI VIDEO FACTORY 🎬                      ║
║               Auto Voice-Over + Perfect Sync                  ║
╚═══════════════════════════════════════════════════════════════╝
    """)


def show_status():
    """แสดงสถานะ config"""
    config = get_config_summary()
    print("\n📊 Current Configuration:")
    print(f"   📁 Base Dir: {config['base_dir']}")
    print(f"   🔑 Gemini Keys: {config['gemini_keys_count']}")
    print(f"   🎤 Voice: {config['voice']}")
    print(f"   🤖 Models: {', '.join(config['models'])}")
    print(f"   🎤 Voice: {config['voice']}")
    print()


def add_urls_interactive():
    """รับ URLs จาก user แบบ interactive"""
    print("\n📝 ใส่ลิงก์ YouTube/TikTok (บรรทัดละลิงก์)")
    print("   พิมพ์ 'done' เมื่อเสร็จ\n")
    
    urls = []
    while True:
        try:
            line = input("   URL: ").strip()
            if line.lower() == 'done':
                break
            if line and ('youtube' in line or 'youtu.be' in line or 'tiktok' in line):
                urls.append(line)
                print(f"   ✅ เพิ่มแล้ว ({len(urls)} URLs)")
            elif line:
                print("   ⚠️ ไม่ใช่ลิงก์ YouTube/TikTok")
        except EOFError:
            break
    
    if urls:
        add_urls_to_file(urls)
        print(f"\n✅ เพิ่ม {len(urls)} URLs สำเร็จ!")
    
    return urls


def process_single_video(url: str, index: int, total: int) -> bool:
    """
    Process วิดีโอ 1 คลิป (full pipeline)
    
    Returns:
        True ถ้าสำเร็จ
    """
    print(f"\n{'='*60}")
    print(f"📦 [{index}/{total}] : {url}")
    print(f"{'='*60}")
    
    # Reset model fallback ก่อนเริ่มคลิปใหม่
    reset_model_fallback()
    
    # Step 1: Download
    video_path = download_single_video(url)
    if not video_path:
        print("❌ Download Failed - ข้ามคลิปนี้")
        return False
    
    try:
        # Get video duration
        from moviepy.editor import VideoFileClip
        clip = VideoFileClip(video_path)
        duration = clip.duration
        clip.close()
        
        # Step 2: Generate Script (AI)
        title, script = get_perfect_fit_script(video_path, duration)
        
        print(f"\n    📜 บทพากย์:")
        print(f"    {script[:120]}{'...' if len(script) > 120 else ''}\n")
        
        # Step 3: Generate Voice
        voice_path = "temp_voice.mp3"
        generate_voice_sync(script, voice_path)
        
        # Step 4: Process Video (resize, sync, overlay)
        result = process_video_pipeline(video_path, script, title, voice_path)
        
        if result:
            # Success - remove from queue
            remove_url_from_file(url)
            return True
        else:
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Cleanup temp files
        for f in [video_path, "temp_voice.mp3"]:
            try:
                if os.path.exists(f):
                    os.remove(f)
            except:
                pass


def run_factory():
    """รัน factory เต็ม pipeline ทุก URLs ใน queue"""
    ensure_directories()
    
    # Test API keys ก่อน
    try:
        test_api_keys()
    except ValueError as e:
        print(f"\n❌ {e}")
        print("💡 กรุณาเพิ่ม API keys ใน .env file")
        return
    
    urls = get_urls()
    
    if not urls:
        print("\n📭 ไม่มี URLs ใน queue")
        print(f"   ใส่ลิงก์ใน: {URL_FILE}")
        print("   หรือรัน: python main.py --add-urls")
        return
    
    print(f"\n🔥 เริ่มประมวลผล {len(urls)} คลิป")
    print(f"🤖 Models: {', '.join(MODEL_HIERARCHY)}")
    print(f"🔑 API Keys: {len(available_keys)}")
    print(f"📂 Output: {OUTPUT_DIR}\n")
    
    success_count = 0
    fail_count = 0
    
    for i, url in enumerate(urls, 1):
        if process_single_video(url, i, len(urls)):
            success_count += 1
        else:
            fail_count += 1
        
        # พักระหว่างคลิป
        if i < len(urls):
            print(f"\n    ⏸️ พัก {DELAY_BETWEEN_CLIPS}วิ ก่อนคลิปถัดไป...")
            time.sleep(DELAY_BETWEEN_CLIPS)
    
    # Cleanup
    cleanup_temp_files()
    
    # Summary
    print(f"\n{'='*60}")
    print(f"🎉 จบงาน!")
    print(f"   ✅ สำเร็จ: {success_count} คลิป")
    print(f"   ❌ ล้มเหลว: {fail_count} คลิป")
    print(f"   📂 Output: {OUTPUT_DIR}")
    print(f"{'='*60}")


# =============================================================================
# 🚀 CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="🎬 AI Video Factory - Auto Voice-Over for YouTube/TikTok",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py              # รัน factory
  python main.py --add-urls   # เพิ่ม URLs ก่อนรัน
  python main.py --test       # ทดสอบ API keys
  python main.py --status     # ดู config
        """
    )
    
    parser.add_argument(
        '--add-urls', '-a',
        action='store_true',
        help='เพิ่ม URLs แบบ interactive ก่อนรัน'
    )
    parser.add_argument(
        '--test', '-t',
        action='store_true',
        help='ทดสอบ API keys เท่านั้น'
    )
    parser.add_argument(
        '--status', '-s',
        action='store_true',
        help='แสดง config status'
    )
    parser.add_argument(
        '--urls',
        nargs='+',
        help='ใส่ URLs โดยตรง (คั่นด้วย space)'
    )
    
    args = parser.parse_args()
    
    show_banner()
    
    if args.status:
        show_status()
        return
    
    if args.test:
        ensure_directories()
        try:
            test_api_keys()
            print("\n✅ API Keys พร้อมใช้งาน!")
        except ValueError as e:
            print(f"\n❌ {e}")
        return
    
    if args.urls:
        add_urls_to_file(args.urls)
        print(f"✅ เพิ่ม {len(args.urls)} URLs")
    
    if args.add_urls:
        add_urls_interactive()
    
    # Run factory
    run_factory()


if __name__ == "__main__":
    main()
