#!/usr/bin/env python3
"""
Debug test for upload functionality on port 8000
Tests the actual file upload process and identifies what's broken
"""

import asyncio
import tempfile
import os
from playwright.async_api import async_playwright
from PIL import Image
from io import BytesIO

# Use the actual running port
BASE_URL = 'http://localhost:8000'

def create_test_image():
    """Create a small test image"""
    img = Image.new('RGB', (100, 100), color='red')
    img_buffer = BytesIO()
    img.save(img_buffer, format='JPEG')
    img_buffer.seek(0)
    return img_buffer.getvalue()

async def test_upload_functionality():
    """Test the upload page and identify issues"""
    
    print("🔍 Starting upload functionality debug test")
    print(f"📍 Testing URL: {BASE_URL}/upload")
    print("=" * 60)
    
    async with async_playwright() as p:
        # Launch browser with more debugging info
        browser = await p.chromium.launch(
            headless=False,  # Run in visible mode to see what's happening
            args=['--no-sandbox', '--disable-web-security'],
            slow_mo=1000  # Slow down operations to observe
        )
        
        # Create a new page with console logging
        page = await browser.new_page()
        
        # Capture console messages
        console_messages = []
        errors = []
        network_failures = []
        
        def handle_console(msg):
            console_messages.append(f"[{msg.type}] {msg.text}")
            print(f"🖥️  Console [{msg.type}]: {msg.text}")
        
        def handle_page_error(error):
            errors.append(str(error))
            print(f"❌ Page Error: {error}")
        
        def handle_response(response):
            if response.status >= 400:
                network_failures.append(f"{response.status} - {response.url}")
                print(f"🌐 Network Error: {response.status} - {response.url}")
        
        page.on("console", handle_console)
        page.on("pageerror", handle_page_error)
        page.on("response", handle_response)
        
        try:
            print("🌐 Navigating to upload page...")
            await page.goto(f'{BASE_URL}/upload', wait_until='networkidle', timeout=30000)
            
            # Take a screenshot to see the current state
            await page.screenshot(path='upload_page_initial.png', full_page=True)
            print("📸 Screenshot saved: upload_page_initial.png")
            
            # Check if page loaded successfully
            title = await page.title()
            print(f"📄 Page title: {title}")
            
            # Look for the upload form elements
            print("\n🔍 Examining upload form elements:")
            
            # Check for upload area
            upload_area = page.locator('#uploadArea')
            upload_area_exists = await upload_area.count() > 0
            print(f"   Upload area (#uploadArea): {'✅ Found' if upload_area_exists else '❌ Missing'}")
            
            if upload_area_exists:
                is_visible = await upload_area.is_visible()
                print(f"   Upload area visible: {'✅ Yes' if is_visible else '❌ No'}")
            
            # Check for file input
            file_input = page.locator('input[type="file"]')
            file_input_count = await file_input.count()
            print(f"   File input elements: {'✅ Found' if file_input_count > 0 else '❌ Missing'} ({file_input_count})")
            
            # Check for browse button
            browse_btn = page.locator('#browseBtn')
            browse_exists = await browse_btn.count() > 0
            print(f"   Browse button (#browseBtn): {'✅ Found' if browse_exists else '❌ Missing'}")
            
            # Check for upload button
            upload_btn = page.locator('#uploadBtn')
            upload_btn_exists = await upload_btn.count() > 0
            print(f"   Upload button (#uploadBtn): {'✅ Found' if upload_btn_exists else '❌ Missing'}")
            
            # Check for guest name input
            guest_input = page.locator('#guestName')
            guest_input_exists = await guest_input.count() > 0
            print(f"   Guest name input (#guestName): {'✅ Found' if guest_input_exists else '❌ Missing'}")
            
            # Check for celebration title
            title_element = page.locator('.celebration-title')
            title_exists = await title_element.count() > 0
            print(f"   Celebration title: {'✅ Found' if title_exists else '❌ Missing'}")
            
            if title_exists:
                title_text = await title_element.text_content()
                print(f"   Title text: {title_text}")
            
            # Try to interact with the upload functionality
            print("\n🎯 Testing upload interactions:")
            
            # Create a temporary test file
            test_image_data = create_test_image()
            
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
                tmp_file.write(test_image_data)
                tmp_file_path = tmp_file.name
            
            try:
                if file_input_count > 0:
                    print("   Attempting to select file...")
                    await file_input.first.set_input_files(tmp_file_path)
                    print("   ✅ File selected successfully")
                    
                    # Check if file selection triggered any changes
                    await page.wait_for_timeout(2000)
                    await page.screenshot(path='upload_page_file_selected.png', full_page=True)
                    print("   📸 Screenshot after file selection: upload_page_file_selected.png")
                    
                    # Try to fill in guest name if field exists
                    if guest_input_exists:
                        await guest_input.fill('Debug Test User')
                        print("   ✅ Guest name filled")
                    
                    # Try to click upload button if it exists
                    if upload_btn_exists:
                        print("   Attempting to click upload button...")
                        
                        # Check if upload button is enabled
                        is_enabled = await upload_btn.is_enabled()
                        print(f"   Upload button enabled: {'✅ Yes' if is_enabled else '❌ No'}")
                        
                        if is_enabled:
                            await upload_btn.click()
                            print("   ✅ Upload button clicked")
                            
                            # Wait for upload response
                            print("   ⏳ Waiting for upload to complete...")
                            await page.wait_for_timeout(5000)
                            
                            await page.screenshot(path='upload_page_after_upload.png', full_page=True)
                            print("   📸 Screenshot after upload attempt: upload_page_after_upload.png")
                        else:
                            print("   ❌ Upload button is disabled")
                    else:
                        print("   ❌ No upload button found to click")
                        
                else:
                    print("   ❌ No file input found - cannot test file selection")
                    
                    # Check if there's a drag-and-drop area we can interact with
                    if upload_area_exists:
                        print("   🎯 Trying drag-and-drop on upload area...")
                        # This is more complex to test programmatically
                        await upload_area.click()
                        await page.wait_for_timeout(1000)
            
            finally:
                # Clean up temp file
                try:
                    os.unlink(tmp_file_path)
                except:
                    pass
            
            # Wait a bit more to catch any delayed responses
            await page.wait_for_timeout(3000)
            
        except Exception as e:
            print(f"❌ Test execution error: {e}")
            await page.screenshot(path='upload_page_error.png', full_page=True)
            errors.append(f"Test execution error: {e}")
        
        finally:
            await browser.close()
    
    # Print summary of findings
    print("\n" + "=" * 60)
    print("📊 UPLOAD DEBUG SUMMARY")
    print("=" * 60)
    
    if console_messages:
        print(f"\n🖥️  Console Messages ({len(console_messages)}):")
        for msg in console_messages:
            print(f"   {msg}")
    else:
        print("\n🖥️  No console messages captured")
    
    if errors:
        print(f"\n❌ Errors Found ({len(errors)}):")
        for error in errors:
            print(f"   {error}")
    else:
        print("\n✅ No JavaScript errors detected")
    
    if network_failures:
        print(f"\n🌐 Network Failures ({len(network_failures)}):")
        for failure in network_failures:
            print(f"   {failure}")
    else:
        print("\n✅ No network failures detected")
    
    print("\n📁 Screenshots saved for manual inspection:")
    print("   - upload_page_initial.png: Initial page state")
    print("   - upload_page_file_selected.png: After file selection")
    print("   - upload_page_after_upload.png: After upload attempt")
    if errors:
        print("   - upload_page_error.png: Error state")
    
    print("\n🔧 RECOMMENDED NEXT STEPS:")
    print("1. Check the saved screenshots to see the actual UI state")
    print("2. Review console messages for JavaScript errors")
    print("3. Verify network requests are reaching the backend")
    print("4. Check if upload endpoint is working via direct API test")

if __name__ == "__main__":
    asyncio.run(test_upload_functionality())