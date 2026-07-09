import React, { useEffect } from 'react';
import { useDownloadStore } from '../store/downloadStore';
import { 
  Play, 
  Pause, 
  XOctagon, 
  DownloadCloud, 
  ArrowUpRight
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export const DownloadsPage: React.FC = () => {
  const navigate = useNavigate();
  const { tasks, connectWebSocket, disconnectWebSocket, pauseTask, resumeTask, cancelTask } = useDownloadStore();

  useEffect(() => {
    connectWebSocket();
    return () => disconnectWebSocket();
  }, []);

  return (
    <div className="space-y-6">
      {/* Header Description */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <DownloadCloud className="w-5.5 h-5.5 text-gold-500" />
            Background Downloads Monitor
          </h1>
          <p className="text-xs text-slate-400">Manage real-time crawling pipelines, monitor speeds, pause or cancel download queues.</p>
        </div>
      </div>

      {/* Task Rows Queue */}
      {tasks.length === 0 ? (
        <div className="glass-card rounded-2xl p-16 text-center border border-dashed border-gold-500/10 flex flex-col items-center justify-center space-y-3">
          <DownloadCloud className="w-12 h-12 text-slate-600 animate-pulse" />
          <h4 className="text-slate-300 font-bold">No active download queues</h4>
          <p className="text-xs text-slate-500 max-w-sm">Queue images downloader tasks by importing datasets from the Global Search tab.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {tasks.map((task) => (
            <div 
              key={task.task_id}
              className="glass-card rounded-2xl p-5 border border-gold-500/10 flex flex-col md:flex-row items-center justify-between gap-6 hover:border-gold-500/20 transition-all"
            >
              {/* Dataset Name info */}
              <div className="space-y-1.5 flex-1 min-w-0">
                <div className="flex items-center gap-2.5">
                  <span className="text-xs text-gold-400 font-extrabold">TASK #{task.task_id}</span>
                  <span className={`px-2 py-0.5 rounded text-[8px] font-bold uppercase tracking-wider ${
                    task.status === 'RUNNING' ? 'bg-gold-500/15 text-gold-400' :
                    task.status === 'COMPLETED' ? 'bg-emerald-500/15 text-emerald-400' :
                    task.status === 'PAUSED' ? 'bg-amber-500/15 text-amber-400' : 'bg-red-500/15 text-red-400'
                  }`}>
                    {task.status}
                  </span>
                </div>
                <h4 className="text-sm font-bold text-slate-100 truncate">Image Crawler Target</h4>
              </div>

              {/* Progress bar */}
              <div className="w-full md:w-64 space-y-1">
                <div className="flex justify-between text-[10px] text-slate-400 font-semibold">
                  <span>Progress</span>
                  <span>{task.progress}%</span>
                </div>
                <div className="w-full bg-darkbg-950 rounded-full h-2 overflow-hidden border border-gold-500/5">
                  <div 
                    className="bg-gold-gradient h-2 rounded-full transition-all duration-300"
                    style={{ width: `${task.progress}%` }}
                  ></div>
                </div>
              </div>

              {/* Speed & ETA */}
              <div className="flex gap-6 text-[10px] shrink-0 text-slate-400 font-medium">
                <div>
                  <span className="text-[8px] text-slate-500 font-extrabold block uppercase tracking-wider">Speed</span>
                  <span className="text-slate-200 font-semibold">{task.speed}</span>
                </div>
                <div>
                  <span className="text-[8px] text-slate-500 font-extrabold block uppercase tracking-wider">ETA</span>
                  <span className="text-slate-200 font-semibold">{task.eta}</span>
                </div>
              </div>

              {/* Control Actions buttons */}
              <div className="flex items-center gap-2 shrink-0">
                {task.status === 'RUNNING' && (
                  <button 
                    onClick={() => pauseTask(task.task_id)}
                    className="p-2.5 bg-amber-500/10 hover:bg-amber-500/20 text-amber-400 border border-amber-500/20 rounded-xl transition-colors"
                    title="Pause Download"
                  >
                    <Pause className="w-4 h-4" />
                  </button>
                )}
                {task.status === 'PAUSED' && (
                  <button 
                    onClick={() => resumeTask(task.task_id)}
                    className="p-2.5 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/20 rounded-xl transition-colors"
                    title="Resume Download"
                  >
                    <Play className="w-4 h-4" />
                  </button>
                )}
                {['RUNNING', 'PENDING', 'PAUSED'].includes(task.status) && (
                  <button 
                    onClick={() => cancelTask(task.task_id)}
                    className="p-2.5 bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/20 rounded-xl transition-colors"
                    title="Cancel Download"
                  >
                    <XOctagon className="w-4 h-4" />
                  </button>
                )}
                <button
                  onClick={() => navigate(`/dataset/${task.dataset_id}`)}
                  className="p-2.5 bg-gold-500/10 hover:bg-gold-500/20 text-gold-400 border border-gold-500/20 rounded-xl transition-colors"
                  title="View Dataset"
                >
                  <ArrowUpRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
