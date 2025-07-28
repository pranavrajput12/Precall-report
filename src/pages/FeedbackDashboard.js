import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { 
  MessageSquare, 
  Star, 
  TrendingUp, 
  Users, 
  CheckCircle, 
  AlertTriangle,
  Clock,
  Filter,
  Calendar,
  BarChart3,
  Loader2
} from 'lucide-react';
import { FeedbackList, FeedbackSummary } from '../components/FeedbackSystem';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell } from 'recharts';

const FeedbackDashboard = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [timeRange, setTimeRange] = useState('30'); // days
  const [selectedWorkflow, setSelectedWorkflow] = useState('all');

  // Fetch feedback summary
  const { data: summary, isLoading: summaryLoading } = useQuery({
    queryKey: ['feedback-summary', selectedWorkflow === 'all' ? null : selectedWorkflow, timeRange],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (selectedWorkflow !== 'all') params.append('workflow_id', selectedWorkflow);
      params.append('days', timeRange);
      
      try {
        const response = await fetch(`/api/feedback/summary?${params}`);
        if (!response.ok) {
          // Return empty summary structure for 404s or API not available
          return {
            total_feedback: 0,
            average_rating: 0,
            implemented_improvements: 0,
            recent_feedback_count: 0,
            rating_distribution: {},
            feedback_by_type: {},
            top_workflows_by_feedback: [],
            common_issues: []
          };
        }
        return await response.json();
      } catch (error) {
        return {
          total_feedback: 0,
          average_rating: 0,
          implemented_improvements: 0,
          recent_feedback_count: 0,
          rating_distribution: {},
          feedback_by_type: {},
          top_workflows_by_feedback: [],
          common_issues: []
        };
      }
    },
    refetchInterval: 30000,
    retry: false,
  });

  // Fetch pending feedback
  const { data: pendingFeedback = [], isLoading: pendingLoading } = useQuery({
    queryKey: ['pending-feedback'],
    queryFn: async () => {
      try {
        const response = await fetch('/api/feedback/pending');
        if (!response.ok) return [];
        const data = await response.json();
        return Array.isArray(data) ? data : (data?.data || []);
      } catch (error) {
        return [];
      }
    },
    refetchInterval: 10000,
    retry: false,
  });

  const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6'];

  // Prepare chart data
  const getRatingDistributionData = () => {
    if (!summary?.rating_distribution) return [];
    
    return Object.entries(summary.rating_distribution).map(([rating, count]) => ({
      rating: `${rating} Star${rating === '1' ? '' : 's'}`,
      count: count,
    }));
  };

  const getFeedbackTypeData = () => {
    if (!summary?.feedback_by_type) return [];
    
    return Object.entries(summary.feedback_by_type).map(([type, count]) => ({
      name: type.replace('_', ' ').toUpperCase(),
      value: count,
    }));
  };

  const getWorkflowPerformanceData = () => {
    if (!summary?.top_workflows_by_feedback) return [];
    
    return summary.top_workflows_by_feedback.slice(0, 10).map(workflow => ({
      workflow: workflow.workflow_id,
      feedback_count: workflow.feedback_count,
      average_rating: workflow.average_rating ? workflow.average_rating.toFixed(1) : 0,
      negative_feedback: workflow.negative_feedback_count || 0,
    }));
  };

  const tabs = [
    { id: 'overview', label: 'Overview', icon: BarChart3 },
    { id: 'pending', label: 'Pending Review', icon: Clock },
    { id: 'analytics', label: 'Analytics', icon: TrendingUp },
    { id: 'workflows', label: 'By Workflow', icon: MessageSquare },
  ];

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Feedback Dashboard</h1>
              <p className="text-gray-600 mt-2">
                Monitor user feedback, quality scores, and improvement suggestions
              </p>
            </div>
            <div className="flex items-center gap-4">
              <select
                value={timeRange}
                onChange={(e) => setTimeRange(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="7">Last 7 days</option>
                <option value="30">Last 30 days</option>
                <option value="90">Last 90 days</option>
                <option value="365">Last year</option>
              </select>
              <select
                value={selectedWorkflow}
                onChange={(e) => setSelectedWorkflow(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All Workflows</option>
                <option value="default_workflow">Default Workflow</option>
                <option value="linkedin_workflow">LinkedIn Workflow</option>
                <option value="email_workflow">Email Workflow</option>
              </select>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 mb-6">
          <div className="border-b border-gray-200">
            <nav className="flex space-x-8 px-6" aria-label="Tabs">
              {tabs.map((tab) => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center gap-2 ${
                      activeTab === tab.id
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    {tab.label}
                  </button>
                );
              })}
            </nav>
          </div>

          <div className="p-6">
            {/* Overview Tab */}
            {activeTab === 'overview' && (
              <div className="space-y-6">
                {/* Stats Cards */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                  <div className="bg-gradient-to-r from-blue-50 to-blue-100 p-6 rounded-lg">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-blue-600">Total Feedback</p>
                        <p className="text-2xl font-bold text-blue-900">
                          {summary?.total_feedback || 0}
                        </p>
                      </div>
                      <MessageSquare className="w-8 h-8 text-blue-500" />
                    </div>
                  </div>

                  <div className="bg-gradient-to-r from-yellow-50 to-yellow-100 p-6 rounded-lg">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-yellow-600">Average Rating</p>
                        <p className="text-2xl font-bold text-yellow-900">
                          {summary?.average_rating ? summary.average_rating.toFixed(1) : 'N/A'}
                        </p>
                      </div>
                      <Star className="w-8 h-8 text-yellow-500" />
                    </div>
                  </div>

                  <div className="bg-gradient-to-r from-green-50 to-green-100 p-6 rounded-lg">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-green-600">Implemented</p>
                        <p className="text-2xl font-bold text-green-900">
                          {summary?.implemented_improvements || 0}
                        </p>
                      </div>
                      <CheckCircle className="w-8 h-8 text-green-500" />
                    </div>
                  </div>

                  <div className="bg-gradient-to-r from-purple-50 to-purple-100 p-6 rounded-lg">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-purple-600">Recent Feedback</p>
                        <p className="text-2xl font-bold text-purple-900">
                          {summary?.recent_feedback_count || 0}
                        </p>
                      </div>
                      <TrendingUp className="w-8 h-8 text-purple-500" />
                    </div>
                  </div>
                </div>

                {/* Charts Row */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* Rating Distribution */}
                  <div className="bg-white p-6 rounded-lg border border-gray-200">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Rating Distribution</h3>
                    {summaryLoading ? (
                      <div className="flex items-center justify-center h-64">
                        <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
                      </div>
                    ) : (
                      <ResponsiveContainer width="100%" height={250}>
                        <BarChart data={getRatingDistributionData()}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="rating" />
                          <YAxis />
                          <Tooltip />
                          <Bar dataKey="count" fill="#3B82F6" />
                        </BarChart>
                      </ResponsiveContainer>
                    )}
                  </div>

                  {/* Feedback Type Distribution */}
                  <div className="bg-white p-6 rounded-lg border border-gray-200">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Feedback Types</h3>
                    {summaryLoading ? (
                      <div className="flex items-center justify-center h-64">
                        <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
                      </div>
                    ) : (
                      <ResponsiveContainer width="100%" height={250}>
                        <PieChart>
                          <Pie
                            data={getFeedbackTypeData()}
                            cx="50%"
                            cy="50%"
                            outerRadius={80}
                            fill="#8884d8"
                            dataKey="value"
                            label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                          >
                            {getFeedbackTypeData().map((entry, index) => (
                              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                            ))}
                          </Pie>
                          <Tooltip />
                        </PieChart>
                      </ResponsiveContainer>
                    )}
                  </div>
                </div>

                {/* Common Issues */}
                {summary?.common_issues && summary.common_issues.length > 0 && (
                  <div className="bg-white p-6 rounded-lg border border-gray-200">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Common Issues</h3>
                    <div className="flex flex-wrap gap-3">
                      {summary.common_issues.map((issue, index) => (
                        <span
                          key={index}
                          className="inline-flex items-center px-3 py-2 rounded-full text-sm font-medium bg-red-100 text-red-800"
                        >
                          <AlertTriangle className="w-4 h-4 mr-2" />
                          {issue.replace('_', ' ')}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Pending Review Tab */}
            {activeTab === 'pending' && (
              <div className="space-y-6">
                <div className="flex justify-between items-center">
                  <h3 className="text-lg font-semibold text-gray-900">
                    Pending Feedback ({pendingFeedback.length})
                  </h3>
                </div>

                {pendingLoading ? (
                  <div className="flex items-center justify-center py-12">
                    <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
                    <span className="ml-2 text-gray-500">Loading pending feedback...</span>
                  </div>
                ) : pendingFeedback.length === 0 ? (
                  <div className="text-center py-12">
                    <CheckCircle className="w-12 h-12 mx-auto text-green-400" />
                    <p className="text-gray-500 mt-2">No pending feedback</p>
                    <p className="text-gray-400 text-sm">All feedback has been reviewed</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {pendingFeedback.map((feedback) => (
                      <div key={feedback.id} className="bg-white p-4 rounded-lg border border-gray-200">
                        <div className="flex justify-between items-start">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-2">
                              <span className="text-sm font-medium text-gray-900 capitalize">
                                {feedback.feedback_type.replace('_', ' ')}
                              </span>
                              {feedback.rating && (
                                <div className="flex">
                                  {[1, 2, 3, 4, 5].map((star) => (
                                    <Star
                                      key={star}
                                      className={`w-4 h-4 ${
                                        star <= feedback.rating
                                          ? 'text-yellow-400 fill-current'
                                          : 'text-gray-300'
                                      }`}
                                    />
                                  ))}
                                </div>
                              )}
                            </div>
                            
                            <p className="text-sm text-gray-700 mb-2">{feedback.content}</p>
                            
                            {feedback.suggested_improvement && (
                              <div className="bg-blue-50 p-3 rounded-lg mb-2">
                                <p className="text-xs font-medium text-blue-900 mb-1">Suggested Improvement:</p>
                                <p className="text-sm text-blue-800">{feedback.suggested_improvement}</p>
                              </div>
                            )}
                            
                            <div className="flex items-center gap-4 text-xs text-gray-500">
                              <span>Workflow: {feedback.workflow_id}</span>
                              <span>Execution: {feedback.execution_id}</span>
                              <span>
                                {feedback.created_at ? new Date(feedback.created_at).toLocaleString() : 'Unknown date'}
                              </span>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Analytics Tab */}
            {activeTab === 'analytics' && (
              <div className="space-y-6">
                <div className="bg-white p-6 rounded-lg border border-gray-200">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Workflow Performance</h3>
                  {summaryLoading ? (
                    <div className="flex items-center justify-center h-64">
                      <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
                    </div>
                  ) : (
                    <ResponsiveContainer width="100%" height={300}>
                      <BarChart data={getWorkflowPerformanceData()}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="workflow" />
                        <YAxis />
                        <Tooltip />
                        <Bar dataKey="feedback_count" fill="#3B82F6" name="Total Feedback" />
                        <Bar dataKey="negative_feedback" fill="#EF4444" name="Negative Feedback" />
                      </BarChart>
                    </ResponsiveContainer>
                  )}
                </div>

                <FeedbackSummary workflowId={selectedWorkflow === 'all' ? null : selectedWorkflow} />
              </div>
            )}

            {/* Workflows Tab */}
            {activeTab === 'workflows' && (
              <div className="space-y-6">
                <FeedbackList 
                  workflowId={selectedWorkflow === 'all' ? 'default_workflow' : selectedWorkflow}
                />
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default FeedbackDashboard;