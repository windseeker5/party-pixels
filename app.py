"""
Party Memory Wall Flask Application
Backend server for Valérie's 50th Birthday celebration
CRITICAL: Must run on port 6000 for testing compatibility
"""

import os
import json
import uuid
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory, render_template
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
import logging

# Import our database class and music search
from database import PartyDatabase
from music_search import MusicSearchService

# Initialize Flask app
app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['SECRET_KEY'] = 'valerie-50th-birthday-party-2024'
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size

# Enable CORS for all domains (party network access)
CORS(app, origins="*")

# Initialize SocketIO for real-time updates
socketio = SocketIO(app, cors_allowed_origins="*", ping_interval=25, ping_timeout=5)

# Configure logging to both file and console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('party-wall.log'),
        logging.StreamHandler()  # This prints to console
    ],
    force=True  # Override any existing logging configuration
)
logger = logging.getLogger(__name__)

# Also add print statements for immediate visibility
def log_and_print(message):
    """Log to file and print to console"""
    logger.info(message)
    print(f"🎉 PARTY: {message}")

# Initialize database and music search service
db = PartyDatabase()
music_search = MusicSearchService(db)

# Ensure media directories exist
MEDIA_DIRS = ['media/photos', 'media/videos', 'media/music']
for media_dir in MEDIA_DIRS:
    os.makedirs(media_dir, exist_ok=True)

# Party configuration
PARTY_CONFIG = {
    'title': "Happy 50th Birthday Valérie!",
    'subtitle': "Celebrating 50 Amazing Years",
    'slideshow_duration': 7,
    'weekend_days': 2,
    'max_file_size': 500 * 1024 * 1024,
    'allowed_photo_types': ['jpg', 'jpeg', 'png', 'gif', 'heic', 'webp'],
    'allowed_video_types': ['mp4', 'mov', 'avi', 'webm', 'm4v', 'mkv'],
    'allowed_music_types': ['mp3', 'm4a', 'wav', 'flac']
}

def get_device_id():
    """Generate or get device ID for guest attribution"""
    device_id = request.headers.get('X-Device-ID')
    if not device_id:
        # Generate device ID from IP + User-Agent
        ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        user_agent = request.headers.get('User-Agent', '')
        device_id = f"{ip}-{hash(user_agent) % 10000}"
    return device_id

def allowed_file(filename, file_type):
    """Check if file extension is allowed"""
    if not filename or '.' not in filename:
        return False
    
    ext = filename.rsplit('.', 1)[1].lower()
    
    if file_type == 'photo':
        return ext in PARTY_CONFIG['allowed_photo_types']
    elif file_type == 'video':
        return ext in PARTY_CONFIG['allowed_video_types']
    elif file_type == 'music':
        return ext in PARTY_CONFIG['allowed_music_types']
    
    return False

def process_file(file_path, file_type):
    """Process uploaded file (placeholder for future processing)"""
    # TODO: Add file processing (thumbnails, metadata extraction, etc.)
    log_and_print(f"Processing {file_type} file: {file_path}")
    return True

def broadcast_new_upload(upload_data):
    """Broadcast new upload to all connected clients"""
    try:
        socketio.emit('new_upload', {
            'type': 'new_upload',
            'data': upload_data
        })
        logger.info(f"Broadcasted new upload: {upload_data['guest_name']} - {upload_data['file_type']}")
    except Exception as e:
        logger.error(f"Failed to broadcast upload: {e}")

def broadcast_music_update(music_data):
    """Broadcast music queue update to all connected clients"""
    try:
        socketio.emit('music_update', {
            'type': 'music_update',
            'data': music_data
        })
        logger.info("Broadcasted music queue update")
    except Exception as e:
        logger.error(f"Failed to broadcast music update: {e}")

# Routes

@app.route('/')
def index():
    """Serve main slideshow page"""
    return render_template('index.html')

@app.route('/upload')
def upload_page():
    """Serve upload interface"""
    return render_template('upload.html')

