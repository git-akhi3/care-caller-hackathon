import { useState, useEffect } from 'react';
import { Phone } from 'lucide-react';
import StatsCard from '../components/StatsCard';
import CallCard from '../components/CallCard';
import Spinner from '../components/Spinner';
import { MOCK_CALLS, MOCK_STATS } from '../mockData';
import './Dashboard.css';

function RecentCalls() {
  const [stats, setStats] = useState(null);
  const [calls, setCalls] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    // Use mock data directly
    setStats(MOCK_STATS);
    setCalls(MOCK_CALLS);
    setLoading(false);
  }, []);

  if (loading) {
    return <Spinner />;
  }

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>Recent Calls</h1>
      </div>

      {/* Stats Bar */}
      <div className="stats-bar">
        <StatsCard
          icon={Phone}
          title="Total Calls"
          value={stats?.total_calls || 0}
        />
      </div>

      {/* Recent Calls */}
      <div className="dashboard-grid">
        <div className="dashboard-section">
          <div className="recent-calls">
            <h3 className="section-title">ALL RECENT CALLS</h3>
            <div className="calls-feed">
              {calls.length > 0 ? (
                calls.map((call) => (
                  <CallCard key={call.id} call={call} />
                ))
              ) : (
                <div className="empty-state">
                  <p>No calls yet. Trigger a call from n8n to see results.</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default RecentCalls;
