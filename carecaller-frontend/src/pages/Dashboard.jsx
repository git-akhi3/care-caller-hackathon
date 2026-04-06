import { useState, useEffect } from 'react';
import { Phone, AlertTriangle, Clock, DollarSign } from 'lucide-react';
import { API_BASE, API_ENDPOINTS } from '../constants';
import StatsCard from '../components/StatsCard';
import ContactsTable from '../components/ContactsTable';
import Spinner from '../components/Spinner';
import { MOCK_PATIENTS, MOCK_CALLS, MOCK_STATS } from '../mockData';
import './Dashboard.css';

function Dashboard() {
  const [stats, setStats] = useState(null);
  const [contacts, setContacts] = useState([]);
  const [calls, setCalls] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Load mock data on component mount
  // API calls and continuous refresh have been commented out
  useEffect(() => {
    setLoading(true);
    // Use mock data directly - no API calls
    setStats(MOCK_STATS);
    setContacts(MOCK_PATIENTS);
    setCalls(MOCK_CALLS);
    setLoading(false);

    // Commented out: API calls that were polling every 5 seconds
    // const fetchData = async () => {
    //   try {
    //     const [statsRes, contactsRes, callsRes] = await Promise.all([
    //       fetch(`${API_BASE}${API_ENDPOINTS.STATS}`),
    //       fetch(`${API_BASE}${API_ENDPOINTS.CONTACTS}`),
    //       fetch(`${API_BASE}${API_ENDPOINTS.CALLS}`),
    //     ]);
    //     // ... fetch logic ...
    //   } catch (err) {
    //     console.error('Error fetching data:', err);
    //   }
    // };
    // fetchData();
    // const interval = setInterval(fetchData, 5000);
    // return () => clearInterval(interval);
  }, []);

  if (loading) {
    return <Spinner />;
  }

  const escalationCount = calls.filter(c => c.outcome === 'escalated').length;

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>Dashboard</h1>
      </div>

      {/* Stats Bar */}
      <div className="stats-bar">
        <StatsCard
          icon={Phone}
          title="Total Calls"
          value={stats?.total_calls || 0}
        />
        <StatsCard
          icon={AlertTriangle}
          title="Escalations"
          value={escalationCount}
        />
        <StatsCard
          icon={Clock}
          title="Avg Duration"
          value={stats?.avg_duration || '0m 0s'}
        />
        <StatsCard
          icon={DollarSign}
          title="Total Cost"
          value={`$${(stats?.total_cost || 0).toFixed(2)}`}
        />
      </div>

      {/* Main Content - Patient Queue */}
      <div className="dashboard-grid">
        <div className="dashboard-section">
          <ContactsTable contacts={contacts} />
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
