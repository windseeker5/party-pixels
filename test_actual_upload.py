#!/usr/bin/env python3
"""
Test the actual upload page functionality
"""
import subprocess
import tempfile
import os

def test_actual_upload_page():
    """Test the real upload page"""
    
    # Create a test image 
    test_content = b'test image data'
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
        f.write(test_content)
        test_file = f.name
    
    try:
        print("🔍 Testing actual upload page...")
        print("🌐 Opening http://localhost:8000/upload")
        
        # Test 1: Check if page loads
        result = subprocess.run(['curl', '-s', '-w', '%{http_code}', 'http://localhost:8000/upload'], 
                              capture_output=True, text=True)
        
        status_code = result.stdout[-3:]  # Last 3 characters are status code
        
        if status_code == '200':
            print("✅ Upload page loads successfully")
        else:
            print(f"❌ Upload page failed to load: {status_code}")
            return False
            
        # Test 2: Check if CSS loads
        css_result = subprocess.run(['curl', '-s', '-w', '%{http_code}', 'http://localhost:8000/static/styles.css'], 
                                  capture_output=True, text=True)
        
        css_status = css_result.stdout[-3:]
        if css_status == '200':
            print("✅ CSS loads successfully")
        else:
            print(f"❌ CSS failed to load: {css_status}")
            
        # Test 3: Check if JS loads
        js_result = subprocess.run(['curl', '-s', '-w', '%{http_code}', 'http://localhost:8000/static/party-upload.js'], 
                                 capture_output=True, text=True)
        
        js_status = js_result.stdout[-3:]
        if js_status == '200':
            print("✅ JavaScript loads successfully")
        else:
            print(f"❌ JavaScript failed to load: {js_status}")
            
        # Test 4: Test file upload via API
        print("🔄 Testing file upload API...")
        with open(test_file, 'rb') as f:
            upload_result = subprocess.run([
                'curl', '-s', '-w', '%{http_code}', '-X', 'POST',
                '-F', f'files=@{test_file}',
                '-F', 'guest_name=Test User',
                '-F', 'birthday_note=Test message',
                '-F', 'type=auto',
                'http://localhost:8000/api/upload'
            ], capture_output=True, text=True)
            
            upload_status = upload_result.stdout[-3:]
            if upload_status in ['200', '201']:
                print("✅ File upload API works!")
                print(f"📤 Upload response: {upload_result.stdout[:-3]}")
                return True
            else:
                print(f"❌ File upload failed: {upload_status}")
                print(f"📤 Upload response: {upload_result.stdout}")
                return False
                
    finally:
        # Clean up
        if os.path.exists(test_file):
            os.unlink(test_file)
    
    return True

if __name__ == "__main__":
    success = test_actual_upload_page()
    if success:
        print("\n🎉 UPLOAD FUNCTIONALITY IS WORKING!")
        print("🌐 Go to http://localhost:8000/upload and try uploading a file!")
    else:
        print("\n❌ UPLOAD FUNCTIONALITY IS BROKEN!")