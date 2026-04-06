import { useNavigate } from 'react-router-dom';
import StatusBadge from './StatusBadge';
import { MOCK_CALLS } from '../mockData';
import './ContactsTable.css';

function ContactsTable({ contacts }) {
  const navigate = useNavigate();

  const handleViewClick = (contactName) => {
    // Find the most recent call for this patient
    const patientCall = MOCK_CALLS.find(call => call.patient_name === contactName);
    if (patientCall) {
      navigate(`/calls/${patientCall.id}`);
    }
  };

  if (!contacts || contacts.length === 0) {
    return (
      <div className="contacts-table-empty">
        <p>No contacts available</p>
      </div>
    );
  }

  return (
    <div className="contacts-table-container">
      <h3 className="table-title">PATIENT QUEUE</h3>
      <div className="contacts-table">
        <table>
          <thead>
            <tr>
              <th>Patient Name</th>
              <th>Medication</th>
              <th>Phone</th>
              <th>Status</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {contacts.map((contact, index) => (
              <tr key={contact.id} style={{ animationDelay: `${index * 50}ms` }}>
                <td className="cell-name">{contact.name}</td>
                <td className="cell-text">{contact.medication || 'N/A'}</td>
                <td className="cell-text">{contact.phone}</td>
                <td className="cell-status">
                  <StatusBadge status={contact.status} />
                </td>
                <td className="cell-action">
                  <button 
                    className="action-btn"
                    onClick={() => handleViewClick(contact.name)}
                  >
                    View
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default ContactsTable;
