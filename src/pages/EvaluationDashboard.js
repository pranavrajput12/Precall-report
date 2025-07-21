import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { BarChart3, TrendingUp, Clock, CheckCircle, AlertCircle, RefreshCw } from 'lucide-react';
import EvalList from '../components/EvalList';
import EvalDetailModal from '../components/EvalDetailModal';
import MetricCard from '../components/MetricCard';

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
  
  const [selectedEval, setSelectedEval] = useState(null);

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
              <p className="text-sm font-medium text-gray-600">Avg Score</p>
              <p className="text-2xl font-bold text-gray-900">
                {summary.average_score ? summary.average_score.toFixed(2) : '--'}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <Clock className="w-8 h-8 text-orange-500 mr-3" />
            <div>
              <p className="text-sm font-medium text-gray-600">Avg Exec Time</p>
              <p className="text-2xl font-bold text-gray-900">
                {summary.average_execution_time ? `${summary.average_execution_time.toFixed(2)}s` : '--'}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <CheckCircle className="w-8 h-8 text-green-500 mr-3" />
            <div>
              <p className="text-sm font-medium text-gray-600">Pass Rate</p>
              <p className="text-2xl font-bold text-green-600">
                {summary.success_rate ? `${(summary.success_rate * 100).toFixed(1)}%` : '--'}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Metric Breakdown */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Metric Breakdown</h3>
        </div>
        <div className="p-6">
          {summary.metric_statistics ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {Object.entries(summary.metric_statistics).map(([metric, stats]) => (
                <div key={metric} className="p-4 bg-gray-50 rounded-lg">
                  <h4 className="font-medium text-gray-900 mb-2 capitalize">
                    {metric.replace('_', ' ')}
                  </h4>
                  <div className="space-y-1">
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Average:</span>
                      <span className="text-sm font-medium text-gray-900">{stats.avg.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Min:</span>
                      <span className="text-sm font-medium text-gray-900">{stats.min.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Max:</span>
                      <span className="text-sm font-medium text-gray-900">{stats.max.toFixed(2)}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <AlertCircle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600">No metric statistics available</p>
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
          {summary.recent_results && summary.recent_results.length > 0 ? (
            <EvalList evals={summary.recent_results} onSelect={setSelectedEval} />
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

      {/* Evaluation Detail Modal */}
      {selectedEval && (
        <EvalDetailModal evalResult={selectedEval} onClose={() => setSelectedEval(null)} />
      )}
    </div>
  );
} 