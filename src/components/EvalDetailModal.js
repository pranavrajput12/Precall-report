import React from 'react';

export default function EvalDetailModal({ evalResult, onClose }) {
  return (
    <div className="eval-detail-modal">
      <div className="modal-content">
        <button className="close-btn" onClick={onClose}>Close</button>
        <h3>Evaluation Details</h3>
        <pre>{JSON.stringify(evalResult, null, 2)}</pre>
      </div>
    </div>
  );
} 