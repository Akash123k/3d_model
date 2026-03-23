import React, { useState } from 'react';
import { useModelStore } from '../../store';

const AssemblyTree: React.FC = () => {
  const { currentModel } = useModelStore();
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set(['root']));
  const [showSurfaceDetails, setShowSurfaceDetails] = useState(false);

  if (!currentModel || !currentModel.assembly_tree) {
    return (
      <div className="p-4">
        <h3 className="font-bold mb-2">Assembly Tree</h3>
        <p className="text-sm text-gray-400">No assembly data available</p>
      </div>
    );
  }

  const tree = currentModel.assembly_tree;

  const toggleNode = (nodeId: string) => {
    const newExpanded = new Set(expandedNodes);
    if (newExpanded.has(nodeId)) {
      newExpanded.delete(nodeId);
    } else {
      newExpanded.add(nodeId);
    }
    setExpandedNodes(newExpanded);
  };

  const getTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      'BREP_MODEL': 'text-blue-400',
      'SOLID': 'text-green-400',
      'SHELL': 'text-yellow-400',
      'FACE': 'text-purple-400',
      'EDGE_GROUP': 'text-orange-400',
      'EDGE': 'text-red-400',
      'VERTEX': 'text-pink-400',
      'ASSEMBLY': 'text-cyan-400',
      'TYPE_GROUP': 'text-indigo-400',
      'ENTITY': 'text-gray-400'
    };
    return colors[type] || 'text-gray-300';
  };

  const getTypeIcon = (type: string) => {
    const icons: Record<string, string> = {
      'BREP_MODEL': '📦',
      'SOLID': '🧊',
      'SHELL': '🔷',
      'FACE': '◼️',
      'EDGE_GROUP': '➖',
      'EDGE': '📏',
      'VERTEX': '📍',
      'ASSEMBLY': '⚙️',
      'TYPE_GROUP': '📁',
      'ENTITY': '📄'
    };
    return icons[type] || '•';
  };

  // Render tree node recursively
  const renderTreeNode = (node: any, level: number = 0) => {
    if (!node) return null;

    const isExpanded = expandedNodes.has(node.id || 'root');
    const hasChildren = node.children && node.children.length > 0;
    const nodeType = node.type || 'UNKNOWN';

    // Extract surface description if available
    const surfaceDesc = node.properties?.surface_description;
    const showDetails = showSurfaceDetails && surfaceDesc;

    return (
      <div key={node.id || 'root'}>
        <div
          className={`flex items-center gap-2 py-1 px-2 hover:bg-gray-700 rounded cursor-pointer transition`}
          style={{ paddingLeft: `${level * 16 + 8}px` }}
          onClick={() => toggleNode(node.id || 'root')}
        >
          <span className="text-gray-400 w-4">
            {hasChildren ? (isExpanded ? '▼' : '▶') : '•'}
          </span>
          <span className="text-lg">{getTypeIcon(nodeType)}</span>
          <span className={`flex-1 truncate text-sm ${getTypeColor(nodeType)}`}>
            {node.name || node.label || 'Unknown'}
          </span>
          {node.type && (
            <span className="text-xs text-gray-500 bg-gray-800 px-1 rounded">
              {node.type}
            </span>
          )}
          {node.properties?.edge_count !== undefined && (
            <span className="text-xs text-gray-400">
              Edges: {node.properties.edge_count}
            </span>
          )}
          {node.properties?.vertex_count !== undefined && (
            <span className="text-xs text-gray-400">
              Vertices: {node.properties.vertex_count}
            </span>
          )}
        </div>
        
        {/* Show surface details if available */}
        {showDetails && (
          <div className="ml-8 mt-1 p-2 bg-gray-800 rounded text-xs space-y-1">
            <div className="text-blue-300 font-semibold">Surface Properties:</div>
            <div className="text-gray-300">Type: {surfaceDesc.type}</div>
            {surfaceDesc.properties && Object.entries(surfaceDesc.properties).map(([key, value]) => (
              <div key={key} className="text-gray-400">
                {key}: {typeof value === 'object' ? JSON.stringify(value) : String(value)}
              </div>
            ))}
          </div>
        )}
        
        {isExpanded && hasChildren && (
          <div>
            {node.children.map((child: any) => renderTreeNode(child, level + 1))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="p-4 h-full overflow-y-auto">
      <div className="flex justify-between items-center mb-4">
        <h3 className="font-bold text-lg">B-Rep Structure</h3>
        <button
          onClick={() => setShowSurfaceDetails(!showSurfaceDetails)}
          className="text-xs px-2 py-1 bg-blue-600 hover:bg-blue-700 rounded"
        >
          {showSurfaceDetails ? 'Hide Details' : 'Show Details'}
        </button>
      </div>
      
      <div className="text-xs text-gray-400 mb-2">
        Total Solids: {currentModel.statistics?.total_solids || 0} | 
        Total Faces: {currentModel.statistics?.total_faces || 0} |
        Total Nodes: {tree.total_nodes || 0}
      </div>
      
      <div className="space-y-1">
        {renderTreeNode(tree.root_node)}
      </div>
    </div>
  );
};

export default AssemblyTree;
