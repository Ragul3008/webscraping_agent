import React, { useEffect, useState } from 'react';
import { api } from '../utils/api';
import { Settings as SettingsIcon, Save, FolderOpen, ShieldCheck } from 'lucide-react';

export const SettingsPage: React.FC = () => {
  const [downloadFolder, setDownloadFolder] = useState('');
  const [concurrency] = useState(4);
  const [proxies, setProxies] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    const fetchSettings = async () => {
      try {
        const response = await api.get('/settings/');
        const data = response.data;
        setDownloadFolder(data.downloads_dir || '');
        // API doesn't return keys directly, only if configured
      } catch (err) {
        // ignore
      } finally {
        setLoading(false);
      }
    };
    fetchSettings();
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setMessage('');
    try {
      await api.post('/settings/', {
        concurrency,
        proxies: proxies.split('\n').filter(p => p.trim())
      });
      setMessage('Settings updated successfully!');
    } catch (err) {
      setMessage('Failed to save settings.');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="h-64 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-gold-500"></div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-100 flex items-center gap-2">
          <SettingsIcon className="w-5.5 h-5.5 text-gold-500" />
          Application Settings
        </h1>
        <p className="text-xs text-slate-400">Configure LLM credentials, local directories, proxy servers, and crawling limits.</p>
      </div>

      <form onSubmit={handleSave} className="glass-card rounded-2xl p-6 border border-gold-500/10 space-y-5">
        {message && (
          <div className="bg-gold-500/10 border border-gold-500/20 text-gold-400 text-xs font-semibold rounded-xl p-3">
            {message}
          </div>
        )}


        {/* Crawler settings */}
        <div className="space-y-4 pt-4">
          <h3 className="text-xs font-extrabold text-slate-400 uppercase tracking-widest flex items-center gap-1.5 pb-2 border-b border-gold-500/5">
            <FolderOpen className="w-4 h-4 text-gold-500" /> Local Storage Configuration
          </h3>
          <div>
            <label className="block text-xs font-semibold text-slate-400 mb-1.5 uppercase tracking-wider">Default Downloads Directory</label>
            <input 
              type="text"
              value={downloadFolder}
              onChange={(e) => setDownloadFolder(e.target.value)}
              className="w-full bg-darkbg-900 border border-gold-500/10 rounded-xl px-4 py-2.5 text-xs text-slate-200 opacity-60 cursor-not-allowed"
              disabled
            />
            <span className="text-[10px] text-slate-500 mt-1 block">To modify download paths, configure the app settings file directly.</span>
          </div>
        </div>

        {/* Advanced proxy rotation */}
        <div className="space-y-4 pt-4">
          <h3 className="text-xs font-extrabold text-slate-400 uppercase tracking-widest flex items-center gap-1.5 pb-2 border-b border-gold-500/5">
            <ShieldCheck className="w-4 h-4 text-gold-500" /> Proxy Rotation Setup
          </h3>
          <div>
            <label className="block text-xs font-semibold text-slate-400 mb-1.5 uppercase tracking-wider">Proxy Lists (One per line)</label>
            <textarea 
              placeholder="http://user:password@proxy_ip:port"
              value={proxies}
              onChange={(e) => setProxies(e.target.value)}
              className="w-full bg-darkbg-900 border border-gold-500/10 rounded-xl px-4 py-2.5 text-xs text-slate-200 h-20 resize-none font-mono"
            />
          </div>
        </div>

        <button 
          type="submit"
          disabled={saving}
          className="w-full bg-gold-gradient text-darkbg-950 font-bold py-2.5 rounded-xl text-xs flex items-center justify-center gap-2 hover:opacity-90 transition-opacity shadow-gold-border disabled:opacity-50"
        >
          <Save className="w-4 h-4 text-darkbg-950" />
          {saving ? 'Saving preferences...' : 'Save Settings'}
        </button>
      </form>
    </div>
  );
};
