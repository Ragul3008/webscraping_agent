import React, { useEffect, useState } from 'react';
import { api } from '../utils/api';
import { Send, Sparkles, AlertCircle } from 'lucide-react';

export const ChatAssistantPage: React.FC = () => {
  const [datasets, setDatasets] = useState<any[]>([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState<number | ''>('');
  const [chatInput, setChatInput] = useState('');
  const [chatHistory, setChatHistory] = useState<any[]>([
    { role: 'assistant', content: 'Select a dataset context on the sidebar panel, then ask me to write PyTorch training scripts, calculate batch loaders, or compare data metrics!' }
  ]);
  const [chatLoading, setChatLoading] = useState(false);
  const [loadingDatasets, setLoadingDatasets] = useState(true);

  useEffect(() => {
    const fetchDatasets = async () => {
      try {
        const response = await api.get('/datasets/');
        setDatasets(response.data);
        if (response.data.length > 0) {
          setSelectedDatasetId(response.data[0].id);
        }
      } catch (err) {
        // ignore
      } finally {
        setLoadingDatasets(false);
      }
    };
    fetchDatasets();
  }, []);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim() || chatLoading || selectedDatasetId === '') return;
    
    const userMsg = { role: 'user', content: chatInput };
    setChatHistory(prev => [...prev, userMsg]);
    setChatInput('');
    setChatLoading(true);
    
    try {
      const response = await api.post(`/chat/dataset/${selectedDatasetId}`, {
        history: chatHistory,
        message: userMsg.content
      });
      setChatHistory(prev => [...prev, { role: 'assistant', content: response.data.reply }]);
    } catch (err) {
      setChatHistory(prev => [...prev, { role: 'assistant', content: 'Connection timed out. Ensure your Gemini API credentials are valid.' }]);
    } finally {
      setChatLoading(false);
    }
  };

  return (
    <div className="flex flex-col md:flex-row gap-6 h-[calc(100vh-10rem)]">
      {/* Sidebar Selector */}
      <div className="w-full md:w-64 glass-card rounded-2xl p-5 border border-gold-500/10 flex flex-col justify-between shrink-0 h-48 md:h-full">
        <div className="space-y-4 overflow-hidden flex flex-col h-full">
          <div>
            <h3 className="text-sm font-bold text-slate-100 flex items-center gap-1.5">
              <Sparkles className="w-4 h-4 text-gold-500" /> Active Context
            </h3>
            <p className="text-[10px] text-slate-500 mt-1 leading-normal">Choose which dataset details to feed into the prompt engine.</p>
          </div>
          
          {loadingDatasets ? (
            <div className="space-y-2 flex-1">
              <div className="h-9 rounded-xl bg-white/5 animate-pulse"></div>
            </div>
          ) : datasets.length === 0 ? (
            <div className="text-[10px] text-slate-500 flex items-center gap-1.5 pt-3">
              <AlertCircle className="w-4.5 h-4.5" /> No datasets synced.
            </div>
          ) : (
            <div className="space-y-2 overflow-y-auto flex-1 pr-1">
              {datasets.map(d => (
                <button
                  key={d.id}
                  onClick={() => {
                    setSelectedDatasetId(d.id);
                    setChatHistory([{ role: 'assistant', content: `Context switched to: "${d.name}". Let's discuss model strategies.` }]);
                  }}
                  className={`w-full text-left px-3.5 py-2.5 rounded-xl text-xs truncate font-semibold border transition-all ${
                    selectedDatasetId === d.id
                      ? 'bg-gold-500/10 border-gold-500/30 text-gold-400'
                      : 'bg-white/5 border-white/5 text-slate-400 hover:bg-white/10'
                  }`}
                >
                  {d.name}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Chat Bot Area */}
      <div className="flex-1 glass-card rounded-2xl border border-gold-500/10 overflow-hidden flex flex-col h-full">
        {/* Chat Window Messages */}
        <div className="flex-1 p-6 space-y-4 overflow-y-auto bg-black/10">
          {chatHistory.map((msg, i) => (
            <div 
              key={i} 
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div className={`max-w-[80%] rounded-2xl px-4.5 py-3 text-xs leading-relaxed ${
                msg.role === 'user'
                  ? 'bg-gold-gradient text-darkbg-950 font-semibold shadow-gold-border'
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
                Aura reasoning...
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
            disabled={selectedDatasetId === ''}
            placeholder={selectedDatasetId === '' ? "Sync a dataset to activate AI Chatbot..." : "Ask questions, generate scripts, compare metrics..."}
            className="flex-1 bg-darkbg-950 border border-gold-500/10 rounded-xl px-4.5 text-xs text-slate-200 disabled:opacity-50"
          />
          <button 
            type="submit"
            disabled={selectedDatasetId === ''}
            className="p-3 bg-gold-gradient text-darkbg-950 rounded-xl hover:opacity-90 transition-opacity shadow-gold-border shrink-0 disabled:opacity-50"
          >
            <Send className="w-4.5 h-4.5 text-darkbg-950" />
          </button>
        </form>
      </div>
    </div>
  );
};
