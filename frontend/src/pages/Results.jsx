import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  HiOutlineCurrencyRupee, HiOutlineAcademicCap, HiOutlineDocumentText,
  HiOutlineChartBar, HiOutlineExclamation, HiOutlineArrowLeft,
  HiOutlineLocationMarker, HiOutlineUser, HiOutlineBriefcase
} from 'react-icons/hi';
import SchemeCard from '../components/SchemeCard';
import ReadinessGauge from '../components/ReadinessGauge';
import './Results.css';

export default function Results() {
  const [data, setData] = useState(null);
  const [selectedScheme, setSelectedScheme] = useState(null);
  const [showGuidance, setShowGuidance] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const raw = sessionStorage.getItem('analysisResult');
    if (!raw) {
      navigate('/analyze');
      return;
    }
    setData(JSON.parse(raw));
  }, [navigate]);

  if (!data) return null;

  const { profile, eligible_count, total_schemes, potential_annual_benefit, readiness_score,
    eligible_schemes, top_rejection_reasons, document_checklist, guidance } = data;

  const formatAmount = (a) => {
    if (!a) return '₹0';
    if (a >= 100000) return `₹${(a / 100000).toFixed(1)}L`;
    if (a >= 1000) return `₹${(a / 1000).toFixed(0)}K`;
    return `₹${a}`;
  };

  return (
    <div className="results-page">
      <div className="container">
        {/* Back Button */}
        <button className="btn btn-ghost results-back" onClick={() => navigate('/analyze')}>
          <HiOutlineArrowLeft /> Back to Profile
        </button>

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

        {/* Benefit Gap Alert */}
        {eligible_count > 0 && (
          <div className="benefit-alert glass-card animate-fadeInUp stagger-2">
            <div className="benefit-alert-icon">
              <HiOutlineExclamation />
            </div>
            <div>
              <h4 className="heading-sm">Benefit Gap Analysis</h4>
              <p>
                You qualify for <strong>{eligible_count} schemes</strong> out of {total_schemes} checked.
                Your potential annual benefits exceed <strong>{formatAmount(potential_annual_benefit)}</strong>.
                {eligible_count > 5 && " Most students only utilize 1-2 schemes — don't miss out!"}
              </p>
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
                  onClick={() => setSelectedScheme(selectedScheme?.slug === scheme.slug ? null : scheme)}
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

        {/* AI Guidance */}
        {guidance && (
          <section className="results-section animate-fadeInUp">
            <h2 className="heading-md results-section-title">
              <HiOutlineBriefcase /> AI Application Roadmap
            </h2>
            <button
              className="btn btn-secondary"
              onClick={() => setShowGuidance(!showGuidance)}
              style={{ marginBottom: 16 }}
            >
              {showGuidance ? 'Hide' : 'Show'} AI Guidance
            </button>
            {showGuidance && (
              <div className="guidance-card glass-card">
                <div className="guidance-content" dangerouslySetInnerHTML={{
                  __html: guidance
                    .replace(/\n/g, '<br/>')
                    .replace(/#{1,3}\s(.+)/g, '<h4>$1</h4>')
                    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
                    .replace(/\*(.+?)\*/g, '<em>$1</em>')
                }} />
              </div>
            )}
          </section>
        )}

        {/* Chat CTA */}
        <div className="results-cta glass-card animate-fadeInUp">
          <h3 className="heading-md">Have questions about these schemes?</h3>
          <p>Ask our AI assistant anything — eligibility, documents, application process.</p>
          <Link to="/chat" className="btn btn-primary">Ask AI Assistant →</Link>
        </div>
      </div>
    </div>
  );
}
