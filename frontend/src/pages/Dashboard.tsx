import React, { useEffect, useState } from 'react';
import { api } from '../utils/api';
import { useNavigate } from 'react-router-dom';
import { 
  FolderGit, 
  Sparkles, 
  Cpu, 
  ChevronRight, 
  ArrowRight,
  PlusCircle
} from 'lucide-react';
import { useWorkspaceStore } from '../store/workspaceStore';

export const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const { activeProject } = useWorkspaceStore();
  const [datasets, setDatasets] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchRecent = async () => {
      try {
        const res = await api.get('/datasets/');
        setDatasets(res.data.slice(0, 4));
      } catch (err) {
        // ignore
      } finally {
        setLoading(false);
      }
    };
    fetchRecent();
  }, []);

  return (
    <div className="space-y-8">
      {/* Welcome Banner */}
      <div className="relative overflow-hidden rounded-2xl glass-card border border-gold-500/10 p-8 flex flex-col md:flex-row items-center justify-between gap-6">
        <div className="absolute top-0 right-0 w-64 h-64 bg-gold-glow pointer-events-none opacity-20"></div>
        <div className="space-y-2 relative">
          <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-gold-500/10 border border-gold-500/20 text-gold-400 text-xs font-semibold">
            <Sparkles className="w-3.5 h-3.5" /> Workspace: {activeProject?.name || 'Loading...'}
          </div>
          <h1 className="text-3xl font-extrabold text-white">
            Welcome to <span className="gold-text-glow font-black">Aura Engine</span>
          </h1>
          <p className="text-slate-400 text-sm max-w-lg">
            Search datasets or crawl images, review quality rankings, manage tasks queues, and optimize models.
          </p>
        </div>
        <button 
          onClick={() => navigate('/search')}
          className="bg-gold-gradient text-darkbg-950 font-bold px-6 py-3 rounded-xl text-sm flex items-center gap-2 shadow-gold-border hover:opacity-90 transition-opacity shrink-0"
        >
          Begin Discovery <ArrowRight className="w-4 h-4 text-darkbg-950" />
        </button>
      </div>

      {/* Grid Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {[
          { title: "Aggregated Sources", value: "12+ Engines", desc: "Kaggle, HF, Roboflow, Figshare", icon: FolderGit },
          { title: "AI Image Verification", value: "Active Filters", desc: "Perceptual Hash, Blur & NSFW Check", icon: Cpu },
          { title: "Active Workspaces", value: "SaaS Multi-Tenant", desc: "Collaborate across project scopes", icon: Sparkles }
        ].map((stat, idx) => {
          const Icon = stat.icon;
          return (
            <div key={idx} className="glass-card rounded-2xl p-6 border border-gold-500/10 relative overflow-hidden group hover:border-gold-500/20 transition-all">
              <div className="absolute top-0 right-0 w-24 h-24 bg-gold-500/5 rounded-full pointer-events-none"></div>
              <div className="flex items-center justify-between mb-4">
                <span className="text-xs text-slate-400 font-semibold uppercase tracking-wider">{stat.title}</span>
                <Icon className="w-5 h-5 text-gold-500" />
              </div>
              <p className="text-2xl font-black text-white mb-1">{stat.value}</p>
              <p className="text-xs text-slate-400">{stat.desc}</p>
            </div>
          );
        })}
      </div>

      {/* Recent Datasets */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
            <FolderGit className="w-5 h-5 text-gold-500" />
            Recent Datasets Catalog
          </h3>
          <button 
            onClick={() => navigate('/collections')}
            className="text-xs font-semibold text-gold-500 hover:text-gold-400 flex items-center gap-1"
          >
            View All Collections <ChevronRight className="w-4 h-4" />
          </button>
        </div>

        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {[1, 2].map(n => (
              <div key={n} className="h-40 rounded-2xl bg-white/5 animate-pulse border border-white/5"></div>
            ))}
          </div>
        ) : datasets.length === 0 ? (
          <div className="glass-card rounded-2xl p-12 text-center border border-dashed border-gold-500/15">
            <p className="text-sm text-slate-400 mb-4">No datasets cataloged in this project yet.</p>
            <button 
              onClick={() => navigate('/search')}
              className="inline-flex items-center gap-2 text-xs font-bold text-darkbg-950 bg-gold-gradient px-4 py-2.5 rounded-xl hover:opacity-90"
            >
              <PlusCircle className="w-4 h-4 text-darkbg-950" /> Add Your First Dataset
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {datasets.map((d) => (
              <div 
                key={d.id} 
                onClick={() => navigate(`/dataset/${d.id}`)}
                className="glass-card glass-card-hover rounded-2xl p-6 cursor-pointer flex flex-col justify-between h-44 relative overflow-hidden group"
              >
                <div>
                  <div className="flex justify-between items-start mb-2.5">
                    <span className="px-2 py-0.5 rounded-full bg-gold-500/10 border border-gold-500/20 text-gold-400 text-[10px] font-bold uppercase tracking-wider">
                      {d.source}
                    </span>
                    <span className="text-xs font-black text-gold-400">Score: {d.quality_score}%</span>
                  </div>
                  <h4 className="text-base font-bold text-slate-100 group-hover:text-gold-400 transition-colors truncate">{d.name}</h4>
                  <p className="text-xs text-slate-400 line-clamp-2 mt-1.5 leading-relaxed">{d.description}</p>
                </div>
                
                <div className="flex items-center justify-between border-t border-gold-500/5 pt-3.5 mt-3.5">
                  <span className="text-[10px] text-slate-500 font-semibold">Images: {d.image_count} | Size: {d.download_size}</span>
                  <span className="text-[10px] text-gold-500 font-bold flex items-center gap-0.5 group-hover:translate-x-1 transition-transform">
                    Explore Details <ArrowRight className="w-3.5 h-3.5" />
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
