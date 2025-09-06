# Frontend Implementation Tasks

## Task 1: Slideshow Display with Celebration Title
**Agent**: flask-ui-developer
**File**: frontend/index.html
**Priority**: High

### Requirements:
- Full-screen Instagram Story layout
- **PERMANENT celebration title**: "Happy 50th Birthday Valérie!"
- Hardware-accelerated animations for Raspberry Pi 4B
- Photo/video display with Ken Burns effect
- Music player overlay
- QR code for sharing
- Guest attribution display
- Real-time WebSocket updates

### HTML Structure:
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Valérie's 50th Birthday Party Wall</title>
    <link href="https://fonts.googleapis.com/css2?family=Great+Vibes:wght@400&family=Bebas+Neue&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <!-- PERMANENT CELEBRATION TITLE -->
    <div class="celebration-header">
        <h1 class="celebration-title">
            <span class="sparkle">✨</span>
            Happy 50th Birthday Valérie!
            <span class="sparkle">✨</span>
        </h1>
    </div>

    <!-- SLIDESHOW CONTAINER -->
    <div class="slideshow-container" id="slideshow">
        <!-- Photos/videos inserted dynamically -->
    </div>

    <!-- MUSIC OVERLAY -->
    <div class="music-overlay" id="musicOverlay">
        <div class="now-playing">
            <h3 id="songTitle">No music playing</h3>
            <p id="artistName">Select a song to play</p>
            <div class="music-controls">
                <button id="prevBtn">⏮</button>
                <button id="playPauseBtn">⏸</button>
                <button id="nextBtn">⏭</button>
            </div>
        </div>
    </div>

    <!-- QR CODE OVERLAY -->
    <div class="qr-overlay">
        <div class="qr-content">
            <img id="qrCode" src="data:image/svg+xml;base64,..." alt="Share QR">
            <p>Share Now!</p>
            <p>party.local</p>
        </div>
    </div>

    <!-- ATTRIBUTION OVERLAY -->
    <div class="attribution-overlay" id="attribution">
        <span id="attributionText">📸 From: Loading...</span>
    </div>

    <!-- PROGRESS BAR -->
    <div class="progress-container">
        <div class="progress-bar" id="progressBar"></div>
        <div class="progress-text" id="progressText">15 seconds</div>
    </div>

    <!-- PREVIEW THUMBNAILS -->
    <div class="preview-container" id="previewContainer">
        <!-- Next 5 photos preview -->
    </div>

    <script src="party-display.js"></script>
</body>
</html>
```

### Key Features to Implement:
1. **Celebration title** - Always visible, animated
2. **Photo/video display** - Full screen with effects
3. **Music integration** - Background audio with controls
4. **Real-time updates** - WebSocket connection
5. **Attribution** - Guest name display
6. **Progress indication** - Time remaining per slide

### Playwright Tests: test/test_frontend.py
```python
from playwright.async_api import async_playwright

async def test_celebration_title_display():
    """Test permanent celebration title is visible"""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto('http://localhost:6000/')
        
        # Check title is present and visible
        title = await page.locator('.celebration-title').text_content()
        assert "Happy 50th Birthday Valérie!" in title
        
        # Check title is always on top
        z_index = await page.locator('.celebration-title').evaluate('el => getComputedStyle(el).zIndex')
        assert int(z_index) >= 9999

async def test_slideshow_functionality():
    """Test slideshow advances automatically"""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto('http://localhost:6000/')
        
        # Wait for slideshow to load
        await page.wait_for_selector('.slide.active')
        
        # Check if slides advance
        first_slide = await page.locator('.slide.active').get_attribute('data-index')
        await page.wait_for_timeout(16000)  # Wait for slide change
        second_slide = await page.locator('.slide.active').get_attribute('data-index')
        assert first_slide != second_slide

async def test_websocket_connection():
    """Test WebSocket updates work"""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        # Listen for console logs (WebSocket events)
        page.on('console', lambda msg: print(f"Console: {msg.text}"))
        
        await page.goto('http://localhost:6000/')
        await page.wait_for_timeout(2000)  # Allow connection
        
        # Check WebSocket connected (look for connection message)
