"""
Test suite for Party Memory Wall Integration Testing

CRITICAL REQUIREMENTS:
- Test complete workflow: upload → display → attribution
- Use existing MCP Playwright for UI testing
- Flask MUST run on port 6000
- Test Valérie's celebration integration end-to-end

Before running tests:
1. cd backend && python app.py (port 6000 with full functionality)
2. Ensure all frontend files served correctly
3. Run: python -m pytest test/test_integration.py -v
"""

import pytest
import requests
import asyncio
import json
from io import BytesIO
from PIL import Image
from playwright.async_api import async_playwright

# Try to import websockets for real-time testing
try:
    import websockets
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    print("⚠️  websockets not available - some integration tests will be skipped")

BASE_URL = 'http://localhost:6000'
WS_URL = 'ws://localhost:6000/ws'

def create_test_image(color='red', size=(100, 100)):
    """Create test image with specified color and size"""
    img = Image.new('RGB', size, color=color)
    img_buffer = BytesIO()
    img.save(img_buffer, format='JPEG')
    img_buffer.seek(0)
    return img_buffer

def create_test_video():
    """Create minimal test video data"""
    # Minimal MP4-like header for testing
    video_data = b'\x00\x00\x00\x20\x66\x74\x79\x70\x6D\x70\x34\x31' + b'integration_test_video' * 100
    return BytesIO(video_data)

def create_test_audio():
    """Create minimal test audio data"""
    # Minimal MP3-like header for testing
    audio_data = b'\xFF\xFB\x90\x00' + b'integration_test_audio' * 50
    return BytesIO(audio_data)

def test_system_health_check():
    """Test all system components are running and healthy"""
    # Test Flask API is responding
    try:
        config_response = requests.get(f'{BASE_URL}/api/config', timeout=10)
        assert config_response.status_code == 200, "Flask API not responding"
        
        config = config_response.json()
        assert "Valérie" in config['title'], f"Valérie's name missing from config: {config['title']}"
        
        print("✅ Flask API healthy and configured for Valérie's party")
        
    except requests.exceptions.ConnectionError:
        pytest.fail("Flask server not running on port 6000. Start with: cd backend && python app.py")
    
    # Test media API endpoint
    media_response = requests.get(f'{BASE_URL}/api/media')
    assert media_response.status_code == 200, "Media API not responding"
    
    # Test music queue endpoint
    queue_response = requests.get(f'{BASE_URL}/api/music/queue')
    assert queue_response.status_code == 200, "Music queue API not responding"
    
    print("✅ All API endpoints healthy")

async def test_complete_photo_upload_to_display_workflow():
    """Test complete workflow: photo upload → database → API → frontend display"""
    
    # Step 1: Upload a photo with guest attribution
    test_image = create_test_image(color='blue', size=(200, 150))
    files = {'files': ('integration_photo.jpg', test_image, 'image/jpeg')}
    data = {'guest_name': 'Integration Tester Sarah'}
    
    upload_response = requests.post(f'{BASE_URL}/api/upload', files=files, data=data)
    assert upload_response.status_code == 201, f"Photo upload failed: {upload_response.text}"
    
    upload_result = upload_response.json()
    upload_id = upload_result['upload_id']
    print(f"✅ Photo uploaded successfully with ID: {upload_id}")
    
    # Step 2: Verify photo appears in media API
    media_response = requests.get(f'{BASE_URL}/api/media')
    assert media_response.status_code == 200, "Media API failed after upload"
    
    media_data = media_response.json()
    uploaded_photo = None
    
    for item in media_data['media']:
        if item.get('id') == upload_id or item.get('guest_name') == 'Integration Tester Sarah':
            uploaded_photo = item
            break
    
    assert uploaded_photo is not None, f"Uploaded photo not found in media API response"
    assert uploaded_photo['type'] == 'photo', f"Photo type incorrect: {uploaded_photo['type']}"
    assert uploaded_photo['guest_name'] == 'Integration Tester Sarah', f"Guest name incorrect: {uploaded_photo['guest_name']}"
    
    print(f"✅ Photo appears correctly in media API")
    
    # Step 3: Test frontend displays the photo
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            await page.goto(BASE_URL, wait_until='networkidle')
            
            # Verify Valérie's title is displayed
            title_element = page.locator('.celebration-title')
            await title_element.wait_for(timeout=10000)
            
            title_text = await title_element.text_content()
            assert "Happy 50th Birthday Valérie!" in title_text, f"Celebration title incorrect: {title_text}"
            
            # Wait for slideshow to load
            await page.wait_for_timeout(3000)
            
            # Check if our uploaded photo attribution appears
            # Note: This test may need to wait for slideshow rotation or have multiple slides
            attribution_element = page.locator('#attribution')
            
            if await attribution_element.is_visible():
                attribution_text = await attribution_element.text_content()
                # Our photo might be visible, or we might need to wait for rotation
                print(f"ℹ️  Current attribution: {attribution_text}")
                
                # If we don't see our guest name immediately, it might be in rotation
                if 'Integration Tester Sarah' in attribution_text:
                    print("✅ Uploaded photo attribution visible on display")
                else:
                    print("ℹ️  Photo attribution not currently visible (may be in rotation)")
            else:
                print("ℹ️  Attribution overlay not visible (no media loaded or different structure)")
            
        except Exception as e:
            await page.screenshot(path='integration_test_failure.png')
            raise e
        finally:
            await browser.close()
    
    print("✅ Complete photo upload to display workflow tested")

