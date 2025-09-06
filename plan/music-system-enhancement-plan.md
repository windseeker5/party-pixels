# Music System Enhancement Plan
## Smart Search with Local Library + YouTube Fallback

### Overview
Transform the music system from file uploads to intelligent search with local library priority and YouTube fallback. After learning from 25-50 user selections, offer AI DJ mode for automated music curation.

---

## Phase 1: Core Search Infrastructure

### Task 1.1: Set up Ollama for Semantic Search
**Agent**: backend-architect
**Sub-tasks**:
1. Install and configure Ollama on Raspberry Pi
2. Select lightweight model (e.g., phi-2, tinyllama)
3. Create embeddings service for music library indexing

**Required Tools/Credentials**:
```bash
# Ollama server is already running at: 127.0.0.1:11434
# No installation needed for testing

# Test endpoint
curl http://127.0.0.1:11434/api/generate -d '{
  "model": "phi-2",
  "prompt": "Find songs similar to Bohemian Rhapsody"
}'
```

**Test Location**: `/test/test_ollama_integration.py`

---

### Task 1.2: Index Music Library
**Agent**: backend-architect
**Sub-tasks**:
1. Scan `/mnt/media/MUSIC/` directory structure (organized by album)
2. Extract metadata (artist, album, track, year)
3. Create SQLite FTS5 full-text search table
4. Generate Ollama embeddings for semantic search

**Database Schema**:
```sql
CREATE TABLE music_library (
    id INTEGER PRIMARY KEY,
    file_path TEXT UNIQUE NOT NULL,
    artist TEXT,
    album TEXT,
    title TEXT,
    year INTEGER,
    genre TEXT,
    duration INTEGER,
    embedding BLOB,  -- Ollama embedding vector
    indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE VIRTUAL TABLE music_search USING fts5(
    artist, album, title, genre,
    content=music_library
);
```

**Test Location**: `/test/test_music_indexing.py`

---

## Phase 2: Search API Implementation

### Task 2.1: Create Search Endpoint
**Agent**: backend-architect
**Sub-tasks**:
1. Implement `/api/music/search` endpoint
2. Integrate Ollama for natural language processing
3. Implement fuzzy matching fallback
4. Return combined local + YouTube results

**API Specification**:
```python
@app.route('/api/music/search', methods=['POST'])
def search_music():
    """
    Request:
    {
        "query": "play something by queen",
        "limit": 10
    }
    
    Response:
    {
        "local": [
            {
                "id": "local_123",
                "title": "Bohemian Rhapsody",
                "artist": "Queen",
                "album": "A Night at the Opera",
                "path": "/mnt/media/MUSIC/Queen/A Night at the Opera/01.mp3",
                "source": "local"
            }
        ],
        "youtube": [
            {
                "id": "yt_abc",
                "title": "Queen - We Will Rock You",
                "channel": "Queen Official",
                "url": "https://youtube.com/watch?v=...",
                "duration": 122,
                "source": "youtube"
            }
        ]
    }
    """
```

**Test Location**: `/test/test_search_api.py`

---

### Task 2.2: YouTube Search Integration
**Agent**: backend-architect
**Sub-tasks**:
1. Integrate youtube-search-python library
2. Implement search with configurable result limit
3. Filter for music content only
4. Extract relevant metadata

**Required Libraries**:
```bash
pip install youtube-search-python
pip install yt-dlp
```

**Implementation Notes**:
```python
from youtubesearchpython import VideosSearch

def search_youtube_music(query, limit=5):
    search = VideosSearch(f"{query} music", limit=limit)
    results = search.result()
    # Filter and format results
    return formatted_results
```

**Test Location**: `/test/test_youtube_search.py`

---

## Phase 3: YouTube Download System

### Task 3.1: Implement Download Endpoint
**Agent**: backend-architect
**Sub-tasks**:
1. Create `/api/music/download` endpoint
2. Use yt-dlp for audio extraction
3. Save to `/media/music/party-requested/`
4. Add to music queue automatically
5. Broadcast real-time updates via WebSocket

**Download Configuration**:
```python
ydl_opts = {
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
    'outtmpl': '/mnt/media/MUSIC/party-requested/%(title)s.%(ext)s',
    'quiet': True,
    'no_warnings': True,
}
```

