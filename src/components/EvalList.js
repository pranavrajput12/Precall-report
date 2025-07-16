import React from 'react';

export default function EvalList({ evals, onSelect }) {
  if (!evals.length) return <p>No evaluations found.</p>;
  return (
    <table className="eval-list-table">
      <thead>
        <tr>
          <th>Metric</th>
          <th>Score</th>
          <th>Confidence</th>
          <th>Evaluator</th>
          <th>Timestamp</th>
        </tr>
      </thead>
      <tbody>
        {evals.map((ev, idx) => (
          <tr key={idx} onClick={() => onSelect(ev)} style={{ cursor: 'pointer' }}>
            <td>{ev.metric}</td>
            <td>{ev.score}</td>
            <td>{ev.confidence}</td>
            <td>{ev.evaluator}</td>
            <td>{ev.timestamp}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
} 