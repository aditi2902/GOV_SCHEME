import { useState } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { HiOutlineMail, HiOutlineLockClosed, HiOutlineUser, HiOutlineEye, HiOutlineEyeOff } from 'react-icons/hi';
import { RiGovernmentLine } from 'react-icons/ri';
import { useAuth } from '../context/AuthContext';
import './Login.css';

export default function Login() {
  const [mode, setMode] = useState('login'); // 'login' | 'signup'
  const [form, setForm] = useState({ name: '', email: '', password: '' });
  const [showPw, setShowPw] = useState(false);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const { login, signup } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const redirectTo = location.state?.from || '/dashboard';

  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  const submit = (e) => {
    e.preventDefault();
    setError('');

    const email = form.email.trim();
    if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email))
      return setError('Please enter a valid email address.');
    if (form.password.length < 4)
      return setError('Password must be at least 4 characters.');
    if (mode === 'signup' && !form.name.trim())
      return setError('Please enter your name.');

    setBusy(true);
    try {
      if (mode === 'login') login(email, form.password);
      else signup(form.name, email, form.password);
      navigate(redirectTo, { replace: true });
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const switchMode = (m) => {
    setMode(m);
    setError('');
  };

  return (
    <div className="auth-page">
      <div className="auth-card animate-fadeInUp">
        <div className="auth-brand">
          <div className="auth-brand-logo"><RiGovernmentLine /></div>
          <span className="auth-brand-title">
            Sarkari<span className="text-gradient">Sahay</span>
          </span>
        </div>

        <div className="auth-tabs" role="tablist">
          <button
            className={`auth-tab ${mode === 'login' ? 'active' : ''}`}
            onClick={() => switchMode('login')}
            type="button"
          >
            Sign In
          </button>
          <button
            className={`auth-tab ${mode === 'signup' ? 'active' : ''}`}
            onClick={() => switchMode('signup')}
            type="button"
          >
            Create Account
          </button>
        </div>

        <p className="auth-sub">
          {mode === 'login'
            ? 'Sign in to see your saved schemes and skip re-entering your details.'
            : 'Create an account so your profile and matched schemes are saved for next time.'}
        </p>

        <form className="auth-form" onSubmit={submit}>
          {mode === 'signup' && (
            <div className="auth-field">
              <label className="auth-label" htmlFor="auth-name">Full Name</label>
              <div className="auth-input-wrap">
                <HiOutlineUser className="auth-input-icon" />
                <input
                  id="auth-name"
                  className="input auth-input"
                  type="text"
                  placeholder="e.g. Aditi Sharma"
                  value={form.name}
                  onChange={(e) => set('name', e.target.value)}
                  autoComplete="name"
                />
              </div>
            </div>
          )}

          <div className="auth-field">
            <label className="auth-label" htmlFor="auth-email">Email</label>
            <div className="auth-input-wrap">
              <HiOutlineMail className="auth-input-icon" />
              <input
                id="auth-email"
                className="input auth-input"
                type="email"
                placeholder="you@example.com"
                value={form.email}
                onChange={(e) => set('email', e.target.value)}
                autoComplete="email"
              />
            </div>
          </div>

          <div className="auth-field">
            <label className="auth-label" htmlFor="auth-password">Password</label>
            <div className="auth-input-wrap">
              <HiOutlineLockClosed className="auth-input-icon" />
              <input
                id="auth-password"
                className="input auth-input"
                type={showPw ? 'text' : 'password'}
                placeholder="••••••••"
                value={form.password}
                onChange={(e) => set('password', e.target.value)}
                autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
              />
              <button
                type="button"
                className="auth-eye"
                onClick={() => setShowPw((s) => !s)}
                aria-label={showPw ? 'Hide password' : 'Show password'}
              >
                {showPw ? <HiOutlineEyeOff /> : <HiOutlineEye />}
              </button>
            </div>
          </div>

          {error && <div className="auth-error" role="alert">⚠️ {error}</div>}

          <button className="btn btn-primary btn-lg auth-submit" type="submit" disabled={busy}>
            {busy ? 'Please wait…' : mode === 'login' ? 'Sign In' : 'Create Account'}
          </button>
        </form>

        <p className="auth-switch">
          {mode === 'login' ? (
            <>New here? <button type="button" onClick={() => switchMode('signup')}>Create an account</button></>
          ) : (
            <>Already have an account? <button type="button" onClick={() => switchMode('login')}>Sign in</button></>
          )}
        </p>

        <p className="auth-note">
          🔒 This is a demo — your account is stored locally in this browser only.
        </p>

        <Link to="/" className="auth-back">← Back to home</Link>
      </div>
    </div>
  );
}