**Test Location**: `/test/test_youtube_download.py`

---

## Phase 4: Frontend Search Interface

### Task 4.1: Replace Upload with Search
**Agent**: flask-ui-developer
**Sub-tasks**:
1. Replace music file upload with search box
2. Implement real-time search suggestions
3. Display results with source badges (local/YouTube)
4. Add one-click queue addition

**UI Components**:
```html
<!-- Search Box -->
<div class="music-search-container">
    <input type="text" 
           id="music-search" 
           placeholder="Search for a song, artist, or just describe a vibe..."
           autocomplete="off">
    <div id="search-suggestions"></div>
</div>

<!-- Results Display -->
<div class="search-results">
    <div class="local-results">
        <h3>🎵 From Party Collection</h3>
        <!-- Local results -->
    </div>
    <div class="youtube-results">
        <h3>🌐 From YouTube</h3>
        <!-- YouTube results -->
    </div>
</div>
```

**Test Location**: `/test/test_search_ui.py` (Playwright)

---

## Phase 5: Learning System

### Task 5.1: Track User Behavior
**Agent**: backend-architect
**Sub-tasks**:
1. Log all searches in database
2. Track selections (local vs YouTube)
3. Record timestamp and party context
4. Calculate party energy metrics

**Database Schema**:
```sql
CREATE TABLE music_searches (
    id INTEGER PRIMARY KEY,
    query TEXT NOT NULL,
    selected_result TEXT,
    source TEXT CHECK(source IN ('local', 'youtube')),
    guest_name TEXT,
    party_energy REAL,  -- Based on upload frequency
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE music_patterns (
    id INTEGER PRIMARY KEY,
    pattern_type TEXT,  -- genre, energy, era
    pattern_value TEXT,
    frequency INTEGER,
    last_seen TIMESTAMP
);
```

**Test Location**: `/test/test_learning_system.py`

---

### Task 5.2: AI DJ Mode Trigger
**Agent**: ui-designer + backend-architect
**Sub-tasks**:
1. Monitor selection count
2. After 25-50 selections, show AI DJ offer
3. Implement acceptance flow
4. Store user preference

**Trigger Logic**:
```javascript
// Frontend trigger
if (totalSelections >= 25 && !aiDjOffered) {
    showAiDjModal({
        title: "🎉 I've learned your party's vibe!",
        message: "Want me to keep the music flowing automatically?",
        options: ["Let AI DJ Take Over", "Keep Choosing Songs"]
    });
}
```

**Test Location**: `/test/test_ai_dj_trigger.py`

---

## Phase 6: AI DJ Implementation

### Task 6.1: Pattern Analysis
**Agent**: backend-architect
**Sub-tasks**:
1. Analyze selected songs for patterns
2. Extract genres, energy levels, eras
3. Build preference profile
4. Generate recommendations

**Analysis Algorithm**:
```python
def analyze_music_patterns(selections):
    patterns = {
        'genres': Counter(),
        'decades': Counter(),
        'energy': [],  # 1-10 scale
        'tempo': [],   # BPM if available
    }
    
    # Analyze each selection
    for song in selections:
        # Extract and count patterns
        pass
    
    return generate_profile(patterns)
```

**Test Location**: `/test/test_pattern_analysis.py`

---

### Task 6.2: Auto-Queue Management
**Agent**: backend-architect
**Sub-tasks**:
1. Generate queue based on patterns
2. Maintain energy flow
3. Allow manual overrides
4. Smooth transitions

**Test Location**: `/test/test_auto_queue.py`

---

## Phase 7: Memory Collection

### Task 7.1: Save All Music Locally
**Agent**: backend-architect
**Sub-tasks**:
1. Organize music by source
2. Create playlist export
3. Include metadata

**Directory Structure**:
```
/mnt/media/MUSIC/
├── party-originals/     # From local library
├── party-requested/     # YouTube downloads
└── party-playlist.json  # Complete sequence with timestamps
```

**Playlist Format**:
```json
{
    "party_date": "2024-01-20",
    "total_songs": 142,
    "ai_dj_activated": true,
    "playlist": [
        {
            "position": 1,
            "title": "Celebration",
            "artist": "Kool & The Gang",
            "played_at": "2024-01-20T20:15:00",
            "source": "local",
            "requested_by": "Kevin",
            "energy_level": 8
        }
    ]
}
```

