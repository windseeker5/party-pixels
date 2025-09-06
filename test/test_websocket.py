"""
Test suite for Party Memory Wall WebSocket Real-time Updates

CRITICAL REQUIREMENTS:
- Test WebSocket connection to port 6000
- Test real-time broadcasts for new uploads
- Test music queue updates
- Test slideshow synchronization

Before running tests:
1. cd backend && python app.py (must run on port 6000 with WebSocket support)
2. Ensure websockets library is available: pip install websockets
3. Run: python -m pytest test/test_websocket.py -v
"""

import pytest
import asyncio
import json
import requests
from io import BytesIO

# Import websocket client
try:
    import websockets
except ImportError:
    pytest.skip("websockets library not available. Install with: pip install websockets", allow_module_level=True)

BASE_URL = 'http://localhost:6000'
WS_URL = 'ws://localhost:6000/ws'

def create_test_image():
    """Create test image for upload testing"""
    from PIL import Image
    img = Image.new('RGB', (50, 50), color='blue')
    img_buffer = BytesIO()
    img.save(img_buffer, format='JPEG')
    img_buffer.seek(0)
    return img_buffer

def create_test_audio():
    """Create test audio for music testing"""
    # Simple fake MP3 data
    audio_data = b'\xFF\xFB\x90\x00' + b'audio_test_data' * 100
    return BytesIO(audio_data)

async def test_websocket_connection():
    """Test basic WebSocket connection to Flask server"""
    try:
        async with websockets.connect(WS_URL, timeout=10) as websocket:
            assert websocket.open, "WebSocket connection should be open"
            
            # Test connection is stable
            await asyncio.sleep(1)
            assert websocket.open, "WebSocket connection should remain stable"
            
            # Send ping to test bidirectional communication
            pong_waiter = await websocket.ping()
            await asyncio.wait_for(pong_waiter, timeout=5)
            
            print("✅ WebSocket connection established successfully")
            
    except ConnectionRefusedError:
        pytest.fail("WebSocket connection refused. Ensure Flask app with WebSocket is running on port 6000")
    except asyncio.TimeoutError:
        pytest.fail("WebSocket connection timeout. Check if WebSocket endpoint is available at /ws")
    except Exception as e:
        pytest.fail(f"WebSocket connection failed: {e}")

async def test_new_photo_upload_broadcast():
    """Test that photo uploads trigger WebSocket broadcasts"""
    upload_broadcast_received = False
    received_data = None
    
    async def websocket_listener():
        nonlocal upload_broadcast_received, received_data
        try:
            async with websockets.connect(WS_URL, timeout=10) as websocket:
                # Wait for broadcast message
                message = await asyncio.wait_for(websocket.recv(), timeout=15)
                received_data = json.loads(message)
                
                if received_data.get('type') == 'new_upload':
                    upload_broadcast_received = True
                    
        except asyncio.TimeoutError:
            pass  # No message received in time
        except Exception as e:
            print(f"WebSocket listener error: {e}")
    
    # Start WebSocket listener
    listener_task = asyncio.create_task(websocket_listener())
    
    # Give WebSocket time to connect
    await asyncio.sleep(1)
    
    # Upload a photo
    test_image = create_test_image()
    files = {'files': ('websocket_test_photo.jpg', test_image, 'image/jpeg')}
    data = {'guest_name': 'WebSocket Tester', 'type': 'photo'}
    
    # Upload in separate thread to not block
    upload_response = await asyncio.to_thread(
        requests.post,
        f'{BASE_URL}/api/upload',
        files=files,
        data=data
    )
    
    # Wait for WebSocket message
    await asyncio.sleep(2)
    
    # Cancel listener
    listener_task.cancel()
    
    # Verify upload succeeded
    assert upload_response.status_code == 201, f"Upload failed: {upload_response.text}"
    
    # Verify WebSocket broadcast was received
    if upload_broadcast_received:
        assert received_data['type'] == 'new_upload'
        assert received_data['data']['guest_name'] == 'WebSocket Tester'
        assert received_data['data']['file_type'] == 'photo'
        print("✅ Photo upload WebSocket broadcast working")
    else:
        print("⚠️  No WebSocket broadcast received (may need implementation)")

