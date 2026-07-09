import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { useAuthStore } from './store/authStore';

// Import Pages
import { LandingPage } from './pages/LandingPage';
import { Dashboard } from './pages/Dashboard';
import { SearchPage } from './pages/SearchPage';
import { DatasetDetails } from './pages/DatasetDetails';
import { DownloadsPage } from './pages/DownloadsPage';
import { ChatAssistantPage } from './pages/ChatAssistantPage';
import { CollectionsPage } from './pages/CollectionsPage';
import { AnalyticsPage } from './pages/AnalyticsPage';
import { AdminPage } from './pages/AdminPage';
import { SettingsPage } from './pages/SettingsPage';

// Import Layout Components
import { Sidebar } from './components/Sidebar';
import { Navbar } from './components/Navbar';

const AppLayout: React.FC = () => {
  const location = useLocation();
  
  // Dynamic page title mapping based on route path
  const getPageTitle = (path: string) => {
    if (path.startsWith('/dashboard')) return 'Overview Dashboard';
    if (path.startsWith('/search')) return 'AI Global Search';
    if (path.startsWith('/dataset/')) return 'Dataset Details Hub';
    if (path.startsWith('/downloads')) return 'Downloads Queue';
    if (path.startsWith('/chat')) return 'AI Preprocessing Chatbot';
    if (path.startsWith('/collections')) return 'Collections Portfolio';
    if (path.startsWith('/analytics')) return 'System Analytics';
    if (path.startsWith('/admin')) return 'SysAdmin Console';
    if (path.startsWith('/settings')) return 'Platform Preferences';
    return 'Dataset Discovery';
  };

  return (
    <div className="flex bg-darkbg-950 min-h-screen text-slate-100 font-sans">
      {/* Sidebar Navigation */}
      <Sidebar onLogout={() => {}} />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        <Navbar title={getPageTitle(location.pathname)} />
        <main className="flex-1 p-8 overflow-y-auto">
          <Routes>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/search" element={<SearchPage />} />
            <Route path="/dataset/:id" element={<DatasetDetails />} />
            <Route path="/downloads" element={<DownloadsPage />} />
            <Route path="/chat" element={<ChatAssistantPage />} />
            <Route path="/collections" element={<CollectionsPage />} />
            <Route path="/analytics" element={<AnalyticsPage />} />
            <Route path="/admin" element={<AdminPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </main>
      </div>
    </div>
  );
};

export const App: React.FC = () => {
  const { token, fetchMe, loading } = useAuthStore();

  useEffect(() => {
    fetchMe();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-darkbg-950 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-gold-500"></div>
      </div>
    );
  }

  return (
    <BrowserRouter>
      <Routes>
        {token ? (
          <Route path="/*" element={<AppLayout />} />
        ) : (
          <>
            <Route path="/" element={<LandingPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </>
        )}
      </Routes>
    </BrowserRouter>
  );
};

export default App;
