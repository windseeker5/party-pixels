"""
Test suite for Party Memory Wall Database Operations

CRITICAL REQUIREMENTS:
- Test SQLite database schema and operations
- Validate party configuration storage
- Test guest attribution and device tracking
- Ensure data integrity for Valérie's celebration

Before running tests:
1. Ensure backend/database.py exists with PartyDatabase class
2. Run: python -m pytest test/test_database.py -v
"""

import pytest
import sqlite3
import os
import tempfile
from datetime import datetime, timedelta

# Import database class (adjust path as needed)
try:
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))
    from database import PartyDatabase
except ImportError:
    pytest.skip("Database module not available yet", allow_module_level=True)

def test_database_creation():
    """Test database initialization and table creation"""
    # Use temporary database for testing
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
        temp_db_path = temp_db.name
    
    try:
        db = PartyDatabase(temp_db_path)
        
        # Verify database file exists
        assert os.path.exists(temp_db_path), "Database file was not created"
        
        # Connect directly to verify tables
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        
        # Check all required tables exist
        tables = cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """).fetchall()
        
        table_names = [table[0] for table in tables]
        expected_tables = ['uploads', 'music_queue', 'settings', 'devices']
        
        for expected_table in expected_tables:
            assert expected_table in table_names, f"Table '{expected_table}' not found in database"
        
        print(f"✅ Database created successfully with tables: {', '.join(table_names)}")
        
        conn.close()
        
    finally:
        # Clean up temporary database
        if os.path.exists(temp_db_path):
            os.unlink(temp_db_path)

def test_uploads_table_schema():
    """Test uploads table has correct schema"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
        temp_db_path = temp_db.name
    
    try:
        db = PartyDatabase(temp_db_path)
        
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        
        # Get uploads table schema
        schema = cursor.execute("PRAGMA table_info(uploads)").fetchall()
        column_info = {row[1]: {'type': row[2], 'notnull': row[3], 'pk': row[5]} for row in schema}
        
        # Verify required columns exist with correct types
        required_columns = {
            'id': 'INTEGER',
            'device_id': 'TEXT', 
            'guest_name': 'TEXT',
            'file_path': 'TEXT',
            'file_type': 'TEXT',
            'original_filename': 'TEXT',
            'file_size': 'INTEGER',
            'duration': 'INTEGER',
            'timestamp': 'DATETIME',
            'processed': 'BOOLEAN'
        }
        
        for col_name, expected_type in required_columns.items():
            assert col_name in column_info, f"Column '{col_name}' missing from uploads table"
            assert column_info[col_name]['type'] == expected_type, \
                f"Column '{col_name}' has wrong type: expected {expected_type}, got {column_info[col_name]['type']}"
        
        # Verify primary key is set correctly
        assert column_info['id']['pk'] == 1, "ID column is not set as primary key"
        
        # Verify not-null constraints
        assert column_info['device_id']['notnull'] == 1, "device_id should be NOT NULL"
        assert column_info['file_path']['notnull'] == 1, "file_path should be NOT NULL"
        assert column_info['file_type']['notnull'] == 1, "file_type should be NOT NULL"
        
        print("✅ Uploads table schema validated")
        
        conn.close()
        
    finally:
        if os.path.exists(temp_db_path):
            os.unlink(temp_db_path)