```

## Task 2: Upload Interface
**Agent**: flask-ui-developer
**File**: frontend/upload.html
**Priority**: High

### Mobile-Optimized Upload Page:
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Share at Valérie's Party</title>
    <link href="https://fonts.googleapis.com/css2?family=Great+Vibes:wght@400&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="styles.css">
</head>
<body class="upload-page">
    <!-- CELEBRATION TITLE (smaller for mobile) -->
    <div class="celebration-header mobile">
        <h1 class="celebration-title mobile">
            ✨ Happy 50th Birthday Valérie! ✨
        </h1>
    </div>

    <div class="upload-container">
        <!-- UPLOAD AREA -->
        <div class="upload-area" id="uploadArea">
            <div class="upload-prompt">
                <div class="upload-icon">📸</div>
                <h2>Drop photos or videos here!</h2>
                <p>Or tap to select files</p>
                <input type="file" id="fileInput" accept="image/*,video/*,audio/*" multiple>
            </div>
            <div class="upload-progress" id="uploadProgress" style="display: none;">
                <div class="progress-bar">
                    <div class="progress-fill" id="progressFill"></div>
                </div>
                <p id="progressText">Uploading...</p>
            </div>
        </div>

        <!-- GUEST INFO FORM -->
        <form id="uploadForm" class="upload-form">
            <div class="form-group">
                <label for="guestName">Your name (optional):</label>
                <input type="text" id="guestName" name="guestName" placeholder="Enter your name">
            </div>

            <div class="form-group">
                <label for="songUrl">Add a song? 🎵</label>
                <input type="text" id="songUrl" name="songUrl" placeholder="Song name or Spotify URL">
            </div>

            <button type="submit" class="share-button" id="shareButton">
                Share It! 🎉
            </button>
        </form>

        <!-- SUCCESS MESSAGE -->
        <div class="success-message" id="successMessage" style="display: none;">
            <div class="success-icon">✅</div>
            <h3>Shared Successfully!</h3>
            <p>Your memory will appear on the big screen soon!</p>
            <button onclick="resetForm()" class="reset-button">Share Another</button>
        </div>
    </div>

    <script src="party-upload.js"></script>
</body>
</html>
```

### Upload Features:
1. **Drag and drop** - Files can be dropped anywhere
2. **Progress indication** - Upload progress with percentage
3. **Multiple files** - Support batch uploads
4. **Guest attribution** - Optional name input
5. **Music integration** - Song requests
6. **Success feedback** - Clear confirmation

### Playwright Tests: test/test_upload_interface.py
```python
async def test_upload_interface():
    """Test upload page loads and functions"""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto('http://localhost:6000/upload')
        
        # Check upload area exists
        upload_area = page.locator('#uploadArea')
        await expect(upload_area).to_be_visible()
        
        # Check celebration title on mobile
        mobile_title = page.locator('.celebration-title.mobile')
        await expect(mobile_title).to_be_visible()

async def test_file_upload_flow():
    """Test complete upload flow"""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto('http://localhost:6000/upload')
        
        # Fill guest name
        await page.fill('#guestName', 'Test User')
        
        # Upload file (simulate file selection)
        # Note: File upload testing may need special setup
        
        # Click share button
        await page.click('#shareButton')
        
        # Wait for success message
        await page.wait_for_selector('#successMessage', state='visible')
```

## Task 3: JavaScript Application Logic
**Agent**: flask-ui-developer
**File**: frontend/party-display.js
**Priority**: High

