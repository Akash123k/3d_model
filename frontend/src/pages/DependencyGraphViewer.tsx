import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useModelStore } from '../store/index.js';
import DependencyGraph from '../components/graph/DependencyGraph.jsx';

const DependencyGraphViewer: React.FC = () => {
  const navigate = useNavigate();
  const { currentModel } = useModelStore();
  const [stats, setStats] = useState({ nodes: 0, edges: 0 });

  useEffect(() => {
    if (currentModel?.dependency_graph) {
      const graph = currentModel.dependency_graph;
      setStats({
        nodes: graph.total_nodes || graph.nodes?.length || 0,
        edges: graph.total_edges || graph.edges?.length || 0
      });
    }
  }, [currentModel]);

  if (!currentModel) {
    return (
      <div className="flex flex-col items-center justify-center h-screen bg-gray-900 text-white">
        <h2 className="text-2xl font-bold mb-4">No Model Loaded</h2>
        <p className="text-gray-400 mb-6">Please upload a STEP file first</p>
        <button
          onClick={() => navigate('/')}
          className="px-6 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg transition"
        >
          Go to Dashboard
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen bg-gray-900 text-white">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-3 bg-gray-800 border-b border-gray-700 shrink-0">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/')}
            className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded transition flex items-center gap-2"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            Back to Dashboard
          </button>
          <div className="border-l border-gray-600 h-6 mx-2"></div>
          <div>
            <h1 className="text-xl font-bold">Dependency Graph Viewer</h1>
            <p className="text-sm text-gray-400">{currentModel.filename}</p>
          </div>
        </div>

        {/* Stats */}
        <div className="flex items-center gap-6">
          <div className="text-center">
            <div className="text-xs text-gray-400 uppercase">Total Nodes</div>
            <div className="text-2xl font-bold text-blue-400">{stats.nodes}</div>
          </div>
          <div className="text-center">
            <div className="text-xs text-gray-400 uppercase">Total Edges</div>
            <div className="text-2xl font-bold text-purple-400">{stats.edges}</div>
          </div>
          <div className="text-center">
            <div className="text-xs text-gray-400 uppercase">File Size</div>
            <div className="text-lg font-semibold text-gray-300">
              {(currentModel.file_size / 1024).toFixed(2)} KB
            </div>
          </div>
        </div>
      </header>

      {/* Graph Canvas */}
      <main className="flex-1 overflow-hidden relative">
        <DependencyGraph />
      </main>
    </div>
  );
};

export default DependencyGraphViewer;
