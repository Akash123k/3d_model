/**
 * Custom hooks for the application
 */

import { useState, useCallback } from 'react';
import { uploadFile, getModel, getAssemblyTree, getDependencyGraph, getStatistics, ModelData } from '../utils/api';
import { useModelStore } from '../store';

/**
 * Hook for file upload functionality
 */
export const useFileUpload = () => {
  const [isUploading, setIsUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const { setCurrentModel, setLoading, setError } = useModelStore();

  const upload = useCallback(async (file: File) => {
    try {
      setIsUploading(true);
      setProgress(0);
      setLoading(true);

      const response = await uploadFile(file, (progressPercent) => {
        setProgress(progressPercent);
      });
      
      console.log('[Upload] File uploaded successfully:', response);
      setProgress(100);

      // Set current model with basic info first (don't wait for full processing)
      const basicModelData: ModelData = {
        model_id: response.model_id,
        filename: response.filename,
        file_size: response.file_size,
        upload_time: response.upload_time,
        status: response.status || 'processing'
      };
      
      setCurrentModel(basicModelData);
      console.log('[Upload] Model data set:', basicModelData);

      setIsUploading(false);
      setLoading(false);
      
      return response;
    } catch (error: any) {
      console.error('[Upload] Error during upload:', error);
      console.error('[Upload] Error details:', error.response?.data || error.message);
      setIsUploading(false);
      setLoading(false);
      setProgress(0);
      const errorMessage = error.response?.data?.message || error.message || 'Failed to upload file';
      setError(errorMessage);
      throw error;
    }
  }, [setCurrentModel, setLoading, setError]);

  return { upload, isUploading, progress };
};

/**
 * Hook for loading model data
 */
export const useModelLoader = () => {
  const [isLoading, setIsLoading] = useState(false);
  const { setCurrentModel, setLoading, setError } = useModelStore();

  const loadModel = useCallback(async (modelId: string) => {
    try {
      setIsLoading(true);
      setLoading(true);

      const modelData = await getModel(modelId);
      setCurrentModel(modelData);

      setIsLoading(false);
      setLoading(false);
    } catch (error: any) {
      setIsLoading(false);
      setLoading(false);
      setError(error.response?.data?.message || 'Failed to load model');
      throw error;
    }
  }, [setCurrentModel, setLoading, setError]);

  return { loadModel, isLoading };
};

/**
 * Hook for assembly tree operations
 */
export const useAssemblyTree = (modelId?: string) => {
  const [tree, setTree] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);

  const loadTree = useCallback(async () => {
    if (!modelId) return;
    
    try {
      setIsLoading(true);
      const data = await getAssemblyTree(modelId);
      setTree(data);
    } catch (error) {
      console.error('Failed to load assembly tree:', error);
    } finally {
      setIsLoading(false);
    }
  }, [modelId]);

  return { tree, isLoading, loadTree };
};

/**
 * Hook for dependency graph operations
 */
export const useDependencyGraph = (modelId?: string) => {
  const [graph, setGraph] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);

  const loadGraph = useCallback(async () => {
    if (!modelId) return;
    
    try {
      setIsLoading(true);
      const data = await getDependencyGraph(modelId);
      setGraph(data);
    } catch (error) {
      console.error('Failed to load dependency graph:', error);
    } finally {
      setIsLoading(false);
    }
  }, [modelId]);

  return { graph, isLoading, loadGraph };
};

/**
 * Hook for statistics operations
 */
export const useStatistics = (modelId?: string) => {
  const [stats, setStats] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);

  const loadStats = useCallback(async () => {
    if (!modelId) return;
    
    try {
      setIsLoading(true);
      const data = await getStatistics(modelId);
      setStats(data);
    } catch (error) {
      console.error('Failed to load statistics:', error);
    } finally {
      setIsLoading(false);
    }
  }, [modelId]);

  return { stats, isLoading, loadStats };
};