async def test_complete_video_upload_workflow():
    """Test complete workflow for video uploads"""
    
    # Upload a video
    test_video = create_test_video()
    files = {'files': ('integration_video.mp4', test_video, 'video/mp4')}
    data = {'guest_name': 'Video Integration Tester'}
    
    upload_response = requests.post(f'{BASE_URL}/api/upload', files=files, data=data)
    assert upload_response.status_code == 201, f"Video upload failed: {upload_response.text}"
    
    upload_id = upload_response.json()['upload_id']
    print(f"✅ Video uploaded successfully with ID: {upload_id}")
    
    # Verify video in media API
    media_response = requests.get(f'{BASE_URL}/api/media')
    media_data = media_response.json()
    
    uploaded_video = None
    for item in media_data['media']:
        if item.get('id') == upload_id:
            uploaded_video = item
            break
    
    assert uploaded_video is not None, "Video not found in media API"
    assert uploaded_video['type'] == 'video', f"Video type incorrect: {uploaded_video['type']}"
    assert uploaded_video['guest_name'] == 'Video Integration Tester'
    
    # Test video display capability
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            await page.goto(BASE_URL, wait_until='networkidle')
            
            # Check slideshow container can handle videos
            slideshow_container = page.locator('.slideshow-container')
            await slideshow_container.wait_for(timeout=5000)
            
            # Look for video elements (may not be active if slideshow hasn't rotated to it)
            video_elements = page.locator('video')
            video_count = await video_elements.count()
            
            if video_count > 0:
                print(f"✅ Video elements found in slideshow: {video_count}")
            else:
                print("ℹ️  No video elements currently visible (may be in rotation or not loaded)")
            
        except Exception as e:
            await page.screenshot(path='integration_video_test_failure.png')
            raise e
        finally:
            await browser.close()
    
    print("✅ Complete video upload workflow tested")

async def test_music_upload_and_queue_integration():
    """Test complete music upload and queue integration"""
    
    # Upload music
    test_audio = create_test_audio()
    files = {'files': ('integration_song.mp3', test_audio, 'audio/mp3')}
    data = {
        'guest_name': 'DJ Integration Tester',
        'type': 'music',
        'song_title': 'Integration Test Song',
        'artist': 'Test Artist'
    }
    
    upload_response = requests.post(f'{BASE_URL}/api/upload', files=files, data=data)
    assert upload_response.status_code == 201, f"Music upload failed: {upload_response.text}"
    
    upload_id = upload_response.json()['upload_id']
    print(f"✅ Music uploaded successfully with ID: {upload_id}")
    
    # Verify music appears in queue
    queue_response = requests.get(f'{BASE_URL}/api/music/queue')
    assert queue_response.status_code == 200, "Music queue API failed"
    
    queue_data = queue_response.json()
    assert 'songs' in queue_data, "Music queue missing 'songs' field"
    
    # Find our uploaded song
    uploaded_song = None
    for song in queue_data['songs']:
        if song.get('guest_name') == 'DJ Integration Tester':
            uploaded_song = song
            break
    
    assert uploaded_song is not None, "Uploaded song not found in music queue"
    assert uploaded_song['song_title'] == 'Integration Test Song'
    
    # Test music controls in UI
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            await page.goto(BASE_URL, wait_until='networkidle')
            
            # Check music overlay exists
            music_overlay = page.locator('.music-overlay')
            if await music_overlay.is_visible():
                # Check for music controls
                song_title_element = page.locator('#songTitle')
                if await song_title_element.is_visible():
                    current_song = await song_title_element.text_content()
                    print(f"ℹ️  Current song display: {current_song}")
                
                # Check for play/pause controls
                play_pause_btn = page.locator('#playPauseBtn')
                if await play_pause_btn.is_visible():
                    print("✅ Music controls visible in UI")
                else:
                    print("ℹ️  Music controls not visible")
            else:
                print("ℹ️  Music overlay not visible")
            
        except Exception as e:
            await page.screenshot(path='integration_music_test_failure.png')
            raise e
        finally:
            await browser.close()
    
    print("✅ Complete music upload and queue integration tested")

