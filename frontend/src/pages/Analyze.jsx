import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { HiOutlineSearch, HiOutlineUser, HiOutlineLightningBolt } from 'react-icons/hi';
import { analyzeProfile, analyzeQuick } from '../api';
import './Analyze.css';

const EXAMPLE_PROFILES = [
  "I am a 20 year old female engineering student from Maharashtra. Family income is 4 lakh per annum. I'm in 3rd year B.Tech with 8.5 CGPA.",
  "Male, 22, pursuing M.Tech in Computer Science. From Karnataka. Family income 6 lakh. OBC category.",
  "I'm a girl from Tamil Nadu studying B.Sc Nursing. My parents earn 3 lakh per year. I belong to SC category.",
  "21 year old male ITI student from Uttar Pradesh. Family income 2 lakh. General category. Have a mild disability.",
];

export default function Analyze() {
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e, quick = false) => {
    e.preventDefault();
    if (!text.trim() || text.trim().length < 10) {
      setError('Please describe yourself in more detail (at least 10 characters).');
      return;
    }
    setError('');
    setLoading(true);

    try {
      const fn = quick ? analyzeQuick : analyzeProfile;
      const result = await fn(text.trim());
      // Store result and navigate to results page
      sessionStorage.setItem('analysisResult', JSON.stringify(result));
      sessionStorage.setItem('userText', text.trim());
      navigate('/results');
    } catch (err) {
      setError(`Analysis failed: ${err.message}. Make sure the backend is running.`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="analyze-page">
      <div className="container">
        <div className="analyze-header animate-fadeInUp">
          <h1 className="heading-lg">
            Tell Us About <span className="text-gradient">Yourself</span>
          </h1>
          <p className="analyze-subtitle">
            Describe your background in plain language — age, gender, state, education, income, category. 
            Our AI will extract your profile and find matching schemes.
          </p>
        </div>

        <form className="analyze-form animate-fadeInUp stagger-1" onSubmit={(e) => handleSubmit(e, false)}>
          <div className="form-group">
            <label className="form-label" htmlFor="profile-input">
              <HiOutlineUser /> Your Profile Description
            </label>
            <textarea
              id="profile-input"
              className="input analyze-textarea"
              placeholder="Example: I am a 20 year old female engineering student from Maharashtra. My family income is 4 lakh per annum. I'm in 3rd year B.Tech with 8.5 CGPA."
              value={text}
              onChange={(e) => setText(e.target.value)}
              rows={5}
              disabled={loading}
            />
          </div>

          {error && <div className="analyze-error">{error}</div>}

          <div className="analyze-actions">
            <button type="submit" className="btn btn-primary btn-lg" disabled={loading}>
              {loading ? (
                <>
                  <span className="spinner" style={{ width: 20, height: 20 }} /> Analyzing...
                </>
              ) : (
                <>
                  <HiOutlineSearch /> Find Schemes + AI Guidance
                </>
              )}
            </button>
            <button
              type="button"
              className="btn btn-secondary btn-lg"
              disabled={loading}
              onClick={(e) => handleSubmit(e, true)}
            >
              <HiOutlineLightningBolt /> Quick Analysis
            </button>
          </div>

          {loading && (
            <div className="analyze-loading-message">
              <div className="loading-dots">
                <span /><span /><span />
              </div>
              <p>Our 6 AI agents are analyzing your profile...</p>
              <p className="loading-sub">This takes 10-30 seconds for full analysis</p>
            </div>
          )}
        </form>

        {/* Example Profiles */}
        <div className="examples-section animate-fadeInUp stagger-2">
          <h3 className="heading-sm">Try an example:</h3>
          <div className="examples-grid">
            {EXAMPLE_PROFILES.map((ex, i) => (
              <button
                key={i}
                className="example-card glass-card"
                onClick={() => setText(ex)}
                disabled={loading}
              >
                <span className="example-num">#{i + 1}</span>
                <p>{ex.substring(0, 80)}...</p>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
