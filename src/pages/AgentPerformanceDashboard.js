import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { 
  Activity, 
  Clock, 
  CheckCircle, 
  AlertCircle, 
  TrendingUp,
  TrendingDown,
  BarChart3,
  Zap,
  Brain,
  Target,
  Award,
  Loader2,
  RefreshCw,
  Filter
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell } from 'recharts';

const AgentPerformanceDashboard = () => {
  const [selectedAgent, setSelectedAgent] = useState('all');
  const [timeRange, setTimeRange] = useState('7'); // days
  const [selectedMetric, setSelectedMetric] = useState('success_rate');

  // Fetch performance summary
  const { data: summary = {}, isLoading: summaryLoading, refetch: refetchSummary } = useQuery({
    queryKey: ['agent-performance-summary'],
    queryFn: async () => {
      try {
        const response = await fetch('/api/agent-performance/summary');
        if (!response.ok) {
          // Return default empty structure for 404s or API not available
          return {
            best_performers: [],
            model_usage: {},
            quality_scores: {},
            total_executions: 0,
            success_rate: 0,
            average_quality: 0
          };
        }
        return await response.json();
      } catch (error) {
        // Return default structure on network errors
        return {
          best_performers: [],
          model_usage: {},
          quality_scores: {},
          total_executions: 0,
          success_rate: 0,
          average_quality: 0
        };
      }
    },
    refetchInterval: 30000, // Refresh every 30 seconds
    retry: false, // Don't retry since API might not be implemented yet
  });

  // Fetch agent-specific metrics
  const { data: agentMetrics = {}, isLoading: metricsLoading } = useQuery({
    queryKey: ['agent-performance-metrics', selectedAgent],
    queryFn: async () => {
      if (selectedAgent === 'all') return {};
      try {
        const response = await fetch(`/api/agent-performance/metrics/${selectedAgent}`);
        if (!response.ok) return {};
        return await response.json();
      } catch (error) {
        return {};
      }
    },
    enabled: selectedAgent !== 'all',
    retry: false,
  });

  const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#06B6D4'];

  // Prepare chart data
  const getPerformanceTrendData = () => {
    if (!summary.best_performers) return [];
    
    return summary.best_performers.slice(0, 10).map((performer, index) => ({
      name: `${performer.agent_id}/${performer.model_name}`,
      success_rate: (performer.success_rate * 100).toFixed(1),
      avg_quality: performer.avg_quality || 0,
      executions: performer.executions,
    }));
  };

  const getModelDistributionData = () => {
    if (!summary.best_performers) return [];
    
    const modelCounts = {};
    summary.best_performers.forEach(performer => {
      const model = performer.model_name;
      modelCounts[model] = (modelCounts[model] || 0) + performer.executions;
    });
    
    return Object.entries(modelCounts).map(([model, count]) => ({
      name: model,
      value: count,
    }));
  };

  const getQualityDistributionData = () => {
    if (!summary.best_performers) return [];
    
    const qualityRanges = {
      'Excellent (90-100)': 0,
      'Good (80-89)': 0,
      'Average (70-79)': 0,
      'Poor (<70)': 0,
    };
    
    summary.best_performers.forEach(performer => {
      const quality = performer.avg_quality || 0;
      if (quality >= 90) qualityRanges['Excellent (90-100)']++;
      else if (quality >= 80) qualityRanges['Good (80-89)']++;
      else if (quality >= 70) qualityRanges['Average (70-79)']++;
      else qualityRanges['Poor (<70)']++;
    });
    
    return Object.entries(qualityRanges).map(([range, count]) => ({
      name: range,
      value: count,
    }));
  };

  const formatPercentage = (value) => `${(value * 100).toFixed(1)}%`;
  const formatDuration = (seconds) => {
    if (!seconds) return 'N/A';
    return `${seconds.toFixed(1)}s`;
  };

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Agent Performance Dashboard</h1>
              <p className="text-gray-600 mt-2">
                Monitor agent performance, model selection, and execution metrics
              </p>
            </div>
            <div className="flex items-center gap-4">
              <select
                value={timeRange}
                onChange={(e) => setTimeRange(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="1">Last 24 hours</option>
                <option value="7">Last 7 days</option>
                <option value="30">Last 30 days</option>
                <option value="90">Last 90 days</option>
              </select>
              <button
                onClick={() => refetchSummary()}
                className="p-2 text-gray-600 hover:text-gray-800 border border-gray-300 rounded-md hover:bg-gray-50"
              >
                <RefreshCw className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>

        {/* Overview Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Agents</p>
                <p className="text-2xl font-bold text-gray-900">
                  {summary.overall_stats?.total_agents || 0}
                </p>
              </div>
              <Brain className="w-8 h-8 text-blue-500" />
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Executions</p>
                <p className="text-2xl font-bold text-gray-900">
                  {summary.overall_stats?.total_executions || 0}
                </p>
              </div>
              <Activity className="w-8 h-8 text-green-500" />
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Success Rate</p>
                <p className="text-2xl font-bold text-green-600">
                  {formatPercentage(summary.overall_stats?.overall_success_rate || 0)}
                </p>
              </div>
              <CheckCircle className="w-8 h-8 text-green-500" />
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Avg Quality</p>
                <p className="text-2xl font-bold text-purple-600">
                  {(summary.overall_stats?.overall_quality || 0).toFixed(1)}
                </p>
              </div>
              <Target className="w-8 h-8 text-purple-500" />
            </div>
          </div>
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Performance Trends */}
          <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-lg font-semibold text-gray-900">Top Performing Agents</h3>
              <select
                value={selectedMetric}
                onChange={(e) => setSelectedMetric(e.target.value)}
                className="px-3 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="success_rate">Success Rate</option>
                <option value="avg_quality">Average Quality</option>
                <option value="executions">Execution Count</option>
              </select>
            </div>
            
            {summaryLoading ? (
              <div className="flex items-center justify-center h-64">
                <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={getPerformanceTrendData()}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="name" 
                    angle={-45}
                    textAnchor="end"
                    height={100}
                    fontSize={10}
                  />
                  <YAxis />
                  <Tooltip />
                  <Bar 
                    dataKey={selectedMetric} 
                    fill="#3B82F6"
                    name={selectedMetric === 'success_rate' ? 'Success Rate (%)' : 
                          selectedMetric === 'avg_quality' ? 'Average Quality' : 
                          'Executions'}
                  />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>

          {/* Model Distribution */}
          <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900 mb-6">Model Usage Distribution</h3>
            
            {summaryLoading ? (
              <div className="flex items-center justify-center h-64">
                <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={getModelDistributionData()}
                    cx="50%"
                    cy="50%"
                    outerRadius={100}
                    fill="#8884d8"
                    dataKey="value"
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  >
                    {getModelDistributionData().map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* Quality Distribution and Best Performers */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Quality Distribution */}
          <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900 mb-6">Quality Score Distribution</h3>
            
            {summaryLoading ? (
              <div className="flex items-center justify-center h-64">
                <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={getQualityDistributionData()}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" fontSize={12} />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="value" fill="#10B981" />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>

          {/* Recent Best Performers */}
          <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900 mb-6">Recent Best Performers</h3>
            
            {summaryLoading ? (
              <div className="flex items-center justify-center h-64">
                <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
              </div>
            ) : (
              <div className="space-y-4">
                {(summary.best_performers || []).slice(0, 6).map((performer, index) => (
                  <div key={`${performer.agent_id}-${performer.model_name}`} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center gap-3">
                      <div className="flex-shrink-0">
                        <Award className="w-5 h-5 text-yellow-500" />
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-900">
                          {performer.agent_id}
                        </p>
                        <p className="text-xs text-gray-500">
                          {performer.model_name} • {performer.executions} runs
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-medium text-green-600">
                        {formatPercentage(performer.success_rate)}
                      </p>
                      <p className="text-xs text-gray-500">
                        Quality: {(performer.avg_quality || 0).toFixed(1)}
                      </p>
                    </div>
                  </div>
                ))}
                
                {(!summary.best_performers || summary.best_performers.length === 0) && (
                  <div className="text-center py-8">
                    <Activity className="w-12 h-12 mx-auto text-gray-400" />
                    <p className="text-gray-500 mt-2">No performance data available</p>
                    <p className="text-gray-400 text-sm">Execute some workflows to see performance metrics</p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Agent-Specific Metrics (when agent is selected) */}
        {selectedAgent !== 'all' && (
          <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900 mb-6">
              Agent Details: {selectedAgent}
            </h3>
            
            {metricsLoading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
                <span className="ml-2 text-gray-500">Loading agent metrics...</span>
              </div>
            ) : Object.keys(agentMetrics).length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {Object.entries(agentMetrics).map(([model, metrics]) => (
                  <div key={model} className="p-4 border border-gray-200 rounded-lg">
                    <h4 className="font-medium text-gray-900 mb-3">{model}</h4>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Success Rate:</span>
                        <span className="text-sm font-medium">
                          {formatPercentage(metrics.success_rate)}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Avg Time:</span>
                        <span className="text-sm font-medium">
                          {formatDuration(metrics.average_execution_time)}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Quality Score:</span>
                        <span className="text-sm font-medium">
                          {(metrics.average_quality_score || 0).toFixed(1)}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Executions:</span>
                        <span className="text-sm font-medium">
                          {metrics.total_executions}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <Brain className="w-12 h-12 mx-auto text-gray-400" />
                <p className="text-gray-500 mt-2">No metrics available for this agent</p>
              </div>
            )}
          </div>
        )}

        {/* Agent Selection */}
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Select Agent for Detailed Metrics</h3>
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => setSelectedAgent('all')}
              className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                selectedAgent === 'all'
                  ? 'bg-blue-100 text-blue-800'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              All Agents
            </button>
            {Array.from(new Set((summary.best_performers || []).map(p => p.agent_id))).map(agentId => (
              <button
                key={agentId}
                onClick={() => setSelectedAgent(agentId)}
                className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  selectedAgent === agentId
                    ? 'bg-blue-100 text-blue-800'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {agentId}
              </button>
            ))}
          </div>
        </div>

        {/* Last Updated */}
        <div className="mt-8 text-center text-sm text-gray-500">
          Last updated: {summary.last_updated ? new Date(summary.last_updated).toLocaleString() : 'Never'}
        </div>
      </div>
    </div>
  );
};

export default AgentPerformanceDashboard;