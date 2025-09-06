# Backend Implementation Tasks

## Task 1: Flask Application Setup
**Agent**: backend-architect
**File**: backend/app.py
**Priority**: High

### Implementation Requirements:
- Flask app running on port 6000 (CRITICAL)
- CORS enabled for local network access
- File upload endpoints with large file support (500MB+)
- WebSocket support for real-time updates
- Party configuration endpoints

### Specific Endpoints Needed:

```python
# Core API endpoints
POST /api/upload          # Upload photo/video/music
GET  /api/media           # Get media list for slideshow
GET  /api/media/current   # Get current playing media
POST /api/media/next      # Skip to next media
GET  /api/music/queue     # Get music queue
POST /api/music/add       # Add song to queue
GET  /api/config          # Get party configuration
WebSocket /ws             # Real-time updates
```

### Party Configuration:
```python
PARTY_CONFIG = {
    'title': "Happy 50th Birthday Valérie!",
    'subtitle': "Celebrating 50 Amazing Years",
    'slideshow_duration': 15,  # seconds per photo
    'weekend_days': 2,
    'max_file_size': 500 * 1024 * 1024,  # 500MB
    'allowed_photo_types': ['jpg', 'jpeg', 'png', 'gif', 'heic', 'webp'],
    'allowed_video_types': ['mp4', 'mov', 'avi', 'webm', 'm4v', 'mkv'],
    'allowed_music_types': ['mp3', 'm4a', 'wav', 'flac']
}
```

### Unit Tests: test/test_upload_api.py
```python
import pytest
import requests
from flask import Flask

def test_flask_port_6000():
    """Test Flask runs on correct port"""
    response = requests.get('http://localhost:6000/api/config')
    assert response.status_code == 200

def test_photo_upload():
    """Test photo upload to /api/upload"""
    # Create test image file
    test_file = create_test_image()
    files = {'file': test_file}
    data = {'guest_name': 'TestUser', 'type': 'photo'}
    
    response = requests.post('http://localhost:6000/api/upload', 
                           files=files, data=data)
    assert response.status_code == 201
    assert 'file_id' in response.json()
    # Verify file saved to media/photos/
    # Check database entry created

def test_video_upload():
    """Test video upload (up to 500MB)"""
    test_video = create_test_video()
    files = {'file': test_video}
    data = {'guest_name': 'VideoUser', 'type': 'video'}
    
    response = requests.post('http://localhost:6000/api/upload', 
                           files=files, data=data)
    assert response.status_code == 201
    # Verify processing and storage
    # Check duration extraction

def test_music_upload():
    """Test music file upload and queue addition"""
    test_music = create_test_audio()
    files = {'file': test_music}
    data = {'guest_name': 'MusicUser', 'type': 'music'}
    
    response = requests.post('http://localhost:6000/api/upload', 
                           files=files, data=data)
    assert response.status_code == 201
    # Verify added to music queue

def test_large_file_handling():
    """Test handling of large files (near 500MB limit)"""
    # Test file size validation
    # Test progress during upload
    pass

def test_party_config_endpoint():
    """Test party configuration retrieval"""
    response = requests.get('http://localhost:6000/api/config')
    assert response.status_code == 200
    config = response.json()
    assert config['title'] == "Happy 50th Birthday Valérie!"
    assert config['slideshow_duration'] == 15
```

## Task 2: Database Layer
**Agent**: backend-architect
**File**: backend/database.py
**Priority**: High

### Database Schema (SQLite):
```sql
-- Media uploads table
CREATE TABLE uploads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id TEXT NOT NULL,
    guest_name TEXT,
    file_path TEXT NOT NULL,
    file_type TEXT NOT NULL,  -- 'photo', 'video', 'music'
    original_filename TEXT,
    file_size INTEGER,
    duration INTEGER,  -- for videos/music (seconds)
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    processed BOOLEAN DEFAULT FALSE
);

-- Music queue table
CREATE TABLE music_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    upload_id INTEGER,
    guest_name TEXT,
    song_path TEXT NOT NULL,
    song_title TEXT,
    artist TEXT,
    played BOOLEAN DEFAULT FALSE,
    queue_position INTEGER,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (upload_id) REFERENCES uploads(id)
);

-- Party settings
CREATE TABLE settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

-- Device tracking for attribution
CREATE TABLE devices (
    device_id TEXT PRIMARY KEY,
    guest_name TEXT,
    first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
    total_uploads INTEGER DEFAULT 0
);
```

### Database Operations:
```python
class PartyDatabase:
    def __init__(self, db_path='database/party.db'):
        # Initialize SQLite connection
        # Create tables if not exist
        # Set up indexes for performance
        
    def add_upload(self, device_id, guest_name, file_path, file_type):
        # Insert new upload record
        # Update device tracking
        # Return upload_id
        
    def get_slideshow_media(self):
        # Return photos/videos for slideshow
        # Order by timestamp
        # Include guest attribution
        
    def add_to_music_queue(self, upload_id, song_info):
        # Add song to queue
        # Update queue positions
        
    def get_music_queue(self):
        # Return current music queue
        # Include guest attribution
        
    def mark_music_played(self, queue_id):
        # Mark song as played
        # Move to next in queue
```

