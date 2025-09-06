# Testing Strategy for Party Memory Wall

## Critical Testing Requirements for All Agents

### MANDATORY ENVIRONMENT SETUP:
1. **Flask MUST run on port 6000** - This is non-negotiable for all testing
2. **Use existing MCP Playwright server** - DO NOT install new Playwright
3. **All tests go in /test folder** - No exceptions
4. **Test both photos AND videos** - Full media support validation
5. **Test celebration title** - Permanent display and animations

## Test Environment Configuration

### Starting the Application for Testing:
```bash
# Backend setup
cd backend
python app.py  # MUST run on port 6000

# Verify correct port
curl http://localhost:6000/api/config
# Should return party configuration including Valérie's title
```

### Available Testing Tools:
- **MCP Playwright server** (already installed) - For UI testing
- **Python requests library** - For API testing  
- **WebSocket client** - For real-time testing
- **SQLite CLI** - For database validation

## Backend Testing Strategy

### test/test_upload_api.py
**Purpose**: Test Flask API endpoints and file upload functionality

```python
import pytest
import requests
import json
from io import BytesIO
from PIL import Image

BASE_URL = 'http://localhost:6000'

def create_test_image():
    """Create a test image file for upload testing"""
    img = Image.new('RGB', (100, 100), color='red')
    img_buffer = BytesIO()
    img.save(img_buffer, format='JPEG')
    img_buffer.seek(0)
    return img_buffer

def test_flask_running_on_port_6000():
    """CRITICAL: Verify Flask runs on correct port"""
    try:
        response = requests.get(f'{BASE_URL}/api/config', timeout=5)
        assert response.status_code == 200, "Flask not running on port 6000"
        
        config = response.json()
        assert 'title' in config, "Config missing title"
        assert "Valérie" in config['title'], "Missing Valérie's name in title"
        
    except requests.exceptions.ConnectionError:
        pytest.fail("Flask is not running on port 6000. Start with: python backend/app.py")

def test_party_configuration():
    """Test party configuration endpoint returns Valérie's celebration details"""
    response = requests.get(f'{BASE_URL}/api/config')
    assert response.status_code == 200
    
    config = response.json()
    assert config['title'] == "Happy 50th Birthday Valérie!"
    assert config['slideshow_duration'] == 15
    assert config['max_file_size'] == 500 * 1024 * 1024  # 500MB

def test_photo_upload():
    """Test photo upload endpoint"""
    test_image = create_test_image()
    
    files = {'files': ('test_photo.jpg', test_image, 'image/jpeg')}
    data = {'guest_name': 'TestUser', 'type': 'photo'}
    
    response = requests.post(f'{BASE_URL}/api/upload', files=files, data=data)
    assert response.status_code == 201
    
    result = response.json()
    assert 'upload_id' in result
    assert result['message'] == 'Upload successful'

def test_video_upload():
    """Test video upload handling"""
    # Create minimal MP4 file for testing
    video_data = b'fake video content for testing'
    
    files = {'files': ('test_video.mp4', BytesIO(video_data), 'video/mp4')}
    data = {'guest_name': 'VideoUser', 'type': 'video'}
    
    response = requests.post(f'{BASE_URL}/api/upload', files=files, data=data)
    assert response.status_code == 201
    
    # Verify video was processed and stored
    result = response.json()
    assert 'upload_id' in result

def test_music_upload_and_queue():
    """Test music upload and queue addition"""
    music_data = b'fake audio content for testing'
    
    files = {'files': ('test_song.mp3', BytesIO(music_data), 'audio/mp3')}
    data = {'guest_name': 'MusicUser', 'type': 'music'}
    
    response = requests.post(f'{BASE_URL}/api/upload', files=files, data=data)
    assert response.status_code == 201
    
    # Check music queue
    queue_response = requests.get(f'{BASE_URL}/api/music/queue')
    assert queue_response.status_code == 200
    queue = queue_response.json()
    assert len(queue['songs']) > 0

def test_media_slideshow_endpoint():
    """Test media retrieval for slideshow"""
    response = requests.get(f'{BASE_URL}/api/media')
    assert response.status_code == 200
    
    data = response.json()
    assert 'media' in data
    assert 'total_count' in data
    
    # Verify media items have required fields
    if data['media']:
        media_item = data['media'][0]
        assert 'id' in media_item
        assert 'type' in media_item  # 'photo' or 'video'
        assert 'url' in media_item
        assert 'guest_name' in media_item
        assert 'timestamp' in media_item

def test_large_file_handling():
    """Test file size limits and validation"""
    # Test file too large (over 500MB limit)
    large_data = b'x' * (501 * 1024 * 1024)  # 501MB
    
    files = {'files': ('large_file.jpg', BytesIO(large_data), 'image/jpeg')}
    data = {'guest_name': 'TestUser'}
    
    response = requests.post(f'{BASE_URL}/api/upload', files=files, data=data)
    assert response.status_code == 413  # Payload Too Large
    
    error = response.json()
    assert 'File too large' in error['error']

def test_invalid_file_type():
    """Test rejection of invalid file types"""
    invalid_file = BytesIO(b'not a valid media file')
    
    files = {'files': ('test.txt', invalid_file, 'text/plain')}
    data = {'guest_name': 'TestUser'}
    
    response = requests.post(f'{BASE_URL}/api/upload', files=files, data=data)
    assert response.status_code == 400
    
    error = response.json()
    assert 'Invalid file type' in error['error']
```

