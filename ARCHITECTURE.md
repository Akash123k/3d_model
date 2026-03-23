# Architecture & Deployment Guide

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         USER BROWSER                        │
│                     http://localhost:3000                   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                      NGINX REVERSE PROXY                    │
│                         Port 80                             │
│  ┌──────────────────────────┬──────────────────────────┐   │
│  │   Frontend Proxy         │    Backend API Proxy     │   │
│  │   :5173                  │    :8283                 │   │
│  └──────────────────────────┴──────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                         │
         ┌───────────────┴───────────────┐
         │                               │
         ▼                               ▼
┌─────────────────────────┐   ┌─────────────────────────┐
│    FRONTEND SERVICE     │   │    BACKEND SERVICE      │
│   React + TypeScript    │   │   FastAPI + Python      │
│       Port 5173         │   │       Port 8283         │
│                         │   │                         │
│  ┌──────────────────┐   │   │  ┌──────────────────┐   │
│  │  Three.js/R3F    │   │   │  │  STEP Parser     │   │
│  │  D3.js Graphs    │   │   │  │  Dependency Graph│   │
│  │  Zustand Store   │   │   │  │  Model Processor │   │
│  │  TailwindCSS     │   │   │  │  Statistics      │   │
│  └──────────────────┘   │   │  └──────────────────┘   │
│                         │   │                         │
│  Components:            │   │  Services:              │
│  - FileUpload          │   │  - step_parser.py       │
│  - Viewer3D            │   │  - dependency_graph.py  │
│  - AssemblyTree        │   │  - model_processor.py   │
│  - GeometryExplorer    │   │                         │
│  - DependencyGraph     │   │  API Routes:            │
│  - StatsDashboard      │   │  - /api/upload          │
│                         │   │  - /api/models/*        │
└─────────────────────────┘   └───────────┬─────────────┘
                                          │
                              ┌───────────┴─────────────┐
                              │                         │
                              ▼                         ▼
                    ┌──────────────────┐      ┌──────────────────┐
                    │   REDIS CACHE    │      │    MINIO S3      │
                    │    Port 6366     │      │    Port 9000     │
                    │                  │      │                  │
                    │  - Model Cache   │      │  - STEP Files    │
                    │  - Session Data  │      │  - Generated     │
                    │  - TTL: 24h      │      │    Meshes        │
                    └──────────────────┘      └──────────────────┘
```

## Data Flow Architecture

### File Upload Flow

```
User → Frontend → Nginx → Backend → MinIO Storage
                           ↓
                       Parse STEP
                           ↓
                    Extract Entities
                           ↓
                  Build Dependency Graph
                           ↓
                   Calculate Statistics
                           ↓
                    Cache in Redis
                           ↓
                   Return Model ID
```

### Model Retrieval Flow

```
User Request → Frontend → Nginx → Backend
                                   ↓
                            Check Redis Cache
                                   ↓
                            ┌──────┴──────┐
                            │             │
                          Hit           Miss
                            │             │
                            │             ↓
                            │      Load from MinIO
                            │             ↓
                            │      Process Data
                            │             ↓
                            │      Cache Result
                            │             │
                            └──────┬──────┘
                                   ↓
                            Return JSON Response
```

## Component Architecture

### Backend Layers

```
┌─────────────────────────────────────────┐
│          API Layer (FastAPI)            │
│  ┌─────────────────────────────────┐   │
│  │  Routes: upload.py, model.py    │   │
│  │  - Request Validation           │   │
│  │  - Response Serialization       │   │
│  │  - Error Handling               │   │
│  └─────────────────────────────────┘   │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         Service Layer                   │
│  ┌─────────────────────────────────┐   │
│  │  - STEPParser                   │   │
│  │  - DependencyGraphBuilder       │   │
│  │  - ModelProcessor               │   │
│  │  - Business Logic               │   │
│  └─────────────────────────────────┘   │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         Data Layer                      │
│  ┌─────────────────────────────────┐   │
│  │  - Redis Client (Cache)         │   │
│  │  - MinIO Client (Storage)       │   │
│  │  - File System (Uploads)        │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

### Frontend Layers

```
┌─────────────────────────────────────────┐
│         Presentation Layer              │
│  ┌─────────────────────────────────┐   │
│  │  Components (JSX/TSX)           │   │
│  │  - FileUpload                   │   │
│  │  - Viewer3D                     │   │
│  │  - AssemblyTree                 │   │
│  │  - GeometryExplorer             │   │
│  │  - DependencyGraph              │   │
│  │  - StatsDashboard               │   │
│  └─────────────────────────────────┘   │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         State Management                │
│  ┌─────────────────────────────────┐   │
│  │  Zustand Stores                 │   │
│  │  - modelStore                   │   │
│  │  - viewerStore                  │   │
│  │  - uiStore                      │   │
│  └─────────────────────────────────┘   │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         Custom Hooks                    │
│  ┌─────────────────────────────────┐   │
│  │  - useFileUpload                │   │
│  │  - useModelLoader               │   │
│  │  - useAssemblyTree              │   │
│  │  - useDependencyGraph           │   │
│  │  - useStatistics                │   │
│  └─────────────────────────────────┘   │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         API Client Layer                │
│  ┌─────────────────────────────────┐   │
│  │  Axios Instance                 │   │
│  │  - Interceptors                 │   │
│  │  - Type-safe Functions          │   │
│  │  - Error Handling               │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

## Directory Structure Deep Dive

```
3d_model/
│
├── backend/                      # Python Backend
│   ├── app/
│   │   ├── __init__.py          # Package init
│   │   ├── main.py              # FastAPI entry point
│   │   ├── config.py            # Configuration management
│   │   │
│   │   ├── api/                 # API Layer
│   │   │   ├── __init__.py
│   │   │   ├── dependencies.py  # Dependency injection
│   │   │   └── routes/
│   │   │       ├── __init__.py
│   │   │       ├── upload.py    # File upload endpoints
│   │   │       └── model.py     # Model data endpoints
│   │   │
│   │   ├── core/                # Core Utilities
│   │   │   ├── __init__.py
│   │   │   ├── logging.py       # Structured logging setup
│   │   │   └── exceptions.py    # Custom exceptions
│   │   │
│   │   ├── models/              # Data Models
│   │   │   ├── __init__.py
│   │   │   └── schemas.py       # Pydantic schemas
│   │   │
│   │   ├── services/            # Business Logic
│   │   │   ├── __init__.py
│   │   │   ├── step_parser.py       # STEP file parsing
│   │   │   ├── dependency_graph.py  # Graph building
│   │   │   └── model_processor.py   # Orchestration
│   │   │
│   │   ├── utils/               # Utilities
│   │   │   └── __init__.py
│   │   │
│   │   └── logs/                # Log Files
│   │       ├── .gitkeep
│   │       ├── app.log          # Application events
│   │       ├── access.log       # HTTP requests
│   │       └── processing.log   # Processing details
│   │
│   ├── uploads/                 # Uploaded Files
│   ├── requirements.txt         # Python dependencies
│   └── Dockerfile              # Backend container
│
├── frontend/                    # React Frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── common/
│   │   │   │   └── FileUpload.tsx
│   │   │   ├── viewer/
│   │   │   │   └── Viewer3D.tsx
│   │   │   ├── tree/
│   │   │   │   └── AssemblyTree.tsx
│   │   │   ├── geometry/
│   │   │   │   └── GeometryExplorer.tsx
│   │   │   ├── graph/
│   │   │   │   └── DependencyGraph.tsx
│   │   │   └── dashboard/
│   │   │       └── StatsDashboard.tsx
│   │   │
│   │   ├── store/
│   │   │   └── index.ts         # Zustand stores
│   │   │
│   │   ├── hooks/
│   │   │   └── index.ts         # Custom hooks
│   │   │
│   │   ├── utils/
│   │   │   └── api.ts           # API client
│   │   │
│   │   ├── App.tsx              # Main component
│   │   ├── main.tsx             # Entry point
│   │   └── styles/
│   │       └── index.css        # Global styles
│   │
│   ├── package.json            # Node dependencies
│   ├── vite.config.ts          # Vite configuration
│   ├── tsconfig.json           # TypeScript config
│   ├── tailwind.config.js      # Tailwind config
│   └── Dockerfile              # Frontend container
│
├── nginx/                       # Reverse Proxy
│   ├── nginx.conf              # Nginx configuration
│   └── Dockerfile              # Nginx container
│
├── scripts/                     # Automation Scripts
│   └── setup.sh                # Setup automation
│
├── docker-compose.yml           # Docker orchestration
├── .env                         # Environment variables
├── .gitignore                   # Git ignore rules
├── README.md                    # Main documentation
├── QUICKSTART.md                # Quick start guide
├── INSTALLATION.md              # Installation guide
├── PROJECT_SUMMARY.md           # Project summary
└── ARCHITECTURE.md              # This file
```

## Network Architecture

### Docker Networks

```
step-cad-network (bridge)
├── step-cad-backend    (172.x.x.x:8283)
├── step-cad-frontend   (172.x.x.x:5173)
├── step-cad-nginx      (172.x.x.x:80)
├── step-cad-redis      (172.x.x.x:6366)
└── step-cad-minio      (172.x.x.x:9000)
```

### Port Mapping

| Service | Internal | External | Purpose |
|---------|----------|----------|---------|
| Backend | 8283 | 8283 | FastAPI server |
| Frontend | 5173 | 3000 | Vite dev server |
| Nginx | 80 | 80 | Reverse proxy |
| Redis | 6366 | 6366 | Cache layer |
| MinIO | 9000 | 9000 | Object storage |
| MinIO Console | 9001 | 9001 | Web UI |

## Security Architecture

### Layers of Security

```
┌─────────────────────────────────────┐
│   File Upload Validation            │
│   - Extension checking              │
│   - Size limits (50MB)              │
│   - Content type validation         │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│   Input Sanitization                │
│   - Pydantic validation             │
│   - SQL injection prevention        │
│   - XSS prevention                  │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│   CORS Configuration                │
│   - Allowed origins                 │
│   - Credential handling             │
│   - Method restrictions             │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│   Container Isolation               │
│   - Network segmentation            │
│   - Volume permissions              │
│   - Resource limits                 │
└─────────────────────────────────────┘
```

## Scalability Considerations

### Horizontal Scaling

```
Load Balancer
    ├── Backend Instance 1 + Redis
    ├── Backend Instance 2 + Redis
    └── Backend Instance N + Redis
              │
              ▼
        Shared MinIO Storage
```

### Vertical Scaling

- Increase container resources (CPU, RAM)
- Optimize database queries
- Implement connection pooling
- Use async operations

### Caching Strategy

```
L1: Browser Cache (static assets)
L2: CDN Cache (global distribution)
L3: Nginx Cache (reverse proxy)
L4: Redis Cache (application data)
L5: Database Cache (query results)
```

## Monitoring & Observability

### Logging Stack

```
Application Logs → File → Log Aggregator → Dashboard
Access Logs      → File → Log Aggregator → Analytics
Processing Logs  → File → Log Aggregator → Alerts
```

### Metrics to Monitor

- Request rate (RPS)
- Response time (p50, p95, p99)
- Error rate (4xx, 5xx)
- Cache hit ratio
- File upload size distribution
- Processing time per model
- Memory usage
- CPU utilization

### Health Checks

```yaml
backend: /api/health
redis: PING command
minio: /minio/health/live
```

## Deployment Strategies

### Development

```bash
docker-compose up -d
# Hot reload enabled
# Debug logging
# Local development tools
```

### Staging

```bash
docker-compose -f docker-compose.staging.yml up -d
# Production-like environment
# Realistic data volumes
# Performance testing
```

### Production

```bash
docker-compose -f docker-compose.prod.yml up -d
# Optimized settings
# SSL/TLS enabled
# Monitoring tools
# Backup systems
```

## Disaster Recovery

### Backup Strategy

```
Daily:   Database dumps
Hourly:  Redis snapshots
Weekly:  Full system backup
Monthly: Archive old backups
```

### Recovery Procedures

1. **Service Failure**: Restart containers
2. **Data Loss**: Restore from backup
3. **Corruption**: Rollback to previous version
4. **Security Breach**: Isolate, investigate, patch

## Performance Optimization

### Backend Optimizations

- Async/await for I/O operations
- Connection pooling
- Query optimization
- Response compression
- Streaming for large files

### Frontend Optimizations

- Code splitting
- Lazy loading
- Image optimization
- CDN for static assets
- Service workers

### Infrastructure Optimizations

- SSD storage
- Adequate RAM
- Multi-core CPUs
- Network optimization
- Load balancing

## Future Enhancements

### Phase 2 Architecture

```
Add:
├── Celery Workers (async tasks)
├── PostgreSQL (persistent data)
├── Elasticsearch (search functionality)
└── WebSocket Server (real-time updates)
```

### Phase 3 Architecture

```
Add:
├── Authentication Service
├── User Management
├── Collaboration Features
└── Advanced Analytics
```

---

**Architecture Version**: 1.0  
**Last Updated**: March 2026  
**Maintained By**: Development Team