@app.route('/api/config', methods=['GET'])
def get_config():
    """Get party configuration"""
    try:
        # Get settings from database
        db_settings = db.get_all_settings()
        
        # Merge with default config
        config = PARTY_CONFIG.copy()
        config.update({
            'title': db_settings.get('party_title', PARTY_CONFIG['title']),
            'slideshow_duration': int(db_settings.get('slideshow_duration', '7')),
            'max_file_size': int(db_settings.get('max_file_size', str(PARTY_CONFIG['max_file_size']))),
            'allowed_photo_types': json.loads(db_settings.get('allowed_photo_types', json.dumps(PARTY_CONFIG['allowed_photo_types']))),
            'allowed_video_types': json.loads(db_settings.get('allowed_video_types', json.dumps(PARTY_CONFIG['allowed_video_types']))),
            'allowed_music_types': json.loads(db_settings.get('allowed_music_types', json.dumps(PARTY_CONFIG['allowed_music_types'])))
        })
        
        return jsonify(config)
        
    except Exception as e:
        logger.error(f"Error getting config: {e}")
        return jsonify({'error': 'Failed to get configuration'}), 500

@app.route('/api/network', methods=['GET'])
def get_network_info():
    """Get network URLs for QR code generation"""
    try:
        import socket
        
        # Get local IP address
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        
        # Get port from request
        port = request.environ.get('SERVER_PORT', '8000')
        
        # Construct URLs
        base_url = f"http://{local_ip}:{port}"
        
        return jsonify({
            'local_ip': local_ip,
            'port': port,
            'base_url': base_url,
            'upload_url': f"{base_url}/upload",
            'display_url': base_url
        })
        
    except Exception as e:
        logger.error(f"Error getting network info: {e}")
        # Fallback to localhost
        return jsonify({
            'local_ip': '127.0.0.1',
            'port': '8000',
            'base_url': 'http://localhost:8000',
            'upload_url': 'http://localhost:8000/upload',
            'display_url': 'http://localhost:8000'
        })

@app.route('/api/upload', methods=['POST'])
def upload_files():
    """Handle file uploads"""
    try:
        # Check if files were uploaded
        if 'files' not in request.files:
            return jsonify({'error': 'No files uploaded'}), 400
        
        files = request.files.getlist('files')
        if not files or files[0].filename == '':
            return jsonify({'error': 'No files selected'}), 400
        
        # Get guest information
        guest_name = request.form.get('guest_name', 'Anonymous')
        file_type = request.form.get('type', 'auto')  # auto-detect if not specified
        song_title = request.form.get('song_title', '')
        artist = request.form.get('artist', 'Unknown Artist')
        device_id = get_device_id()
        
        uploaded_files = []
        
        for file in files:
            if file and file.filename:
                # Auto-detect file type if not specified
                if file_type == 'auto':
                    mime_type = file.content_type.lower()
                    if mime_type.startswith('image/'):
                        detected_type = 'photo'
                    elif mime_type.startswith('video/'):
                        detected_type = 'video'
                    elif mime_type.startswith('audio/'):
                        detected_type = 'music'
                    else:
                        return jsonify({'error': f'Unsupported file type: {mime_type}'}), 400
                else:
                    detected_type = file_type
                
                # Validate file type
                if not allowed_file(file.filename, detected_type):
                    return jsonify({'error': f'File type not allowed for {detected_type}: {file.filename}'}), 400
                
                # Secure filename
                filename = secure_filename(file.filename)
                if not filename:
                    filename = f"{uuid.uuid4()}.{file.filename.split('.')[-1]}"
                
                # Generate unique filename to prevent conflicts
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                unique_filename = f"{timestamp}_{filename}"
                
                # Determine save path
                media_folder = f"media/{detected_type}s"
                file_path = os.path.join(media_folder, unique_filename)
                
                # Save file
                file.save(file_path)
                file_size = os.path.getsize(file_path)
                
                # Process file
                process_success = process_file(file_path, detected_type)
                
                # Add to database
                upload_id = db.add_upload(
                    device_id=device_id,
                    guest_name=guest_name,
                    file_path=file_path,
                    file_type=detected_type,
                    original_filename=file.filename,
                    file_size=file_size
                )
                
                # Mark as processed
                if process_success:
                    db.mark_upload_processed(upload_id)
                
                # Handle music queue
                if detected_type == 'music':
                    queue_id = db.add_to_music_queue(
                        upload_id=upload_id,
                        song_title=song_title if song_title else os.path.splitext(filename)[0],
                        artist=artist
                    )
                    
                    # Broadcast music update
                    music_queue = db.get_music_queue()
                    broadcast_music_update({
                        'queue_length': music_queue['unplayed_count'],
                        'new_song': {
                            'title': song_title,
                            'artist': artist,
                            'guest_name': guest_name
                        }
                    })
                
                uploaded_files.append({
                    'upload_id': upload_id,
                    'filename': unique_filename,
                    'original_filename': file.filename,
                    'file_type': detected_type,
                    'file_size': file_size
                })
                
                # Broadcast new upload
                broadcast_new_upload({
                    'upload_id': upload_id,
                    'guest_name': guest_name,
                    'file_type': detected_type,
                    'filename': unique_filename,
                    'timestamp': datetime.now().isoformat()
                })
                
                log_and_print(f"File uploaded: {unique_filename} by {guest_name} ({detected_type})")
        
        return jsonify({
            'message': 'Upload successful',
            'files': uploaded_files,
            'upload_id': uploaded_files[0]['upload_id'] if uploaded_files else None
        }), 201
        
    except RequestEntityTooLarge:
        return jsonify({'error': 'File too large. Maximum size is 500MB.'}), 413
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@app.route('/api/media', methods=['GET'])
def get_media():
    """Get media for slideshow"""
    try:
        limit = request.args.get('limit', 100, type=int)
        media_items = db.get_slideshow_media(limit=limit)
        
        return jsonify({
            'media': media_items,
            'total_count': len(media_items)
        })
        
    except Exception as e:
        logger.error(f"Error getting media: {e}")
        return jsonify({'error': 'Failed to get media'}), 500

