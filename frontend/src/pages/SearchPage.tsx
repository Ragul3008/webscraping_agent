import React, { useState } from 'react';
import { api } from '../utils/api';
import { useDownloadStore } from '../store/downloadStore';
import { Search, Sparkles, FolderDown, AlertCircle, Info } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export const SearchPage: React.FC = () => {
  const navigate = useNavigate();
  const { triggerDownload } = useDownloadStore();
  
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<any[]>([]);
  const [selectedSources, setSelectedSources] = useState<string[]>([
    'HuggingFace', 'Kaggle', 'GitHub', 'Roboflow', 'Zenodo'
  ]);
  const [importingId, setImportingId] = useState<string | null>(null);

  const sources = [
    'HuggingFace', 'Kaggle', 'GitHub', 'Roboflow', 'Zenodo', 'Figshare', 'OpenML', 'UCI'
  ];

  const toggleSource = (src: string) => {
    if (selectedSources.includes(src)) {
      setSelectedSources(selectedSources.filter(s => s !== src));
    } else {
      setSelectedSources([...selectedSources, src]);
    }
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    setResults([]);
    try {
      const response = await api.get('/search/', { params: { query } });
      // Filter by selected sources
      const filtered = response.data.filter((r: any) => selectedSources.includes(r.source));
      setResults(filtered.length > 0 ? filtered : response.data);
    } catch (err) {
      // fallback
    } finally {
      setLoading(false);
    }
  };

  const handleImportDataset = async (datasetData: any) => {
    setImportingId(datasetData.name);
    try {
      const response = await api.post('/datasets/', datasetData);
      const newDataset = response.data;
      
      // Auto queue images downloader for this dataset
      await triggerDownload(newDataset.id);
      
      // Redirect to detailed explorer
      navigate(`/dataset/${newDataset.id}`);
    } catch (err) {
      // ignore
    } finally {
      setImportingId(null);
    }
  };

  return (
    <div className="space-y-8">
      {/* Floating Query Search Box */}
      <div className="glass-card rounded-2xl p-6 border border-gold-500/10 shadow-glass">
        <form onSubmit={handleSearch} className="flex gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-4.5 top-3.5 w-5 h-5 text-slate-500" />
            <input 
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search datasets (e.g. banana disease, brain MRI, cars)..."
              className="w-full bg-darkbg-900 border border-gold-500/10 rounded-xl pl-12 pr-4 py-3.5 text-sm text-slate-200"
            />
          </div>
          <button 
            type="submit"
            disabled={loading}
            className="bg-gold-gradient text-darkbg-950 font-bold px-6 py-3.5 rounded-xl text-sm flex items-center gap-2 hover:opacity-90 shadow-gold-border disabled:opacity-50"
          >
            <Sparkles className="w-4 h-4 text-darkbg-950" />
            {loading ? 'Searching Hubs...' : 'Discover'}
          </button>
        </form>
        
        {/* Source Badges */}
        <div className="flex flex-wrap items-center gap-2 mt-4 pt-3 border-t border-gold-500/5">
          <span className="text-[10px] text-slate-500 font-extrabold uppercase tracking-wider mr-2">Target Sources:</span>
          {sources.map(src => {
            const active = selectedSources.includes(src);
            return (
              <button
                key={src}
                onClick={() => toggleSource(src)}
                className={`px-3 py-1 rounded-full text-xs font-semibold transition-all border ${
                  active 
                    ? 'bg-gold-500/10 border-gold-500/35 text-gold-400' 
                    : 'bg-white/5 border-white/5 text-slate-400 hover:bg-white/10'
                }`}
              >
                {src}
              </button>
            );
          })}
        </div>
      </div>

      {/* Results Header */}
      {results.length > 0 && (
        <div className="flex items-center gap-2 text-xs font-bold text-slate-400">
          <Info className="w-4.5 h-4.5 text-gold-500" />
          Discovered {results.length} matched files. Click import to queue downloader pipeline.
        </div>
      )}

      {/* Grid of Results */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {[1, 2, 3, 4].map(n => (
            <div key={n} className="h-44 rounded-2xl bg-white/5 animate-pulse border border-white/5"></div>
          ))}
        </div>
      ) : results.length === 0 ? (
        <div className="glass-card rounded-2xl p-16 text-center border border-dashed border-gold-500/10 flex flex-col items-center justify-center space-y-3">
          <AlertCircle className="w-12 h-12 text-slate-600" />
          <h4 className="text-slate-300 font-bold">Discover Global Repositories</h4>
          <p className="text-xs text-slate-500 max-w-sm">Enter keywords above to scan academic records, Kaggle datasets, and HuggingFace repositories in parallel.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {results.map((r, idx) => (
            <div 
              key={idx}
              className="glass-card rounded-2xl p-6 border border-gold-500/10 flex flex-col justify-between h-48 relative overflow-hidden group hover:border-gold-500/25 transition-all"
            >
              <div className="space-y-2">
                <div className="flex justify-between items-start">
                  <span className="px-2 py-0.5 rounded-full bg-gold-500/10 border border-gold-500/20 text-gold-400 text-[10px] font-bold uppercase tracking-wider">
                    {r.source}
                  </span>
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] text-slate-400 font-bold">{r.popularity}</span>
                    <span className="text-xs font-black text-gold-400">Score: {r.quality_score}%</span>
                  </div>
                </div>
                <h4 className="text-base font-bold text-slate-100 truncate">{r.name}</h4>
                <p className="text-xs text-slate-400 line-clamp-2 mt-1 leading-relaxed">{r.description}</p>
              </div>

              <div className="flex items-center justify-between border-t border-gold-500/5 pt-3.5 mt-3.5">
                <div className="flex items-center gap-3 text-[10px] text-slate-500 font-medium">
                  <span>License: {r.license}</span>
                  {r.download_size !== 'Unknown' && <span>Size: {r.download_size}</span>}
                </div>
                <button
                  onClick={() => handleImportDataset(r)}
                  disabled={importingId === r.name}
                  className="px-4 py-2 bg-gold-500/10 border border-gold-500/20 text-gold-400 rounded-xl text-xs font-bold flex items-center gap-1.5 hover:bg-gold-500/20 shadow-glass disabled:opacity-50"
                >
                  <FolderDown className="w-4 h-4 text-gold-400" />
                  {importingId === r.name ? 'Importing...' : 'Import & Pull'}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