### test/test_database.py
**Purpose**: Test SQLite database operations

```python
import pytest
import sqlite3
import os
from backend.database import PartyDatabase

def test_database_creation():
    """Test database initialization and table creation"""
    # Use temporary database for testing
    test_db_path = ':memory:'
    db = PartyDatabase(test_db_path)
    
    # Verify tables exist
    conn = db.get_connection()
    cursor = conn.cursor()
    
    tables = cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table'
    """).fetchall()
    
    table_names = [table[0] for table in tables]
    assert 'uploads' in table_names
    assert 'music_queue' in table_names
    assert 'settings' in table_names
    assert 'devices' in table_names

def test_add_upload_record():
    """Test adding upload records to database"""
    db = PartyDatabase(':memory:')
    
    upload_id = db.add_upload(
        device_id='test-device-123',
        guest_name='Sarah Johnson',
        file_path='/media/photos/test_photo.jpg',
        file_type='photo',
        original_filename='birthday_pic.jpg',
        file_size=2048000
    )
    
    assert upload_id is not None
    assert isinstance(upload_id, int)
    
    # Verify record was saved
    upload = db.get_upload(upload_id)
    assert upload['guest_name'] == 'Sarah Johnson'
    assert upload['file_type'] == 'photo'
    assert upload['device_id'] == 'test-device-123'

def test_slideshow_media_retrieval():
    """Test getting media for slideshow display"""
    db = PartyDatabase(':memory:')
    
    # Add test media records
    db.add_upload('device1', 'User1', '/media/photos/1.jpg', 'photo', 'pic1.jpg', 1024)
    db.add_upload('device2', 'User2', '/media/videos/1.mp4', 'video', 'vid1.mp4', 5120000)
    db.add_upload('device3', 'User3', '/media/photos/2.jpg', 'photo', 'pic2.jpg', 2048)
    
    media = db.get_slideshow_media()
    assert len(media) == 3
    
    # Verify order (should be by timestamp)
    assert media[0]['guest_name'] == 'User1'
    assert media[1]['guest_name'] == 'User2'
    assert media[2]['guest_name'] == 'User3'
    
    # Verify required fields
    for item in media:
        assert 'id' in item
        assert 'type' in item
        assert 'guest_name' in item
        assert 'file_path' in item

def test_music_queue_operations():
    """Test music queue management"""
    db = PartyDatabase(':memory:')
    
    # Add music upload
    upload_id = db.add_upload('device1', 'DJ Mike', '/media/music/song.mp3', 'music', 'song.mp3', 4096000)
    
    # Add to music queue
    queue_id = db.add_to_music_queue(
        upload_id=upload_id,
        song_title='Summer Vibes',
        artist='Unknown Artist',
        duration=240
    )
    
    assert queue_id is not None
    
    # Get music queue
    queue = db.get_music_queue()
    assert len(queue) == 1
    assert queue[0]['song_title'] == 'Summer Vibes'
    assert queue[0]['guest_name'] == 'DJ Mike'
    
    # Mark as played
    db.mark_music_played(queue_id)
    
    played_song = db.get_queue_item(queue_id)
    assert played_song['played'] is True

def test_device_tracking():
    """Test device tracking for attribution"""
    db = PartyDatabase(':memory:')
    
    device_id = 'iphone-sarah-123'
    
    # First upload from device
    db.add_upload(device_id, 'Sarah', '/media/photos/1.jpg', 'photo', '1.jpg', 1024)
    
    device_info = db.get_device_info(device_id)
    assert device_info['guest_name'] == 'Sarah'
    assert device_info['total_uploads'] == 1
    
    # Second upload from same device
    db.add_upload(device_id, 'Sarah', '/media/photos/2.jpg', 'photo', '2.jpg', 2048)
    
    device_info = db.get_device_info(device_id)
    assert device_info['total_uploads'] == 2
```