### Core Slideshow Logic:
```javascript
class PartyDisplay {
    constructor() {
        this.currentSlide = 0;
        this.slides = [];
        this.slideInterval = 15000; // 15 seconds
        this.slideshowTimer = null;
        this.websocket = null;
        this.musicPlayer = null;
        
        this.init();
    }

    async init() {
        await this.loadContent();
        this.setupWebSocket();
        this.startSlideshow();
        this.setupMusicPlayer();
        this.generateQRCode();
    }

    async loadContent() {
        try {
            const response = await fetch('/api/media');
            const data = await response.json();
            this.slides = data.media || [];
            await this.renderSlides();
        } catch (error) {
            console.error('Failed to load content:', error);
        }
    }

    async renderSlides() {
        const container = document.getElementById('slideshow');
        container.innerHTML = '';
        
        this.slides.forEach((slide, index) => {
            const slideEl = document.createElement('div');
            slideEl.className = 'slide';
            slideEl.setAttribute('data-index', index);
            
            if (index === 0) slideEl.classList.add('active');
            
            if (slide.type === 'photo') {
                slideEl.style.backgroundImage = `url(${slide.url})`;
                slideEl.classList.add('ken-burns-effect');
            } else if (slide.type === 'video') {
                const video = document.createElement('video');
                video.src = slide.url;
                video.autoplay = true;
                video.muted = false;
                video.loop = false;
                video.onended = () => this.nextSlide();
                slideEl.appendChild(video);
            }
            
            container.appendChild(slideEl);
        });
        
        this.updateAttribution();
        this.updatePreview();
    }

    nextSlide() {
        if (this.slides.length === 0) return;
        
        const currentSlideEl = document.querySelector('.slide.active');
        if (currentSlideEl) currentSlideEl.classList.remove('active');
        
        this.currentSlide = (this.currentSlide + 1) % this.slides.length;
        
        const nextSlideEl = document.querySelector(`[data-index="${this.currentSlide}"]`);
        if (nextSlideEl) nextSlideEl.classList.add('active');
        
        this.updateAttribution();
        this.updateProgress();
    }

    startSlideshow() {
        this.slideshowTimer = setInterval(() => {
            this.nextSlide();
        }, this.slideInterval);
    }

    setupWebSocket() {
        this.websocket = new WebSocket(`ws://${window.location.host}/ws`);
        
        this.websocket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            
            switch (data.type) {
                case 'new_upload':
                    this.handleNewUpload(data.data);
                    break;
                case 'music_update':
                    this.updateMusic(data.data);
                    break;
                case 'slideshow_update':
                    // Handle manual slideshow controls
                    break;
            }
        };
        
        this.websocket.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
    }

    updateAttribution() {
        const currentSlide = this.slides[this.currentSlide];
        if (currentSlide) {
            const attribution = document.getElementById('attributionText');
            const icon = currentSlide.type === 'video' ? '📹' : '📸';
            attribution.textContent = `${icon} From: ${currentSlide.guest_name || 'Anonymous'}`;
        }
    }

    generateQRCode() {
        // Generate QR code for party.local/upload
        // Use a QR code library or API
        const qrCodeElement = document.getElementById('qrCode');
        qrCodeElement.src = `https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=http://party.local/upload`;
    }
}