@app.route('/api/media/current', methods=['GET'])
def get_current_media():
    """Get currently displayed media (placeholder)"""
    try:
        # This would track which media is currently being displayed
        # For now, just return the most recent
        media_items = db.get_slideshow_media(limit=1)
        current_media = media_items[0] if media_items else None
        
        return jsonify({
            'current_media': current_media,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting current media: {e}")
        return jsonify({'error': 'Failed to get current media'}), 500

@app.route('/api/media/next', methods=['POST'])
def next_media():
    """Skip to next media (slideshow control)"""
    try:
        # Broadcast slideshow update
        socketio.emit('slideshow_update', {
            'type': 'slideshow_update',
            'data': {
                'action': 'next',
                'timestamp': datetime.now().isoformat()
            }
        })
        
        return jsonify({'message': 'Skipped to next media'})
        
    except Exception as e:
        logger.error(f"Error skipping media: {e}")
        return jsonify({'error': 'Failed to skip media'}), 500

@app.route('/api/music/queue', methods=['GET'])
def get_music_queue():
    """Get music playback queue"""
    try:
        queue_data = db.get_music_queue()
        return jsonify(queue_data)
        
    except Exception as e:
        logger.error(f"Error getting music queue: {e}")
        return jsonify({'error': 'Failed to get music queue'}), 500

@app.route('/api/music/add', methods=['POST'])
def add_music():
    """Add music to queue (alternative endpoint)"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # This endpoint could be used for adding music without file upload
        # (e.g., from Spotify URLs or existing library)
        
        return jsonify({'message': 'Music added to queue'}), 201
        
    except Exception as e:
        logger.error(f"Error adding music: {e}")
        return jsonify({'error': 'Failed to add music'}), 500

@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """Get party statistics"""
    try:
        stats = db.get_statistics()
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        return jsonify({'error': 'Failed to get statistics'}), 500

# Media serving routes
@app.route('/media/<path:filename>')
def serve_media(filename):
    """Serve uploaded media files"""
    try:
        # Determine media type from path
        if filename.startswith('photos/'):
            media_dir = 'media/photos'
            filename = filename[7:]  # Remove 'photos/' prefix
        elif filename.startswith('videos/'):
            media_dir = 'media/videos'
            filename = filename[7:]  # Remove 'videos/' prefix
        elif filename.startswith('music/'):
            media_dir = 'media/music'
            filename = filename[6:]  # Remove 'music/' prefix
        else:
            return jsonify({'error': 'Invalid media path'}), 404
        
        return send_from_directory(media_dir, filename)
        
    except Exception as e:
        logger.error(f"Error serving media {filename}: {e}")
        return jsonify({'error': 'Media not found'}), 404

# Static file serving
@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static frontend files"""
    return send_from_directory(app.static_folder, filename)

# WebSocket events
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    client_id = request.sid
    logger.info(f"Client connected: {client_id}")
    emit('connected', {'message': 'Connected to Party Memory Wall', 'client_id': client_id})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    client_id = request.sid
    logger.info(f"Client disconnected: {client_id}")

@socketio.on('ping')
def handle_ping():
    """Handle ping from client"""
    emit('pong')

# Error handlers
@app.errorhandler(413)
def too_large(e):
    return jsonify({'error': 'File too large. Maximum size is 500MB.'}), 413

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(e):
    logger.error(f"Internal server error: {e}")
    return jsonify({'error': 'Internal server error'}), 500

# Music Search API Endpoints

@app.route('/api/music/search', methods=['POST'])
def search_music():
    """Search for music in local library and YouTube"""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({'error': 'Search query is required'}), 400
        
        local_limit = data.get('local_limit', 10)
        youtube_limit = data.get('youtube_limit', 5)
        
        log_and_print(f"Music search: '{query}'")
        
        # Perform combined search
        results = music_search.combined_search(query, local_limit, youtube_limit)
        
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"Error searching music: {e}")
        return jsonify({'error': 'Music search failed'}), 500

@app.route('/api/music/recommendations', methods=['GET'])
def get_music_recommendations():
    """Get AI-powered music recommendations based on party patterns"""
    try:
        limit = request.args.get('limit', 10, type=int)
        
        recommendations = music_search.get_recommendations(limit)
        
        return jsonify({
            'recommendations': recommendations,
            'count': len(recommendations)
        })
        
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        return jsonify({'error': 'Failed to get recommendations'}), 500

@app.route('/api/music/add-to-queue', methods=['POST'])
def add_music_to_queue():
    """Add music to the party queue (local or YouTube)"""
    try:
        data = request.get_json()
        
        source = data.get('source')  # 'local' or 'youtube'
        guest_name = data.get('guest_name', 'Anonymous')
        
        if source == 'local':
            # Add local file to queue
            file_path = data.get('file_path')
            title = data.get('title', 'Unknown')
            artist = data.get('artist', 'Unknown Artist')
            duration = data.get('duration')
            
            if not file_path:
                return jsonify({'error': 'file_path is required for local music'}), 400
            
            # Create upload record first
            upload_id = db.add_upload(
                device_id=get_device_id(),
                guest_name=guest_name,
                file_path=file_path,
                file_type='music',
                original_filename=os.path.basename(file_path)
            )
            
            # Add to music queue
            queue_id = db.add_to_music_queue(
                upload_id=upload_id,
                song_title=title,
                artist=artist,
                duration=duration
            )
            
            # Log the selection for learning
            db.log_music_search(
                query=data.get('original_query', ''),
                selected_result={
                    'title': title,
                    'artist': artist,
                    'file_path': file_path,
                    'source': 'local'
                },
                source='local',
                guest_name=guest_name
            )
            
            # Update patterns for AI learning
            db.update_music_pattern('artist', artist)
            if data.get('genre'):
                db.update_music_pattern('genre', data.get('genre'))
            
            log_and_print(f"Added local music to queue: {artist} - {title}")
            
        elif source == 'youtube':
            # For YouTube, we'll need to download first (handled by download endpoint)
            return jsonify({
                'message': 'YouTube music requires download first',
                'next_action': 'use /api/music/download endpoint'
            }), 400
            
        else:
            return jsonify({'error': 'source must be "local" or "youtube"'}), 400
        
        # Broadcast music update
        music_queue = db.get_music_queue()
        broadcast_music_update(music_queue)
        
        return jsonify({
            'message': 'Music added to queue',
            'queue_id': queue_id,
            'upload_id': upload_id
        })
        
    except Exception as e:
        logger.error(f"Error adding music to queue: {e}")
        return jsonify({'error': 'Failed to add music to queue'}), 500

@app.route('/api/music/patterns', methods=['GET'])
def get_music_patterns():
    """Get music patterns for AI DJ insights"""
    try:
        pattern_type = request.args.get('type')  # Optional: filter by type
        limit = request.args.get('limit', 50, type=int)
        
        patterns = db.get_music_patterns(pattern_type, limit)
        
        return jsonify({
            'patterns': patterns,
            'count': len(patterns)
        })
        
    except Exception as e:
        logger.error(f"Error getting music patterns: {e}")
        return jsonify({'error': 'Failed to get music patterns'}), 500

@app.route('/api/music/ai-dj-status', methods=['GET'])
def get_ai_dj_status():
    """Check if AI DJ mode should be offered"""
    try:
        search_count = db.get_search_count()
        ai_dj_threshold = 25  # From environment or config
        
        return jsonify({
            'total_searches': search_count,
            'threshold': ai_dj_threshold,
            'ready_for_ai_dj': search_count >= ai_dj_threshold,
            'searches_remaining': max(0, ai_dj_threshold - search_count)
        })
        
    except Exception as e:
        logger.error(f"Error checking AI DJ status: {e}")
        return jsonify({'error': 'Failed to check AI DJ status'}), 500

@app.route('/api/music/download', methods=['POST'])
def download_youtube_music():
    """Download music from YouTube and add to queue"""
    try:
        data = request.get_json()
        
        youtube_url = data.get('url')
        guest_name = data.get('guest_name', 'Anonymous')
        title = data.get('title', 'Unknown')
        artist = data.get('artist', 'Unknown Artist')
        
        if not youtube_url:
            return jsonify({'error': 'YouTube URL is required'}), 400
        
        log_and_print(f"Downloading YouTube music: {artist} - {title}")
        
        # Import yt-dlp here to avoid startup delays
        import yt_dlp
        
        # Create download directory
        download_dir = 'media/music'
        os.makedirs(download_dir, exist_ok=True)
        
        # Configure yt-dlp
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': f'{download_dir}/%(title)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract info first to get the actual title
                info = ydl.extract_info(youtube_url, download=False)
                actual_title = info.get('title', title)
                actual_duration = info.get('duration')
                
                # Download the audio
                ydl.download([youtube_url])
                
                # Find the downloaded file
                safe_title = "".join(c for c in actual_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
                downloaded_file = f"{download_dir}/{safe_title}.mp3"
                
                # Try to find the actual downloaded file
                import glob
                possible_files = glob.glob(f"{download_dir}/*.mp3")
                if possible_files:
                    # Get the most recently created file
                    downloaded_file = max(possible_files, key=os.path.getctime)
                
                if not os.path.exists(downloaded_file):
                    return jsonify({'error': 'Download completed but file not found'}), 500
                
                # Create upload record
                upload_id = db.add_upload(
                    device_id=get_device_id(),
                    guest_name=guest_name,
                    file_path=downloaded_file,
                    file_type='music',
                    original_filename=f"{actual_title}.mp3",
                    file_size=os.path.getsize(downloaded_file)
                )
                
                # Add to music queue
                queue_id = db.add_to_music_queue(
                    upload_id=upload_id,
                    song_title=actual_title,
                    artist=artist,
                    duration=actual_duration
                )
                
                # Log the selection for learning
                db.log_music_search(
                    query=data.get('original_query', ''),
                    selected_result={
                        'title': actual_title,
                        'artist': artist,
                        'url': youtube_url,
                        'source': 'youtube'
                    },
                    source='youtube',
                    guest_name=guest_name
                )
                
                # Update patterns for AI learning
                db.update_music_pattern('artist', artist)
                
                log_and_print(f"Successfully downloaded and queued: {artist} - {actual_title}")
                
                # Broadcast music update
                music_queue = db.get_music_queue()
                broadcast_music_update(music_queue)
                
                return jsonify({
                    'message': 'Music downloaded and added to queue',
                    'title': actual_title,
                    'artist': artist,
                    'duration': actual_duration,
                    'queue_id': queue_id,
                    'upload_id': upload_id,
                    'file_path': downloaded_file
                })
                
        except Exception as download_error:
            logger.error(f"yt-dlp download error: {download_error}")
            return jsonify({'error': f'Download failed: {str(download_error)}'}), 500
            
    except Exception as e:
        logger.error(f"Error downloading YouTube music: {e}")
        return jsonify({'error': 'YouTube download failed'}), 500

@app.route('/api/ollama/models', methods=['GET'])
def get_available_models():
    """Get available Ollama models"""
    try:
        import requests
        response = requests.get('http://127.0.0.1:11434/api/tags', timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            models = []
            
            for model in data.get('models', []):
                model_info = {
                    'name': model['name'],
                    'size': model['size'],
                    'modified_at': model['modified_at'],
                    'parameter_size': model.get('details', {}).get('parameter_size', 'Unknown'),
                    'family': model.get('details', {}).get('family', 'Unknown')
                }
                models.append(model_info)
            
            # Get current selected model
            current_model = db.get_setting('ollama_model', 'llama3.1:8b')
            
            return jsonify({
                'models': models,
                'current_model': current_model,
                'ollama_available': True
            })
        else:
            return jsonify({
                'models': [],
                'current_model': None,
                'ollama_available': False,
                'error': 'Ollama server not responding'
            })
            
    except Exception as e:
        logger.error(f"Error fetching Ollama models: {e}")
        return jsonify({
            'models': [],
            'current_model': None,
            'ollama_available': False,
            'error': str(e)
        }), 500

@app.route('/api/ollama/select-model', methods=['POST'])
def select_ollama_model():
    """Select which Ollama model to use for music search"""
    try:
        data = request.get_json()
        model_name = data.get('model')
        
        if not model_name:
            return jsonify({'error': 'Model name is required'}), 400
        
        # Verify the model exists
        import requests
        response = requests.get('http://127.0.0.1:11434/api/tags', timeout=5)
        
        if response.status_code == 200:
            available_models = [m['name'] for m in response.json().get('models', [])]
            
            if model_name not in available_models:
                return jsonify({'error': f'Model {model_name} is not available'}), 400
            
            # Save the selected model
            db.update_setting('ollama_model', model_name)
            
            # Update the music search service to use the new model
            global music_search_service
            music_search_service.selected_model = model_name
            
            logger.info(f"Ollama model changed to: {model_name}")
            
            return jsonify({
                'message': f'Model changed to {model_name}',
                'selected_model': model_name
            })
        else:
            return jsonify({'error': 'Cannot verify model availability'}), 500
            
    except Exception as e:
        logger.error(f"Error selecting Ollama model: {e}")
        return jsonify({'error': str(e)}), 500

# Health check
@app.route('/health')
def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        stats = db.get_statistics()
        
        return jsonify({
            'status': 'healthy',
            'party': PARTY_CONFIG['title'],
            'uptime': datetime.now().isoformat(),
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

if __name__ == '__main__':
    print("🎉 Starting Party Memory Wall Backend")
    print(f"🎂 {PARTY_CONFIG['title']}")
    print("=" * 50)
    print("Running on port 8000 for Firefox compatibility")
    print("Frontend URL: http://localhost:8000")
    print("Upload URL: http://localhost:8000/upload")
    print("API Docs: http://localhost:8000/health")
    print("=" * 50)
    
    # Run Flask-SocketIO app
    socketio.run(
        app, 
        host='0.0.0.0', 
        port=8000,  # Changed to 8000 for Firefox compatibility
        debug=True,
        allow_unsafe_werkzeug=True  # For development
    )