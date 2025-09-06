# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Party Memory Wall is a Flask-based web application designed for Valérie's 50th Birthday celebration. It's a real-time photo/video sharing platform optimized for Raspberry Pi deployment with Docker containerization.

## Development Commands

### Starting the Application

**Docker Deployment (Recommended):**
```bash
./start-party.sh              # Start complete party system
./start-party.sh --logs       # Start and follow logs
```

**Development Mode:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  
pip install -r requirements.txt
python app.py                 # Runs on port 8000 by default
```

### Testing

```bash
# Install test dependencies
pip install pytest playwright websockets

# Run all tests
python -m pytest test/ -v

# Run specific test categories
python -m pytest test/test_upload_api.py -v     # API tests
python -m pytest test/test_frontend.py -v      # UI tests  
python -m pytest test/test_database.py -v      # Database tests
python -m pytest test/test_websocket.py -v     # WebSocket tests
python -m pytest test/test_integration.py -v   # End-to-end tests

# Quick validation
python3 test_basic.py
```

**CRITICAL:** Flask MUST run on port 6000 for testing compatibility. The main app.py currently runs on port 8000 but tests expect port 6000.

### Docker Operations

```bash
# Stop containers
docker-compose -f docker-compose-party.yml down --remove-orphans

# View container status
docker-compose -f docker-compose-party.yml ps

# Follow logs
docker-compose -f docker-compose-party.yml logs -f

# Download party memories
docker cp party-memory-wall:/app/media ./party-memories
```

## Architecture

### Backend (Flask + SQLite)
- **Main App**: `backend/app.py` - Flask server with SocketIO for real-time updates
- **Database**: `backend/database.py` - SQLite database operations
- **Port**: 8000 for main deployment, 6000 required for testing
- **File Storage**: `media/` directory with subdirectories for photos/, videos/, music/
- **WebSocket**: Real-time updates for new uploads and slideshow control

### Frontend (Vanilla JS + CSS)
- **Slideshow Display**: `frontend/index.html` + `frontend/party-display.js`
- **Upload Interface**: `frontend/upload.html` + `frontend/party-upload.js`
- **Styling**: `frontend/styles.css` with hardware-accelerated animations
- **Key Feature**: Permanent "Happy 50th Birthday Valérie!" title with shimmer animation
- **Responsive**: Mobile-first design optimized for touch interactions

### Docker Configuration
- **Backend Container**: `party-flask` (Flask app)
- **Proxy Container**: `party-nginx` (NGINX reverse proxy)
- **Volumes**: Persistent storage for media files and database
- **Networks**: Bridge network for container communication

## Key Technical Details

### File Upload System
- **Max File Size**: 500MB per file
- **Supported Types**: 
  - Photos: JPG, PNG, HEIC, WebP, GIF
  - Videos: MP4, MOV, WebM, AVI, M4V, MKV  
  - Music: MP3, M4A, WAV, FLAC
- **Processing**: Auto-detection of file types, secure filename generation
- **Storage**: Organized by type in media/ subdirectories

### Real-time Features
- **WebSocket Endpoint**: `/socket.io/` for live updates
- **Broadcasting**: New uploads, music queue changes, slideshow controls
- **Client Events**: `new_upload`, `music_update`, `slideshow_update`

### Database Schema
The SQLite database (`database/party.db`) includes tables for:
- `uploads` - File upload records with guest attribution
- `music_queue` - Music playback queue management
- `settings` - Configurable party settings
- Managed through `PartyDatabase` class in `database.py`

### Performance Optimizations
- **Raspberry Pi Focused**: Hardware-accelerated CSS (transform/opacity only)
- **Efficient WebSockets**: Minimal bandwidth usage for updates
- **Compressed Assets**: Gzip compression in NGINX
- **Image Processing**: Placeholder for thumbnails and metadata extraction

## Access Points

- **Main Display**: `http://localhost:8000/` or `http://party.local/`
- **Upload Interface**: `http://localhost:8000/upload` or `http://party.local/upload`  
- **Health Check**: `http://localhost:8000/health`
- **API Statistics**: `http://localhost:8000/api/statistics`
- **Configuration**: `http://localhost:8000/api/config`

## Testing Requirements

### Port Configuration
- Tests expect Flask to run on **port 6000**
- Main deployment uses port 8000
- When testing, ensure backend runs on port 6000

### Critical Test Areas
- **Celebration Title**: Must be always visible with proper animation
- **File Upload**: Test photos, videos, and music uploads
- **WebSocket**: Real-time updates between display and upload interfaces  
- **Mobile UI**: Touch-friendly upload interface
- **Database**: SQLite operations and data persistence

### Test Data
- Use existing MCP Playwright for UI testing
- Login credentials when needed: kdresdell@gmail.com / admin123
- Test with various file types and sizes

## Party-Specific Configuration

The application is specifically configured for Valérie's 50th Birthday:
- **Celebration Title**: "Happy 50th Birthday Valérie!" (permanent display)
- **Party Theme**: Glamorous gold shimmer animations
- **File Limits**: 500MB max file size for high-quality memories
- **Network**: Configured for `party.local` hostname with mDNS
- **SSL**: Self-signed certificates for HTTPS access

## Development Workflow

1. **Code Changes**: Edit files in `backend/` or `frontend/` directories
2. **Testing**: Run relevant tests from `test/` directory  
3. **Local Testing**: Use development mode with Flask debug enabled
4. **Container Testing**: Use Docker compose for production-like environment
5. **Port Awareness**: Remember port differences between development (8000) and testing (6000)

## Directory Structure

```
party-wall/
├── backend/           # Flask application
│   ├── app.py         # Main Flask server
│   ├── database.py    # SQLite database operations
│   └── requirements.txt
├── frontend/          # Web interface files  
│   ├── index.html     # Slideshow display
│   ├── upload.html    # Mobile upload interface
│   ├── styles.css     # Hardware-accelerated CSS
│   ├── party-display.js  # Slideshow logic
│   └── party-upload.js   # Upload handling
├── test/             # Comprehensive test suite
├── media/            # Uploaded content storage
├── plan/             # Implementation documentation
├── nginx/            # NGINX configuration
└── docker-compose-party.yml  # Container orchestration
```