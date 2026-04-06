import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ChevronLeft, Sparkles, ChevronDown } from 'lucide-react';
import { API_BASE, API_ENDPOINTS } from '../constants';
import Spinner from '../components/Spinner';
import StatusBadge from '../components/StatusBadge';
import { MOCK_CALLS } from '../mockData';
import './CallDetail.css';

function CallDetail() {
  const { callId } = useParams();
  const navigate = useNavigate();
  const [call, setCall] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expandedTranscript, setExpandedTranscript] = useState(false);

  useEffect(() => {
    // Load call from mock data
    const callData = MOCK_CALLS.find(c => c.id === callId);
    if (callData) {
      setCall(callData);
      setError(null);
    } else {
      setError('Call not found in mock data');
    }
    setLoading(false);

    // Commented out: Original API fetch
    // const fetchCallDetail = async () => {
    //   try {
    //     setLoading(true);
    //     const response = await fetch(
    //       `${API_BASE}${API_ENDPOINTS.CALL_DETAIL(callId)}`
    //     );
    //     if (!response.ok) {
    //       throw new Error('Failed to fetch call details');
    //     }
    //     const data = await response.json();
    //     setCall(data);
    //     setError(null);
    //   } catch (err) {
    //     console.error('Error fetching call detail:', err);
    //     setError('Failed to load call details.');
    //   } finally {
    //     setLoading(false);
    //   }
    // };
    // fetchCallDetail();
  }, [callId]);

  if (loading) {
    return <Spinner />;
  }

  if (error && !call) {
    return (
      <div className="call-detail-error">
        <p>{error}</p>
        <button onClick={() => navigate('/dashboard')}>
          Back to Dashboard
        </button>
      </div>
    );
  }

  if (!call) {
    return (
      <div className="call-detail-error">
        <p>Call not found</p>
        <button onClick={() => navigate('/dashboard')}>
          Back to Dashboard
        </button>
      </div>
    );
  }

  const analysis = call.ai_analysis;
  const flagsData = {
    excessive_weight_loss: false,
    concerning_goal_weight: false,
    new_medications_reported: false,
    surgery_reported: false,
    escalation_needed: false,
    stt_issues_detected: false,
  };

  const getQualityScoreColor = (score) => {
    if (score >= 80) return 'var(--accent-green)';
    if (score >= 50) return 'var(--accent-amber)';
    return 'var(--accent-red)';
  };

  const getRecommendationStyle = (action) => {
    const styles = {
      routine_refill: {
        icon: '✓',
        text: 'ROUTINE REFILL APPROVED',
        color: 'green',
      },
      needs_doctor_review: {
        icon: '⚠',
        text: 'DOCTOR REVIEW REQUIRED',
        color: 'amber',
      },
      urgent_escalation: {
        icon: '🚨',
        text: 'URGENT ESCALATION',
        color: 'red',
      },
      follow_up_required: {
        icon: '↻',
        text: 'FOLLOW-UP REQUIRED',
        color: 'cyan',
      },
    };
    return styles[action] || styles.routine_refill;
  };

  const recommendedAction = getRecommendationStyle(
    analysis?.recommended_action || 'routine_refill'
  );

  return (
    <div className="call-detail">
      <div className="call-detail-header">
        <button className="back-btn" onClick={() => navigate('/dashboard')}>
          ← BACK TO DASHBOARD
        </button>
        <div className="header-content">
          <h1>{call.patient_name}</h1>
          <StatusBadge status={call.outcome} />
        </div>
        <div className="header-metadata">
          <div className="metadata-item">
            <span className="label">Duration</span>
            <span className="value">{call.duration || 'N/A'}</span>
          </div>
          <div className="metadata-item">
            <span className="label">Cost</span>
            <span className="value">${call.cost?.toFixed(2) || '0.00'}</span>
          </div>
          <div className="metadata-item">
            <span className="label">Timestamp</span>
            <span className="value">
              {new Date(call.timestamp).toLocaleString()}
            </span>
          </div>
          <div className="metadata-item">
            <span className="label">Medication</span>
            <span className="value">
              {call.medication} {call.dosage ? `- ${call.dosage}` : ''}
            </span>
          </div>
        </div>
      </div>

      {/* AI Analysis Panel */}
      <div className="analysis-panel">
        <div className="analysis-header">
          <Sparkles size={18} />
          <span>AI CLINICAL ANALYSIS</span>
          <span className="powered-by">Powered by Claude</span>
        </div>

        {analysis ? (
          <>
            <div className="clinical-summary">
              <p>{analysis.clinical_summary || 'No summary available.'}</p>
            </div>

            <div className={`recommendation-banner recommendation-${recommendedAction.color}`}>
              <span className="recommendation-icon">
                {recommendedAction.icon}
              </span>
              <span className="recommendation-text">
                {recommendedAction.text}
              </span>
            </div>
          </>
        ) : (
          <div className="loading-analysis">
            <p>⟳ AI Analysis Processing...</p>
          </div>
        )}
      </div>

      {/* Quality Score + Flags Row */}
      <div className="quality-flags-row">
        <div className="quality-score-section">
          <div className="quality-number" style={{ color: getQualityScoreColor(analysis?.quality_score || 0) }}>
            {analysis?.quality_score || 0}
          </div>
          <div className="quality-label">CALL QUALITY SCORE</div>

          <div className="quality-metrics">
            <div className="metric-bar">
              <span className="metric-name">Response Completeness</span>
              <div className="bar-container">
                <div
                  className="bar-fill"
                  style={{
                    width: `${analysis?.response_completeness || 0}%`,
                    backgroundColor:
                      analysis?.response_completeness >= 80
                        ? 'var(--accent-green)'
                        : analysis?.response_completeness >= 50
                        ? 'var(--accent-amber)'
                        : 'var(--accent-red)',
                  }}
                ></div>
              </div>
              <span className="metric-value">
                {analysis?.response_completeness || 0}%
              </span>
            </div>

            <div className="metric-bar">
              <span className="metric-name">Conversation Flow</span>
              <div className="bar-container">
                <div
                  className="bar-fill"
                  style={{
                    width: `${analysis?.conversation_flow || 0}%`,
                    backgroundColor:
                      analysis?.conversation_flow >= 80
                        ? 'var(--accent-green)'
                        : analysis?.conversation_flow >= 50
                        ? 'var(--accent-amber)'
                        : 'var(--accent-red)',
                  }}
                ></div>
              </div>
              <span className="metric-value">
                {analysis?.conversation_flow || 0}%
              </span>
            </div>

            <div className="metric-bar">
              <span className="metric-name">Data Accuracy</span>
              <div className="bar-container">
                <div
                  className="bar-fill"
                  style={{
                    width: `${analysis?.data_accuracy || 0}%`,
                    backgroundColor:
                      analysis?.data_accuracy >= 80
                        ? 'var(--accent-green)'
                        : analysis?.data_accuracy >= 50
                        ? 'var(--accent-amber)'
                        : 'var(--accent-red)',
                  }}
                ></div>
              </div>
              <span className="metric-value">
                {analysis?.data_accuracy || 0}%
              </span>
            </div>

            <div className="metric-bar">
              <span className="metric-name">Guardrail Compliance</span>
              <div className="bar-container">
                <div
                  className="bar-fill"
                  style={{
                    width: `${analysis?.guardrail_compliance || 0}%`,
                    backgroundColor:
                      analysis?.guardrail_compliance >= 80
                        ? 'var(--accent-green)'
                        : analysis?.guardrail_compliance >= 50
                        ? 'var(--accent-amber)'
                        : 'var(--accent-red)',
                  }}
                ></div>
              </div>
              <span className="metric-value">
                {analysis?.guardrail_compliance || 0}%
              </span>
            </div>
          </div>
        </div>

        <div className="flags-section">
          <div className="flags-title">DETECTED FLAGS</div>
          <div className="flags-grid">
            {Object.entries(flagsData).map(([key, value]) => (
              <div key={key} className={`flag-pill ${value ? 'flag-true' : 'flag-false'}`}>
                <span className="flag-name">
                  {key.replace(/_/g, ' ').toUpperCase()}
                </span>
                <span className="flag-value">{value ? 'TRUE' : 'FALSE'}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Q&A Responses Grid */}
      {call.health_questionnaire && (
        <div className="qa-responses">
          <h3 className="qa-title">HEALTH QUESTIONNAIRE RESPONSES</h3>
          <div className="qa-grid">
            {Object.entries(call.health_questionnaire).map(([question, answer], index) => {
              const qNum = index + 1;
              let borderClass = '';
              
              if (
                (qNum === 5 && answer && answer !== 'none' && answer !== 'no') ||
                (qNum === 9 && answer) ||
                (qNum === 12 && answer) ||
                (qNum === 6 && answer === 'not satisfied') ||
                (qNum === 14 && answer === 'yes')
              ) {
                borderClass = 'highlight';
              }

              return (
                <div key={qNum} className={`qa-card ${borderClass}`}>
                  <div className="qa-question-num">Q{qNum}</div>
                  <div className="qa-question">{question}</div>
                  <div className="qa-answer">{answer || 'N/A'}</div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Transcript Viewer */}
      {call.transcript && (
        <div className="transcript-section">
          <button
            className="transcript-header"
            onClick={() => setExpandedTranscript(!expandedTranscript)}
          >
            <span>FULL TRANSCRIPT</span>
            <ChevronDown
              size={18}
              style={{
                transform: expandedTranscript ? 'rotate(180deg)' : 'rotate(0deg)',
                transition: 'transform 200ms ease',
              }}
            />
          </button>

          {expandedTranscript && (
            <div className="transcript-viewer">
              {call.transcript.map((turn, index) => (
                <div key={index} className={`transcript-turn turn-${turn.role}`}>
                  <div className="turn-label">{turn.role.toUpperCase()}</div>
                  <div className="turn-text">{turn.text}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default CallDetail;
