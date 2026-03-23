                                              import React, { useState, useEffect } from 'react';
import { useModelStore } from '../../store';
import { getBRepGeometry, BRepGeometryResponse } from '../../utils/api';

interface TreeNode {
  id: string;
  name: string;
  type: string;
  children?: TreeNode[];
  properties?: any;
  label?: string;
  depth?: number;
  coords?: number[];
}

const GeometryExplorer: React.FC = () => {
  const { currentModel } = useModelStore();
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set(['brep_root']));
  const [brepData, setBrepData] = useState<BRepGeometryResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch B-Rep geometry data on mount or when model changes
  useEffect(() => {
    const fetchBRepData = async () => {
      if (!currentModel?.model_id) return;
      
      setLoading(true);
      setError(null);
      
      try {
        const data = await getBRepGeometry(currentModel.model_id);
        setBrepData(data);
        console.log('[B-Rep Geometry] Data loaded:', data);
      } catch (err: any) {
        console.error('[B-Rep Geometry] Failed to load:', err);
        setError(err.response?.data?.detail || 'Failed to load B-Rep geometry');
      } finally {
        setLoading(false);
      }
    };

    fetchBRepData();
  }, [currentModel?.model_id]);

  if (!currentModel || !currentModel.statistics) {
    return (
      <div className="p-4">
        <h3 className="font-bold mb-2">Geometry Explorer (B-Rep Structure)</h3>
        <p className="text-sm text-gray-400">No geometry data available</p>
      </div>
    );
  }

  const stats = currentModel.statistics;
  const brepHierarchy = currentModel.brep_hierarchy;

  // Toggle node expansion
  const toggleNode = (nodeId: string) => {
    const newExpanded = new Set(expandedNodes);
    if (newExpanded.has(nodeId)) {
      newExpanded.delete(nodeId);
    } else {
      newExpanded.add(nodeId);
    }
    setExpandedNodes(newExpanded);
  };

  // Render tree node recursively
  const renderTreeNode = (node: TreeNode, level: number = 0) => {
    const isExpanded = expandedNodes.has(node.id);
    const hasChildren = node.children && node.children.length > 0;
    const paddingLeft = `${level * 16 + 8}px`;

    // Icons based on type
    const getIcon = (type: string) => {
      switch (type) {
        case 'BREP_MODEL': return '📦';
        case 'SOLID': return '🔷';
        case 'SHELL': return '🔶';
        case 'FACE': return '▢';
        case 'EDGE_GROUP': return '┅';
        case 'EDGE': return '╌';
        case 'VERTEX': return '•';
        default: return '◼';
      }
    };

    // Get meaningful label based on entity type and properties
    const getMeaningfulLabel = (node: TreeNode): string => {
      const props = node.properties || {};
      
      // For brep.py-style nodes with coordinates
      if (node.coords && node.coords.length === 3) {
        return `${node.name} (${node.coords[0].toFixed(2)}, ${node.coords[1].toFixed(2)}, ${node.coords[2].toFixed(2)})`;
      }
      
      switch (node.type) {
        case 'FACE': {
          const surfaceType = props.surface_type 
            ? props.surface_type.replace(/_/g, ' ').replace('SURFACE', '') 
            : 'Face';
          const edgeCount = props.edge_count || node.properties?.statistics?.total_edges || 0;
          return `${surfaceType} (${edgeCount} edges)`;
        }
        case 'EDGE': {
          const curveTypeRaw = props.curve_type || 'EDGE';
          const curveType = curveTypeRaw.replace(/_/g, ' ');
          const length = props.length;
          return length ? `${curveType} (L: ${length.toFixed(2)})` : curveType;
        }
        case 'VERTEX': {
          const coords = typeof props.coordinates === 'string' 
            ? props.coordinates 
            : null;
          return coords || `Vertex`;
        }
        default:
          return node.name;
      }
    };

    // Color based on type
    const getBgColor = (type: string) => {
      switch (type) {
        case 'BREP_MODEL': return 'bg-purple-700';
        case 'SOLID': return 'bg-blue-700';
        case 'SHELL': return 'bg-indigo-700';
        case 'FACE': return 'bg-teal-700';
        case 'EDGE_GROUP': return 'bg-orange-700';
        case 'EDGE': return 'bg-gray-700';
        case 'VERTEX': return 'bg-gray-800';
        default: return 'bg-gray-700';
      }
    };

    return (
      <div key={node.id}>
        <div
          className={`flex items-center justify-between p-2 rounded cursor-pointer hover:opacity-80 transition ${getBgColor(node.type)}`}
          style={{ paddingLeft }}
          onClick={() => hasChildren && toggleNode(node.id)}
        >
          <div className="flex items-center gap-2 flex-1">
            {hasChildren && (
              <span className="text-xs text-gray-300">
                {isExpanded ? '▼' : '▶'}
              </span>
            )}
            {!hasChildren && <span className="w-3"></span>}
            <span className="text-base">{getIcon(node.type)}</span>
            <div className="flex flex-col flex-1">
              <span className="text-sm font-medium">{getMeaningfulLabel(node)}</span>
              {node.properties?.description && (
                <span className="text-xs text-gray-300 italic">{node.properties.description}</span>
              )}
            </div>
          </div>
          <div className="flex items-center gap-2 flex-shrink-0">
            <span className="text-xs text-gray-300 bg-black/30 px-2 py-1 rounded">
              {node.type.replace(/_/g, ' ')}
            </span>
            {node.properties?.statistics?.total_edges !== undefined && (
              <span className="text-xs bg-blue-900 px-2 py-1 rounded" title="Total edges">
                ╌ {node.properties.statistics.total_edges}
              </span>
            )}
            {node.properties?.statistics?.total_vertices !== undefined && (
              <span className="text-xs bg-green-900 px-2 py-1 rounded" title="Total vertices">
                • {node.properties.statistics.total_vertices}
              </span>
            )}
            {node.properties?.surface_type && (
              <span className="text-xs bg-purple-900 px-2 py-1 rounded" title="Surface type">
                {node.properties.surface_type.replace(/_/g, ' ').replace('SURFACE', '')}
              </span>
            )}
            {node.properties?.surface_class && (
              <span className="text-xs bg-pink-900 px-2 py-1 rounded capitalize" title="Surface class">
                {node.properties.surface_class}
              </span>
            )}
            {node.properties?.length && (
              <span className="text-xs bg-yellow-900 px-2 py-1 rounded" title="Edge length">
                L: {node.properties.length.toFixed(2)}
              </span>
            )}
          </div>
        </div>
        
        {hasChildren && isExpanded && (
          <div className="border-l-2 border-gray-600 ml-4">
            {node.children!.map(child => renderTreeNode(child, level + 1))}
          </div>
        )}
      </div>
    );
  };

  // Build root node from B-Rep hierarchy (brep.py style)
  const buildRootNode = (): TreeNode => {
    // Use new brep_tree data if available
    if (brepData && brepData.brep_tree && brepData.brep_tree.length > 0) {
      return {
        id: 'brep_root',
        name: `B-Rep Model (${brepData.total_components} Components, ${brepData.entities_count} Entities)`,
        type: 'BREP_MODEL',
        children: brepData.brep_tree.map(tree => convertBRepTreeToNode(tree)),
        properties: {
          bounding_box: brepData.bounding_box
        }
      };
    }

    // Fallback to old brep_hierarchy format
    if (!brepHierarchy || !brepHierarchy.solids || brepHierarchy.solids.length === 0) {
      return {
        id: 'no_brep',
        name: loading ? 'Loading B-Rep data...' : 'No B-Rep Data Available',
        type: 'UNKNOWN',
        children: []
      };
    }

    return {
      id: 'brep_root',
      name: `B-Rep Model (${brepHierarchy.total_solids || 0} Solids, ${brepHierarchy.total_faces || 0} Faces)`,
      type: 'BREP_MODEL',
      children: brepHierarchy.solids.map((solid: any, solidIndex: number) => ({
        id: solid.id || `solid_${solidIndex}`,
        name: solid.name || `Solid ${solidIndex + 1}`,
        type: 'SOLID',
        properties: {
          description: solid.description,
          is_closed: solid.properties?.is_closed,
          solid_type: solid.properties?.solid_type,
          statistics: solid.statistics
        },
        children: solid.shells?.map((shell: any, shellIndex: number) => ({
          id: shell.id || `solid_${solidIndex}_shell_${shellIndex}`,
          name: shell.name || `Shell ${shellIndex + 1}`,
          type: 'SHELL',
          properties: {
            description: shell.description,
            shell_type: shell.properties?.shell_type,
            statistics: shell.statistics
          },
          children: shell.faces?.map((face: any, faceIndex: number) => {
            const faceNode: TreeNode = {
              id: face.id || `solid_${solidIndex}_shell_${shellIndex}_face_${faceIndex}`,
              name: face.name || `${face.surface_type?.replace(/_/g, ' ').title() || 'Face'} ${faceIndex + 1}`,
              type: 'FACE',
              properties: {
                description: face.description,
                surface_type: face.surface_type,
                surface_class: face.properties?.surface_class,
                is_planar: face.properties?.is_planar,
                is_curved: face.properties?.is_curved,
                statistics: face.statistics || {
                  total_edges: face.edges?.length || 0,
                  total_vertices: face.vertices?.length || 0
                }
              },
              children: []
            };

            // Group edges by type
            if (face.edges && face.edges.length > 0) {
              const edgeTypes: { [key: string]: any[] } = {};
              face.edges.forEach((edge: any) => {
                const curveType = edge.curve_type || 'UNKNOWN_EDGE';
                if (!edgeTypes[curveType]) {
                  edgeTypes[curveType] = [];
                }
                edgeTypes[curveType].push(edge);
              });

              Object.entries(edgeTypes).forEach(([edgeType, edges]) => {
                const edgeGroupNode: TreeNode = {
                  id: `face_${faceIndex}_${edgeType}`,
                  name: `${edgeType.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())} (${edges.length})`,
                  type: 'EDGE_GROUP',
                  children: edges.slice(0, 10).map((edge: any, edgeIndex: number) => {
                    const edgeNode: TreeNode = {
                      id: edge.id || `face_${faceIndex}_edge_${edgeIndex}`,
                      name: edge.name || `Edge ${edgeIndex + 1}`,
                      type: 'EDGE',
                      properties: {
                        description: edge.description,
                        curve_type: edge.curve_type,
                        length: edge.properties?.length,
                        radius: edge.properties?.radius,
                        statistics: {
                          total_vertices: edge.vertices?.length || 0
                        }
                      },
                      children: []
                    };

                    // Add vertices
                    if (edge.vertices && edge.vertices.length > 0) {
                      edgeNode.children = edge.vertices.slice(0, 5).map((vertex: any, vertexIndex: number) => ({
                        id: `edge_${edgeIndex}_vertex_${vertexIndex}`,
                        name: vertex.label || `Vertex ${vertexIndex + 1}`,
                        type: 'VERTEX',
                        properties: {
                          description: 'A point in 3D space',
                          coordinates: vertex.coordinates 
                            ? `X: ${vertex.coordinates[0]?.toFixed(2)}, Y: ${vertex.coordinates[1]?.toFixed(2)}, Z: ${vertex.coordinates[2]?.toFixed(2)}`
                            : 'N/A'
                        }
                      }));
                    }

                    return edgeNode;
                  })
                };

                faceNode.children!.push(edgeGroupNode);
              });
            }

            return faceNode;
          }) || []
        })) || []
      })) || []
    };
  };

  // Convert brep.py-style tree to TreeNode format
  const convertBRepTreeToNode = (tree: any, level: number = 0): TreeNode => {
    return {
      id: tree.id,
      name: tree.label || `${tree.id} [${tree.type}]`,
      type: tree.type,
      depth: tree.depth,
      coords: tree.coords,
      children: tree.children ? tree.children.map((child: any) => convertBRepTreeToNode(child, level + 1)) : [],
      properties: {
        entity_id: tree.id,
        has_coordinates: !!tree.coords
      }
    };
  };

  const rootNode = buildRootNode();

  return (
    <div className="p-4 border-b border-gray-700">
      <h3 className="font-bold mb-4 text-lg">Geometry Explorer (B-Rep Structure)</h3>
      
      {/* Loading State */}
      {loading && (
        <div className="p-4 text-center text-yellow-400">
          <div className="animate-spin inline-block mr-2">⚙️</div>
          Loading B-Rep geometry data...
        </div>
      )}
      
      {/* Error State */}
      {error && (
        <div className="p-4 text-center text-red-400 bg-red-900/20 rounded">
          ⚠️ {error}
        </div>
      )}
      
      {/* Statistics Summary */}
      {!loading && !error && currentModel && currentModel.statistics && (
      <div className="mb-4 p-3 bg-gray-800 rounded-lg">
        <div className="grid grid-cols-4 gap-2 text-center">
          <div>
            <div className="text-2xl font-bold text-blue-400">{stats.total_solids || 0}</div>
            <div className="text-xs text-gray-400">Solids</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-green-400">{stats.total_faces || 0}</div>
            <div className="text-xs text-gray-400">Faces</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-yellow-400">{stats.total_edges || 0}</div>
            <div className="text-xs text-gray-400">Edges</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-purple-400">{stats.total_vertices || 0}</div>
            <div className="text-xs text-gray-400">Vertices</div>
          </div>
        </div>
      </div>
      )}

      {/* Hierarchy Legend */}
      <div className="mb-3 p-2 bg-gray-800 rounded text-xs">
        <div className="font-semibold mb-1">Hierarchy Structure:</div>
        <div className="flex flex-wrap gap-2">
          <span className="px-2 py-1 bg-purple-700 rounded">📦 Model</span>
          <span className="px-2 py-1 bg-blue-700 rounded">🔷 Solid</span>
          <span className="px-2 py-1 bg-indigo-700 rounded">🔶 Shell</span>
          <span className="px-2 py-1 bg-teal-700 rounded">▢ Face</span>
          <span className="px-2 py-1 bg-orange-700 rounded">┅ Edge Group</span>
          <span className="px-2 py-1 bg-gray-700 rounded">╌ Edge</span>
          <span className="px-2 py-1 bg-gray-800 rounded">• Vertex</span>
        </div>
        <div className="mt-1 text-gray-400">Click on items with ▶ to expand/collapse nested structure</div>
      </div>

      {/* Tree View */}
      <div className="space-y-1 max-h-[600px] overflow-y-auto pr-2">
        {renderTreeNode(rootNode)}
      </div>
    </div>
  );
};

export default GeometryExplorer;
