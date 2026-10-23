import React, { useState, useEffect } from 'react';
import { Settings, Key, Shield, Cpu, Mic, Eye, MapPin, Trash2, X, Check, Globe, Sparkles, ExternalLink, RefreshCw } from 'lucide-react';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({ isOpen, onClose }) => {
  const [apiKey, setApiKey] = useState<string>('');
  const [geminiKey, setGeminiKey] = useState<string>('');
  const [model, setModel] = useState<string>('google/gemini-2.5-flash');
  const [customModel, setCustomModel] = useState<string>('');
  const [isCustomModel, setIsCustomModel] = useState<boolean>(false);
  const [cameraEnabled, setCameraEnabled] = useState<boolean>(false);
  const [locationEnabled, setLocationEnabled] = useState<boolean>(true);
  const [learningEnabled, setLearningEnabled] = useState<boolean>(true);
  const [voiceFirstMode, setVoiceFirstMode] = useState<boolean>(false);
  const [saveStatus, setSaveStatus] = useState<string>('');
  const [testStatus, setTestStatus] = useState<string>('');
  const [isTesting, setIsTesting] = useState<boolean>(false);

  useEffect(() => {
    if (isOpen) {
      fetch('/api/settings')
        .then((res) => res.json())
        .then((data) => {
          const currentModel = data.OPENROUTER_MODEL || 'google/gemini-2.5-flash';
          const presetModels = [
            'google/gemini-2.5-flash',
            'google/gemini-2.5-pro',
            'anthropic/claude-3.5-sonnet',
            'openai/gpt-4o',
            'openai/gpt-4o-mini',
            'deepseek/deepseek-r1',
            'meta-llama/llama-3.3-70b-instruct',
            'qwen/qwen-2.5-72b-instruct'
          ];
          if (presetModels.includes(currentModel)) {
            setModel(currentModel);
            setIsCustomModel(false);
          } else {
            setModel('custom');
            setCustomModel(currentModel);
            setIsCustomModel(true);
          }
          setCameraEnabled(data.CAMERA_ENABLED || false);
          setLocationEnabled(data.LOCATION_ENABLED || true);
          setLearningEnabled(data.LEARNING_ENABLED || true);
          setVoiceFirstMode(data.VOICE_FIRST_MODE || false);
        })
        .catch((e) => console.error(e));
    }
  }, [isOpen]);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    const finalModel = isCustomModel ? (customModel.trim() || 'google/gemini-2.5-flash') : model;
    try {
      const res = await fetch('/api/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          OPENROUTER_API_KEY: apiKey,
          GEMINI_API_KEY: geminiKey,
          OPENROUTER_MODEL: finalModel,
          CAMERA_ENABLED: cameraEnabled,
          LOCATION_ENABLED: locationEnabled,
          LEARNING_ENABLED: learningEnabled,
          VOICE_FIRST_MODE: voiceFirstMode
        })
      });
      if (res.ok) {
        setSaveStatus('Settings updated successfully.');
        setTimeout(() => setSaveStatus(''), 2500);
      }
    } catch (e) {
      setSaveStatus('Error saving settings.');
    }
  };

  const handleTestAI = async () => {
    setIsTesting(true);
    setTestStatus('Testing AI reasoning engine...');
    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: 'Explain gravity in one sentence.', is_voice: false })
      });
      if (res.ok) {
        const data = await res.json();
        setTestStatus(`AI Active (${data.tool || 'engine'}): "${data.response.slice(0, 75)}..."`);
      } else {
        setTestStatus('AI check returned status ' + res.status);
      }
    } catch (err: any) {
      setTestStatus('Test failed: ' + err.message);
    } finally {
      setIsTesting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-md animate-fade-in">
      <div className="w-full max-w-lg glass-panel border border-cyan-500/30 rounded-2xl p-6 shadow-2xl space-y-5 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between pb-3 border-b border-slate-700/60">
          <div className="flex items-center gap-2 text-aura-cyan">
            <Settings className="w-5 h-5" />
            <h2 className="text-base font-bold text-slate-100">ARHIEA System & AI Settings</h2>
          </div>
          <button onClick={onClose} className="p-1 rounded-lg text-slate-400 hover:text-slate-100 hover:bg-slate-800 transition">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Frontier AI Banner */}
        <div className="p-3.5 rounded-xl bg-gradient-to-r from-cyan-950/70 to-indigo-950/70 border border-cyan-500/30 text-slate-200 text-xs space-y-1.5 shadow-sm">
          <div className="flex items-center gap-1.5 font-bold text-cyan-300 text-[11px]">
            <Sparkles className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
            <span>Multi-AI Generative Intelligence</span>
          </div>
          <p className="text-[11px] text-slate-300 leading-relaxed">
            ARHIEA supports <strong>Google Gemini</strong>, <strong>Claude 3.5</strong>, <strong>GPT-4o</strong>, <strong>DeepSeek R1</strong>, and <strong>Llama 3.3</strong>. If no key is entered, the high-speed <strong>Autonomous Open Knowledge Engine</strong> provides complete answers automatically.
          </p>
        </div>

        <form onSubmit={handleSave} className="space-y-4 text-xs">
          {/* Gemini API Key */}
          <div className="space-y-1.5">
            <label className="flex items-center gap-1.5 font-semibold text-slate-300">
              <Key className="w-3.5 h-3.5 text-cyan-400" />
              <span>Google Gemini API Key (AI Studio)</span>
            </label>
            <input
              type="password"
              placeholder="AIzaSy..."
              value={geminiKey}
              onChange={(e) => setGeminiKey(e.target.value)}
              className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-aura-cyan"
            />
            <p className="text-[10px] text-slate-400">
              Get a free API key at <a href="https://aistudio.google.com/app/apikey" target="_blank" rel="noreferrer" className="text-cyan-400 underline">aistudio.google.com</a>.
            </p>
          </div>

          {/* OpenRouter API Key */}
          <div className="space-y-1.5">
            <label className="flex items-center gap-1.5 font-semibold text-slate-300">
              <Key className="w-3.5 h-3.5 text-indigo-400" />
              <span>OpenRouter API Key (For Claude, GPT-4o, DeepSeek, Llama)</span>
            </label>
            <input
              type="password"
              placeholder="sk-or-v1-..."
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-aura-cyan"
            />
          </div>

          {/* Model Selector */}
          <div className="space-y-1.5">
            <label className="flex items-center gap-1.5 font-semibold text-slate-300">
              <Cpu className="w-3.5 h-3.5 text-cyan-400" />
              <span>AI Model Selection</span>
            </label>
            <select
              value={model}
              onChange={(e) => {
                const val = e.target.value;
                setModel(val);
                setIsCustomModel(val === 'custom');
              }}
              className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 text-slate-100 focus:outline-none focus:border-aura-cyan"
            >
              <option value="google/gemini-2.5-flash">Gemini 2.5 Flash (Fast, High Quality)</option>
              <option value="google/gemini-2.5-pro">Gemini 2.5 Pro (Deep Complex Reasoning)</option>
              <option value="anthropic/claude-3.5-sonnet">Claude 3.5 Sonnet (Elite Coding & Nuance)</option>
              <option value="openai/gpt-4o">OpenAI GPT-4o (Frontier Multimodal)</option>
              <option value="openai/gpt-4o-mini">OpenAI GPT-4o Mini (Ultra Fast)</option>
              <option value="deepseek/deepseek-r1">DeepSeek R1 (Deep Mathematical Thinking)</option>
              <option value="meta-llama/llama-3.3-70b-instruct">Meta Llama 3.3 70B (Open Weights Champion)</option>
              <option value="qwen/qwen-2.5-72b-instruct">Qwen 2.5 72B Instruct</option>
              <option value="custom">Custom Model Name...</option>
            </select>

            {isCustomModel && (
              <input
                type="text"
                placeholder="e.g. meta-llama/llama-3.1-405b-instruct or ollama/mistral"
                value={customModel}
                onChange={(e) => setCustomModel(e.target.value)}
                className="w-full mt-1.5 px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-400 font-mono text-xs"
              />
            )}
          </div>

          {/* Test AI Connection Button */}
          <div className="pt-1">
            <button
              type="button"
              onClick={handleTestAI}
              disabled={isTesting}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-cyan-300 text-xs font-medium border border-cyan-500/30 transition disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isTesting ? 'animate-spin' : ''}`} />
              <span>{isTesting ? 'Testing...' : 'Test AI Connection'}</span>
            </button>
            {testStatus && (
              <p className="mt-1 text-[11px] text-slate-300 font-mono bg-slate-950/60 p-2 rounded-lg border border-slate-800">
                {testStatus}
              </p>
            )}
          </div>

          {/* Privacy Toggles */}
          <div className="space-y-2 pt-2 border-t border-slate-700/60">
            <h3 className="font-semibold text-slate-300 uppercase tracking-wider text-[10px]">Privacy & Permissions</h3>

            <div className="flex items-center justify-between p-2 rounded-lg bg-slate-900/60 border border-slate-800">
              <div className="flex items-center gap-2">
                <Eye className="w-4 h-4 text-cyan-400" />
                <span>Camera Access</span>
              </div>
              <input
                type="checkbox"
                checked={cameraEnabled}
                onChange={(e) => setCameraEnabled(e.target.checked)}
                className="w-4 h-4 rounded border-slate-700 text-aura-cyan focus:ring-0"
              />
            </div>

            <div className="flex items-center justify-between p-2 rounded-lg bg-slate-900/60 border border-slate-800">
              <div className="flex items-center gap-2">
                <MapPin className="w-4 h-4 text-blue-400" />
                <span>Location Access (For Maps Navigation)</span>
              </div>
              <input
                type="checkbox"
                checked={locationEnabled}
                onChange={(e) => setLocationEnabled(e.target.checked)}
                className="w-4 h-4 rounded border-slate-700 text-aura-cyan focus:ring-0"
              />
            </div>

            <div className="flex items-center justify-between p-2 rounded-lg bg-slate-900/60 border border-slate-800">
              <div className="flex items-center gap-2">
                <Globe className="w-4 h-4 text-purple-400" />
                <span>Daily Routine Learning (SIH)</span>
              </div>
              <input
                type="checkbox"
                checked={learningEnabled}
                onChange={(e) => setLearningEnabled(e.target.checked)}
                className="w-4 h-4 rounded border-slate-700 text-aura-cyan focus:ring-0"
              />
            </div>
          </div>

          {saveStatus && (
            <div className="flex items-center gap-1.5 text-xs text-emerald-400">
              <Check className="w-3.5 h-3.5" />
              <span>{saveStatus}</span>
            </div>
          )}

          <div className="flex justify-end gap-2 pt-2 border-t border-slate-700/60">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium transition"
            >
              Close
            </button>
            <button
              type="submit"
              className="px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-medium shadow-md transition active:scale-95"
            >
              Save Changes
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