### test/test_websocket.py
**Purpose**: Test WebSocket real-time updates

```python
import pytest
import asyncio
import websockets
import json
import requests
from io import BytesIO

BASE_URL = 'http://localhost:6000'
WS_URL = 'ws://localhost:6000/ws'

async def test_websocket_connection():
    """Test WebSocket connection establishment"""
    try:
        async with websockets.connect(WS_URL) as websocket:
            # Connection successful if we get here
            assert websocket.open
            
            # Send ping to test connection
            await websocket.ping()
            
    except Exception as e:
        pytest.fail(f"WebSocket connection failed: {e}")

async def test_new_upload_broadcast():
    """Test that new uploads trigger WebSocket broadcast"""
    async with websockets.connect(WS_URL) as websocket:
        
        # Upload a test file
        test_image = BytesIO(b'fake image data')
        files = {'files': ('test.jpg', test_image, 'image/jpeg')}
        data = {'guest_name': 'TestUser'}
        
        # Start upload in background
        upload_task = asyncio.create_task(
            asyncio.to_thread(
                requests.post, 
                f'{BASE_URL}/api/upload', 
                files=files, 
                data=data
            )
        )
        
        # Wait for WebSocket message
        message = await asyncio.wait_for(websocket.recv(), timeout=10)
        event = json.loads(message)
        
        assert event['type'] == 'new_upload'
        assert event['data']['guest_name'] == 'TestUser'
        assert event['data']['file_type'] == 'photo'
        
        # Wait for upload to complete
        response = await upload_task
        assert response.status_code == 201

async def test_music_update_broadcast():
    """Test music queue updates via WebSocket"""
    async with websockets.connect(WS_URL) as websocket:
        
        # Add music to queue
        music_data = BytesIO(b'fake music data')
        files = {'files': ('song.mp3', music_data, 'audio/mp3')}
        data = {'guest_name': 'DJ Test', 'song_title': 'Test Song'}
        
        upload_task = asyncio.create_task(
            asyncio.to_thread(
                requests.post,
                f'{BASE_URL}/api/upload',
                files=files,
                data=data
            )
        )
        
        # Wait for WebSocket update
        message = await asyncio.wait_for(websocket.recv(), timeout=10)
        event = json.loads(message)
        
        assert event['type'] == 'music_update'
        assert 'now_playing' in event['data'] or 'queue_length' in event['data']
        
        await upload_task

def test_websocket_multiple_clients():
    """Test WebSocket handles multiple concurrent connections"""
    async def client_handler():
        async with websockets.connect(WS_URL) as websocket:
            # Keep connection open for 5 seconds
            await asyncio.sleep(5)
            return "Connected"
    
    # Run multiple clients concurrently
    async def run_test():
        tasks = [client_handler() for _ in range(5)]
        results = await asyncio.gather(*tasks)
        assert len(results) == 5
        assert all(result == "Connected" for result in results)
    
    asyncio.run(run_test())
```

## Frontend Testing Strategy

