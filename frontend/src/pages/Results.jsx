import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  HiOutlineCurrencyRupee, HiOutlineAcademicCap, HiOutlineDocumentText,
  HiOutlineChartBar, HiOutlineExclamation, HiOutlineArrowLeft,
  HiOutlineLocationMarker, HiOutlineUser, HiOutlineBriefcase,
  HiOutlineCheckCircle, HiOutlineSparkles
} from 'react-icons/hi';
import SchemeCard from '../components/SchemeCard';
import ReadinessGauge from '../components/ReadinessGauge';
import SchemeDetailModal from '../components/SchemeDetailModal';
import './Results.css';

export default function Results() {
  const [data, setData] = useState(null);
  const [activeModal, setActiveModal] = useState(null); // slug of scheme to show in modal
  const [showGuidance, setShowGuidance] = useState(false);
  const [viewedSlugs, setViewedSlugs] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    const raw = sessionStorage.getItem('analysisResult');
    if (!raw) {
      navigate('/analyze');
      return;
    }
    setData(JSON.parse(raw));
    // Load viewed slugs
    setViewedSlugs(JSON.parse(localStorage.getItem('viewed_schemes') || '[]'));
  }, [navigate]);

  // Refresh viewed slugs when modal closes
  const handleModalClose = () => {
    setActiveModal(null);
    setViewedSlugs(JSON.parse(localStorage.getItem('viewed_schemes') || '[]'));
  };

  if (!data) return null;

  const { profile, eligible_count, total_schemes, potential_annual_benefit, readiness_score,
    eligible_schemes, top_rejection_reasons, document_checklist, guidance } = data;

  const formatAmount = (a) => {
    if (!a) return '₹0';
    if (a >= 100000) return `₹${(a / 100000).toFixed(1)}L`;
    if (a >= 1000) return `₹${(a / 1000).toFixed(0)}K`;
    return `₹${a}`;
  };

  // Compute benefit gap stats
  const viewedSchemes = eligible_schemes.filter(s => viewedSlugs.includes(s.slug));
  const missedSchemes = eligible_schemes.filter(s => !viewedSlugs.includes(s.slug));
  const missedBenefit = missedSchemes.reduce((sum, s) => sum + (s.benefit_amount || 0), 0);

  return (
    <div className="results-page">
      <div className="container">
        {/* Back Button */}
        <button className="btn btn-ghost results-back" onClick={() => navigate('/analyze')}>
          <HiOutlineArrowLeft /> Back to Profile
        </button>

        {data.insufficient_data ? (
          <div className="insufficient-data-card glass-card animate-fadeInUp">
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '16px', color: 'var(--accent)' }}>
              <HiOutlineExclamation style={{ fontSize: '2rem' }} />
              <h2 className="heading-md" style={{ margin: 0 }}>Insufficient Information</h2>
            </div>
            <p style={{ color: 'var(--text-secondary)', fontSize: '1.05rem', lineHeight: '1.6', marginBottom: '24px' }}>
              {data.error_message}
            </p>
            <div style={{ background: 'rgba(255, 107, 107, 0.1)', padding: '16px', borderRadius: '8px', border: '1px solid rgba(255, 107, 107, 0.2)' }}>
              <h4 style={{ marginBottom: '8px', color: 'var(--text-primary)' }}>What we understood from your input:</h4>
              <ul style={{ listStyle: 'none', padding: 0, margin: 0, color: 'var(--text-secondary)' }}>
                {Object.entries(profile).filter(([_, v]) => v !== null && v !== false).length > 0 ? (
                  Object.entries(profile)
                    .filter(([_, v]) => v !== null && v !== false)
                    .map(([k, v]) => (
                      <li key={k} style={{ marginBottom: '4px' }}>
                        <strong style={{ textTransform: 'capitalize' }}>{k.replace('_', ' ')}:</strong> {v}
                      </li>
                    ))
                ) : (
                  <li><em>No usable profile details found.</em></li>
                )}
              </ul>
            </div>
            <button className="btn btn-primary" onClick={() => navigate('/analyze')} style={{ marginTop: '24px' }}>
              Try Again
            </button>
          </div>
        ) : (
          <>
            {/* Header Stats */}
        <div className="results-hero animate-fadeInUp">
          <div className="results-hero-left">
            <h1 className="heading-lg">
              Your Scheme <span className="text-gradient">Analysis</span>
            </h1>

            <div className="stats-row">
              <div className="stat-card glass-card">
                <HiOutlineAcademicCap className="stat-icon" style={{ color: 'var(--primary)' }} />
                <div>
                  <span className="stat-value">{eligible_count}</span>
                  <span className="stat-label">Eligible Schemes</span>
                </div>
              </div>
              <div className="stat-card glass-card">
                <HiOutlineCurrencyRupee className="stat-icon" style={{ color: 'var(--accent)' }} />
                <div>
                  <span className="stat-value">{formatAmount(potential_annual_benefit)}</span>
                  <span className="stat-label">Potential Benefits</span>
                </div>
              </div>
              <div className="stat-card glass-card">
                <HiOutlineChartBar className="stat-icon" style={{ color: 'var(--accent-green)' }} />
                <div>
                  <span className="stat-value">{total_schemes}</span>
                  <span className="stat-label">Total Checked</span>
                </div>
              </div>
            </div>
          </div>

          <div className="results-hero-right">
            <ReadinessGauge score={readiness_score} />
          </div>
        </div>

        {/* Profile Card */}
        <div className="profile-card glass-card animate-fadeInUp stagger-1">
          <h3 className="heading-sm profile-card-title">
            <HiOutlineUser /> Extracted Profile
          </h3>
          <div className="profile-tags">
            {profile.gender && (
              <span className="profile-tag">
                <HiOutlineUser /> {profile.gender}
              </span>
            )}
            {profile.state && (
              <span className="profile-tag">
                <HiOutlineLocationMarker /> {profile.state}
              </span>
            )}
            {profile.education_level && (
              <span className="profile-tag">
                <HiOutlineAcademicCap /> {profile.education_level}
              </span>
            )}
            {profile.course && (
              <span className="profile-tag">
                <HiOutlineBriefcase /> {profile.course}
              </span>
            )}
            {profile.income && (
              <span className="profile-tag">
                <HiOutlineCurrencyRupee /> {formatAmount(profile.income)} income
              </span>
            )}
            {profile.cgpa && (
              <span className="profile-tag">CGPA: {profile.cgpa}</span>
            )}
            {profile.category && (
              <span className="profile-tag">Category: {profile.category}</span>
            )}
            {profile.year_of_study && (
              <span className="profile-tag">Year: {profile.year_of_study}</span>
            )}
            {profile.age && (
              <span className="profile-tag">Age: {profile.age}</span>
            )}
          </div>
        </div>

        {/* Benefit Gap Analysis */}
        {eligible_count > 0 && (
          <div className="benefit-gap-card glass-card animate-fadeInUp stagger-2">
            <div className="benefit-gap-header">
              <div className="benefit-gap-icon">
                <HiOutlineSparkles />
              </div>
              <div>
                <h4 className="heading-sm">Benefit Gap Analysis</h4>
                <p>Track which schemes you've explored and what you might be missing.</p>
              </div>
              <Link to="/benefits" className="btn btn-secondary btn-sm">
                Full Analysis →
              </Link>
            </div>
            <div className="benefit-gap-stats">
              <div className="gap-stat gap-stat--green">
                <HiOutlineCheckCircle className="gap-stat-icon" />
                <div>
                  <span className="gap-stat-value">{viewedSchemes.length}</span>
                  <span className="gap-stat-label">Schemes Viewed</span>
                </div>
              </div>
              <div className="gap-stat gap-stat--warn">
                <HiOutlineExclamation className="gap-stat-icon" />
                <div>
                  <span className="gap-stat-value">{missedSchemes.length}</span>
                  <span className="gap-stat-label">Not Yet Explored</span>
                </div>
              </div>
              <div className="gap-stat gap-stat--primary">
                <HiOutlineCurrencyRupee className="gap-stat-icon" />
                <div>
                  <span className="gap-stat-value">{formatAmount(missedBenefit)}</span>
                  <span className="gap-stat-label">Benefits Unclaimed</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Eligible Schemes Grid */}
        <section className="results-section animate-fadeInUp stagger-3">
          <h2 className="heading-md results-section-title">
            <HiOutlineChartBar /> Top Recommended Schemes
          </h2>

          {eligible_schemes.length > 0 ? (
            <div className="schemes-grid">
              {eligible_schemes.slice(0, 12).map((scheme, i) => (
                <SchemeCard
                  key={scheme.slug || i}
                  scheme={scheme}
                  rank={i + 1}
                  onViewDetails={(slug) => setActiveModal(slug)}
                />
              ))}
            </div>
          ) : (
            <div className="no-schemes glass-card">
              <p>No eligible schemes found. Try broadening your profile description.</p>
            </div>
          )}
        </section>

        {/* Rejection Reasons */}
        {top_rejection_reasons?.length > 0 && (
          <section className="results-section animate-fadeInUp">
            <h2 className="heading-md results-section-title">
              <HiOutlineExclamation /> Why Some Schemes Didn't Match
            </h2>
            <div className="rejection-list glass-card">
              {top_rejection_reasons.slice(0, 5).map((r, i) => (
                <div key={i} className="rejection-item">
                  <span className="rejection-num">{i + 1}</span>
                  <span>{r}</span>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Document Checklist */}
        {document_checklist?.length > 0 && (
          <section className="results-section animate-fadeInUp">
            <h2 className="heading-md results-section-title">
              <HiOutlineDocumentText /> Document Checklist
            </h2>
            <div className="docs-grid">
              {document_checklist.slice(0, 6).map((doc, i) => (
                <div key={i} className="doc-card glass-card">
                  <h4 className="doc-scheme-name">{doc.scheme_name?.substring(0, 60)}</h4>
                  {doc.required?.length > 0 && (
                    <div className="doc-list">
                      <span className="doc-list-label">Required:</span>
                      {doc.required.map((d, j) => (
                        <span key={j} className="doc-item">{d}</span>
                      ))}
                    </div>
                  )}
                  {doc.readiness_tip && (
                    <p className="doc-tip">💡 {doc.readiness_tip}</p>
                  )}
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Chat CTA */}
        <div className="results-cta glass-card animate-fadeInUp">
          <h3 className="heading-md">Have questions about these schemes?</h3>
          <p>Ask our AI assistant anything — eligibility, documents, application process.</p>
          <Link to="/chat" className="btn btn-primary">Ask AI Assistant →</Link>
        </div>
          </>
        )}
      </div>

      {/* Scheme Detail Modal */}
      {activeModal && (
        <SchemeDetailModal
          slug={activeModal}
          onClose={handleModalClose}
        />
      )}
    </div>
  );
}
