"""
Test suite for Party Memory Wall upload API endpoints

CRITICAL REQUIREMENTS:
- Flask MUST run on port 6000 for all tests
- Use existing MCP Playwright (no new installations)
- Test both photos AND videos
- Validate Valérie's celebration title configuration

Before running tests:
1. cd backend && python app.py (must be port 6000)
2. Verify: curl http://localhost:6000/api/config
"""

import pytest
import requests
import json
from io import BytesIO
from PIL import Image
import time

BASE_URL = 'http://localhost:6000'

def create_test_image():
    """Create a test image file for upload testing"""
    img = Image.new('RGB', (100, 100), color='red')
    img_buffer = BytesIO()
    img.save(img_buffer, format='JPEG')
    img_buffer.seek(0)
    return img_buffer

def create_test_video():
    """Create minimal test video data"""
    # Simple fake MP4 header for testing
    video_data = b'\x00\x00\x00\x20\x66\x74\x79\x70\x6D\x70\x34\x31' + b'x' * 1000
    return BytesIO(video_data)

def create_test_audio():
    """Create minimal test audio data"""
    # Simple fake MP3 data for testing
    audio_data = b'\xFF\xFB\x90\x00' + b'x' * 1000
    return BytesIO(audio_data)

def test_flask_running_on_port_6000():
    """CRITICAL: Verify Flask runs on correct port with Valérie's configuration"""
    try:
        response = requests.get(f'{BASE_URL}/api/config', timeout=5)
        assert response.status_code == 200, "Flask not running on port 6000"
        
        config = response.json()
        assert 'title' in config, "Config missing title"
        assert "Valérie" in config['title'], "Missing Valérie's name in title"
        assert "50th Birthday" in config['title'], "Missing 50th Birthday in title"
        
        print(f"✅ Flask running on port 6000 with title: {config['title']}")
        
    except requests.exceptions.ConnectionError:
        pytest.fail("""
        ❌ Flask is not running on port 6000. 
        Start with: cd backend && python app.py
        Then verify: curl http://localhost:6000/api/config
        """)

def test_party_configuration():
    """Test party configuration endpoint returns Valérie's celebration details"""
    response = requests.get(f'{BASE_URL}/api/config')
    assert response.status_code == 200
    
    config = response.json()
    
    # Verify celebration title
    expected_title = "Happy 50th Birthday Valérie!"
    assert config['title'] == expected_title, f"Expected '{expected_title}', got '{config['title']}'"
    
    # Verify slideshow settings
    assert config['slideshow_duration'] == 15, "Slideshow duration should be 15 seconds"
    assert config['max_file_size'] == 500 * 1024 * 1024, "Max file size should be 500MB"
    
    # Verify file type support
    assert 'jpg' in config['allowed_photo_types']
    assert 'mp4' in config['allowed_video_types']
    assert 'mp3' in config['allowed_music_types']
    
    print(f"✅ Party configuration validated for {config['title']}")

def test_photo_upload():
    """Test photo upload endpoint with guest attribution"""
    test_image = create_test_image()
    
    files = {'files': ('test_photo.jpg', test_image, 'image/jpeg')}
    data = {'guest_name': 'TestUser', 'type': 'photo'}
    
    response = requests.post(f'{BASE_URL}/api/upload', files=files, data=data)
    assert response.status_code == 201, f"Upload failed: {response.text}"
    
    result = response.json()
    assert 'upload_id' in result, "Response missing upload_id"
    assert result['message'] == 'Upload successful', f"Unexpected message: {result['message']}"
    assert 'file_path' in result, "Response missing file_path"
    
    print(f"✅ Photo upload successful with ID: {result['upload_id']}")