### test/test_frontend.py
**Purpose**: Test frontend UI using existing MCP Playwright

```python
from playwright.async_api import async_playwright
import pytest

async def test_celebration_title_always_visible():
    """CRITICAL: Test Valérie's celebration title is permanently displayed"""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto('http://localhost:6000/')
        
        # Check title exists and contains correct text
        title_element = page.locator('.celebration-title')
        await title_element.wait_for()
        
        title_text = await title_element.text_content()
        assert "Happy 50th Birthday Valérie!" in title_text
        assert "✨" in title_text  # Check for sparkles
        
        # Verify title is always on top (high z-index)
        z_index = await title_element.evaluate('el => getComputedStyle(el).zIndex')
        assert int(z_index) >= 9999
        
        # Check title remains visible after slideshow starts
        await page.wait_for_timeout(2000)
        assert await title_element.is_visible()
        
        # Check title has animation (shimmer effect)
        animation_name = await title_element.evaluate('el => getComputedStyle(el).animationName')
        assert 'shimmer' in animation_name
        
        await browser.close()

async def test_slideshow_functionality():
    """Test slideshow display and auto-advance"""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto('http://localhost:6000/')
        
        # Wait for slideshow to initialize
        await page.wait_for_selector('.slideshow-container')
        
        # Check if slides exist
        slides = await page.locator('.slide').count()
        if slides > 1:
            # Get first active slide
            first_active = await page.locator('.slide.active').get_attribute('data-index')
            
            # Wait for slide transition (15+ seconds)
            await page.wait_for_timeout(16000)
            
            # Check if slide changed
            second_active = await page.locator('.slide.active').get_attribute('data-index')
            assert first_active != second_active, "Slideshow not advancing automatically"
        
        await browser.close()

async def test_upload_interface_mobile():
    """Test mobile upload interface"""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        # Set mobile viewport
        await page.set_viewport_size({"width": 375, "height": 812})
        await page.goto('http://localhost:6000/upload')
        
        # Check mobile celebration title exists
        mobile_title = page.locator('.celebration-title.mobile')
        await mobile_title.wait_for()
        
        title_text = await mobile_title.text_content()
        assert "Valérie" in title_text
        
        # Check upload area is visible and functional
        upload_area = page.locator('#uploadArea')
        await upload_area.wait_for()
        assert await upload_area.is_visible()
        
        # Check form fields exist
        guest_name_input = page.locator('#guestName')
        song_input = page.locator('#songUrl')
        share_button = page.locator('#shareButton')
        
        assert await guest_name_input.is_visible()
        assert await song_input.is_visible()
        assert await share_button.is_visible()
        
        await browser.close()

async def test_websocket_connection_frontend():
    """Test WebSocket connection from frontend"""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        # Listen for console messages (WebSocket events)
        console_messages = []
        page.on('console', lambda msg: console_messages.append(msg.text))
        
        await page.goto('http://localhost:6000/')
        
        # Wait for WebSocket connection
        await page.wait_for_timeout(3000)
        
        # Check for WebSocket connection message in console
        websocket_connected = any('WebSocket' in msg or 'ws' in msg for msg in console_messages)
        # Note: This test depends on frontend logging WebSocket events
        
        await browser.close()

async def test_qr_code_display():
    """Test QR code is displayed for sharing"""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto('http://localhost:6000/')
        
        # Check QR code overlay exists
        qr_overlay = page.locator('.qr-overlay')
        await qr_overlay.wait_for()
        
        # Check QR code image
        qr_image = page.locator('#qrCode')
        assert await qr_image.is_visible()
        
        # Check QR code has valid src
        qr_src = await qr_image.get_attribute('src')
        assert qr_src is not None
        assert len(qr_src) > 0
        
        await browser.close()

async def test_attribution_display():
    """Test guest attribution is shown"""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto('http://localhost:6000/')
        
        # Wait for content to load
        await page.wait_for_timeout(2000)
        
        # Check attribution overlay exists
        attribution = page.locator('#attribution')
        if await attribution.is_visible():
            attribution_text = await attribution.text_content()
            # Should show guest name or "Anonymous"
            assert "From:" in attribution_text
            assert len(attribution_text) > 5
        
        await browser.close()

async def test_performance_animations():
    """Test animations perform well (basic performance check)"""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto('http://localhost:6000/')
        
        # Check CSS animations are hardware accelerated
        title_element = page.locator('.celebration-title')
        transform = await title_element.evaluate('el => getComputedStyle(el).transform')
        
        # GPU acceleration should set transform
        assert transform != 'none'
        
        await browser.close()
```

