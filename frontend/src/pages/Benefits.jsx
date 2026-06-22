import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  HiOutlineArrowLeft, HiOutlineCurrencyRupee, HiOutlineCheckCircle,
  HiOutlineExclamation, HiOutlineExternalLink, HiOutlineTrash,
  HiOutlineChartPie, HiOutlineLightningBolt, HiOutlineSparkles,
  HiOutlineAcademicCap
} from 'react-icons/hi';
import SchemeDetailModal from '../components/SchemeDetailModal';
import './Benefits.css';

export default function Benefits() {
  const [eligibleSchemes, setEligibleSchemes] = useState([]);
  const [viewedSlugs, setViewedSlugs] = useState([]);
  const [activeModal, setActiveModal] = useState(null);
  const [activeTab, setActiveTab] = useState('missed'); // 'missed' | 'viewed'
  const navigate = useNavigate();

  useEffect(() => {
    const raw = sessionStorage.getItem('analysisResult');
    if (raw) {
      const data = JSON.parse(raw);
      setEligibleSchemes(data.eligible_schemes || []);
    }
    setViewedSlugs(JSON.parse(localStorage.getItem('viewed_schemes') || '[]'));
  }, []);

  const refreshViewed = () => {
    setViewedSlugs(JSON.parse(localStorage.getItem('viewed_schemes') || '[]'));
  };

  const handleModalClose = () => {
    setActiveModal(null);
    refreshViewed();
  };

  const clearViewed = () => {
    localStorage.removeItem('viewed_schemes');
    setViewedSlugs([]);
  };

  const formatAmount = (a) => {
    if (!a) return '₹0';
    if (a >= 100000) return `₹${(a / 100000).toFixed(1)}L`;
    if (a >= 1000) return `₹${(a / 1000).toFixed(0)}K`;
    return `₹${a}`;
  };

  const viewedSchemes = eligibleSchemes.filter(s => viewedSlugs.includes(s.slug));
  const missedSchemes = eligibleSchemes.filter(s => !viewedSlugs.includes(s.slug));
  const totalPotential = eligibleSchemes.reduce((sum, s) => sum + (s.benefit_amount || 0), 0);
  const viewedBenefit = viewedSchemes.reduce((sum, s) => sum + (s.benefit_amount || 0), 0);
  const missedBenefit = missedSchemes.reduce((sum, s) => sum + (s.benefit_amount || 0), 0);
  const captureRate = totalPotential > 0 ? Math.round((viewedBenefit / totalPotential) * 100) : 0;

  const displaySchemes = activeTab === 'missed' ? missedSchemes : viewedSchemes;

  if (eligibleSchemes.length === 0) {
    return (
      <div className="benefits-page">
        <div className="container">
          <button className="btn btn-ghost results-back" onClick={() => navigate('/results')}>
            <HiOutlineArrowLeft /> Back to Results
          </button>
          <div className="benefits-empty glass-card">
            <HiOutlineAcademicCap className="empty-icon" />
            <h2 className="heading-md">No Analysis Found</h2>
            <p>Run a scheme analysis first to see your benefit gap dashboard.</p>
            <Link to="/analyze" className="btn btn-primary" style={{ marginTop: 16 }}>
              Analyse My Profile →
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="benefits-page">
      <div className="container">
        <button className="btn btn-ghost results-back" onClick={() => navigate('/results')}>
          <HiOutlineArrowLeft /> Back to Results
        </button>

        {/* Page Title */}
        <div className="benefits-hero animate-fadeInUp">
          <div>
            <h1 className="heading-lg">
              Benefit <span className="text-gradient">Gap Analysis</span>
            </h1>
            <p className="benefits-subtitle">
              Track schemes you've explored and discover what benefits you're still missing out on.
            </p>
          </div>
          {viewedSlugs.length > 0 && (
            <button className="btn btn-ghost btn-sm" onClick={clearViewed} id="clear-viewed-btn">
              <HiOutlineTrash /> Reset Tracker
            </button>
          )}
        </div>

        {/* Summary Cards */}
        <div className="benefits-summary animate-fadeInUp stagger-1">
          {/* Capture Rate Gauge */}
          <div className="capture-card glass-card">
            <div className="capture-gauge">
              <svg viewBox="0 0 120 120" className="gauge-svg">
                <circle cx="60" cy="60" r="50" className="gauge-track" />
                <circle
                  cx="60" cy="60" r="50"
                  className="gauge-fill"
                  strokeDasharray={`${(captureRate / 100) * 314} 314`}
                  transform="rotate(-90 60 60)"
                />
              </svg>
              <div className="gauge-center">
                <span className="gauge-value">{captureRate}%</span>
                <span className="gauge-label">Captured</span>
              </div>
            </div>
            <div className="capture-info">
              <h3 className="heading-sm">Benefits Capture Rate</h3>
              <p>You've explored <strong>{viewedSchemes.length}</strong> out of <strong>{eligibleSchemes.length}</strong> eligible schemes.</p>
            </div>
          </div>

          {/* Stats */}
          <div className="benefits-stats">
            <div className="bstat-card glass-card bstat--green">
              <HiOutlineCheckCircle className="bstat-icon" />
              <div>
                <span className="bstat-value">{formatAmount(viewedBenefit)}</span>
                <span className="bstat-label">Benefits Explored</span>
                <span className="bstat-sub">{viewedSchemes.length} schemes viewed</span>
              </div>
            </div>
            <div className="bstat-card glass-card bstat--warn">
              <HiOutlineExclamation className="bstat-icon" />
              <div>
                <span className="bstat-value">{formatAmount(missedBenefit)}</span>
                <span className="bstat-label">Benefits Unclaimed</span>
                <span className="bstat-sub">{missedSchemes.length} schemes unexplored</span>
              </div>
            </div>
            <div className="bstat-card glass-card bstat--primary">
              <HiOutlineChartPie className="bstat-icon" />
              <div>
                <span className="bstat-value">{formatAmount(totalPotential)}</span>
                <span className="bstat-label">Total Potential</span>
                <span className="bstat-sub">{eligibleSchemes.length} eligible schemes</span>
              </div>
            </div>
          </div>
        </div>

        {/* Missed Benefits Alert */}
        {missedSchemes.length > 0 && (
          <div className="missed-alert glass-card animate-fadeInUp stagger-2">
            <HiOutlineLightningBolt className="missed-alert-icon" />
            <div>
              <h4 className="heading-sm">Don't leave money on the table!</h4>
              <p>
                You're potentially missing <strong>{formatAmount(missedBenefit)}</strong> in annual benefits from{' '}
                <strong>{missedSchemes.length} unexplored schemes</strong>.
                Click any scheme below to view full details and apply.
              </p>
            </div>
          </div>
        )}

        {/* Tabs */}
        <div className="benefits-tabs animate-fadeInUp stagger-3">
          <button
            className={`benefits-tab ${activeTab === 'missed' ? 'benefits-tab--active' : ''}`}
            onClick={() => setActiveTab('missed')}
            id="tab-missed"
          >
            <HiOutlineExclamation /> Not Yet Explored
            <span className="tab-count tab-count--warn">{missedSchemes.length}</span>
          </button>
          <button
            className={`benefits-tab ${activeTab === 'viewed' ? 'benefits-tab--active' : ''}`}
            onClick={() => setActiveTab('viewed')}
            id="tab-viewed"
          >
            <HiOutlineCheckCircle /> Viewed / Applied
            <span className="tab-count tab-count--green">{viewedSchemes.length}</span>
          </button>
        </div>

        {/* Scheme List */}
        {displaySchemes.length === 0 ? (
          <div className="benefits-tab-empty glass-card animate-fadeIn">
            <HiOutlineSparkles className="empty-icon-sm" />
            {activeTab === 'missed'
              ? <p>🎉 Great job! You've explored all your eligible schemes.</p>
              : <p>You haven't viewed any schemes yet. Click "View Details" on the Results page.</p>
            }
          </div>
        ) : (
          <div className="benefits-list animate-fadeInUp">
            {displaySchemes.map((scheme, i) => (
              <div
                key={scheme.slug}
                className={`benefit-row glass-card ${activeTab === 'viewed' ? 'benefit-row--viewed' : ''}`}
                id={`benefit-row-${scheme.slug}`}
              >
                <div className="benefit-row-rank">#{i + 1}</div>
                <div className="benefit-row-info">
                  <h4 className="benefit-row-name">{scheme.scheme_name}</h4>
                  <div className="benefit-row-meta">
                    {scheme.level && <span className="badge badge-primary">{scheme.level}</span>}
                    {scheme.benefit_type && <span className="badge badge-green">{scheme.benefit_type}</span>}
                    {scheme.category && scheme.category !== 'nan' && (
                      <span className="badge badge-warm">{scheme.category}</span>
                    )}
                    <span className="match-pct">
                      {Math.round(scheme.match_score || 0)}% match
                    </span>
                  </div>
                  {scheme.details_snippet && (
                    <p className="benefit-row-desc">{scheme.details_snippet.substring(0, 100)}...</p>
                  )}
                </div>
                <div className="benefit-row-right">
                  {scheme.benefit_amount && (
                    <div className="benefit-row-amount">
                      <HiOutlineCurrencyRupee />
                      <span>{formatAmount(scheme.benefit_amount)}</span>
                      <small>/yr</small>
                    </div>
                  )}
                  <div className="benefit-row-actions">
                    <button
                      className="btn btn-secondary btn-sm"
                      onClick={() => setActiveModal(scheme.slug)}
                      id={`view-btn-${scheme.slug}`}
                    >
                      View Details
                    </button>
                    {scheme.portal_url && (
                      <a
                        href={scheme.portal_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="btn btn-primary btn-sm"
                        id={`apply-row-${scheme.slug}`}
                      >
                        Apply <HiOutlineExternalLink />
                      </a>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {activeModal && (
        <SchemeDetailModal slug={activeModal} onClose={handleModalClose} />
      )}
    </div>
  );
}
