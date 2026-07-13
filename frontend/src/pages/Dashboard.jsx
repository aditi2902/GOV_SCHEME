import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  HiOutlineUser, HiOutlineLocationMarker, HiOutlineAcademicCap,
  HiOutlineCurrencyRupee, HiOutlineBriefcase, HiOutlineChartBar,
  HiOutlineSparkles, HiOutlineRefresh, HiOutlinePlus,
} from 'react-icons/hi';
import SchemeCard from '../components/SchemeCard';
import SchemeDetailModal from '../components/SchemeDetailModal';
import { useAuth } from '../context/AuthContext';
import { getUserData } from '../utils/storage';
import './Dashboard.css';

export default function Dashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [data, setData] = useState({ profile: null, lastResult: null, savedAt: null });
  const [activeModal, setActiveModal] = useState(null);

  useEffect(() => {
    if (user) setData(getUserData(user.email));
  }, [user]);

  const { profile, lastResult, savedAt } = data;
  const result = lastResult;

  const formatAmount = (a) => {
    if (!a) return '₹0';
    if (a >= 100000) return `₹${(a / 100000).toFixed(1)}L`;
    if (a >= 1000) return `₹${(a / 1000).toFixed(0)}K`;
    return `₹${a}`;
  };

  const firstName = (user?.name || 'there').split(' ')[0];

  const openSavedResults = () => {
    if (result) {
      sessionStorage.setItem('analysisResult', JSON.stringify(result));
      navigate('/results');
    }
  };

  return (
    <div className="dash-page">
      <div className="container">
        {/* Greeting */}
        <div className="dash-head animate-fadeInUp">
          <div>
            <h1 className="heading-lg">
              Welcome back, <span className="text-gradient">{firstName}</span>
            </h1>
            <p className="dash-sub">
              {savedAt
                ? `Your details are saved — last updated ${new Date(savedAt).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}.`
                : 'Set up your profile to get personalised scheme matches.'}
            </p>
          </div>
          <div className="dash-head-actions">
            <Link to="/analyze" className="btn btn-secondary">
              <HiOutlineRefresh /> {profile ? 'Update details' : 'Add details'}
            </Link>
            {result && (
              <button className="btn btn-primary" onClick={openSavedResults}>
                <HiOutlineChartBar /> View full analysis
              </button>
            )}
          </div>
        </div>

        {!profile && !result ? (
          /* Empty state */
          <div className="dash-empty glass-card animate-fadeInUp stagger-1">
            <div className="dash-empty-icon"><HiOutlineSparkles /></div>
            <h2 className="heading-md">No saved profile yet</h2>
            <p>
              Fill in your details once and we'll remember them — so you never have to
              re-enter your age, income, or education level again.
            </p>
            <Link to="/analyze" className="btn btn-primary btn-lg">
              <HiOutlinePlus /> Find my schemes
            </Link>
          </div>
        ) : (
          <>
            {/* Stat row */}
            {result && (
              <div className="dash-stats animate-fadeInUp stagger-1">
                <div className="dash-stat glass-card">
                  <HiOutlineAcademicCap className="dash-stat-icon" style={{ color: 'var(--primary)' }} />
                  <div>
                    <span className="dash-stat-value">{result.eligible_count ?? 0}</span>
                    <span className="dash-stat-label">Eligible schemes</span>
                  </div>
                </div>
                <div className="dash-stat glass-card">
                  <HiOutlineCurrencyRupee className="dash-stat-icon" style={{ color: 'var(--gov-orange)' }} />
                  <div>
                    <span className="dash-stat-value">{formatAmount(result.potential_annual_benefit)}</span>
                    <span className="dash-stat-label">Potential benefits</span>
                  </div>
                </div>
                <div className="dash-stat glass-card">
                  <HiOutlineChartBar className="dash-stat-icon" style={{ color: 'var(--gov-green)' }} />
                  <div>
                    <span className="dash-stat-value">{result.readiness_score ?? 0}%</span>
                    <span className="dash-stat-label">Readiness score</span>
                  </div>
                </div>
              </div>
            )}

            {/* Saved profile */}
            {profile && (
              <div className="dash-profile glass-card animate-fadeInUp stagger-2">
                <div className="dash-profile-head">
                  <h3 className="heading-sm"><HiOutlineUser /> Your saved profile</h3>
                  <Link to="/analyze" className="dash-edit-link">Edit</Link>
                </div>
                <div className="dash-tags">
                  {profile.age && <span className="dash-tag">Age: {profile.age}</span>}
                  {profile.gender && <span className="dash-tag"><HiOutlineUser /> {profile.gender}</span>}
                  {profile.category && <span className="dash-tag">Category: {profile.category}</span>}
                  {profile.state && <span className="dash-tag"><HiOutlineLocationMarker /> {profile.state}</span>}
                  {profile.education_level && <span className="dash-tag"><HiOutlineAcademicCap /> {profile.education_level}</span>}
                  {profile.course && <span className="dash-tag"><HiOutlineBriefcase /> {profile.course}</span>}
                  {(profile.income || profile.income === 0) && (
                    <span className="dash-tag"><HiOutlineCurrencyRupee /> {formatAmount(profile.income)} income</span>
                  )}
                  {profile.cgpa && <span className="dash-tag">Score: {profile.cgpa}</span>}
                  {profile.year_of_study && <span className="dash-tag">Year/Class: {profile.year_of_study}</span>}
                </div>
              </div>
            )}

            {/* Saved schemes */}
            {result?.eligible_schemes?.length > 0 && (
              <section className="dash-section animate-fadeInUp stagger-3">
                <div className="dash-section-head">
                  <h2 className="heading-md"><HiOutlineSparkles /> Your matched schemes</h2>
                  <button className="btn btn-ghost btn-sm" onClick={openSavedResults}>See all →</button>
                </div>
                <div className="dash-schemes-grid">
                  {result.eligible_schemes.slice(0, 6).map((scheme, i) => (
                    <SchemeCard
                      key={scheme.slug || i}
                      scheme={scheme}
                      rank={i + 1}
                      onViewDetails={(slug) => setActiveModal(slug)}
                    />
                  ))}
                </div>
              </section>
            )}

            {profile && !result && (
              <div className="dash-empty glass-card animate-fadeInUp stagger-3">
                <p>Your profile is saved, but no analysis has been run yet.</p>
                <Link to="/analyze" className="btn btn-primary">Run scheme matching</Link>
              </div>
            )}
          </>
        )}
      </div>

      {activeModal && (
        <SchemeDetailModal slug={activeModal} onClose={() => setActiveModal(null)} />
      )}
    </div>
  );
}
