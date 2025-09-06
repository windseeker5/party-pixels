/**
 * Party Memory Wall Upload Interface
 * Mobile-optimized upload handling for Valérie's 50th Birthday
 * Supports photos, videos, and music uploads with real-time progress
 */

class PartyUpload {
    constructor() {
        this.uploadArea = null;
        this.fileInput = null;
        this.uploadForm = null;
        this.selectedFiles = [];
        this.isUploading = false;
        this.websocket = null;
        this.connectionRetryCount = 0;
        this.maxRetries = 3;
        
        // Configuration from server
        this.config = {
            max_file_size: 500 * 1024 * 1024, // 500MB default
            allowed_photo_types: ['jpg', 'jpeg', 'png', 'gif', 'heic', 'webp'],
            allowed_video_types: ['mp4', 'mov', 'avi', 'webm', 'm4v', 'mkv'],
            allowed_music_types: ['mp3', 'm4a', 'wav', 'flac']
        };
        
        // Initialize when DOM is ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.init());
        } else {
            this.init();
        }
    }

    async init() {
        console.log('📱 Initializing Party Upload Interface');
        
        // Get DOM elements
        this.uploadArea = document.getElementById('uploadArea');
        this.fileInput = document.getElementById('fileInput');
        this.uploadForm = document.getElementById('uploadForm');
        
        if (!this.uploadArea || !this.fileInput || !this.uploadForm) {
            console.error('❌ Required DOM elements not found');
            return;
        }
        
        try {
            // Load configuration from server
            await this.loadConfig();
            
            // Setup event listeners
            this.setupEventListeners();
            // Setup Socket.IO connection for real-time updates
            this.setupWebSocket();
            
            // Setup form validation
            this.setupFormValidation();
            
            // Setup music search functionality
            this.setupMusicSearch();
            
            // Setup model selection functionality
            this.setupModelSelection();
            
            console.log('✅ Party Upload Interface initialized successfully');
            
        } catch (error) {
            console.error('❌ Failed to initialize upload interface:', error);
            this.showError('Failed to initialize upload interface');
        }
    }

    async loadConfig() {
        try {
            const response = await fetch('/api/config');
            if (response.ok) {
                const config = await response.json();
                this.config = { ...this.config, ...config };
                console.log('⚙️ Configuration loaded:', this.config);
            }
        } catch (error) {
            console.warn('⚠️ Failed to load config, using defaults:', error);
        }
    }

    setupEventListeners() {
        console.log('🎧 Setting up event listeners...');
        
        // Drag and drop events
        this.uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.uploadArea.classList.add('drag-over');
        });
        
        this.uploadArea.addEventListener('dragleave', (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.uploadArea.classList.remove('drag-over');
        });
        
        this.uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.uploadArea.classList.remove('drag-over');
            
            const files = Array.from(e.dataTransfer.files);
            console.log(`📎 Files dropped: ${files.length}`);
            this.handleFiles(files);
        });
        
        // Click to select files
        this.uploadArea.addEventListener('click', (e) => {
            if (this.isUploading) return;
            
            // Only trigger file input if clicking the upload area itself, not child elements
            if (e.target === this.uploadArea || e.target.closest('.upload-prompt')) {
                this.fileInput.click();
            }
        });
        
        // File input change
        this.fileInput.addEventListener('change', (e) => {
            const files = Array.from(e.target.files);
            console.log(`📎 Files selected: ${files.length}`);
            this.handleFiles(files);
        });
        
        // Form submission
        this.uploadForm.addEventListener('submit', (e) => {
            e.preventDefault();
            if (!this.isUploading && this.selectedFiles.length > 0) {
                this.uploadFiles();
            }
        });
        
        // Prevent default drag behavior on document
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            document.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
            });
        });
    }

    setupWebSocket() {
        if (!window.io) {
            console.warn('⚠️ Socket.IO not loaded');
            this.updateConnectionStatus('disconnected', 'Socket.IO unavailable');
            return;
        }
        
        console.log('🔌 Setting up Socket.IO connection...');
        this.updateConnectionStatus('connecting', 'Connecting to server...');
        
        try {
            this.websocket = io({
                transports: ['polling', 'websocket'],
                upgrade: true
            });
            
            this.websocket.on('connect', () => {
                console.log('✅ Socket.IO connected');
                this.connectionRetryCount = 0;
                this.updateConnectionStatus('connected', 'Connected to party server');
            });
            
            this.websocket.on('disconnect', (reason) => {
                console.log('🔌 Socket.IO disconnected:', reason);
                this.updateConnectionStatus('disconnected', 'Disconnected');
                if (reason === 'io server disconnect') {
                    // Server disconnected, reconnect manually
                    this.scheduleWebSocketReconnect();
                }
            });
            
            this.websocket.on('connect_error', (error) => {
                console.error('❌ Socket.IO connection error:', error);
                this.updateConnectionStatus('disconnected', 'Connection failed');
                this.scheduleWebSocketReconnect();
            });
            
            // Listen for real-time updates
            this.websocket.on('new_upload', (data) => {
                console.log('📸 New upload notification:', data);
            });
            
            this.websocket.on('music_update', (data) => {
                console.log('🎵 Music update notification:', data);
            });
            
        } catch (error) {
            console.error('❌ Failed to create Socket.IO connection:', error);
            this.updateConnectionStatus('disconnected', 'Failed to connect');
        }
    }

    scheduleWebSocketReconnect() {
        if (this.connectionRetryCount >= this.maxRetries) {
            console.log('❌ Max Socket.IO reconnection attempts reached');
            this.updateConnectionStatus('disconnected', 'Connection failed');
            return;
        }
        
        this.connectionRetryCount++;
        const delay = Math.min(1000 * Math.pow(2, this.connectionRetryCount), 10000);
        
        this.updateConnectionStatus('connecting', `Reconnecting... (${this.connectionRetryCount}/${this.maxRetries})`);
        
        setTimeout(() => {
            if (this.websocket) {
                this.websocket.connect();
            } else {
                this.setupWebSocket();
            }
        }, delay);
    }

    setupFormValidation() {
        const inputs = this.uploadForm.querySelectorAll('input[type="text"]');
        
        inputs.forEach(input => {
            input.addEventListener('input', () => {
                this.updateSubmitButton();
            });
        });
        
        this.updateSubmitButton();
    }

    handleFiles(files) {
        if (this.isUploading) {
            console.log('⚠️ Upload in progress, ignoring new files');
            return;
        }
        
        console.log(`📎 Processing ${files.length} files...`);
        
        const validFiles = [];
        const errors = [];
        
        files.forEach(file => {
            const validation = this.validateFile(file);
            if (validation.valid) {
                validFiles.push(file);
            } else {
                errors.push(`${file.name}: ${validation.error}`);
            }
        });
        
        if (errors.length > 0) {
            this.showError(`Some files were rejected:\n${errors.join('\n')}`);
        }
        
        if (validFiles.length > 0) {
            this.selectedFiles = validFiles;
            this.showFilePreview(validFiles);
            this.updateSubmitButton();
            console.log(`✅ ${validFiles.length} files ready for upload`);
        } else {
            console.log('❌ No valid files selected');
        }
    }

    validateFile(file) {
        console.log(`🔍 Validating file: ${file.name} (${file.type}, ${this.formatFileSize(file.size)})`);
        
        // Check file size
        if (file.size > this.config.max_file_size) {
            return {
                valid: false,
                error: `File too large. Maximum size is ${this.formatFileSize(this.config.max_file_size)}`
            };
        }
        
        if (file.size === 0) {
            return {
                valid: false,
                error: 'Empty file'
            };
        }
        
        // Check file type
        const fileName = file.name.toLowerCase();
        const fileExtension = fileName.split('.').pop();
        const mimeType = file.type.toLowerCase();
        
        let isValidType = false;
        
        // Check by MIME type first, then by extension
        if (mimeType.startsWith('image/') || this.config.allowed_photo_types.includes(fileExtension)) {
            isValidType = true;
        } else if (mimeType.startsWith('video/') || this.config.allowed_video_types.includes(fileExtension)) {
            isValidType = true;
        } else if (mimeType.startsWith('audio/') || this.config.allowed_music_types.includes(fileExtension)) {
            isValidType = true;
        }
        
        if (!isValidType) {
            return {
                valid: false,
                error: 'File type not supported. Please upload photos, videos, or music files.'
            };
        }
        
        return { valid: true };
    }

    showFilePreview(files) {
        console.log(`🖼️ Showing preview for ${files.length} files`);
        
        const previewContainer = document.getElementById('filePreviews');
        if (!previewContainer) return;
        
        previewContainer.innerHTML = '';
        previewContainer.style.display = 'block';
        
        files.forEach((file, index) => {
            const preview = document.createElement('div');
            preview.className = 'file-preview';
            preview.dataset.index = index;
            
            // Detect file type
            const mimeType = file.type.toLowerCase();
            const fileName = file.name.toLowerCase();
            const fileExtension = fileName.split('.').pop();
            
            if (mimeType.startsWith('image/') || this.config.allowed_photo_types.includes(fileExtension)) {
                preview.classList.add('photo');
                
                // Create image preview
                const reader = new FileReader();
                reader.onload = (e) => {
                    preview.style.backgroundImage = `url(${e.target.result})`;
                };
                reader.readAsDataURL(file);
                
            } else if (mimeType.startsWith('video/') || this.config.allowed_video_types.includes(fileExtension)) {
                preview.classList.add('video');
                const videoIcon = document.createElement('div');
                videoIcon.className = 'file-type-icon';
                videoIcon.innerHTML = '🎥<span class="file-type-label">Video</span>';
                preview.appendChild(videoIcon);
                
            } else if (mimeType.startsWith('audio/') || this.config.allowed_music_types.includes(fileExtension)) {
                preview.classList.add('music');
                const musicIcon = document.createElement('div');
                musicIcon.className = 'file-type-icon';
                musicIcon.innerHTML = '🎵<span class="file-type-label">Music</span>';
                preview.appendChild(musicIcon);
            }
            
            // Add file info
            const fileInfo = document.createElement('div');
            fileInfo.className = 'file-info';
            fileInfo.innerHTML = `
                <div class="file-name">${file.name}</div>
                <div class="file-size">${this.formatFileSize(file.size)}</div>
            `;
            
            preview.appendChild(fileInfo);
            previewContainer.appendChild(preview);
        });
        
        // Hide upload prompt, show preview
        const uploadPrompt = document.getElementById('uploadPrompt');
        if (uploadPrompt) {
            uploadPrompt.style.display = 'none';
        }
    }

    updateSubmitButton() {
        const shareButton = document.getElementById('shareButton');
        const buttonText = shareButton.querySelector('.button-text');
        
        if (this.selectedFiles.length > 0) {
            shareButton.disabled = false;
            shareButton.style.cursor = 'pointer';
            
            const fileCount = this.selectedFiles.length;
            const fileWord = fileCount === 1 ? 'file' : 'files';
            buttonText.textContent = `Share ${fileCount} ${fileWord}! 🎉`;
            
        } else {
            shareButton.disabled = true;
            shareButton.style.cursor = 'not-allowed';
            buttonText.textContent = 'Select files first';
        }
    }

    async uploadFiles() {
        if (this.isUploading || this.selectedFiles.length === 0) {
            console.log('⚠️ Upload already in progress or no files selected');
            return;
        }
        
        console.log(`🚀 Starting upload of ${this.selectedFiles.length} files...`);
        
        // Immediate button feedback
        const shareButton = document.getElementById('shareButton');
        const buttonText = shareButton.querySelector('.button-text');
        
        shareButton.disabled = true;
        buttonText.textContent = 'Uploading... ⏳';
        shareButton.style.backgroundColor = '#FFA500'; // Orange for uploading
        
        this.isUploading = true;
        this.showProgress(true);
        
        try {
            const formData = new FormData();
            
            // Add files to form data
            this.selectedFiles.forEach(file => {
                formData.append('files', file);
            });
            
            // Add metadata
            const guestName = document.getElementById('guestName').value.trim();
            const songTitle = document.getElementById('songTitle').value.trim();
            const artist = document.getElementById('artist').value.trim();
            
            if (guestName) formData.append('guest_name', guestName);
            if (songTitle) formData.append('song_title', songTitle);
            if (artist) formData.append('artist', artist);
            
            // Auto-detect file type (server will handle this)
            formData.append('type', 'auto');
            
            // Create progress tracking
            const xhr = new XMLHttpRequest();
            
            xhr.upload.addEventListener('progress', (e) => {
                if (e.lengthComputable) {
                    const percentComplete = (e.loaded / e.total) * 100;
                    this.updateProgress(percentComplete, `Uploading... ${Math.round(percentComplete)}%`);
                }
            });
            
            xhr.addEventListener('load', () => {
                if (xhr.status === 200 || xhr.status === 201) {
                    try {
                        const response = JSON.parse(xhr.responseText);
                        this.handleUploadSuccess(response);
                    } catch (error) {
                        this.handleUploadError('Invalid response from server');
                    }
                } else {
                    try {
                        const errorResponse = JSON.parse(xhr.responseText);
                        this.handleUploadError(errorResponse.error || `Upload failed (${xhr.status})`);
                    } catch (error) {
                        this.handleUploadError(`Upload failed (${xhr.status})`);
                    }
                }
            });
            
            xhr.addEventListener('error', () => {
                this.handleUploadError('Network error during upload');
            });
            
            xhr.addEventListener('timeout', () => {
                this.handleUploadError('Upload timed out');
            });
            
            // Send the request
            xhr.open('POST', '/api/upload');
            xhr.timeout = 300000; // 5 minutes timeout
            xhr.send(formData);
            
        } catch (error) {
            console.error('❌ Upload error:', error);
            this.handleUploadError(error.message);
        }
    }

    handleUploadSuccess(response) {
        console.log('✅ Upload successful:', response);
        
        this.isUploading = false;
        this.showProgress(false);
        
        // Add haptic feedback for mobile
        if (navigator.vibrate) {
            navigator.vibrate([200, 100, 200]); // Success vibration pattern
        }
        
        // Hide any error messages first
        const errorMessage = document.getElementById('errorMessage');
        if (errorMessage) errorMessage.style.display = 'none';
        
        // Show success message
        const successMessage = document.getElementById('successMessage');
        const successDetails = document.getElementById('successDetails');
        
        console.log('🔍 Success elements found:', {
            successMessage: !!successMessage, 
            successDetails: !!successDetails
        });
        
        if (successMessage) {
            const fileCount = response.files ? response.files.length : this.selectedFiles.length;
            const fileWord = fileCount === 1 ? 'file' : 'files';
            
            if (successDetails) {
                successDetails.textContent = `${fileCount} ${fileWord} uploaded successfully! They will appear on the big screen soon.`;
            }
            
            // Don't hide upload container - just show success message prominently
            const uploadContainer = document.querySelector('.upload-container');
            // Instead of hiding, just scroll to success message
            
            // Make success message very visible
            successMessage.style.display = 'block';
            successMessage.style.position = 'fixed';
            successMessage.style.top = '50%';
            successMessage.style.left = '50%';
            successMessage.style.transform = 'translate(-50%, -50%)';
            successMessage.style.zIndex = '9999';
            successMessage.style.width = '90%';
            successMessage.style.maxWidth = '400px';
            successMessage.style.background = 'rgba(0, 255, 0, 0.9)';
            successMessage.style.border = '3px solid #00ff00';
            successMessage.style.color = '#000';
            
            // Scroll to top to show success message
            window.scrollTo({ top: 0, behavior: 'smooth' });
            
            // Add animation class for extra visibility
            successMessage.classList.add('animate-success');
            
            // Also show a browser notification if possible
            if ('Notification' in window && Notification.permission === 'granted') {
                new Notification('Upload Successful! 🎉', {
                    body: `Your ${fileWord} uploaded successfully!`,
                    icon: '✅'
                });
            }
            
            // Auto-hide after 4 seconds
            setTimeout(() => {
                this.hideSuccessMessage();
            }, 4000);
            
            console.log('🎉 Success message displayed successfully');
        } else {
            console.error('❌ Success message element not found!');
            // Fallback: show browser alert
            alert('Upload successful! Your photos will appear on the big screen soon.');
        }
        
        // Clear selected files
        this.selectedFiles = [];
        this.fileInput.value = '';
    }

    hideSuccessMessage() {
        const successMessage = document.getElementById('successMessage');
        if (successMessage) {
            // Reset positioning
            successMessage.style.position = '';
            successMessage.style.top = '';
            successMessage.style.left = '';
            successMessage.style.transform = '';
            successMessage.style.width = '';
            successMessage.style.maxWidth = '';
            successMessage.style.background = '';
            successMessage.style.border = '';
            successMessage.style.color = '';
            
            // Hide the message
            successMessage.style.display = 'none';
            successMessage.classList.remove('animate-success');
            
            console.log('🔄 Success message hidden and reset');
        }
    }

    handleUploadError(errorMessage) {
        console.error('❌ Upload error:', errorMessage);
        
        this.isUploading = false;
        this.showProgress(false);
        
        // Show error message
        this.showError(errorMessage);
    }

    showProgress(show, text = 'Preparing upload...') {
        const uploadProgress = document.getElementById('uploadProgress');
        const progressText = document.getElementById('progressText');
        const uploadPrompt = document.getElementById('uploadPrompt');
        const filePreviews = document.getElementById('filePreviews');
        
        if (show) {
            if (uploadProgress) uploadProgress.style.display = 'block';
            if (uploadPrompt) uploadPrompt.style.display = 'none';
            if (filePreviews) filePreviews.style.display = 'none';
            if (progressText) progressText.textContent = text;
            
        } else {
            if (uploadProgress) uploadProgress.style.display = 'none';
            
            // Only show prompt if no files selected
            if (this.selectedFiles.length === 0) {
                if (uploadPrompt) uploadPrompt.style.display = 'block';
            } else {
                if (filePreviews) filePreviews.style.display = 'block';
            }
        }
    }

    updateProgress(percentage, text) {
        const progressFill = document.getElementById('progressFill');
        const progressText = document.getElementById('progressText');
        const uploadDetails = document.getElementById('uploadDetails');
        
        if (progressFill) {
            progressFill.style.width = `${percentage}%`;
        }
        
        if (progressText) {
            progressText.textContent = text;
        }
        
        if (uploadDetails) {
            const totalSize = this.selectedFiles.reduce((sum, file) => sum + file.size, 0);
            const uploadedSize = (percentage / 100) * totalSize;
            
            uploadDetails.innerHTML = `
                <div>${this.formatFileSize(uploadedSize)} / ${this.formatFileSize(totalSize)}</div>
                <div>${this.selectedFiles.length} files</div>
            `;
        }
    }

    showError(message) {
        console.error('❌ Error:', message);
        
        const errorMessage = document.getElementById('errorMessage');
        const errorDetails = document.getElementById('errorDetails');
        
        if (errorMessage && errorDetails) {
            errorDetails.textContent = message;
            errorMessage.style.display = 'block';
            
            // Auto-hide after 10 seconds
            setTimeout(() => {
                this.hideError();
            }, 10000);
            
            // Scroll to error message
            errorMessage.scrollIntoView({ behavior: 'smooth', block: 'center' });
        } else {
            // Fallback to alert if error elements not found
            alert(message);
        }
    }

    hideError() {
        const errorMessage = document.getElementById('errorMessage');
        if (errorMessage) {
            errorMessage.style.display = 'none';
        }
    }

    updateConnectionStatus(status, message) {
        const connectionStatus = document.getElementById('connectionStatus');
        if (!connectionStatus) return;
        
        const statusDot = connectionStatus.querySelector('.status-dot');
        const statusText = connectionStatus.querySelector('.status-text');
        
        if (statusDot) {
            statusDot.className = `status-dot ${status}`;
        }
        
        if (statusText) {
            statusText.textContent = message;
        }
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    // ============================================================================
    // MUSIC SEARCH FUNCTIONALITY
    // ============================================================================

    setupMusicSearch() {
        console.log('🎵 Setting up music search functionality');
        
        // Get music search elements
        this.musicSearchInput = document.getElementById('musicSearch');
        this.searchButton = document.getElementById('searchButton');
        this.searchResults = document.getElementById('searchResults');
        this.searchLoading = document.getElementById('searchLoading');
        
        if (!this.musicSearchInput || !this.searchButton) {
            console.log('⚠️  Music search elements not found');
            return;
        }
        
        // Add event listeners
        this.searchButton.addEventListener('click', () => this.performMusicSearch());
        this.musicSearchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                this.performMusicSearch();
            }
        });
        
        // Add real-time search suggestions (debounced)
        let searchTimeout;
        this.musicSearchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            const query = e.target.value.trim();
            if (query.length >= 3) {
                searchTimeout = setTimeout(() => this.performMusicSearch(), 1000);
            }
        });
    }

    async performMusicSearch() {
        const query = this.musicSearchInput.value.trim();
        
        if (!query) {
            this.showError('Please enter a search query');
            return;
        }
        
        console.log(`🔍 Searching for music: "${query}"`);
        
        // Show loading state
        this.showSearchLoading();
        
        try {
            const response = await fetch('/api/music/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query: query,
                    local_limit: 5,
                    youtube_limit: 3
                }),
            });
            
            if (!response.ok) {
                throw new Error(`Search failed: ${response.statusText}`);
            }
            
            const results = await response.json();
            console.log('🎵 Search results:', results);
            
            this.displaySearchResults(results);
            
        } catch (error) {
            console.error('❌ Music search error:', error);
            this.showError('Music search failed. Please try again.');
            this.hideSearchLoading();
        }
    }

    showSearchLoading() {
        if (this.searchLoading) {
            this.searchLoading.style.display = 'block';
        }
        if (this.searchResults) {
            this.searchResults.style.display = 'none';
        }
    }

    hideSearchLoading() {
        if (this.searchLoading) {
            this.searchLoading.style.display = 'none';
        }
    }

    displaySearchResults(results) {
        this.hideSearchLoading();
        
        if (!this.searchResults) return;
        
        const totalResults = results.total_results || 0;
        
        if (totalResults === 0) {
            this.showNoResults();
            return;
        }
        
        // Update results count
        const resultsCount = document.getElementById('resultsCount');
        if (resultsCount) {
            resultsCount.textContent = `${totalResults} result${totalResults !== 1 ? 's' : ''}`;
        }
        
        // Display local results
        this.displayLocalResults(results.local || []);
        
        // Display YouTube results
        this.displayYouTubeResults(results.youtube || []);
        
        // Show results container
        this.searchResults.style.display = 'block';
    }

    displayLocalResults(localResults) {
        const localList = document.getElementById('localResultsList');
        const localContainer = document.getElementById('localResults');
        
        if (!localList || !localContainer) return;
        
        if (localResults.length === 0) {
            localContainer.style.display = 'none';
            return;
        }
        
        localContainer.style.display = 'block';
        localList.innerHTML = '';
        
        localResults.forEach((song, index) => {
            const resultElement = this.createMusicResultElement(song, 'local');
            localList.appendChild(resultElement);
        });
    }

    displayYouTubeResults(youtubeResults) {
        const youtubeList = document.getElementById('youtubeResultsList');
        const youtubeContainer = document.getElementById('youtubeResults');
        
        if (!youtubeList || !youtubeContainer) return;
        
        if (youtubeResults.length === 0) {
            youtubeContainer.style.display = 'none';
            return;
        }
        
        youtubeContainer.style.display = 'block';
        youtubeList.innerHTML = '';
        
        youtubeResults.forEach((song, index) => {
            const resultElement = this.createMusicResultElement(song, 'youtube');
            youtubeList.appendChild(resultElement);
        });
    }

    createMusicResultElement(song, source) {
        const div = document.createElement('div');
        div.className = 'music-result';
        
        const duration = song.duration ? this.formatDuration(song.duration) : '';
        const sourceLabel = source === 'youtube' ? 'YouTube' : 'Library';
        const sourceClass = source === 'youtube' ? 'youtube' : '';
        
        div.innerHTML = `
            <div class="result-info">
                <div class="result-title">${this.escapeHtml(song.title || song.artist || 'Unknown')}</div>
                <div class="result-artist">${this.escapeHtml(song.artist || 'Unknown Artist')}</div>
                <div class="result-details">
                    <span class="result-source ${sourceClass}">${sourceLabel}</span>
                    ${duration ? `<span>${duration}</span>` : ''}
                    ${song.album ? `<span>${this.escapeHtml(song.album)}</span>` : ''}
                </div>
            </div>
            <div class="result-actions">
                <button class="add-btn" data-source="${source}">
                    Add to Queue
                </button>
            </div>
        `;
        
        // Add event listener to the button
        const button = div.querySelector('.add-btn');
        button.addEventListener('click', (event) => {
            this.addMusicToQueue(source, song, event.target);
        });
        
        return div;
    }

    async addMusicToQueue(source, song, button = null) {
        const guestName = document.getElementById('guestName')?.value || 'Anonymous';
        
        console.log(`🎵 Adding ${source} music to queue:`, song);
        
        // If no button passed, find it from the event
        if (!button && event && event.target) {
            button = event.target;
        }
        
        const originalText = button ? button.textContent : 'Add to Queue';
        
        try {
            if (source === 'local') {
                // Add local music directly to queue
                const response = await fetch('/api/music/add-to-queue', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        source: 'local',
                        file_path: song.file_path,
                        title: song.title,
                        artist: song.artist,
                        duration: song.duration,
                        guest_name: guestName,
                        original_query: this.musicSearchInput.value
                    }),
                });
                
                if (!response.ok) {
                    throw new Error(`Failed to add to queue: ${response.statusText}`);
                }
                
                const result = await response.json();
                console.log('✅ Local music added to queue:', result);
                
                if (button) {
                    button.textContent = '✅ Added!';
                    button.className = 'add-btn added';
                    button.disabled = true;
                }
                
            } else if (source === 'youtube') {
                // Download from YouTube first
                if (button) {
                    button.textContent = 'Downloading...';
                    button.className = 'add-btn downloading';
                    button.disabled = true;
                }
                
                const response = await fetch('/api/music/download', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        url: song.url,
                        title: song.title,
                        artist: song.artist,
                        guest_name: guestName,
                        original_query: this.musicSearchInput.value
                    }),
                });
                
                if (!response.ok) {
                    throw new Error(`Download failed: ${response.statusText}`);
                }
                
                const result = await response.json();
                console.log('✅ YouTube music downloaded and queued:', result);
                
                if (button) {
                    button.textContent = '✅ Downloaded!';
                    button.className = 'add-btn added';
                }
            }
            
        } catch (error) {
            console.error('❌ Error adding music to queue:', error);
            this.showError(`Failed to add "${song.title}" to queue`);
            
            // Reset button
            if (button) {
                button.textContent = originalText;
                button.className = 'add-btn';
                button.disabled = false;
            }
        }
    }

    showNoResults() {
        if (!this.searchResults) return;
        
        this.searchResults.innerHTML = `
            <div class="no-results">
                <span class="emoji">🎵</span>
                <p>No music found for your search.</p>
                <p>Try different keywords or check the spelling.</p>
            </div>
        `;
        this.searchResults.style.display = 'block';
    }

    formatDuration(seconds) {
        if (!seconds || seconds <= 0) return '';
        
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
    }

    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    escapeForJs(text) {
        return text.replace(/'/g, "\\'").replace(/"/g, '\\"');
    }

    // ============================================================================
    // MODEL SELECTION FUNCTIONALITY
    // ============================================================================

    setupModelSelection() {
        console.log('🤖 Setting up model selection functionality');
        
        this.modelSelectionSection = document.getElementById('modelSelectionSection');
        this.modelSelect = document.getElementById('modelSelect');
        this.modelInfo = document.getElementById('modelInfo');
        
        if (!this.modelSelect || !this.modelInfo) {
            console.warn('⚠️ Model selection elements not found');
            return;
        }
        
        // Load available models
        this.loadAvailableModels();
        
        // Handle model selection changes
        this.modelSelect.addEventListener('change', (e) => {
            this.selectModel(e.target.value);
        });
    }

    async loadAvailableModels() {
        try {
            const response = await fetch('/api/ollama/models');
            const data = await response.json();
            
            if (data.ollama_available && data.models.length > 0) {
                this.populateModelDropdown(data.models, data.current_model);
                this.updateModelInfo(data.current_model, data.models);
                
                // Show the model selection section
                if (this.modelSelectionSection) {
                    this.modelSelectionSection.style.display = 'block';
                }
            } else {
                this.showModelUnavailable(data.error || 'No models available');
            }
            
        } catch (error) {
            console.error('❌ Error loading models:', error);
            this.showModelUnavailable('Failed to load models');
        }
    }

    populateModelDropdown(models, currentModel) {
        this.modelSelect.innerHTML = '';
        
        // Add models as options
        models.forEach(model => {
            const option = document.createElement('option');
            option.value = model.name;
            option.textContent = `${model.name} (${model.parameter_size})`;
            
            if (model.name === currentModel) {
                option.selected = true;
            }
            
            this.modelSelect.appendChild(option);
        });
    }

    updateModelInfo(currentModel, models) {
        if (!currentModel || !models) {
            this.modelInfo.innerHTML = '<span class="model-status unavailable">❌ No model selected</span>';
            return;
        }
        
        const model = models.find(m => m.name === currentModel);
        if (model) {
            const sizeGB = (model.size / (1024 * 1024 * 1024)).toFixed(1);
            
            this.modelInfo.innerHTML = `
                <span class="model-status available">✅ ${model.name} active</span>
                <div class="model-details">
                    Size: ${sizeGB} GB | Parameters: ${model.parameter_size} | Family: ${model.family}
                </div>
            `;
        } else {
            this.modelInfo.innerHTML = '<span class="model-status unavailable">⚠️ Model information unavailable</span>';
        }
    }

    showModelUnavailable(error) {
        this.modelSelect.innerHTML = '<option value="">Models unavailable</option>';
        this.modelInfo.innerHTML = `<span class="model-status unavailable">❌ ${error}</span>`;
        
        // Still show the section so users know about the feature
        if (this.modelSelectionSection) {
            this.modelSelectionSection.style.display = 'block';
        }
    }

    async selectModel(modelName) {
        if (!modelName) return;
        
        try {
            const response = await fetch('/api/ollama/select-model', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ model: modelName })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                console.log(`✅ Model changed to: ${modelName}`);
                this.loadAvailableModels(); // Refresh the info
                
                // Show brief confirmation
                const originalText = this.modelInfo.innerHTML;
                this.modelInfo.innerHTML = '<span class="model-status available">🔄 Model updated successfully!</span>';
                
                setTimeout(() => {
                    this.loadAvailableModels();
                }, 2000);
                
            } else {
                console.error('❌ Error selecting model:', data.error);
                this.modelInfo.innerHTML = `<span class="model-status unavailable">❌ Error: ${data.error}</span>`;
            }
            
        } catch (error) {
            console.error('❌ Error selecting model:', error);
            this.modelInfo.innerHTML = '<span class="model-status unavailable">❌ Failed to change model</span>';
        }
    }
}

