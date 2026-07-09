import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Search, 
  DownloadCloud, 
  MessageSquareCode, 
  BarChart3, 
  FolderHeart,
  Settings, 
  ShieldCheck, 
  LogOut,
  Sparkles
} from 'lucide-react';
import { useAuthStore } from '../store/authStore';

interface SidebarProps {
  onLogout: () => void;
}

export const Sidebar: React.FC<SidebarProps> = () => {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const navItems = [
    { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/search', label: 'Global Search', icon: Search },
    { to: '/downloads', label: 'Downloads', icon: DownloadCloud },
    { to: '/chat', label: 'AI Chat Assistant', icon: MessageSquareCode },
    { to: '/collections', label: 'Collections', icon: FolderHeart },
    { to: '/analytics', label: 'Analytics', icon: BarChart3 },
  ];

  if (user?.is_admin) {
    navItems.push({ to: '/admin', label: 'Admin Portal', icon: ShieldCheck });
  }

  navItems.push({ to: '/settings', label: 'Settings', icon: Settings });

  return (
    <aside className="w-64 h-screen sticky top-0 flex flex-col border-r border-gold-500/10 bg-darkbg-900/80 backdrop-blur-md z-30">
      {/* Brand Logo Header */}
      <div className="p-6 border-b border-gold-500/10 flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-gold-gradient flex items-center justify-center shadow-gold-border animate-pulse">
          <Sparkles className="w-4 h-4 text-darkbg-950 font-bold" />
        </div>
        <div>
          <h1 className="text-sm font-extrabold gold-text-glow tracking-wider uppercase">WEBSCRAP AGENT</h1>
          <span className="text-[9px] text-gold-500 font-medium tracking-widest uppercase">AI Multi-Crawler</span>
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 px-4 py-6 space-y-1.5 overflow-y-auto">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center gap-3.5 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200 group ${
                  isActive
                    ? 'bg-gold-500/15 border-l-2 border-gold-500 text-gold-400 font-semibold shadow-gold-border'
                    : 'text-slate-400 hover:bg-white/5 hover:text-slate-200'
                }`
              }
            >
              <Icon className="w-5 h-5 transition-transform duration-200 group-hover:scale-110 group-hover:text-gold-400" />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>

      {/* User Session Profile Footing */}
      {user && (
        <div className="p-4 border-t border-gold-500/10 bg-black/30 flex items-center justify-between gap-3">
          <div className="flex items-center gap-3 overflow-hidden">
            <img 
              src={user.avatar_url || `https://api.dicebear.com/7.x/bottts/svg?seed=${user.email}`} 
              alt="Avatar" 
              className="w-10 h-10 rounded-full border border-gold-500/20 bg-darkbg-800"
            />
            <div className="truncate">
              <p className="text-xs font-semibold text-slate-200 truncate">{user.email}</p>
              <span className="text-[10px] text-gold-500 uppercase tracking-widest font-bold">
                {user.is_admin ? 'SysAdmin' : 'SaaS Member'}
              </span>
            </div>
          </div>
          <button 
            onClick={handleLogout}
            className="p-2 rounded-lg text-slate-400 hover:bg-red-500/10 hover:text-red-400 transition-colors"
            title="Log Out"
          >
            <LogOut className="w-5 h-5" />
          </button>
        </div>
      )}
    </aside>
  );
};
