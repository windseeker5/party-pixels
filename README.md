# 🎉 Party Memory Wall - Valérie's 50th Birthday Celebration

A complete party photo/music sharing application with real-time slideshow display, optimized for Raspberry Pi deployment.

## 🎂 Project Overview

**Celebration**: Valérie's 50th Birthday  
**Features**: Photo/video uploads, music queue, real-time slideshow, QR code sharing  
**Platform**: Raspberry Pi 4B optimized with Docker deployment  
**Frontend**: Instagram Story layout with permanent celebration title  
**Backend**: Flask + SQLite + WebSocket for real-time updates  

## 📁 Project Structure

```
party-wall/
├── 📋 plan/                    # Complete implementation plans
│   ├── README.md              # Master plan with wireframes
│   ├── backend-tasks.md       # Backend implementation guide
│   ├── frontend-tasks.md      # Frontend implementation guide
│   ├── testing-strategy.md    # Testing instructions for agents
│   └── wireframe.md           # UI design specifications
├── 🧪 test/                   # Comprehensive test suite
│   ├── test_upload_api.py     # Flask API testing
│   ├── test_frontend.py       # Playwright UI testing
│   ├── test_database.py       # SQLite database testing
│   ├── test_websocket.py      # WebSocket testing
│   └── test_integration.py    # End-to-end testing
├── ⚙️ backend/                # Flask application
│   ├── app.py                 # Main Flask app (port 6000)
│   ├── database.py            # SQLite database operations
│   ├── requirements.txt       # Python dependencies
│   └── Dockerfile            # Backend container
├── 🎨 frontend/               # Web interface
│   ├── index.html             # Slideshow display
│   ├── upload.html            # Mobile upload interface
│   ├── styles.css             # Hardware-accelerated CSS
│   ├── party-display.js       # Slideshow logic
│   └── party-upload.js        # Upload handling
├── 🐳 Docker Configuration
│   ├── docker-compose-party.yml  # Container orchestration
│   ├── nginx/party.conf          # NGINX proxy config
│   └── start-party.sh            # Startup script
└── 🎵 media/                  # Uploaded content storage
    ├── photos/                # Guest photos
    ├── videos/                # Guest videos
    └── music/                 # Music queue
```

## 🚀 Quick Start

### Option 1: Docker Deployment (Recommended for Pi)

```bash
# Start the complete party system
./start-party.sh

# Follow logs
./start-party.sh --logs
```

### Option 2: Development Mode

```bash
# Backend (Terminal 1)
cd backend
python3 -m venv venv
source venv/bin/activate
pip install flask flask-cors flask-socketio pillow
python app.py

# Frontend served by Flask at http://localhost:6000
```

## 🌐 Access Points

- **📱 Upload Interface**: `http://localhost:6000/upload` or `http://party.local/upload`
- **📺 Big Screen Display**: `http://localhost:6000/` or `http://party.local/`
- **🔧 API Health**: `http://localhost:6000/health`
- **📊 Statistics**: `http://localhost:6000/api/statistics`

## 🎯 Key Features

### 🎂 Permanent Celebration Title
- **"Happy 50th Birthday Valérie!"** always visible
- Glamorous gold shimmer animation
- Hardware-accelerated for smooth performance

### 📸 Media Upload & Display
- **Photos**: JPG, PNG, HEIC (Ken Burns effect)
- **Videos**: MP4, MOV, WebM (full duration playback)
- **Music**: MP3, M4A, WAV (background queue)
- **Max Size**: 500MB per file

### 🎵 Real-time Features
- WebSocket updates across all devices
- Live slideshow with guest attribution
- Music queue with play controls
- QR code sharing for easy access

### 📱 Mobile Optimized
- Touch-friendly upload interface
- Drag & drop support
- Progress indicators
- Guest name attribution

## 🧪 Testing

### Run All Tests
```bash
# Install test dependencies
pip install pytest playwright websockets

# Run complete test suite
python -m pytest test/ -v

# Run specific test categories
python -m pytest test/test_upload_api.py -v     # API tests
python -m pytest test/test_frontend.py -v      # UI tests
python -m pytest test/test_database.py -v      # Database tests
```

### Critical Testing Requirements
- **Flask MUST run on port 6000** for all tests
- **Use existing MCP Playwright** (no new installation)
- **Test celebration title** is always visible
- **Test both photos AND videos**

### Basic Validation
```bash
# Quick functionality check
python3 test_basic.py
```

## 🏗️ Architecture

