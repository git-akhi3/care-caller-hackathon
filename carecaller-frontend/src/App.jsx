import { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { API_BASE, API_ENDPOINTS } from './constants';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import RecentCalls from './pages/RecentCalls';
import CallDetail from './pages/CallDetail';
import './App.css';

function App() {
  useEffect(() => {
    // Seed demo data on first load
    const seedDemoData = async () => {
      try {
        await fetch(`${API_BASE}${API_ENDPOINTS.DEMO_SEED}`, {
          method: 'POST',
        });
      } catch (error) {
        console.log('Demo seed endpoint not available - proceeding with normal flow');
      }
    };

    seedDemoData();
  }, []);

  return (
    <Router>
      <div className="app-container">
        <Sidebar />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/recent-calls" element={<RecentCalls />} />
            <Route path="/calls/:callId" element={<CallDetail />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;



