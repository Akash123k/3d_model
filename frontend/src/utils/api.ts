/**
 * API client for communicating with the backend
 */

import axios, { AxiosError } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

// Create axios instance
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  maxContentLength: Infinity,
  maxBodyLength: Infinity,
});

// Request interceptor for logging
apiClient.interceptors.request.use(
  (config) => {
    console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`);
    console.log('[API] Headers:', config.headers);
    if (config.data instanceof FormData) {
      console.log('[API] FormData entries:', Array.from((config.data as FormData).entries()));
    }
    return config;
  },
  (error) => {
    console.error('[API] Request error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => {
    console.log(`[API] Response ${response.status}:`, response.config.url, response.data);
    return response;
  },
  (error: AxiosError) => {
    console.error('[API] Response error:', {
      status: error.response?.status,
      data: error.response?.data,
      message: error.message,
      config: error.config
    });
    return Promise.reject(error);
  }
);

export interface UploadResponse {
  model_id: string;
  filename: string;
  file_size: number;
  upload_time: string;
  status: string;
}

export interface ModelSummary {
  model_id: string;
  filename: string;
  original_filename: string;
  file_size: number;
  upload_time: string;
  status: string;
  entities_count: number;
  has_statistics: boolean;
  has_assembly_tree: boolean;
  has_dependency_graph: boolean;
}

export interface ModelsListResponse {
  models: ModelSummary[];
  total: number;
}

  export interface ModelData {
  model_id: string;
  filename: string;
  file_size: number;
  upload_time: string;
  status: string;
  assembly_tree?: any;
  dependency_graph?: any;
  statistics?: any;
  brep_hierarchy?: any;
  meshes?: any[];
  entities_count?: number;
}

export interface AssemblyTree {
  model_id: string;
  root_node: any;
  total_nodes: number;
}

export interface DependencyGraph {
    model_id: string;
    nodes: Array<{
      id: string;
      label: string;
      type: string;
      references: string[];
      referenced_by: string[];
      properties: Record<string, any>;
    }>;
    edges: Array<{
      source: string;
      target: string;
      relationship: string;
    }>;
    total_nodes: number;
    total_edges: number;
  }

  export interface Statistics {
  total_solids: number;
  total_faces: number;
  total_edges: number;
  total_vertices: number;
  total_surfaces: number;
  bounding_box?: {
    min_point: { x: number; y: number; z: number };
    max_point: { x: number; y: number; z: number };
    dimensions: { x: number; y: number; z: number };
  };
  total_volume?: number;
  total_surface_area?: number;
}

export interface BRepGeometryResponse {
  model_id: string;
  entities_count: number;
  total_components: number;
  brep_tree: Array<{
    id: string;
    type: string;
    label: string;
    children: any[];
    depth: number;
    coords?: number[];
  }>;
  bounding_box?: {
    min: number[];
    max: number[];
    dimensions: number[];
  };
}

// API Functions
export const uploadFile = async (file: File, onProgress?: (progress: number) => void): Promise<UploadResponse> => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await apiClient.post<UploadResponse>('/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (progressEvent) => {
      if (onProgress && progressEvent.total) {
        const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        onProgress(percentCompleted);
      }
    },
  });

  return response.data;
};

export const getModel = async (modelId: string): Promise<ModelData> => {
  const response = await apiClient.get<ModelData>(`/models/${modelId}`);
  return response.data;
};

export const getAssemblyTree = async (modelId: string): Promise<AssemblyTree> => {
  const response = await apiClient.get<AssemblyTree>(`/models/${modelId}/assembly-tree`);
  return response.data;
};

export const getDependencyGraph = async (modelId: string): Promise<DependencyGraph> => {
  const response = await apiClient.get<DependencyGraph>(`/models/${modelId}/dependency-graph`);
  return response.data;
};

export const getStatistics = async (modelId: string): Promise<Statistics> => {
  const response = await apiClient.get<Statistics>(`/models/${modelId}/statistics`);
  return response.data;
};

export const getBRepGeometry = async (modelId: string): Promise<BRepGeometryResponse> => {
  const response = await apiClient.get<BRepGeometryResponse>(`/models/${modelId}/brep-geometry`);
  return response.data;
};

export const getEntityDetail = async (modelId: string, entityId: string): Promise<any> => {
  const response = await apiClient.get(`/models/${modelId}/entity/${entityId}`);
  return response.data;
};

export const getAllModels = async (): Promise<ModelsListResponse> => {
  const response = await apiClient.get<ModelsListResponse>('/models');
  return response.data;
};

export default apiClient;
