import React, { useEffect, useState } from 'react';
import { api } from '../utils/api';
import { ShieldAlert, Users, Terminal, Activity } from 'lucide-react';

export const AdminPage: React.FC = () => {
  const [users, setUsers] = useState<any[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [logs, setLogs] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAdminData = async () => {
      try {
        const usersRes = await api.get('/admin/users');
        setUsers(usersRes.data);
        
        const statsRes = await api.get('/admin/stats');
        setStats(statsRes.data);
        
        const logsRes = await api.get('/admin/logs');
        setLogs(logsRes.data.logs);
      } catch (err) {
        // ignore
      } finally {
        setLoading(false);
      }
    };
    fetchAdminData();
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
          <ShieldAlert className="w-5.5 h-5.5 text-gold-500" />
          SysAdmin Control Portal
        </h1>
        <p className="text-xs text-slate-400">Monitor active user profiles, review downloads volumes, and audit backend console logs.</p>
      </div>

      {/* Stats row */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[
            { title: "Registered Users", value: stats.total_users, desc: "SaaS Workspace profiles", icon: Users },
            { title: "Datasets Cataloged", value: stats.total_datasets, desc: "Discovered repositories", icon: Activity },
            { title: "Download Tasks Initiated", value: stats.total_downloads, desc: "Task queue transactions", icon: Terminal }
          ].map((item, i) => {
            const Icon = item.icon;
            return (
              <div key={i} className="glass-card rounded-2xl p-5 border border-gold-500/10">
                <div className="flex justify-between items-center mb-3">
                  <span className="text-[10px] text-slate-500 font-extrabold uppercase tracking-wider">{item.title}</span>
                  <Icon className="w-4 h-4 text-gold-500" />
                </div>
                <h3 className="text-2xl font-black text-slate-100">{item.value}</h3>
                <p className="text-[10px] text-slate-400 mt-1">{item.desc}</p>
              </div>
            );
          })}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* User list */}
        <div className="glass-card rounded-2xl p-6 border border-gold-500/10 space-y-4 lg:col-span-1">
          <h4 className="text-xs font-extrabold text-slate-400 uppercase tracking-widest flex items-center gap-1.5">
            <Users className="w-4.5 h-4.5 text-gold-500" /> Member Directory
          </h4>
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {users.map(u => (
              <div key={u.id} className="flex justify-between items-center p-3 bg-black/20 rounded-xl border border-white/5">
                <div className="truncate">
                  <p className="text-xs font-semibold text-slate-200 truncate">{u.email}</p>
                  <span className="text-[9px] text-slate-500">ID: {u.id}</span>
                </div>
                {u.is_admin && (
                  <span className="px-2 py-0.5 rounded bg-gold-500/10 border border-gold-500/20 text-gold-400 text-[8px] font-bold uppercase tracking-wider">
                    Admin
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* System logs view */}
        <div className="glass-card rounded-2xl p-6 border border-gold-500/10 space-y-4 lg:col-span-2 flex flex-col">
          <h4 className="text-xs font-extrabold text-slate-400 uppercase tracking-widest flex items-center gap-1.5">
            <Terminal className="w-4.5 h-4.5 text-gold-500" /> Crawler Execution Console
          </h4>
          <div className="bg-black/40 border border-gold-500/5 rounded-xl p-4 h-72 overflow-y-auto font-mono text-[10px] text-slate-300 space-y-1">
            {logs.map((logLine, i) => (
              <div key={i} className="leading-relaxed hover:bg-white/5 px-1 py-0.5 rounded transition-colors">
                {logLine}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
