#!/bin/bash

# Quick Start Script for STEP CAD Viewer
# This script starts the application quickly

set -e

echo "🚀 Starting STEP CAD Viewer..."
echo ""

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✓ Docker and Docker Compose found"
echo ""

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p backend/uploads
mkdir -p backend/app/logs
touch backend/app/logs/.gitkeep
touch backend/uploads/.gitkeep
echo "✓ Directories created"
echo ""

# Check if requirements.txt exists
if [ ! -f "backend/requirements.txt" ]; then
    echo "❌ requirements.txt not found in backend directory!"
    exit 1
fi

echo "✓ Requirements file found"
echo ""

# Start Docker services
echo "🐳 Starting Docker services..."
echo "This may take a few minutes on first run..."
echo ""

docker-compose up -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service status
echo ""
echo "📊 Service Status:"
docker-compose ps

echo ""
echo "========================================="
echo "✅ STEP CAD Viewer is starting up!"
echo "========================================="
echo ""
echo "Services:"
echo "  🌐 Frontend:  http://localhost:3000"
echo "  🔌 Backend API: http://localhost:8283"
echo "  📖 API Docs: http://localhost:8283/api/docs"
echo "  🌐 Nginx Proxy: http://localhost:8080"
echo "  💾 MinIO Console: http://localhost:9001"
echo ""

echo "Next steps:"
echo "  1. Wait ~30 seconds for all services to fully start"
echo "  2. Open http://localhost:3000 in your browser"
echo "  3. Click 'Upload STEP File' and select a .step or .stp file"
echo ""
echo "Useful commands:"
echo "  - View logs: docker-compose logs -f"
echo "  - Stop services: docker-compose down"
echo "  - Restart: docker-compose restart"
echo ""
echo "To stop the services, press Ctrl+C or run:"
echo "  docker-compose down"
echo ""