## Integration Testing

### test/test_integration.py
**Purpose**: Test complete workflow from upload to display

```python
import pytest
import requests
import asyncio
import websockets
from playwright.async_api import async_playwright
from io import BytesIO

async def test_complete_upload_to_display_workflow():
    """Test full workflow: upload photo -> see on slideshow"""
    
    # Step 1: Upload a photo
    test_image = BytesIO(b'fake image data for integration test')
    files = {'files': ('integration_test.jpg', test_image, 'image/jpeg')}
    data = {'guest_name': 'Integration Tester'}
    
    upload_response = requests.post('http://localhost:6000/api/upload', files=files, data=data)
    assert upload_response.status_code == 201
    
    upload_id = upload_response.json()['upload_id']
    
    # Step 2: Verify photo appears in media API
    media_response = requests.get('http://localhost:6000/api/media')
    assert media_response.status_code == 200
    
    media_data = media_response.json()
    uploaded_item = None
    for item in media_data['media']:
        if item.get('guest_name') == 'Integration Tester':
            uploaded_item = item
            break
    
    assert uploaded_item is not None
    assert uploaded_item['type'] == 'photo'
    
    # Step 3: Check slideshow displays the photo
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto('http://localhost:6000/')
        
        # Wait for slideshow to load
        await page.wait_for_timeout(3000)
        
        # Look for attribution with our test user name
        attribution = page.locator('#attribution')
        if await attribution.is_visible():
            attribution_text = await attribution.text_content()
            # May need to wait for our photo to cycle through
            # This is a basic check - more sophisticated timing needed for full validation
        
        await browser.close()

async def test_websocket_real_time_update():
    """Test WebSocket broadcasts upload to connected clients"""
    
    # Connect WebSocket client
    websocket_messages = []
    
    async def websocket_listener():
        async with websockets.connect('ws://localhost:6000/ws') as websocket:
            try:
                while True:
                    message = await asyncio.wait_for(websocket.recv(), timeout=1)
                    websocket_messages.append(message)
            except asyncio.TimeoutError:
                pass
    
    # Start WebSocket listener
    listener_task = asyncio.create_task(websocket_listener())
    
    # Give WebSocket time to connect
    await asyncio.sleep(1)
    
    # Upload file
    test_image = BytesIO(b'websocket test image')
    files = {'files': ('ws_test.jpg', test_image, 'image/jpeg')}
    data = {'guest_name': 'WebSocket Tester'}
    
    upload_response = await asyncio.to_thread(
        requests.post,
        'http://localhost:6000/api/upload',
        files=files,
        data=data
    )
    
    assert upload_response.status_code == 201
    
    # Wait for WebSocket message
    await asyncio.sleep(2)
    listener_task.cancel()
    
    # Check if we received a WebSocket message about the upload
    assert len(websocket_messages) > 0
    
    # Parse and verify message
    import json
    for msg in websocket_messages:
        event = json.loads(msg)
        if event.get('type') == 'new_upload':
            assert event['data']['guest_name'] == 'WebSocket Tester'
            return
    
    pytest.fail("No new_upload WebSocket message received")
```

## Performance Testing for Raspberry Pi

### test/test_performance.py
**Purpose**: Validate performance on Raspberry Pi 4B

