import React, { useState } from 'react';
import { useAuthStore } from '../store/authStore';
import { useNavigate } from 'react-router-dom';
import { Sparkles, CheckCircle2, Server, Lock, Mail } from 'lucide-react';

export const LandingPage: React.FC = () => {
  const { login, register, error, loading } = useAuthStore();
  const navigate = useNavigate();
  
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isRegister) {
      const success = await register(email, password);
      if (success) {
        setIsRegister(false); // Go to login
      }
    } else {
      const success = await login(email, password);
      if (success) {
        navigate('/dashboard');
      }
    }
  };

  return (
    <div className="min-h-screen bg-darkbg-950 flex flex-col md:flex-row relative overflow-hidden font-sans">
      {/* Background Animated Gradient Mesh */}
      <div className="absolute inset-0 bg-gold-glow pointer-events-none opacity-40 z-0"></div>
      
      {/* Brand Hero Column */}
      <div className="flex-1 flex flex-col justify-center px-8 lg:px-16 py-12 z-10 select-none">
        <div className="max-w-lg space-y-6">
          <div className="flex items-center gap-3.5 mb-2">
            <div className="w-10 h-10 rounded-xl bg-gold-gradient flex items-center justify-center shadow-gold-border animate-pulse">
              <Sparkles className="w-5 h-5 text-darkbg-950" />
            </div>
            <span className="text-sm text-gold-400 font-extrabold tracking-widest uppercase">Platform Launch v1.0</span>
          </div>
          
          <h1 className="text-4xl lg:text-5xl font-extrabold tracking-tight text-white leading-tight">
            Discover, Build & Refine <span className="gold-text-glow font-black">AI Datasets</span> In Real-Time.
          </h1>
          
          <p className="text-slate-400 text-sm leading-relaxed max-w-md">
            The standard hub for machine learning developers. Aggregate image datasets from multi-engines, auto-tag using CLIP, filter duplicates via phash, and chat with data.
          </p>

          <div className="space-y-3.5 pt-4">
            {[
              "Aggregates search on HuggingFace, Kaggle, GitHub, Figshare",
              "Perceptual Hashing duplicate checking & blur removal",
              "Interactive AI dataset assistant Chatbot",
              "Real-time WebSocket active download managers"
            ].map((text, i) => (
              <div key={i} className="flex items-center gap-3">
                <CheckCircle2 className="w-5 h-5 text-gold-500 shrink-0" />
                <span className="text-xs text-slate-300 font-medium">{text}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Login / Auth Form Column */}
      <div className="flex-1 flex items-center justify-center p-6 lg:p-12 z-10">
        <div className="w-full max-w-md glass-card rounded-2xl p-8 relative overflow-hidden border border-gold-500/10">
          <div className="absolute top-0 right-0 w-32 h-32 bg-gold-500/5 blur-3xl rounded-full"></div>
          
          <div className="mb-6">
            <h2 className="text-2xl font-bold text-slate-100 gold-text-glow mb-1">
              {isRegister ? 'Create Account' : 'Welcome Developer'}
            </h2>
            <p className="text-xs text-slate-400">
              {isRegister ? 'Join our premium AI discovery platform today.' : 'Login to access your project workspaces.'}
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4 relative">
            {error && (
              <div className="bg-red-500/10 border border-red-500/20 text-red-400 text-xs font-semibold rounded-xl p-3">
                {error}
              </div>
            )}
            
            <div>
              <label className="block text-xs font-semibold text-slate-400 mb-1.5 uppercase tracking-wider">Email Address</label>
              <div className="relative">
                <Mail className="absolute left-4.5 top-3.5 w-4 h-4 text-slate-500" />
                <input 
                  type="email" 
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@domain.com"
                  className="w-full bg-darkbg-900 border border-gold-500/10 rounded-xl pl-12 pr-4 py-3 text-sm text-slate-200"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-400 mb-1.5 uppercase tracking-wider">Password</label>
              <div className="relative">
                <Lock className="absolute left-4.5 top-3.5 w-4 h-4 text-slate-500" />
                <input 
                  type="password" 
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full bg-darkbg-900 border border-gold-500/10 rounded-xl pl-12 pr-4 py-3 text-sm text-slate-200"
                  required
                />
              </div>
            </div>

            <button 
              type="submit" 
              disabled={loading}
              className="w-full bg-gold-gradient text-darkbg-950 font-bold py-3 px-4 rounded-xl text-sm hover:opacity-90 transition-opacity flex items-center justify-center gap-2 mt-6 shadow-gold-border disabled:opacity-50"
            >
              <Server className="w-4 h-4 text-darkbg-950" />
              {loading ? 'Processing session...' : isRegister ? 'Register' : 'Log In'}
            </button>
          </form>

          <div className="mt-6 text-center text-xs text-slate-400 border-t border-gold-500/10 pt-4">
            {isRegister ? 'Already have an account?' : 'Need a workspace profile?'}
            <button 
              onClick={() => setIsRegister(!isRegister)}
              className="text-gold-500 hover:text-gold-400 font-semibold ml-1.5 hover:underline"
            >
              {isRegister ? 'Log In' : 'Sign Up'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
