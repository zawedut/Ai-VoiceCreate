# =============================================================================
# 🧠 GEMINI BRAIN MODULE - AI Script Generation
# =============================================================================
# Gemini API สำหรับสร้างบทพากย์

import os
import re
import time
import random
import requests
import google.generativeai as genai
from google.api_core import retry
from pathlib import Path

from config.settings import (
    API_KEYS, MODEL_HIERARCHY, 
    WORDS_PER_SECOND, SYNC_TOLERANCE,
    MAX_UPLOAD_ATTEMPTS, MAX_SCRIPT_ATTEMPTS, ATTEMPTS_PER_MODEL,
    TEMP_DIR
)
from modules.voice import get_audio_duration

__all__ = [
    'test_api_keys',
    'get_perfect_fit_script',
    'clean_script_final',
    'AIBrain',
]

# =============================================================================
# 🔧 GLOBAL STATE
# =============================================================================
available_keys = []
current_key_index = 0
current_model_index = 0

# =============================================================================
# 🔑 API KEY MANAGEMENT
# =============================================================================

def configure_gemini(key: str) -> None:
    """ตั้งค่า Gemini API key"""
    genai.configure(api_key=key)


def test_api_keys() -> list:
    """
    ทดสอบทุก API keys ก่อนรันจริง
    
    Returns:
        list ของ keys ที่ทำงานได้
    """
    global available_keys
    print("🔍 กำลังทดสอบ API Keys...")
    
    test_prompt = "พูดว่า 'สวัสดี' เป็นภาษาไทย"
    test_model = MODEL_HIERARCHY[0]
    working_keys = []
    
    for idx, key in enumerate(API_KEYS):
        try:
            configure_gemini(key)
            model = genai.GenerativeModel(test_model)
            response = model.generate_content(test_prompt)
            if response.text:
                working_keys.append(key)
                print(f"    ✅ Key {idx+1} ทำงานได้")
        except Exception as e:
            error_msg = str(e).lower()
            print(f"    ❌ Key {idx+1} ล้มเหลว")
            if "quota" in error_msg:
                print("       └─ Quota หมด")
            elif "invalid" in error_msg:
                print("       └─ Key ไม่ถูกต้อง")
    
    available_keys = working_keys
    
    if not available_keys:
        raise ValueError("❌ ไม่มี Gemini API Key ที่ใช้งานได้!")
    else:
        print(f"✅ มี {len(available_keys)} keys พร้อมใช้งาน")
    
    return available_keys


def rotate_key() -> None:
    """สลับไปใช้ key ถัดไป"""
    global current_key_index
    if not available_keys:
        return
    current_key_index = (current_key_index + 1) % len(available_keys)
    print(f"    🔄 สลับ Key -> {current_key_index + 1}")
    configure_gemini(available_keys[current_key_index])


# =============================================================================
# 🤖 MODEL MANAGEMENT
# =============================================================================

def get_next_model() -> str:
    """เปลี่ยนไป Model ถัดไปใน hierarchy"""
    global current_model_index
    current_model_index = (current_model_index + 1) % len(MODEL_HIERARCHY)
    return MODEL_HIERARCHY[current_model_index]


def reset_model_fallback() -> None:
    """รีเซ็ตกลับไปใช้ Model เก่งสุด"""
    global current_model_index
    current_model_index = 0


# =============================================================================
# 📝 SCRIPT UTILITIES
# =============================================================================

def clean_script_final(text: str) -> str:
    """ทำความสะอาดบทพากย์"""
    # ลบ markdown formatting
    text = re.sub(r'\*\*', '', text)
    text = re.sub(r'\[.*?\]', '', text)
    
    # ลบคำที่ไม่ต้องการ
    bad_words = [
        "สวัสดีครับ", "สวัสดีค่ะ",
        "คลิปนี้", "วิดีโอนี้", 
        "ท่านผู้ชม", "เพื่อนๆ",
        "มาดูกัน", "ไปดูกันเลย"
    ]
    for word in bad_words:
        text = text.replace(word, "")
    
    # ทำความสะอาด whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


# =============================================================================
# 📤 VIDEO UPLOAD
# =============================================================================

