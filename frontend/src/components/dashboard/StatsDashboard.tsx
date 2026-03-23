    import React from 'react';
import { useModelStore } from '../../store';
import UploadedFilesList from './UploadedFilesList';

const StatsDashboard: React.FC = () => {
  const { currentModel } = useModelStore();

  // If no model is selected, show uploaded files list
  if (!currentModel) {
    return <UploadedFilesList />;
  }

  // If model is selected but no statistics, show message
  if (!currentModel.statistics) {
    return (
      <div className="p-4">
        <h3 className="font-bold mb-2">Statistics</h3>
        <p className="text-sm text-gray-400">No statistics available yet</p>
        <p className="text-xs text-gray-500 mt-2">Processing may still be in progress</p>
      </div>
    );
  }

  const stats = currentModel.statistics;

  return (
    <div className="p-4 border-t border-gray-700">
      <h3 className="font-bold mb-4 text-lg">Statistics</h3>
      
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-gray-700 p-3 rounded">
          <div className="text-xs text-gray-400 uppercase">Solids</div>
          <div className="text-2xl font-bold">{stats.total_solids || 0}</div>
        </div>
        
        <div className="bg-gray-700 p-3 rounded">
          <div className="text-xs text-gray-400 uppercase">Faces</div>
          <div className="text-2xl font-bold">{stats.total_faces || 0}</div>
        </div>
        
        <div className="bg-gray-700 p-3 rounded">
          <div className="text-xs text-gray-400 uppercase">Edges</div>
          <div className="text-2xl font-bold">{stats.total_edges || 0}</div>
        </div>
        
        <div className="bg-gray-700 p-3 rounded">
          <div className="text-xs text-gray-400 uppercase">Vertices</div>
          <div className="text-2xl font-bold">{stats.total_vertices || 0}</div>
        </div>
        
        <div className="bg-gray-700 p-3 rounded col-span-2">
          <div className="text-xs text-gray-400 uppercase">Surfaces</div>
          <div className="text-2xl font-bold">{stats.total_surfaces || 0}</div>
        </div>
      </div>

      {stats.bounding_box && (
        <div className="mt-4 bg-gray-700 p-3 rounded">
          <div className="text-xs text-gray-400 uppercase mb-2">Bounding Box</div>
          <div className="text-sm space-y-1">
            <div className="flex justify-between">
              <span className="text-gray-400">X:</span>
              <span>{stats.bounding_box.dimensions.x.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Y:</span>
              <span>{stats.bounding_box.dimensions.y.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Z:</span>
              <span>{stats.bounding_box.dimensions.z.toFixed(2)}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default StatsDashboard;