// Initialize when DOM loaded
document.addEventListener('DOMContentLoaded', () => {
    new PartyDisplay();
});
```

### Upload JavaScript (party-upload.js):
```javascript
class PartyUpload {
    constructor() {
        this.uploadArea = document.getElementById('uploadArea');
        this.fileInput = document.getElementById('fileInput');
        this.uploadForm = document.getElementById('uploadForm');
        
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Drag and drop
        this.uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            this.uploadArea.classList.add('drag-over');
        });
        
        this.uploadArea.addEventListener('dragleave', () => {
            this.uploadArea.classList.remove('drag-over');
        });
        
        this.uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            this.uploadArea.classList.remove('drag-over');
            const files = Array.from(e.dataTransfer.files);
            this.handleFiles(files);
        });
        
        // Click to select
        this.uploadArea.addEventListener('click', () => {
            this.fileInput.click();
        });
        
        this.fileInput.addEventListener('change', (e) => {
            const files = Array.from(e.target.files);
            this.handleFiles(files);
        });
        
        // Form submission
        this.uploadForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.uploadFiles();
        });
    }

    handleFiles(files) {
        // Validate files and show preview
        const validFiles = files.filter(file => this.validateFile(file));
        if (validFiles.length > 0) {
            this.showPreview(validFiles);
        }
    }

    validateFile(file) {
        const maxSize = 500 * 1024 * 1024; // 500MB
        if (file.size > maxSize) {
            alert('File too large. Maximum size is 500MB.');
            return false;
        }
        
        const allowedTypes = ['image/', 'video/', 'audio/'];
        if (!allowedTypes.some(type => file.type.startsWith(type))) {
            alert('Invalid file type. Please upload photos, videos, or music.');
            return false;
        }
        
        return true;
    }

    async uploadFiles() {
        const formData = new FormData();
        const files = this.fileInput.files;
        
        Array.from(files).forEach(file => {
            formData.append('files', file);
        });
        
        formData.append('guest_name', document.getElementById('guestName').value);
        formData.append('song_url', document.getElementById('songUrl').value);
        
        try {
            this.showProgress(true);
            
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });
            
            if (response.ok) {
                this.showSuccess();
            } else {
                throw new Error('Upload failed');
            }
        } catch (error) {
            this.showError(error.message);
        } finally {
            this.showProgress(false);
        }
    }

    showSuccess() {
        document.getElementById('successMessage').style.display = 'block';
        document.querySelector('.upload-container').style.display = 'none';
    }
}

// Initialize upload page
document.addEventListener('DOMContentLoaded', () => {
    new PartyUpload();
});
```

## Task 4: CSS Styling
**Agent**: flask-ui-developer
**File**: frontend/styles.css
**Priority**: High

### Key CSS Requirements:
1. **Hardware acceleration** - Use `transform` and `opacity` only
2. **Celebration title** - Always visible, animated
3. **Responsive design** - Mobile and desktop
4. **Smooth transitions** - Optimized for Raspberry Pi
5. **Party theme** - Gold, elegant, festive

### Critical Animations for RPi:
```css
/* CELEBRATION TITLE - PERMANENT */
.celebration-title {
    position: fixed;
    top: 20px;
    width: 100%;
    text-align: center;
    font-family: 'Great Vibes', 'Dancing Script', cursive;
    font-size: clamp(36px, 4vw, 72px);
    background: linear-gradient(90deg, #FFD700 0%, #FFFFFF 25%, #FFD700 50%, #FFFFFF 75%, #FFD700 100%);
    background-size: 200% 100%;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: shimmer 4s linear infinite;
    z-index: 9999;
    letter-spacing: 2px;
}

/* GPU-ACCELERATED ANIMATIONS ONLY */
@keyframes shimmer {
    0% { background-position: -200% 0; }
    100% { background-position: 200% 0; }
}

.slide {
    position: absolute;
    width: 100%;
    height: 100%;
    opacity: 0;
    transition: opacity 0.8s ease-in-out;
    transform: translateZ(0); /* Force GPU layer */
}

.slide.active {
    opacity: 1;
}

.ken-burns-effect {
    animation: kenBurns 15s linear infinite;
    background-size: 110% 110%;
}

@keyframes kenBurns {
    0% { transform: scale(1) translateZ(0); }
    100% { transform: scale(1.1) translateZ(0); }
}
```

## Critical Testing Requirements:

1. **Flask runs on port 6000** - Mandatory for all tests
2. **Use MCP Playwright** - No new installations
3. **Test celebration title** - Always visible and animated
4. **Test both photo/video** - Full media support
5. **Test mobile interface** - Touch-friendly upload
6. **Test WebSocket updates** - Real-time functionality
7. **Performance on RPi** - Smooth 60fps animations

## Hardware Optimization Notes:

- Use only `transform` and `opacity` for animations
- Avoid `width`, `height`, `left`, `top` changes
- Enable GPU acceleration with `translateZ(0)`
- Limit simultaneous animations
- Preload next media items
- Optimize image sizes for display resolution