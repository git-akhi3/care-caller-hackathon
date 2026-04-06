import { Circle } from 'lucide-react';
import './StatusBadge.css';

function StatusBadge({ status }) {
  const statusConfig = {
    pending: { label: 'PENDING', color: 'pending', icon: 'gray' },
    in_progress: { label: 'IN CALL', color: 'in_progress', icon: 'cyan' },
    completed: { label: 'COMPLETED', color: 'completed', icon: 'green' },
    escalated: { label: 'ESCALATED', color: 'escalated', icon: 'red' },
    opted_out: { label: 'OPTED OUT', color: 'opted_out', icon: 'gray' },
  };

  const config = statusConfig[status] || statusConfig.pending;

  return (
    <div className={`status-badge status-${config.color}`}>
      <Circle size={8} className={`status-dot status-${config.color}`} />
      <span>{config.label}</span>
    </div>
  );
}

export default StatusBadge;
