# =============================================================================
# 🧪 TESTS - Voice Module
# =============================================================================

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestDurationEstimation:
    """Test duration estimation functions"""
    
    def test_estimate_duration_basic(self):
        """ทดสอบประมาณการความยาว"""
        from modules.voice import estimate_duration
        
        # 24 คำ / 2.4 คำต่อวิ = 10 วิ
        text = " ".join(["คำ"] * 24)
        duration = estimate_duration(text)
        assert abs(duration - 10.0) < 0.1
    
    def test_estimate_duration_empty(self):
        """ทดสอบ empty text"""
        from modules.voice import estimate_duration
        
        duration = estimate_duration("")
        assert duration == 0.0
    
    def test_estimate_with_custom_rate(self):
        """ทดสอบ custom words per second"""
        from modules.voice import estimate_duration
        
        text = "หนึ่ง สอง สาม สี่ ห้า"  # 5 คำ
        duration = estimate_duration(text, words_per_second=1.0)
        assert abs(duration - 5.0) < 0.1


class TestVoiceGeneration:
    """Test voice generation (ไม่สร้างจริง ใช้ mock)"""
    
    @pytest.mark.asyncio
    async def test_generate_voice_creates_file(self, tmp_path):
        """ทดสอบว่าสร้างไฟล์ได้ (ต้องมี internet)"""
        # Skip ถ้าไม่ต้องการ test จริง
        pytest.skip("Skip real TTS test - requires internet")
        
        from modules.voice import generate_voice
        
        output = tmp_path / "test_voice.mp3"
        await generate_voice("สวัสดี", str(output))
        
        assert output.exists()
        assert output.stat().st_size > 0
    
    def test_generate_voice_sync(self, tmp_path):
        """ทดสอบ sync wrapper (skip ถ้าไม่มี internet)"""
        pytest.skip("Skip real TTS test - requires internet")
        
        from modules.voice import generate_voice_sync
        
        output = tmp_path / "test_voice_sync.mp3"
        result = generate_voice_sync("ทดสอบ", str(output))
        
        assert Path(result).exists()


class TestAudioDuration:
    """Test audio duration measurement"""
    
    def test_get_audio_duration_returns_float(self):
        """ทดสอบว่า return float"""
        pytest.skip("Skip real TTS test - requires internet")
        
        from modules.voice import get_audio_duration
        
        duration = get_audio_duration("สวัสดีครับ นี่คือการทดสอบ")
        assert isinstance(duration, float)
        assert duration > 0
