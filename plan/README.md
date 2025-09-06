# Party Memory Wall - Implementation Plan

## Project Overview
A party photo/music sharing application for Valérie's 50th Birthday celebration. Guests upload photos/videos via mobile web interface, displayed on big screen with permanent celebration title.

## Selected Architecture
- **Frontend**: Instagram Story Layout (Full Screen) with Vanilla JS/CSS
- **Backend**: Flask on port 6000 with SQLite
- **Deployment**: Docker containers on Raspberry Pi 4B
- **Special Feature**: Permanent celebration title with beautiful animations

## Wireframe - Instagram Story Full Screen Layout

```
┌────────────────────────────────────────────────┐
│  ✨ Happy 50th Birthday Valérie! ✨            │  ← PERMANENT TITLE
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │     (Animated sparkles)
│                                                 │
│          [FULL SCREEN PHOTO/VIDEO]             │
│                                                 │
│  ┌──────────────┐              ┌─────────────┐│
│  │🎵 Now Playing│              │📱 Share Now!││
│  │ "Song Name"  │              │  [QR CODE]  ││
│  │ by Guest     │              │ party.local ││
│  └──────────────┘              └─────────────┘│
│                                                 │
│       ┌──────────────────────────────┐         │
│       │ 📸 From: "Sarah's iPhone" 💝 │         │
│       └──────────────────────────────┘         │
│                                                 │
│  [Progress Bar: ████████░░░░ 15 sec]          │
│  [◀ ● ● ● ● ▶] Next 5 photos preview          │
└────────────────────────────────────────────────┘
```

## Agent Assignments

### Backend Tasks - Agent: backend-architect
- Build Flask API with file upload (port 6000)
- Implement SQLite database
- Create WebSocket server
- Docker container setup
- Party configuration endpoints

### Frontend Tasks - Agent: flask-ui-developer
- Create responsive upload page
- Build slideshow display with celebration title
- Implement hardware-accelerated animations
- WebSocket client integration
- Celebration title with glamorous styling

### Testing Tasks - Agent: general-purpose
- Write unit tests using existing MCP Playwright
- Test on Flask running on port 6000
- Validate RPi performance
- All tests in /test folder

## Testing Instructions for Agents

IMPORTANT: 
- Flask MUST run on port 6000 for testing
- Use existing MCP Playwright server (no new installation)
- All tests go in /test folder
- Test both photo AND video uploads
- Test celebration title animations

## File Structure

```
party-wall/
├── plan/
│   ├── README.md (this file)
│   ├── backend-tasks.md
│   ├── frontend-tasks.md
│   ├── testing-strategy.md
│   └── wireframe.md
├── test/
│   ├── test_upload_api.py
│   ├── test_slideshow_api.py
│   ├── test_websocket.py
│   ├── test_database.py
│   └── test_frontend.py
├── backend/
│   ├── app.py
│   ├── database.py
│   ├── websocket_handler.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── index.html
│   ├── upload.html
│   ├── party-display.js
│   ├── party-upload.js
│   └── styles.css
├── media/
│   ├── photos/
│   ├── videos/
│   └── music/
└── database/
    └── party.db
```

## Key Features

### Celebration Title
- **Text**: "Happy 50th Birthday Valérie!"
- **Style**: Glamorous Hollywood with gold gradient
- **Animation**: Shimmer effect with floating sparkles
- **Position**: Fixed top, always visible
- **Font**: Great Vibes (elegant script) with fallback

### Media Support
- **Photos**: JPG, PNG, HEIC (Ken Burns effect)
- **Videos**: MP4, MOV, WebM (full duration playback)
- **Music**: MP3, M4A (background queue)
- **Max Size**: 500MB per file

### Real-time Features
- WebSocket for live updates
- Auto-advancing slideshow
- Music queue management
- Guest attribution display
- Progress indicators

## Implementation Order
1. ✅ Plan documentation (current)
2. Create test specifications
3. Backend implementation by backend-architect
4. Frontend implementation by flask-ui-developer
5. Integration testing with Playwright
6. Performance testing on Raspberry Pi

## Critical Requirements
- Flask ALWAYS runs on port 6000
- Use existing MCP Playwright server
- All tests in test/ folder
- Support both photos AND videos
- Optimize for Raspberry Pi 4B performance
- Celebration title must remain visible throughout weekend