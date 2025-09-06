/**
 * Party Memory Wall Display
 * Main slideshow application for Valérie's 50th Birthday
 * Optimized for Raspberry Pi 4B hardware acceleration
 */

class PartyDisplay {
    constructor() {
        this.currentSlide = 0;
        this.slides = [];
        this.slideInterval = 15000; // 15 seconds
        this.slideshowTimer = null;
        this.progressTimer = null;
        this.websocket = null;
        this.musicPlayer = null;
        this.musicQueueData = [];
        this.currentMusic = null;
        this.isPlaying = false;
        this.connectionRetryCount = 0;
        this.maxRetries = 5;
        
        // DOM elements
        this.slideshow = null;
        this.photoQueue = null;
        this.musicQueue = null;
        this.progressBar = null;
        this.progressText = null;
        this.previewContainer = null;
        this.audioPlayer = null;
        this.connectionStatus = null;
        
        // Initialize when DOM is ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.init());
        } else {
            this.init();
        }
    }

    async init() {
        console.log('🎉 Initializing Party Memory Wall Display');
        
        // Get DOM elements
        this.slideshow = document.getElementById('slideshow');
        this.photoQueue = document.getElementById('photoQueue');
        this.musicQueue = document.getElementById('musicQueue');
        this.progressBar = document.getElementById('progressBar');
        this.progressText = document.getElementById('progressText');
        this.previewContainer = document.getElementById('previewContainer');
        this.audioPlayer = document.getElementById('audioPlayer');
        this.connectionStatus = document.getElementById('connectionStatus');
        
        // Verify essential elements exist
        if (!this.slideshow) {
            console.error('❌ Slideshow container not found');
            return;
        }
        
        try {
            // Initialize all components
            await this.loadContent();
            // Enable WebSocket connection for real-time updates
            this.setupWebSocket();
            this.setupMusicPlayer();
            this.setupProgressBar();
            this.generateQRCode();
            // Don't start slideshow immediately - wait for content to load
            
            console.log('✅ Party Memory Wall Display initialized successfully');
        } catch (error) {
            console.error('❌ Failed to initialize Party Display:', error);
            this.showError('Failed to initialize slideshow');
        }
    }

    async loadContent() {
        console.log('📡 Loading media content...');
        
        try {
            const response = await fetch('/api/media');
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            this.slides = data.media || [];
            
            console.log(`📷 Loaded ${this.slides.length} media items`);
            
            // Always ensure we have at least the welcome slide
            if (this.slides.length === 0) {
                console.log('💡 No media found, keeping welcome slide');
                return;
            }
            
            await this.renderSlides();
            
            // Start slideshow after content is loaded
            if (this.slides.length > 0) {
                console.log('🎬 Starting slideshow with', this.slides.length, 'slides');
                console.log('🔍 First slide data:', this.slides[0]);
                
                // Start with the first uploaded photo (skip welcome slide)
                this.currentSlide = 1; // Welcome is 0, first photo is 1
                this.showSlide(1); // Show first uploaded photo
                
                // Start slideshow with a small delay to ensure DOM is ready
                setTimeout(() => {
                    this.startSlideshow();
                }, 500);
            } else {
                console.log('📺 No media loaded, showing welcome slide only');
                this.showSlide(0); // Show welcome slide
            }
            
        } catch (error) {
            console.error('❌ Failed to load content:', error);
            // Keep welcome slide as fallback
            console.log('🔄 Keeping welcome slide as fallback');
            this.showSlide(0);
        }
    }

    async renderSlides() {
        console.log('🎨 Rendering slides...');
        
        if (!this.slideshow) return;
        
        // Clear existing slides except welcome slide
        const existingSlides = this.slideshow.querySelectorAll('.slide:not(#welcomeSlide)');
        existingSlides.forEach(slide => slide.remove());
        
        // Add new slides
        this.slides.forEach((slide, index) => {
            const slideEl = this.createSlideElement(slide, index + 1); // +1 to account for welcome slide
            this.slideshow.appendChild(slideEl);
        });
        
        // Update displays
        this.updatePhotoQueue();
        this.updateMusicQueueDisplay();
        
        console.log(`✅ Rendered ${this.slides.length} slides`);
    }

    createSlideElement(slide, index) {
        const slideEl = document.createElement('div');
        slideEl.className = 'slide';
        slideEl.setAttribute('data-index', index);
        slideEl.setAttribute('data-upload-id', slide.upload_id);
        
        // Handle different media types
        if (slide.file_type === 'photo') {
            slideEl.style.backgroundImage = `url(${slide.url})`;
            slideEl.classList.add('ken-burns-effect');
        } else if (slide.file_type === 'video') {
            const video = document.createElement('video');
            video.src = slide.url;
            video.autoplay = false; // Will be enabled when slide becomes active
            video.muted = false;
            video.loop = false;
            video.preload = 'metadata';
            
            // Handle video end - advance to next slide
            video.addEventListener('ended', () => {
                console.log('📹 Video ended, advancing to next slide');
                this.nextSlide();
            });
            
            // Handle video load
            video.addEventListener('loadeddata', () => {
                console.log('📹 Video loaded:', slide.url);
            });
            
            slideEl.appendChild(video);
        }
        
        // Add slide metadata
        slideEl.dataset.guestName = slide.guest_name || 'Anonymous';
        slideEl.dataset.fileType = slide.file_type;
        slideEl.dataset.timestamp = slide.timestamp;
        
        console.log(`🏷️ Created slide for: ${slide.guest_name} (${slide.file_type})`);
        console.log(`📄 Slide dataset:`, slideEl.dataset);
        
        return slideEl;
    }

    nextSlide() {
        const totalSlides = this.slideshow.querySelectorAll('.slide').length;
        const uploadedSlidesCount = this.slides.length; // Actual uploaded content
        console.log(`⏭️ Next slide - Total slides: ${totalSlides}, Uploaded: ${uploadedSlidesCount}, Current: ${this.currentSlide}`);
        
        if (uploadedSlidesCount === 0) {
            console.log('⚠️ No uploaded slides to show');
            return; // Only welcome slide
        }
        
        // Stop current video if playing
        const currentSlideEl = this.slideshow.querySelector('.slide.active');
        if (currentSlideEl) {
            const video = currentSlideEl.querySelector('video');
            if (video) {
                video.pause();
                video.currentTime = 0;
            }
            currentSlideEl.classList.remove('active');
        }
        
        // Calculate next slide index (only cycle through uploaded content, skip welcome slide)
        if (this.currentSlide >= uploadedSlidesCount) {
            this.currentSlide = 1; // Loop back to first uploaded slide
        } else {
            this.currentSlide++;
        }
        
        // Ensure we stay within uploaded slides range
        if (this.currentSlide < 1 || this.currentSlide > uploadedSlidesCount) {
            this.currentSlide = 1;
        }
        
        console.log(`📄 Advancing to slide ${this.currentSlide} of ${uploadedSlidesCount} uploaded slides`);
        
        // Activate next slide
        const nextSlideEl = this.slideshow.querySelector(`[data-index="${this.currentSlide}"]`);
        if (nextSlideEl) {
            nextSlideEl.classList.add('active');
            
            // Start video if this is a video slide
            const video = nextSlideEl.querySelector('video');
            if (video) {
                video.currentTime = 0;
                video.play().catch(error => {
                    console.warn('⚠️ Failed to play video:', error);
                });
            }
        } else {
            console.error(`❌ Could not find slide with data-index="${this.currentSlide}"`);
        }
        
        this.updatePhotoQueue();
        this.restartProgressBar();
        
        console.log(`📄 Advanced to slide ${this.currentSlide} of ${uploadedSlidesCount} uploaded slides`);
    }

    previousSlide() {
        const totalSlides = this.slideshow.querySelectorAll('.slide').length;
        if (totalSlides <= 1) return;
        
        // Stop current video
        const currentSlideEl = this.slideshow.querySelector('.slide.active');
        if (currentSlideEl) {
            const video = currentSlideEl.querySelector('video');
            if (video) {
                video.pause();
                video.currentTime = 0;
            }
            currentSlideEl.classList.remove('active');
        }
        
        // Calculate previous slide index
        this.currentSlide = this.currentSlide <= 0 ? totalSlides - 1 : this.currentSlide - 1;
        
        // Activate previous slide
        const prevSlideEl = this.slideshow.querySelector(`[data-index="${this.currentSlide}"], #welcomeSlide`);
        if (prevSlideEl) {
            prevSlideEl.classList.add('active');
            
            // Start video if needed
            const video = prevSlideEl.querySelector('video');
            if (video) {
                video.currentTime = 0;
                video.play().catch(error => {
                    console.warn('⚠️ Failed to play video:', error);
                });
            }
        }
        
        this.updatePhotoQueue();
        this.restartProgressBar();
    }

    showSlide(slideIndex) {
        console.log(`🎯 Showing slide ${slideIndex}`);
        
        const allSlides = this.slideshow.querySelectorAll('.slide');
        console.log(`📊 Total slides found: ${allSlides.length}`);
        
        if (slideIndex >= allSlides.length) {
            console.error(`❌ Slide index ${slideIndex} out of range (max: ${allSlides.length - 1})`);
            return;
        }
        
        // Remove active class from all slides
        allSlides.forEach(slide => {
            slide.classList.remove('active');
            const video = slide.querySelector('video');
            if (video) {
                video.pause();
                video.currentTime = 0;
            }
        });
        
        // Activate target slide
        const targetSlide = allSlides[slideIndex];
        if (targetSlide) {
            this.currentSlide = slideIndex;
            targetSlide.classList.add('active');
            
            // Start video if this is a video slide
            const video = targetSlide.querySelector('video');
            if (video) {
                video.currentTime = 0;
                video.play().catch(error => {
                    console.warn('⚠️ Failed to play video:', error);
                });
            }
            
            this.updatePhotoQueue();
        }
    }

    startSlideshow() {
        console.log('▶️ Starting slideshow timer');
        
        this.stopSlideshow(); // Clear any existing timer
        
        this.slideshowTimer = setInterval(() => {
            this.nextSlide();
        }, this.slideInterval);
        
        this.restartProgressBar();
    }

    stopSlideshow() {
        if (this.slideshowTimer) {
            clearInterval(this.slideshowTimer);
            this.slideshowTimer = null;
        }
        
        if (this.progressTimer) {
            clearInterval(this.progressTimer);
            this.progressTimer = null;
        }
    }

    setupProgressBar() {
        if (!this.progressBar || !this.progressText) return;
        
        this.restartProgressBar();
    }

    restartProgressBar() {
        // Clear existing progress timer
        if (this.progressTimer) {
            clearInterval(this.progressTimer);
        }
        
        let timeLeft = this.slideInterval / 1000; // Convert to seconds
        
        if (this.progressText) {
            this.progressText.textContent = `${timeLeft} seconds`;
        }
        
        // Update progress bar animation
        if (this.progressBar) {
            const progressFill = this.progressBar.querySelector('::after') || this.progressBar;
            progressFill.style.animation = 'none';
            // Force reflow
            progressFill.offsetHeight;
            progressFill.style.animation = `progressFill ${this.slideInterval}ms linear`;
        }
        
        // Update text countdown
        this.progressTimer = setInterval(() => {
            timeLeft--;
            if (this.progressText) {
                this.progressText.textContent = `${timeLeft} seconds`;
            }
            
            if (timeLeft <= 0) {
                clearInterval(this.progressTimer);
                this.progressTimer = null;
            }
        }, 1000);
    }

    setupWebSocket() {
        console.log('🔌 Setting up SocketIO connection...');
        
        try {
            // Use SocketIO instead of plain WebSocket
            this.websocket = io();
            
            this.websocket.on('connect', () => {
                console.log('✅ SocketIO connected');
                this.connectionRetryCount = 0;
                this.updateConnectionStatus('connected', 'Connected');
            });
            
            this.websocket.on('new_upload', (data) => {
                console.log('📨 New upload received:', data);
                this.handleNewUpload(data.data);
            });
            
            this.websocket.on('music_update', (data) => {
                console.log('🎵 Music update received:', data);
                this.updateMusicQueue(data.data);
            });
            
            this.websocket.on('slideshow_update', (data) => {
                console.log('🎬 Slideshow update received:', data);
                this.handleSlideshowUpdate(data.data);
            });
            
            this.websocket.on('disconnect', () => {
                console.log('🔌 SocketIO disconnected');
                this.updateConnectionStatus('disconnected', 'Disconnected');
                this.scheduleWebSocketReconnect();
            });
            
            this.websocket.on('connect_error', (error) => {
                console.error('❌ SocketIO error:', error);
                this.updateConnectionStatus('disconnected', 'Connection Error');
            });
            
        } catch (error) {
            console.error('❌ Failed to create WebSocket:', error);
            this.updateConnectionStatus('disconnected', 'Failed to Connect');
        }
    }

    scheduleWebSocketReconnect() {
        if (this.connectionRetryCount >= this.maxRetries) {
            console.log('❌ Max WebSocket reconnection attempts reached');
            return;
        }
        
        this.connectionRetryCount++;
        const delay = Math.min(1000 * Math.pow(2, this.connectionRetryCount), 30000);
        
        console.log(`🔄 Reconnecting WebSocket in ${delay}ms (attempt ${this.connectionRetryCount})`);
        
        setTimeout(() => {
            this.setupWebSocket();
        }, delay);
    }

    handleWebSocketMessage(data) {
        console.log('📨 WebSocket message:', data.type);
        
        switch (data.type) {
            case 'new_upload':
                this.handleNewUpload(data.data);
                break;
            case 'music_update':
                this.updateMusicQueue(data.data);
                break;
            case 'slideshow_update':
                this.handleSlideshowUpdate(data.data);
                break;
            case 'connected':
                console.log('🎉 Connected to Party Memory Wall');
                break;
            case 'pong':
                // Keep-alive response
                break;
            default:
                console.log('❓ Unknown WebSocket message type:', data.type);
        }
    }

    async handleNewUpload(uploadData) {
        console.log('🆕 New upload received:', uploadData.guest_name, uploadData.file_type);
        
        try {
            // Reload content to include new upload
            await this.loadContent();
            
            // Show notification (you could add a toast notification here)
            console.log('✅ Content reloaded with new upload');
            
        } catch (error) {
            console.error('❌ Failed to handle new upload:', error);
        }
    }

    updateMusicQueue(musicData) {
        console.log('🎵 Music queue updated:', musicData);
        
        if (musicData.new_song) {
            // Update now playing display
            const songTitle = document.getElementById('songTitle');
            const artistName = document.getElementById('artistName');
            
            if (songTitle) {
                songTitle.textContent = musicData.new_song.title || 'New song added';
            }
            
            if (artistName) {
                artistName.textContent = `by ${musicData.new_song.guest_name || 'Anonymous'}`;
            }
        }
    }

    handleSlideshowUpdate(updateData) {
        console.log('🎬 Slideshow update:', updateData.action);
        
        switch (updateData.action) {
            case 'next':
                this.nextSlide();
                break;
            case 'previous':
                this.previousSlide();
                break;
            case 'pause':
                this.stopSlideshow();
                break;
            case 'play':
                this.startSlideshow();
                break;
        }
    }

    setupMusicPlayer() {
        console.log('🎵 Setting up music player...');
        
        const playPauseBtn = document.getElementById('playPauseBtn');
        const prevBtn = document.getElementById('prevBtn');
        const nextBtn = document.getElementById('nextBtn');
        const volumeBtn = document.getElementById('volumeBtn');
        const volumeSlider = document.getElementById('volumeSlider');
        const volumeRange = document.getElementById('volumeRange');
        
        // Play/Pause button
        if (playPauseBtn) {
            playPauseBtn.addEventListener('click', () => {
                this.toggleMusic();
            });
        }
        
        // Previous/Next buttons
        if (prevBtn) {
            prevBtn.addEventListener('click', () => {
                this.previousMusic();
            });
        }
        
        if (nextBtn) {
            nextBtn.addEventListener('click', () => {
                this.nextMusic();
            });
        }
        
        // Volume controls
        if (volumeBtn && volumeSlider) {
            volumeBtn.addEventListener('click', () => {
                volumeSlider.style.display = volumeSlider.style.display === 'none' ? 'block' : 'none';
            });
        }
        
        if (volumeRange && this.audioPlayer) {
            volumeRange.addEventListener('input', (e) => {
                const volume = e.target.value / 100;
                this.audioPlayer.volume = volume;
                console.log('🔊 Volume set to:', Math.round(volume * 100) + '%');
            });
            
            // Set initial volume
            this.audioPlayer.volume = 0.7;
            volumeRange.value = 70;
        }
        
        // Load initial music queue
        this.loadMusicQueue();
    }

    async loadMusicQueue() {
        try {
            const response = await fetch('/api/music/queue');
            if (response.ok) {
                const queueData = await response.json();
                this.musicQueueData = queueData.queue || [];
                console.log(`🎵 Loaded ${this.musicQueueData.length} songs in queue`);
                
                if (this.musicQueueData.length > 0 && !this.currentMusic) {
                    this.playNextMusic();
                }
            }
        } catch (error) {
            console.error('❌ Failed to load music queue:', error);
        }
    }

    toggleMusic() {
        if (!this.audioPlayer) return;
        
        if (this.isPlaying) {
            this.audioPlayer.pause();
            this.isPlaying = false;
            document.getElementById('playPauseBtn').textContent = '▶';
            console.log('⏸️ Music paused');
        } else {
            this.audioPlayer.play().catch(error => {
                console.error('❌ Failed to play music:', error);
            });
            this.isPlaying = true;
            document.getElementById('playPauseBtn').textContent = '⏸';
            console.log('▶️ Music playing');
        }
    }

    previousMusic() {
        // TODO: Implement previous track functionality
        console.log('⏮️ Previous music (not implemented)');
    }

    nextMusic() {
        this.playNextMusic();
    }

    async playNextMusic() {
        if (this.musicQueueData.length === 0) {
            await this.loadMusicQueue();
            if (this.musicQueueData.length === 0) {
                console.log('🎵 No music in queue');
                return;
            }
        }
        
        const nextSong = this.musicQueueData.shift(); // Remove from queue
        this.currentMusic = nextSong;
        
        if (this.audioPlayer && nextSong) {
            this.audioPlayer.src = `/media/music/${nextSong.filename}`;
            this.audioPlayer.play().catch(error => {
                console.error('❌ Failed to play music:', error);
            });
            
            this.isPlaying = true;
            document.getElementById('playPauseBtn').textContent = '⏸';
            
            // Update display
            document.getElementById('songTitle').textContent = nextSong.song_title || nextSong.original_filename;
            document.getElementById('artistName').textContent = nextSong.artist || nextSong.guest_name || 'Unknown Artist';
            
            console.log('🎵 Now playing:', nextSong.song_title);
        }
        
        // Auto-advance when song ends
        if (this.audioPlayer) {
            this.audioPlayer.addEventListener('ended', () => {
                console.log('🎵 Song ended, playing next');
                this.playNextMusic();
            });
        }
    }

    updatePhotoQueue() {
        console.log('📸 Updating photo queue...');
        
        if (!this.photoQueue) {
            console.warn('⚠️ Photo queue element not found');
            return;
        }
        
        // Clear existing queue items
        this.photoQueue.innerHTML = '';
        
        if (this.slides.length === 0) {
            console.log('📸 No photos to show in queue');
            return;
        }
        
        // Get next 6-8 photos starting from current slide
        const queueItems = [];
        const totalSlides = this.slides.length;
        
        for (let i = 0; i < Math.min(8, totalSlides); i++) {
            const slideIndex = (this.currentSlide - 1 + i) % totalSlides;
            if (slideIndex >= 0) {
                queueItems.push({
                    slide: this.slides[slideIndex],
                    isCurrent: i === 0
                });
            }
        }
        
        // Create queue item elements
        queueItems.forEach(({slide, isCurrent}) => {
            const queueItem = document.createElement('div');
            queueItem.className = `photo-queue-item${isCurrent ? ' current' : ''}`;
            
            // Create thumbnail
            const thumbnail = document.createElement('div');
            thumbnail.className = 'photo-queue-thumbnail';
            if (slide.file_type === 'photo') {
                thumbnail.style.backgroundImage = `url(${slide.url})`;
            } else {
                thumbnail.textContent = '📹';
                thumbnail.style.backgroundColor = 'rgba(255, 215, 0, 0.3)';
            }
            
            // Create info section
            const info = document.createElement('div');
            info.className = 'photo-queue-info';
            
            const submitter = document.createElement('div');
            submitter.className = 'photo-queue-submitter';
            submitter.textContent = slide.guest_name || 'Anonymous';
            
            info.appendChild(submitter);
            queueItem.appendChild(thumbnail);
            queueItem.appendChild(info);
            this.photoQueue.appendChild(queueItem);
        });
        
        console.log(`✅ Photo queue updated with ${queueItems.length} items`);
    }

    updateMusicQueueDisplay() {
        console.log('🎵 Updating music queue display...');
        
        if (!this.musicQueue) {
            console.warn('⚠️ Music queue element not found');
            return;
        }
        
        // Clear existing queue items
        this.musicQueue.innerHTML = '';
        
        if (this.musicQueueData.length === 0) {
            const noMusic = document.createElement('div');
            noMusic.className = 'music-queue-item';
            noMusic.innerHTML = `
                <div class="music-queue-title">No music in queue</div>
                <div class="music-queue-submitter">Add songs via upload</div>
            `;
            this.musicQueue.appendChild(noMusic);
            return;
        }
        
        // Show upcoming music (first 6-8 items)
        const upcomingMusic = this.musicQueueData.slice(0, 8);
        
        upcomingMusic.forEach((song, index) => {
            const queueItem = document.createElement('div');
            queueItem.className = `music-queue-item${index === 0 ? ' current' : ''}`;
            
            const title = document.createElement('div');
            title.className = 'music-queue-title';
            title.textContent = song.song_title || song.original_filename || 'Unknown Song';
            
            const submitter = document.createElement('div');
            submitter.className = 'music-queue-submitter';
            submitter.textContent = song.guest_name || 'Anonymous';
            
            queueItem.appendChild(title);
            queueItem.appendChild(submitter);
            this.musicQueue.appendChild(queueItem);
        });
        
        console.log(`✅ Music queue updated with ${upcomingMusic.length} items`);
    }

    async generateQRCode() {
        console.log('📱 Generating QR code...');
        
        const qrCodeElement = document.getElementById('qrCode');
        if (qrCodeElement) {
            try {
                // Get network info from backend
                const response = await fetch('/api/network');
                const networkInfo = await response.json();
                
                // Use network IP for QR code so mobile devices can access it
                const uploadUrl = networkInfo.upload_url;
                const qrUrl = `https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=${encodeURIComponent(uploadUrl)}`;
                
                qrCodeElement.src = qrUrl;
                qrCodeElement.alt = `QR Code for ${uploadUrl}`;
                
                console.log('📱 QR code generated for network access:', uploadUrl);
                console.log('📡 Network info:', networkInfo);
                
            } catch (error) {
                console.error('❌ Failed to get network info, using fallback:', error);
                // Fallback to current location
                const uploadUrl = `${window.location.protocol}//${window.location.host}/upload`;
                const qrUrl = `https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=${encodeURIComponent(uploadUrl)}`;
                
                qrCodeElement.src = qrUrl;
                qrCodeElement.alt = `QR Code for ${uploadUrl}`;
            }
        }
    }

    updateConnectionStatus(status, message) {
        if (!this.connectionStatus) return;
        
        const statusDot = this.connectionStatus.querySelector('.status-dot');
        const statusText = this.connectionStatus.querySelector('.status-text');
        
        if (statusDot) {
            statusDot.className = `status-dot ${status}`;
        }
        
        if (statusText) {
            statusText.textContent = message;
        }
    }

    showError(message) {
        console.error('❌ Error:', message);
        // Could show a toast notification or error overlay here
    }

    // Keyboard controls for testing/debugging
    setupKeyboardControls() {
        document.addEventListener('keydown', (event) => {
            switch (event.key) {
                case 'ArrowRight':
                case ' ':
                    event.preventDefault();
                    this.nextSlide();
                    break;
                case 'ArrowLeft':
                    event.preventDefault();
                    this.previousSlide();
                    break;
                case 'p':
                    event.preventDefault();
                    this.isPlaying ? this.stopSlideshow() : this.startSlideshow();
                    break;
                case 'r':
                    event.preventDefault();
                    this.loadContent();
                    break;
            }
        });
    }
}

// Initialize Party Display when DOM is ready
window.addEventListener('load', () => {
    console.log('🎉 Party Memory Wall loading...');
    window.partyDisplay = new PartyDisplay();
    
    // Enable keyboard controls in development
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        window.partyDisplay.setupKeyboardControls();
        console.log('⌨️ Keyboard controls enabled (dev mode)');
    }
});

// Prevent context menu and text selection for kiosk mode
document.addEventListener('contextmenu', (e) => e.preventDefault());
document.addEventListener('selectstart', (e) => e.preventDefault());

// Handle window focus/blur for pause/resume
window.addEventListener('blur', () => {
    console.log('👁️ Window lost focus, pausing slideshow');
    if (window.partyDisplay) {
        window.partyDisplay.stopSlideshow();
    }
});

window.addEventListener('focus', () => {
    console.log('👁️ Window gained focus, resuming slideshow');
    if (window.partyDisplay) {
        window.partyDisplay.startSlideshow();
    }
});

// Export for testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PartyDisplay;
}