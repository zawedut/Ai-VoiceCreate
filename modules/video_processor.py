# =============================================================================
# 🎬 VIDEO PROCESSOR MODULE
# =============================================================================
# ประมวลผลวิดีโอ: resize, crop, overlay avatar, sync audio

import os
import subprocess
import time
import shutil
from pathlib import Path
from moviepy.editor import (
    VideoFileClip, AudioFileClip, CompositeVideoClip,
    concatenate_audioclips, AudioClip
)

from config.settings import (
    AVATAR_FILE, AVATAR_LOOPED_TEMP, AVATAR_CHROMA_TEMP,
    OUTPUT_DIR, TEMP_DIR,
    VIDEO_WIDTH, VIDEO_HEIGHT, VIDEO_FPS, VIDEO_BITRATE, VIDEO_PRESET
)
from modules.downloader import sanitize_filename

__all__ = [
    'prepare_avatar_with_chromakey',
    'sync_audio_to_video',
    'render_final_video',
    'process_video_pipeline',
    'resize_for_shorts',
    'cleanup_temp_files',
]

# =============================================================================
# 🔧 FFMPEG HELPER
# =============================================================================

def get_ffmpeg_path() -> str:
    """หา path ของ ffmpeg (รองรับ winget installation)"""
    # 1. ลองหาจาก PATH ปกติ
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg:
        return ffmpeg
    
    # 2. ลองหาจาก winget installation paths
    possible_paths = [
        r"C:\Users\Admin\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.0.1-full_build\bin\ffmpeg.exe",
        r"C:\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
    ]
    
    for path in possible_paths:
        if Path(path).exists():
            return path
    
    # 3. ลองหาจาก winget packages folder
    winget_packages = Path(r"C:\Users\Admin\AppData\Local\Microsoft\WinGet\Packages")
    if winget_packages.exists():
        for folder in winget_packages.iterdir():
            if "ffmpeg" in folder.name.lower():
                ffmpeg_exe = folder / "ffmpeg-8.0.1-full_build" / "bin" / "ffmpeg.exe"
                if ffmpeg_exe.exists():
                    return str(ffmpeg_exe)
                # ลองหาแบบ recursive
                for exe in folder.rglob("ffmpeg.exe"):
                    return str(exe)
    
    return "ffmpeg"  # ใช้ค่า default ถ้าหาไม่เจอ

FFMPEG_PATH = get_ffmpeg_path()

# =============================================================================
# 👤 AVATAR PROCESSING
# =============================================================================

