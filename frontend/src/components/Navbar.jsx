import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useState } from 'react';
import { HiOutlineMenu, HiOutlineX, HiOutlineSun, HiOutlineMoon, HiOutlineLogout, HiOutlineViewGrid } from 'react-icons/hi';
import { RiGovernmentLine } from 'react-icons/ri';
import { useTheme } from '../context/ThemeContext';
import { useAuth } from '../context/AuthContext';
import './Navbar.css';

export default function Navbar() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const { theme, toggleTheme } = useTheme();
  const { user, logout } = useAuth();

  const links = [
    { to: '/', label: 'Home' },
    { to: '/analyze', label: 'Find Schemes' },
    { to: '/benefits', label: 'Benefit Analysis' },
    { to: '/chat', label: 'Ask AI' },
  ];

  const initials = user
    ? user.name.split(' ').map((n) => n[0]).slice(0, 2).join('').toUpperCase()
    : '';

  const handleLogout = () => {
    setMenuOpen(false);
    logout();
    navigate('/');
  };

  return (
    <nav className="navbar">
      <div className="container navbar-inner">
        <Link to="/" className="navbar-brand" onClick={() => setMobileOpen(false)}>
          <span className="navbar-logo"><RiGovernmentLine /></span>
          <span className="navbar-title">Sarkari<span className="text-gradient">Sahay</span></span>
        </Link>

        <div className={`navbar-links ${mobileOpen ? 'open' : ''}`}>
          {links.map((l) => (
            <Link
              key={l.to}
              to={l.to}
              className={`navbar-link ${location.pathname === l.to ? 'active' : ''}`}
              onClick={() => setMobileOpen(false)}
            >
              {l.label}
            </Link>
          ))}
          {user && (
            <Link
              to="/dashboard"
              className={`navbar-link mobile-only-link ${location.pathname === '/dashboard' ? 'active' : ''}`}
              onClick={() => setMobileOpen(false)}
            >
              Dashboard
            </Link>
          )}
        </div>

        <div className="navbar-actions">
          <button
            className="navbar-theme-btn"
            onClick={toggleTheme}
            aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
            title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
          >
            {theme === 'dark' ? <HiOutlineSun /> : <HiOutlineMoon />}
          </button>

          {user ? (
            <div className="navbar-user">
              <button
                className="navbar-avatar"
                onClick={() => setMenuOpen((o) => !o)}
                aria-label="Account menu"
              >
                {initials}
              </button>
              {menuOpen && (
                <>
                  <div className="navbar-menu-backdrop" onClick={() => setMenuOpen(false)} />
                  <div className="navbar-menu">
                    <div className="navbar-menu-head">
                      <span className="navbar-menu-name">{user.name}</span>
                      <span className="navbar-menu-email">{user.email}</span>
                    </div>
                    <Link to="/dashboard" className="navbar-menu-item" onClick={() => setMenuOpen(false)}>
                      <HiOutlineViewGrid /> Dashboard
                    </Link>
                    <button className="navbar-menu-item" onClick={handleLogout}>
                      <HiOutlineLogout /> Sign out
                    </button>
                  </div>
                </>
              )}
            </div>
          ) : (
            <Link to="/login" className="btn btn-primary btn-sm navbar-signin">Sign In</Link>
          )}

          <button
            className="navbar-toggle"
            onClick={() => setMobileOpen(!mobileOpen)}
            aria-label="Toggle menu"
          >
            {mobileOpen ? <HiOutlineX /> : <HiOutlineMenu />}
          </button>
        </div>
      </div>
    </nav>
  );
}
