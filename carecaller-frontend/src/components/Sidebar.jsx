import { useLocation, useNavigate } from 'react-router-dom';
import { Heart, Activity, Phone } from 'lucide-react';
import './Sidebar.css';

function Sidebar() {
  const location = useLocation();
  const navigate = useNavigate();

  const isActive = (path) => location.pathname === path;

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="logo">
          <Heart size={24} color="var(--accent-cyan)" />
          <span>CareCaller</span>
        </div>
      </div>

      <nav className="sidebar-nav">
        <button
          className={`nav-item ${isActive('/dashboard') ? 'active' : ''}`}
          onClick={() => navigate('/dashboard')}
        >
          <Activity size={18} />
          <span>Dashboard</span>
        </button>
        <button
          className={`nav-item ${isActive('/recent-calls') ? 'active' : ''}`}
          onClick={() => navigate('/recent-calls')}
        >
          <Phone size={18} />
          <span>Recent Calls</span>
        </button>
      </nav>

      <div className="sidebar-footer">
        <div className="status-indicator">
          <div className="pulse-dot"></div>
          <span>SYSTEM LIVE</span>
        </div>
      </div>
    </aside>
  );
}

export default Sidebar;
