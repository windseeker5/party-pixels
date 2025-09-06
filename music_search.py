"""
Music Search Service
Handles local library search, YouTube search, and Ollama integration
"""

import os
import json
import requests
import re
from typing import List, Dict, Any, Optional
from youtubesearchpython import VideosSearch
from fuzzywuzzy import fuzz
from database import PartyDatabase


class MusicSearchService:
    """Service for searching music locally and on YouTube"""
    
    def __init__(self, db: PartyDatabase, ollama_host: str = "http://127.0.0.1:11434"):
        self.db = db
        self.ollama_host = ollama_host
        self.ollama_available = self._test_ollama_connection()
    
    def _test_ollama_connection(self) -> bool:
        """Test if Ollama is available"""
        try:
            response = requests.get(f"{self.ollama_host}/api/tags", timeout=3)
            return response.status_code == 200
        except:
            return False
    
    def search_local_library(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search local music library"""
        results = []
        
        # First try FTS5 search
        fts_results = self.db.search_music_library(query, limit)
        results.extend(fts_results)
        
        # If FTS5 doesn't find enough results, try fuzzy matching
        if len(results) < limit:
            fuzzy_results = self._fuzzy_search_library(query, limit - len(results))
            # Avoid duplicates
            existing_paths = {r['file_path'] for r in results}
            for result in fuzzy_results:
                if result['file_path'] not in existing_paths:
                    results.append(result)
        
        return results[:limit]
    
    def _fuzzy_search_library(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Fuzzy search through music library"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT id, file_path, artist, album, title, year, genre, duration, file_size
        FROM music_library
        ORDER BY id
        ''')
        
        all_songs = cursor.fetchall()
        conn.close()
        
        # Score each song based on fuzzy matching
        scored_songs = []
        query_lower = query.lower()
        
        for row in all_songs:
            song = dict(row)
            
            # Create searchable text
            search_text_parts = []
            for field in ['artist', 'album', 'title', 'genre']:
                value = song.get(field)
                if value:
                    search_text_parts.append(str(value).lower())
            
            search_text = ' '.join(search_text_parts)
            
            # Calculate fuzzy score
            score = fuzz.partial_ratio(query_lower, search_text)
            
            if score > 60:  # Minimum threshold
                song['source'] = 'local'
                song['url'] = f"/media/music/{os.path.basename(song['file_path'])}"
                song['_score'] = score
                scored_songs.append(song)
        
        # Sort by score and return top results
        scored_songs.sort(key=lambda x: x['_score'], reverse=True)
        return scored_songs[:limit]
    
    def search_youtube(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search YouTube for music"""
        try:
            # Add "music" to the query to improve results
            music_query = f"{query} music"
            
            # Search YouTube
            videos_search = VideosSearch(music_query, limit=limit)
            results = videos_search.result()
            
            youtube_results = []
            for video in results.get('result', []):
                # Filter out obviously non-music content
                title = video.get('title', '').lower()
                if self._is_music_video(title, video.get('channel', {}).get('name', '')):
                    youtube_results.append({
                        'id': video['id'],
                        'title': video['title'],
                        'artist': video.get('channel', {}).get('name', 'Unknown'),
                        'duration': self._parse_duration(video.get('duration')),
                        'url': video['link'],
                        'thumbnail': video.get('thumbnails', [{}])[-1].get('url'),
                        'views': video.get('viewCount', {}).get('text', ''),
                        'source': 'youtube'
                    })
            
            return youtube_results
            
        except Exception as e:
            print(f"YouTube search error: {e}")
            return []
    
    def _is_music_video(self, title: str, channel: str) -> bool:
        """Heuristic to determine if a YouTube video is music"""
        # Keywords that suggest music content
        music_keywords = ['official', 'music', 'song', 'album', 'single', 'audio', 'lyrics']
        
        # Keywords that suggest non-music content
        exclude_keywords = ['tutorial', 'lesson', 'review', 'reaction', 'interview', 'live stream']
        
        title_lower = title.lower()
        channel_lower = channel.lower()
        
        # Check for exclusions first
        for keyword in exclude_keywords:
            if keyword in title_lower:
                return False
        
        # Check for music indicators
        for keyword in music_keywords:
            if keyword in title_lower or keyword in channel_lower:
                return True
        
        # If it contains common music patterns, it's likely music
        if any(pattern in title_lower for pattern in [' - ', ' feat', ' ft', ' remix']):
            return True
        
        return True  # Default to including if unsure
    
    def _parse_duration(self, duration_str: Optional[str]) -> Optional[int]:
        """Parse YouTube duration string to seconds"""
        if not duration_str:
            return None
        
        try:
            # Handle format like "3:45" or "1:23:45"
            parts = duration_str.split(':')
            if len(parts) == 2:  # mm:ss
                return int(parts[0]) * 60 + int(parts[1])
            elif len(parts) == 3:  # hh:mm:ss
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        except:
            pass
        
        return None
    
    def search_with_ollama(self, query: str) -> Optional[str]:
        """Use Ollama to enhance search query"""
        if not self.ollama_available:
            return query
        
        try:
            prompt = f"""Given this music search query: "{query}"

Extract the key information and suggest 2-3 alternative search terms that would help find similar music.
Focus on artist names, song titles, genres, or musical styles.
Return only the search terms, separated by commas.

Query: {query}
Search terms:"""

            response = requests.post(
                f"{self.ollama_host}/api/generate",
                json={
                    "model": "llama3.1:8b",
                    "prompt": prompt,
                    "stream": False
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                enhanced_query = result.get('response', '').strip()
                return enhanced_query if enhanced_query else query
                
        except Exception as e:
            print(f"Ollama enhancement error: {e}")
        
        return query
    
    def combined_search(self, query: str, local_limit: int = 10, youtube_limit: int = 5) -> Dict[str, Any]:
        """Perform combined local + YouTube search"""
        
        # Log the search
        self.db.log_music_search(query)
        
        # Enhance query with Ollama if available
        enhanced_query = self.search_with_ollama(query)
        
        # Search local library
        local_results = self.search_local_library(query, local_limit)
        
        # Search YouTube if we need more results
        youtube_results = []
        if len(local_results) < 3:  # Always get some YouTube results
            youtube_results = self.search_youtube(enhanced_query, youtube_limit)
        
        return {
            'query': query,
            'enhanced_query': enhanced_query if enhanced_query != query else None,
            'local': local_results,
            'youtube': youtube_results,
            'total_results': len(local_results) + len(youtube_results)
        }
    
    def get_recommendations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get music recommendations based on patterns"""
        patterns = self.db.get_music_patterns(limit=20)
        
        if not patterns:
            # Return random popular songs from library
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
            SELECT id, file_path, artist, album, title, year, genre
            FROM music_library
            ORDER BY RANDOM()
            LIMIT ?
            ''', (limit,))
            
            results = []
            for row in cursor.fetchall():
                song = dict(row)
                song['source'] = 'local'
                song['url'] = f"/media/music/{os.path.basename(song['file_path'])}"
                results.append(song)
            
            conn.close()
            return results
        
        # Use patterns to find similar music
        # This is a simplified version - could be enhanced with ML
        popular_artists = [p['pattern_value'] for p in patterns if p['pattern_type'] == 'artist'][:5]
        
        if not popular_artists:
            return []
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Find songs by popular artists
        placeholders = ','.join('?' * len(popular_artists))
        cursor.execute(f'''
        SELECT id, file_path, artist, album, title, year, genre
        FROM music_library
        WHERE artist IN ({placeholders})
        ORDER BY RANDOM()
        LIMIT ?
        ''', popular_artists + [limit])
        
        results = []
        for row in cursor.fetchall():
            song = dict(row)
            song['source'] = 'local'
            song['url'] = f"/media/music/{os.path.basename(song['file_path'])}"
            results.append(song)
        
        conn.close()
        return results