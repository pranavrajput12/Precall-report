import React from 'react';

export default function TraceList({ traces, onSelect }) {
  if (!traces.length) return <p>No traces found.</p>;
  return (
    <table className="trace-list-table">
      <thead>
        <tr>
          <th>Trace ID</th>
          <th>Timestamp</th>
          <th>Status</th>
          <th>Duration (s)</th>
        </tr>
      </thead>
      <tbody>
        {traces.map((trace) => (
          <tr key={trace.id || trace.trace_id} onClick={() => onSelect(trace)} style={{ cursor: 'pointer' }}>
            <td>{trace.id || trace.trace_id}</td>
            <td>{trace.timestamp}</td>
            <td>{trace.status || (trace.error ? 'Error' : 'Success')}</td>
            <td>{trace.duration ? trace.duration.toFixed(2) : '--'}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
} 