// Global functions for HTML event handlers
window.resetForm = function() {
    console.log('🔄 Resetting form...');
    
    // Hide success/error messages
    const successMessage = document.getElementById('successMessage');
    const errorMessage = document.getElementById('errorMessage');
    const uploadContainer = document.querySelector('.upload-container');
    
    if (successMessage) successMessage.style.display = 'none';
    if (errorMessage) errorMessage.style.display = 'none';
    if (uploadContainer) uploadContainer.style.display = 'flex';
    
    // Reset form
    const uploadForm = document.getElementById('uploadForm');
    if (uploadForm) uploadForm.reset();
    
    // Reset file input and preview
    const fileInput = document.getElementById('fileInput');
    const filePreviews = document.getElementById('filePreviews');
    const uploadPrompt = document.getElementById('uploadPrompt');
    
    if (fileInput) fileInput.value = '';
    if (filePreviews) filePreviews.style.display = 'none';
    if (uploadPrompt) uploadPrompt.style.display = 'block';
    
    // Clear selected files
    if (window.partyUpload) {
        window.partyUpload.selectedFiles = [];
        window.partyUpload.updateSubmitButton();
    }
    
    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
};

window.viewSlideshow = function() {
    console.log('📺 Navigating to slideshow...');
    window.location.href = '/';
};

window.hideError = function() {
    if (window.partyUpload) {
        window.partyUpload.hideError();
    }
};

// Initialize when DOM is ready
window.addEventListener('load', () => {
    console.log('📱 Party Upload Interface loading...');
    window.partyUpload = new PartyUpload();
});

// Prevent accidental page refresh during upload
window.addEventListener('beforeunload', (e) => {
    if (window.partyUpload && window.partyUpload.isUploading) {
        e.preventDefault();
        e.returnValue = 'Upload in progress. Are you sure you want to leave?';
        return e.returnValue;
    }
});

// Export for testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PartyUpload;
}