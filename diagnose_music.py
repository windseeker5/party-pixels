#!/usr/bin/env python3
"""
Diagnose Music Search Issues
Quick diagnostic tool to check all components
"""

import requests
import json
from database import PartyDatabase

def test_api_endpoints():
    """Test all music API endpoints"""
    print("🔧 Testing Music API Endpoints")
    print("-" * 40)
    
    base_url = "http://localhost:8000"
    
    # Test search endpoint
    try:
        response = requests.post(f"{base_url}/api/music/search", 
            json={"query": "evanescence"}, timeout=10)
        print(f"✅ Search API: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   - Found {data.get('total_results', 0)} results")
        else:
            print(f"   - Error: {response.text}")
    except Exception as e:
        print(f"❌ Search API: {e}")
    
    # Test AI DJ status
    try:
        response = requests.get(f"{base_url}/api/music/ai-dj-status", timeout=5)
        print(f"✅ AI DJ Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   - Searches: {data.get('total_searches', 0)}/{data.get('threshold', 25)}")
    except Exception as e:
        print(f"❌ AI DJ Status: {e}")
    
    # Test upload page
    try:
        response = requests.get(f"{base_url}/upload", timeout=5)
        print(f"✅ Upload Page: {response.status_code}")
        if "music-search-section" in response.text:
            print("   - Music search UI present")
        else:
            print("   - Music search UI missing")
    except Exception as e:
        print(f"❌ Upload Page: {e}")

def test_database():
    """Test database functionality"""
    print("\n🔧 Testing Database")
    print("-" * 40)
    
    try:
        db = PartyDatabase()
        
        # Check music library
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM music_library")
        count = cursor.fetchone()[0]
        print(f"✅ Music Library: {count} songs indexed")
        
        if count > 0:
            cursor.execute("SELECT artist, title FROM music_library LIMIT 3")
            songs = cursor.fetchall()
            for song in songs:
                print(f"   - {song[0] or 'Unknown'} - {song[1] or 'Unknown'}")
        
        # Check search functionality
        results = db.search_music_library("evanescence", limit=3)
        print(f"✅ Search Function: {len(results)} results for 'evanescence'")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Database: {e}")

def test_file_access():
    """Test file access and paths"""
    print("\n🔧 Testing File Access")
    print("-" * 40)
    
    import os
    
    files_to_check = [
        '/home/kdresdell/Documents/DEV/PartyWall/templates/upload.html',
        '/home/kdresdell/Documents/DEV/PartyWall/static/party-upload.js',
        '/home/kdresdell/Documents/DEV/PartyWall/static/styles.css',
        '/home/kdresdell/Documents/DEV/PartyWall/music_search.py',
        '/home/kdresdell/Documents/DEV/PartyWall/database.py',
    ]
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"✅ {os.path.basename(file_path)}: {size} bytes")
        else:
            print(f"❌ {os.path.basename(file_path)}: Missing")
    
    # Check if JavaScript has music search code
    try:
        with open('/home/kdresdell/Documents/DEV/PartyWall/static/party-upload.js', 'r') as f:
            js_content = f.read()
            if 'setupMusicSearch' in js_content:
                print("✅ JavaScript: Music search methods present")
            else:
                print("❌ JavaScript: Music search methods missing")
    except Exception as e:
        print(f"❌ JavaScript check: {e}")

def suggest_fixes():
    """Suggest potential fixes"""
    print("\n💡 Troubleshooting Steps")
    print("-" * 40)
    
    print("1. Clear browser cache and reload upload page")
    print("2. Check browser console for JavaScript errors")
    print("3. Try search with: 'evanescence', 'mozart', 'kanye'")
    print("4. Verify Flask server restarted after code changes")
    print("5. Test debug page: http://localhost:8000/test_music_ui.html")

def main():
    print("🎵 Music Search Diagnostics")
    print("=" * 50)
    
    test_database()
    test_api_endpoints()
    test_file_access()
    suggest_fixes()
    
    print("\n🎵 Diagnostic complete!")

if __name__ == "__main__":
    main()