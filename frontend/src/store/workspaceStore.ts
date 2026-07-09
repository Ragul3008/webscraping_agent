import { create } from 'zustand';
import { api } from '../utils/api';

export interface Project {
  id: number;
  name: string;
  description: string;
  created_at: string;
}

interface WorkspaceState {
  projects: Project[];
  activeProject: Project | null;
  loading: boolean;
  fetchProjects: () => Promise<void>;
  createProject: (name: string, description: string) => Promise<Project | null>;
  selectProject: (project: Project) => void;
  bookmarkAsset: (projectId: number, datasetId?: number, imageId?: number) => Promise<boolean>;
}

export const useWorkspaceStore = create<WorkspaceState>((set, get) => ({
  projects: [],
  activeProject: null,
  loading: false,

  fetchProjects: async () => {
    set({ loading: true });
    try {
      const response = await api.get('/workspace/projects');
      set({ projects: response.data, loading: false });
      if (response.data.length > 0 && !get().activeProject) {
        set({ activeProject: response.data[0] });
      }
    } catch (err) {
      set({ loading: false });
    }
  },

  createProject: async (name, description) => {
    try {
      const response = await api.post('/workspace/projects', { name, description });
      const newProj = response.data;
      set((state) => ({
        projects: [newProj, ...state.projects],
        activeProject: newProj
      }));
      return newProj;
    } catch (err) {
      return null;
    }
  },

  selectProject: (project) => {
    set({ activeProject: project });
  },

  bookmarkAsset: async (projectId, datasetId, imageId) => {
    try {
      await api.post('/workspace/bookmarks', {
        project_id: projectId,
        dataset_id: datasetId,
        preview_image_id: imageId
      });
      return true;
    } catch (err) {
      return false;
    }
  }
}));
