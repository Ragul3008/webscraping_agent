import React, { useEffect, useState } from 'react';
import { api } from '../utils/api';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, LineChart, Line, Legend } from 'recharts';
import { BarChart3, LineChart as LineIcon, PieChart } from 'lucide-react';

export const AnalyticsPage: React.FC = () => {
  const [datasets, setDatasets] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDatasets = async () => {
      try {
        const res = await api.get('/datasets/');
        setDatasets(res.data);
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

  // Aggregate global source counts
  const sourceMap: Record<string, number> = {};
  datasets.forEach(d => {
    sourceMap[d.source] = (sourceMap[d.source] || 0) + 1;
  });
  const sourceData = Object.entries(sourceMap).map(([name, count]) => ({ name, count }));

  // Aggregate quality score groupings
  const qualityData = datasets.map(d => ({
    name: d.name.slice(0, 15) + '...',
    'Quality Score': d.quality_score,
    'Trust Index': d.trust_score
  }));

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-100 flex items-center gap-2">
          <BarChart3 className="w-5.5 h-5.5 text-gold-500" />
          Global Analytics Dashboard
        </h1>
        <p className="text-xs text-slate-400">Aggregate dataset scores and source distributions across active workspaces.</p>
      </div>

      {datasets.length === 0 ? (
        <div className="glass-card rounded-2xl p-16 text-center border border-dashed border-gold-500/10">
          <p className="text-sm text-slate-400">Import datasets to activate global metrics analysis.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Engine distribution chart */}
          <div className="glass-card rounded-2xl p-6 border border-gold-500/10 space-y-4">
            <h4 className="text-xs font-extrabold text-slate-400 uppercase tracking-widest flex items-center gap-2">
              <PieChart className="w-4.5 h-4.5 text-gold-500" /> Source Engines Distribution
            </h4>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={sourceData}>
                  <XAxis dataKey="name" stroke="#888" fontSize={9} />
                  <YAxis stroke="#888" fontSize={9} />
                  <Tooltip />
                  <Bar dataKey="count" fill="#d9b40f" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Quality metrics graph */}
          <div className="glass-card rounded-2xl p-6 border border-gold-500/10 space-y-4">
            <h4 className="text-xs font-extrabold text-slate-400 uppercase tracking-widest flex items-center gap-2">
              <LineIcon className="w-4.5 h-4.5 text-gold-500" /> Quality vs Trust Score Profile
            </h4>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={qualityData}>
                  <XAxis dataKey="name" stroke="#888" fontSize={8} />
                  <YAxis stroke="#888" fontSize={9} />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="Quality Score" stroke="#d9b40f" strokeWidth={2} />
                  <Line type="monotone" dataKey="Trust Index" stroke="#888" strokeWidth={1.5} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