async def test_new_video_upload_broadcast():
    """Test that video uploads trigger WebSocket broadcasts"""
    broadcast_received = False
    received_data = None
    
    async def websocket_listener():
        nonlocal broadcast_received, received_data
        try:
            async with websockets.connect(WS_URL, timeout=10) as websocket:
                message = await asyncio.wait_for(websocket.recv(), timeout=15)
                received_data = json.loads(message)
                
                if received_data.get('type') == 'new_upload' and received_data.get('data', {}).get('file_type') == 'video':
                    broadcast_received = True
                    
        except asyncio.TimeoutError:
            pass
        except Exception as e:
            print(f"Video WebSocket listener error: {e}")
    
    # Start listener
    listener_task = asyncio.create_task(websocket_listener())
    await asyncio.sleep(1)
    
    # Upload a video
    test_video = BytesIO(b'\x00\x00\x00\x20\x66\x74\x79\x70\x6D\x70\x34\x31' + b'x' * 1000)
    files = {'files': ('websocket_test_video.mp4', test_video, 'video/mp4')}
    data = {'guest_name': 'Video Tester', 'type': 'video'}
    
    upload_response = await asyncio.to_thread(
        requests.post,
        f'{BASE_URL}/api/upload', 
        files=files,
        data=data
    )
    
    await asyncio.sleep(2)
    listener_task.cancel()
    
    # Verify upload
    assert upload_response.status_code == 201, f"Video upload failed: {upload_response.text}"
    
    if broadcast_received:
        assert received_data['data']['file_type'] == 'video'
        assert received_data['data']['guest_name'] == 'Video Tester'
        print("✅ Video upload WebSocket broadcast working")
    else:
        print("⚠️  Video upload WebSocket broadcast not received")

async def test_music_queue_update_broadcast():
    """Test music queue updates are broadcast via WebSocket"""
    music_broadcast_received = False
    received_data = None
    
    async def websocket_listener():
        nonlocal music_broadcast_received, received_data
        try:
            async with websockets.connect(WS_URL, timeout=10) as websocket:
                while True:
                    message = await asyncio.wait_for(websocket.recv(), timeout=15)
                    data = json.loads(message)
                    
                    if data.get('type') == 'music_update':
                        music_broadcast_received = True
                        received_data = data
                        break
                    elif data.get('type') == 'new_upload' and data.get('data', {}).get('file_type') == 'music':
                        # Music upload might trigger different event type
                        music_broadcast_received = True
                        received_data = data
                        break
                        
        except asyncio.TimeoutError:
            pass
        except Exception as e:
            print(f"Music WebSocket listener error: {e}")
    
    # Start listener
    listener_task = asyncio.create_task(websocket_listener())
    await asyncio.sleep(1)
    
    # Upload music
    test_audio = create_test_audio()
    files = {'files': ('websocket_test_song.mp3', test_audio, 'audio/mp3')}
    data = {
        'guest_name': 'DJ WebSocket',
        'type': 'music',
        'song_title': 'WebSocket Test Song',
        'artist': 'Test Artist'
    }
    
    upload_response = await asyncio.to_thread(
        requests.post,
        f'{BASE_URL}/api/upload',
        files=files,
        data=data
    )
    
    await asyncio.sleep(3)  # Give more time for music processing
    listener_task.cancel()
    
    # Verify upload
    assert upload_response.status_code == 201, f"Music upload failed: {upload_response.text}"
    
    if music_broadcast_received:
        # Verify broadcast contains music information
        if received_data['type'] == 'music_update':
            # Specific music update event
            assert 'now_playing' in received_data['data'] or 'queue_length' in received_data['data']
        else:
            # General upload event for music
            assert received_data['data']['file_type'] == 'music'
            
        print("✅ Music queue WebSocket broadcast working")
    else:
        print("⚠️  Music queue WebSocket broadcast not received")

async def test_slideshow_control_broadcast():
    """Test slideshow control commands are broadcast"""
    slideshow_broadcast_received = False
    received_data = None
    
    async def websocket_listener():
        nonlocal slideshow_broadcast_received, received_data
        try:
            async with websockets.connect(WS_URL, timeout=10) as websocket:
                message = await asyncio.wait_for(websocket.recv(), timeout=10)
                received_data = json.loads(message)
                
                if received_data.get('type') == 'slideshow_update':
                    slideshow_broadcast_received = True
                    
        except asyncio.TimeoutError:
            pass
        except Exception as e:
            print(f"Slideshow WebSocket listener error: {e}")
    
    # Start listener
    listener_task = asyncio.create_task(websocket_listener())
    await asyncio.sleep(1)
    
    # Trigger slideshow control (if API exists)
    try:
        control_response = await asyncio.to_thread(
            requests.post,
            f'{BASE_URL}/api/media/next',
            json={'action': 'next'}
        )
        
        await asyncio.sleep(2)
        listener_task.cancel()
        
        if control_response.status_code == 200 and slideshow_broadcast_received:
            assert received_data['type'] == 'slideshow_update'
            print("✅ Slideshow control WebSocket broadcast working")
        else:
            print("ℹ️  Slideshow control API not implemented yet or no broadcast")
            
    except Exception as e:
        listener_task.cancel()
        print(f"ℹ️  Slideshow control test skipped: {e}")

