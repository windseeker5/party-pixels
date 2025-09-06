#!/usr/bin/env python3
"""
Music Library Indexer for Party Memory Wall
Scans and indexes local music collection with metadata and Ollama embeddings
"""

import os
import json
import requests
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from mutagen import File
from mutagen.id3 import ID3NoHeaderError
from database import PartyDatabase

class MusicLibraryIndexer:
    """Indexes local music library for smart search capabilities"""
    
    def __init__(self, library_path: str = "/mnt/media/MUSIC", 
                 ollama_host: str = "http://127.0.0.1:11434",
                 db_path: str = "database/party.db"):
        self.library_path = Path(library_path)
        self.ollama_host = ollama_host
        self.db = PartyDatabase(db_path)
        self.supported_formats = {'.mp3', '.m4a', '.wav', '.flac', '.ogg'}
        
    def scan_library(self) -> List[str]:
        """Scan library directory for music files"""
        print(f"🎵 Scanning music library: {self.library_path}")
        music_files = []
        
        if not self.library_path.exists():
            print(f"❌ Library path does not exist: {self.library_path}")
            return music_files
        
        for root, dirs, files in os.walk(self.library_path):
            for file in files:
                file_path = Path(root) / file
                if file_path.suffix.lower() in self.supported_formats:
                    music_files.append(str(file_path))
        
        print(f"✅ Found {len(music_files)} music files")
        return music_files
    
    def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract metadata from music file"""
        try:
            audio_file = File(file_path)
            if audio_file is None:
                return self._fallback_metadata(file_path)
            
            # Extract basic metadata
            metadata = {
                'file_path': file_path,
                'file_size': os.path.getsize(file_path),
                'duration': getattr(audio_file.info, 'length', None),
                'artist': self._get_tag(audio_file, ['TPE1', 'ARTIST', '\xa9ART', 'artist']),
                'album': self._get_tag(audio_file, ['TALB', 'ALBUM', '\xa9alb', 'album']),
                'title': self._get_tag(audio_file, ['TIT2', 'TITLE', '\xa9nam', 'title']),
                'year': self._get_year(audio_file),
                'genre': self._get_tag(audio_file, ['TCON', 'GENRE', '\xa9gen', 'genre'])
            }
            
            # Convert duration to integer seconds
            if metadata['duration']:
                metadata['duration'] = int(float(metadata['duration']))
            
            # Fallback to filename parsing if no metadata
            if not any([metadata['artist'], metadata['album'], metadata['title']]):
                fallback = self._parse_filename(file_path)
                metadata.update(fallback)
            
            return metadata
            
        except Exception as e:
            print(f"⚠️  Error extracting metadata from {file_path}: {e}")
            return self._fallback_metadata(file_path)
    
    def _get_tag(self, audio_file: File, tag_keys: List[str]) -> Optional[str]:
        """Get tag value from multiple possible keys"""
        for key in tag_keys:
            if key in audio_file:
                value = audio_file[key]
                if isinstance(value, list) and value:
                    return str(value[0]).strip()
                elif value:
                    return str(value).strip()
        return None
    
    def _get_year(self, audio_file: File) -> Optional[int]:
        """Extract year from various date formats"""
        year_keys = ['TDRC', 'TYER', 'DATE', '\xa9day', 'date']
        for key in year_keys:
            if key in audio_file:
                value = audio_file[key]
                if isinstance(value, list) and value:
                    value = str(value[0])
                else:
                    value = str(value)
                
                # Extract year from various formats
                if len(value) >= 4 and value[:4].isdigit():
                    return int(value[:4])
        return None
    
    def _parse_filename(self, file_path: str) -> Dict[str, Optional[str]]:
        """Parse metadata from filename and directory structure"""
        path_parts = Path(file_path).parts
        filename = Path(file_path).stem
        
        # Try to extract from directory structure: Artist/Album/Track
        artist = None
        album = None
        title = filename
        
        if len(path_parts) >= 3:
            # Assume structure: .../Artist/Album/Track.ext
            artist = path_parts[-3] if path_parts[-3] != 'MUSIC' else None
            album = path_parts[-2]
        elif len(path_parts) >= 2:
            # Assume structure: .../Artist/Track.ext
            artist = path_parts[-2] if path_parts[-2] != 'MUSIC' else None
        
        # Clean up common filename patterns
        # Remove track numbers: "01 Song Name" -> "Song Name"
        if title and len(title) > 3 and title[:2].isdigit():
            title = title[2:].strip(' -_')
        
        # Handle "Artist - Song" format in filename
        if ' - ' in filename:
            parts = filename.split(' - ', 1)
            if len(parts) == 2 and not artist:
                artist = parts[0].strip()
                title = parts[1].strip()
        
        return {
            'artist': artist,
            'album': album,
            'title': title
        }
    
    def _fallback_metadata(self, file_path: str) -> Dict[str, Any]:
        """Generate fallback metadata when extraction fails"""
        parsed = self._parse_filename(file_path)
        return {
            'file_path': file_path,
            'file_size': os.path.getsize(file_path) if os.path.exists(file_path) else 0,
            'duration': None,
            'artist': parsed['artist'],
            'album': parsed['album'],
            'title': parsed['title'],
            'year': None,
            'genre': None
        }
    
    def generate_embedding(self, metadata: Dict[str, Any]) -> Optional[str]:
        """Generate Ollama embedding for semantic search"""
        try:
            # Create search text from metadata
            search_text_parts = []
            for key in ['artist', 'album', 'title', 'genre']:
                if metadata.get(key):
                    search_text_parts.append(str(metadata[key]))
            
            search_text = ' '.join(search_text_parts)
            if not search_text.strip():
                return None
            
            # Call Ollama embeddings API
            response = requests.post(
                f"{self.ollama_host}/api/embeddings",
                json={
                    "model": "llama3.1:8b",
                    "prompt": search_text
                },
                timeout=30
            )
            
            if response.status_code == 200:
                embedding_data = response.json()
                return json.dumps(embedding_data.get('embedding', []))
            else:
                print(f"⚠️  Embedding failed for '{search_text}': {response.status_code}")
                return None
                
        except Exception as e:
            print(f"⚠️  Error generating embedding: {e}")
            return None
    
    def index_file(self, file_path: str) -> bool:
        """Index a single music file"""
        try:
            print(f"🎼 Indexing: {os.path.basename(file_path)}")
            
            # Extract metadata
            metadata = self.extract_metadata(file_path)
            
            # Generate embedding (optional - can be slow)
            embedding = self.generate_embedding(metadata)
            
            # Add to database
            library_id = self.db.add_to_music_library(
                file_path=metadata['file_path'],
                artist=metadata['artist'],
                album=metadata['album'],
                title=metadata['title'],
                year=metadata['year'],
                genre=metadata['genre'],
                duration=metadata['duration'],
                file_size=metadata['file_size'],
                embedding=embedding
            )
            
            print(f"✅ Indexed: {metadata.get('artist', 'Unknown')} - {metadata.get('title', 'Unknown')} [ID: {library_id}]")
            return True
            
        except Exception as e:
            print(f"❌ Failed to index {file_path}: {e}")
            return False
    
    def index_library(self, max_files: int = None, skip_embeddings: bool = False) -> Dict[str, int]:
        """Index entire music library"""
        print("🎵 Starting music library indexing...")
        
        # Test Ollama connection first
        if not skip_embeddings:
            if not self._test_ollama_connection():
                print("⚠️  Ollama not available - indexing without embeddings")
                skip_embeddings = True
        
        # Scan for music files
        music_files = self.scan_library()
        
        if max_files:
            music_files = music_files[:max_files]
            print(f"📊 Limiting to first {max_files} files for testing")
        
        # Index files
        stats = {'total': len(music_files), 'success': 0, 'failed': 0}
        
        for i, file_path in enumerate(music_files, 1):
            print(f"\n[{i}/{stats['total']}] ", end="")
            
            if skip_embeddings:
                # Temporarily disable embeddings
                original_method = self.generate_embedding
                self.generate_embedding = lambda x: None
            
            success = self.index_file(file_path)
            
            if skip_embeddings:
                self.generate_embedding = original_method
            
            if success:
                stats['success'] += 1
            else:
                stats['failed'] += 1
            
            # Small delay to prevent overwhelming the system
            time.sleep(0.1)
        
        print(f"\n🎉 Indexing complete!")
        print(f"✅ Successful: {stats['success']}")
        print(f"❌ Failed: {stats['failed']}")
        print(f"📊 Total: {stats['total']}")
        
        return stats
    
    def _test_ollama_connection(self) -> bool:
        """Test if Ollama is available"""
        try:
            response = requests.get(f"{self.ollama_host}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def search_test(self, query: str = "queen"):
        """Test search functionality"""
        print(f"\n🔍 Testing search for: '{query}'")
        results = self.db.search_music_library(query, limit=5)
        
        if results:
            print(f"Found {len(results)} results:")
            for i, result in enumerate(results, 1):
                print(f"{i}. {result.get('artist', 'Unknown')} - {result.get('title', 'Unknown')} [{result.get('album', 'Unknown')}]")
        else:
            print("No results found")
        
        return results


def main():
    """Main indexing function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Index music library for Party Memory Wall")
    parser.add_argument("--library", default="/mnt/media/MUSIC", help="Music library path")
    parser.add_argument("--ollama", default="http://127.0.0.1:11434", help="Ollama server URL")
    parser.add_argument("--max-files", type=int, help="Maximum files to index (for testing)")
    parser.add_argument("--skip-embeddings", action="store_true", help="Skip embedding generation")
    parser.add_argument("--test-search", help="Test search with query")
    
    args = parser.parse_args()
    
    indexer = MusicLibraryIndexer(
        library_path=args.library,
        ollama_host=args.ollama
    )
    
    if args.test_search:
        indexer.search_test(args.test_search)
    else:
        stats = indexer.index_library(
            max_files=args.max_files,
            skip_embeddings=args.skip_embeddings
        )
        
        # Test search after indexing
        if stats['success'] > 0:
            indexer.search_test("queen")


if __name__ == "__main__":
    main()