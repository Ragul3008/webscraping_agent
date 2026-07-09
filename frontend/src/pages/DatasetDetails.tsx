import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api, STORAGE_BASE_URL } from '../utils/api';
import { 
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell
} from 'recharts';
import { 
  Image as ImageIcon, MessageSquare, BarChart3, 
  DownloadCloud, CheckCircle2, ShieldAlert,
  Sliders, Maximize2, ArrowLeft, Send, Sparkles
} from 'lucide-react';
import { useDownloadStore } from '../store/downloadStore';

export const DatasetDetails: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { tasks, triggerDownload } = useDownloadStore();

  const [activeTab, setActiveTab] = useState<'summary' | 'images' | 'chat'>('summary');
  const [dataset, setDataset] = useState<any>(null);
  const [recs, setRecs] = useState<any>({});
  const [analytics, setAnalytics] = useState<any>(null);
  const [images, setImages] = useState<any[]>([]);
  const [imagesTotal, setImagesTotal] = useState(0);
  const [imagesPage, setImagesPage] = useState(1);
  const [loading, setLoading] = useState(true);

  // Filter states for images tab
  const [hideBlurry, setHideBlurry] = useState(false);
  const [hideDuplicates, setHideDuplicates] = useState(false);
  const [minWidth, setMinWidth] = useState(0);
  const [selectedTag, setSelectedTag] = useState('');
  
  // Image zoom viewer modal state
  const [selectedImage, setSelectedImage] = useState<any>(null);

  // Chatbot states
  const [chatInput, setChatInput] = useState('');
  const [chatHistory, setChatHistory] = useState<any[]>([
    { role: 'assistant', content: 'Hi! Ask me anything about this dataset. I can write python preprocessing scripts or training boilerplate code.' }
  ]);
  const [chatLoading, setChatLoading] = useState(false);

  // Find active task if downloading
  const activeTask = tasks.find(t => t.dataset_id === parseInt(id || ''));

  const fetchDetails = async () => {
    try {
      const detailsRes = await api.get(`/datasets/${id}`);
      setDataset(detailsRes.data.dataset);
      setRecs(detailsRes.data.recommendations);
      
      const analyticsRes = await api.get(`/analytics/dataset/${id}`);
      setAnalytics(analyticsRes.data);
      
      const imagesRes = await api.get(`/datasets/${id}/images`, {
        params: {
          page: imagesPage,
          hide_blurry: hideBlurry,
          hide_duplicates: hideDuplicates,
          min_width: minWidth,
          tag: selectedTag
        }
      });
      setImages(imagesRes.data.images);
      setImagesTotal(imagesRes.data.total);
    } catch (err) {
      // ignore
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDetails();
  }, [id, imagesPage, hideBlurry, hideDuplicates, minWidth, selectedTag]);

  // Periodic poll to refresh dataset details if task completes
  useEffect(() => {
    let interval: any;
    if (activeTask && activeTask.status === 'RUNNING') {
      interval = setInterval(() => {
        fetchDetails();
      }, 3000);
    }
    return () => clearInterval(interval);
  }, [activeTask]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim() || chatLoading) return;
    
    const userMsg = { role: 'user', content: chatInput };
    setChatHistory(prev => [...prev, userMsg]);
    setChatInput('');
    setChatLoading(true);
    
    try {
      const response = await api.post(`/chat/dataset/${id}`, {
        history: chatHistory,
        message: userMsg.content
      });
      setChatHistory(prev => [...prev, { role: 'assistant', content: response.data.reply }]);
    } catch (err) {
      setChatHistory(prev => [...prev, { role: 'assistant', content: 'Error connecting to Gemini Chat module.' }]);
    } finally {
      setChatLoading(false);
    }
  };

  if (loading && !dataset) {
    return (
      <div className="h-96 flex items-center justify-center">
        <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-gold-500"></div>
      </div>
    );
  }

  const COLORS = ['#d9b40f', '#b78f09', '#fbe64d', '#734f07', '#563a07'];

  return (
    <div className="space-y-6">
      {/* Back Header Nav */}
      <button 
        onClick={() => navigate('/dashboard')}
        className="flex items-center gap-2 text-xs font-bold text-slate-400 hover:text-gold-400 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" /> Back to Dashboard
      </button>

      {/* Dataset Header Card */}
      <div className="glass-card rounded-2xl p-6 border border-gold-500/10 flex flex-col md:flex-row md:items-center justify-between gap-6 relative overflow-hidden">
        <div className="space-y-2">
          <div className="flex items-center gap-3">
            <span className="px-2.5 py-0.5 rounded-full bg-gold-500/10 border border-gold-500/20 text-gold-400 text-xs font-bold uppercase tracking-wider">
              {dataset.source}
            </span>
            <span className="text-xs text-slate-400 font-medium">License: {dataset.license}</span>
          </div>
          <h1 className="text-2xl font-extrabold text-slate-100">{dataset.name}</h1>
          <p className="text-xs text-slate-400 max-w-2xl">{dataset.description}</p>
        </div>
        
        {/* Dynamic Sync/Download state */}
        <div className="flex flex-col items-end shrink-0 gap-2">
          {activeTask ? (
            <div className="w-48 bg-darkbg-900 border border-gold-500/10 rounded-xl p-3.5 space-y-1.5 shadow-glass">
              <div className="flex justify-between items-center text-[10px]">
                <span className="text-gold-400 font-bold flex items-center gap-1">
                  <DownloadCloud className="w-3.5 h-3.5 animate-bounce" /> {activeTask.status}
                </span>
                <span className="text-slate-300 font-semibold">{activeTask.progress}%</span>
              </div>
              <div className="w-full bg-darkbg-950 rounded-full h-1.5 overflow-hidden">
                <div 
                  className="bg-gold-gradient h-1.5 rounded-full transition-all duration-300"
                  style={{ width: `${activeTask.progress}%` }}
                ></div>
              </div>
              <div className="flex justify-between text-[9px] text-slate-500">
                <span>Speed: {activeTask.speed}</span>
                <span>ETA: {activeTask.eta}</span>
              </div>
            </div>
          ) : dataset.image_count === 0 ? (
            <button 
              onClick={() => triggerDownload(dataset.id)}
              className="bg-gold-gradient text-darkbg-950 font-bold px-5 py-2.5 rounded-xl text-xs flex items-center gap-2 hover:opacity-90 transition-opacity shadow-gold-border"
            >
              <DownloadCloud className="w-4 h-4 text-darkbg-950" /> Sync Images Crawler
            </button>
          ) : (
            <div className="text-right">
              <span className="text-[10px] text-slate-500 font-bold uppercase tracking-widest block">Local Catalog Status</span>
              <span className="text-xs text-emerald-400 font-bold flex items-center gap-1 mt-1">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" /> Synced locally
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Tabs Menu */}
      <div className="flex border-b border-gold-500/10 gap-6">
        {[
          { id: 'summary', label: 'Summary & ML Metrics', icon: BarChart3 },
          { id: 'images', label: `Collected Images (${imagesTotal})`, icon: ImageIcon },
          { id: 'chat', label: 'AI Dataset Chatbot', icon: MessageSquare }
        ].map(tab => {
          const Icon = tab.icon;
          const active = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center gap-2 pb-3.5 text-sm font-semibold transition-all border-b-2 -mb-0.5 ${
                active 
                  ? 'border-gold-500 text-gold-400 font-bold' 
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <Icon className="w-4.5 h-4.5" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Tab Area 1: Summary */}
      {activeTab === 'summary' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Quality Metrics */}
          <div className="lg:col-span-2 space-y-6">
            {/* Top Scores Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[
                { title: "Quality Score", value: `${dataset.quality_score}%`, color: "text-gold-400" },
                { title: "Trust Index", value: `${dataset.trust_score}%`, color: "text-slate-200" },
                { title: "Duplicate Ratio", value: `${dataset.duplicate_ratio}%`, color: "text-slate-200" },
                { title: "Missing Annotations", value: dataset.missing_labels ? "Yes" : "No", color: dataset.missing_labels ? "text-amber-500" : "text-emerald-400" }
              ].map((card, i) => (
                <div key={i} className="glass-card rounded-2xl p-4 text-center border border-gold-500/5">
                  <span className="text-[9px] text-slate-400 font-extrabold uppercase tracking-wider block mb-1">{card.title}</span>
                  <span className={`text-xl font-black ${card.color}`}>{card.value}</span>
                </div>
              ))}
            </div>

            {/* Graphs Charts Card */}
            {analytics && analytics.total_images > 0 && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Recharts Pie Chart (Classes distribution) */}
                <div className="glass-card rounded-2xl p-5 border border-gold-500/10">
                  <h4 className="text-xs font-extrabold text-slate-400 uppercase tracking-widest mb-4">Classes Distribution</h4>
                  <div className="h-44">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={analytics.class_distribution}
                          cx="50%"
                          cy="50%"
                          innerRadius={45}
                          outerRadius={65}
                          paddingAngle={2}
                          dataKey="value"
                        >
                          {analytics.class_distribution.map((_: any, index: number) => (
                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                          ))}
                        </Pie>
                        <Tooltip />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                  {/* Legend */}
                  <div className="flex flex-wrap gap-x-4 gap-y-1 justify-center mt-2 text-[10px]">
                    {analytics.class_distribution.map((entry: any, i: number) => (
                      <div key={i} className="flex items-center gap-1.5">
                        <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: COLORS[i % COLORS.length] }}></span>
                        <span className="text-slate-400 font-semibold">{entry.name} ({entry.value})</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Bar Chart (Resolutions) */}
                <div className="glass-card rounded-2xl p-5 border border-gold-500/10">
                  <h4 className="text-xs font-extrabold text-slate-400 uppercase tracking-widest mb-4">Image Resolutions</h4>
                  <div className="h-52">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={analytics.resolution_distribution}>
                        <XAxis dataKey="resolution" stroke="#888" fontSize={9} />
                        <YAxis stroke="#888" fontSize={9} />
                        <Tooltip />
                        <Bar dataKey="count" fill="#d9b40f" radius={[4, 4, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              </div>
            )}

            {/* Preprocessing boilerplate code output */}
            <div className="glass-card rounded-2xl p-6 border border-gold-500/10 space-y-4">
              <h4 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                <Sliders className="w-4 h-4 text-gold-500" /> Model Preprocessing Pipeline
              </h4>
              <p className="text-xs text-slate-400">Copy this Python script to load and resize images collected for model training.</p>
              <pre className="bg-black/40 border border-gold-500/5 rounded-xl p-4 text-[11px] text-slate-300 font-mono overflow-x-auto">
{`import cv2
import os

def load_and_preprocess_dataset(dataset_dir):
    processed_images = []
    for root, dirs, files in os.walk(dataset_dir):
        for file in files:
            if file.endswith(('.png', '.jpg', '.jpeg')):
                img_path = os.path.join(root, file)
                img = cv2.imread(img_path)
                if img is not None:
                    # 1. Resize to target dimensions
                    img_resized = cv2.resize(img, (224, 224))
                    # 2. Normalize to float [0, 1]
                    img_normalized = img_resized.astype("float32") / 255.0
                    processed_images.append(img_normalized)
    return processed_images`}
              </pre>
            </div>
          </div>

          {/* AI recommendations side column */}
          <div className="space-y-6">
            <div className="glass-card rounded-2xl p-6 border border-gold-500/10 relative overflow-hidden">
              <div className="absolute top-0 right-0 w-24 h-24 bg-gold-500/5 blur-2xl rounded-full"></div>
              <h3 className="text-base font-bold text-slate-100 mb-4 gold-text-glow flex items-center gap-2">
                <Sparkles className="w-4.5 h-4.5 text-gold-500" />
                Gemini Training Recommendations
              </h3>
              
              <div className="space-y-4.5 text-xs">
                <div>
                  <span className="text-[10px] text-slate-500 font-extrabold uppercase tracking-wider block mb-1">Recommended Model</span>
                  <span className="font-semibold text-slate-200">{recs.recommended_model || 'ResNet-50'}</span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-500 font-extrabold uppercase tracking-wider block mb-1">Primary Use Case</span>
                  <span className="font-semibold text-slate-200">{recs.best_use_case || 'Image Classification'}</span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-500 font-extrabold uppercase tracking-wider block mb-1">Training Difficulty</span>
                  <span className="px-2 py-0.5 rounded-md bg-gold-500/10 border border-gold-500/20 text-gold-400 font-bold">
                    {recs.difficulty || 'Medium'}
                  </span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-500 font-extrabold uppercase tracking-wider block mb-1">Expected Target Accuracy</span>
                  <span className="font-bold text-emerald-400">{recs.expected_accuracy || '88.5%'}</span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-500 font-extrabold uppercase tracking-wider block mb-1">Preprocessing Steps</span>
                  <span className="text-slate-400 leading-relaxed block mt-0.5">{recs.preprocessing || 'Standard resizing and normalization.'}</span>
                </div>
                <div>
                  <span className="text-[10px] text-amber-500 font-extrabold uppercase tracking-wider flex items-center gap-1 mb-1">
                    <ShieldAlert className="w-3.5 h-3.5 text-amber-500" /> Potential Problems
                  </span>
                  <span className="text-slate-400 leading-relaxed block">{recs.potential_issues || 'Watch out for blurry inputs and duplicates.'}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab Area 2: Images Masonry */}
      {activeTab === 'images' && (
        <div className="space-y-6">
          {/* Controls filtering bar */}
          <div className="glass-card rounded-2xl p-4 border border-gold-500/10 flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-6 flex-wrap">
              <label className="flex items-center gap-2 text-xs font-semibold text-slate-300">
                <input 
                  type="checkbox" 
                  checked={hideBlurry} 
                  onChange={(e) => setHideBlurry(e.target.checked)}
                  className="rounded accent-gold-500 w-4 h-4"
                />
                Filter Blurry Images
              </label>
              
              <label className="flex items-center gap-2 text-xs font-semibold text-slate-300">
                <input 
                  type="checkbox" 
                  checked={hideDuplicates} 
                  onChange={(e) => setHideDuplicates(e.target.checked)}
                  className="rounded accent-gold-500 w-4 h-4"
                />
                Hide Near-Duplicates
              </label>

              <div className="flex items-center gap-2 text-xs text-slate-400 font-semibold">
                <span>Min Dimensions:</span>
                <select 
                  value={minWidth} 
                  onChange={(e) => setMinWidth(parseInt(e.target.value))}
                  className="bg-darkbg-900 border border-gold-500/10 rounded-lg px-2 py-1 text-slate-200 outline-none text-xs"
                >
                  <option value={0}>Any Resolution</option>
                  <option value={300}>SD (300px+)</option>
                  <option value={720}>HD (720px+)</option>
                  <option value={1080}>Full HD (1080px+)</option>
                </select>
              </div>
            </div>
            
            {/* Class tags input selector filter */}
            <input 
              type="text"
              placeholder="Filter by class tag..."
              value={selectedTag}
              onChange={(e) => setSelectedTag(e.target.value)}
              className="bg-darkbg-900 border border-gold-500/10 rounded-xl px-4 py-2 text-xs text-slate-200 w-48"
            />
          </div>

          {/* Pinterest-like Masonry Grid list */}
          {images.length === 0 ? (
            <div className="h-64 flex flex-col items-center justify-center space-y-2 text-slate-500">
              <ImageIcon className="w-10 h-10 text-slate-600" />
              <p className="text-xs">No preview images match the selected filter query criteria.</p>
            </div>
          ) : (
            <div className="columns-2 md:columns-3 lg:columns-4 gap-4 space-y-4">
              {images.map((img) => {
                // Local static asset path configuration
                const displayUrl = img.local_path 
                  ? `${STORAGE_BASE_URL}/${img.local_path.replace(/\\/g, '/').split('storage/')[1]}` 
                  : img.image_url;
                
                return (
                  <div 
                    key={img.id}
                    onClick={() => setSelectedImage(img)}
                    className="break-inside-avoid glass-card rounded-2xl overflow-hidden border border-gold-500/5 relative group cursor-pointer"
                  >
                    <img 
                      src={displayUrl} 
                      alt={img.caption || "Preview"} 
                      className="w-full h-auto object-cover max-h-72 group-hover:scale-[1.02] transition-transform duration-300"
                      loading="lazy"
                    />
                    
                    {/* Hover Overlay Panel */}
                    <div className="absolute inset-0 bg-gradient-to-t from-black/85 via-black/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity p-4 flex flex-col justify-end">
                      <p className="text-[10px] text-slate-200 font-medium line-clamp-2 leading-relaxed mb-2">
                        {img.caption || 'No caption generated.'}
                      </p>
                      
                      <div className="flex items-center justify-between">
                        <span className="text-[8px] text-gold-400 font-extrabold uppercase tracking-widest">
                          {img.width}x{img.height} px
                        </span>
                        <Maximize2 className="w-3.5 h-3.5 text-gold-500" />
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {/* Basic pagination controls */}
          {imagesTotal > images.length && (
            <div className="flex justify-center gap-4 pt-4">
              <button 
                onClick={() => setImagesPage(prev => Math.max(prev - 1, 1))}
                disabled={imagesPage === 1}
                className="px-4 py-2 bg-white/5 border border-white/5 rounded-xl text-xs font-semibold text-slate-300 disabled:opacity-30"
              >
                Previous Page
              </button>
              <button 
                onClick={() => setImagesPage(prev => prev + 1)}
                className="px-4 py-2 bg-white/5 border border-white/5 rounded-xl text-xs font-semibold text-slate-300"
              >
                Next Page
              </button>
            </div>
          )}
        </div>
      )}

      {/* Tab Area 3: AI chatbot Q&A */}
      {activeTab === 'chat' && (
        <div className="glass-card rounded-2xl border border-gold-500/10 overflow-hidden flex flex-col h-[500px]">
          {/* Chat Window Messages Area */}
          <div className="flex-1 p-6 space-y-4 overflow-y-auto bg-black/10">
            {chatHistory.map((msg, i) => (
              <div 
                key={i} 
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div className={`max-w-[75%] rounded-2xl px-4.5 py-3 text-xs leading-relaxed ${
                  msg.role === 'user'
                    ? 'bg-gold-gradient text-darkbg-950 font-medium shadow-gold-border'
                    : 'bg-darkbg-900 border border-gold-500/5 text-slate-300'
                }`}>
                  <p className="whitespace-pre-line">{msg.content}</p>
                </div>
              </div>
            ))}
            {chatLoading && (
              <div className="flex justify-start">
                <div className="bg-darkbg-900 border border-gold-500/5 rounded-2xl px-4 py-3 text-xs text-slate-400 flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-gold-500 animate-bounce"></span>
                  <span className="w-1.5 h-1.5 rounded-full bg-gold-500 animate-bounce delay-100"></span>
                  <span className="w-1.5 h-1.5 rounded-full bg-gold-500 animate-bounce delay-200"></span>
                  Gemini analyzing...
                </div>
              </div>
            )}
          </div>

          {/* Form input field */}
          <form onSubmit={handleSendMessage} className="p-4 border-t border-gold-500/10 bg-darkbg-900 flex gap-3">
            <input 
              type="text"
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              placeholder="Ask about model layers to use, generate PyTorch loaders..."
              className="flex-1 bg-darkbg-950 border border-gold-500/10 rounded-xl px-4.5 text-xs text-slate-200"
            />
            <button 
              type="submit"
              className="p-3 bg-gold-gradient text-darkbg-950 rounded-xl hover:opacity-90 transition-opacity shadow-gold-border shrink-0"
            >
              <Send className="w-4.5 h-4.5 text-darkbg-950" />
            </button>
          </form>
        </div>
      )}

      {/* Image zoom viewer modal dialog overlay */}
      {selectedImage && (
        <div className="fixed inset-0 bg-black/90 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="max-w-4xl w-full flex flex-col md:flex-row glass-card rounded-2xl border border-gold-500/20 overflow-hidden relative animate-in fade-in zoom-in-95 duration-200">
            {/* Left Image Area */}
            <div className="flex-1 bg-black flex items-center justify-center p-4">
              <img 
                src={selectedImage.local_path 
                  ? `${STORAGE_BASE_URL}/${selectedImage.local_path.replace(/\\/g, '/').split('storage/')[1]}` 
                  : selectedImage.image_url} 
                alt="Zoom" 
                className="max-h-[500px] object-contain w-full"
              />
            </div>
            
            {/* Right Meta Info sidebar panel */}
            <div className="w-80 border-t md:border-t-0 md:border-l border-gold-500/10 p-6 flex flex-col justify-between bg-darkbg-900">
              <div className="space-y-5">
                <div>
                  <span className="text-[9px] text-slate-500 font-extrabold uppercase tracking-widest block mb-1">Caption Description</span>
                  <p className="text-xs text-slate-200 leading-relaxed font-medium">{selectedImage.caption || 'Generating caption...'}</p>
                </div>
                <div>
                  <span className="text-[9px] text-slate-500 font-extrabold uppercase tracking-widest block mb-1.5">Class Tags / Keywords</span>
                  <div className="flex flex-wrap gap-1.5">
                    {selectedImage.tags_json && JSON.parse(selectedImage.tags_json).map((t: string) => (
                      <span key={t} className="px-2 py-0.5 rounded bg-gold-500/10 border border-gold-500/20 text-gold-400 text-[9px] font-bold uppercase tracking-wider">
                        {t}
                      </span>
                    ))}
                  </div>
                </div>
                <div>
                  <span className="text-[9px] text-slate-500 font-extrabold uppercase tracking-widest block mb-1">Image Specs</span>
                  <ul className="text-[10px] text-slate-400 space-y-1">
                    <li>Dimensions: <b>{selectedImage.width}x{selectedImage.height} px</b></li>
                    <li>Quality Blur Index: <b>{selectedImage.blur_score.toFixed(1)}</b></li>
                    <li>NSFW Safety Index: <b>{(selectedImage.nsfw_score * 100).toFixed(1)}%</b></li>
                  </ul>
                </div>
              </div>

              <div className="pt-6 border-t border-gold-500/5 flex justify-end gap-3">
                <button 
                  onClick={() => setSelectedImage(null)}
                  className="px-4 py-2 border border-white/5 text-slate-400 hover:text-slate-200 rounded-xl text-xs font-semibold"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
