#!/bin/bash

# STEP CAD Viewer - Setup Script
# This script sets up the entire project including all dependencies

set -e  # Exit on error

echo "========================================="
echo "STEP CAD Viewer - Setup Script"
echo "========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}Docker is not installed. Please install Docker first.${NC}"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}Docker Compose is not installed. Please install Docker Compose first.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ Docker and Docker Compose are installed${NC}"
}

# Setup backend
setup_backend() {
    echo ""
    echo -e "${YELLOW}Setting up Python backend...${NC}"
    
    cd "$PROJECT_ROOT/backend"
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        echo "Creating Python virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    echo "Upgrading pip..."
    pip install --upgrade pip
    
    # Install requirements
    echo "Installing Python dependencies..."
    pip install -r requirements.txt
    
    # Note about pythonOCC
    echo ""
    echo -e "${YELLOW}Note: pythonOCC (OpenCASCADE) needs to be installed separately for full geometry support${NC}"
    echo "Install with: pip install pythonocc-core==7.8.1"
    echo "(This may require additional system dependencies)"
    echo ""
    
    cd ..
    
    echo -e "${GREEN}✓ Backend setup complete${NC}"
}

# Setup frontend
setup_frontend() {
    echo ""
    echo -e "${YELLOW}Setting up React frontend...${NC}"
    
    cd "$PROJECT_ROOT/frontend"
    
    # Install npm dependencies
    echo "Installing npm dependencies..."
    npm install
    
    cd ..
    
    echo -e "${GREEN}✓ Frontend setup complete${NC}"
}

# Create necessary directories
create_directories() {
    echo ""
    echo -e "${YELLOW}Creating necessary directories...${NC}"
    
    # Backend directories
    mkdir -p "$PROJECT_ROOT/backend/uploads"
    mkdir -p "$PROJECT_ROOT/backend/app/logs"
    
    # Create .gitkeep files
    touch "$PROJECT_ROOT/backend/app/logs/.gitkeep"
    touch "$PROJECT_ROOT/backend/uploads/.gitkeep"
    
    echo -e "${GREEN}✓ Directories created${NC}"
}

# Start services
start_services() {
    echo ""
    echo -e "${YELLOW}Starting Docker services...${NC}"
    echo "This may take a few minutes on first run..."
    echo ""
    
    cd "$PROJECT_ROOT"
    docker-compose up -d
    
    echo ""
    echo -e "${GREEN}✓ Services started successfully!${NC}"
}

# Display usage information
show_info() {
    echo ""
    echo "========================================="
    echo -e "${GREEN}Setup Complete!${NC}"
    echo "========================================="
    echo ""
    echo "Services are now running:"
    echo "  - Frontend:  http://localhost:3000"
    echo "  - Backend API: http://localhost:8283"
    echo "  - API Docs: http://localhost:8283/api/docs"
    echo "  - MinIO Console: http://localhost:9001"
    echo ""
    echo "Useful commands:"
    echo "  - View logs: docker-compose logs -f"
    echo "  - Stop services: docker-compose down"
    echo "  - Restart services: docker-compose restart"
    echo ""
    echo "Development mode:"
    echo "  Backend: cd backend && source venv/bin/activate && uvicorn app.main:app --reload"
    echo "  Frontend: cd frontend && npm run dev"
    echo ""
    echo -e "${YELLOW}Next steps:${NC}"
    echo "1. Upload a STEP file through the web interface"
    echo "2. Explore the 3D model, assembly tree, and dependency graph"
    echo "3. Check the logs for detailed processing information"
    echo ""
}

# Main execution
main() {
    check_docker
    create_directories
    
    echo ""
    echo "Choose setup mode:"
    echo "1) Full setup (install all dependencies + start Docker)"
    echo "2) Development setup (install dependencies only)"
    echo "3) Start Docker services only"
    echo ""
    read -p "Enter choice [1-3]: " choice
    
    case $choice in
        1)
            setup_backend
            setup_frontend
            start_services
            show_info
            ;;
        2)
            setup_backend
            setup_frontend
            echo ""
            echo -e "${GREEN}Development setup complete!${NC}"
            echo "You can now run the services manually for development."
            ;;
        3)
            start_services
            show_info
            ;;
        *)
            echo -e "${RED}Invalid choice${NC}"
            exit 1
            ;;
    esac
}

# Run main function
main
