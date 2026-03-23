import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useModelStore, useUIStore } from '../../store';
import FileUpload from '../common/FileUpload';
import Viewer3D from '../viewer/Viewer3D';
import GeometryExplorer from '../geometry/GeometryExplorer';
import StatsDashboard from '../dashboard/StatsDashboard';

const DashboardLayout: React.FC = () => {
  const navigate = useNavigate();
  const { currentModel, error } = useModelStore();
  const { rightPanelOpen } = useUIStore();
  const [showUpload, setShowUpload] = useState(true);

  return (
    <div className="flex flex-col h-screen bg-gray-900 text-white">
      {/* Header */}
      <header className="flex items-center justify-between px-4 py-2 bg-gray-800 border-b border-gray-700">
        <h1 className="text-xl font-bold">STEP CAD Viewer</h1>
        <div className="flex items-center gap-2">
          {currentModel && (
            <>
              <button
                onClick={() => navigate('/dependency-graph')}
                className="px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded transition flex items-center gap-2"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                </svg>
                Dependency Graph
              </button>
              <button
                onClick={() => navigate('/brep-geometry')}
                className="px-4 py-2 bg-green-600 hover:bg-green-700 rounded transition flex items-center gap-2"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
                </svg>
                B-Rep Tree
              </button>
            </>
          )}
          <button
            onClick={() => setShowUpload(true)}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded transition"
          >
            Upload STEP File
          </button>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Center - 3D Viewer */}
        <main className="flex-1 flex flex-col relative w-full overflow-hidden">
          {currentModel ? (
            <>
              <div className="flex-1 relative min-h-0">
                <Viewer3D />
              </div>
            </>
          ) : (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <p className="text-gray-400 mb-4">No model loaded</p>
                <button
                  onClick={() => setShowUpload(true)}
                  className="px-6 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg transition"
                >
                  Upload a STEP file to get started
                </button>
              </div>
            </div>
          )}
        </main>

        {/* Right Panel - Geometry Explorer & Stats */}
        {rightPanelOpen && (
          <aside className="w-96 bg-gray-800 border-l border-gray-700 overflow-y-auto">
            {currentModel && <GeometryExplorer />}
            <StatsDashboard />
          </aside>
        )}
      </div>

      {/* Error Display */}
      {error && (
        <div className="fixed bottom-4 right-4 bg-red-600 text-white px-4 py-2 rounded shadow-lg">
          {error}
        </div>
      )}

      {/* Upload Modal */}
      {showUpload && <FileUpload onClose={() => setShowUpload(false)} />}
    </div>
  );
};

export default DashboardLayout;
