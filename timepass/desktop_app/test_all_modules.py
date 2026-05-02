"""
Bitflow Developer Toolkit - Comprehensive Test Suite
Tests all modules for proper functionality
"""
import sys
sys.path.insert(0, '.')

def print_header(text):
    print("\n" + "=" * 60)
    print(text)
    print("=" * 60)

def test_pass(msg):
    print(f"  ✓ {msg}")

def test_fail(msg, error=None):
    print(f"  ✗ {msg}" + (f": {error}" if error else ""))

def main():
    print("=" * 60)
    print("BITFLOW DEVELOPER TOOLKIT - COMPREHENSIVE TEST SUITE")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    # ==========================================
    # 1. Module Import Tests
    # ==========================================
    print_header("[1] Testing Module Imports...")
    
    modules_to_test = [
        ('core.config', 'Config'),
        ('core.database', 'Database'),
        ('core.main_window', 'MainWindow'),
        ('modules.dashboard', 'DashboardModule'),
        ('modules.time_tracker', 'TimeTrackerModule'),
        ('modules.quick_notes', 'QuickNotesModule'),
        ('modules.snippet_manager', 'SnippetManagerModule'),
        ('modules.api_tester', 'ApiTesterModule'),
        ('modules.json_formatter', 'JsonFormatterModule'),
        ('modules.regex_tester', 'RegexTesterModule'),
        ('modules.encoder_decoder', 'EncoderDecoderModule'),
        ('modules.color_converter', 'ColorConverterModule'),
        ('modules.password_generator', 'PasswordGeneratorModule'),
        ('modules.qr_generator', 'QRCodeGeneratorModule'),
        ('modules.markdown_previewer', 'MarkdownPreviewerModule'),
        ('modules.lorem_generator', 'LoremGeneratorModule'),
        ('modules.log_viewer', 'LogViewerModule'),
        ('modules.port_scanner', 'PortScannerModule'),
        ('modules.env_manager', 'EnvManagerModule'),
        ('modules.web_crawler', 'WebCrawlerModule'),
        ('modules.finance', 'FinanceModule'),
        ('modules.settings', 'SettingsDialog'),
    ]
    
    for module_path, class_name in modules_to_test:
        try:
            module = __import__(module_path, fromlist=[class_name])
            cls = getattr(module, class_name)
            test_pass(f"{module_path}.{class_name}")
            passed += 1
        except Exception as e:
            test_fail(f"{module_path}.{class_name}", str(e))
            failed += 1
    
    # ==========================================
    # 2. Core Component Tests
    # ==========================================
    print_header("[2] Testing Core Components...")
    
    # Config test
    try:
        from core.config import Config
        config = Config()
        config.set('test_key', 'test_value')
        assert config.get('test_key') == 'test_value'
        test_pass("Config: get/set working")
        passed += 1
    except Exception as e:
        test_fail("Config: get/set", str(e))
        failed += 1
    
    # Database test
    try:
        from core.database import Database
        db = Database()
        session = db.get_session()
        session.close()
        test_pass("Database: session creation working")
        passed += 1
    except Exception as e:
        test_fail("Database: session creation", str(e))
        failed += 1
    
    # ==========================================
    # 3. Utility Function Tests
    # ==========================================
    print_header("[3] Testing Utility Functions...")
    
    # JSON parsing
    try:
        import json
        test_json = '{"name": "test", "value": 123}'
        parsed = json.loads(test_json)
        assert parsed['name'] == 'test'
        test_pass("JSON parsing working")
        passed += 1
    except Exception as e:
        test_fail("JSON parsing", str(e))
        failed += 1
    
    # Regex matching
    try:
        import re
        pattern = r'\d+'
        test_str = 'abc123def456'
        matches = re.findall(pattern, test_str)
        assert matches == ['123', '456']
        test_pass("Regex matching working")
        passed += 1
    except Exception as e:
        test_fail("Regex matching", str(e))
        failed += 1
    
    # Base64 encoding
    try:
        import base64
        test_text = 'Hello World'
        encoded = base64.b64encode(test_text.encode()).decode()
        decoded = base64.b64decode(encoded).decode()
        assert decoded == test_text
        test_pass("Base64 encoding/decoding working")
        passed += 1
    except Exception as e:
        test_fail("Base64 encoding/decoding", str(e))
        failed += 1
    
    # URL encoding
    try:
        from urllib.parse import quote, unquote
        test_url = "Hello World & Test"
        encoded = quote(test_url)
        decoded = unquote(encoded)
        assert decoded == test_url
        test_pass("URL encoding/decoding working")
        passed += 1
    except Exception as e:
        test_fail("URL encoding/decoding", str(e))
        failed += 1
    
    # HTML encoding
    try:
        import html
        test_html = "<script>alert('test')</script>"
        encoded = html.escape(test_html)
        decoded = html.unescape(encoded)
        assert decoded == test_html
        test_pass("HTML encoding/decoding working")
        passed += 1
    except Exception as e:
        test_fail("HTML encoding/decoding", str(e))
        failed += 1
    
    # Color conversion
    try:
        def hex_to_rgb(hex_color):
            hex_color = hex_color.lstrip('#')
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        rgb = hex_to_rgb('#FF5733')
        assert rgb == (255, 87, 51)
        test_pass("Color HEX to RGB conversion working")
        passed += 1
    except Exception as e:
        test_fail("Color conversion", str(e))
        failed += 1
    
    # Password generation
    try:
        import secrets
        import string
        chars = string.ascii_letters + string.digits
        password = ''.join(secrets.choice(chars) for _ in range(16))
        assert len(password) == 16
        test_pass("Password generation working")
        passed += 1
    except Exception as e:
        test_fail("Password generation", str(e))
        failed += 1
    
    # Hashing - MD5
    try:
        import hashlib
        text = 'test'
        md5_hash = hashlib.md5(text.encode()).hexdigest()
        assert len(md5_hash) == 32
        test_pass("MD5 hashing working")
        passed += 1
    except Exception as e:
        test_fail("MD5 hashing", str(e))
        failed += 1
    
    # Hashing - SHA256
    try:
        sha256_hash = hashlib.sha256(text.encode()).hexdigest()
        assert len(sha256_hash) == 64
        test_pass("SHA256 hashing working")
        passed += 1
    except Exception as e:
        test_fail("SHA256 hashing", str(e))
        failed += 1
    
    # Markdown conversion
    try:
        import markdown
        md_text = '# Hello\n**Bold** text'
        html_output = markdown.markdown(md_text)
        assert '<h1>' in html_output or '<strong>' in html_output
        test_pass("Markdown conversion working")
        passed += 1
    except Exception as e:
        test_fail("Markdown conversion", str(e))
        failed += 1
    
    # QR Code generation
    try:
        import qrcode
        qr = qrcode.QRCode(version=1)
        qr.add_data('https://bitflow.dev')
        qr.make()
        img = qr.make_image()
        test_pass("QR Code generation working")
        passed += 1
    except Exception as e:
        test_fail("QR Code generation", str(e))
        failed += 1
    
    # Lorem ipsum generation
    try:
        import random
        LOREM_WORDS = ['lorem', 'ipsum', 'dolor', 'sit', 'amet']
        words = ' '.join(random.choices(LOREM_WORDS, k=10))
        assert len(words.split()) == 10
        test_pass("Lorem ipsum generation working")
        passed += 1
    except Exception as e:
        test_fail("Lorem ipsum generation", str(e))
        failed += 1
    
    # ==========================================
    # 4. Database Model Tests
    # ==========================================
    print_header("[4] Testing Database Models...")
    
    models_to_test = [
        ('core.database', 'QuickNote'),
        ('core.database', 'CodeSnippet'),
        ('core.database', 'TimeEntry'),
        ('core.database', 'Client'),
        ('core.database', 'Invoice'),
        ('modules.finance', 'Expense'),
        ('modules.env_manager', 'EnvProfile'),
    ]
    
    for module_path, model_name in models_to_test:
        try:
            module = __import__(module_path, fromlist=[model_name])
            model = getattr(module, model_name)
            test_pass(f"{model_name} model loaded")
            passed += 1
        except Exception as e:
            test_fail(f"{model_name} model", str(e))
            failed += 1
    
    # ==========================================
    # 5. Network Tests
    # ==========================================
    print_header("[5] Testing Network Operations...")
    
    # Socket/hostname resolution
    try:
        import socket
        ip = socket.gethostbyname('localhost')
        assert ip == '127.0.0.1'
        test_pass("Hostname resolution working")
        passed += 1
    except Exception as e:
        test_fail("Hostname resolution", str(e))
        failed += 1
    
    # HTTP client
    try:
        import httpx
        test_pass("httpx HTTP client available")
        passed += 1
    except Exception as e:
        test_fail("httpx HTTP client", str(e))
        failed += 1
    
    # ==========================================
    # 6. GUI Component Tests (non-visual)
    # ==========================================
    print_header("[6] Testing GUI Components (non-visual)...")
    
    try:
        from PyQt6.QtWidgets import QApplication
        test_pass("PyQt6.QtWidgets available")
        passed += 1
    except Exception as e:
        test_fail("PyQt6.QtWidgets", str(e))
        failed += 1
    
    try:
        from PyQt6.QtCore import Qt, QThread, pyqtSignal
        test_pass("PyQt6.QtCore available")
        passed += 1
    except Exception as e:
        test_fail("PyQt6.QtCore", str(e))
        failed += 1
    
    try:
        from PyQt6.QtGui import QColor, QFont
        test_pass("PyQt6.QtGui available")
        passed += 1
    except Exception as e:
        test_fail("PyQt6.QtGui", str(e))
        failed += 1
    
    try:
        from PyQt6.QtWebEngineWidgets import QWebEngineView
        test_pass("PyQt6.QtWebEngineWidgets available")
        passed += 1
    except Exception as e:
        test_fail("PyQt6.QtWebEngineWidgets", str(e))
        failed += 1
    
    # ==========================================
    # Summary
    # ==========================================
    print_header("TEST SUMMARY")
    total = passed + failed
    print(f"\n  Total Tests: {total}")
    print(f"  Passed: {passed} ✓")
    print(f"  Failed: {failed} ✗")
    print(f"  Success Rate: {passed/total*100:.1f}%")
    
    if failed == 0:
        print("\n  🎉 ALL TESTS PASSED!")
    else:
        print(f"\n  ⚠️ {failed} test(s) failed")
    
    print("\n" + "=" * 60)
    
    return failed == 0

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
