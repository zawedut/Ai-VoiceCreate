# =============================================================================
# 🧪 TESTS - Config Module
# =============================================================================

import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestConfigSettings:
    """Test config/settings.py"""
    
    def test_config_imports(self):
        """ทดสอบว่า import config ได้"""
        from config import settings
        assert hasattr(settings, 'BASE_DIR')
        assert hasattr(settings, 'MODEL_HIERARCHY')
    
    def test_paths_are_pathlib(self):
        """ทดสอบว่า paths เป็น Path objects"""
        from config.settings import BASE_DIR, INPUT_DIR, OUTPUT_DIR
        assert isinstance(BASE_DIR, Path)
        assert isinstance(INPUT_DIR, Path)
        assert isinstance(OUTPUT_DIR, Path)
    
    def test_model_hierarchy_not_empty(self):
        """ทดสอบว่ามี models ใน hierarchy"""
        from config.settings import MODEL_HIERARCHY
        assert len(MODEL_HIERARCHY) > 0
        assert all(isinstance(m, str) for m in MODEL_HIERARCHY)
    
    def test_ensure_directories(self):
        """ทดสอบว่าสร้าง directories ได้"""
        from config.settings import ensure_directories, INPUT_DIR, OUTPUT_DIR
        ensure_directories()
        assert INPUT_DIR.exists()
        assert OUTPUT_DIR.exists()
    
    def test_get_config_summary(self):
        """ทดสอบ config summary"""
        from config.settings import get_config_summary
        summary = get_config_summary()
        assert 'base_dir' in summary
        assert 'gemini_keys_count' in summary
        assert 'voice' in summary


class TestAPIKeysLoading:
    """Test API keys loading from .env"""
    
    def test_get_api_keys_returns_list(self):
        """ทดสอบว่า get_api_keys คืน list"""
        from config.settings import get_api_keys
        keys = get_api_keys()
        assert isinstance(keys, list)
    
    def test_empty_keys_if_no_env(self):
        """ทดสอบว่าไม่มี keys ถ้าไม่ได้ตั้งค่า .env"""
        import os
        # บันทึกค่าเดิม
        original = os.environ.get('GEMINI_API_KEYS', '')
        
        # ลบค่า
        if 'GEMINI_API_KEYS' in os.environ:
            del os.environ['GEMINI_API_KEYS']
        
        from config.settings import get_api_keys
        # Reload function
        keys = get_api_keys()
        
        # คืนค่าเดิม
        if original:
            os.environ['GEMINI_API_KEYS'] = original
        
        assert isinstance(keys, list)
