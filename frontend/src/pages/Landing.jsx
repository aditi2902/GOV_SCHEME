import { Link } from 'react-router-dom';
import {
  HiOutlineSearch, HiOutlineLightningBolt, HiOutlineDocumentText, HiOutlineChartBar,
  HiOutlineChatAlt2, HiOutlineShieldCheck, HiOutlineArrowRight, HiOutlineCheckCircle,
  HiOutlineBadgeCheck, HiOutlineAcademicCap, HiOutlineCurrencyRupee,
} from 'react-icons/hi';
import { RiGovernmentLine } from 'react-icons/ri';
import IndiaMap from '../components/IndiaMap';
import './Landing.css';

export default function Landing() {
  const features = [
    {
      icon: <HiOutlineSearch />,
      title: 'AI Eligibility Finder',
      desc: 'Describe yourself in plain language. Our AI instantly matches you with schemes you qualify for.',
      color: 'var(--primary)',
    },
    {
      icon: <HiOutlineChartBar />,
      title: 'Smart Ranking',
      desc: 'Schemes ranked by benefit amount, eligibility match, and application ease — see the best first.',
      color: 'var(--accent-green)',
    },
    {
      icon: <HiOutlineDocumentText />,
      title: 'Document Checklist',
      desc: 'Know exactly which documents you need. Never miss an application due to missing paperwork.',
      color: 'var(--accent)',
    },
    {
      icon: <HiOutlineChatAlt2 />,
      title: 'Ask Anything',
      desc: '"Can I apply without income certificate?" — get instant AI answers from scheme documents.',
      color: 'var(--accent-teal)',
    },
    {
      icon: <HiOutlineShieldCheck />,
      title: 'Benefit Gap Analysis',
      desc: 'Discover schemes you\'re missing out on. See your total potential benefits at a glance.',
      color: 'var(--gov-amber)',
    },
    {
      icon: <HiOutlineBadgeCheck />,
      title: 'Verified Sources',
      desc: 'Every scheme is sourced from MyScheme, NSP, and official state/central government portals.',
      color: 'var(--gov-green)',
    },
  ];

  const bannerStats = [
    { value: '580+', label: 'Schemes Indexed', icon: <HiOutlineDocumentText /> },
    { value: '<30s', label: 'Avg. Match Time', icon: <HiOutlineLightningBolt /> },
    { value: '₹1.2L+', label: 'Avg. Potential Benefit', icon: <HiOutlineCurrencyRupee /> },
    { value: '100%', label: 'Free To Use', icon: <HiOutlineShieldCheck /> },
  ];

  const aboutPoints = [
    'Real-time eligibility matching against 580+ Central & State schemes',
    'No paperwork guesswork — see the exact documents you need upfront',
    'Deterministic rule-based scoring, not a black-box AI guess',
    'Your profile is saved securely to your account for instant re-matching',
  ];

  const steps = [
    { num: '01', title: 'Describe Yourself', desc: 'Tell us your age, state, education, and income — in plain language or through a guided form.' },
    { num: '02', title: 'Engine Analyzes', desc: 'Our rule-based matching engine checks eligibility, ranks schemes by benefit, and verifies documents — with AI-generated guidance on top.' },
    { num: '03', title: 'Get Eligible Schemes', desc: 'See eligible schemes ranked by value, with the exact documents needed and eligibility reasoning.' },
  ];

  return (
    <div className="landing">
      {/* ── Hero ─────────────────────────────────────── */}
      <section className="hero">
        <div className="hero-bg-elements">
          <div className="hero-orb hero-orb-1" />
          <div className="hero-orb hero-orb-2" />
        </div>

        <div className="container hero-grid">
          {/* Left: copy */}
          <div className="hero-copy">
            <div className="hero-badge animate-fadeInUp">
              <RiGovernmentLine />
              <span>AI-Powered Government Scheme Discovery</span>
            </div>

            <h1 className="heading-xl animate-fadeInUp stagger-1">
              Find Every Scheme<br />
              <span className="text-gradient">You Deserve</span>
            </h1>

            <p className="hero-subtitle animate-fadeInUp stagger-2">
              Stop searching through 20 government websites. Tell us about yourself,
              and our AI finds, ranks, and guides you through every scheme you qualify for.
            </p>

            <div className="hero-actions animate-fadeInUp stagger-3">
              <Link to="/analyze" className="btn btn-primary btn-lg">
                <HiOutlineSearch /> Find My Schemes
              </Link>
              <Link to="/chat" className="btn btn-secondary btn-lg">
                <HiOutlineChatAlt2 /> Ask AI
              </Link>
            </div>

            <div className="hero-trust animate-fadeInUp stagger-4">
              <span><HiOutlineCheckCircle /> No fees, ever</span>
              <span><HiOutlineCheckCircle /> Official sources only</span>
              <span><HiOutlineCheckCircle /> Data saved to your account</span>
            </div>
          </div>

          {/* Right: illustrated mock panel */}
          <div className="hero-visual animate-fadeInUp stagger-2">
            <div className="hero-mock-card">
              <div className="hero-mock-topbar">
                <span className="hero-mock-dot" /><span className="hero-mock-dot" /><span className="hero-mock-dot" />
                <span className="hero-mock-url">sarkarisahay.gov.in/results</span>
              </div>
              <div className="hero-mock-body">
                {[
                  { name: 'Pre-Matric Scholarship', pct: 96, tone: 'green' },
                  { name: 'National Merit Scheme', pct: 88, tone: 'blue' },
                  { name: 'State Education Grant', pct: 74, tone: 'orange' },
                ].map((row, i) => (
                  <div className="hero-mock-row" key={i}>
                    <span className={`hero-mock-icon tone-${row.tone}`}><HiOutlineAcademicCap /></span>
                    <div className="hero-mock-lines">
                      <span className="hero-mock-line-title">{row.name}</span>
                      <span className="hero-mock-line-bar"><i style={{ width: `${row.pct}%` }} /></span>
                    </div>
                    <span className={`hero-mock-pct tone-${row.tone}`}>{row.pct}%</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="hero-float-chip chip-verified">
              <HiOutlineBadgeCheck /> Verified Schemes
            </div>
            <div className="hero-float-chip chip-instant">
              <HiOutlineLightningBolt /> Instant Match
            </div>
          </div>
        </div>

        {/* Floating stat strip overlapping hero edge */}
        <div className="container">
          <div className="hero-stat-strip animate-fadeInUp stagger-4">
            {bannerStats.slice(0, 4).map((s, i) => (
              <div key={i} className="hero-stat-pill">
                <span className="hero-stat-pill-icon">{s.icon}</span>
                <div>
                  <span className="hero-stat-pill-value">{s.value}</span>
                  <span className="hero-stat-pill-label">{s.label}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── About / Info Section ────────────────────── */}
      <section className="section about-section">
        <div className="container about-grid">
          <div className="about-visual">
            <div className="about-map-wrap">
              <IndiaMap />
            </div>
            <div className="about-visual-badge about-badge-1">
              <HiOutlineDocumentText /> 580+ Schemes
            </div>
            <div className="about-visual-badge about-badge-2">
              <HiOutlineShieldCheck /> Govt. Verified
            </div>
            <p className="about-map-credit">
              Map: <a href="https://commons.wikimedia.org/wiki/File:India_outline.svg" target="_blank" rel="noopener noreferrer">Wikimedia Commons</a> (CC BY-SA 3.0)
            </p>
          </div>

          <div className="about-content">
            <span className="section-eyebrow">About The Platform</span>
            <h2 className="heading-lg">
              One place to discover <span className="text-gradient">every benefit</span> you're entitled to
            </h2>
            <p className="about-desc">
              Government scholarships and welfare schemes are scattered across dozens of
              ministries, states, and portals. SarkariSahay brings them into a single,
              deterministic matching engine — so you spend less time searching and more
              time applying.
            </p>
            <ul className="about-points">
              {aboutPoints.map((p, i) => (
                <li key={i}><HiOutlineCheckCircle /> {p}</li>
              ))}
            </ul>
            <Link to="/analyze" className="about-link">
              Start your eligibility check <HiOutlineArrowRight />
            </Link>
          </div>
        </div>
      </section>

      {/* ── Features ─────────────────────────────────── */}
      <section className="section features-section">
        <div className="container">
          <div className="section-head text-center">
            <span className="section-eyebrow">Why SarkariSahay</span>
            <h2 className="heading-lg">
              Everything You Need, <span className="text-gradient-warm">In One Place</span>
            </h2>
            <p className="section-subtitle">
              Not just search — intelligent analysis, ranking, and personalized guidance
            </p>
          </div>

          <div className="features-grid">
            {features.map((f, i) => (
              <div
                key={i}
                className="feature-card animate-fadeInUp"
                style={{ animationDelay: `${0.06 * i}s`, '--fcolor': f.color }}
              >
                <div className="feature-icon" style={{ color: f.color, background: `${f.color}16` }}>
                  {f.icon}
                </div>
                <h3 className="heading-sm">{f.title}</h3>
                <p className="feature-desc">{f.desc}</p>
                <Link to="/analyze" className="feature-link" style={{ color: f.color }}>
                  Learn more <HiOutlineArrowRight />
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Colorful Stats Banner ────────────────────── */}
      <section className="stats-banner">
        <div className="container stats-banner-grid">
          {bannerStats.map((s, i) => (
            <div key={i} className="stats-banner-item">
              <span className="stats-banner-icon">{s.icon}</span>
              <span className="stats-banner-value">{s.value}</span>
              <span className="stats-banner-label">{s.label}</span>
            </div>
          ))}
        </div>
      </section>

      {/* ── How It Works ─────────────────────────────── */}
      <section className="section how-it-works">
        <div className="container">
          <div className="section-head text-center">
            <span className="section-eyebrow">Simple Process</span>
            <h2 className="heading-lg">
              How It <span className="text-gradient">Works</span>
            </h2>
            <p className="section-subtitle">From confusion to clarity in three simple steps</p>
          </div>

          <div className="steps-track">
            {steps.map((step, i) => (
              <div key={i} className="step-item">
                <div className="step-circle">{step.num}</div>
                {i < steps.length - 1 && <div className="step-line" />}
                <h3 className="heading-sm">{step.title}</h3>
                <p className="step-desc">{step.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA Banner ───────────────────────────────── */}
      <section className="cta-banner-section">
        <div className="container cta-banner">
          <div className="cta-banner-text">
            <h2 className="heading-lg">Ready to discover your benefits?</h2>
            <p>Join students and families finding scholarships and schemes they never knew existed.</p>
          </div>
          <Link to="/analyze" className="btn btn-lg cta-banner-btn">
            Get Started — It&apos;s Free <HiOutlineArrowRight />
          </Link>
        </div>
      </section>
    </div>
  );
}