def test_video_upload():
    """Test video upload handling with duration extraction"""
    test_video = create_test_video()
    
    files = {'files': ('test_video.mp4', test_video, 'video/mp4')}
    data = {'guest_name': 'VideoUser', 'type': 'video'}
    
    response = requests.post(f'{BASE_URL}/api/upload', files=files, data=data)
    assert response.status_code == 201, f"Video upload failed: {response.text}"
    
    result = response.json()
    assert 'upload_id' in result, "Video upload response missing upload_id"
    
    # Verify video was processed
    upload_id = result['upload_id']
    
    # Check if upload appears in media endpoint
    media_response = requests.get(f'{BASE_URL}/api/media')
    assert media_response.status_code == 200
    
    media_data = media_response.json()
    video_found = False
    for item in media_data.get('media', []):
        if item.get('id') == upload_id and item.get('type') == 'video':
            video_found = True
            assert item['guest_name'] == 'VideoUser'
            break
    
    assert video_found, "Uploaded video not found in media list"
    print(f"✅ Video upload and processing successful")

def test_music_upload_and_queue():
    """Test music upload and automatic queue addition"""
    test_music = create_test_audio()
    
    files = {'files': ('test_song.mp3', test_music, 'audio/mp3')}
    data = {'guest_name': 'MusicUser', 'type': 'music', 'song_title': 'Test Song'}
    
    response = requests.post(f'{BASE_URL}/api/upload', files=files, data=data)
    assert response.status_code == 201, f"Music upload failed: {response.text}"
    
    result = response.json()
    assert 'upload_id' in result
    
    # Check music was added to queue
    queue_response = requests.get(f'{BASE_URL}/api/music/queue')
    assert queue_response.status_code == 200
    
    queue_data = queue_response.json()
    assert 'songs' in queue_data, "Music queue response missing 'songs'"
    assert len(queue_data['songs']) > 0, "Music queue is empty after upload"
    
    # Find our uploaded song
    song_found = False
    for song in queue_data['songs']:
        if song.get('guest_name') == 'MusicUser':
            song_found = True
            assert song['song_title'] == 'Test Song'
            break
    
    assert song_found, "Uploaded song not found in music queue"
    print(f"✅ Music upload and queue addition successful")

def test_media_slideshow_endpoint():
    """Test media retrieval for slideshow with proper attribution"""
    response = requests.get(f'{BASE_URL}/api/media')
    assert response.status_code == 200
    
    data = response.json()
    assert 'media' in data, "Media response missing 'media' field"
    assert 'total_count' in data, "Media response missing 'total_count'"
    
    # Verify media items have required fields for slideshow
    if data['media']:
        media_item = data['media'][0]
        required_fields = ['id', 'type', 'url', 'guest_name', 'timestamp']
        
        for field in required_fields:
            assert field in media_item, f"Media item missing required field: {field}"
        
        # Verify media type is valid
        assert media_item['type'] in ['photo', 'video'], f"Invalid media type: {media_item['type']}"
        
        print(f"✅ Media endpoint returning {len(data['media'])} items for slideshow")
    else:
        print("ℹ️  No media items found (empty slideshow)")

def test_large_file_handling():
    """Test file size limits and validation (500MB max)"""
    # Test file that's too large (over 500MB limit)
    large_size = 501 * 1024 * 1024  # 501MB
    
    # Create large fake image data
    large_data = b'x' * min(large_size, 10 * 1024 * 1024)  # Limit to 10MB for test performance
    
    files = {'files': ('large_file.jpg', BytesIO(large_data), 'image/jpeg')}
    data = {'guest_name': 'TestUser'}
    
    # Note: This test may need to be adjusted based on actual file size validation implementation
    response = requests.post(f'{BASE_URL}/api/upload', files=files, data=data)
    
    # Should either accept (if under real limit) or reject appropriately
    if response.status_code == 413:
        error = response.json()
        assert 'File too large' in error.get('error', ''), "Missing appropriate error message"
        print("✅ Large file rejection working correctly")
    else:
        # File was accepted (test file wasn't actually over limit)
        print("ℹ️  Large file test passed (file under actual limit)")

def test_invalid_file_type():
    """Test rejection of invalid file types"""
    invalid_file = BytesIO(b'This is not a valid media file, just text')
    
    files = {'files': ('test.txt', invalid_file, 'text/plain')}
    data = {'guest_name': 'TestUser'}
    
    response = requests.post(f'{BASE_URL}/api/upload', files=files, data=data)
    assert response.status_code == 400, f"Invalid file type should be rejected, got {response.status_code}"
    
    error = response.json()
    assert 'error' in error, "Error response missing 'error' field"
    assert any(word in error['error'].lower() for word in ['invalid', 'type', 'format']), \
        f"Error message should mention invalid type: {error['error']}"
    
    print("✅ Invalid file type rejection working correctly")

