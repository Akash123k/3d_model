#!/bin/bash
# Database migration script to add model_meshes table

set -e

echo "🚀 Running database migration for mesh storage..."
echo ""

# Get the container name
CONTAINER_NAME="step-cad-db"

# Check if container is running
if ! docker ps | grep -q "$CONTAINER_NAME"; then
    echo "❌ Error: Database container '$CONTAINER_NAME' is not running"
    echo "Please start the containers with: docker-compose up -d"
    exit 1
fi

echo "✅ Database container found"
echo ""

# SQL commands to create the mesh table
SQL_COMMAND="
-- Create model_meshes table for persistent mesh storage
CREATE TABLE IF NOT EXISTS model_meshes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id UUID NOT NULL REFERENCES models(id) ON DELETE CASCADE,
    face_id VARCHAR(100) NOT NULL,
    surface_type VARCHAR(100) NOT NULL,
    solid_index INTEGER,
    shell_index INTEGER,
    face_index INTEGER,
    vertices JSONB NOT NULL,
    normals JSONB,
    indices JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_mesh_model_id ON model_meshes(model_id);
CREATE INDEX IF NOT EXISTS idx_mesh_face_id ON model_meshes(face_id);
CREATE INDEX IF NOT EXISTS idx_mesh_surface_type ON model_meshes(surface_type);

-- Add comment to table
COMMENT ON TABLE model_meshes IS 'Stores triangulated mesh data for 3D visualization';
COMMENT ON COLUMN model_meshes.model_id IS 'Reference to parent model';
COMMENT ON COLUMN model_meshes.face_id IS 'Unique identifier for the face';
COMMENT ON COLUMN model_meshes.surface_type IS 'Type of surface (PLANE, CYLINDRICAL, etc.)';
COMMENT ON COLUMN model_meshes.vertices IS 'Array of vertex coordinates [x1,y1,z1,x2,y2,z2,...]';
COMMENT ON COLUMN model_meshes.normals IS 'Array of normal vectors';
COMMENT ON COLUMN model_meshes.indices IS 'Triangle indices for mesh rendering';

-- Verify table creation
SELECT COUNT(*) as mesh_table_count FROM model_meshes;

-- Show existing tables
\\dt
"

# Execute SQL commands
echo "📝 Executing SQL commands..."
docker exec -i "$CONTAINER_NAME" psql -U postgres -d step_cad_viewer <<EOF
$SQL_COMMAND
EOF

echo ""
echo "✅ Migration completed successfully!"
echo ""
echo "📊 Next steps:"
echo "   1. Restart backend container to pick up new model changes"
echo "   2. Upload a new STEP file to test mesh persistence"
echo "   3. Verify meshes are saved to database"
echo ""
echo "🔍 Verification commands:"
echo "   docker exec step-cad-db psql -U postgres -d step_cad_viewer -c 'SELECT COUNT(*) FROM model_meshes;'"
echo "   docker logs step-cad-backend | grep meshes_saved"
