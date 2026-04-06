import { useNavigate } from 'react-router-dom';
import './CallCard.css';

function CallCard({ call }) {
  const navigate = useNavigate();

  const getOutcomeBadgeColor = (outcome) => {
    const colors = {
      completed: '#00FF88',
      failed: '#FF4560',
      escalated: '#FF4560',
      pending: '#FFB347',
    };
    return colors[outcome] || '#00D4FF';
  };

  const getQualityScoreColor = (score) => {
    if (score >= 80) return '#00FF88';
    if (score >= 50) return '#FFB347';
    return '#FF4560';
  };

  const needsAttention = call.needs_attention || false;
  const hasAnalysis = call.ai_analysis !== null && call.ai_analysis !== undefined;
  const quality = call.ai_analysis?.quality_score || 0;

  return (
    <div
      className={`call-card ${needsAttention ? 'needs-attention' : ''}`}
      onClick={() => navigate(`/calls/${call.id}`)}
    >
      <div
        className="outcome-badge"
        style={{ backgroundColor: getOutcomeBadgeColor(call.outcome) }}
      >
        <span>{call.outcome.toUpperCase()}</span>
      </div>

      <div className="call-main">
        <div className="call-header">
          <div className="call-info">
            <div className="call-patient">
              <strong>{call.patient_name}</strong>
              <span className="call-phone">{call.phone}</span>
            </div>
            <div className="call-details">
              {call.medication && (
                <span className="detail-item">{call.medication}</span>
              )}
              {call.dosage && <span className="detail-item">{call.dosage}</span>}
            </div>
          </div>

          <div className="call-metrics">
            <div className="metric">
              <span className="metric-label">Duration</span>
              <span className="metric-value">{call.duration || 'N/A'}</span>
            </div>
            <div className="metric">
              <span className="metric-label">Cost</span>
              <span className="metric-value">${call.cost?.toFixed(2) || '0.00'}</span>
            </div>
            {hasAnalysis && (
              <div className="metric">
                <div
                  className="quality-score-circle"
                  style={{ color: getQualityScoreColor(quality) }}
                >
                  {quality}
                </div>
              </div>
            )}
          </div>

          <button className="view-analysis-btn">VIEW ANALYSIS →</button>
        </div>
      </div>
    </div>
  );
}

export default CallCard;