**Test Location**: `/test/test_memory_collection.py`

---

## Testing Strategy

### Unit Tests Required
Location: `/test/`

1. **test_ollama_integration.py**
   - Test Ollama connection
   - Test embedding generation
   - Test semantic search

2. **test_music_indexing.py**
   - Test library scanning
   - Test metadata extraction
   - Test FTS5 search

3. **test_search_api.py**
   - Test search endpoint
   - Test fuzzy matching
   - Test result formatting

4. **test_youtube_search.py**
   - Test YouTube API calls
   - Test result filtering
   - Test error handling

5. **test_youtube_download.py**
   - Test yt-dlp integration
   - Test file saving
   - Test queue addition

6. **test_search_ui.py** (Playwright)
   - Test search interface
   - Test result display
   - Test one-click addition

7. **test_learning_system.py**
   - Test behavior tracking
   - Test pattern detection
   - Test threshold triggers

8. **test_ai_dj_trigger.py**
   - Test modal display
   - Test user acceptance
   - Test mode activation

9. **test_pattern_analysis.py**
   - Test pattern extraction
   - Test profile generation
   - Test recommendation logic

10. **test_auto_queue.py**
    - Test queue generation
    - Test energy management
    - Test override handling

11. **test_memory_collection.py**
    - Test file organization
    - Test playlist export
    - Test metadata preservation

---

## Required Dependencies

```bash
# Backend
pip install ollama
pip install youtube-search-python
pip install yt-dlp
pip install chromadb  # For vector search
pip install fuzzywuzzy  # For fuzzy matching
pip install python-Levenshtein  # For fuzzy matching optimization

# Testing
pip install pytest
pip install pytest-asyncio
pip install pytest-mock
pip install playwright
```

---

## Environment Variables

```bash
# .env file
OLLAMA_HOST=http://127.0.0.1:11434
MUSIC_LIBRARY_PATH=/mnt/media/MUSIC
YOUTUBE_DL_PATH=/usr/local/bin/yt-dlp
MAX_DOWNLOAD_SIZE=50MB
AI_DJ_THRESHOLD=25  # Number of selections before offering AI mode
```

---

## Success Metrics

1. **Search Performance**: < 500ms response time
2. **YouTube Downloads**: < 30s per song
3. **AI DJ Accuracy**: 70% acceptance rate of suggestions
4. **Memory Collection**: 100% of played music saved locally
5. **User Engagement**: 50% activate AI DJ when offered

---

## Risk Mitigation

1. **YouTube API Limits**: Cache search results for 1 hour
2. **Download Failures**: Retry logic with exponential backoff
3. **Ollama Offline**: Fallback to keyword search
4. **Storage Space**: Monitor and alert at 80% capacity
5. **Network Issues**: Queue downloads, process when available

---

## Implementation Order

1. **Week 1**: Tasks 1.1-1.2 (Ollama setup, library indexing)
2. **Week 1**: Tasks 2.1-2.2 (Search API, YouTube integration)
3. **Week 2**: Tasks 3.1, 4.1 (Download system, UI)
4. **Week 2**: Tasks 5.1-5.2 (Learning system, AI trigger)
5. **Week 3**: Tasks 6.1-6.2 (AI DJ implementation)
6. **Week 3**: Task 7.1 (Memory collection)
7. **Week 4**: Testing and refinement

---

## Notes for Agents

### backend-architect
- Focus on performance for Raspberry Pi deployment
- Implement proper error handling and logging
- Ensure all downloads are virus-scanned
- Use connection pooling for database

### flask-ui-developer
- Maintain mobile-first design
- Use WebSocket for real-time updates
- Implement loading states for downloads
- Keep UI responsive during searches

### ui-designer
- Design clear visual hierarchy for search results
- Create engaging AI DJ modal
- Use consistent party theme styling
- Ensure accessibility standards

### trend-researcher
- Monitor popular party music trends
- Identify energy pattern templates
- Research optimal BPM progressions
- Study party music psychology

---

## Post-Event Deliverables

1. Complete music collection on USB drive
2. Detailed playlist with timestamps
3. Analytics report (most played, peak times)
4. Guest preference profiles
5. AI DJ performance metrics