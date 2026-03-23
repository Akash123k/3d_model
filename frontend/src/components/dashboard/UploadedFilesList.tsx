import React, { useState, useEffect, useCallback } from 'react';
import { getAllModels, ModelSummary } from '../../utils/api';
import { useModelStore } from '../../store';

const UploadedFilesList: React.FC = () => {
  const [models, setModels] = useState<ModelSummary[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { setCurrentModel, setLoading } = useModelStore();

  const loadModels = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await getAllModels();
      console.log('[FileList] Loaded models:', data.models.length, 'files');
      console.log('[FileList] Models data:', data.models.map(m => ({
        id: m.model_id.slice(0, 8),
        filename: m.original_filename,
        status: m.status
      })));
      
      // Remove duplicates based on model_id (keep first occurrence)
      const uniqueModels = Array.from(
        new Map(data.models.map(model => [model.model_id, model])).values()
      );
      
      if (uniqueModels.length !== data.models.length) {
        console.warn('[FileList] Removed duplicate models:', data.models.length - uniqueModels.length);
      }
      
      setModels(uniqueModels);
      setIsLoading(false);
    } catch (err: any) {
      console.error('Failed to load models:', err);
      setError(err.response?.data?.message || 'Failed to load uploaded files');
      setIsLoading(false);
    }
  }, []);

  // Auto-refresh on mount
  useEffect(() => {
    loadModels();
  }, [loadModels]);

  // Auto-refresh every 5 seconds when component is mounted
  useEffect(() => {
    const interval = setInterval(loadModels, 5000);
    return () => clearInterval(interval);
  }, [loadModels]);

  const handleSelectModel = async (model: ModelSummary) => {
    try {
      console.log('[FileList] Selecting model:', model.model_id, model.original_filename);
      setLoading(true);
      // Fetch complete model data
      const response = await fetch(`${import.meta.env.VITE_API_URL || '/api'}/models/${model.model_id}`);
      const completeData = await response.json();
      console.log('[FileList] Model loaded successfully:', completeData.status);
      setCurrentModel(completeData);
      setLoading(false);
    } catch (err) {
      console.error('Failed to load model:', err);
      setLoading(false);
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
  };

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getStatusColor = (status: string): string => {
    switch (status.toLowerCase()) {
      case 'completed':
        return 'bg-green-500';
      case 'processing':
        return 'bg-yellow-500';
      case 'error':
        return 'bg-red-500';
      default:
        return 'bg-gray-500';
    }
  };

  if (isLoading) {
    return (
      <div className="p-4 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 text-red-400 bg-red-900/20 rounded">
        <p>{error}</p>
        <button 
          onClick={loadModels}
          className="mt-2 px-4 py-2 bg-red-600 hover:bg-red-700 rounded text-sm"
        >
          Retry
        </button>
      </div>
    );
  }

  if (models.length === 0) {
    return (
      <div className="p-4 text-center text-gray-400">
        <p>No uploaded files found</p>
        <p className="text-sm mt-2">Upload a STEP file to see it here</p>
      </div>
    );
  }

  return (
    <div className="p-4 overflow-y-auto" style={{ maxHeight: 'calc(100vh - 200px)' }}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-bold text-lg">Uploaded Files</h3>
        <button
          onClick={loadModels}
          disabled={isLoading}
          className="p-2 hover:bg-gray-700 rounded transition disabled:opacity-50"
          title="Refresh list"
        >
          <svg 
            className={`w-5 h-5 ${isLoading ? 'animate-spin' : ''}`} 
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        </button>
      </div>
      
      <div className="space-y-2">
        {models.map((model) => (
          <div
            key={`${model.model_id}-${model.status}`} // Unique key includes status to show updates
            onClick={() => handleSelectModel(model)}
            className="bg-gray-700 hover:bg-gray-600 rounded p-3 cursor-pointer transition-colors border border-gray-600 hover:border-blue-500"
          >
            <div className="flex items-start justify-between mb-2">
              <div className="flex-1 min-w-0">
                <h4 className="font-semibold text-sm truncate" title={model.original_filename}>
                  {model.original_filename}
                </h4>
                <p className="text-xs text-gray-400 mt-1" title={model.filename}>
                  ID: {model.model_id.slice(0, 8)}...
                </p>
              </div>
              <div className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(model.status)} text-white`}>
                {model.status}
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-2 text-xs text-gray-300">
              <div>
                <span className="text-gray-400">Size:</span>{' '}
                <span>{formatFileSize(model.file_size)}</span>
              </div>
              <div>
                <span className="text-gray-400">Uploaded:</span>{' '}
                <span title={new Date(model.upload_time).toLocaleString()}>
                  {formatDate(model.upload_time)}
                </span>
              </div>
              <div>
                <span className="text-gray-400">Entities:</span>{' '}
                <span>{model.entities_count || 0}</span>
              </div>
              <div className="flex gap-1">
                {model.has_statistics && (
                  <span className="px-1.5 py-0.5 bg-blue-600 rounded text-xs" title="Has statistics">
                    📊
                  </span>
                )}
                {model.has_assembly_tree && (
                  <span className="px-1.5 py-0.5 bg-purple-600 rounded text-xs" title="Has assembly tree">
                    🌳
                  </span>
                )}
                {model.has_dependency_graph && (
                  <span className="px-1.5 py-0.5 bg-green-600 rounded text-xs" title="Has dependency graph">
                    🔗
                  </span>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default UploadedFilesList;