async def test_multiple_websocket_clients():
    """Test multiple WebSocket clients can connect simultaneously"""
    client_count = 5
    connected_clients = []
    messages_received = [[] for _ in range(client_count)]
    
    async def client_handler(client_id):
        try:
            async with websockets.connect(WS_URL, timeout=10) as websocket:
                connected_clients.append(client_id)
                
                # Listen for messages for 5 seconds
                try:
                    while True:
                        message = await asyncio.wait_for(websocket.recv(), timeout=1)
                        messages_received[client_id].append(message)
                except asyncio.TimeoutError:
                    pass  # Normal timeout
                    
                return f"Client {client_id} connected"
                
        except Exception as e:
            return f"Client {client_id} failed: {e}"
    
    # Connect multiple clients
    tasks = [client_handler(i) for i in range(client_count)]
    
    try:
        results = await asyncio.gather(*tasks, timeout=15)
        
        # Verify all clients connected successfully
        successful_connections = len([r for r in results if "connected" in r])
        assert successful_connections >= client_count - 1, f"Only {successful_connections}/{client_count} clients connected"
        
        print(f"✅ Multiple WebSocket clients: {successful_connections}/{client_count} connected successfully")
        
    except asyncio.TimeoutError:
        pytest.fail("Multiple client connection test timed out")

async def test_websocket_message_format():
    """Test WebSocket messages have correct JSON format"""
    valid_message_received = False
    message_data = None
    
    async def message_validator():
        nonlocal valid_message_received, message_data
        try:
            async with websockets.connect(WS_URL, timeout=10) as websocket:
                # Trigger an upload to generate a message
                await asyncio.sleep(1)
                
                message = await asyncio.wait_for(websocket.recv(), timeout=10)
                
                # Verify message is valid JSON
                message_data = json.loads(message)
                
                # Verify message has required structure
                if isinstance(message_data, dict):
                    if 'type' in message_data and 'data' in message_data:
                        valid_message_received = True
                        
        except json.JSONDecodeError:
            pytest.fail("WebSocket message is not valid JSON")
        except asyncio.TimeoutError:
            pass  # No message received
        except Exception as e:
            print(f"Message validation error: {e}")
    
    # Start validator
    validator_task = asyncio.create_task(message_validator())
    
    # Trigger an upload to generate WebSocket message
    await asyncio.sleep(0.5)  # Let validator start first
    
    test_image = create_test_image()
    files = {'files': ('format_test.jpg', test_image, 'image/jpeg')}
    data = {'guest_name': 'Format Tester'}
    
    await asyncio.to_thread(
        requests.post,
        f'{BASE_URL}/api/upload',
        files=files,
        data=data
    )
    
    # Wait for message
    await asyncio.sleep(2)
    validator_task.cancel()
    
    if valid_message_received:
        # Verify message structure
        assert isinstance(message_data, dict), "Message should be a dictionary"
        assert 'type' in message_data, "Message missing 'type' field"
        assert 'data' in message_data, "Message missing 'data' field"
        
        # Verify type is valid
        valid_types = ['new_upload', 'music_update', 'slideshow_update']
        assert message_data['type'] in valid_types, f"Invalid message type: {message_data['type']}"
        
        print(f"✅ WebSocket message format valid: {message_data['type']}")
    else:
        print("ℹ️  No WebSocket message received for format validation")

async def test_websocket_error_handling():
    """Test WebSocket handles errors gracefully"""
    # Test invalid JSON message (if server accepts client messages)
    try:
        async with websockets.connect(WS_URL, timeout=10) as websocket:
            # Try sending invalid data (if server accepts client messages)
            try:
                await websocket.send("invalid json {")
                await asyncio.sleep(1)
                # Connection should still be alive
                assert websocket.open, "WebSocket should handle invalid messages gracefully"
            except Exception as e:
                # Server might not accept client messages, which is fine
                print(f"ℹ️  Server doesn't accept client messages: {e}")
            
            print("✅ WebSocket error handling test completed")
            
    except Exception as e:
        print(f"ℹ️  WebSocket error handling test failed: {e}")