```python
import pytest
import time
import psutil
import requests
from concurrent.futures import ThreadPoolExecutor

def test_concurrent_uploads():
    """Test system handles multiple simultaneous uploads"""
    
    def upload_file(user_id):
        test_image = BytesIO(f'test image data for user {user_id}'.encode())
        files = {'files': (f'test_{user_id}.jpg', test_image, 'image/jpeg')}
        data = {'guest_name': f'User{user_id}'}
        
        start_time = time.time()
        response = requests.post('http://localhost:6000/api/upload', files=files, data=data)
        end_time = time.time()
        
        return {
            'user_id': user_id,
            'status_code': response.status_code,
            'response_time': end_time - start_time
        }
    
    # Simulate 10 concurrent uploads
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(upload_file, i) for i in range(10)]
        results = [future.result() for future in futures]
    
    # All uploads should succeed
    success_count = sum(1 for r in results if r['status_code'] == 201)
    assert success_count >= 8  # Allow for some failures under load
    
    # Average response time should be reasonable
    avg_response_time = sum(r['response_time'] for r in results) / len(results)
    assert avg_response_time < 10  # 10 seconds max average

def test_memory_usage():
    """Test memory usage stays within reasonable limits"""
    process = psutil.Process()
    
    # Get baseline memory usage
    baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    # Upload several files
    for i in range(20):
        test_data = BytesIO(f'memory test data {i}' * 1000)  # ~20KB each
        files = {'files': (f'mem_test_{i}.jpg', test_data, 'image/jpeg')}
        data = {'guest_name': f'MemTest{i}'}
        
        response = requests.post('http://localhost:6000/api/upload', files=files, data=data)
        assert response.status_code == 201
    
    # Check memory usage after uploads
    final_memory = process.memory_info().rss / 1024 / 1024  # MB
    memory_increase = final_memory - baseline_memory
    
    # Memory increase should be reasonable (less than 100MB for test data)
    assert memory_increase < 100, f"Memory usage increased by {memory_increase}MB"

def test_slideshow_animation_performance():
    """Test slideshow animations don't cause excessive CPU usage"""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto('http://localhost:6000/')
        
        # Let slideshow run for 30 seconds
        start_time = time.time()
        while time.time() - start_time < 30:
            await page.wait_for_timeout(1000)
            
            # Check CPU usage periodically
            cpu_percent = psutil.cpu_percent(interval=1)
            # On RPi 4B, should not exceed 80% CPU for slideshow
            if cpu_percent > 80:
                pytest.fail(f"CPU usage too high: {cpu_percent}%")
        
        await browser.close()
```

## Test Execution Instructions for Agents

### Running Backend Tests:
```bash
# Start Flask application
cd backend && python app.py &  # MUST be port 6000

# Run backend tests
python -m pytest test/test_upload_api.py -v
python -m pytest test/test_database.py -v  
python -m pytest test/test_websocket.py -v
```

### Running Frontend Tests:
```bash
# Ensure Flask is running on port 6000
curl http://localhost:6000/api/config

# Run Playwright tests (using existing MCP server)
python -m pytest test/test_frontend.py -v
```

### Running Integration Tests:
```bash
# Full system must be running
python -m pytest test/test_integration.py -v
python -m pytest test/test_performance.py -v
```

## Test Failure Debugging

### Common Issues and Solutions:

1. **Flask not on port 6000**:
   - Check `python app.py` output
   - Verify no other service using port 6000
   - Check Flask configuration

2. **Playwright tests failing**:
   - Ensure using existing MCP Playwright (no installation)
   - Check browser console for JavaScript errors
   - Verify all frontend files are served correctly

3. **WebSocket tests failing**:
   - Check WebSocket server is enabled in Flask
   - Verify port 6000 WebSocket endpoint accessible
   - Check firewall settings

4. **Database tests failing**:
   - Check SQLite file permissions
   - Verify database schema matches requirements
   - Check file path configurations

5. **Performance tests failing**:
   - Run on Raspberry Pi 4B for accurate results
   - Ensure no other heavy processes running
   - Check available RAM and storage space

## Coverage Requirements

All tests must achieve:
- **Backend API**: 90%+ endpoint coverage
- **Database operations**: 95%+ function coverage  
- **Frontend UI**: All major user flows tested
- **WebSocket events**: All event types tested
- **Error handling**: All error conditions tested
- **Performance**: RPi 4B optimization validated

Remember: **Flask MUST run on port 6000** for ALL testing!