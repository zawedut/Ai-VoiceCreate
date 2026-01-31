# =============================================================================
# 🧪 TESTS - Downloader Module
# =============================================================================

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestSanitizeFilename:
    """Test filename sanitization"""
    
    def test_removes_special_chars(self):
        """ลบอักขระพิเศษ"""
        from modules.downloader import sanitize_filename
        
        assert sanitize_filename('test*file') == 'testfile'
        assert sanitize_filename('test:file') == 'testfile'
        assert sanitize_filename('test<file>') == 'testfile'
        assert sanitize_filename('test|file') == 'testfile'
    
    def test_replaces_spaces(self):
        """แทนที่ space ด้วย underscore"""
        from modules.downloader import sanitize_filename
        
        assert sanitize_filename('test file') == 'test_file'
        assert sanitize_filename('test  file') == 'test__file'
    
    def test_limits_length(self):
        """จำกัดความยาว 50 ตัวอักษร"""
        from modules.downloader import sanitize_filename
        
        long_name = 'a' * 100
        result = sanitize_filename(long_name)
        assert len(result) <= 50
    
    def test_handles_empty(self):
        """จัดการ empty string"""
        from modules.downloader import sanitize_filename
        
        assert sanitize_filename('') == ''
        assert sanitize_filename('   ') == ''


class TestURLManagement:
    """Test URL file management"""
    
    def test_get_urls_returns_list(self):
        """get_urls คืน list"""
        from modules.downloader import get_urls
        
        urls = get_urls()
        assert isinstance(urls, list)
    
    def test_add_and_remove_urls(self, tmp_path):
        """ทดสอบเพิ่มและลบ URLs"""
        import os
        from config import settings
        
        # ใช้ temp file
        original_url_file = settings.URL_FILE
        settings.URL_FILE = tmp_path / "urls.txt"
        
        from modules.downloader import add_urls_to_file, get_urls, remove_url_from_file
        
        # เพิ่ม URLs
        test_urls = [
            'https://youtube.com/shorts/abc123',
            'https://youtube.com/shorts/def456',
        ]
        add_urls_to_file(test_urls)
        
        # ตรวจสอบ
        urls = get_urls()
        assert len(urls) == 2
        assert test_urls[0] in urls
        
        # ลบ URL
        remove_url_from_file(test_urls[0])
        urls = get_urls()
        assert len(urls) == 1
        assert test_urls[0] not in urls
        
        # คืนค่าเดิม
        settings.URL_FILE = original_url_file


class TestVideoInfo:
    """Test video info extraction (แบบไม่ download จริง)"""
    
    def test_get_video_info_invalid_url(self):
        """ทดสอบ URL ไม่ถูกต้อง"""
        from modules.downloader import get_video_info
        
        result = get_video_info('https://invalid-url.com/fake')
        assert result is None
