import { create } from 'zustand';
import { api } from '../utils/api';

export interface DownloadTask {
  task_id: number;
  dataset_id: number;
  status: string; // PENDING, RUNNING, PAUSED, COMPLETED, FAILED
  progress: number;
  speed: string;
  eta: string;
}

interface DownloadState {
  tasks: DownloadTask[];
  socket: WebSocket | null;
  connectWebSocket: () => void;
  disconnectWebSocket: () => void;
  triggerDownload: (datasetId: number) => Promise<boolean>;
  pauseTask: (taskId: number) => Promise<void>;
  resumeTask: (taskId: number) => Promise<void>;
  cancelTask: (taskId: number) => Promise<void>;
}

export const useDownloadStore = create<DownloadState>((set, get) => ({
  tasks: [],
  socket: null,

  connectWebSocket: () => {
    // Check if socket already exists
    if (get().socket) return;
    
    const ws = new WebSocket('ws://localhost:8000/api/v1/ws/progress');
    
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.tasks) {
          set({ tasks: data.tasks });
        }
      } catch (err) {
        // ignore
      }
    };
    
    ws.onclose = () => {
      set({ socket: null });
      // Retry connection after 5 seconds
      setTimeout(() => {
        if (localStorage.getItem('token')) {
          get().connectWebSocket();
        }
      }, 5000);
    };
    
    set({ socket: ws });
  },

  disconnectWebSocket: () => {
    const ws = get().socket;
    if (ws) {
      ws.close();
      set({ socket: null, tasks: [] });
    }
  },

  triggerDownload: async (datasetId) => {
    try {
      const response = await api.post('/downloads/start', { dataset_id: datasetId });
      // WS will pick up updates once running
      return response.status === 200;
    } catch (err) {
      return false;
    }
  },

  pauseTask: async (taskId) => {
    try {
      await api.post(`/downloads/${taskId}/pause`);
    } catch (err) {
      // ignore
    }
  },

  resumeTask: async (taskId) => {
    try {
      await api.post(`/downloads/${taskId}/resume`);
    } catch (err) {
      // ignore
    }
  },

  cancelTask: async (taskId) => {
    try {
      await api.post(`/downloads/${taskId}/cancel`);
    } catch (err) {
      // ignore
    }
  }
}));