def upload_to_gemini(path: str, max_attempts: int = None) -> object:
    """
    Upload video ไปยัง Gemini พร้อม retry logic
    
    Args:
        path: path ของไฟล์วิดีโอ
        max_attempts: จำนวนครั้งที่ลองใหม่
        
    Returns:
        Gemini File object
    """
    if max_attempts is None:
        max_attempts = MAX_UPLOAD_ATTEMPTS
    
    attempt = 0
    while attempt < max_attempts:
        try:
            print(f"       📤 Uploading... ({attempt+1}/{max_attempts})")
            file = genai.upload_file(path, mime_type="video/mp4")
            
            # Poll จนกว่าจะ process เสร็จ
            start_time = time.time()
            while file.state.name == "PROCESSING":
                elapsed = time.time() - start_time
                if elapsed > 600:  # 10 นาที timeout
                    raise TimeoutError("Video processing timeout")
                
                sleep_time = 4 + random.uniform(0, 3)
                print(f"       ⏳ Processing... ({elapsed:.0f}s)")
                time.sleep(sleep_time)
                
                @retry.Retry(predicate=retry.if_transient_error, initial=2, maximum=30, multiplier=1.5)
                def safe_get_file(name):
                    return genai.get_file(name)
                
                file = safe_get_file(file.name)
            
            if file.state.name == "FAILED":
                raise ValueError("Upload Failed - Gemini processing error")
            
            print("       ✅ Upload สำเร็จ!")
            return file
            
        except (ConnectionResetError, ConnectionError, requests.exceptions.ConnectionError, TimeoutError) as e:
            print(f"       ⚠️ Connection issue: {str(e)[:60]}")
            attempt += 1
            delay = (2 ** attempt) + random.uniform(0, 3)
            print(f"       ⏳ รอ {delay:.1f}s แล้วลองใหม่...")
            time.sleep(delay)
            
        except Exception as e:
            print(f"       ❌ Error: {str(e)[:80]}")
            raise
    
    raise RuntimeError(f"Upload ล้มเหลวหลังจากลอง {max_attempts} ครั้ง")




# =============================================================================
# 🧠 MAIN SCRIPT GENERATION
# =============================================================================

