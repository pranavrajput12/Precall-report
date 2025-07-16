import React from 'react';

export default function TraceDetailModal({ trace, onClose }) {
  return (
    <div className="trace-detail-modal">
      <div className="modal-content">
        <button className="close-btn" onClick={onClose}>Close</button>
        <h3>Trace Details</h3>
        <pre>{JSON.stringify(trace, null, 2)}</pre>
      </div>
    </div>
  );
} 