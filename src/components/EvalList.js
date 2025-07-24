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

// Helper function to format score
const formatScore = (score) => {
  if (typeof score === 'number') {
    return score.toFixed(2);
  }
  return score;
};

// Helper function to format confidence
const formatConfidence = (confidence) => {
  if (typeof confidence === 'number') {
    return `${(confidence * 100).toFixed(0)}%`;
  }
  return confidence;
};

export default function EvalList({ evals, onSelect }) {
  if (!evals.length) return <p className="text-gray-500 text-center py-4">No evaluations found.</p>;
  
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Metric
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Score
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Confidence
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Evaluator
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Timestamp
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {evals.map((ev, idx) => (
            <tr 
              key={idx} 
              onClick={() => onSelect(ev)} 
              className="hover:bg-gray-50 cursor-pointer transition-colors"
            >
              <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 capitalize">
                {ev.metric}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                  ev.score === 0 ? 'bg-red-100 text-red-800' : 
                  ev.score >= 0.8 ? 'bg-green-100 text-green-800' : 
                  'bg-yellow-100 text-yellow-800'
                }`}>
                  {formatScore(ev.score)}
                </span>
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                {formatConfidence(ev.confidence)}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                {ev.evaluator}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {formatTimestamp(ev.timestamp)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
} 