def test_add_upload_record():
    """Test adding upload records to database"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
        temp_db_path = temp_db.name
    
    try:
        db = PartyDatabase(temp_db_path)
        
        # Add test upload record
        upload_id = db.add_upload(
            device_id='test-device-123',
            guest_name='Sarah Johnson',
            file_path='/media/photos/test_photo.jpg',
            file_type='photo',
            original_filename='birthday_pic.jpg',
            file_size=2048000
        )
        
        assert upload_id is not None, "Upload ID should not be None"
        assert isinstance(upload_id, int), f"Upload ID should be integer, got {type(upload_id)}"
        assert upload_id > 0, f"Upload ID should be positive, got {upload_id}"
        
        # Verify record was saved correctly
        upload = db.get_upload(upload_id)
        assert upload is not None, f"Upload record {upload_id} not found"
        
        assert upload['guest_name'] == 'Sarah Johnson', f"Guest name mismatch: {upload['guest_name']}"
        assert upload['file_type'] == 'photo', f"File type mismatch: {upload['file_type']}"
        assert upload['device_id'] == 'test-device-123', f"Device ID mismatch: {upload['device_id']}"
        assert upload['file_path'] == '/media/photos/test_photo.jpg', f"File path mismatch: {upload['file_path']}"
        assert upload['file_size'] == 2048000, f"File size mismatch: {upload['file_size']}"
        
        # Verify timestamp is recent
        timestamp = datetime.fromisoformat(upload['timestamp'].replace('Z', '+00:00'))
        time_diff = datetime.now() - timestamp
        assert time_diff.total_seconds() < 60, f"Timestamp too old: {timestamp}"
        
        print(f"✅ Upload record added successfully with ID: {upload_id}")
        
    finally:
        if os.path.exists(temp_db_path):
            os.unlink(temp_db_path)

def test_slideshow_media_retrieval():
    """Test getting media for slideshow display"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
        temp_db_path = temp_db.name
    
    try:
        db = PartyDatabase(temp_db_path)
        
        # Add multiple test media records
        test_uploads = [
            ('device1', 'Alice', '/media/photos/1.jpg', 'photo', 'alice_pic.jpg', 1024000),
            ('device2', 'Bob', '/media/videos/1.mp4', 'video', 'bob_video.mp4', 5120000),
            ('device3', 'Charlie', '/media/photos/2.jpg', 'photo', 'charlie_pic.jpg', 2048000),
            ('device1', 'Alice', '/media/videos/2.mp4', 'video', 'alice_video.mp4', 8192000),
        ]
        
        upload_ids = []
        for device_id, guest_name, file_path, file_type, filename, file_size in test_uploads:
            upload_id = db.add_upload(device_id, guest_name, file_path, file_type, filename, file_size)
            upload_ids.append(upload_id)
        
        # Get media for slideshow (should exclude music)
        media = db.get_slideshow_media()
        assert len(media) == 4, f"Expected 4 media items, got {len(media)}"
        
        # Verify media items are properly structured
        for item in media:
            required_fields = ['id', 'type', 'guest_name', 'file_path', 'url', 'timestamp']
            for field in required_fields:
                assert field in item, f"Media item missing field: {field}"
            
            # Verify type is photo or video (not music)
            assert item['type'] in ['photo', 'video'], f"Invalid media type for slideshow: {item['type']}"
        
        # Verify ordering (should be by timestamp, newest first or oldest first)
        timestamps = [datetime.fromisoformat(item['timestamp'].replace('Z', '+00:00')) for item in media]
        is_sorted_desc = all(timestamps[i] >= timestamps[i+1] for i in range(len(timestamps)-1))
        is_sorted_asc = all(timestamps[i] <= timestamps[i+1] for i in range(len(timestamps)-1))
        
        assert is_sorted_desc or is_sorted_asc, "Media items are not properly sorted by timestamp"
        
        # Verify guest attribution is preserved
        guest_names = [item['guest_name'] for item in media]
        assert 'Alice' in guest_names, "Alice's uploads missing from media"
        assert 'Bob' in guest_names, "Bob's uploads missing from media"
        assert 'Charlie' in guest_names, "Charlie's uploads missing from media"
        
        print(f"✅ Slideshow media retrieval working: {len(media)} items found")
        
    finally:
        if os.path.exists(temp_db_path):
            os.unlink(temp_db_path)

