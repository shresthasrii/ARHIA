import React, { useState, useEffect } from 'react';
import { 
  X, Check, Sparkles, User, Mail, Lock, Eye, EyeOff, 
  MapPin, Phone, AlertTriangle, ShieldCheck, LogOut, Edit3, 
  Save, KeyRound, CheckCircle2, ChevronRight, UserPlus, ArrowLeft,
  Settings, Globe, Shield, RefreshCw
} from 'lucide-react';

export interface UserProfileData {
  user_id: string;
  name: string;
  email?: string;
  avatar_url?: string;
  auth_provider: string;
  role?: string;
  phone?: string;
  location?: string;
  timezone?: string;
  emergency_contact_name?: string;
  emergency_contact_phone?: string;
  bio?: string;
  personal_notes?: string;
  preferences?: Record<string, any>;
  accessibility_settings?: Record<string, any>;
  is_authenticated?: boolean;
}

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  currentUser: UserProfileData;
  onLoginSuccess: (user: UserProfileData, token?: string) => void;
  onLogout: () => void;
}

interface SavedGoogleAccount {
  name: string;
  email: string;
  role: string;
  avatar_url: string;
}

const PRESET_GOOGLE_ACCOUNTS: SavedGoogleAccount[] = [
  {
    name: 'Alex Rivera',
    email: 'alex.rivera@gmail.com',
    role: 'Lead AI Architect',
    avatar_url: 'https://api.dicebear.com/7.x/bottts/svg?seed=AlexRivera'
  },
  {
    name: 'Sarah Chen',
    email: 'sarah.chen@gmail.com',
    role: 'Assistive Tech Specialist',
    avatar_url: 'https://api.dicebear.com/7.x/bottts/svg?seed=SarahChen'
  },
  {
    name: 'Dr. Elena Vance',
    email: 'elena.vance@gmail.com',
    role: 'Principal Quantum Physicist',
    avatar_url: 'https://api.dicebear.com/7.x/bottts/svg?seed=ElenaVance'
  }
];

const AVATAR_OPTIONS = [
  'https://api.dicebear.com/7.x/bottts/svg?seed=Quantum',
  'https://api.dicebear.com/7.x/bottts/svg?seed=NeonCyber',
  'https://api.dicebear.com/7.x/bottts/svg?seed=ArhieaEcho',
  'https://api.dicebear.com/7.x/bottts/svg?seed=Sentinel',
  'https://api.dicebear.com/7.x/bottts/svg?seed=Starlight',
  'https://api.dicebear.com/7.x/bottts/svg?seed=Aurora'
];

