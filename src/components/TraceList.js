import React from 'react';

// Helper function to format timestamp
const formatTimestamp = (timestamp) => {
  try {
    const date = new Date(timestamp);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: true
    });
  } catch (e) {
    return timestamp;
  }
};

// Helper function to format workflow ID
const formatWorkflowId = (id) => {
  if (!id) return '--';
  // If it's a long ID, show first and last parts
  if (id.length > 20) {
    return `${id.substring(0, 8)}...${id.substring(id.length - 4)}`;
  }
  return id;
};

// Helper function to get status color
const getStatusColor = (status) => {
  switch (status?.toLowerCase()) {
    case 'completed':
    case 'success':
      return 'bg-green-100 text-green-800';
    case 'failed':
    case 'error':
      return 'bg-red-100 text-red-800';
    case 'running':
      return 'bg-blue-100 text-blue-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
};

export default function TraceList({ traces, onSelect }) {
  if (!traces.length) return <p className="text-gray-500 text-center py-4">No traces found.</p>;
  
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Workflow
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Execution ID
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Timestamp
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Status
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Duration
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {traces.map((trace, idx) => (
            <tr 
              key={trace.workflow_id || trace.id || trace.trace_id || idx} 
              onClick={() => onSelect(trace)} 
              className="hover:bg-gray-50 cursor-pointer transition-colors"
            >
              <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                {trace.workflow_name || 'Unknown Workflow'}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 font-mono">
                {formatWorkflowId(trace.workflow_id || trace.id || trace.trace_id)}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {formatTimestamp(trace.timestamp)}
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                  getStatusColor(trace.status || (trace.error ? 'Error' : 'Success'))
                }`}>
                  {trace.status || (trace.error ? 'Error' : 'Success')}
                </span>
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                {trace.duration ? `${trace.duration.toFixed(2)}s` : '--'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
} 