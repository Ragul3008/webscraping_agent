import React, { useEffect, useState } from 'react';
import { useWorkspaceStore } from '../store/workspaceStore';
import { Briefcase, FolderPlus, Compass } from 'lucide-react';

interface NavbarProps {
  title: string;
}

export const Navbar: React.FC<NavbarProps> = ({ title }) => {
  const { projects, activeProject, fetchProjects, selectProject, createProject } = useWorkspaceStore();
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newProjName, setNewProjName] = useState('');
  const [newProjDesc, setNewProjDesc] = useState('');

  useEffect(() => {
    fetchProjects();
  }, []);

  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newProjName.trim()) return;
    await createProject(newProjName, newProjDesc);
    setNewProjName('');
    setNewProjDesc('');
    setShowCreateModal(false);
  };

  return (
    <header className="h-16 sticky top-0 px-8 border-b border-gold-500/10 bg-darkbg-950/70 backdrop-blur-md flex items-center justify-between z-20">
      {/* Title */}
      <h2 className="text-xl font-bold tracking-tight text-slate-100 flex items-center gap-2">
        <Compass className="w-5 h-5 text-gold-500" />
        {title}
      </h2>

      {/* Workspace Manager */}
      <div className="flex items-center gap-4">
        {/* Project Selector dropdown */}
        <div className="flex items-center gap-2 bg-darkbg-900 border border-gold-500/15 rounded-xl px-3.5 py-1.5 shadow-glass">
          <Briefcase className="w-4 h-4 text-gold-500" />
          <select 
            value={activeProject?.id || ''} 
            onChange={(e) => {
              const proj = projects.find(p => p.id === parseInt(e.target.value));
              if (proj) selectProject(proj);
            }}
            className="bg-transparent text-xs font-semibold text-slate-200 border-none outline-none cursor-pointer pr-4"
          >
            {projects.length === 0 ? (
              <option value="" disabled className="bg-darkbg-950">No workspaces</option>
            ) : (
              projects.map(p => (
                <option key={p.id} value={p.id} className="bg-darkbg-950 text-slate-200">{p.name}</option>
              ))
            )}
          </select>
        </div>

        {/* Add Workspace Button */}
        <button 
          onClick={() => setShowCreateModal(true)}
          className="p-2 bg-gold-500/10 border border-gold-500/20 text-gold-400 hover:bg-gold-500/20 rounded-xl transition-all shadow-glass"
          title="Create New Project Workspace"
        >
          <FolderPlus className="w-4.5 h-4.5" />
        </button>
      </div>

      {/* Create Project Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="w-full max-w-md glass-card rounded-2xl p-6 relative overflow-hidden border border-gold-500/20 animate-in fade-in zoom-in-95 duration-200">
            <h3 className="text-lg font-bold text-slate-100 mb-4 gold-text-glow flex items-center gap-2">
              <FolderPlus className="w-5 h-5 text-gold-500" />
              Create Project Workspace
            </h3>
            <form onSubmit={handleCreateProject} className="space-y-4">
              <div>
                <label className="block text-xs text-slate-400 font-semibold mb-1 uppercase tracking-wider">Workspace Name</label>
                <input 
                  type="text" 
                  value={newProjName}
                  onChange={(e) => setNewProjName(e.target.value)}
                  placeholder="e.g. Brain Tumor Classification"
                  className="w-full bg-darkbg-900 border border-gold-500/10 rounded-xl px-4 py-2.5 text-sm text-slate-200"
                  required
                />
              </div>
              <div>
                <label className="block text-xs text-slate-400 font-semibold mb-1 uppercase tracking-wider">Description</label>
                <textarea 
                  value={newProjDesc}
                  onChange={(e) => setNewProjDesc(e.target.value)}
                  placeholder="Describe your dataset requirements or model goals..."
                  className="w-full bg-darkbg-900 border border-gold-500/10 rounded-xl px-4 py-2.5 text-sm text-slate-200 h-24 resize-none"
                />
              </div>
              <div className="flex justify-end gap-3 pt-2">
                <button 
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 text-xs font-semibold text-slate-400 hover:text-slate-200"
                >
                  Cancel
                </button>
                <button 
                  type="submit"
                  className="px-5 py-2 text-xs font-semibold bg-gold-gradient text-darkbg-950 rounded-xl hover:opacity-90 shadow-gold-border"
                >
                  Create Project
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </header>
  );
};
