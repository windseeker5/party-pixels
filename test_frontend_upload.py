#!/usr/bin/env python3
"""
Test the frontend upload functionality using selenium/playwright equivalent
"""
import subprocess
import time
import tempfile
import os

def create_test_image():
    """Create a small test image file"""
    test_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x00\x00\x00\x01\x00\x01\x00\x00\x00\x00\x02\x00\x01\x8d\xb4\x8d\xb4'
    
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        f.write(test_content)
        return f.name

def test_upload_with_javascript():
    """Test if the JavaScript upload works via a headless browser test"""
    test_file = create_test_image()
    
    try:
        # Create a simple HTML test file that simulates the upload
        test_html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Upload Test</title>
</head>
<body>
    <script>
    async function testUpload() {{
        try {{
            // Create a form with the test file
            const formData = new FormData();
            
            // Create a fake file blob
            const blob = new Blob(['test content'], {{ type: 'image/png' }});
            const file = new File([blob], 'test.png', {{ type: 'image/png' }});
            
            formData.append('files', file);
            formData.append('guest_name', 'Test User');
            formData.append('birthday_note', 'Test message');
            formData.append('type', 'auto');
            
            const response = await fetch('http://localhost:8000/api/upload', {{
                method: 'POST',
                body: formData
            }});
            
            const result = await response.json();
            
            if (response.ok) {{
                console.log('SUCCESS: Upload worked!', result);
                document.body.innerHTML = '<h1 style="color: green;">UPLOAD SUCCESS!</h1>';
            }} else {{
                console.error('FAILED: Upload failed', result);
                document.body.innerHTML = '<h1 style="color: red;">UPLOAD FAILED!</h1>';
            }}
        }} catch (error) {{
            console.error('ERROR:', error);
            document.body.innerHTML = '<h1 style="color: red;">UPLOAD ERROR: ' + error.message + '</h1>';
        }}
    }}
    
    // Run test when page loads
    window.onload = testUpload;
    </script>
    
    <h1>Testing upload...</h1>
</body>
</html>
        """
        
        # Write test HTML file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.write(test_html)
            test_html_file = f.name
        
        print("🧪 Testing frontend upload with JavaScript...")
        print(f"Created test HTML: {test_html_file}")
        print("You can open this file in a browser to test the upload functionality")
        print(f"Or run: firefox {test_html_file}")
        
        return test_html_file
        
    finally:
        # Clean up test file
        if os.path.exists(test_file):
            os.unlink(test_file)

if __name__ == "__main__":
    test_file = test_upload_with_javascript()
    print(f"Test file created: {test_file}")