### Backend (Flask + SQLite)
- **Port**: 6000 (critical for testing)
- **Database**: SQLite with automatic schema creation
- **WebSocket**: Real-time updates via Flask-SocketIO
- **File Processing**: Upload handling with type validation
- **API**: RESTful endpoints for media and configuration

### Frontend (Vanilla JS + CSS)
- **Layout**: Instagram Story full-screen design
- **Animations**: Hardware-accelerated (transform/opacity only)
- **WebSocket**: Live updates for new uploads
- **Responsive**: Mobile-first design with touch support

### Docker Deployment
- **party-flask**: Backend application container
- **party-nginx**: Reverse proxy and static file serving
- **Volumes**: Persistent storage for media and database

## 🔧 Configuration

### Party Settings (Customizable)
```python
PARTY_CONFIG = {
    'title': "Happy 50th Birthday Valérie!",
    'slideshow_duration': 15,  # seconds per photo
    'max_file_size': 500 * 1024 * 1024,  # 500MB
    'weekend_days': 2
}
```

### Network Configuration
- **mDNS**: `party.local` hostname
- **CORS**: Enabled for local network access
- **SSL**: Self-signed certificate for HTTPS

## 📊 Performance

### Raspberry Pi 4B Optimizations
- **GPU-accelerated CSS**: Only transform/opacity animations
- **Efficient WebSockets**: Minimal bandwidth usage
- **Compressed assets**: Gzip compression enabled
- **Optimized images**: Hardware-accelerated rendering

### Expected Performance
- **100+ concurrent users** supported
- **5GB+ media storage** capacity
- **48+ hours** continuous operation
- **<2 second** upload processing

## 🎊 Party Day Checklist

### Pre-Party Setup
- [ ] Deploy to Raspberry Pi: `./start-party.sh`
- [ ] Connect Pi to party WiFi network
- [ ] Display QR code on big screen
- [ ] Test upload from mobile devices
- [ ] Verify slideshow displays correctly

### During Party
- [ ] Monitor upload queue: `http://localhost:6000/api/statistics`
- [ ] Check container health: `docker-compose -f docker-compose-party.yml ps`
- [ ] Manage music queue if needed
- [ ] Ensure big screen displays celebration title

### Post-Party
- [ ] Download all photos: `docker cp party-memory-wall:/app/media ./party-memories`
- [ ] Generate memory compilation
- [ ] Share with guests via Jellyfin or direct download

## 🛠️ Development

### Adding New Features
1. Update plan documents in `plan/`
2. Implement backend changes in `backend/`
3. Update frontend in `frontend/`
4. Add tests in `test/`
5. Update Docker configuration if needed

### Testing New Features
```bash
# Test backend changes
python -m pytest test/test_upload_api.py -v

# Test frontend changes
python -m pytest test/test_frontend.py -v

# Test integration
python -m pytest test/test_integration.py -v
```

## 🔍 Troubleshooting

### Common Issues

**Flask not starting on port 6000:**
```bash
# Check if port is in use
lsof -i :6000
# Kill existing process if needed
pkill -f "python.*app.py"
```

**Frontend not loading:**
```bash
# Check if Flask is serving static files
curl http://localhost:6000/
# Check backend health
curl http://localhost:6000/health
```

**WebSocket connection failed:**
```bash
# Check WebSocket endpoint
curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" -H "Sec-WebSocket-Version: 13" -H "Sec-WebSocket-Key: test" http://localhost:6000/socket.io/
```

**Database errors:**
```bash
# Check database file permissions
ls -la database/
# Reset database (removes all data)
rm database/party.db && python backend/database.py
```

### Debug Mode
```bash
# Enable Flask debug mode
export FLASK_ENV=development
cd backend && python app.py

# View container logs
docker-compose -f docker-compose-party.yml logs -f
```

## 📚 Documentation

- **Complete Plan**: `plan/README.md`
- **Backend API**: `plan/backend-tasks.md`
- **Frontend UI**: `plan/frontend-tasks.md`
- **Testing Guide**: `plan/testing-strategy.md`
- **Wireframes**: `plan/wireframe.md`

## 🎁 Credits

Built with ❤️ for Valérie's 50th Birthday celebration using:
- **Flask** + **SQLite** for backend
- **Vanilla JavaScript** + **CSS3** for frontend  
- **Docker** + **NGINX** for deployment
- **Raspberry Pi** optimization
- **WebSocket** real-time updates

---

## 🎂 Happy 50th Birthday Valérie! 🎉

*May your special day be filled with wonderful memories shared by friends and family!*