def test_music_queue_operations():
    """Test music queue management"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
        temp_db_path = temp_db.name
    
    try:
        db = PartyDatabase(temp_db_path)
        
        # Add music uploads first
        music_uploads = [
            ('device1', 'DJ Mike', '/media/music/song1.mp3', 'music', 'summer_vibes.mp3', 4096000),
            ('device2', 'DJ Sarah', '/media/music/song2.mp3', 'music', 'party_anthem.mp3', 3584000),
            ('device3', 'DJ Tom', '/media/music/song3.mp3', 'music', 'birthday_song.mp3', 2560000),
        ]
        
        upload_ids = []
        for device_id, guest_name, file_path, file_type, filename, file_size in music_uploads:
            upload_id = db.add_upload(device_id, guest_name, file_path, file_type, filename, file_size)
            upload_ids.append(upload_id)
        
        # Add songs to music queue
        queue_ids = []
        songs_info = [
            ('Summer Vibes', 'Unknown Artist', 240),
            ('Party Anthem', 'DJ Sarah', 180), 
            ('Happy Birthday Valérie', 'Traditional', 120),
        ]
        
        for i, (song_title, artist, duration) in enumerate(songs_info):
            queue_id = db.add_to_music_queue(
                upload_id=upload_ids[i],
                song_title=song_title,
                artist=artist,
                duration=duration
            )
            queue_ids.append(queue_id)
            assert queue_id is not None, f"Music queue ID should not be None for song: {song_title}"
        
        # Get music queue
        queue = db.get_music_queue()
        assert len(queue) == 3, f"Expected 3 songs in queue, got {len(queue)}"
        
        # Verify queue items have required fields
        for song in queue:
            required_fields = ['id', 'song_title', 'artist', 'guest_name', 'duration', 'played', 'queue_position']
            for field in required_fields:
                assert field in song, f"Queue item missing field: {field}"
            
            # Verify data types
            assert isinstance(song['duration'], int), f"Duration should be integer: {song['duration']}"
            assert isinstance(song['played'], (bool, int)), f"Played should be boolean: {song['played']}"
            assert isinstance(song['queue_position'], int), f"Queue position should be integer: {song['queue_position']}"
        
        # Verify queue ordering (by queue_position)
        positions = [song['queue_position'] for song in queue]
        assert positions == sorted(positions), f"Queue not properly ordered: {positions}"
        
        # Test marking song as played
        first_song_id = queue_ids[0]
        db.mark_music_played(first_song_id)
        
        # Verify song marked as played
        played_song = db.get_queue_item(first_song_id)
        assert played_song is not None, "Played song not found"
        assert played_song['played'] is True or played_song['played'] == 1, "Song not marked as played"
        
        # Verify guest attribution in queue
        guest_names_in_queue = [song['guest_name'] for song in queue]
        assert 'DJ Mike' in guest_names_in_queue, "DJ Mike missing from queue"
        assert 'DJ Sarah' in guest_names_in_queue, "DJ Sarah missing from queue"
        assert 'DJ Tom' in guest_names_in_queue, "DJ Tom missing from queue"
        
        print(f"✅ Music queue operations working: {len(queue)} songs queued")
        
    finally:
        if os.path.exists(temp_db_path):
            os.unlink(temp_db_path)

def test_device_tracking():
    """Test device tracking for guest attribution"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
        temp_db_path = temp_db.name
    
    try:
        db = PartyDatabase(temp_db_path)
        
        device_id = 'iphone-sarah-123'
        guest_name = 'Sarah'
        
        # First upload from device
        upload_id1 = db.add_upload(device_id, guest_name, '/media/photos/1.jpg', 'photo', '1.jpg', 1024)
        assert upload_id1 is not None, "First upload failed"
        
        # Check device was tracked
        device_info = db.get_device_info(device_id)
        assert device_info is not None, "Device info not found after first upload"
        assert device_info['guest_name'] == guest_name, f"Device guest name mismatch: {device_info['guest_name']}"
        assert device_info['total_uploads'] == 1, f"Upload count wrong after first upload: {device_info['total_uploads']}"
        
        # Verify timestamps are recent
        first_seen = datetime.fromisoformat(device_info['first_seen'].replace('Z', '+00:00'))
        last_seen = datetime.fromisoformat(device_info['last_seen'].replace('Z', '+00:00'))
        now = datetime.now()
        
        assert (now - first_seen).total_seconds() < 60, "First seen timestamp too old"
        assert (now - last_seen).total_seconds() < 60, "Last seen timestamp too old"
        
        # Second upload from same device
        upload_id2 = db.add_upload(device_id, guest_name, '/media/photos/2.jpg', 'photo', '2.jpg', 2048)
        assert upload_id2 is not None, "Second upload failed"
        
        # Check device info updated
        device_info_updated = db.get_device_info(device_id)
        assert device_info_updated['total_uploads'] == 2, f"Upload count wrong after second upload: {device_info_updated['total_uploads']}"
        
        # Last seen should be updated
        last_seen_updated = datetime.fromisoformat(device_info_updated['last_seen'].replace('Z', '+00:00'))
        assert last_seen_updated >= last_seen, "Last seen timestamp not updated"
        
        # Test multiple devices
        device_id2 = 'android-mike-456'
        upload_id3 = db.add_upload(device_id2, 'Mike', '/media/videos/1.mp4', 'video', 'video.mp4', 5120000)
        
        device_info2 = db.get_device_info(device_id2)
        assert device_info2 is not None, "Second device info not found"
        assert device_info2['guest_name'] == 'Mike', "Second device guest name wrong"
        assert device_info2['total_uploads'] == 1, "Second device upload count wrong"
        
        # Verify first device info unchanged
        device_info_original = db.get_device_info(device_id)
        assert device_info_original['total_uploads'] == 2, "First device upload count changed unexpectedly"
        
        print(f"✅ Device tracking working for multiple devices")
        
    finally:
        if os.path.exists(temp_db_path):
            os.unlink(temp_db_path)