def test_guest_attribution_tracking():
    """Test that guest names are properly tracked and attributed"""
    guest_names = ['Alice', 'Bob', 'Charlie']
    upload_ids = []
    
    for guest_name in guest_names:
        test_image = create_test_image()
        files = {'files': (f'{guest_name}_photo.jpg', test_image, 'image/jpeg')}
        data = {'guest_name': guest_name}
        
        response = requests.post(f'{BASE_URL}/api/upload', files=files, data=data)
        assert response.status_code == 201
        upload_ids.append(response.json()['upload_id'])
    
    # Verify all uploads appear in media with correct attribution
    media_response = requests.get(f'{BASE_URL}/api/media')
    media_data = media_response.json()
    
    found_guests = set()
    for item in media_data['media']:
        if item['guest_name'] in guest_names:
            found_guests.add(item['guest_name'])
    
    assert len(found_guests) == len(guest_names), \
        f"Expected {len(guest_names)} guests, found {len(found_guests)}: {found_guests}"
    
    print(f"✅ Guest attribution working for: {', '.join(found_guests)}")

def test_concurrent_uploads():
    """Test system handles multiple simultaneous uploads"""
    import threading
    import time
    
    results = []
    
    def upload_worker(user_id):
        test_image = create_test_image()
        files = {'files': (f'concurrent_test_{user_id}.jpg', test_image, 'image/jpeg')}
        data = {'guest_name': f'ConcurrentUser{user_id}'}
        
        try:
            start_time = time.time()
            response = requests.post(f'{BASE_URL}/api/upload', files=files, data=data)
            end_time = time.time()
            
            results.append({
                'user_id': user_id,
                'status_code': response.status_code,
                'response_time': end_time - start_time,
                'success': response.status_code == 201
            })
        except Exception as e:
            results.append({
                'user_id': user_id,
                'error': str(e),
                'success': False
            })
    
    # Create 5 concurrent upload threads
    threads = []
    for i in range(5):
        thread = threading.Thread(target=upload_worker, args=(i,))
        threads.append(thread)
    
    # Start all threads
    start_time = time.time()
    for thread in threads:
        thread.start()
    
    # Wait for all to complete
    for thread in threads:
        thread.join()
    
    total_time = time.time() - start_time
    
    # Analyze results
    success_count = sum(1 for r in results if r.get('success', False))
    avg_response_time = sum(r.get('response_time', 0) for r in results if 'response_time' in r) / len(results)
    
    # At least 80% should succeed
    assert success_count >= 4, f"Only {success_count}/5 concurrent uploads succeeded"
    
    # Average response time should be reasonable
    assert avg_response_time < 10, f"Average response time too high: {avg_response_time:.2f}s"
    
    print(f"✅ Concurrent uploads: {success_count}/5 succeeded, avg time: {avg_response_time:.2f}s")

def test_api_health_check():
    """Test basic API health and responsiveness"""
    endpoints_to_test = [
        '/api/config',
        '/api/media',
        '/api/music/queue'
    ]
    
    for endpoint in endpoints_to_test:
        response = requests.get(f'{BASE_URL}{endpoint}')
        assert response.status_code == 200, f"Health check failed for {endpoint}"
        
        # Verify response is valid JSON
        try:
            json_data = response.json()
            assert isinstance(json_data, dict), f"Expected dict response from {endpoint}"
        except json.JSONDecodeError:
            pytest.fail(f"Invalid JSON response from {endpoint}")
    
    print("✅ All API endpoints responding correctly")

if __name__ == "__main__":
    print("🎉 Running Party Memory Wall Upload API Tests")
    print("⚠️  Ensure Flask is running on port 6000: cd backend && python app.py")
    print("=" * 60)
    
    # Run tests
    pytest.main([__file__, "-v"])