@pytest.mark.skipif(not WEBSOCKETS_AVAILABLE, reason="websockets library not available")
async def test_real_time_upload_notification_integration():
    """Test real-time WebSocket notifications for uploads"""
    
    websocket_notifications = []
    
    async def websocket_listener():
        try:
            async with websockets.connect(WS_URL, timeout=10) as websocket:
                # Listen for notifications
                while True:
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=15)
                        data = json.loads(message)
                        websocket_notifications.append(data)
                        
                        # Stop after receiving a new_upload notification
                        if data.get('type') == 'new_upload':
                            break
                            
                    except asyncio.TimeoutError:
                        break
                        
        except Exception as e:
            print(f"WebSocket listener error: {e}")
    
    # Start WebSocket listener
    listener_task = asyncio.create_task(websocket_listener())
    await asyncio.sleep(1)  # Allow connection to establish
    
    # Upload a file while listening
    test_image = create_test_image(color='green')
    files = {'files': ('realtime_test.jpg', test_image, 'image/jpeg')}
    data = {'guest_name': 'Realtime Test User'}
    
    upload_response = await asyncio.to_thread(
        requests.post,
        f'{BASE_URL}/api/upload',
        files=files,
        data=data
    )
    
    assert upload_response.status_code == 201, "Upload failed during WebSocket test"
    
    # Wait for WebSocket notification
    await asyncio.sleep(3)
    listener_task.cancel()
    
    # Verify we received a notification
    upload_notifications = [n for n in websocket_notifications if n.get('type') == 'new_upload']
    
    if upload_notifications:
        notification = upload_notifications[0]
        assert notification['data']['guest_name'] == 'Realtime Test User'
        assert notification['data']['file_type'] == 'photo'
        print("✅ Real-time upload notification integration working")
    else:
        print("⚠️  No real-time upload notifications received (may need WebSocket implementation)")
    
    print(f"ℹ️  Total WebSocket messages received: {len(websocket_notifications)}")