def test_party_settings_storage():
    """Test party settings and configuration storage"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
        temp_db_path = temp_db.name
    
    try:
        db = PartyDatabase(temp_db_path)
        
        # Test setting values
        party_settings = {
            'party_title': "Happy 50th Birthday Valérie!",
            'slideshow_duration': '15',
            'party_date': '2024-09-05',
            'host_name': 'Party Host',
            'max_file_size': '524288000'  # 500MB
        }
        
        # Set all settings
        for key, value in party_settings.items():
            db.set_setting(key, value)
        
        # Retrieve and verify settings
        for key, expected_value in party_settings.items():
            actual_value = db.get_setting(key)
            assert actual_value == expected_value, f"Setting '{key}' mismatch: expected '{expected_value}', got '{actual_value}'"
        
        # Test updating existing setting
        db.set_setting('slideshow_duration', '20')
        updated_duration = db.get_setting('slideshow_duration')
        assert updated_duration == '20', f"Setting update failed: {updated_duration}"
        
        # Test default value for non-existent setting
        non_existent = db.get_setting('non_existent_setting', 'default_value')
        assert non_existent == 'default_value', f"Default value not returned: {non_existent}"
        
        # Verify Valérie's title is stored correctly
        title = db.get_setting('party_title')
        assert "Valérie" in title, f"Valérie's name missing from stored title: {title}"
        assert "50th Birthday" in title, f"50th Birthday missing from stored title: {title}"
        
        print("✅ Party settings storage working correctly")
        
    finally:
        if os.path.exists(temp_db_path):
            os.unlink(temp_db_path)

def test_database_performance():
    """Test database performance with larger datasets"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
        temp_db_path = temp_db.name
    
    try:
        db = PartyDatabase(temp_db_path)
        
        # Add many upload records to test performance
        start_time = datetime.now()
        
        upload_ids = []
        for i in range(100):  # 100 uploads
            device_id = f'device-{i % 10}'  # 10 different devices
            guest_name = f'Guest{i % 20}'   # 20 different guests
            file_type = 'photo' if i % 3 != 0 else 'video'
            file_path = f'/media/{file_type}s/{i}.jpg'
            
            upload_id = db.add_upload(
                device_id=device_id,
                guest_name=guest_name,
                file_path=file_path,
                file_type=file_type,
                original_filename=f'file_{i}.jpg',
                file_size=1024 * (i + 1)
            )
            upload_ids.append(upload_id)
        
        insert_time = (datetime.now() - start_time).total_seconds()
        assert insert_time < 10, f"Insert performance too slow: {insert_time:.2f} seconds for 100 records"
        
        # Test retrieval performance
        start_time = datetime.now()
        media = db.get_slideshow_media()
        retrieval_time = (datetime.now() - start_time).total_seconds()
        
        assert retrieval_time < 1, f"Retrieval performance too slow: {retrieval_time:.2f} seconds"
        
        # Verify we got the right number of records (photos + videos, no music)
        expected_count = len([i for i in range(100) if i % 3 != 0 or i % 3 == 1])  # Photos and videos
        actual_count = len([item for item in media if item['type'] in ['photo', 'video']])
        
        # Should have photos and videos (not music)
        assert actual_count > 50, f"Expected many media items, got {actual_count}"
        
        print(f"✅ Database performance: {insert_time:.2f}s insert, {retrieval_time:.2f}s retrieval for {len(media)} items")
        
    finally:
        if os.path.exists(temp_db_path):
            os.unlink(temp_db_path)

