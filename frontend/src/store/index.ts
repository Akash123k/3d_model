/**
 * Global state management using Zustand
 */

import { create, SetState } from 'zustand';

// Model data types
export interface ModelData {
  model_id: string
  filename: string
  file_size: number
  upload_time: string
  status: string
  assembly_tree?: any
  dependency_graph?: any
  statistics?: any
  brep_hierarchy?: any
  meshes?: any[]
  entities_count?: number
}

interface ModelState {
  currentModel: ModelData | null
  isLoading: boolean
  error: string | null
  
  // Actions
  setCurrentModel: (model: ModelData) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  clearModel: () => void
}

export const useModelStore = create<ModelState>((set: SetState<ModelState>) => ({
  currentModel: null,
  isLoading: false,
  error: null,
  
  setCurrentModel: (model: ModelData) => set({ currentModel: model, error: null }),
  setLoading: (loading: boolean) => set({ isLoading: loading }),
  setError: (error: string | null) => set({ error, isLoading: false }),
  clearModel: () => set({ currentModel: null, error: null, isLoading: false })
}))

// Viewer state
interface ViewerState {
  selectedPartId: string | null
  explodedView: boolean
  showCrossSection: boolean
  explosionFactor: number
  
  setSelectedPartId: (id: string | null) => void
  toggleExplodedView: () => void
  toggleCrossSection: () => void
  setExplosionFactor: (factor: number) => void
}

export const useViewerStore = create<ViewerState>((set: SetState<ViewerState>) => ({
  selectedPartId: null,
  explodedView: false,
  showCrossSection: false,
  explosionFactor: 1.5,
  
  setSelectedPartId: (id: string | null) => set({ selectedPartId: id }),
  toggleExplodedView: () => set((state: ViewerState) => ({ explodedView: !state.explodedView })),
  toggleCrossSection: () => set((state: ViewerState) => ({ showCrossSection: !state.showCrossSection })),
  setExplosionFactor: (factor: number) => set({ explosionFactor: factor })
}))

// UI state
interface UIState {
  leftPanelOpen: boolean
  rightPanelOpen: boolean
  bottomPanelOpen: boolean
  
  toggleLeftPanel: () => void
  toggleRightPanel: () => void
  toggleBottomPanel: () => void
}

export const useUIStore = create<UIState>((set: SetState<UIState>) => ({
  leftPanelOpen: true,
  rightPanelOpen: true,
  bottomPanelOpen: true,
  
  toggleLeftPanel: () => set((state: UIState) => ({ leftPanelOpen: !state.leftPanelOpen })),
  toggleRightPanel: () => set((state: UIState) => ({ rightPanelOpen: !state.rightPanelOpen })),
  toggleBottomPanel: () => set((state: UIState) => ({ bottomPanelOpen: !state.bottomPanelOpen }))
}))
