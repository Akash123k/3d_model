# STEP CAD Viewer Application

A full-stack web application for visualizing and analyzing STEP (.step/.stp) CAD files with 3D viewing, assembly tree exploration, geometry analysis, and dependency graph visualization.

## Features

### 1. **3D Model Viewer**
- Interactive 3D rendering with Three.js
- Rotate, zoom, and pan controls
- Part selection and highlighting
- Exploded view visualization
- Cross-section tool

### 2. **Assembly Tree**
- Hierarchical structure parsing from STEP files
- Expandable/collapsible tree view
- Click-to-highlight functionality
- Parent-child relationship visualization

### 3. **Geometry Explorer**
- B-Rep topology visualization (Solid → Shell → Face → Edge → Vertex)
- Entity type identification (CARTESIAN_POINT, EDGE_CURVE, ADVANCED_FACE, etc.)
- Detailed metadata display

### 4. **Dependency Graph**
- Visual representation of STEP entity references
- Interactive graph navigation
- Entity relationship mapping
- Built with D3.js

### 5. **Model Statistics Dashboard**
- Total solids, faces, edges, vertices count
- Surface area and volume calculations
- Bounding box dimensions
- Real-time metrics

## Technology Stack

### Backend
- **Python 3.11+** with FastAPI
- **pythonOCC** (OpenCASCADE) for STEP parsing
- **Redis** for caching
- **MinIO** for file storage
- **Structlog** for structured logging

### Frontend
- **React 18** with TypeScript
- **Vite** for build tooling
- **Three.js** with React Three Fiber
- **Zustand** for state management
- **D3.js** for graph visualization
- **TailwindCSS** for styling

### Infrastructure
- **Docker** & **Docker Compose**
- **Nginx** as reverse proxy

## Quick Start

### Prerequisites
- Docker (version 20.10 or higher)
- Docker Compose (version 2.0 or higher)
- Git

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd 3d_model
```

2. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env if needed
```

3. **Start all services**
```bash
docker-compose up -d
```

4. **Access the application**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8283
- API Documentation: http://localhost:8283/api/docs
- MinIO Console: http://localhost:9001

### Development Mode

For development with hot-reload:

```bash
# Start backend only
docker-compose up backend

# In another terminal, start frontend
cd frontend
npm install
npm run dev
```

## Project Structure

```
3d_model/
├── backend/                 # Python/FastAPI backend
│   ├── app/
│   │   ├── api/            # API routes
│   │   ├── core/           # Core utilities (logging, exceptions)
│   │   ├── models/         # Pydantic schemas
│   │   ├── services/       # Business logic
│   │   └── main.py         # FastAPI entry point
│   ├── uploads/            # Uploaded STEP files
│   └── logs/               # Application logs
│
├── frontend/               # React/TypeScript frontend
│   └── src/
│       ├── components/     # React components
│       ├── store/          # Zustand stores
│       ├── hooks/          # Custom hooks
│       └── utils/          # Utility functions
│
├── nginx/                  # Nginx configuration
├── docker-compose.yml      # Docker services definition
└── .env                    # Environment variables
```

## API Endpoints

### File Upload
- `POST /api/upload` - Upload STEP file

### Model Data
- `GET /api/models/{model_id}` - Get complete model data
- `GET /api/models/{model_id}/assembly-tree` - Get assembly structure
- `GET /api/models/{model_id}/dependency-graph` - Get entity dependency graph
- `GET /api/models/{model_id}/statistics` - Get model statistics
- `GET /api/models/{model_id}/entity/{entity_id}` - Get entity details

### Health Check
- `GET /api/health` - Health check endpoint

## Logging

The application generates three log files in `backend/app/logs/`:

1. **app.log** - Application events (INFO, WARNING, ERROR)
2. **access.log** - HTTP request logging
3. **processing.log** - STEP file processing details

Logs are in JSON format for easy parsing and include timestamps and correlation IDs.

## Usage Guide

### 1. Upload a STEP File
- Click the "Upload" button in the top toolbar
- Select a `.step` or `.stp` file (max 50MB)
- Wait for processing to complete

### 2. Explore the Model
- **Left Panel**: Navigate the assembly tree
- **Center**: Interact with the 3D model
- **Right Panel**: Explore geometry details
- **Bottom**: View dependency graph

### 3. Advanced Features
- **Exploded View**: Toggle to see parts separated
- **Cross Section**: Enable to slice through the model
- **Part Selection**: Click on any part to highlight and view details

## Configuration

### Environment Variables

Key variables in `.env`:

```bash
# Backend
ENVIRONMENT=development
LOG_LEVEL=DEBUG
MAX_UPLOAD_SIZE=52428800  # 50MB

# Redis
REDIS_URL=redis://redis:6366/0

# MinIO
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
```

## Troubleshooting

### Common Issues

**Backend won't start:**
```bash
docker-compose logs backend
```

**Frontend can't connect to backend:**
- Ensure both containers are running
- Check CORS settings in `.env`

**File upload fails:**
- Verify file size is under limit
- Check file extension (.step or .stp)
- Review `backend/app/logs/app.log`

### Viewing Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

## Development

### Adding Dependencies

**Backend:**
```bash
echo "package-name==version" >> backend/requirements.txt
docker-compose restart backend
```

**Frontend:**
```bash
cd frontend
npm install package-name
```

### Running Tests

```bash
# Backend tests (to be implemented)
docker-compose exec backend pytest

# Frontend tests (to be implemented)
docker-compose exec frontend npm test
```

## Limitations

Current version uses simplified STEP parsing without pythonOCC integration. For full geometry extraction and accurate B-Rep analysis:

1. Install pythonOCC in backend Dockerfile:
```dockerfile
RUN pip install pythonocc-core==7.8.1
```

2. Update services to use OCC for:
- Accurate mesh generation
- Precise volume/area calculations
- Proper assembly structure parsing

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - See LICENSE file for details

## Support

For issues and questions:
- GitHub Issues: [Create an issue]
- Email: support@example.com

## Acknowledgments

- OpenCASCADE for STEP file processing capabilities
- Three.js community for excellent 3D rendering tools
- FastAPI framework for modern Python web development

---

**Version:** 1.0.0  
**Last Updated:** March 2026
# 3d_model
