import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
  Copy,
  ChevronDown,
  ChevronUp,
  Download,
  RefreshCw,
  MessageSquare,
  Calendar,
  TrendingUp
} from 'lucide-react';
import toast from 'react-hot-toast';

const fetchAllRuns = async () => {
  const response = await fetch('/api/execution-history');
  if (!response.ok) throw new Error('Failed to fetch execution history');
  const data = await response.json();
  console.log('Fetched runs:', data);
  console.log('Total executions received:', data.executions?.length);
  console.log('Execution IDs:', data.executions?.map(e => e.id));
  return data.executions || [];
};

const AllRuns = () => {
  const [expandedRuns, setExpandedRuns] = useState({});
  const [filterStatus, setFilterStatus] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');

  const { data: runs = [], isLoading, refetch } = useQuery({
    queryKey: ['all-runs'],
    queryFn: fetchAllRuns,
    refetchInterval: 10000, // Refresh every 10 seconds
    staleTime: 5000, // Consider data stale after 5 seconds
    cacheTime: 0 // Don't cache the data
  });

  // Sort runs by date (newest first) and then filter
  const sortedRuns = [...runs].sort((a, b) => {
    const dateA = new Date(a.started_at);
    const dateB = new Date(b.started_at);
    return dateB - dateA; // Newest first
  });

  // Filter runs based on status and search term
  const filteredRuns = sortedRuns.filter(run => {
    const matchesStatus = filterStatus === 'all' || run.status === filterStatus;
    const matchesSearch = searchTerm === '' || 
      run.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      run.workflow_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      run.input_data?.prospect_company_url?.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesStatus && matchesSearch;
  });

  const toggleExpand = (runId) => {
    setExpandedRuns(prev => ({
      ...prev,
      [runId]: !prev[runId]
    }));
  };

  const copyMessage = (message) => {
    navigator.clipboard.writeText(message);
    toast.success('Message copied to clipboard!');
  };

  const copyAllMessages = () => {
    const allMessages = filteredRuns
      .filter(run => run.output?.message)
      .map(run => {
        let messageText = `--- ${run.id} (${new Date(run.started_at).toLocaleString()}) ---\n`;
        messageText += `IMMEDIATE RESPONSE:\n${run.output.immediate_response || run.output.message}\n`;
        
        if (run.output.follow_up_sequence && run.output.follow_up_sequence.length > 0) {
          messageText += '\nFOLLOW-UP SEQUENCE:\n';
          run.output.follow_up_sequence.forEach((followup, index) => {
            messageText += `\nFollow-up ${index + 1} (${followup.timing}):\n${followup.message}\n`;
          });
        }
        
        return messageText;
      })
      .join('\n---\n\n');
    
    navigator.clipboard.writeText(allMessages);
    toast.success(`Copied ${filteredRuns.length} message sequences to clipboard!`);
  };

  const exportToCSV = () => {
    const headers = ['ID', 'Status', 'Started At', 'Duration', 'Company', 'Quality Score', 'Immediate Response', 'Follow-up 1', 'Follow-up 2', 'Follow-up 3'];
    const rows = filteredRuns.map(run => [
      run.id,
      run.status,
      new Date(run.started_at).toLocaleString(),
      run.duration ? `${run.duration.toFixed(1)}s` : 'N/A',
      run.input_data?.prospect_company_url || '',
      run.output?.quality_score || '',
      (run.output?.immediate_response || run.output?.message || '').replace(/\n/g, ' '),
      run.output?.follow_up_sequence?.[0]?.message?.replace(/\n/g, ' ') || '',
      run.output?.follow_up_sequence?.[1]?.message?.replace(/\n/g, ' ') || '',
      run.output?.follow_up_sequence?.[2]?.message?.replace(/\n/g, ' ') || ''
    ]);

    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `workflow-runs-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success('Exported to CSV!');
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'failed':
        return <XCircle className="w-5 h-5 text-red-500" />;
      case 'running':
        return <RefreshCw className="w-5 h-5 text-yellow-500 animate-spin" />;
      default:
        return <AlertCircle className="w-5 h-5 text-gray-500" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'failed':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'running':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <RefreshCw className="w-8 h-8 animate-spin text-blue-600 mx-auto mb-2" />
          <p className="text-gray-600">Loading runs...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-6 flex justify-between items-start">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">All Workflow Runs</h1>
          <p className="text-gray-600">View, search, and manage all your workflow executions</p>
        </div>
        <button
          onClick={() => {
            refetch();
            toast.success('Refreshing data...');
          }}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white rounded-lg border p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Runs</p>
              <p className="text-2xl font-bold text-gray-900">{runs.length}</p>
              {sortedRuns.length > 0 && (
                <p className="text-xs text-gray-500 mt-1">Latest: {sortedRuns[0].id}</p>
              )}
            </div>
            <Calendar className="w-8 h-8 text-blue-500" />
          </div>
        </div>
        
        <div className="bg-white rounded-lg border p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Success Rate</p>
              <p className="text-2xl font-bold text-green-600">
                {runs.length > 0 
                  ? `${((runs.filter(r => r.status === 'completed').length / runs.length) * 100).toFixed(0)}%`
                  : '0%'}
              </p>
            </div>
            <TrendingUp className="w-8 h-8 text-green-500" />
          </div>
        </div>

        <div className="bg-white rounded-lg border p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Avg Quality</p>
              <p className="text-2xl font-bold text-blue-600">
                {runs.length > 0
                  ? `${(runs.reduce((acc, r) => acc + (r.output?.quality_score || 0), 0) / runs.length).toFixed(0)}%`
                  : '0%'}
              </p>
            </div>
            <MessageSquare className="w-8 h-8 text-blue-500" />
          </div>
        </div>

        <div className="bg-white rounded-lg border p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Avg Duration</p>
              <p className="text-2xl font-bold text-purple-600">
                {runs.length > 0
                  ? `${(runs.reduce((acc, r) => acc + (r.duration || 0), 0) / runs.length).toFixed(1)}s`
                  : '0s'}
              </p>
            </div>
            <Clock className="w-8 h-8 text-purple-500" />
          </div>
        </div>
      </div>

      {/* Controls */}
      <div className="bg-white rounded-lg border p-4 mb-6">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1">
            <input
              type="text"
              placeholder="Search by ID, workflow name, or company..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          
          <div className="flex gap-2">
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Status</option>
              <option value="completed">Completed</option>
              <option value="running">Running</option>
              <option value="failed">Failed</option>
            </select>

            <button
              onClick={() => refetch()}
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center gap-2 transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
              Refresh
            </button>

            <button
              onClick={copyAllMessages}
              className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg flex items-center gap-2 transition-colors"
            >
              <Copy className="w-4 h-4" />
              Copy All Sequences
            </button>

            <button
              onClick={exportToCSV}
              className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg flex items-center gap-2 transition-colors"
            >
              <Download className="w-4 h-4" />
              Export CSV
            </button>
          </div>
        </div>
      </div>

      {/* Runs List */}
      <div className="space-y-4">
        {filteredRuns.length === 0 ? (
          <div className="bg-white rounded-lg border p-8 text-center">
            <AlertCircle className="w-12 h-12 text-gray-400 mx-auto mb-2" />
            <p className="text-gray-600">No runs found matching your criteria</p>
          </div>
        ) : (
          filteredRuns.map((run) => (
            <div key={run.id} className="bg-white rounded-lg border overflow-hidden">
              {/* Run Header */}
              <div
                className="p-4 cursor-pointer hover:bg-gray-50 transition-colors"
                onClick={() => toggleExpand(run.id)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    {getStatusIcon(run.status)}
                    <div>
                      <h3 className="font-semibold text-gray-900">{run.id}</h3>
                      <p className="text-sm text-gray-600">
                        {run.workflow_name} • {new Date(run.started_at).toLocaleString()}
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-4">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(run.status)}`}>
                      {run.status}
                    </span>
                    {run.output?.quality_score && (
                      <span className="text-sm font-medium text-gray-600">
                        Quality: {run.output.quality_score}%
                      </span>
                    )}
                    {run.output?.has_follow_ups && (
                      <span className="text-xs bg-purple-100 text-purple-700 px-2 py-1 rounded-full">
                        +3 Follow-ups
                      </span>
                    )}
                    {run.duration && (
                      <span className="text-sm text-gray-500">
                        {run.duration.toFixed(1)}s
                      </span>
                    )}
                    {expandedRuns[run.id] ? <ChevronUp /> : <ChevronDown />}
                  </div>
                </div>
              </div>

              {/* Expanded Content */}
              {expandedRuns[run.id] && (
                <div className="border-t">
                  <div className="p-4 bg-gray-50">
                    <h4 className="font-medium text-gray-900 mb-2">Input Data</h4>
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div>
                        <span className="text-gray-600">Channel:</span>
                        <span className="ml-2 font-medium">{run.input_data?.channel}</span>
                      </div>
                      <div>
                        <span className="text-gray-600">Company:</span>
                        <span className="ml-2 font-medium text-blue-600 hover:underline">
                          <a href={run.input_data?.prospect_company_url} target="_blank" rel="noopener noreferrer">
                            {run.input_data?.prospect_company_url}
                          </a>
                        </span>
                      </div>
                    </div>
                  </div>

                  {run.output?.message && (
                    <div className="p-4">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-medium text-gray-900">Immediate Response</h4>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            copyMessage(run.output.immediate_response || run.output.message);
                          }}
                          className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded-lg text-sm flex items-center gap-1 transition-colors"
                        >
                          <Copy className="w-3 h-3" />
                          Copy Immediate
                        </button>
                      </div>
                      <div className="bg-white border rounded-lg p-4">
                        <pre className="whitespace-pre-wrap text-sm text-gray-800 font-sans">
                          {run.output.immediate_response || run.output.message}
                        </pre>
                      </div>
                      
                      {/* Follow-up Sequence */}
                      {run.output.follow_up_sequence && run.output.follow_up_sequence.length > 0 && (
                        <div className="mt-4">
                          <h4 className="font-medium text-gray-900 mb-3">Follow-up Sequence</h4>
                          <div className="space-y-3">
                            {run.output.follow_up_sequence.map((followup, index) => (
                              <div key={index} className="bg-gray-50 border rounded-lg p-4">
                                <div className="flex items-center justify-between mb-2">
                                  <div>
                                    <span className="font-medium text-gray-900">Follow-up {index + 1}</span>
                                    <span className="ml-2 text-sm text-gray-600">({followup.timing})</span>
                                    <span className="ml-2 text-xs text-gray-500">{followup.word_count} words</span>
                                  </div>
                                  <button
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      copyMessage(followup.message);
                                    }}
                                    className="bg-gray-600 hover:bg-gray-700 text-white px-2 py-1 rounded text-xs flex items-center gap-1 transition-colors"
                                  >
                                    <Copy className="w-3 h-3" />
                                    Copy
                                  </button>
                                </div>
                                <pre className="whitespace-pre-wrap text-sm text-gray-700 font-sans">
                                  {followup.message}
                                </pre>
                              </div>
                            ))}
                          </div>
                          
                          {/* Copy All Messages Button */}
                          <div className="mt-3 flex justify-end">
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                const allMessages = [
                                  `IMMEDIATE RESPONSE:\n${run.output.immediate_response || run.output.message}`,
                                  ...run.output.follow_up_sequence.map((f, i) => 
                                    `\nFOLLOW-UP ${i + 1} (${f.timing}):\n${f.message}`
                                  )
                                ].join('\n\n---\n\n');
                                navigator.clipboard.writeText(allMessages);
                                toast.success('Copied all messages!');
                              }}
                              className="bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded-lg text-sm flex items-center gap-1 transition-colors"
                            >
                              <Copy className="w-3 h-3" />
                              Copy All Messages
                            </button>
                          </div>
                        </div>
                      )}
                      
                      {/* Metrics */}
                      <div className="mt-4 grid grid-cols-2 gap-4">
                        <div className="bg-blue-50 rounded-lg p-3">
                          <p className="text-sm text-gray-600">Quality Score</p>
                          <p className="text-xl font-bold text-blue-600">{run.output.quality_score}%</p>
                        </div>
                        <div className="bg-green-50 rounded-lg p-3">
                          <p className="text-sm text-gray-600">Predicted Response Rate</p>
                          <p className="text-xl font-bold text-green-600">
                            {(run.output.predicted_response_rate * 100).toFixed(0)}%
                          </p>
                        </div>
                      </div>
                    </div>
                  )}

                  {run.error && (
                    <div className="p-4">
                      <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                        <p className="text-sm text-red-800">{run.error}</p>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default AllRuns;