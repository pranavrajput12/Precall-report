import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Activity, AlertCircle, CheckCircle, Clock, Zap, Database, RefreshCw } from 'lucide-react';
import TraceList from '../components/TraceList';
import TraceDetailModal from '../components/TraceDetailModal';
import MetricCard from '../components/MetricCard';

const fetchTraces = async () => {
  const res = await fetch('/api/observability/traces');
  if (!res.ok) throw new Error('Failed to fetch traces');
  return res.json();
};

const fetchMetrics = async () => {
  const res = await fetch('/api/observability/metrics');
  if (!res.ok) throw new Error('Failed to fetch metrics');
  return res.json();
};

const fetchHealth = async () => {
  const res = await fetch('/api/system/health');
  if (!res.ok) throw new Error('Failed to fetch health');
  return res.json();
};

export default function ObservabilityDashboard() {
  const { data: traces = {}, isLoading: tracesLoading } = useQuery({ 
    queryKey: ['traces'], 
    queryFn: fetchTraces,
    refetchInterval: 5000
  });
  
  const { data: metrics = {}, isLoading: metricsLoading } = useQuery({ 
    queryKey: ['metrics'], 
    queryFn: fetchMetrics,
    refetchInterval: 5000
  });
  
  const { data: health = {}, isLoading: healthLoading } = useQuery({ 
    queryKey: ['health'], 
    queryFn: fetchHealth,
    refetchInterval: 5000
  });
  
  const [selectedTrace, setSelectedTrace] = useState(null);

  if (tracesLoading || metricsLoading || healthLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <RefreshCw className="w-8 h-8 animate-spin text-blue-600 mx-auto mb-2" />
          <p className="text-gray-600">Loading observability data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Observability & Traceability</h1>
        <p className="text-gray-600">Monitor system performance and trace workflow executions</p>
      </div>

      {/* Metrics Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <Activity className="w-8 h-8 text-blue-500 mr-3" />
            <div>
              <p className="text-sm font-medium text-gray-600">Total Traces</p>
              <p className="text-2xl font-bold text-gray-900">{metrics.traces?.total_traces || 0}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <AlertCircle className="w-8 h-8 text-red-500 mr-3" />
            <div>
              <p className="text-sm font-medium text-gray-600">Errors</p>
              <p className="text-2xl font-bold text-gray-900">{metrics.traces?.errors || 0}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <Clock className="w-8 h-8 text-green-500 mr-3" />
            <div>
              <p className="text-sm font-medium text-gray-600">Avg Exec Time</p>
              <p className="text-2xl font-bold text-gray-900">
                {metrics.traces?.avg_execution_time ? `${metrics.traces.avg_execution_time.toFixed(2)}s` : '--'}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <CheckCircle className="w-8 h-8 text-green-500 mr-3" />
            <div>
              <p className="text-sm font-medium text-gray-600">System Health</p>
              <p className="text-2xl font-bold text-green-600">
                {health.performance?.monitoring_active ? 'Healthy' : 'Degraded'}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* System Health Panel */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">System Health</h3>
        </div>
        <div className="p-6">
          {health.system_metrics ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center">
                  <Database className="w-5 h-5 text-blue-500 mr-2" />
                  <span className="text-sm font-medium text-gray-700">CPU Usage</span>
                </div>
                <span className="text-lg font-semibold text-gray-900">{health.system_metrics.cpu_usage}%</span>
              </div>
              
              <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center">
                  <Zap className="w-5 h-5 text-green-500 mr-2" />
                  <span className="text-sm font-medium text-gray-700">Memory Usage</span>
                </div>
                <span className="text-lg font-semibold text-gray-900">{health.system_metrics.memory_usage}%</span>
              </div>
              
              <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center">
                  <Activity className="w-5 h-5 text-purple-500 mr-2" />
                  <span className="text-sm font-medium text-gray-700">Active Connections</span>
                </div>
                <span className="text-lg font-semibold text-gray-900">{health.system_metrics.active_connections}</span>
              </div>
              
              <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center">
                  <Clock className="w-5 h-5 text-orange-500 mr-2" />
                  <span className="text-sm font-medium text-gray-700">Uptime</span>
                </div>
                <span className="text-lg font-semibold text-gray-900">{health.system_metrics.uptime}</span>
              </div>
              
              <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center">
                  <AlertCircle className="w-5 h-5 text-red-500 mr-2" />
                  <span className="text-sm font-medium text-gray-700">Network Latency</span>
                </div>
                <span className="text-lg font-semibold text-gray-900">{health.system_metrics.network_latency}ms</span>
              </div>
              
              <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center">
                  <Database className="w-5 h-5 text-indigo-500 mr-2" />
                  <span className="text-sm font-medium text-gray-700">Disk Usage</span>
                </div>
                <span className="text-lg font-semibold text-gray-900">{health.system_metrics.disk_usage}%</span>
              </div>
            </div>
          ) : (
            <div className="text-center py-8">
              <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
              <p className="text-gray-600">System health data unavailable</p>
            </div>
          )}
        </div>
      </div>

      {/* Trace List Section */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Recent Traces</h3>
        </div>
        <div className="p-6">
          {traces.recent_traces && traces.recent_traces.length > 0 ? (
            <TraceList traces={traces.recent_traces} onSelect={setSelectedTrace} />
          ) : (
            <div className="text-center py-8">
              <Activity className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600">No traces available</p>
            </div>
          )}
        </div>
      </div>

      {/* Trace Detail Modal */}
      {selectedTrace && (
        <TraceDetailModal trace={selectedTrace} onClose={() => setSelectedTrace(null)} />
      )}
    </div>
  );
} 