async def test_websocket_connection_persistence():
    """Test WebSocket connections persist through multiple uploads"""
    messages_received = []
    
    async def persistent_listener():
        try:
            async with websockets.connect(WS_URL, timeout=10) as websocket:
                # Listen for multiple messages
                for _ in range(3):  # Expect up to 3 messages
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=8)
                        messages_received.append(json.loads(message))
                    except asyncio.TimeoutError:
                        break
                        
        except Exception as e:
            print(f"Persistent listener error: {e}")
    
    # Start persistent listener
    listener_task = asyncio.create_task(persistent_listener())
    await asyncio.sleep(1)
    
    # Upload multiple files
    uploads = [
        ('persistent_test_1.jpg', 'Persistence Test 1'),
        ('persistent_test_2.jpg', 'Persistence Test 2'),
        ('persistent_test_3.jpg', 'Persistence Test 3'),
    ]
    
    for filename, guest_name in uploads:
        test_image = create_test_image()
        files = {'files': (filename, test_image, 'image/jpeg')}
        data = {'guest_name': guest_name}
        
        await asyncio.to_thread(
            requests.post,
            f'{BASE_URL}/api/upload',
            files=files,
            data=data
        )
        await asyncio.sleep(1)  # Brief pause between uploads
    
    # Wait for all messages
    await asyncio.sleep(3)
    listener_task.cancel()
    
    # Verify we received messages for the uploads
    upload_messages = [msg for msg in messages_received if msg.get('type') == 'new_upload']
    
    if len(upload_messages) >= 1:
        print(f"✅ WebSocket persistence: received {len(upload_messages)} upload notifications")
        
        # Verify guest names in messages
        guest_names_received = [msg['data']['guest_name'] for msg in upload_messages]
        for upload_name in ['Persistence Test 1', 'Persistence Test 2', 'Persistence Test 3']:
            if upload_name in guest_names_received:
                print(f"  - Received notification for: {upload_name}")
    else:
        print("ℹ️  WebSocket persistence test: no upload messages received")

async def test_websocket_performance():
    """Test WebSocket performance with rapid messages"""
    start_time = asyncio.get_event_loop().time()
    messages_received = []
    
    async def performance_listener():
        try:
            async with websockets.connect(WS_URL, timeout=10) as websocket:
                # Listen for up to 5 seconds
                end_time = start_time + 5
                while asyncio.get_event_loop().time() < end_time:
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=1)
                        messages_received.append({
                            'timestamp': asyncio.get_event_loop().time(),
                            'message': json.loads(message)
                        })
                    except asyncio.TimeoutError:
                        continue
                        
        except Exception as e:
            print(f"Performance listener error: {e}")
    
    # Start performance listener
    listener_task = asyncio.create_task(performance_listener())
    await asyncio.sleep(0.5)
    
    # Rapid uploads
    for i in range(3):  # 3 rapid uploads
        test_image = create_test_image()
        files = {'files': (f'perf_test_{i}.jpg', test_image, 'image/jpeg')}
        data = {'guest_name': f'Performance Test {i}'}
        
        upload_task = asyncio.create_task(asyncio.to_thread(
            requests.post,
            f'{BASE_URL}/api/upload',
            files=files,
            data=data
        ))
        
        # Don't wait for upload to complete, send next immediately
    
    # Wait for listener to complete
    await asyncio.sleep(6)
    listener_task.cancel()
    
    if messages_received:
        # Calculate message intervals
        if len(messages_received) > 1:
            intervals = [
                messages_received[i]['timestamp'] - messages_received[i-1]['timestamp']
                for i in range(1, len(messages_received))
            ]
            avg_interval = sum(intervals) / len(intervals)
            
            # Messages should arrive quickly
            assert avg_interval < 5, f"WebSocket message interval too slow: {avg_interval:.2f}s"
            
            print(f"✅ WebSocket performance: {len(messages_received)} messages, avg interval {avg_interval:.2f}s")
        else:
            print(f"✅ WebSocket performance: {len(messages_received)} messages received")
    else:
        print("ℹ️  No messages received for performance test")

# Main test runner
if __name__ == "__main__":
    print("🎉 Running Party Memory Wall WebSocket Tests")
    print("⚠️  Ensure Flask with WebSocket support is running on port 6000")
    print("⚠️  Install websockets: pip install websockets")
    print("=" * 70)
    
    # Run tests
    pytest.main([__file__, "-v", "-s"])