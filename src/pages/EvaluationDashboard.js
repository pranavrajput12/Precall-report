import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { BarChart3, TrendingUp, Clock, CheckCircle, AlertCircle, RefreshCw } from 'lucide-react';

const fetchSummary = async () => {
  const res = await fetch('/api/evaluation/summary');
  if (!res.ok) throw new Error('Failed to fetch summary');
  return res.json();
};

const fetchMetrics = async () => {
  const res = await fetch('/api/evaluation/metrics');
  if (!res.ok) throw new Error('Failed to fetch metrics');
  return res.json();
};

export default function EvaluationDashboard() {
  const { data: summary = {}, isLoading: summaryLoading } = useQuery({ 
    queryKey: ['eval-summary'], 
    queryFn: fetchSummary,
    refetchInterval: 30000
  });
  
  const { data: metrics = {}, isLoading: metricsLoading } = useQuery({ 
    queryKey: ['eval-metrics'], 
    queryFn: fetchMetrics,
    refetchInterval: 30000
  });
  

  if (summaryLoading || metricsLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <RefreshCw className="w-8 h-8 animate-spin text-blue-600 mx-auto mb-2" />
          <p className="text-gray-600">Loading evaluation data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">LLM Evaluation Dashboard</h1>
        <p className="text-gray-600">Monitor and analyze LLM performance across different metrics</p>
      </div>

      {/* Metrics Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <BarChart3 className="w-8 h-8 text-blue-500 mr-3" />
            <div>
              <p className="text-sm font-medium text-gray-600">Total Evaluations</p>
              <p className="text-2xl font-bold text-gray-900">{summary.total_evaluations || 0}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <TrendingUp className="w-8 h-8 text-green-500 mr-3" />
            <div>
              <p className="text-sm font-medium text-gray-600">Avg Quality Score</p>
              <p className="text-2xl font-bold text-gray-900">
                {summary.average_quality_score ? summary.average_quality_score.toFixed(1) : '--'}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <Clock className="w-8 h-8 text-orange-500 mr-3" />
            <div>
              <p className="text-sm font-medium text-gray-600">Avg Response Rate</p>
              <p className="text-2xl font-bold text-gray-900">
                {summary.average_response_rate ? `${summary.average_response_rate.toFixed(1)}%` : '--'}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <CheckCircle className="w-8 h-8 text-green-500 mr-3" />
            <div>
              <p className="text-sm font-medium text-gray-600">Success Rate</p>
              <p className="text-2xl font-bold text-green-600">
                {summary.by_status && summary.total_evaluations ? 
                  `${((summary.by_status.success / summary.total_evaluations) * 100).toFixed(1)}%` : '--'}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Status Breakdown */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Status Breakdown</h3>
        </div>
        <div className="p-6">
          {summary.by_status ? (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="p-4 bg-green-50 rounded-lg">
                <h4 className="font-medium text-green-900 mb-2">Success</h4>
                <p className="text-3xl font-bold text-green-600">{summary.by_status.success || 0}</p>
                <p className="text-sm text-green-700 mt-1">Completed workflows</p>
              </div>
              <div className="p-4 bg-red-50 rounded-lg">
                <h4 className="font-medium text-red-900 mb-2">Failed</h4>
                <p className="text-3xl font-bold text-red-600">{summary.by_status.failed || 0}</p>
                <p className="text-sm text-red-700 mt-1">Failed workflows</p>
              </div>
              <div className="p-4 bg-yellow-50 rounded-lg">
                <h4 className="font-medium text-yellow-900 mb-2">Running</h4>
                <p className="text-3xl font-bold text-yellow-600">{summary.by_status.running || 0}</p>
                <p className="text-sm text-yellow-700 mt-1">In-progress workflows</p>
              </div>
            </div>
          ) : metrics.metric_distribution ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {Object.entries(metrics.metric_distribution).map(([channel, count]) => (
                <div key={channel} className="p-4 bg-gray-50 rounded-lg">
                  <h4 className="font-medium text-gray-900 mb-2 capitalize">{channel}</h4>
                  <p className="text-2xl font-bold text-gray-600">{count}</p>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <AlertCircle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600">No status breakdown available</p>
            </div>
          )}
        </div>
      </div>

      {/* Recent Evaluations */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Recent Evaluations</h3>
        </div>
        <div className="p-6">
          {summary.recent_evaluations && summary.recent_evaluations.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Execution ID
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Quality Score
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Response Rate
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Time
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {summary.recent_evaluations.map((evaluation, index) => (
                    <tr key={evaluation.execution_id || index} className="hover:bg-gray-50 cursor-pointer">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {evaluation.execution_id ? evaluation.execution_id.substring(0, 8) : '--'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        <span className={`font-medium ${evaluation.quality_score >= 80 ? 'text-green-600' : evaluation.quality_score >= 60 ? 'text-yellow-600' : 'text-red-600'}`}>
                          {evaluation.quality_score ? evaluation.quality_score.toFixed(1) : '--'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {evaluation.predicted_response_rate ? `${evaluation.predicted_response_rate.toFixed(1)}%` : '--'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                          evaluation.status === 'completed' ? 'bg-green-100 text-green-800' :
                          evaluation.status === 'failed' ? 'bg-red-100 text-red-800' :
                          'bg-yellow-100 text-yellow-800'
                        }`}>
                          {evaluation.status || 'unknown'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {evaluation.timestamp ? new Date(evaluation.timestamp).toLocaleString() : '--'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center py-8">
              <BarChart3 className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600">No recent evaluations available</p>
            </div>
          )}
        </div>
      </div>

      {/* Performance Trends */}
      {metrics.recent_trends && (
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">Performance Trends</h3>
          </div>
          <div className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-medium text-gray-900 mb-4">Recent Trend</h4>
                <div className="space-y-2">
                  {metrics.recent_trends.map((trend, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <span className="text-sm text-gray-600">{trend.date}</span>
                      <div className="flex items-center">
                        <span className="text-sm font-medium text-gray-900 mr-2">{trend.score.toFixed(2)}</span>
                        {index > 0 && (
                          <span className={`text-xs px-2 py-1 rounded-full ${
                            trend.score > metrics.recent_trends[index - 1].score
                              ? 'bg-green-100 text-green-800'
                              : 'bg-red-100 text-red-800'
                          }`}>
                            {trend.score > metrics.recent_trends[index - 1].score ? '↑' : '↓'}
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              
              <div>
                <h4 className="font-medium text-gray-900 mb-4">Overall Performance</h4>
                <div className="space-y-3">
                  <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <span className="text-sm text-gray-600">Improvement Trend</span>
                    <span className={`text-sm font-medium ${
                      metrics.overall_performance?.improvement_trend > 0 ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {metrics.overall_performance?.improvement_trend > 0 ? '+' : ''}
                      {(metrics.overall_performance?.improvement_trend * 100).toFixed(1)}%
                    </span>
                  </div>
                  
                  <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <span className="text-sm text-gray-600">Success Rate</span>
                    <span className="text-sm font-medium text-gray-900">
                      {(metrics.overall_performance?.success_rate * 100).toFixed(1)}%
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
} 