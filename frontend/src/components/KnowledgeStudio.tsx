import React, { useState, useEffect } from 'react';
import {
  Brain, Search, Plus, Trash2, BookOpen, Sparkles, X, CheckCircle, RefreshCw, Layers, Database
} from 'lucide-react';

interface KnowledgeStudioProps {
  isOpen: boolean;
  onClose: () => void;
}

interface ConceptItem {
  id: number;
  topic: string;
  category: string;
  summary: string;
  content: string;
  source: string;
  confidence: number;
  created_at?: string;
  updated_at?: string;
}

interface BrainStats {
  total_concepts: number;
  categories: Record<string, number>;
  sources: Record<string, number>;
  last_trained: string;
}

export const KnowledgeStudio: React.FC<KnowledgeStudioProps> = ({ isOpen, onClose }) => {
  const [concepts, setConcepts] = useState<ConceptItem[]>([]);
  const [stats, setStats] = useState<BrainStats | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [activeTab, setActiveTab] = useState<'concepts' | 'teach' | 'train' | 'stats'>('concepts');

  // Teach Form
  const [teachTopic, setTeachTopic] = useState<string>('');
  const [teachContent, setTeachContent] = useState<string>('');
  const [teachCategory, setTeachCategory] = useState<string>('General Knowledge');
  const [teachSuccess, setTeachSuccess] = useState<string>('');

  // Document Train Form
  const [trainText, setTrainText] = useState<string>('');
  const [trainCategory, setTrainCategory] = useState<string>('Document Trained');
  const [trainSuccess, setTrainSuccess] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const fetchKnowledge = async () => {
    try {
      const url = selectedCategory === 'all' ? '/api/knowledge' : `/api/knowledge?category=${encodeURIComponent(selectedCategory)}`;
      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        setConcepts(data.concepts || []);
      }
    } catch (e) {
      console.error('Failed to fetch knowledge:', e);
    }
  };

  const fetchStats = async () => {
    try {
      const res = await fetch('/api/knowledge/stats');
      if (res.ok) {
        const data = await res.json();
        setStats(data);
      }
    } catch (e) {
      console.error('Failed to fetch stats:', e);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchKnowledge();
      fetchStats();
    }
  }, [isOpen, selectedCategory]);

  const handleTeachSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!teachTopic.trim() || !teachContent.trim()) return;

    setIsLoading(true);
    setTeachSuccess('');
    try {
      const res = await fetch('/api/knowledge/teach', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          topic: teachTopic.trim(),
          content: teachContent.trim(),
          category: teachCategory
        })
      });
      if (res.ok) {
        setTeachSuccess(`Learned: "${teachTopic}" successfully!`);
        setTeachTopic('');
        setTeachContent('');
        fetchKnowledge();
        fetchStats();
      }
    } catch (e) {
      console.error('Failed to teach concept:', e);
    } finally {
      setIsLoading(false);
    }
  };

  const handleTrainSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!trainText.trim()) return;

    setIsLoading(true);
    setTrainSuccess('');
    try {
      const res = await fetch('/api/knowledge/train', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: trainText.trim(),
          category: trainCategory
        })
      });
      if (res.ok) {
        const data = await res.json();
        setTrainSuccess(`Successfully extracted and learned ${data.concepts_learned} concepts!`);
        setTrainText('');
        fetchKnowledge();
        fetchStats();
      }
    } catch (e) {
      console.error('Failed to train text:', e);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteConcept = async (id: number) => {
    try {
      const res = await fetch(`/api/knowledge/${id}`, { method: 'DELETE' });
      if (res.ok) {
        fetchKnowledge();
        fetchStats();
      }
    } catch (e) {
      console.error('Failed to delete concept:', e);
    }
  };

  const handleReseed = async () => {
    setIsLoading(true);
    try {
      const res = await fetch('/api/knowledge/seed', { method: 'POST' });
      if (res.ok) {
        fetchKnowledge();
        fetchStats();
      }
    } catch (e) {
      console.error('Failed to reseed:', e);
    } finally {
      setIsLoading(false);
    }
  };

  const filteredConcepts = concepts.filter(c =>
    c.topic.toLowerCase().includes(searchQuery.toLowerCase()) ||
    c.summary.toLowerCase().includes(searchQuery.toLowerCase()) ||
    c.content.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/80 backdrop-blur-md transition-all duration-300">
      <div className="w-full max-w-2xl bg-slate-950 border-l border-emerald-500/40 text-slate-100 flex flex-col h-full shadow-2xl shadow-emerald-950/50">
        
        {/* Header */}
        <div className="p-4 sm:p-5 border-b border-emerald-500/30 bg-gradient-to-r from-emerald-950/80 via-slate-900 to-slate-950 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-emerald-600/30 border border-emerald-500/60 text-emerald-400">
              <Brain className="w-6 h-6 text-emerald-400" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white tracking-wide flex items-center gap-2">
                ARHIEA NEURAL BRAIN STUDIO
                <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
                  Continuous Learning
                </span>
              </h2>
              <p className="text-xs text-emerald-200/80">Persistent Neural Memory & Offline Intelligence Engine</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Top Telemetry Stats Strip */}
        {stats && (
          <div className="px-5 py-3 bg-slate-900/90 border-b border-slate-800 flex items-center justify-between text-xs font-mono">
            <div className="flex items-center gap-4">
              <span className="text-slate-400">
                Concepts: <strong className="text-emerald-400 text-sm">{stats.total_concepts}</strong>
              </span>
              <span className="text-slate-400">
                Domains: <strong className="text-cyan-400">{Object.keys(stats.categories || {}).length}</strong>
              </span>
            </div>
            <button
              onClick={handleReseed}
              disabled={isLoading}
              className="text-[11px] text-emerald-300 hover:text-white flex items-center gap-1.5 transition"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
              Re-seed Curriculum
            </button>
          </div>
        )}

        {/* Tab Navigation */}
        <div className="flex border-b border-slate-800 bg-slate-900/60 px-4 pt-2 gap-2 text-xs font-semibold">
          <button
            onClick={() => setActiveTab('concepts')}
            className={`pb-2.5 px-3 border-b-2 transition ${
              activeTab === 'concepts'
                ? 'border-emerald-500 text-emerald-400 font-bold'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            Learned Concepts ({filteredConcepts.length})
          </button>
          <button
            onClick={() => setActiveTab('teach')}
            className={`pb-2.5 px-3 border-b-2 transition flex items-center gap-1.5 ${
              activeTab === 'teach'
                ? 'border-emerald-500 text-emerald-400 font-bold'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Plus className="w-3.5 h-3.5" />
            Teach Concept
          </button>
          <button
            onClick={() => setActiveTab('train')}
            className={`pb-2.5 px-3 border-b-2 transition flex items-center gap-1.5 ${
              activeTab === 'train'
                ? 'border-emerald-500 text-emerald-400 font-bold'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <BookOpen className="w-3.5 h-3.5" />
            Train from Document
          </button>
        </div>

        {/* Tab Contents */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4">
          
          {/* TAB 1: CONCEPTS LIST */}
          {activeTab === 'concepts' && (
            <div className="space-y-4">
              {/* Search Bar */}
              <div className="relative">
                <Search className="w-4 h-4 absolute left-3 top-3 text-slate-500" />
                <input
                  type="text"
                  placeholder="Search internal knowledge base..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 rounded-xl pl-9 pr-4 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500/50"
                />
              </div>

              {/* Categories Pills */}
              {stats && (
                <div className="flex items-center gap-1.5 overflow-x-auto pb-1 text-xs">
                  <button
                    onClick={() => setSelectedCategory('all')}
                    className={`px-3 py-1 rounded-full shrink-0 transition ${
                      selectedCategory === 'all'
                        ? 'bg-emerald-600 text-white font-bold'
                        : 'bg-slate-900 text-slate-400 border border-slate-800'
                    }`}
                  >
                    All ({stats.total_concepts})
                  </button>
                  {Object.entries(stats.categories).map(([cat, count]) => (
                    <button
                      key={cat}
                      onClick={() => setSelectedCategory(cat)}
                      className={`px-3 py-1 rounded-full shrink-0 transition ${
                        selectedCategory === cat
                          ? 'bg-emerald-600 text-white font-bold'
                          : 'bg-slate-900 text-slate-400 border border-slate-800'
                      }`}
                    >
                      {cat} ({count})
                    </button>
                  ))}
                </div>
              )}

              {/* Concepts Cards */}
              <div className="space-y-3">
                {filteredConcepts.length === 0 ? (
                  <p className="text-center text-xs text-slate-500 py-10">No concepts found matching your query.</p>
                ) : (
                  filteredConcepts.map((c) => (
                    <div
                      key={c.id}
                      className="p-4 rounded-2xl bg-slate-900/90 border border-slate-800 hover:border-emerald-500/40 transition space-y-2"
                    >
                      <div className="flex items-center justify-between">
                        <h4 className="font-bold text-white text-sm text-emerald-300">{c.topic}</h4>
                        <div className="flex items-center gap-2">
                          <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-slate-950 border border-slate-700 text-slate-300">
                            {c.category}
                          </span>
                          <button
                            onClick={() => handleDeleteConcept(c.id)}
                            className="p-1 rounded-lg text-slate-500 hover:text-rose-400 transition"
                            title="Delete Concept"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </div>
                      <p className="text-xs text-slate-300 leading-relaxed">{c.summary}</p>
                      <details className="text-[11px] text-slate-400 cursor-pointer pt-1">
                        <summary className="hover:text-emerald-300 select-none">View Full Neural Memory</summary>
                        <div className="mt-2 p-3 rounded-xl bg-slate-950/80 border border-slate-800 text-slate-300 font-mono text-xs whitespace-pre-line leading-relaxed">
                          {c.content}
                        </div>
                      </details>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}

          {/* TAB 2: TEACH CONCEPT */}
          {activeTab === 'teach' && (
            <form onSubmit={handleTeachSubmit} className="space-y-4">
              {teachSuccess && (
                <div className="p-3 rounded-xl bg-emerald-950/80 border border-emerald-500/50 text-xs text-emerald-300 flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 shrink-0" />
                  <span>{teachSuccess}</span>
                </div>
              )}

              <div>
                <label className="text-xs font-mono uppercase text-slate-400 block mb-1.5">Topic / Title</label>
                <input
                  type="text"
                  placeholder="e.g. My Favorite Restaurant, Quantum Entanglement, Doctor Info"
                  value={teachTopic}
                  onChange={(e) => setTeachTopic(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3.5 py-2.5 text-xs text-white focus:outline-none focus:border-emerald-500"
                  required
                />
              </div>

              <div>
                <label className="text-xs font-mono uppercase text-slate-400 block mb-1.5">Domain Category</label>
                <select
                  value={teachCategory}
                  onChange={(e) => setTeachCategory(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3.5 py-2.5 text-xs text-white focus:outline-none focus:border-emerald-500"
                >
                  <option value="General Knowledge">General Knowledge</option>
                  <option value="Road & Emergency Intelligence">Road & Emergency Intelligence</option>
                  <option value="Computer Science & AI">Computer Science & AI</option>
                  <option value="Physics & Cosmology">Physics & Cosmology</option>
                  <option value="Biology & Medicine">Biology & Medicine</option>
                  <option value="User Learned">User Personal Fact</option>
                </select>
              </div>

              <div>
                <label className="text-xs font-mono uppercase text-slate-400 block mb-1.5">Detailed Knowledge Content</label>
                <textarea
                  rows={6}
                  placeholder="Provide complete explanation, facts, formulas, or instructions..."
                  value={teachContent}
                  onChange={(e) => setTeachContent(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 rounded-xl p-3 text-xs text-white focus:outline-none focus:border-emerald-500 leading-relaxed"
                  required
                />
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className="w-full py-3 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs uppercase tracking-wider transition shadow-lg shadow-emerald-950/60 disabled:opacity-50"
              >
                {isLoading ? 'Learning Concept...' : 'Save & Learn Concept into Brain'}
              </button>
            </form>
          )}

          {/* TAB 3: TRAIN FROM DOCUMENT */}
          {activeTab === 'train' && (
            <form onSubmit={handleTrainSubmit} className="space-y-4">
              {trainSuccess && (
                <div className="p-3 rounded-xl bg-emerald-950/80 border border-emerald-500/50 text-xs text-emerald-300 flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 shrink-0" />
                  <span>{trainSuccess}</span>
                </div>
              )}

              <div>
                <label className="text-xs font-mono uppercase text-slate-400 block mb-1.5">Document Domain</label>
                <input
                  type="text"
                  placeholder="e.g. Operating Systems, Chemistry Notes, Project Spec"
                  value={trainCategory}
                  onChange={(e) => setTrainCategory(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3.5 py-2.5 text-xs text-white focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div>
                <label className="text-xs font-mono uppercase text-slate-400 block mb-1.5">
                  Paste Documentation, Markdown, or Notes
                </label>
                <textarea
                  rows={10}
                  placeholder="Paste multi-topic notes, markdown articles, or research summaries. ARHIEA will parse headers and semantic chunks to extract distinct concepts..."
                  value={trainText}
                  onChange={(e) => setTrainText(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 rounded-xl p-3 text-xs text-white focus:outline-none focus:border-emerald-500 leading-relaxed font-mono"
                  required
                />
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className="w-full py-3 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs uppercase tracking-wider transition shadow-lg shadow-emerald-950/60 disabled:opacity-50"
              >
                {isLoading ? 'Ingesting & Training...' : 'Train Brain from Document'}
              </button>
            </form>
          )}

        </div>

      </div>
    </div>
  );
};
