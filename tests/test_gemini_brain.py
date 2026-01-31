# =============================================================================
# 🧪 TESTS - Gemini Brain Module
# =============================================================================

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestScriptCleaning:
    """Test script cleaning functions"""
    
    def test_removes_markdown(self):
        """ลบ markdown formatting"""
        from modules.gemini_brain import clean_script_final
        
        text = "**bold** และ **more bold**"
        result = clean_script_final(text)
        assert '**' not in result
    
    def test_removes_brackets(self):
        """ลบ [text in brackets]"""
        from modules.gemini_brain import clean_script_final
        
        text = "นี่คือ [note] ข้อความ [another]"
        result = clean_script_final(text)
        assert '[' not in result
        assert ']' not in result
    
    def test_removes_bad_words(self):
        """ลบคำที่ไม่ต้องการ"""
        from modules.gemini_brain import clean_script_final
        
        text = "สวัสดีครับ คลิปนี้เกี่ยวกับ วิดีโอนี้"
        result = clean_script_final(text)
        assert 'สวัสดีครับ' not in result
        assert 'คลิปนี้' not in result
        assert 'วิดีโอนี้' not in result
    
    def test_normalizes_whitespace(self):
        """ทำให้ whitespace ปกติ"""
        from modules.gemini_brain import clean_script_final
        
        text = "ข้อความ   มี   ช่องว่าง   เยอะ"
        result = clean_script_final(text)
        assert '   ' not in result


class TestModelManagement:
    """Test model fallback functions"""
    
    def test_get_next_model_cycles(self):
        """ทดสอบ model rotation"""
        from modules.gemini_brain import (
            get_next_model, reset_model_fallback, 
            MODEL_HIERARCHY, current_model_index
        )
        import modules.gemini_brain as brain
        
        reset_model_fallback()
        assert brain.current_model_index == 0
        
        # วน models
        for i in range(len(MODEL_HIERARCHY)):
            model = get_next_model()
            assert isinstance(model, str)
            assert model in MODEL_HIERARCHY
    
    def test_reset_model_fallback(self):
        """ทดสอบ reset กลับไป model แรก"""
        from modules.gemini_brain import reset_model_fallback
        import modules.gemini_brain as brain
        
        brain.current_model_index = 2
        reset_model_fallback()
        assert brain.current_model_index == 0


class TestKeyManagement:
    """Test API key management"""
    
    def test_configure_gemini_no_error(self):
        """ทดสอบว่า configure ไม่ error (แม้ key จะไม่ valid)"""
        from modules.gemini_brain import configure_gemini
        
        # ควรไม่ raise error แม้จะเป็น dummy key
        configure_gemini("dummy-key-for-testing")


class TestAIBrainClass:
    """Test AIBrain class"""
    
    def test_create_instance(self):
        """สร้าง instance ได้"""
        from modules.gemini_brain import AIBrain
        
        brain = AIBrain()
        assert brain.initialized == False
        assert brain.keys == []
    
    def test_status_property(self):
        """ทดสอบ status property"""
        from modules.gemini_brain import AIBrain
        
        brain = AIBrain()
        status = brain.status
        
        assert 'gemini_keys' in status
        assert 'current_model' in status
        assert 'current_model' in status
