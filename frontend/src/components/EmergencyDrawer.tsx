import React, { useState, useEffect, useRef } from 'react';
import {
  ShieldAlert, PhoneCall, AlertTriangle, Heart, Activity,
  MapPin, User, FileText, Send, X, CheckCircle, Volume2, VolumeX, Flame, Droplets, Zap
} from 'lucide-react';

interface EmergencyDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  initialProtocol?: string;
}

interface EmergencyProtocol {
  title: string;
  category: string;
  severity: string;
  voice_summary: string;
  steps: string[];
  metronome_bpm?: number;
}

interface MedicalProfile {
  name: string;
  blood_group: string;
  emergency_contact_name: string;
  emergency_contact_phone: string;
  allergies: string;
  medical_conditions: string;
}

export const EmergencyDrawer: React.FC<EmergencyDrawerProps> = ({ isOpen, onClose, initialProtocol }) => {
  const [selectedTab, setSelectedTab] = useState<'protocols' | 'sos' | 'cpr' | 'profile'>('protocols');
  const [selectedProtocolKey, setSelectedProtocolKey] = useState<string>(initialProtocol || 'brake_failure');
  const [protocolData, setProtocolData] = useState<EmergencyProtocol | null>(null);
  const [medicalProfile, setMedicalProfile] = useState<MedicalProfile | null>(null);
  const [sosStatus, setSosStatus] = useState<any>(null);
  const [isSosLoading, setIsSosLoading] = useState<boolean>(false);

  // CPR Metronome States
  const [isMetronomeActive, setIsMetronomeActive] = useState<boolean>(false);
  const [beatCount, setBeatCount] = useState<number>(0);
  const audioContextRef = useRef<AudioContext | null>(null);
  const metronomeIntervalRef = useRef<any>(null);

  // Fetch Protocol Details
  const fetchProtocol = async (type: string) => {
    try {
      const res = await fetch(`/api/emergency/protocol/${type}`);
      if (res.ok) {
        const data = await res.json();
        setProtocolData(data);
      }
    } catch (e) {
      console.error('Failed to fetch emergency protocol:', e);
    }
  };

  // Fetch Medical Profile
  const fetchMedicalProfile = async () => {
    try {
      const res = await fetch('/api/emergency/medical-profile');
      if (res.ok) {
        const data = await res.json();
        setMedicalProfile(data.profile);
      }
    } catch (e) {
      console.error('Failed to fetch medical profile:', e);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchProtocol(selectedProtocolKey);
      fetchMedicalProfile();
    } else {
      stopMetronome();
    }
  }, [isOpen, selectedProtocolKey]);

  // Metronome Beep Generator (Web Audio API)
  const playBeep = () => {
    try {
      if (!audioContextRef.current) {
        audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
      }
      const ctx = audioContextRef.current;
      if (ctx.state === 'suspended') {
        ctx.resume();
      }
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(880, ctx.currentTime); // 880 Hz High Pitch Beat
      gain.gain.setValueAtTime(0.3, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.08);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start();
      osc.stop(ctx.currentTime + 0.09);
    } catch (e) {
      console.error('Audio Metronome error:', e);
    }
  };

  const startMetronome = () => {
    setIsMetronomeActive(true);
    setBeatCount(0);
    const intervalMs = (60 / 110) * 1000; // 110 BPM rhythm
    metronomeIntervalRef.current = setInterval(() => {
      setBeatCount((prev) => {
        const next = (prev % 30) + 1;
        playBeep();
        return next;
      });
    }, intervalMs);
  };

  const stopMetronome = () => {
    setIsMetronomeActive(false);
    if (metronomeIntervalRef.current) {
      clearInterval(metronomeIntervalRef.current);
      metronomeIntervalRef.current = null;
    }
  };

  // Trigger Emergency SOS Beacon
  const handleTriggerSos = async () => {
    setIsSosLoading(true);
    try {
      const res = await fetch('/api/emergency/sos', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          incident_description: 'High-Priority Emergency SOS triggered from Dashboard',
          severity: 'CRITICAL'
        })
      });
      if (res.ok) {
        const data = await res.json();
        setSosStatus(data);
        setSelectedTab('sos');
      }
    } catch (e) {
      console.error('Failed to trigger SOS:', e);
    } finally {
      setIsSosLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/80 backdrop-blur-md transition-all duration-300">
      <div className="w-full max-w-2xl bg-slate-950 border-l border-red-500/40 text-slate-100 flex flex-col h-full shadow-2xl shadow-red-950/50">
        
        {/* Header with High-Visibility Emergency Theme */}
        <div className="p-4 sm:p-5 border-b border-red-500/30 bg-gradient-to-r from-red-950/80 via-slate-900 to-slate-950 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-red-600/30 border border-red-500/60 text-red-400 animate-pulse">
              <ShieldAlert className="w-6 h-6 text-red-400" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white tracking-wide flex items-center gap-2">
                ARHIEA EMERGENCY CENTER
                <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded-full bg-red-500/20 text-red-300 border border-red-500/40">
                  SIH26204 Life-Safety
                </span>
              </h2>
              <p className="text-xs text-red-200/80">Voice-Guided Road & Medical Emergency Intelligence</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tab Navigation */}
        <div className="flex border-b border-slate-800 bg-slate-900/60 px-4 pt-2 gap-2 text-xs font-semibold">
          <button
            onClick={() => setSelectedTab('protocols')}
            className={`pb-2.5 px-3 border-b-2 transition ${
              selectedTab === 'protocols'
                ? 'border-red-500 text-red-400 font-bold'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            Emergency Protocols
          </button>
          <button
            onClick={() => setSelectedTab('cpr')}
            className={`pb-2.5 px-3 border-b-2 transition flex items-center gap-1.5 ${
              selectedTab === 'cpr'
                ? 'border-red-500 text-red-400 font-bold'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Heart className="w-3.5 h-3.5 text-red-400" />
            CPR Metronome
          </button>
          <button
            onClick={() => setSelectedTab('sos')}
            className={`pb-2.5 px-3 border-b-2 transition flex items-center gap-1.5 ${
              selectedTab === 'sos'
                ? 'border-red-500 text-red-400 font-bold'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <PhoneCall className="w-3.5 h-3.5 text-amber-400" />
            SOS Beacon & Hotlines
          </button>
          <button
            onClick={() => setSelectedTab('profile')}
            className={`pb-2.5 px-3 border-b-2 transition flex items-center gap-1.5 ${
              selectedTab === 'profile'
                ? 'border-red-500 text-red-400 font-bold'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <User className="w-3.5 h-3.5 text-cyan-400" />
            Medical Context
          </button>
        </div>

        {/* Tab Contents */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6">

          {/* TAB 1: PROTOCOLS */}
          {selectedTab === 'protocols' && (
            <div className="space-y-5">
              {/* Quick Protocol Selectors */}
              <div>
                <label className="text-xs font-mono uppercase text-slate-400 tracking-wider block mb-2">
                  Select Road or Medical Emergency:
                </label>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                  {[
                    { key: 'brake_failure', label: 'Brake Failure', icon: AlertTriangle, color: 'text-amber-400' },
                    { key: 'cpr', label: 'CPR & Arrest', icon: Heart, color: 'text-rose-400' },
                    { key: 'aquaplaning', label: 'Aquaplaning', icon: Droplets, color: 'text-cyan-400' },
                    { key: 'tyre_blowout', label: 'Tyre Blowout', icon: Zap, color: 'text-amber-400' },
                    { key: 'choking_heimlich', label: 'Choking (Heimlich)', icon: Activity, color: 'text-purple-400' },
                    { key: 'burns', label: 'Severe Burns', icon: Flame, color: 'text-orange-400' },
                    { key: 'severe_bleeding', label: 'Severe Bleeding', icon: AlertTriangle, color: 'text-rose-400' },
                    { key: 'road_accident', label: 'Crash Triage', icon: ShieldAlert, color: 'text-red-400' }
                  ].map((p) => {
                    const Icon = p.icon;
                    return (
                      <button
                        key={p.key}
                        onClick={() => setSelectedProtocolKey(p.key)}
                        className={`p-2.5 rounded-xl border text-left text-xs font-semibold flex items-center gap-2 transition ${
                          selectedProtocolKey === p.key
                            ? 'bg-red-950/80 border-red-500 text-white shadow-lg shadow-red-950/50'
                            : 'bg-slate-900/80 border-slate-800 text-slate-300 hover:border-slate-600'
                        }`}
                      >
                        <Icon className={`w-4 h-4 shrink-0 ${p.color}`} />
                        <span className="truncate">{p.label}</span>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Protocol Step-by-Step Display */}
              {protocolData && (
                <div className="p-4 sm:p-5 rounded-2xl bg-slate-900/90 border border-red-500/30 space-y-4">
                  <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                    <h3 className="font-bold text-white text-sm sm:text-base tracking-wide text-red-300">
                      {protocolData.title}
                    </h3>
                    <span className="text-[10px] px-2.5 py-1 rounded-full font-mono font-bold bg-red-600/30 text-red-300 border border-red-500/50">
                      {protocolData.severity}
                    </span>
                  </div>

                  <div className="p-3 rounded-xl bg-slate-950/80 border border-red-500/20 text-xs text-red-200 italic leading-relaxed">
                    "{protocolData.voice_summary}"
                  </div>

                  <div className="space-y-2.5">
                    <span className="text-xs font-mono uppercase text-slate-400 tracking-wider">
                      Action Protocol Steps:
                    </span>
                    {protocolData.steps.map((step, idx) => (
                      <div
                        key={idx}
                        className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 text-xs text-slate-200 leading-relaxed flex items-start gap-2.5"
                      >
                        <span className="w-5 h-5 rounded-full bg-red-500/20 text-red-400 font-bold text-[10px] flex items-center justify-center shrink-0 mt-0.5">
                          {idx + 1}
                        </span>
                        <div>{step.replace(/^\d+\.\s*/, '')}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* TAB 2: CPR METRONOME */}
          {selectedTab === 'cpr' && (
            <div className="space-y-6 text-center">
              <div className="p-6 rounded-3xl bg-slate-900/90 border border-red-500/40 relative overflow-hidden">
                <div className="flex flex-col items-center gap-4">
                  {/* Beating Heart Visualizer */}
                  <div
                    className={`w-28 h-28 rounded-full flex items-center justify-center transition-all duration-100 ${
                      isMetronomeActive
                        ? 'bg-red-600/30 border-4 border-red-500 shadow-[0_0_40px_rgba(239,68,68,0.6)] scale-110'
                        : 'bg-slate-800/50 border border-slate-700'
                    }`}
                  >
                    <Heart
                      className={`w-14 h-14 ${
                        isMetronomeActive ? 'text-red-500 animate-ping' : 'text-slate-500'
                      }`}
                    />
                  </div>

                  <div>
                    <h3 className="text-xl font-bold text-white tracking-wide">
                      110 BPM CPR COMPRESSION GUIDE
                    </h3>
                    <p className="text-xs text-slate-400 mt-1">
                      Target Rhythm: 100–120 compressions/minute (Rhythm of "Stayin' Alive")
                    </p>
                  </div>

                  {/* Compression Counter */}
                  <div className="flex items-center gap-4 my-2">
                    <div className="p-3 px-6 rounded-2xl bg-slate-950 border border-red-500/30">
                      <span className="text-xs text-slate-400 block font-mono">COMPRESSION</span>
                      <span className="text-3xl font-extrabold text-red-400 font-mono">
                        {beatCount} / 30
                      </span>
                    </div>
                  </div>

                  {/* Start / Stop Button */}
                  <button
                    onClick={isMetronomeActive ? stopMetronome : startMetronome}
                    className={`px-8 py-3.5 rounded-2xl font-bold text-sm tracking-wider uppercase transition-all shadow-xl flex items-center gap-2 ${
                      isMetronomeActive
                        ? 'bg-red-600 hover:bg-red-500 text-white shadow-red-950/80 animate-pulse'
                        : 'bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-500 text-white'
                    }`}
                  >
                    {isMetronomeActive ? (
                      <>
                        <VolumeX className="w-5 h-5" />
                        Stop Audio Metronome
                      </>
                    ) : (
                      <>
                        <Volume2 className="w-5 h-5" />
                        Start 110 BPM Metronome Beat
                      </>
                    )}
                  </button>
                </div>
              </div>

              {/* CPR Key Rules Card */}
              <div className="grid grid-cols-2 gap-3 text-left">
                <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 text-xs">
                  <span className="font-bold text-red-300 block mb-1">Depth: 5 to 6 cm</span>
                  <p className="text-slate-400">Push hard on the center of breastbone; allow complete chest recoil between pumps.</p>
                </div>
                <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 text-xs">
                  <span className="font-bold text-red-300 block mb-1">Cycle: 30 : 2</span>
                  <p className="text-slate-400">30 rapid compressions followed by 2 gentle 1-second rescue breaths, or continuous Hands-Only CPR.</p>
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: SOS BEACON & HOTLINES */}
          {selectedTab === 'sos' && (
            <div className="space-y-5">
              {/* Massive Trigger SOS Button */}
              <div className="p-5 rounded-2xl bg-gradient-to-br from-red-950/60 via-slate-900 to-slate-950 border border-red-500/50 text-center space-y-3">
                <h3 className="text-base font-bold text-white tracking-wide">
                  ONE-CLICK EMERGENCY SOS BEACON
                </h3>
                <p className="text-xs text-slate-300 max-w-md mx-auto">
                  Captures current GPS coordinates, dials national emergency services, and archives an official accident medical report to your Desktop.
                </p>
                <button
                  onClick={handleTriggerSos}
                  disabled={isSosLoading}
                  className="px-8 py-4 rounded-2xl bg-red-600 hover:bg-red-500 text-white font-black text-sm tracking-widest uppercase transition shadow-2xl shadow-red-950/80 active:scale-95 disabled:opacity-50"
                >
                  {isSosLoading ? 'DISPATCHING SOS...' : '🚨 TRIGGER EMERGENCY SOS NOW'}
                </button>
              </div>

              {/* SOS Status Callback */}
              {sosStatus && (
                <div className="p-4 rounded-2xl bg-slate-900 border border-green-500/50 space-y-3">
                  <div className="flex items-center gap-2 text-green-400 font-bold text-sm">
                    <CheckCircle className="w-5 h-5" />
                    <span>EMERGENCY SOS BEACON DISPATCHED</span>
                  </div>
                  <div className="text-xs text-slate-300 space-y-1">
                    <p><strong className="text-white">Location:</strong> {sosStatus.location}</p>
                    <p><strong className="text-white">Report Archived:</strong> {sosStatus.report_saved_to}</p>
                  </div>
                  {sosStatus.whatsapp_sos_link && (
                    <a
                      href={sosStatus.whatsapp_sos_link}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold transition"
                    >
                      <Send className="w-4 h-4" />
                      Send Pre-filled WhatsApp Alert to Emergency Contact
                    </a>
                  )}
                </div>
              )}

              {/* Verified Hotlines List */}
              <div className="space-y-2">
                <span className="text-xs font-mono uppercase text-slate-400 tracking-wider">
                  Verified Emergency Direct Dials:
                </span>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                  {[
                    { name: 'National All-in-One Emergency', number: '112', desc: 'Police, Medical, Fire' },
                    { name: 'Ambulance / Medical Response', number: '108', desc: 'Direct Trauma & Paramedics' },
                    { name: 'National Highway Patrol (NHAI)', number: '1073', desc: 'Expressway Breakdown & Crash' },
                    { name: 'Police Dispatch', number: '100', desc: 'Law Enforcement' }
                  ].map((h, i) => (
                    <div
                      key={i}
                      className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 flex items-center justify-between"
                    >
                      <div>
                        <span className="font-bold text-white text-xs block">{h.name}</span>
                        <span className="text-[11px] text-slate-400">{h.desc}</span>
                      </div>
                      <a
                        href={`tel:${h.number}`}
                        className="px-3 py-1.5 rounded-lg bg-red-600/30 hover:bg-red-600/50 text-red-300 border border-red-500/40 text-xs font-mono font-bold flex items-center gap-1.5 transition"
                      >
                        <PhoneCall className="w-3.5 h-3.5" />
                        {h.number}
                      </a>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* TAB 4: MEDICAL CONTEXT */}
          {selectedTab === 'profile' && (
            <div className="space-y-4">
              <div className="p-4 rounded-2xl bg-slate-900/90 border border-cyan-500/30 space-y-3">
                <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                  <h3 className="font-bold text-white text-xs tracking-wider uppercase font-mono text-cyan-400">
                    Episodic Emergency Profile
                  </h3>
                  <span className="text-[10px] text-slate-400">Synced to SQLite Brain</span>
                </div>

                {medicalProfile ? (
                  <div className="grid grid-cols-2 gap-3 text-xs">
                    <div className="p-2.5 rounded-xl bg-slate-950/80 border border-slate-800">
                      <span className="text-slate-400 block text-[10px] uppercase font-mono">Patient Name</span>
                      <span className="font-semibold text-white">{medicalProfile.name}</span>
                    </div>
                    <div className="p-2.5 rounded-xl bg-slate-950/80 border border-slate-800">
                      <span className="text-slate-400 block text-[10px] uppercase font-mono">Blood Group</span>
                      <span className="font-bold text-red-400">{medicalProfile.blood_group || 'Not set'}</span>
                    </div>
                    <div className="p-2.5 rounded-xl bg-slate-950/80 border border-slate-800">
                      <span className="text-slate-400 block text-[10px] uppercase font-mono">Emergency Contact</span>
                      <span className="font-semibold text-white">
                        {medicalProfile.emergency_contact_name} ({medicalProfile.emergency_contact_phone})
                      </span>
                    </div>
                    <div className="p-2.5 rounded-xl bg-slate-950/80 border border-slate-800">
                      <span className="text-slate-400 block text-[10px] uppercase font-mono">Known Allergies</span>
                      <span className="font-semibold text-amber-300">{medicalProfile.allergies}</span>
                    </div>
                  </div>
                ) : (
                  <p className="text-xs text-slate-400">No medical profile recorded. Log in to sync profile.</p>
                )}
              </div>
            </div>
          )}

        </div>

      </div>
    </div>
  );
};