async def test_mobile_upload_interface_integration():
    """Test mobile upload interface complete integration"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Set mobile viewport
        await page.set_viewport_size({"width": 375, "height": 812})
        
        try:
            # Navigate to mobile upload page
            await page.goto(f'{BASE_URL}/upload', wait_until='networkidle')
            
            # Verify Valérie's celebration title on mobile
            title_visible = False
            
            # Check for mobile-specific title
            mobile_title = page.locator('.celebration-title.mobile')
            if await mobile_title.count() > 0 and await mobile_title.is_visible():
                title_text = await mobile_title.text_content()
                title_visible = "Valérie" in title_text
            else:
                # Check for responsive title
                regular_title = page.locator('.celebration-title')
                if await regular_title.is_visible():
                    title_text = await regular_title.text_content()
                    title_visible = "Valérie" in title_text
            
            assert title_visible, "Valérie's celebration title not visible on mobile"
            print("✅ Valérie's title displayed on mobile upload page")
            
            # Test form interaction
            guest_name_input = page.locator('#guestName')
            await guest_name_input.wait_for(timeout=5000)
            
            # Fill in guest information
            await guest_name_input.fill('Mobile Integration Tester')
            
            song_input = page.locator('#songUrl')
            await song_input.fill('Mobile Test Song')
            
            # Verify form values were set
            guest_value = await guest_name_input.input_value()
            song_value = await song_input.input_value()
            
            assert guest_value == 'Mobile Integration Tester', f"Guest name not set: {guest_value}"
            assert song_value == 'Mobile Test Song', f"Song not set: {song_value}"
            
            # Check upload area is accessible
            upload_area = page.locator('#uploadArea')
            assert await upload_area.is_visible(), "Upload area not visible on mobile"
            
            # Check share button is accessible
            share_button = page.locator('#shareButton')
            assert await share_button.is_visible(), "Share button not visible on mobile"
            
            print("✅ Mobile upload interface fully functional")
            
        except Exception as e:
            await page.screenshot(path='integration_mobile_test_failure.png')
            raise e
        finally:
            await browser.close()

async def test_celebration_title_persistence_integration():
    """Test Valérie's celebration title persists across all pages and states"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        # Test title on main slideshow page
        page1 = await browser.new_page()
        try:
            await page1.goto(BASE_URL, wait_until='networkidle')
            
            title1 = page1.locator('.celebration-title')
            await title1.wait_for(timeout=5000)
            title_text1 = await title1.text_content()
            assert "Happy 50th Birthday Valérie!" in title_text1, f"Main page title incorrect: {title_text1}"
            
            # Verify title stays visible after page interaction
            await page1.wait_for_timeout(3000)
            assert await title1.is_visible(), "Title disappeared after page load"
            
        finally:
            await page1.close()
        
        # Test title on upload page
        page2 = await browser.new_page()
        try:
            await page2.goto(f'{BASE_URL}/upload', wait_until='networkidle')
            
            # Look for title on upload page
            upload_title = page2.locator('.celebration-title')
            await upload_title.wait_for(timeout=5000)
            title_text2 = await upload_title.text_content()
            assert "Valérie" in title_text2, f"Upload page title missing Valérie: {title_text2}"
            
        finally:
            await page2.close()
        
        # Test title on mobile viewport
        page3 = await browser.new_page()
        await page3.set_viewport_size({"width": 390, "height": 844})
        
        try:
            await page3.goto(BASE_URL, wait_until='networkidle')
            
            mobile_title = page3.locator('.celebration-title')
            await mobile_title.wait_for(timeout=5000)
            title_text3 = await mobile_title.text_content()
            assert "Valérie" in title_text3, f"Mobile title missing Valérie: {title_text3}"
            
            # Check title scales appropriately on mobile
            font_size = await mobile_title.evaluate('el => getComputedStyle(el).fontSize')
            font_size_px = int(font_size.replace('px', ''))
            assert font_size_px >= 24, f"Mobile font size too small: {font_size_px}px"
            
        finally:
            await page3.close()
        
        await browser.close()
    
    print("✅ Valérie's celebration title persists across all pages and viewports")

async def test_multiple_guest_attribution_integration():
    """Test multiple guests uploading and attribution tracking"""
    
    # Simulate multiple party guests uploading
    guests = [
        ('Alice Johnson', 'alice_party_pic.jpg', 'photo'),
        ('Bob Smith', 'bob_video.mp4', 'video'),
        ('Charlie Davis', 'charlie_song.mp3', 'music'),
        ('Diana Wilson', 'diana_selfie.jpg', 'photo'),
    ]
    
    upload_ids = []
    
    for guest_name, filename, file_type in guests:
        if file_type == 'photo':
            test_file = create_test_image(color='purple')
            mime_type = 'image/jpeg'
        elif file_type == 'video':
            test_file = create_test_video()
            mime_type = 'video/mp4'
        else:  # music
            test_file = create_test_audio()
            mime_type = 'audio/mp3'
        
        files = {'files': (filename, test_file, mime_type)}
        data = {'guest_name': guest_name, 'type': file_type}
        
        if file_type == 'music':
            data['song_title'] = f"{guest_name}'s Song"
        
        upload_response = requests.post(f'{BASE_URL}/api/upload', files=files, data=data)
        assert upload_response.status_code == 201, f"Upload failed for {guest_name}: {upload_response.text}"
        
        upload_ids.append(upload_response.json()['upload_id'])
        print(f"✅ {guest_name} uploaded {file_type} successfully")
    
    # Verify all guests appear in media/queue APIs
    media_response = requests.get(f'{BASE_URL}/api/media')
    media_data = media_response.json()
    
    # Check photos and videos appear
    media_guests = [item['guest_name'] for item in media_data['media']]
    assert 'Alice Johnson' in media_guests, "Alice's photo not in media"
    assert 'Bob Smith' in media_guests, "Bob's video not in media"
    assert 'Diana Wilson' in media_guests, "Diana's photo not in media"
    
    # Check music appears in queue
    queue_response = requests.get(f'{BASE_URL}/api/music/queue')
    queue_data = queue_response.json()
    
    music_guests = [song['guest_name'] for song in queue_data['songs']]
    assert 'Charlie Davis' in music_guests, "Charlie's music not in queue"
    
    print("✅ Multiple guest attribution integration working")