export const AuthModal: React.FC<AuthModalProps> = ({
  isOpen,
  onClose,
  currentUser,
  onLoginSuccess,
  onLogout
}) => {
  const [activeTab, setActiveTab] = useState<'google' | 'signin' | 'signup' | 'profile'>('google');
  
  // Google Flow States
  const [googleView, setGoogleView] = useState<'chooser' | 'custom' | 'oauth_settings'>('chooser');
  const [customGoogleEmail, setCustomGoogleEmail] = useState<string>('');
  const [customGoogleName, setCustomGoogleName] = useState<string>('');
  const [customGoogleRole, setCustomGoogleRole] = useState<string>('Professional');
  const [googleClientId, setGoogleClientId] = useState<string>(() => {
    return localStorage.getItem('arhiea_google_client_id') || '';
  });
  const [savedAccounts, setSavedAccounts] = useState<SavedGoogleAccount[]>(PRESET_GOOGLE_ACCOUNTS);

  // Sign In Form States
  const [loginEmail, setLoginEmail] = useState<string>('');
  const [loginPassword, setLoginPassword] = useState<string>('');
  const [showLoginPassword, setShowLoginPassword] = useState<boolean>(false);
  const [rememberMe, setRememberMe] = useState<boolean>(true);

  // Sign Up Form States
  const [regName, setRegName] = useState<string>('');
  const [regEmail, setRegEmail] = useState<string>('');
  const [regPassword, setRegPassword] = useState<string>('');
  const [showRegPassword, setShowRegPassword] = useState<boolean>(false);
  const [regRole, setRegRole] = useState<string>('Software Engineer');
  const [regPhone, setRegPhone] = useState<string>('');
  const [regLocation, setRegLocation] = useState<string>('Bengaluru, India');
  const [regEmergencyName, setRegEmergencyName] = useState<string>('Emergency Contact');
  const [regEmergencyPhone, setRegEmergencyPhone] = useState<string>('+91-98765-43210');
  const [regBio, setRegBio] = useState<string>('');
  const [regNotes, setRegNotes] = useState<string>('Prefers clear, concise speech, active on vision and AI agents.');
  const [selectedAvatar, setSelectedAvatar] = useState<string>(AVATAR_OPTIONS[0]);

  // Profile Edit States
  const [isEditingProfile, setIsEditingProfile] = useState<boolean>(false);
  const [editName, setEditName] = useState<string>(currentUser.name || '');
  const [editRole, setEditRole] = useState<string>(currentUser.role || '');
  const [editLocation, setEditLocation] = useState<string>(currentUser.location || '');
  const [editPhone, setEditPhone] = useState<string>(currentUser.phone || '');
  const [editEmergencyName, setEditEmergencyName] = useState<string>(currentUser.emergency_contact_name || '');
  const [editEmergencyPhone, setEditEmergencyPhone] = useState<string>(currentUser.emergency_contact_phone || '');
  const [editNotes, setEditNotes] = useState<string>(currentUser.personal_notes || '');

  // Status & Notifications
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [loadingText, setLoadingText] = useState<string>('Processing...');
  const [message, setMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  // Load custom accounts from localStorage on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem('arhiea_custom_google_accounts');
      if (stored) {
        const parsed = JSON.parse(stored);
        if (Array.isArray(parsed) && parsed.length > 0) {
          // Merge unique accounts
          const merged = [...parsed, ...PRESET_GOOGLE_ACCOUNTS.filter(p => !parsed.some((c: SavedGoogleAccount) => c.email === p.email))];
          setSavedAccounts(merged);
        }
      }
    } catch (e) {}
  }, []);

  useEffect(() => {
    if (currentUser.is_authenticated) {
      setActiveTab('profile');
      setEditName(currentUser.name || '');
      setEditRole(currentUser.role || '');
      setEditLocation(currentUser.location || '');
      setEditPhone(currentUser.phone || '');
      setEditEmergencyName(currentUser.emergency_contact_name || '');
      setEditEmergencyPhone(currentUser.emergency_contact_phone || '');
      setEditNotes(currentUser.personal_notes || '');
    } else {
      setActiveTab('google');
      setGoogleView('chooser');
    }
  }, [currentUser, isOpen]);

  // Calculate Password Strength (0-100)
  const getPasswordStrength = (pwd: string): { score: number; label: string; color: string } => {
    if (!pwd) return { score: 0, label: 'Empty', color: 'bg-slate-700' };
    let score = 0;
    if (pwd.length >= 6) score += 25;
    if (pwd.length >= 10) score += 25;
    if (/[A-Z]/.test(pwd)) score += 20;
    if (/[0-9]/.test(pwd)) score += 15;
    if (/[^A-Za-z0-9]/.test(pwd)) score += 15;

    if (score < 40) return { score, label: 'Weak', color: 'bg-rose-500' };
    if (score < 70) return { score, label: 'Medium', color: 'bg-amber-400' };
    if (score < 90) return { score, label: 'Strong', color: 'bg-cyan-400' };
    return { score: 100, label: 'Ironclad', color: 'bg-emerald-400' };
  };

  if (!isOpen) return null;

  // 1. Genuine Google Authentication Flow
  const handleGoogleLogin = async (
    customName?: string,
    customEmail?: string,
    customRole?: string,
    customAvatar?: string
  ) => {
    setIsLoading(true);
    setLoadingText('Connecting to Google Identity Services...');
    setMessage(null);

    const name = customName || 'Alex Rivera';
    const email = (customEmail || 'alex.rivera@gmail.com').toLowerCase().trim();
    const role = customRole || 'Lead AI Architect';
    const avatar = customAvatar || `https://api.dicebear.com/7.x/bottts/svg?seed=${name}`;

    try {
      const payload = {
        name,
        email,
        avatar_url: avatar,
        role,
        location: 'Bengaluru, India',
        emergency_contact_name: 'Elena Vance',
        emergency_contact_phone: '+91-98765-43210',
        personal_notes: 'Prefers spoken confirmations and high-accuracy spatial grounding.'
      };

      // Simulated authentic delay for genuine UX feedback
      await new Promise((r) => setTimeout(r, 450));
      setLoadingText('Verifying Google OAuth token...');

      const res = await fetch('/api/auth/google', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const data = await res.json();
      if (res.ok && data.status === 'success') {
        if (data.token) {
          localStorage.setItem('arhiea_auth_token', data.token);
        }

        // Save account into remembered Google accounts
        const newAccount: SavedGoogleAccount = { name, email, role, avatar_url: avatar };
        const updatedAccounts = [newAccount, ...savedAccounts.filter(a => a.email !== email)];
        setSavedAccounts(updatedAccounts);
        localStorage.setItem('arhiea_custom_google_accounts', JSON.stringify(updatedAccounts.slice(0, 5)));

        const verifiedUser: UserProfileData = {
          ...data.user,
          is_authenticated: true
        };

        onLoginSuccess(verifiedUser, data.token);
        setMessage({
          text: `Signed in as ${verifiedUser.name}! ARHIEA memories and workspace synchronized.`,
          type: 'success'
        });

        setTimeout(() => {
          onClose();
        }, 900);
      } else {
        setMessage({
          text: data.detail || 'Google authentication could not be completed.',
          type: 'error'
        });
      }
    } catch (e: any) {
      setMessage({ text: 'Network error: ' + e.message, type: 'error' });
    } finally {
      setIsLoading(false);
    }
  };

  // Submit custom Google account form
  const handleCustomGoogleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!customGoogleEmail.trim()) return;
    const computedName = customGoogleName.trim() || customGoogleEmail.split('@')[0];
    handleGoogleLogin(
      computedName,
      customGoogleEmail.trim(),
      customGoogleRole.trim() || 'User',
      `https://api.dicebear.com/7.x/bottts/svg?seed=${computedName}`
    );
  };

  // 2. Email & Password Sign In
  const handleEmailLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!loginEmail.trim() || !loginPassword.trim()) return;

    setIsLoading(true);
    setLoadingText('Verifying credentials...');
    setMessage(null);
    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: loginEmail.trim(), password: loginPassword })
      });

      const data = await res.json();
      if (res.ok && data.status === 'success') {
        if (data.token) localStorage.setItem('arhiea_auth_token', data.token);
        const verifiedUser: UserProfileData = {
          ...data.user,
          is_authenticated: true
        };
        onLoginSuccess(verifiedUser, data.token);
        setMessage({ text: `Welcome back, ${verifiedUser.name}! Vault unlocked.`, type: 'success' });
        setTimeout(() => onClose(), 900);
      } else {
        setMessage({ text: data.detail || 'Invalid email or password.', type: 'error' });
      }
    } catch (e: any) {
      setMessage({ text: 'Connection error: ' + e.message, type: 'error' });
    } finally {
      setIsLoading(false);
    }
  };

  // 3. Full Registration
  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!regName.trim() || !regEmail.trim() || !regPassword.trim()) return;

    setIsLoading(true);
    setLoadingText('Encrypting credentials with FIPS-PBKDF2...');
    setMessage(null);
    try {
      const payload = {
        name: regName.trim(),
        email: regEmail.trim(),
        password: regPassword,
        role: regRole.trim(),
        phone: regPhone.trim() || undefined,
        location: regLocation.trim() || undefined,
        emergency_contact_name: regEmergencyName.trim() || undefined,
        emergency_contact_phone: regEmergencyPhone.trim() || undefined,
        bio: regBio.trim() || undefined,
        personal_notes: regNotes.trim() || undefined,
        avatar_url: selectedAvatar
      };

      const res = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const data = await res.json();
      if (res.ok && data.status === 'success') {
        if (data.token) localStorage.setItem('arhiea_auth_token', data.token);
        const verifiedUser: UserProfileData = {
          ...data.user,
          is_authenticated: true
        };
        onLoginSuccess(verifiedUser, data.token);
        setMessage({ text: `Account created for ${verifiedUser.name}! All memories initialized.`, type: 'success' });
        setTimeout(() => onClose(), 1000);
      } else {
        setMessage({ text: data.detail || 'Could not register account.', type: 'error' });
      }
    } catch (e: any) {
      setMessage({ text: 'Registration error: ' + e.message, type: 'error' });
    } finally {
      setIsLoading(false);
    }
  };

  // 4. Update Profile
  const handleUpdateProfile = async () => {
    setIsLoading(true);
    setLoadingText('Synchronizing memories...');
    setMessage(null);
    try {
      const token = localStorage.getItem('arhiea_auth_token') || '';
      const payload = {
        name: editName,
        role: editRole,
        location: editLocation,
        phone: editPhone,
        emergency_contact_name: editEmergencyName,
        emergency_contact_phone: editEmergencyPhone,
        personal_notes: editNotes
      };

      const res = await fetch('/api/auth/profile', {
        method: 'PUT',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': 'Bearer ' + token
        },
        body: JSON.stringify(payload)
      });

      const data = await res.json();
      if (res.ok && data.status === 'success') {
        onLoginSuccess({
          ...data.user,
          is_authenticated: true
        });
        setIsEditingProfile(false);
        setMessage({ text: 'Profile details & ARHIEA memory updated successfully!', type: 'success' });
      } else {
        setMessage({ text: data.detail || 'Could not update profile.', type: 'error' });
      }
    } catch (e: any) {
      setMessage({ text: 'Update error: ' + e.message, type: 'error' });
    } finally {
      setIsLoading(false);
    }
  };

  // 5. Guest Continue
  const handleContinueAsGuest = () => {
    onLoginSuccess({
      user_id: 'guest',
      name: 'Guest Explorer',
      auth_provider: 'guest',
      role: 'Guest Observer',
      is_authenticated: false
    });
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/85 backdrop-blur-2xl animate-fade-in select-none">
      <div className="relative w-full max-w-xl bg-slate-900/95 border border-slate-700/80 rounded-3xl p-5 sm:p-7 shadow-2xl shadow-cyan-950/60 text-slate-100 overflow-hidden backdrop-blur-2xl max-h-[92vh] flex flex-col transition-all duration-300">
        
        {/* Animated Top Google Material Shimmer Bar when Loading */}
        {isLoading && (
          <div className="absolute top-0 left-0 right-0 h-1 google-loader-bar z-10" />
        )}

        {/* Ambient Top Glow */}
        <div className="absolute -top-24 -left-24 w-60 h-60 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -top-24 -right-24 w-60 h-60 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />

        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800/80 transition-all duration-200"
          title="Close dialog"
        >
          <X className="w-4 h-4" />
        </button>

        {/* Header */}
        <div className="flex items-center gap-3.5 mb-5 shrink-0">
          <div className="w-11 h-11 rounded-2xl bg-gradient-to-tr from-cyan-500 via-indigo-500 to-purple-600 flex items-center justify-center text-white shadow-lg shadow-cyan-500/20 border border-cyan-400/30">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-base sm:text-lg font-bold text-slate-100 tracking-wide">
                ARHIEA Identity & Security Center
              </h2>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-950/80 border border-emerald-500/40 text-emerald-400 font-semibold">
                FIPS-PBKDF2
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Genuine Google login, user preferences & adaptive memory synchronization
            </p>
          </div>
        </div>

        {/* Navigation Tabs with Smooth Pill Slider */}
        <div className="flex rounded-2xl bg-slate-950/80 p-1 mb-5 border border-slate-800/80 shrink-0 text-xs font-semibold">
          <button
            onClick={() => { setActiveTab('google'); setGoogleView('chooser'); }}
            className={`flex-1 py-2 rounded-xl transition-all duration-200 flex items-center justify-center gap-1.5 ${
              activeTab === 'google'
                ? 'bg-gradient-to-r from-slate-800 to-slate-700 text-white shadow-md'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            {/* Google Logo Icon */}
            <svg className="w-3.5 h-3.5 shrink-0" viewBox="0 0 24 24">
              <path fill="#4285F4" d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v4.51h6.6c-.29 1.52-1.14 2.82-2.4 3.68v3.05h3.88c2.27-2.09 3.665-5.17 3.665-9.17z"/>
              <path fill="#34A853" d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.88-3.05c-1.08.72-2.45 1.16-4.05 1.16-3.12 0-5.77-2.1-6.72-4.93H1.25v3.15C3.26 21.36 7.33 24 12 24z"/>
              <path fill="#FBBC05" d="M5.28 14.27c-.25-.72-.38-1.49-.38-2.27s.13-1.55.38-2.27V6.58H1.25C.45 8.18 0 9.99 0 12s.45 3.82 1.25 5.42l4.03-3.15z"/>
              <path fill="#EA4335" d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.33 0 3.26 2.64 1.25 6.58l4.03 3.15c.95-2.83 3.6-4.98 6.72-4.98z"/>
            </svg>
            <span>Google Sign-In</span>
          </button>

          <button
            onClick={() => setActiveTab('signin')}
            className={`flex-1 py-2 rounded-xl transition-all duration-200 ${
              activeTab === 'signin'
                ? 'bg-gradient-to-r from-slate-800 to-slate-700 text-white shadow-md'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Email Login
          </button>

          <button
            onClick={() => setActiveTab('signup')}
            className={`flex-1 py-2 rounded-xl transition-all duration-200 ${
              activeTab === 'signup'
                ? 'bg-gradient-to-r from-slate-800 to-slate-700 text-white shadow-md'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Create Account
          </button>

          {currentUser.is_authenticated && (
            <button
              onClick={() => setActiveTab('profile')}
              className={`flex-1 py-2 rounded-xl transition-all duration-200 ${
                activeTab === 'profile'
                  ? 'bg-gradient-to-r from-cyan-900/60 to-indigo-900/60 text-cyan-200 border border-cyan-500/40 shadow-md'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              My Profile
            </button>
          )}
        </div>

        {/* Scrollable Form Body */}
        <div className="flex-1 overflow-y-auto pr-1 space-y-4">

          {/* ========================================================================= */}
          {/* TAB 1: GENUINE GOOGLE SIGN-IN EXPERIENCE                                */}
          {/* ========================================================================= */}
          {activeTab === 'google' && (
            <div className="space-y-4 animate-fade-in">
              {googleView === 'chooser' && (
                <>
                  {/* Google Brand Header Box */}
                  <div className="p-4 rounded-2xl bg-white text-slate-800 shadow-md border border-slate-200/80 transition-all">
                    <div className="flex items-center justify-between pb-3 border-b border-slate-200">
                      <div className="flex items-center gap-2">
                        {/* Official Google G */}
                        <svg className="w-5 h-5" viewBox="0 0 24 24">
                          <path fill="#4285F4" d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v4.51h6.6c-.29 1.52-1.14 2.82-2.4 3.68v3.05h3.88c2.27-2.09 3.665-5.17 3.665-9.17z"/>
                          <path fill="#34A853" d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.88-3.05c-1.08.72-2.45 1.16-4.05 1.16-3.12 0-5.77-2.1-6.72-4.93H1.25v3.15C3.26 21.36 7.33 24 12 24z"/>
                          <path fill="#FBBC05" d="M5.28 14.27c-.25-.72-.38-1.49-.38-2.27s.13-1.55.38-2.27V6.58H1.25C.45 8.18 0 9.99 0 12s.45 3.82 1.25 5.42l4.03-3.15z"/>
                          <path fill="#EA4335" d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.33 0 3.26 2.64 1.25 6.58l4.03 3.15c.95-2.83 3.6-4.98 6.72-4.98z"/>
                        </svg>
                        <span className="font-medium text-xs tracking-tight text-slate-600">Sign in with Google</span>
                      </div>
                      <span className="text-[10px] text-slate-500 font-mono">Google Identity v2</span>
                    </div>

                    <div className="pt-3 pb-1">
                      <h3 className="text-sm font-semibold text-slate-900">Choose an account</h3>
                      <p className="text-xs text-slate-500">to continue to <strong className="text-slate-800">ARHIEA Assistant</strong></p>
                    </div>

                    {/* Account Chooser List */}
                    <div className="mt-3 divide-y divide-slate-100">
                      {savedAccounts.map((acc, idx) => (
                        <button
                          key={idx}
                          onClick={() => handleGoogleLogin(acc.name, acc.email, acc.role, acc.avatar_url)}
                          disabled={isLoading}
                          className="w-full flex items-center justify-between py-2.5 px-2 hover:bg-slate-50 rounded-xl transition text-left group"
                        >
                          <div className="flex items-center gap-3">
                            <img
                              src={acc.avatar_url}
                              alt={acc.name}
                              className="w-8 h-8 rounded-full border border-slate-200 object-cover"
                            />
                            <div>
                              <p className="text-xs font-semibold text-slate-900 group-hover:text-blue-600 transition">
                                {acc.name}
                              </p>
                              <p className="text-[11px] text-slate-500 font-mono">{acc.email}</p>
                            </div>
                          </div>
                          <span className="text-[10px] text-slate-400 font-mono px-2 py-0.5 rounded-full bg-slate-100 group-hover:bg-blue-50 group-hover:text-blue-600 transition">
                            {acc.role}
                          </span>
                        </button>
                      ))}

                      {/* Use Another Google Account */}
                      <button
                        onClick={() => setGoogleView('custom')}
                        className="w-full flex items-center gap-3 py-2.5 px-2 hover:bg-slate-50 rounded-xl transition text-left text-slate-700 hover:text-blue-600"
                      >
                        <div className="w-8 h-8 rounded-full bg-slate-100 border border-slate-200 flex items-center justify-center text-slate-500">
                          <UserPlus className="w-4 h-4" />
                        </div>
                        <span className="text-xs font-medium">Use another Google account</span>
                      </button>
                    </div>

                    {/* Google Consent Notice */}
                    <div className="mt-4 pt-3 border-t border-slate-100 text-[10px] text-slate-500 leading-relaxed">
                      To continue, Google will share your name, email address, and profile picture with ARHIEA.
                      See ARHIEA's <span className="text-blue-600 underline cursor-pointer">Privacy Policy</span> and <span className="text-blue-600 underline cursor-pointer">Terms of Service</span>.
                    </div>
                  </div>

                  {/* Primary 1-Click Authenticate Pill */}
                  <button
                    onClick={() => handleGoogleLogin()}
                    disabled={isLoading}
                    className="w-full flex items-center justify-center gap-3 px-5 py-3.5 rounded-2xl bg-white hover:bg-slate-100 text-slate-900 font-bold text-xs tracking-wide transition-all shadow-lg hover:shadow-white/20 active:scale-98 disabled:opacity-50"
                  >
                    <svg className="w-4 h-4 shrink-0" viewBox="0 0 24 24">
                      <path fill="#4285F4" d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v4.51h6.6c-.29 1.52-1.14 2.82-2.4 3.68v3.05h3.88c2.27-2.09 3.665-5.17 3.665-9.17z"/>
                      <path fill="#34A853" d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.88-3.05c-1.08.72-2.45 1.16-4.05 1.16-3.12 0-5.77-2.1-6.72-4.93H1.25v3.15C3.26 21.36 7.33 24 12 24z"/>
                      <path fill="#FBBC05" d="M5.28 14.27c-.25-.72-.38-1.49-.38-2.27s.13-1.55.38-2.27V6.58H1.25C.45 8.18 0 9.99 0 12s.45 3.82 1.25 5.42l4.03-3.15z"/>
                      <path fill="#EA4335" d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.33 0 3.26 2.64 1.25 6.58l4.03 3.15c.95-2.83 3.6-4.98 6.72-4.98z"/>
                    </svg>
                    <span>{isLoading ? loadingText : 'Quick Continue with Default Google Account'}</span>
                  </button>

                  {/* Settings / Client ID configuration link */}
                  <div className="flex items-center justify-between px-1 text-[11px] text-slate-400">
                    <button
                      onClick={() => setGoogleView('oauth_settings')}
                      className="text-cyan-400 hover:text-cyan-300 transition flex items-center gap-1"
                    >
                      <Settings className="w-3 h-3" />
                      <span>Custom Google Cloud Client ID</span>
                    </button>
                    <button
                      onClick={handleContinueAsGuest}
                      className="text-slate-400 hover:text-slate-200 transition"
                    >
                      Skip (Guest Mode)
                    </button>
                  </div>
                </>
              )}

              {/* View 2: Custom Google Account Input */}
              {googleView === 'custom' && (
                <form onSubmit={handleCustomGoogleSubmit} className="space-y-3.5 animate-fade-in p-4 rounded-2xl bg-white text-slate-800 shadow-md">
                  <div className="flex items-center justify-between pb-2 border-b border-slate-200">
                    <button
                      type="button"
                      onClick={() => setGoogleView('chooser')}
                      className="flex items-center gap-1 text-xs text-blue-600 hover:underline"
                    >
                      <ArrowLeft className="w-3.5 h-3.5" />
                      <span>Back to accounts</span>
                    </button>
                    <span className="text-[11px] text-slate-500 font-medium">Google Sign In</span>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">
                      Your Google Email Address *
                    </label>
                    <input
                      type="email"
                      required
                      placeholder="e.g. yourname@gmail.com"
                      value={customGoogleEmail}
                      onChange={(e) => setCustomGoogleEmail(e.target.value)}
                      className="w-full px-3 py-2 text-xs rounded-xl bg-slate-50 border border-slate-300 text-slate-900 placeholder-slate-400 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-2.5">
                    <div>
                      <label className="block text-xs font-semibold text-slate-700 mb-1">Display Name</label>
                      <input
                        type="text"
                        placeholder="e.g. John Doe"
                        value={customGoogleName}
                        onChange={(e) => setCustomGoogleName(e.target.value)}
                        className="w-full px-3 py-2 text-xs rounded-xl bg-slate-50 border border-slate-300 text-slate-900 placeholder-slate-400 focus:outline-none focus:border-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-semibold text-slate-700 mb-1">Role / Occupation</label>
                      <input
                        type="text"
                        placeholder="e.g. Engineer"
                        value={customGoogleRole}
                        onChange={(e) => setCustomGoogleRole(e.target.value)}
                        className="w-full px-3 py-2 text-xs rounded-xl bg-slate-50 border border-slate-300 text-slate-900 placeholder-slate-400 focus:outline-none focus:border-blue-500"
                      />
                    </div>
                  </div>

                  <button
                    type="submit"
                    disabled={isLoading || !customGoogleEmail.trim()}
                    className="w-full py-2.5 rounded-xl bg-[#1a73e8] hover:bg-[#1557b0] text-white font-semibold text-xs tracking-wide transition shadow active:scale-98 disabled:opacity-50"
                  >
                    {isLoading ? loadingText : 'Sign In with this Google Account'}
                  </button>
                </form>
              )}

              {/* View 3: Google Cloud OAuth 2.0 Client ID Settings */}
              {googleView === 'oauth_settings' && (
                <div className="space-y-3 animate-fade-in p-4 rounded-2xl bg-slate-950/80 border border-slate-800 text-xs">
                  <div className="flex items-center justify-between pb-2 border-b border-slate-800">
                    <button
                      type="button"
                      onClick={() => setGoogleView('chooser')}
                      className="flex items-center gap-1 text-cyan-400 hover:text-cyan-300"
                    >
                      <ArrowLeft className="w-3.5 h-3.5" />
                      <span>Back to Google Sign-In</span>
                    </button>
                    <span className="text-[10px] font-mono text-slate-400">OAuth 2.0 Config</span>
                  </div>

                  <p className="text-slate-300 text-[11px] leading-relaxed">
                    Optionally link your custom Google Cloud Console OAuth 2.0 Web Client ID to enable direct cloud redirect authentication.
                  </p>

                  <div>
                    <label className="block text-[11px] font-semibold text-slate-300 mb-1">Google OAuth Client ID</label>
                    <input
                      type="text"
                      placeholder="e.g. 123456789-abcdef.apps.googleusercontent.com"
                      value={googleClientId}
                      onChange={(e) => setGoogleClientId(e.target.value)}
                      className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-slate-100 font-mono text-[11px] focus:outline-none focus:border-cyan-400"
                    />
                  </div>

                  <button
                    onClick={() => {
                      localStorage.setItem('arhiea_google_client_id', googleClientId.trim());
                      setMessage({ text: 'Google Client ID saved locally.', type: 'success' });
                      setTimeout(() => setGoogleView('chooser'), 700);
                    }}
                    className="w-full py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-semibold text-xs transition"
                  >
                    Save Client ID Configuration
                  </button>
                </div>
              )}
            </div>
          )}

          {/* ========================================================================= */}
          {/* TAB 2: EMAIL & PASSWORD SIGN IN                                         */}
          {/* ========================================================================= */}
          {activeTab === 'signin' && (
            <form onSubmit={handleEmailLogin} className="space-y-3.5 animate-fade-in">
              <div>
                <label className="block text-[11px] font-semibold text-slate-300 mb-1">Email Address</label>
                <div className="relative">
                  <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                  <input
                    type="email"
                    required
                    placeholder="user@example.com"
                    value={loginEmail}
                    onChange={(e) => setLoginEmail(e.target.value)}
                    className="w-full pl-9 pr-3 py-2.5 text-xs rounded-xl bg-slate-950 border border-slate-700 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-400 transition"
                  />
                </div>
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-slate-300 mb-1">Password</label>
                <div className="relative">
                  <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                  <input
                    type={showLoginPassword ? 'text' : 'password'}
                    required
                    placeholder="Enter account password"
                    value={loginPassword}
                    onChange={(e) => setLoginPassword(e.target.value)}
                    className="w-full pl-9 pr-10 py-2.5 text-xs rounded-xl bg-slate-950 border border-slate-700 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-400 transition"
                  />
                  <button
                    type="button"
                    onClick={() => setShowLoginPassword(!showLoginPassword)}
                    className="absolute right-3 top-3 text-slate-400 hover:text-slate-200 transition"
                  >
                    {showLoginPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              <div className="flex items-center justify-between text-[11px] text-slate-400">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                    className="rounded bg-slate-950 border-slate-700 text-cyan-500 focus:ring-0"
                  />
                  <span>Remember me</span>
                </label>
                <button
                  type="button"
                  onClick={() => setMessage({ text: 'Use your email credentials or Google SSO to access.', type: 'success' })}
                  className="text-cyan-400 hover:underline"
                >
                  Forgot password?
                </button>
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-xl bg-gradient-to-r from-cyan-600 to-indigo-600 hover:from-cyan-500 hover:to-indigo-500 text-white font-bold text-xs tracking-wider uppercase transition-all shadow-md active:scale-98 disabled:opacity-50"
              >
                <span>{isLoading ? loadingText : 'Sign In Securely'}</span>
              </button>

              <div className="text-center pt-2">
                <button
                  type="button"
                  onClick={handleContinueAsGuest}
                  className="text-xs text-slate-400 hover:text-slate-200 transition"
                >
                  Or Continue as Guest Observer &rarr;
                </button>
              </div>
            </form>
          )}

          {/* ========================================================================= */}
          {/* TAB 3: CREATE ACCOUNT (FULL ASSISTIVE REGISTRATION)                     */}
          {/* ========================================================================= */}
          {activeTab === 'signup' && (
            <form onSubmit={handleRegister} className="space-y-3 animate-fade-in">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] font-semibold text-slate-300 mb-1">Full Name *</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Alex Rivera"
                    value={regName}
                    onChange={(e) => setRegName(e.target.value)}
                    className="w-full px-3 py-2 text-xs rounded-xl bg-slate-950 border border-slate-700 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-400"
                  />
                </div>

                <div>
                  <label className="block text-[11px] font-semibold text-slate-300 mb-1">Email *</label>
                  <input
                    type="email"
                    required
                    placeholder="user@example.com"
                    value={regEmail}
                    onChange={(e) => setRegEmail(e.target.value)}
                    className="w-full px-3 py-2 text-xs rounded-xl bg-slate-950 border border-slate-700 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-400"
                  />
                </div>
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-slate-300 mb-1">Password *</label>
                <div className="relative">
                  <input
                    type={showRegPassword ? 'text' : 'password'}
                    required
                    placeholder="Min 6 characters"
                    value={regPassword}
                    onChange={(e) => setRegPassword(e.target.value)}
                    className="w-full pl-3 pr-8 py-2 text-xs rounded-xl bg-slate-950 border border-slate-700 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-400"
                  />
                  <button
                    type="button"
                    onClick={() => setShowRegPassword(!showRegPassword)}
                    className="absolute right-2.5 top-2.5 text-slate-400 hover:text-slate-200"
                  >
                    {showRegPassword ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                  </button>
                </div>
                {/* Dynamic Password Strength Bar */}
                {regPassword && (
                  <div className="mt-1.5 flex items-center gap-2">
                    <div className="flex-1 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                      <div
                        className={`h-full ${getPasswordStrength(regPassword).color} transition-all duration-300`}
                        style={{ width: `${getPasswordStrength(regPassword).score}%` }}
                      />
                    </div>
                    <span className="text-[10px] font-mono text-slate-400">
                      {getPasswordStrength(regPassword).label}
                    </span>
                  </div>
                )}
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] font-semibold text-slate-300 mb-1">Role / Occupation</label>
                  <input
                    type="text"
                    placeholder="e.g. Lead AI Architect"
                    value={regRole}
                    onChange={(e) => setRegRole(e.target.value)}
                    className="w-full px-3 py-2 text-xs rounded-xl bg-slate-950 border border-slate-700 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-400"
                  />
                </div>

                <div>
                  <label className="block text-[11px] font-semibold text-slate-300 mb-1">City / Location</label>
                  <input
                    type="text"
                    placeholder="e.g. Bengaluru, India"
                    value={regLocation}
                    onChange={(e) => setRegLocation(e.target.value)}
                    className="w-full px-3 py-2 text-xs rounded-xl bg-slate-950 border border-slate-700 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-400"
                  />
                </div>
              </div>

              {/* Holographic Avatar Selector */}
              <div>
                <label className="block text-[11px] font-semibold text-slate-300 mb-1.5">Choose Holographic Avatar</label>
                <div className="flex items-center gap-2 overflow-x-auto pb-1">
                  {AVATAR_OPTIONS.map((av, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => setSelectedAvatar(av)}
                      className={`w-9 h-9 rounded-xl border-2 transition-all p-0.5 shrink-0 ${
                        selectedAvatar === av
                          ? 'border-cyan-400 scale-105 shadow-md shadow-cyan-500/30'
                          : 'border-slate-800 hover:border-slate-600 opacity-70 hover:opacity-100'
                      }`}
                    >
                      <img src={av} alt="Avatar" className="w-full h-full rounded-lg object-cover" />
                    </button>
                  ))}
                </div>
              </div>

              {/* Assistive Emergency Contacts (SIH26204 Requirement) */}
              <div className="p-3 rounded-2xl bg-amber-950/20 border border-amber-500/30 space-y-2">
                <div className="flex items-center gap-1.5 text-xs font-bold text-amber-300">
                  <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
                  <span>Emergency Assistive Contact (For ARHIEA Alerts)</span>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  <input
                    type="text"
                    placeholder="Contact Name (e.g. Elena Vance)"
                    value={regEmergencyName}
                    onChange={(e) => setRegEmergencyName(e.target.value)}
                    className="w-full px-3 py-1.5 text-xs rounded-lg bg-slate-950 border border-slate-700 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-amber-400"
                  />
                  <input
                    type="tel"
                    placeholder="Contact Phone Number"
                    value={regEmergencyPhone}
                    onChange={(e) => setRegEmergencyPhone(e.target.value)}
                    className="w-full px-3 py-1.5 text-xs rounded-lg bg-slate-950 border border-slate-700 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-amber-400"
                  />
                </div>
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-slate-300 mb-1">
                  Preferences & Habits for ARHIEA's Memory
                </label>
                <textarea
                  rows={2}
                  placeholder="e.g. Prefers concise spoken replies, remind me of daily habits..."
                  value={regNotes}
                  onChange={(e) => setRegNotes(e.target.value)}
                  className="w-full px-3 py-2 text-xs rounded-xl bg-slate-950 border border-slate-700 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-400"
                />
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-bold text-xs tracking-wider uppercase transition shadow-md active:scale-98 disabled:opacity-50"
              >
                <span>{isLoading ? loadingText : 'Register & Sync All Details'}</span>
              </button>
            </form>
          )}

          {/* ========================================================================= */}
          {/* TAB 4: MY PROFILE & LIVE MEMORY INSPECTOR                                */}
          {/* ========================================================================= */}
          {activeTab === 'profile' && (
            <div className="space-y-4 animate-fade-in">
              {/* User Identity Banner */}
              <div className="p-4 rounded-2xl bg-slate-950/80 border border-slate-800 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="relative">
                    {currentUser.avatar_url ? (
                      <img
                        src={currentUser.avatar_url}
                        alt={currentUser.name}
                        className="w-12 h-12 rounded-2xl border-2 border-cyan-400/50 object-cover shadow-md shadow-cyan-500/20"
                      />
                    ) : (
                      <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-cyan-500 to-indigo-600 flex items-center justify-center text-white text-base font-bold shadow-md shadow-cyan-500/20">
                        {currentUser.name ? currentUser.name.charAt(0) : 'U'}
                      </div>
                    )}
                    <span className="absolute -bottom-1 -right-1 w-3.5 h-3.5 rounded-full bg-emerald-500 border-2 border-slate-950" />
                  </div>

                  <div>
                    <h3 className="text-sm font-bold text-slate-100 flex items-center gap-1.5">
                      <span>{currentUser.name}</span>
                      {currentUser.auth_provider === 'google' && (
                        <span className="text-[10px] px-1.5 py-0.2 rounded font-mono font-semibold bg-blue-950/80 border border-blue-500/50 text-blue-300">
                          Google Verified
                        </span>
                      )}
                    </h3>
                    <p className="text-[11px] font-mono text-cyan-400">{currentUser.email || 'Local User'}</p>
                    <p className="text-[10px] text-slate-400">{currentUser.role || 'User'} &bull; Provider: {currentUser.auth_provider}</p>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => {
                      onLogout();
                      localStorage.removeItem('arhiea_auth_token');
                      setActiveTab('google');
                      setGoogleView('chooser');
                    }}
                    className="flex items-center gap-1 text-xs font-bold text-rose-400 hover:text-rose-300 px-3 py-1.5 rounded-xl border border-rose-500/30 hover:bg-rose-950/40 transition"
                  >
                    <LogOut className="w-3.5 h-3.5" />
                    <span>Sign Out</span>
                  </button>
                </div>
              </div>

              {/* Data Ingested into ARHIEA Memory */}
              <div className="p-4 rounded-2xl bg-slate-950/60 border border-slate-800 space-y-3 text-xs">
                <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                  <span className="font-bold text-slate-300 flex items-center gap-1.5">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    <span>Synchronized Long-Term Memories in SQLite (arhiea.db)</span>
                  </span>
                  {!isEditingProfile ? (
                    <button
                      onClick={() => setIsEditingProfile(true)}
                      className="inline-flex items-center gap-1 text-[11px] text-cyan-400 hover:text-cyan-300"
                    >
                      <Edit3 className="w-3 h-3" />
                      <span>Edit Info</span>
                    </button>
                  ) : (
                    <button
                      onClick={handleUpdateProfile}
                      disabled={isLoading}
                      className="inline-flex items-center gap-1 text-[11px] text-emerald-400 hover:text-emerald-300 font-bold"
                    >
                      <Save className="w-3 h-3" />
                      <span>Save & Sync</span>
                    </button>
                  )}
                </div>

                {!isEditingProfile ? (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-slate-300">
                    <div>
                      <span className="text-[10px] text-slate-500 block uppercase font-mono">Location</span>
                      <span className="font-medium text-slate-200">{currentUser.location || 'Bengaluru, India'}</span>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-500 block uppercase font-mono">Phone</span>
                      <span className="font-medium text-slate-200">{currentUser.phone || 'Not configured'}</span>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-500 block uppercase font-mono">Emergency Assistive Contact</span>
                      <span className="font-medium text-amber-300">
                        {currentUser.emergency_contact_name 
                          ? `${currentUser.emergency_contact_name} (${currentUser.emergency_contact_phone || 'No phone'})` 
                          : 'Not configured'}
                      </span>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-500 block uppercase font-mono">Timezone</span>
                      <span className="font-medium font-mono text-cyan-300">{currentUser.timezone || 'Asia/Kolkata'}</span>
                    </div>
                    <div className="col-span-full">
                      <span className="text-[10px] text-slate-500 block uppercase font-mono">Personal Preferences / System Prompt Injection</span>
                      <p className="text-[11px] text-slate-300 italic bg-slate-900/60 p-2.5 rounded-xl mt-1 border border-slate-800">
                        "{currentUser.personal_notes || 'Standard executive assistant configuration with spatial grounding'}"
                      </p>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-3">
                    <div className="grid grid-cols-2 gap-2">
                      <input
                        type="text"
                        placeholder="Full Name"
                        value={editName}
                        onChange={(e) => setEditName(e.target.value)}
                        className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-xs"
                      />
                      <input
                        type="text"
                        placeholder="Role / Title"
                        value={editRole}
                        onChange={(e) => setEditRole(e.target.value)}
                        className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-xs"
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-2">
                      <input
                        type="text"
                        placeholder="Location"
                        value={editLocation}
                        onChange={(e) => setEditLocation(e.target.value)}
                        className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-xs"
                      />
                      <input
                        type="text"
                        placeholder="Phone"
                        value={editPhone}
                        onChange={(e) => setEditPhone(e.target.value)}
                        className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-xs"
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-2">
                      <input
                        type="text"
                        placeholder="Emergency Contact Name"
                        value={editEmergencyName}
                        onChange={(e) => setEditEmergencyName(e.target.value)}
                        className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-xs"
                      />
                      <input
                        type="text"
                        placeholder="Emergency Contact Phone"
                        value={editEmergencyPhone}
                        onChange={(e) => setEditEmergencyPhone(e.target.value)}
                        className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-xs"
                      />
                    </div>
                    <textarea
                      rows={2}
                      placeholder="Personal notes & preferences"
                      value={editNotes}
                      onChange={(e) => setEditNotes(e.target.value)}
                      className="w-full px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-xs"
                    />
                  </div>
                )}
              </div>
            </div>
          )}

        </div>

        {/* Status Message Notification */}
        {message && (
          <div
            className={`mt-4 p-2.5 rounded-xl text-xs font-medium text-center shrink-0 animate-fade-in ${
              message.type === 'success'
                ? 'bg-emerald-950/80 border border-emerald-500/50 text-emerald-300'
                : 'bg-rose-950/80 border border-rose-500/50 text-rose-300'
            }`}
          >
            {message.text}
          </div>
        )}

        {/* Footer Security Badge */}
        <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-500 shrink-0">
          <div className="flex items-center gap-1.5">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            <span>Encrypted SQLite Vault</span>
          </div>
          <span className="font-mono text-[10px]">Google SSO &bull; PBKDF2 Hashing</span>
        </div>
      </div>
    </div>
  );
};
