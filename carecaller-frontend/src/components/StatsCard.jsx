import './StatsCard.css';

function StatsCard({ icon: Icon, title, value, unit = '' }) {
  return (
    <div className="stats-card">
      <div className="stats-header">
        <Icon size={20} className="stats-icon" />
      </div>
      <div className="stats-value">
        {value}
        {unit && <span className="stats-unit">{unit}</span>}
      </div>
      <div className="stats-label">{title}</div>
    </div>
  );
}

export default StatsCard;
