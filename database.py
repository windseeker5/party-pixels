"""
Party Memory Wall Database Operations
SQLite database handling for Valérie's 50th Birthday celebration
"""

import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional, Any
import json


class PartyDatabase:
    """Database operations for Party Memory Wall"""
    
    def __init__(self, db_path: str = 'database/party.db'):
        """Initialize database connection and create tables if needed"""
        self.db_path = db_path
        
        # Ensure database directory exists
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        
        self._create_tables()
        self._create_indexes()
        self._initialize_settings()
    
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection with proper configuration"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
        return conn
    
    def _create_tables(self):
        """Create all required database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Uploads table - stores all uploaded media
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS uploads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT NOT NULL,
            guest_name TEXT,
            file_path TEXT NOT NULL,
            file_type TEXT NOT NULL,
            original_filename TEXT,
            file_size INTEGER,
            duration INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            processed BOOLEAN DEFAULT FALSE
        )
        ''')
        
        # Music queue table - manages music playback queue
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS music_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            upload_id INTEGER,
            guest_name TEXT,
            song_path TEXT NOT NULL,
            song_title TEXT,
            artist TEXT,
            duration INTEGER,
            played BOOLEAN DEFAULT FALSE,
            queue_position INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (upload_id) REFERENCES uploads(id)
        )
        ''')
        
        # Settings table - party configuration
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Devices table - track guest devices for attribution
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS devices (
            device_id TEXT PRIMARY KEY,
            guest_name TEXT,
            first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
            total_uploads INTEGER DEFAULT 0
        )
        ''')
        
        # Music library table - indexed local music collection
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS music_library (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT UNIQUE NOT NULL,
            artist TEXT,
            album TEXT,
            title TEXT,
            year INTEGER,
            genre TEXT,
            duration INTEGER,
            file_size INTEGER,
            embedding TEXT,  -- JSON-encoded Ollama embedding vector
            indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Music searches table - track user search behavior
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS music_searches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT NOT NULL,
            selected_result TEXT,  -- JSON of selected item
            source TEXT CHECK(source IN ('local', 'youtube')),
            guest_name TEXT,
            party_energy REAL,  -- Based on upload frequency
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Music patterns table - AI learning for recommendations
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS music_patterns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pattern_type TEXT NOT NULL,  -- genre, energy, era, artist
            pattern_value TEXT NOT NULL,
            frequency INTEGER DEFAULT 1,
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(pattern_type, pattern_value)
        )
        ''')
        
        # Create FTS5 virtual table for music search
        cursor.execute('''
        CREATE VIRTUAL TABLE IF NOT EXISTS music_search USING fts5(
            artist, album, title, genre, 
            content=music_library
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def _create_indexes(self):
        """Create database indexes for better performance"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Indexes for better query performance
        indexes = [
            'CREATE INDEX IF NOT EXISTS idx_uploads_timestamp ON uploads(timestamp)',
            'CREATE INDEX IF NOT EXISTS idx_uploads_type ON uploads(file_type)',
            'CREATE INDEX IF NOT EXISTS idx_uploads_device ON uploads(device_id)',
            'CREATE INDEX IF NOT EXISTS idx_queue_position ON music_queue(queue_position)',
            'CREATE INDEX IF NOT EXISTS idx_queue_played ON music_queue(played)',
            'CREATE INDEX IF NOT EXISTS idx_devices_last_seen ON devices(last_seen)',
            'CREATE INDEX IF NOT EXISTS idx_library_artist ON music_library(artist)',
            'CREATE INDEX IF NOT EXISTS idx_library_album ON music_library(album)',
            'CREATE INDEX IF NOT EXISTS idx_library_title ON music_library(title)',
            'CREATE INDEX IF NOT EXISTS idx_searches_timestamp ON music_searches(timestamp)',
            'CREATE INDEX IF NOT EXISTS idx_searches_source ON music_searches(source)',
            'CREATE INDEX IF NOT EXISTS idx_patterns_type ON music_patterns(pattern_type)'
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
        
        conn.commit()
        conn.close()
    
    def _initialize_settings(self):
        """Initialize party settings with Valérie's birthday configuration"""
        default_settings = {
            'party_title': "Happy 50th Birthday Valérie!",
            'party_subtitle': "Celebrating 50 Amazing Years",
            'slideshow_duration': '7',
            'party_date': datetime.now().strftime('%Y-%m-%d'),
            'max_file_size': str(500 * 1024 * 1024),  # 500MB
            'allowed_photo_types': json.dumps(['jpg', 'jpeg', 'png', 'gif', 'heic', 'webp']),
            'allowed_video_types': json.dumps(['mp4', 'mov', 'avi', 'webm', 'm4v', 'mkv']),
            'allowed_music_types': json.dumps(['mp3', 'm4a', 'wav', 'flac']),
            'weekend_days': '2'
        }
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        for key, value in default_settings.items():
            cursor.execute('''
            INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)
            ''', (key, value))
        
        conn.commit()
        conn.close()
    
    def add_upload(self, device_id: str, guest_name: str, file_path: str, 
                  file_type: str, original_filename: str = None, 
                  file_size: int = None, duration: int = None) -> int:
        """Add new upload record and update device tracking"""
        if not device_id or not file_path or not file_type:
            raise ValueError("device_id, file_path, and file_type are required")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Insert upload record
            cursor.execute('''
            INSERT INTO uploads (device_id, guest_name, file_path, file_type, 
                               original_filename, file_size, duration)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (device_id, guest_name, file_path, file_type, 
                  original_filename, file_size, duration))
            
            upload_id = cursor.lastrowid
            
            # Update device tracking
            cursor.execute('''
            INSERT OR REPLACE INTO devices (device_id, guest_name, first_seen, last_seen, total_uploads)
            VALUES (?, ?, 
                    COALESCE((SELECT first_seen FROM devices WHERE device_id = ?), CURRENT_TIMESTAMP),
                    CURRENT_TIMESTAMP,
                    COALESCE((SELECT total_uploads FROM devices WHERE device_id = ?), 0) + 1)
            ''', (device_id, guest_name, device_id, device_id))
            
            conn.commit()
            return upload_id
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def get_upload(self, upload_id: int) -> Optional[Dict[str, Any]]:
        """Get upload record by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM uploads WHERE id = ?', (upload_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def get_slideshow_media(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get media items for slideshow (photos and videos only)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT id, device_id, guest_name, file_path, file_type, 
               original_filename, file_size, duration, timestamp
        FROM uploads
        WHERE file_type IN ('photo', 'video') AND processed = TRUE
        ORDER BY timestamp DESC
        LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        media_items = []
        for row in rows:
            item = dict(row)
            # Add URL for frontend access
            item['url'] = f"/media/{item['file_type']}s/{os.path.basename(item['file_path'])}"
            item['type'] = item['file_type']  # Standardize field name
            media_items.append(item)
        
        return media_items
    
    def add_to_music_queue(self, upload_id: int, song_title: str = None, 
                          artist: str = None, duration: int = None) -> int:
        """Add song to music queue"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Get upload info
            cursor.execute('''
            SELECT guest_name, file_path FROM uploads WHERE id = ?
            ''', (upload_id,))
            upload_info = cursor.fetchone()
            
            if not upload_info:
                raise ValueError(f"Upload ID {upload_id} not found")
            
            guest_name, file_path = upload_info
            
            # Get next queue position
            cursor.execute('SELECT COALESCE(MAX(queue_position), 0) + 1 FROM music_queue')
            next_position = cursor.fetchone()[0]
            
            # Insert into queue
            cursor.execute('''
            INSERT INTO music_queue (upload_id, guest_name, song_path, song_title, 
                                   artist, duration, queue_position)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (upload_id, guest_name, file_path, song_title, artist, duration, next_position))
            
            queue_id = cursor.lastrowid
            conn.commit()
            return queue_id
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def get_music_queue(self) -> Dict[str, Any]:
        """Get current music queue"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT id, guest_name, song_path, song_title, artist, 
               duration, played, queue_position, timestamp
        FROM music_queue
        ORDER BY queue_position ASC
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        songs = []
        for row in rows:
            song = dict(row)
            # Add URL for frontend access
            song['url'] = f"/media/music/{os.path.basename(song['song_path'])}"
            songs.append(song)
        
        return {
            'songs': songs,
            'total_count': len(songs),
            'unplayed_count': len([s for s in songs if not s['played']])
        }
    
    def mark_music_played(self, queue_id: int) -> bool:
        """Mark song as played in queue"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        UPDATE music_queue SET played = TRUE WHERE id = ?
        ''', (queue_id,))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    def get_queue_item(self, queue_id: int) -> Optional[Dict[str, Any]]:
        """Get specific queue item by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM music_queue WHERE id = ?', (queue_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def get_device_info(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Get device information for attribution"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM devices WHERE device_id = ?', (device_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def set_setting(self, key: str, value: str):
        """Set party setting"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT OR REPLACE INTO settings (key, value, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', (key, value))
        
        conn.commit()
        conn.close()
    
    def get_setting(self, key: str, default_value: str = None) -> Optional[str]:
        """Get party setting"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return row[0]
        return default_value
    
    def get_all_settings(self) -> Dict[str, str]:
        """Get all party settings as dictionary"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT key, value FROM settings')
        rows = cursor.fetchall()
        conn.close()
        
        return {row[0]: row[1] for row in rows}
    
    def mark_upload_processed(self, upload_id: int) -> bool:
        """Mark upload as processed"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('UPDATE uploads SET processed = TRUE WHERE id = ?', (upload_id,))
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    def add_to_music_library(self, file_path: str, artist: str = None, album: str = None, 
                            title: str = None, year: int = None, genre: str = None, 
                            duration: int = None, file_size: int = None, 
                            embedding: str = None) -> int:
        """Add song to music library index"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
            INSERT OR REPLACE INTO music_library 
            (file_path, artist, album, title, year, genre, duration, file_size, embedding)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (file_path, artist, album, title, year, genre, duration, file_size, embedding))
            
            library_id = cursor.lastrowid
            
            # Update FTS5 index
            cursor.execute('''
            INSERT OR REPLACE INTO music_search (rowid, artist, album, title, genre)
            VALUES (?, ?, ?, ?, ?)
            ''', (library_id, artist or '', album or '', title or '', genre or ''))
            
            conn.commit()
            return library_id
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def search_music_library(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search music library using FTS5 and semantic similarity"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # FTS5 text search first
        cursor.execute('''
        SELECT ml.id, ml.file_path, ml.artist, ml.album, ml.title, 
               ml.year, ml.genre, ml.duration, ml.file_size
        FROM music_library ml
        JOIN music_search ms ON ml.rowid = ms.rowid
        WHERE music_search MATCH ?
        ORDER BY rank
        LIMIT ?
        ''', (query, limit))
        
        results = []
        for row in cursor.fetchall():
            song = dict(row)
            song['source'] = 'local'
            song['url'] = f"/media/music/{os.path.basename(song['file_path'])}"
            results.append(song)
        
        conn.close()
        return results
    
    def log_music_search(self, query: str, selected_result: Dict[str, Any] = None, 
                        source: str = None, guest_name: str = None, 
                        party_energy: float = None) -> int:
        """Log user search behavior for learning"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        import json
        selected_json = json.dumps(selected_result) if selected_result else None
        
        cursor.execute('''
        INSERT INTO music_searches (query, selected_result, source, guest_name, party_energy)
        VALUES (?, ?, ?, ?, ?)
        ''', (query, selected_json, source, guest_name, party_energy))
        
        search_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return search_id
    
    def update_music_pattern(self, pattern_type: str, pattern_value: str):
        """Update music pattern frequency for AI learning"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT OR REPLACE INTO music_patterns (pattern_type, pattern_value, frequency, last_seen)
        VALUES (?, ?, 
                COALESCE((SELECT frequency FROM music_patterns WHERE pattern_type = ? AND pattern_value = ?), 0) + 1,
                CURRENT_TIMESTAMP)
        ''', (pattern_type, pattern_value, pattern_type, pattern_value))
        
        conn.commit()
        conn.close()
    
    def get_music_patterns(self, pattern_type: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get music patterns for AI recommendations"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if pattern_type:
            cursor.execute('''
            SELECT pattern_type, pattern_value, frequency, last_seen
            FROM music_patterns
            WHERE pattern_type = ?
            ORDER BY frequency DESC, last_seen DESC
            LIMIT ?
            ''', (pattern_type, limit))
        else:
            cursor.execute('''
            SELECT pattern_type, pattern_value, frequency, last_seen
            FROM music_patterns
            ORDER BY frequency DESC, last_seen DESC
            LIMIT ?
            ''', (limit,))
        
        patterns = []
        for row in cursor.fetchall():
            patterns.append(dict(row))
        
        conn.close()
        return patterns
    
    def get_search_count(self) -> int:
        """Get total number of music searches for AI trigger"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM music_searches')
        count = cursor.fetchone()[0]
        conn.close()
        
        return count
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get party statistics"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Count uploads by type
        cursor.execute('''
        SELECT file_type, COUNT(*) as count
        FROM uploads
        GROUP BY file_type
        ''')
        upload_counts = dict(cursor.fetchall())
        
        # Count unique guests
        cursor.execute('SELECT COUNT(DISTINCT guest_name) FROM uploads WHERE guest_name IS NOT NULL')
        unique_guests = cursor.fetchone()[0]
        
        # Count devices
        cursor.execute('SELECT COUNT(*) FROM devices')
        device_count = cursor.fetchone()[0]
        
        # Music queue stats
        cursor.execute('SELECT COUNT(*) FROM music_queue')
        total_songs = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM music_queue WHERE played = FALSE')
        unplayed_songs = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'upload_counts': upload_counts,
            'unique_guests': unique_guests,
            'device_count': device_count,
            'total_songs': total_songs,
            'unplayed_songs': unplayed_songs,
            'total_uploads': sum(upload_counts.values())
        }


# Utility functions for database operations
def init_database(db_path: str = 'database/party.db') -> PartyDatabase:
    """Initialize and return party database instance"""
    return PartyDatabase(db_path)


def cleanup_old_data(db_path: str = 'database/party.db', days_old: int = 7):
    """Cleanup old data (utility for maintenance)"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
    DELETE FROM uploads 
    WHERE timestamp < datetime('now', '-{} days')
    '''.format(days_old))
    
    # Clean up orphaned music queue entries
    cursor.execute('''
    DELETE FROM music_queue 
    WHERE upload_id NOT IN (SELECT id FROM uploads)
    ''')
    
    # Clean up devices with no uploads
    cursor.execute('''
    DELETE FROM devices 
    WHERE device_id NOT IN (SELECT DISTINCT device_id FROM uploads)
    ''')
    
    conn.commit()
    conn.close()


if __name__ == "__main__":
    # Test database creation and basic operations
    print("🎉 Testing Party Memory Wall Database")
    
    # Initialize database
    db = PartyDatabase(':memory:')  # Use in-memory for testing
    
    # Test upload
    upload_id = db.add_upload(
        device_id='test-device',
        guest_name='Test User',
        file_path='/media/photos/test.jpg',
        file_type='photo',
        original_filename='test.jpg',
        file_size=1024000
    )
    print(f"✅ Test upload created with ID: {upload_id}")
    
    # Test settings
    settings = db.get_all_settings()
    print(f"✅ Party settings: {settings['party_title']}")
    
    # Test statistics
    stats = db.get_statistics()
    print(f"✅ Database stats: {stats}")
    
    print("🎂 Database ready for Valérie's 50th Birthday celebration!")