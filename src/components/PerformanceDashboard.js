import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  Area,
  AreaChart,
} from 'recharts';
import { RefreshCw, Activity, Clock, CheckCircle, AlertCircle } from 'lucide-react';
import toast from 'react-hot-toast';

const fetchPerformanceMetrics = async () => {
  const response = await fetch('http://localhost:8090/api/performance/metrics');
  if (!response.ok) throw new Error('Failed to fetch performance metrics');
  return response.json();
};

const fetchAgentPerformance = async () => {
  const response = await fetch('http://localhost:8090/api/performance/agents');
  if (!response.ok) throw new Error('Failed to fetch agent performance');
  return response.json();
};

const fetchSystemPerformance = async () => {
  const response = await fetch('http://localhost:8090/api/performance/system');
  if (!response.ok) throw new Error('Failed to fetch system performance');
  return response.json();
};

const PerformanceDashboard = ({ 
  agents = [], 
  executionHistory = [], 
  testResults = [],
  refreshInterval = 5000 
}) => {
  const { data: performanceData, isLoading: perfLoading } = useQuery({
    queryKey: ['performance-metrics'],
    queryFn: fetchPerformanceMetrics,
    refetchInterval: refreshInterval
  });

  const { data: agentData, isLoading: agentLoading } = useQuery({
    queryKey: ['agent-performance'],
    queryFn: fetchAgentPerformance,
    refetchInterval: refreshInterval
  });

  const { data: systemData, isLoading: systemLoading } = useQuery({
    queryKey: ['system-performance'],
    queryFn: fetchSystemPerformance,
    refetchInterval: refreshInterval
  });

  if (perfLoading || agentLoading || systemLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <RefreshCw className="w-8 h-8 animate-spin text-blue-600 mx-auto mb-2" />
          <p className="text-gray-600">Loading performance data...</p>
        </div>
      </div>
    );
  }

  const performanceMetrics = performanceData?.performance_data || [];
  const agentMetrics = agentData?.agent_metrics || [];
  const systemHealth = systemData?.system_health || {};

  const statusColors = {
    ready: '#6b7280',
    running: '#f59e0b',
    completed: '#10b981',
    error: '#ef4444',
  };

  const pieData = agentMetrics.map(agent => ({
    name: agent.name,
    value: agent.executions,
    fill: statusColors[agent.status] || '#6b7280',
  }));

  const handleMetricClick = (data) => {
    if (data && data.activeLabel) {
      toast.success(`Viewing details for ${data.activeLabel}`);
    }
  };

  return (
    <div className="performance-dashboard">
      <div className="dashboard-header">
        <h2>Performance Monitoring Dashboard</h2>
        <div className="system-health">
          <div className="health-metric">
            <span className="metric-label">CPU:</span>
            <span className={`metric-value ${systemHealth.cpu > 80 ? 'critical' : systemHealth.cpu > 60 ? 'warning' : 'normal'}`}>
              {systemHealth.cpu}%
            </span>
          </div>
          <div className="health-metric">
            <span className="metric-label">Memory:</span>
            <span className={`metric-value ${systemHealth.memory > 80 ? 'critical' : systemHealth.memory > 60 ? 'warning' : 'normal'}`}>
              {systemHealth.memory}%
            </span>
          </div>
          <div className="health-metric">
            <span className="metric-label">Active Agents:</span>
            <span className="metric-value normal">{systemHealth.activeAgents}</span>
          </div>
          <div className="health-metric">
            <span className="metric-label">Total Executions:</span>
            <span className="metric-value normal">{systemHealth.totalExecutions}</span>
          </div>
        </div>
      </div>

      <div className="dashboard-grid">
        {/* Execution Timeline */}
        <div className="chart-container">
          <h3>Execution Timeline</h3>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={performanceMetrics} onClick={handleMetricClick}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Area 
                type="monotone" 
                dataKey="executions" 
                stroke="#3b82f6" 
                fill="#3b82f6" 
                fillOpacity={0.3}
                name="Executions"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Average Execution Time */}
        <div className="chart-container">
          <h3>Average Execution Time</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={performanceMetrics} onClick={handleMetricClick}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis />
              <Tooltip formatter={(value) => [`${value}ms`, 'Avg Time']} />
              <Legend />
              <Line 
                type="monotone" 
                dataKey="averageTime" 
                stroke="#f59e0b" 
                strokeWidth={2}
                name="Avg Time (ms)"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Success Rate */}
        <div className="chart-container">
          <h3>Success Rate</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={performanceMetrics} onClick={handleMetricClick}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis domain={[0, 100]} />
              <Tooltip formatter={(value) => [`${value}%`, 'Success Rate']} />
              <Legend />
              <Line 
                type="monotone" 
                dataKey="successRate" 
                stroke="#10b981" 
                strokeWidth={2}
                name="Success Rate (%)"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Agent Performance Comparison */}
        <div className="chart-container">
          <h3>Agent Performance Comparison</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={agentMetrics} onClick={handleMetricClick}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="executions" fill="#3b82f6" name="Executions" />
              <Bar dataKey="avgTime" fill="#f59e0b" name="Avg Time (ms)" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Agent Execution Distribution */}
        <div className="chart-container">
          <h3>Agent Execution Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart onClick={handleMetricClick}>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {pieData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.fill} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Error Rate */}
        <div className="chart-container">
          <h3>Error Rate</h3>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={performanceMetrics} onClick={handleMetricClick}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Area 
                type="monotone" 
                dataKey="errors" 
                stroke="#ef4444" 
                fill="#ef4444" 
                fillOpacity={0.3}
                name="Errors"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      <style>{`
        .performance-dashboard {
          padding: 20px;
          background: #f8fafc;
          border-radius: 8px;
          margin: 20px 0;
        }

        .dashboard-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 30px;
          padding-bottom: 20px;
          border-bottom: 2px solid #e2e8f0;
        }

        .dashboard-header h2 {
          color: #1f2937;
          margin: 0;
        }

        .system-health {
          display: flex;
          gap: 20px;
        }

        .health-metric {
          display: flex;
          flex-direction: column;
          align-items: center;
          padding: 10px;
          background: white;
          border-radius: 8px;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }

        .metric-label {
          font-size: 12px;
          color: #6b7280;
          margin-bottom: 4px;
        }

        .metric-value {
          font-size: 18px;
          font-weight: bold;
        }

        .metric-value.normal {
          color: #10b981;
        }

        .metric-value.warning {
          color: #f59e0b;
        }

        .metric-value.critical {
          color: #ef4444;
        }

        .dashboard-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
          gap: 20px;
        }

        .chart-container {
          background: white;
          padding: 20px;
          border-radius: 8px;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }

        .chart-container h3 {
          margin: 0 0 20px 0;
          color: #1f2937;
          font-size: 16px;
        }

        @media (max-width: 768px) {
          .dashboard-grid {
            grid-template-columns: 1fr;
          }
          
          .dashboard-header {
            flex-direction: column;
            gap: 20px;
          }
          
          .system-health {
            flex-wrap: wrap;
            justify-content: center;
          }
        }
      `}</style>
    </div>
  );
};

export default PerformanceDashboard; 