# 🎉 Party Memory Wall - Valérie's 50th Birthday Celebration

A complete party photo/music sharing application with real-time slideshow display, optimized for Raspberry Pi deployment.

## 🎂 Project Overview

**Celebration**: Valérie's 50th Birthday  
**Features**: Photo/video uploads, music queue, real-time slideshow, QR code sharing  
**Platform**: Raspberry Pi 4B optimized with Docker deployment  
**Frontend**: Instagram Story layout with permanent celebration title  
**Backend**: Flask + SQLite + WebSocket for real-time updates  


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
