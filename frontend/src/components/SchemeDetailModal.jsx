import { useState, useEffect } from 'react';
import { HiOutlineX, HiOutlineExternalLink, HiOutlineCheckCircle, HiOutlineCurrencyRupee, HiOutlineDocumentText, HiOutlineShieldCheck, HiOutlineLocationMarker, HiOutlineAcademicCap, HiOutlineClipboardList, HiOutlineUserGroup } from 'react-icons/hi';
import { getSchemeDetail } from '../api';
import './SchemeDetailModal.css';

export default function SchemeDetailModal({ slug, onClose }) {
  const [scheme, setScheme] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isViewed, setIsViewed] = useState(false);

  useEffect(() => {
    // Check if already viewed
    const viewed = JSON.parse(localStorage.getItem('viewed_schemes') || '[]');
    setIsViewed(viewed.includes(slug));

    // Fetch full detail
    setLoading(true);
    getSchemeDetail(slug)
      .then(data => {
        setScheme(data);
        setLoading(false);
        // Auto-mark as viewed when modal opens
        markViewed(slug);
      })
      .catch(err => {
        setError('Failed to load scheme details.');
        setLoading(false);
      });
  }, [slug]);

  const markViewed = (s) => {
    const viewed = JSON.parse(localStorage.getItem('viewed_schemes') || '[]');
    if (!viewed.includes(s)) {
      viewed.push(s);
      localStorage.setItem('viewed_schemes', JSON.stringify(viewed));
    }
    setIsViewed(true);
  };

  const formatAmount = (a) => {
    if (!a) return null;
    if (a >= 100000) return `₹${(a / 100000).toFixed(1)}L`;
    if (a >= 1000) return `₹${(a / 1000).toFixed(0)}K`;
    return `₹${a}`;
  };

  const parseList = (text) => {
    if (!text || text === 'nan') return [];
    return text
      .split(/\n|(?<=\.)(?=\s*[A-Z0-9])/)
      .map(s => s.trim())
      .filter(s => s.length > 5);
  };

  // Close on backdrop click
  const handleBackdrop = (e) => {
    if (e.target === e.currentTarget) onClose();
  };

  return (
    <div className="modal-backdrop" onClick={handleBackdrop}>
      <div className="modal-container animate-fadeIn">
        {/* Modal Header */}
        <div className="modal-header">
          <div className="modal-header-left">
            {scheme && (
              <div className="modal-badges">
                {scheme.level && <span className="badge badge-primary">{scheme.level}</span>}
                {scheme.benefit_type && <span className="badge badge-green">{scheme.benefit_type}</span>}
                {scheme.state && <span className="badge badge-warm">{scheme.state}</span>}
              </div>
            )}
            <h2 className="modal-title">{loading ? 'Loading...' : scheme?.scheme_name}</h2>
          </div>
          <button className="modal-close" onClick={onClose} id="modal-close-btn">
            <HiOutlineX />
          </button>
        </div>

        {/* Modal Body */}
        <div className="modal-body">
          {loading && (
            <div className="modal-loading">
              <div className="spinner" />
              <p>Loading scheme details...</p>
            </div>
          )}

          {error && <div className="modal-error">{error}</div>}

          {scheme && !loading && (
            <>
              {/* Benefit Amount Hero */}
              {scheme.benefit_amount && (
                <div className="modal-benefit-hero">
                  <HiOutlineCurrencyRupee className="benefit-hero-icon" />
                  <div>
                    <div className="benefit-hero-amount">{formatAmount(scheme.benefit_amount)}</div>
                    <div className="benefit-hero-label">per year · {scheme.benefit_type || 'benefit'}</div>
                  </div>
                </div>
              )}

              {/* Quick Tags Row */}
              <div className="modal-tags-row">
                {scheme.income_max && (
                  <div className="modal-tag-pill">
                    <HiOutlineCurrencyRupee />
                    <span>Income ≤ {formatAmount(scheme.income_max)}/yr</span>
                  </div>
                )}
                {scheme.caste_category && (
                  <div className="modal-tag-pill">
                    <HiOutlineUserGroup />
                    <span>{scheme.caste_category}</span>
                  </div>
                )}
                {scheme.education_level && (
                  <div className="modal-tag-pill">
                    <HiOutlineAcademicCap />
                    <span>{scheme.education_level}</span>
                  </div>
                )}
                {scheme.cgpa_min && (
                  <div className="modal-tag-pill">
                    <HiOutlineShieldCheck />
                    <span>Min {scheme.cgpa_min}% marks</span>
                  </div>
                )}
                {scheme.gender && scheme.gender !== 'nan' && (
                  <div className="modal-tag-pill">
                    <HiOutlineUserGroup />
                    <span>{scheme.gender} only</span>
                  </div>
                )}
                {scheme.disability_required && (
                  <div className="modal-tag-pill modal-tag-pill--warn">
                    <HiOutlineShieldCheck />
                    <span>PwD Required</span>
                  </div>
                )}
              </div>

              {/* Details Section */}
              {scheme.details && scheme.details !== 'nan' && (
                <div className="modal-section">
                  <h3 className="modal-section-title">
                    <HiOutlineClipboardList /> About this Scheme
                  </h3>
                  <p className="modal-section-text">{scheme.details}</p>
                </div>
              )}

              {/* Benefits */}
              {scheme.benefits && scheme.benefits !== 'nan' && (
                <div className="modal-section">
                  <h3 className="modal-section-title">
                    <HiOutlineCurrencyRupee /> Benefits
                  </h3>
                  <p className="modal-section-text">{scheme.benefits}</p>
                </div>
              )}

              {/* Eligibility */}
              {scheme.eligibility && scheme.eligibility !== 'nan' && (
                <div className="modal-section">
                  <h3 className="modal-section-title">
                    <HiOutlineShieldCheck /> Eligibility Criteria
                  </h3>
                  <ul className="modal-list modal-list--check">
                    {parseList(scheme.eligibility).map((item, i) => (
                      <li key={i}><HiOutlineCheckCircle className="list-check-icon" />{item}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Application Process */}
              {scheme.application && scheme.application !== 'nan' && (
                <div className="modal-section">
                  <h3 className="modal-section-title">
                    <HiOutlineDocumentText /> How to Apply
                  </h3>
                  <p className="modal-section-text modal-section-text--pre">{scheme.application}</p>
                </div>
              )}

              {/* Documents */}
              {scheme.documents && scheme.documents !== 'nan' && (
                <div className="modal-section">
                  <h3 className="modal-section-title">
                    <HiOutlineClipboardList /> Required Documents
                  </h3>
                  <ul className="modal-list modal-list--docs">
                    {parseList(scheme.documents).map((doc, i) => (
                      <li key={i}><span className="doc-bullet">📄</span>{doc}</li>
                    ))}
                  </ul>
                </div>
              )}
            </>
          )}
        </div>

        {/* Modal Footer */}
        {scheme && !loading && (
          <div className="modal-footer">
            <div className="modal-footer-left">
              {isViewed && (
                <span className="viewed-badge">
                  <HiOutlineCheckCircle /> Marked as Viewed
                </span>
              )}
            </div>
            <div className="modal-footer-right">
              <button className="btn btn-secondary" onClick={onClose}>
                Close
              </button>
              <a
                href={scheme.portal_url}
                target="_blank"
                rel="noopener noreferrer"
                className="btn btn-primary"
                id={`apply-btn-${scheme.slug}`}
              >
                Apply on Govt Portal <HiOutlineExternalLink />
              </a>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
