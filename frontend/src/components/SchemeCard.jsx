import { HiOutlineStar, HiOutlineCurrencyRupee, HiOutlineAcademicCap, HiOutlineShieldCheck } from 'react-icons/hi';
import './SchemeCard.css';

export default function SchemeCard({ scheme, rank, onClick }) {
  const getBenefitColor = (type) => {
    const colors = {
      scholarship: 'badge-primary',
      fellowship: 'badge-gold',
      internship: 'badge-green',
      stipend: 'badge-warm',
    };
    return colors[type?.toLowerCase()] || 'badge-primary';
  };

  const formatAmount = (amount) => {
    if (!amount) return null;
    if (amount >= 100000) return `₹${(amount / 100000).toFixed(1)}L`;
    if (amount >= 1000) return `₹${(amount / 1000).toFixed(0)}K`;
    return `₹${amount}`;
  };

  return (
    <div className="scheme-card glass-card" onClick={onClick} role="button" tabIndex={0}>
      <div className="scheme-card-header">
        <div className="scheme-rank-badge">#{rank}</div>
        <div className="scheme-score-ring">
          <svg viewBox="0 0 36 36" className="score-svg">
            <path
              className="score-bg"
              d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
            />
            <path
              className="score-fill"
              strokeDasharray={`${scheme.match_score || 0}, 100`}
              d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
            />
          </svg>
          <span className="score-text">{Math.round(scheme.match_score || 0)}%</span>
        </div>
      </div>

      <h3 className="scheme-card-title">{scheme.scheme_name}</h3>

      <div className="scheme-card-meta">
        {scheme.benefit_type && (
          <span className={`badge ${getBenefitColor(scheme.benefit_type)}`}>
            <HiOutlineAcademicCap /> {scheme.benefit_type}
          </span>
        )}
        {scheme.level && (
          <span className="badge badge-primary">
            <HiOutlineShieldCheck /> {scheme.level}
          </span>
        )}
      </div>

      {scheme.benefit_amount && (
        <div className="scheme-benefit-amount">
          <HiOutlineCurrencyRupee />
          <span>{formatAmount(scheme.benefit_amount)}</span>
          <span className="benefit-label">/ year</span>
        </div>
      )}

      {scheme.details_snippet && (
        <p className="scheme-card-desc">
          {scheme.details_snippet.substring(0, 120)}...
        </p>
      )}

      <div className="scheme-card-footer">
        <div className="scheme-score-bar">
          <div className="score-bar-track">
            <div
              className="score-bar-fill"
              style={{ width: `${scheme.score ? Math.min((scheme.score / 80) * 100, 100) : 0}%` }}
            />
          </div>
          <span className="score-label">Score: {scheme.score?.toFixed(1)}</span>
        </div>
        <span className="scheme-card-cta">View Details →</span>
      </div>
    </div>
  );
}