def prepare_avatar_with_chromakey(duration_needed: float) -> bool:
    """
    เตรียม Avatar โดย loop และลบ green screen
    
    Args:
        duration_needed: ความยาวที่ต้องการ (วินาที)
        
    Returns:
        True ถ้าสำเร็จ, False ถ้าไม่มี avatar หรือ error
    """
    if not AVATAR_FILE.exists():
        print("    ⚠️ ไม่พบไฟล์ Avatar")
        return False
    
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    safe_duration = duration_needed + 2  # เผื่อไว้
    
    try:
        # Step 1: Loop video ให้ยาวพอ
        subprocess.run([
            FFMPEG_PATH, "-y",
            "-stream_loop", "-1",
            "-i", str(AVATAR_FILE),
            "-t", str(safe_duration),
            "-vf", "fps=30",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-an",
            str(AVATAR_LOOPED_TEMP)
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Step 2: Chromakey ลบ green screen
        subprocess.run([
            FFMPEG_PATH, "-y",
            "-i", str(AVATAR_LOOPED_TEMP),
            "-filter_complex", "[0:v]chromakey=0x00FF00:0.33:0.05,scale=700:-1[out]",
            "-map", "[out]",
            "-c:v", "qtrle",
            "-pix_fmt", "argb",
            str(AVATAR_CHROMA_TEMP)
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        print("    ✅ เตรียม Avatar สำเร็จ")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"    ⚠️ Avatar processing error: {e}")
        return False
    except FileNotFoundError:
        print(f"    ⚠️ ไม่พบ ffmpeg ที่ {FFMPEG_PATH}")
        return False


# =============================================================================
# 🔊 AUDIO SYNC
# =============================================================================

def sync_audio_to_video(audio_clip: AudioFileClip, target_duration: float) -> AudioFileClip:
    """
    ปรับความยาวเสียงให้ตรงกับวิดีโอ
    
    - ถ้าเสียงสั้นกว่า: เติม silence ท้าย
    - ถ้าเสียงยาวกว่า: ตัดและ fade out
    
    Args:
        audio_clip: AudioFileClip
        target_duration: ความยาวเป้าหมาย
        
    Returns:
        AudioFileClip ที่ปรับแล้ว
    """
    audio_duration = audio_clip.duration
    diff = target_duration - audio_duration
    
    if abs(diff) <= 0.5:
        # ต่างนิดเดียว ใช้ได้เลย
        if diff > 0:
            silence = AudioClip(lambda t: 0, duration=diff)
            return concatenate_audioclips([audio_clip, silence])
        else:
            return audio_clip.subclip(0, target_duration).audio_fadeout(0.3)
    
    elif diff > 0.5:
        # เสียงสั้นกว่า - เติม silence
        print(f"       ⚠️ เสียงสั้นกว่า {diff:.2f}s, เติม silence...")
        silence = AudioClip(lambda t: 0, duration=diff)
        return concatenate_audioclips([audio_clip, silence])
    
    else:
        # เสียงยาวกว่า - ตัด
        print(f"       ⚠️ เสียงยาวกว่า {-diff:.2f}s, ตัด...")
        return audio_clip.subclip(0, target_duration).audio_fadeout(0.5)


# =============================================================================
# 🎥 VIDEO RENDERING
# =============================================================================

def resize_for_shorts(clip: VideoFileClip) -> VideoFileClip:
    """Resize & crop วิดีโอให้เป็น 9:16 (1080x1920)"""
    clip = clip.resize(height=VIDEO_HEIGHT)
    
    if clip.w > VIDEO_WIDTH:
        # Crop center
        x_center = clip.w / 2
        clip = clip.crop(
            x1=x_center - VIDEO_WIDTH/2,
            width=VIDEO_WIDTH,
            height=VIDEO_HEIGHT
        )
    else:
        # Resize width and crop height
        clip = clip.resize(width=VIDEO_WIDTH)
        y_center = clip.h / 2
        clip = clip.crop(
            y1=y_center - VIDEO_HEIGHT/2,
            width=VIDEO_WIDTH,
            height=VIDEO_HEIGHT
        )
    
    return clip


def render_final_video(
    video_clip: VideoFileClip,
    audio_clip: AudioFileClip,
    output_path: Path,
    add_avatar: bool = True
) -> str:
    """
    Render วิดีโอสุดท้าย
    
    Args:
        video_clip: Video ที่ resize แล้ว
        audio_clip: Audio ที่ sync แล้ว
        output_path: Path output
        add_avatar: ใส่ Avatar หรือไม่
        
    Returns:
        Path ของไฟล์ output
    """
    duration = video_clip.duration
    
    # Combine video + audio
    final_clip = video_clip.without_audio().set_audio(audio_clip).set_duration(duration)
    
    # Layers
    layers = [final_clip]
    
    # Add Avatar overlay
    if add_avatar and AVATAR_CHROMA_TEMP.exists():
        try:
            avatar = VideoFileClip(str(AVATAR_CHROMA_TEMP), has_mask=True)
            if avatar.duration < duration:
                avatar = avatar.loop(n=int(duration/avatar.duration) + 1)
            avatar = avatar.subclip(0, duration).set_position(("center", "bottom"))
            layers.append(avatar)
        except Exception as e:
            print(f"    ⚠️ Avatar overlay error: {e}")
    
    # Composite & export
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    composite = CompositeVideoClip(layers, size=(VIDEO_WIDTH, VIDEO_HEIGHT))
    composite = composite.set_duration(duration)
    
    composite.write_videofile(
        str(output_path),
        fps=VIDEO_FPS,
        codec='libx264',
        audio_codec='aac',
        bitrate=VIDEO_BITRATE,
        preset=VIDEO_PRESET,
        threads=4,
        logger='bar'
    )
    
    return str(output_path)


# =============================================================================
# 🏭 MAIN PIPELINE
# =============================================================================

def process_video_pipeline(
    video_path: str,
    script: str,
    title: str,
    voice_path: str
) -> str | None:
    """
    Pipeline หลักสำหรับ process วิดีโอ
    
    Args:
        video_path: Path ของวิดีโอต้นฉบับ
        script: บทพากย์
        title: ชื่อคลิป
        voice_path: Path ของไฟล์เสียงพากย์
        
    Returns:
        Path ของไฟล์ output หรือ None ถ้า error
    """
    clips_to_close = []
    temp_files = []
    
    try:
        # Load source video
        source_clip = VideoFileClip(video_path)
        clips_to_close.append(source_clip)
        original_duration = source_clip.duration
        
        print(f"    🎬 Processing: {original_duration:.2f}s")
        
        # Load audio
        audio_clip = AudioFileClip(voice_path)
        clips_to_close.append(audio_clip)
        
        # Sync audio
        synced_audio = sync_audio_to_video(audio_clip, original_duration)
        
        # Save synced audio
        TEMP_DIR.mkdir(parents=True, exist_ok=True)
        synced_audio_path = TEMP_DIR / "synced_audio.mp3"
        synced_audio.write_audiofile(str(synced_audio_path), logger=None)
        temp_files.append(synced_audio_path)
        
        # Reload synced audio
        final_audio = AudioFileClip(str(synced_audio_path))
        clips_to_close.append(final_audio)
        
        # Resize video
        resized_clip = resize_for_shorts(source_clip)
        
        # Prepare avatar
        has_avatar = prepare_avatar_with_chromakey(original_duration)
        
        # Generate output filename
        safe_title = sanitize_filename(title) or f"Clip_{int(time.time())}"
        output_path = OUTPUT_DIR / f"{safe_title}.mp4"
        
        # Handle duplicate names
        counter = 1
        while output_path.exists():
            output_path = OUTPUT_DIR / f"{safe_title}_{counter}.mp4"
            counter += 1
        
        # Render
        result = render_final_video(
            resized_clip,
            final_audio,
            output_path,
            add_avatar=has_avatar
        )
        
        print(f"    ✅ Output: {output_path.name}")
        return result
        
    except Exception as e:
        print(f"    ❌ Processing Error: {e}")
        import traceback
        traceback.print_exc()
        return None
        
    finally:
        # Cleanup
        for clip in clips_to_close:
            try:
                clip.close()
            except:
                pass
        
        for f in temp_files:
            try:
                if Path(f).exists():
                    os.remove(f)
            except:
                pass


def cleanup_temp_files():
    """ลบไฟล์ temp ทั้งหมด"""
    temp_files = [
        AVATAR_LOOPED_TEMP,
        AVATAR_CHROMA_TEMP,
        TEMP_DIR / "synced_audio.mp3",
        TEMP_DIR / "temp_measure.mp3",
        TEMP_DIR / "frame_preview.jpg",
    ]
    
    for f in temp_files:
        try:
            if Path(f).exists():
                os.remove(f)
        except:
            pass
