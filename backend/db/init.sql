-- Database initialization script for STEP CAD Viewer
-- Creates tables, indexes, and initial data

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Models table - stores uploaded model metadata
CREATE TABLE IF NOT EXISTS models (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size BIGINT NOT NULL,
    upload_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) NOT NULL DEFAULT 'processing',
    entities_count INTEGER DEFAULT 0,
    cache_key VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Statistics table - stores model statistics
CREATE TABLE IF NOT EXISTS model_statistics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_id UUID NOT NULL REFERENCES models(id) ON DELETE CASCADE,
    total_solids INTEGER DEFAULT 0,
    total_faces INTEGER DEFAULT 0,
    total_edges INTEGER DEFAULT 0,
    total_vertices INTEGER DEFAULT 0,
    total_surfaces INTEGER DEFAULT 0,
    min_x DOUBLE PRECISION,
    min_y DOUBLE PRECISION,
    min_z DOUBLE PRECISION,
    max_x DOUBLE PRECISION,
    max_y DOUBLE PRECISION,
    max_z DOUBLE PRECISION,
    dimensions_x DOUBLE PRECISION,
    dimensions_y DOUBLE PRECISION,
    dimensions_z DOUBLE PRECISION,
    total_volume DOUBLE PRECISION,
    total_surface_area DOUBLE PRECISION,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Assembly trees table - stores hierarchical structure
CREATE TABLE IF NOT EXISTS assembly_trees (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_id UUID NOT NULL REFERENCES models(id) ON DELETE CASCADE,
    root_node JSONB NOT NULL,
    total_nodes INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Dependency graphs table - stores entity relationships
CREATE TABLE IF NOT EXISTS dependency_graphs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_id UUID NOT NULL REFERENCES models(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Graph nodes table
CREATE TABLE IF NOT EXISTS graph_nodes (
    id VARCHAR(50) NOT NULL,
    graph_id UUID NOT NULL REFERENCES dependency_graphs(id) ON DELETE CASCADE,
    label VARCHAR(255) NOT NULL,
    type VARCHAR(100) NOT NULL,
    properties JSONB,
    "references" TEXT[] DEFAULT '{}',
    referenced_by TEXT[] DEFAULT '{}',
    PRIMARY KEY (id, graph_id)
);

-- Graph edges table
CREATE TABLE IF NOT EXISTS graph_edges (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    graph_id UUID NOT NULL REFERENCES dependency_graphs(id) ON DELETE CASCADE,
    source VARCHAR(50) NOT NULL,
    target VARCHAR(50) NOT NULL,
    relationship VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Entities table - stores raw entity data
CREATE TABLE IF NOT EXISTS entities (
    id VARCHAR(50) NOT NULL,
    model_id UUID NOT NULL REFERENCES models(id) ON DELETE CASCADE,
    entity_type VARCHAR(100) NOT NULL,
    attributes JSONB,
    "references" TEXT[] DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id, model_id)
);

-- Create indexes for better query performance
CREATE INDEX idx_models_status ON models(status);
CREATE INDEX idx_models_upload_time ON models(upload_time DESC);
CREATE INDEX idx_models_cache_key ON models(cache_key);

CREATE INDEX idx_model_statistics_model_id ON model_statistics(model_id);

CREATE INDEX idx_assembly_trees_model_id ON assembly_trees(model_id);

CREATE INDEX idx_dependency_graphs_model_id ON dependency_graphs(model_id);
CREATE INDEX idx_graph_nodes_graph_id ON graph_nodes(graph_id);
CREATE INDEX idx_graph_edges_graph_id ON graph_edges(graph_id);
CREATE INDEX idx_graph_edges_source_target ON graph_edges(graph_id, source, target);

CREATE INDEX idx_entities_model_id ON entities(model_id);
CREATE INDEX idx_entities_type ON entities(entity_type);
CREATE INDEX idx_entities_attributes ON entities USING GIN(attributes);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update updated_at
CREATE TRIGGER update_models_updated_at BEFORE UPDATE ON models
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Comments for documentation
COMMENT ON TABLE models IS 'Uploaded STEP files metadata';
COMMENT ON TABLE model_statistics IS 'Statistics calculated from STEP files';
COMMENT ON TABLE assembly_trees IS 'Hierarchical assembly structure';
COMMENT ON TABLE dependency_graphs IS 'Entity dependency relationships';
COMMENT ON TABLE graph_nodes IS 'Nodes in dependency graphs';
COMMENT ON TABLE graph_edges IS 'Edges connecting graph nodes';
COMMENT ON TABLE entities IS 'Raw STEP file entities';
