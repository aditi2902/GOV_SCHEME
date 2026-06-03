import './ReadinessGauge.css';

export default function ReadinessGauge({ score, label = 'Readiness Score' }) {
  const radius = 70;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;

  const getColor = (s) => {
    if (s >= 80) return '#00D4AA';
    if (s >= 50) return '#FFB347';
    return '#FF6B6B';
  };

  const color = getColor(score);

  return (
    <div className="gauge-container">
      <svg className="gauge-svg" viewBox="0 0 180 180">
        {/* Background glow */}
        <defs>
          <filter id="glow">
            <feGaussianBlur stdDeviation="4" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Track */}
        <circle
          cx="90" cy="90" r={radius}
          fill="none"
          stroke="rgba(148, 163, 184, 0.1)"
          strokeWidth="10"
        />

        {/* Filled arc */}
        <circle
          cx="90" cy="90" r={radius}
          fill="none"
          stroke={color}
          strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          transform="rotate(-90 90 90)"
          filter="url(#glow)"
          className="gauge-fill"
        />
      </svg>

      <div className="gauge-center">
        <span className="gauge-value" style={{ color }}>{Math.round(score)}%</span>
        <span className="gauge-label">{label}</span>
      </div>
    </div>
  );
}