def test_data_integrity_constraints():
    """Test database constraints and data integrity"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
        temp_db_path = temp_db.name
    
    try:
        db = PartyDatabase(temp_db_path)
        
        # Test required field constraints
        try:
            # This should fail due to missing required fields
            db.add_upload(
                device_id=None,  # Required field
                guest_name='Test',
                file_path='/test/path',
                file_type='photo'
            )
            pytest.fail("Should have failed with None device_id")
        except (ValueError, sqlite3.IntegrityError):
            pass  # Expected to fail
        
        try:
            # This should fail due to missing file_path
            db.add_upload(
                device_id='test-device',
                guest_name='Test',
                file_path=None,  # Required field
                file_type='photo'
            )
            pytest.fail("Should have failed with None file_path")
        except (ValueError, sqlite3.IntegrityError):
            pass  # Expected to fail
        
        # Test valid upload still works
        valid_upload = db.add_upload(
            device_id='test-device',
            guest_name='Test User',
            file_path='/valid/path.jpg',
            file_type='photo'
        )
        assert valid_upload is not None, "Valid upload should succeed"
        
        # Test file type validation
        valid_types = ['photo', 'video', 'music']
        for file_type in valid_types:
            upload_id = db.add_upload(
                device_id=f'device-{file_type}',
                guest_name='Test User',
                file_path=f'/test/{file_type}.ext',
                file_type=file_type
            )
            assert upload_id is not None, f"Valid file type '{file_type}' should be accepted"
        
        print("✅ Database integrity constraints working correctly")
        
    finally:
        if os.path.exists(temp_db_path):
            os.unlink(temp_db_path)

# Database schema validation test
def test_database_schema_complete():
    """Test complete database schema matches requirements"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
        temp_db_path = temp_db.name
    
    try:
        db = PartyDatabase(temp_db_path)
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        
        # Test all tables have proper indexes
        indexes = cursor.execute("""
            SELECT name, tbl_name, sql FROM sqlite_master 
            WHERE type='index' AND name NOT LIKE 'sqlite_%'
        """).fetchall()
        
        # Should have indexes for performance
        index_tables = [idx[1] for idx in indexes]
        assert 'uploads' in index_tables, "uploads table should have indexes"
        
        # Test foreign key relationships if any
        foreign_keys = cursor.execute("PRAGMA foreign_key_list(music_queue)").fetchall()
        if foreign_keys:
            # If foreign keys exist, verify they're correct
            fk_info = {fk[3]: fk[2] for fk in foreign_keys}  # child_column: parent_table
            if 'upload_id' in fk_info:
                assert fk_info['upload_id'] == 'uploads', "music_queue should reference uploads table"
        
        conn.close()
        
        print("✅ Complete database schema validated")
        
    finally:
        if os.path.exists(temp_db_path):
            os.unlink(temp_db_path)

if __name__ == "__main__":
    print("🎉 Running Party Memory Wall Database Tests")
    print("⚠️  Ensure backend/database.py exists with PartyDatabase class")
    print("=" * 60)
    
    # Run tests
    pytest.main([__file__, "-v"])