# =============================================================================
# 🎤 VOICE MODULE
# =============================================================================
# สร้างเสียงพากย์ด้วย Edge TTS

import os
import asyncio
import edge_tts
from pathlib import Path
from moviepy.editor import AudioFileClip

from config.settings import (
    VOICE_NAME, VOICE_RATE, VOICE_PITCH, VOICE_VOLUME, TEMP_DIR
)

__all__ = [
    'generate_voice',
    'generate_voice_sync',
    'get_audio_duration',
]

# =============================================================================
# 🎤 VOICE GENERATION
# =============================================================================

async def generate_voice(text: str, output_path: str) -> str:
    """
    สร้างเสียงพากย์ด้วย Edge TTS (async)
    
    Settings ปรับให้เป็นธรรมชาติ:
    - Rate: +5% (เร็วพอดี ไม่เร่งเกิน)
    - Pitch: +3Hz (เสียงมีชีวิตชีวา)
    - Volume: +10% (ชัดเจน)
    
    Args:
        text: บทพากย์
        output_path: path ไฟล์ output (mp3)
        
    Returns:
        path ของไฟล์เสียง
    """
    communicate = edge_tts.Communicate(
        text,
        VOICE_NAME,
        rate=VOICE_RATE,
        pitch=VOICE_PITCH,
        volume=VOICE_VOLUME
    )
    await communicate.save(output_path)
    return output_path


def generate_voice_sync(text: str, output_path: str) -> str:
    """Sync wrapper สำหรับ generate_voice"""
    return asyncio.run(generate_voice(text, output_path))


# =============================================================================
# ⏱️ AUDIO DURATION
# =============================================================================

def get_audio_duration(text: str) -> float:
    """
    สร้างเสียงชั่วคราวเพื่อวัดความยาวจริง
    
    Args:
        text: บทพากย์
        
    Returns:
        ความยาวเสียงเป็นวินาที
    """
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    temp_file = TEMP_DIR / "temp_measure.mp3"
    
    try:
        asyncio.run(generate_voice(text, str(temp_file)))
        audio = AudioFileClip(str(temp_file))
        duration = audio.duration
        audio.close()
        return duration
    except Exception as e:
        print(f"    ⚠️ Error measuring audio: {e}")
        return 0.0
    finally:
        if temp_file.exists():
            os.remove(temp_file)


def estimate_duration(text: str, words_per_second: float = 2.4) -> float:
    """ประมาณความยาวจากจำนวนคำ (ไม่ต้องสร้างเสียง)"""
    words = len(text.split())
    return words / words_per_second
