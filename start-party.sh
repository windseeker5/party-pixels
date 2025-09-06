#!/bin/bash

# Party Memory Wall - Startup Script
# Valérie's 50th Birthday Celebration

echo "🎉 Starting Party Memory Wall for Valérie's 50th Birthday! 🎂"
echo "=" * 60

# Check if running on Raspberry Pi
if [[ $(uname -m) == "arm"* ]] || [[ $(uname -m) == "aarch64" ]]; then
    echo "🍓 Detected Raspberry Pi - optimizing for ARM architecture"
    export DOCKER_DEFAULT_PLATFORM=linux/arm64
fi

# Create required directories
echo "📁 Creating required directories..."
mkdir -p media/photos media/videos media/music database nginx/ssl

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Generate self-signed SSL certificate for local network (if not exists)
if [ ! -f nginx/ssl/party.crt ]; then
    echo "🔒 Generating SSL certificate for local network..."
    mkdir -p nginx/ssl
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout nginx/ssl/party.key \
        -out nginx/ssl/party.crt \
        -subj "/C=US/ST=Party/L=Celebration/O=Valerie50th/CN=party.local" \
        -config <(
        echo '[distinguished_name]'
        echo '[req]'
        echo 'distinguished_name=distinguished_name'
        echo '[v3_req]'
        echo 'keyUsage=keyEncipherment,dataEncipherment'
        echo 'extendedKeyUsage=serverAuth'
        echo 'subjectAltName=@alt_names'
        echo '[alt_names]'
        echo 'DNS.1=party.local'
        echo 'DNS.2=localhost'
        echo 'IP.1=192.168.1.100'  # Update with actual Pi IP
        echo 'IP.2=127.0.0.1'
        ) -extensions v3_req
fi

# Set proper permissions
chmod 755 media database
chmod 644 nginx/ssl/party.crt
chmod 600 nginx/ssl/party.key

# Stop existing containers
echo "🛑 Stopping existing party containers..."
docker-compose -f docker-compose-party.yml down --remove-orphans

# Build and start containers
echo "🚀 Building and starting Party Memory Wall..."
docker-compose -f docker-compose-party.yml up --build -d

# Wait for services to be healthy
echo "⏳ Waiting for services to start..."
sleep 10

# Check service health
echo "🏥 Checking service health..."
if curl -sf http://localhost:6000/health > /dev/null; then
    echo "✅ Flask backend is healthy"
else
    echo "❌ Flask backend health check failed"
fi

if curl -sf http://localhost/health > /dev/null 2>&1; then
    echo "✅ NGINX proxy is healthy"
else
    echo "⚠️  NGINX proxy may still be starting"
fi

# Display access information
echo ""
echo "🎊 Party Memory Wall is Ready! 🎊"
echo "=" * 50
echo "🎂 Valérie's 50th Birthday Celebration"
echo ""
echo "📱 Upload Interface: http://localhost/upload"
echo "📺 Big Screen Display: http://localhost/"
echo "🔧 Backend API: http://localhost:6000/api/config"
echo "💾 Health Check: http://localhost:6000/health"
echo ""
echo "📡 Network Access:"
echo "   - Local WiFi: http://$(hostname -I | awk '{print $1}')"
echo "   - Party Network: http://party.local"
echo ""
echo "🎵 Features Ready:"
echo "   ✅ Photo uploads (JPG, PNG, HEIC)"
echo "   ✅ Video uploads (MP4, MOV, WebM)"  
echo "   ✅ Music uploads (MP3, M4A, WAV)"
echo "   ✅ Real-time slideshow updates"
echo "   ✅ Guest attribution tracking"
echo "   ✅ QR code sharing"
echo "   ✅ Mobile-optimized interface"
echo ""
echo "🎉 Ready for 100+ guests!"
echo "🎂 Happy 50th Birthday Valérie!"
echo "=" * 50

# Show container status
echo ""
echo "📊 Container Status:"
docker-compose -f docker-compose-party.yml ps

# Follow logs (optional)
if [[ "$1" == "--logs" ]]; then
    echo ""
    echo "📋 Following container logs (Ctrl+C to stop):"
    docker-compose -f docker-compose-party.yml logs -f
fi