### Unit Tests: test/test_database.py
```python
import pytest
import sqlite3
from backend.database import PartyDatabase

def test_database_creation():
    """Test database and tables are created correctly"""
    db = PartyDatabase(':memory:')  # In-memory for testing
    # Verify all tables exist
    # Check schema is correct

def test_add_upload():
    """Test adding upload records"""
    db = PartyDatabase(':memory:')
    upload_id = db.add_upload(
        device_id='test-device',
        guest_name='Test User',
        file_path='/media/photos/test.jpg',
        file_type='photo'
    )
    assert upload_id is not None
    
def test_slideshow_media_retrieval():
    """Test getting media for slideshow"""
    db = PartyDatabase(':memory:')
    # Add test records
    media = db.get_slideshow_media()
    # Verify correct order and format

def test_music_queue_operations():
    """Test music queue management"""
    db = PartyDatabase(':memory:')
    # Test adding to queue
    # Test queue ordering
    # Test marking as played
```

## Task 3: WebSocket Handler
**Agent**: backend-architect  
**File**: backend/websocket_handler.py
**Priority**: Medium

### WebSocket Events:
```python
# Events sent to frontend
{
    'type': 'new_upload',
    'data': {
        'file_type': 'photo',
        'guest_name': 'Sarah',
        'preview_url': '/media/photos/thumb_123.jpg'
    }
}

{
    'type': 'music_update',
    'data': {
        'now_playing': {
            'title': 'Summer Vibes',
            'artist': 'Unknown',
            'guest_name': 'Mike'
        },
        'queue_length': 3
    }
}

{
    'type': 'slideshow_update',
    'data': {
        'current_index': 5,
        'total_media': 47,
        'current_media': {
            'type': 'photo',
            'url': '/media/photos/123.jpg',
            'guest_name': 'Emma'
        }
    }
}
```

### Unit Tests: test/test_websocket.py
```python
import pytest
import websocket
from backend.websocket_handler import WebSocketHandler

def test_websocket_connection():
    """Test WebSocket connection to /ws"""
    ws = websocket.create_connection("ws://localhost:6000/ws")
    # Test connection successful
    ws.close()

def test_new_upload_broadcast():
    """Test broadcast when new media uploaded"""
    # Connect WebSocket client
    # Upload new media
    # Verify broadcast received
    
def test_music_update_broadcast():
    """Test music queue updates"""
    # Connect WebSocket
    # Add song to queue
    # Verify update broadcast
```

## Task 4: File Processing
**Agent**: backend-architect
**File**: backend/file_processor.py
**Priority**: Medium

### File Processing Requirements:
- Generate thumbnails for photos
- Extract video duration and create preview frames
- Extract music metadata (title, artist, duration)
- Handle HEIC to JPEG conversion (iPhone photos)
- Compress large videos for RPi playback if needed

### Implementation:
```python
from PIL import Image
import ffmpeg
from mutagen import File as MutagenFile

class FileProcessor:
    def process_photo(self, file_path):
        # Generate thumbnail
        # Convert HEIC to JPEG if needed
        # Extract EXIF data
        
    def process_video(self, file_path):
        # Extract duration
        # Generate thumbnail frame
        # Optional: compress for RPi if >100MB
        
    def process_music(self, file_path):
        # Extract metadata (title, artist, duration)
        # Generate waveform preview (optional)
```

## Task 5: Docker Configuration
**Agent**: backend-architect
**Files**: backend/Dockerfile, backend/requirements.txt
**Priority**: Low

### requirements.txt:
```
Flask==2.3.2
Flask-CORS==4.0.0
Flask-SocketIO==5.3.4
python-socketio==5.8.0
Pillow==10.0.0
mutagen==1.46.0
ffmpeg-python==0.2.0
sqlite3
werkzeug==2.3.6
```

### Dockerfile:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libimage-exiftool-perl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 6000

CMD ["python", "app.py"]
```

## Critical Testing Notes for Agents:

1. **Port Requirement**: Flask MUST run on port 6000 for all testing
2. **Existing Tools**: Use MCP Playwright server (already installed)
3. **Test Location**: All tests go in /test folder
4. **File Support**: Test both photos AND videos
5. **Large Files**: Test files up to 500MB
6. **Real-time**: Test WebSocket updates work correctly
7. **Attribution**: Verify guest names are tracked and displayed

## Error Handling Requirements:

- File size limits (500MB max)
- Invalid file types  
- Disk space checks
- Database connection errors
- WebSocket connection failures
- Graceful degradation if services fail