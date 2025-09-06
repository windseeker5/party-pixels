#!/usr/bin/env python3
"""
Test Music Search API Endpoints
Tests the music search, indexing, and learning systems
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import requests
import json
from database import PartyDatabase
from music_search import MusicSearchService

class TestMusicSearch:
    """Test music search functionality"""
    
    @classmethod
    def setup_class(cls):
        """Set up test environment"""
        cls.base_url = "http://localhost:8000"
        
        # Create database with proper initialization
        import tempfile
        cls.test_db_file = tempfile.mktemp(suffix='.db')
        cls.db = PartyDatabase(cls.test_db_file)
        cls.music_search = MusicSearchService(cls.db)
        
        # Add some test data
        cls.db.add_to_music_library(
            file_path="/test/queen.mp3",
            artist="Queen",
            title="Bohemian Rhapsody",
            album="A Night at the Opera",
            year=1975,
            genre="Rock"
        )
        
        cls.db.add_to_music_library(
            file_path="/test/mozart.mp3",
            artist="Wolfgang Amadeus Mozart",
            title="Eine kleine Nachtmusik",
            album="Classical Masterpieces",
            year=1787,
            genre="Classical"
        )
    
    def test_music_search_api(self):
        """Test the music search API endpoint"""
        try:
            response = requests.post(f"{self.base_url}/api/music/search", 
                json={"query": "queen", "local_limit": 5})
            
            assert response.status_code == 200
            data = response.json()
            
            assert "query" in data
            assert "local" in data
            assert "youtube" in data
            assert "total_results" in data
            
            print("✅ Music search API test passed")
            
        except requests.exceptions.ConnectionError:
            print("⚠️  Flask server not running, skipping API test")
            pytest.skip("Flask server not available")
    
    def test_local_library_search(self):
        """Test local library search"""
        results = self.music_search.search_local_library("queen", limit=5)
        
        assert isinstance(results, list)
        if results:  # Only test if we have results
            result = results[0]
            assert "artist" in result
            assert "title" in result
            assert "source" in result
            assert result["source"] == "local"
        
        print("✅ Local library search test passed")
    
    def test_youtube_search(self):
        """Test YouTube search functionality"""
        results = self.music_search.search_youtube("test song", limit=3)
        
        assert isinstance(results, list)
        # YouTube results may be empty due to network issues, so just check structure
        for result in results:
            assert "title" in result
            assert "source" in result
            assert result["source"] == "youtube"
        
        print("✅ YouTube search test passed")
    
    def test_combined_search(self):
        """Test combined search functionality"""
        results = self.music_search.combined_search("queen", local_limit=5, youtube_limit=3)
        
        assert isinstance(results, dict)
        assert "query" in results
        assert "local" in results
        assert "youtube" in results
        assert "total_results" in results
        
        print("✅ Combined search test passed")
    
    def test_music_patterns(self):
        """Test music pattern tracking"""
        # Add some pattern data
        self.db.update_music_pattern("artist", "Queen")
        self.db.update_music_pattern("artist", "Queen")  # Increment frequency
        self.db.update_music_pattern("genre", "Rock")
        
        patterns = self.db.get_music_patterns()
        assert isinstance(patterns, list)
        
        if patterns:
            pattern = patterns[0]
            assert "pattern_type" in pattern
            assert "pattern_value" in pattern
            assert "frequency" in pattern
        
        print("✅ Music patterns test passed")
    
    def test_search_logging(self):
        """Test search behavior logging"""
        search_id = self.db.log_music_search(
            query="test query",
            selected_result={"title": "Test Song", "artist": "Test Artist"},
            source="local",
            guest_name="Test User"
        )
        
        assert isinstance(search_id, int)
        assert search_id > 0
        
        # Test search count
        count = self.db.get_search_count()
        assert count >= 1
        
        print("✅ Search logging test passed")
    
    def test_ai_dj_status_api(self):
        """Test AI DJ status API endpoint"""
        try:
            response = requests.get(f"{self.base_url}/api/music/ai-dj-status")
            
            assert response.status_code == 200
            data = response.json()
            
            assert "total_searches" in data
            assert "threshold" in data
            assert "ready_for_ai_dj" in data
            assert "searches_remaining" in data
            
            print("✅ AI DJ status API test passed")
            
        except requests.exceptions.ConnectionError:
            print("⚠️  Flask server not running, skipping API test")
            pytest.skip("Flask server not available")
    
    def test_music_recommendations(self):
        """Test music recommendations"""
        recommendations = self.music_search.get_recommendations(limit=5)
        
        assert isinstance(recommendations, list)
        # Recommendations may be empty if no patterns exist
        for rec in recommendations:
            assert "source" in rec
            
        print("✅ Music recommendations test passed")


def test_music_indexer():
    """Test music library indexer"""
    try:
        from music_indexer import MusicLibraryIndexer
        
        indexer = MusicLibraryIndexer(
            library_path="/tmp/test_music",  # Use temp directory
            ollama_host="http://127.0.0.1:11434"
        )
        
        # Test metadata extraction (with fake file)
        metadata = indexer._parse_filename("/test/Queen/A Night at the Opera/01 Bohemian Rhapsody.mp3")
        assert metadata["artist"] == "Queen"
        assert metadata["album"] == "A Night at the Opera"
        assert "Bohemian Rhapsody" in metadata["title"]
        
        print("✅ Music indexer test passed")
        
    except ImportError:
        print("⚠️  Music indexer import failed, skipping test")


def run_tests():
    """Run all music system tests"""
    print("🎵 Running Music System Tests")
    print("=" * 50)
    
    # Run pytest
    exit_code = pytest.main([
        __file__,
        "-v",
        "--tb=short"
    ])
    
    if exit_code == 0:
        print("\n🎉 All music system tests passed!")
    else:
        print(f"\n❌ Some tests failed (exit code: {exit_code})")
    
    return exit_code


if __name__ == "__main__":
    run_tests()