import React, { useEffect, useState } from 'react';
import { api } from '../utils/api';
import { useNavigate } from 'react-router-dom';
import { FolderHeart, Star, ShieldAlert, Cpu } from 'lucide-react';

export const CollectionsPage: React.FC = () => {
  const navigate = useNavigate();
  const [datasets, setDatasets] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDatasets = async () => {
      try {
        const response = await api.get('/datasets/');
        setDatasets(response.data);
      } catch (err) {
        // ignore
      } finally {
        setLoading(false);
      }
    };
    fetchDatasets();
  }, []);

  if (loading) {
    return (
      <div className="h-64 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-gold-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-100 flex items-center gap-2">
          <FolderHeart className="w-5.5 h-5.5 text-gold-500" />
          Workspace Dataset Collections
        </h1>
        <p className="text-xs text-slate-400">View and manage datasets synced to your current workspace collection.</p>
      </div>

      {datasets.length === 0 ? (
        <div className="glass-card rounded-2xl p-16 text-center border border-dashed border-gold-500/10">
          <p className="text-sm text-slate-400 mb-4">No datasets imported yet.</p>
          <button 
            onClick={() => navigate('/search')}
            className="text-xs font-bold bg-gold-gradient text-darkbg-950 px-4 py-2.5 rounded-xl"
          >
            Go to Search
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {datasets.map((d) => (
            <div 
              key={d.id} 
              onClick={() => navigate(`/dataset/${d.id}`)}
              className="glass-card glass-card-hover rounded-2xl p-5 cursor-pointer flex flex-col justify-between h-48 relative overflow-hidden group border border-gold-500/5"
            >
              <div>
                <div className="flex justify-between items-center mb-3">
                  <span className="px-2 py-0.5 rounded-full bg-gold-500/10 border border-gold-500/20 text-gold-400 text-[10px] font-bold uppercase tracking-wider">
                    {d.source}
                  </span>
                  <div className="flex items-center gap-1">
                    <Star className="w-3.5 h-3.5 text-gold-500 fill-gold-500" />
                    <span className="text-[10px] text-gold-400 font-bold">{d.quality_score}%</span>
                  </div>
                </div>
                <h4 className="text-sm font-bold text-slate-100 group-hover:text-gold-400 transition-colors truncate">{d.name}</h4>
                <p className="text-xs text-slate-400 line-clamp-2 mt-1.5 leading-relaxed">{d.description}</p>
              </div>

              <div className="flex items-center justify-between border-t border-gold-500/5 pt-3.5 mt-4 text-[10px] text-slate-500 font-medium">
                <span className="flex items-center gap-1"><Cpu className="w-3.5 h-3.5" /> Images: {d.image_count}</span>
                <span className="flex items-center gap-1"><ShieldAlert className="w-3.5 h-3.5" /> License: {d.license}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
