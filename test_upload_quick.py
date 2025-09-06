#!/usr/bin/env python3
"""
Quick test to check if the upload endpoint is working
"""
import requests
import os
import tempfile

def test_upload():
    print("🧪 Testing upload functionality...")
    
    # Create a test image file
    test_content = b"fake image content for testing"
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
        f.write(test_content)
        test_file_path = f.name
    
    try:
        # Test the upload endpoint
        with open(test_file_path, 'rb') as f:
            files = {'files': ('test.jpg', f, 'image/jpeg')}
            data = {
                'guest_name': 'Test User',
                'birthday_note': 'Test upload',
                'type': 'auto'
            }
            
            response = requests.post('http://localhost:8000/api/upload', files=files, data=data)
            
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            
            if response.status_code == 200:
                print("✅ Upload endpoint is working!")
            else:
                print("❌ Upload endpoint failed!")
                
    except Exception as e:
        print(f"❌ Error testing upload: {e}")
    finally:
        # Clean up
        os.unlink(test_file_path)

if __name__ == "__main__":
    test_upload()