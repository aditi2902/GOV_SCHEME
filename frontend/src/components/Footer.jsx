import { Link } from 'react-router-dom';
import { RiGovernmentLine } from 'react-icons/ri';
import {
  HiOutlineMail, HiOutlinePhone, HiOutlineLocationMarker, HiOutlineExternalLink,
} from 'react-icons/hi';
import './Footer.css';

export default function Footer() {
  const year = new Date().getFullYear();

  const quickLinks = [
    { to: '/analyze', label: 'Find Schemes' },
    { to: '/benefits', label: 'Benefit Analysis' },
    { to: '/chat', label: 'Ask AI Assistant' },
    { to: '/dashboard', label: 'My Dashboard' },
  ];

  const resources = [
    { href: 'https://www.myscheme.gov.in', label: 'MyScheme Portal' },
    { href: 'https://scholarships.gov.in', label: 'National Scholarship Portal' },
    { href: 'https://www.india.gov.in', label: 'National Portal of India' },
    { href: 'https://www.digitalindia.gov.in', label: 'Digital India' },
  ];

  return (
    <footer className="site-footer">
      <div className="footer-tricolor" />

      <div className="container footer-grid">
        <div className="footer-col footer-col-brand">
          <div className="footer-brand">
            <span className="footer-logo"><RiGovernmentLine /></span>
            <span className="footer-brand-name">Sarkari<span className="text-gradient">Sahay</span></span>
          </div>
          <p className="footer-tagline">
            AI-powered government scheme discovery — helping every Indian citizen find
            the scholarships, subsidies, and benefits they qualify for.
          </p>
        </div>

        <div className="footer-col">
          <h4 className="footer-col-title">Quick Links</h4>
          <ul className="footer-list">
            {quickLinks.map((l) => (
              <li key={l.to}><Link to={l.to}>{l.label}</Link></li>
            ))}
          </ul>
        </div>

        <div className="footer-col">
          <h4 className="footer-col-title">Official Resources</h4>
          <ul className="footer-list">
            {resources.map((r) => (
              <li key={r.href}>
                <a href={r.href} target="_blank" rel="noopener noreferrer">
                  {r.label} <HiOutlineExternalLink className="footer-ext-icon" />
                </a>
              </li>
            ))}
          </ul>
        </div>

        <div className="footer-col">
          <h4 className="footer-col-title">Contact</h4>
          <ul className="footer-list footer-contact">
            <li><HiOutlineLocationMarker /> New Delhi, India</li>
            <li><HiOutlineMail /> support@sarkarisahay.example</li>
            <li><HiOutlinePhone /> 1800-XXX-XXXX (Toll Free)</li>
          </ul>
        </div>
      </div>

      <div className="footer-bottom">
        <div className="container footer-bottom-inner">
          <p>© {year} SarkariSahay. Data sourced from MyScheme, NSP &amp; official government portals.</p>
          <p className="footer-disclaimer">Not an official Government of India website — an independent aid tool.</p>
        </div>
      </div>
    </footer>
  );
}
