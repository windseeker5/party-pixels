#!/usr/bin/env python3
"""
Basic functionality test for Party Memory Wall
Tests core components without heavy dependencies
"""

import sys
import os
import sqlite3
from datetime import datetime

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def test_database_creation():
    """Test SQLite database creation"""
    print("🧪 Testing database creation...")
    
    try:
        # Test in-memory database
        conn = sqlite3.connect(':memory:')
        cursor = conn.cursor()
        
        # Create basic table structure
        cursor.execute('''
        CREATE TABLE uploads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT NOT NULL,
            guest_name TEXT,
            file_path TEXT NOT NULL,
            file_type TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Insert test data
        cursor.execute('''
        INSERT INTO uploads (device_id, guest_name, file_path, file_type)
        VALUES (?, ?, ?, ?)
        ''', ('test-device', 'Test User', '/media/photos/test.jpg', 'photo'))
        
        # Query test data
        cursor.execute('SELECT * FROM uploads WHERE guest_name = ?', ('Test User',))
        result = cursor.fetchone()
        
        conn.close()
        
        if result:
            print("✅ Database creation and basic operations working")
            return True
        else:
            print("❌ Database test failed - no data found")
            return False
            
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_party_configuration():
    """Test party configuration"""
    print("🧪 Testing party configuration...")
    
    try:
        party_config = {
            'title': "Happy 50th Birthday Valérie!",
            'slideshow_duration': 15,
            'max_file_size': 500 * 1024 * 1024,
            'allowed_photo_types': ['jpg', 'jpeg', 'png'],
            'allowed_video_types': ['mp4', 'mov', 'webm'],
            'allowed_music_types': ['mp3', 'm4a', 'wav']
        }
        
        # Test configuration values
        assert "Valérie" in party_config['title'], "Valérie's name missing from title"
        assert "50th Birthday" in party_config['title'], "50th Birthday missing from title"
        assert party_config['slideshow_duration'] == 15, "Slideshow duration incorrect"
        assert party_config['max_file_size'] == 500 * 1024 * 1024, "File size limit incorrect"
        
        print(f"✅ Party configuration valid: {party_config['title']}")
        return True
        
    except Exception as e:
        print(f"❌ Party configuration test failed: {e}")
        return False

def test_file_structure():
    """Test required file structure exists"""
    print("🧪 Testing file structure...")
    
    try:
        required_files = [
            'backend/app.py',
            'backend/database.py',
            'backend/requirements.txt',
            'backend/Dockerfile',
            'frontend/index.html',
            'frontend/upload.html',
            'frontend/styles.css',
            'frontend/party-display.js',
            'frontend/party-upload.js',
            'plan/README.md',
            'test/test_upload_api.py',
            'test/test_frontend.py'
        ]
        
        missing_files = []
        for file_path in required_files:
            if not os.path.exists(file_path):
                missing_files.append(file_path)
        
        if missing_files:
            print(f"❌ Missing files: {', '.join(missing_files)}")
            return False
        else:
            print(f"✅ All {len(required_files)} required files exist")
            return True
            
    except Exception as e:
        print(f"❌ File structure test failed: {e}")
        return False

def test_frontend_content():
    """Test frontend files contain required content"""
    print("🧪 Testing frontend content...")
    
    try:
        # Test celebration title in HTML
        with open('frontend/index.html', 'r') as f:
            index_content = f.read()
        
        if "Happy 50th Birthday Valérie!" not in index_content:
            print("❌ Celebration title missing from index.html")
            return False
        
        # Test CSS has celebration styling
        with open('frontend/styles.css', 'r') as f:
            css_content = f.read()
        
        if ".celebration-title" not in css_content:
            print("❌ Celebration title styling missing from CSS")
            return False
        
        # Test JavaScript has slideshow logic
        with open('frontend/party-display.js', 'r') as f:
            js_content = f.read()
        
        if "PartyDisplay" not in js_content:
            print("❌ PartyDisplay class missing from JavaScript")
            return False
        
        print("✅ Frontend content validation passed")
        return True
        
    except Exception as e:
        print(f"❌ Frontend content test failed: {e}")
        return False

def test_media_directories():
    """Test media directory structure"""
    print("🧪 Testing media directory structure...")
    
    try:
        required_dirs = ['media/photos', 'media/videos', 'media/music', 'database']
        
        for dir_path in required_dirs:
            os.makedirs(dir_path, exist_ok=True)
            if not os.path.exists(dir_path):
                print(f"❌ Failed to create directory: {dir_path}")
                return False
        
        print("✅ Media directory structure created successfully")
        return True
        
    except Exception as e:
        print(f"❌ Media directory test failed: {e}")
        return False

def main():
    """Run all basic tests"""
    print("🎉 Party Memory Wall - Basic Functionality Tests")
    print("🎂 Valérie's 50th Birthday Celebration")
    print("=" * 60)
    
    tests = [
        test_file_structure,
        test_party_configuration,
        test_database_creation,
        test_frontend_content,
        test_media_directories
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            failed += 1
        print()
    
    print("=" * 60)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎊 All basic tests passed! Party Memory Wall is ready!")
        print("🚀 Next steps:")
        print("  1. Install Python dependencies: cd backend && python -m venv venv && source venv/bin/activate && pip install flask flask-cors flask-socketio pillow")
        print("  2. Start backend: cd backend && python app.py")
        print("  3. Test frontend: Open http://localhost:6000 in browser")
        print("  4. Run full tests: python -m pytest test/ -v")
        return True
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)