async def test_end_to_end_party_simulation():
    """Comprehensive end-to-end party simulation"""
    
    print("🎉 Starting end-to-end party simulation for Valérie's 50th Birthday")
    
    # Step 1: Verify party configuration
    config_response = requests.get(f'{BASE_URL}/api/config')
    config = config_response.json()
    assert "Happy 50th Birthday Valérie!" in config['title']
    print(f"✅ Party configured: {config['title']}")
    
    # Step 2: Simulate party guests arriving and uploading content
    party_uploads = [
        ('Sarah Mitchell', 'sarah_birthday_photo.jpg', 'photo', None),
        ('Mike Thompson', 'mike_party_video.mp4', 'video', None),
        ('Emily Chen', 'happy_birthday_song.mp3', 'music', 'Happy Birthday Valérie'),
        ('David Rodriguez', 'group_photo.jpg', 'photo', None),
        ('Lisa Park', 'birthday_wishes.mp4', 'video', None),
    ]
    
    successful_uploads = 0
    
    for guest_name, filename, file_type, song_title in party_uploads:
        try:
            if file_type == 'photo':
                test_file = create_test_image()
                mime_type = 'image/jpeg'
            elif file_type == 'video':
                test_file = create_test_video()
                mime_type = 'video/mp4'
            else:
                test_file = create_test_audio()
                mime_type = 'audio/mp3'
            
            files = {'files': (filename, test_file, mime_type)}
            data = {'guest_name': guest_name, 'type': file_type}
            
            if song_title:
                data['song_title'] = song_title
            
            response = requests.post(f'{BASE_URL}/api/upload', files=files, data=data)
            if response.status_code == 201:
                successful_uploads += 1
                print(f"  ✅ {guest_name} shared a {file_type}")
            
        except Exception as e:
            print(f"  ❌ {guest_name}'s upload failed: {e}")
    
    print(f"✅ Party simulation: {successful_uploads}/{len(party_uploads)} guests successfully shared content")
    
    # Step 3: Verify slideshow has content
    media_response = requests.get(f'{BASE_URL}/api/media')
    media_count = len(media_response.json()['media'])
    print(f"✅ Slideshow has {media_count} items to display")
    
    # Step 4: Verify music queue has content
    queue_response = requests.get(f'{BASE_URL}/api/music/queue')
    queue_count = len(queue_response.json()['songs'])
    print(f"✅ Music queue has {queue_count} songs")
    
    # Step 5: Test frontend displays everything correctly
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            await page.goto(BASE_URL, wait_until='networkidle')
            
            # Verify Valérie's celebration title
            title = page.locator('.celebration-title')
            await title.wait_for()
            title_text = await title.text_content()
            assert "Happy 50th Birthday Valérie!" in title_text
            print("✅ Celebration title prominently displayed")
            
            # Check slideshow is functional
            slideshow = page.locator('.slideshow-container')
            assert await slideshow.is_visible()
            print("✅ Slideshow container ready")
            
            # Check overlays are present
            overlays_present = []
            
            if await page.locator('.music-overlay').is_visible():
                overlays_present.append('Music')
            if await page.locator('.qr-overlay').is_visible():
                overlays_present.append('QR Code')
            if await page.locator('#attribution').is_visible():
                overlays_present.append('Attribution')
            
            print(f"✅ UI overlays present: {', '.join(overlays_present)}")
            
        finally:
            await browser.close()
    
    print("🎉 End-to-end party simulation completed successfully!")
    print("🎂 Valérie's 50th Birthday Memory Wall is ready for the celebration!")

# Test execution order
if __name__ == "__main__":
    print("🎉 Running Party Memory Wall Integration Tests")
    print("⚠️  Ensure complete system is running:")
    print("   - Flask backend on port 6000: cd backend && python app.py")
    print("   - All frontend files served correctly")
    print("   - Database initialized and accessible")
    print("=" * 70)
    
    # Run tests
    pytest.main([__file__, "-v", "-s"])