def get_perfect_fit_script(video_path: str, duration: float) -> tuple:
    """
    สร้างบทพากย์ที่ความยาวพอดีกับวิดีโอ
    
    ใช้ Gemini AI + Calibration loop เพื่อปรับความยาวให้ตรง
    
    Args:
        video_path: path ของวิดีโอ
        duration: ความยาวเป้าหมาย (วินาที)
        
    Returns:
        (title, script) tuple
    """
    global current_model_index
    
    print(f"    🧠 AI: กำลังวิเคราะห์วิดีโอ (Target: {duration:.2f}s)...")
    
    # ตรวจสอบว่ามี Gemini keys
    if not available_keys:
        raise RuntimeError("ไม่มี Gemini API Key ที่ใช้งานได้")
    
    # Configure Gemini
    configure_gemini(available_keys[current_key_index])
    
    # Upload video
    video_file = upload_to_gemini(video_path)
    
    # Calculate target words - ปรับให้แม่นยำขึ้น
    # Thai speech at +5% rate ≈ 2.4 words/sec, but shorter words = faster
    target_words = int(duration * 2.2)  # ลดลงนิดเพราะคำไทยสั้นกว่า
    min_words = int(duration * 2.0)
    max_words = int(duration * 2.5)
    
    # Initial prompt - เน้นจำนวนคำให้ชัดเจน
    initial_prompt = f"""คุณคือนักพากย์มืออาชีพ ต้องพากย์คลิปนี้ให้พอดี {duration:.0f} วินาที

📏 **ข้อกำหนดความยาว (สำคัญมาก!):**
- เป้าหมาย: {target_words} คำ (ต่ำสุด {min_words}, สูงสุด {max_words})
- พูด 2.2 คำ/วินาที (ไม่เร็วไป ไม่ช้าไป)
- ถ้าคำน้อยกว่า {min_words} = บทสั้นเกิน
- ถ้าคำเกิน {max_words} = บทยาวเกิน

📝 **กฎการเขียน:**
1. ดูวิดีโอแล้วบรรยายสิ่งที่เห็นตามลำดับเวลา
2. ใช้ประโยคสั้นๆ มีจุด จุลภาค สร้างจังหวะหายใจ
3. ห้ามใช้: "สวัสดีครับ", "คลิปนี้", "วิดีโอนี้", "เพื่อนๆ"
4. เขียนให้เป็นธรรมชาติ เหมือนเล่าเรื่องให้เพื่อนฟัง

📤 **Output Format:**
ชื่อคลิป: [ชื่อสั้นๆ 3-5 คำ]
บท: [บทพากย์ต่อเนื่องในย่อหน้าเดียว ประมาณ {target_words} คำ]"""

    final_script = ""
    final_title = "คลิปเด็ด"
    current_model = MODEL_HIERARCHY[current_model_index]
    chat = None
    
    # เก็บผลลัพธ์สำหรับ calibration
    all_results = []  # [(title, script, audio_len, word_count)]
    
    # Calibration Loop - ใช้ผลรอบก่อนมาปรับจำนวนคำ
    for attempt in range(MAX_SCRIPT_ATTEMPTS):
        try:
            # สร้าง/ใช้ chat session
            if chat is None:
                print(f"       🤖 ใช้ {current_model}")
                model = genai.GenerativeModel(current_model)
                chat = model.start_chat(history=[])
            
            # คำนวณ target words จากผลรอบก่อน
            if attempt == 0:
                # รอบแรก - ใช้ค่าประมาณ
                current_target_words = target_words
            else:
                # รอบถัดไป - คำนวณจากผลลัพธ์ก่อนหน้า
                prev_title, prev_script, prev_audio_len, prev_word_count = all_results[-1]
                
                # คำนวณ words per second จริงจากรอบก่อน
                actual_wps = prev_word_count / prev_audio_len if prev_audio_len > 0 else 2.2
                
                # คำนวณจำนวนคำที่ต้องการจริงๆ
                current_target_words = int(duration * actual_wps)
                
                # ปรับตามส่วนต่าง
                diff_seconds = duration - prev_audio_len
                word_adjustment = int(diff_seconds * actual_wps)
                current_target_words = prev_word_count + word_adjustment
                
                print(f"       📊 Calibration: {prev_word_count} คำ = {prev_audio_len:.1f}s, ต้องการอีก {word_adjustment:+d} คำ")
            
            # สร้าง prompt ที่ระบุจำนวนคำชัดเจน
            if attempt == 0:
                prompt = f"""ดูวิดีโอนี้แล้วเขียนบทพากย์ภาษาไทย ความยาว {duration:.0f} วินาที

สำคัญมาก: ต้องเขียนประมาณ {current_target_words} คำ

กฎ:
- บรรยายสิ่งที่เห็นในวิดีโอตามลำดับเวลา
- เขียนต่อเนื่องเป็นย่อหน้าเดียว
- ใช้ภาษาเป็นธรรมชาติ เหมือนเล่าเรื่องให้เพื่อนฟัง
- ห้ามขึ้นต้นว่า "สวัสดี"

ตอบในรูปแบบ:
ชื่อ: [ชื่อคลิปสั้นๆ]
---
[บทพากย์ยาวๆ ประมาณ {current_target_words} คำ ที่นี่]"""
                response = chat.send_message([video_file, prompt])
            else:
                prompt = f"""บทที่แล้วสั้นไป ได้แค่ {prev_audio_len:.0f} วินาที (ต้องการ {duration:.0f} วินาที)

เขียนบทใหม่ให้ยาวขึ้น ต้องมีประมาณ {current_target_words} คำ

บรรยายทุกฉากในวิดีโอ เพิ่มรายละเอียดเกี่ยวกับ:
- สิ่งที่เกิดขึ้นในแต่ละช่วงเวลา
- อารมณ์ ความรู้สึก
- รายละเอียดของวัตถุและบุคคล

ตอบเป็นบทพากย์เพียงอย่างเดียว ไม่ต้องมี label:"""
                response = chat.send_message(prompt)
            
            text = response.text.strip()
            
            # Parse response - ปรับปรุงให้ดีขึ้น
            current_title = "คลิปเด็ด"
            current_script = ""
            
            # แยกชื่อและบท
            if "---" in text:
                parts = text.split("---", 1)
                header = parts[0].strip()
                current_script = parts[1].strip() if len(parts) > 1 else ""
                # หาชื่อจาก header
                for line in header.split('\n'):
                    if line.strip().startswith("ชื่อ"):
                        current_title = re.sub(r'^ชื่อ[คลิป]*:', '', line).strip()
            else:
                # ลองหา pattern อื่น
                lines = [l.strip() for l in text.split('\n') if l.strip()]
                for i, line in enumerate(lines):
                    if line.startswith("ชื่อ") and ":" in line:
                        current_title = line.split(":", 1)[1].strip()
                    elif line.startswith("บท") and ":" in line:
                        current_script = line.split(":", 1)[1].strip()
                        # รวมบรรทัดถัดไปด้วย
                        current_script += " " + " ".join(lines[i+1:])
                        break
                
                # ถ้ายังไม่มี script ให้ใช้ทั้งหมดยกเว้นบรรทัดแรก
                if not current_script and len(lines) > 1:
                    current_script = " ".join(lines[1:])
                elif not current_script:
                    current_script = text
            
            current_script = clean_script_final(current_script)
            
            # นับคำและวัดเสียง
            word_count = len(current_script.split())
            audio_len = get_audio_duration(current_script)
            diff = duration - audio_len
            
            print(f"       >> รอบ {attempt+1}: {word_count} คำ = {audio_len:.2f}s | เป้า {duration:.2f}s | ต่าง {diff:+.2f}s")
            
            # เก็บผลลัพธ์
            all_results.append((current_title, current_script, audio_len, word_count))
            
            # ถ้าใกล้เคียงมาก (ต่าง < 3 วิ) หยุดเลย
            if abs(diff) <= 3.0:
                print("       ✅ บทใกล้เคียงมาก! ใช้เลย")
                final_script = current_script
                final_title = current_title
                break
                
        except Exception as e:
            error_msg = str(e)
            print(f"    ⚠️ Error: {error_msg[:80]}")
            
            if "429" in error_msg or "quota" in error_msg.lower():
                print("       🚨 Rate Limit! สลับ Key")
                rotate_key()
                chat = None
                time.sleep(2)
            elif "404" in error_msg or "not found" in error_msg.lower():
                print(f"       💀 Model {current_model} ไม่พร้อมใช้งาน")
                current_model = get_next_model()
                chat = None
            else:
                time.sleep(1)
    
    # เลือกผลลัพธ์ที่ดีที่สุด (ใกล้เคียง duration มากที่สุด)
    if all_results and not final_script:
        # sort by diff (ascending) - เอาอันที่ใกล้เคียงที่สุด
        all_results.sort(key=lambda x: abs(duration - x[2]))
        best = all_results[0]
        final_title, final_script, best_len, best_words = best
        print(f"       ✅ เลือกบทที่ดีที่สุด: {best_words} คำ = {best_len:.1f}s (ต่าง {duration - best_len:+.1f}s)")
    
    # Cleanup
    try:
        genai.delete_file(video_file.name)
    except:
        pass
    
    return final_title, final_script


# =============================================================================
# 🎯 AI BRAIN CLASS (Alternative OOP Interface)
# =============================================================================

class AIBrain:
    """Object-oriented wrapper สำหรับ AI functions"""
    
    def __init__(self):
        self.keys = []
        self.current_key_idx = 0
        self.current_model_idx = 0
        self.initialized = False
    
    def initialize(self) -> bool:
        """ทดสอบและเตรียม AI"""
        self.keys = test_api_keys()
        self.initialized = True
        return len(self.keys) > 0
    
    def generate_script(self, video_path: str, duration: float) -> tuple:
        """สร้างบทพากย์"""
        if not self.initialized:
            self.initialize()
        return get_perfect_fit_script(video_path, duration)
    
    @property
    def status(self) -> dict:
        """สถานะปัจจุบัน"""
        return {
            "gemini_keys": len(available_keys),
            "current_model": MODEL_HIERARCHY[current_model_index],
        }
