import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  Play, 
  Square, 
  Upload, 
  Download, 
  Clock, 
  CheckCircle, 
  XCircle, 
  AlertCircle,
  MoreVertical,
  Trash2,
  Eye,
  BarChart3,
  Loader2,
  Plus,
  FileText
} from 'lucide-react';
import { toast } from 'react-hot-toast';

const BatchProcessing = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  const [selectedBatch, setSelectedBatch] = useState(null);
  const [newBatch, setNewBatch] = useState({
    name: '',
    workflow_id: 'default_workflow',
    input_data: ''
  });

  const queryClient = useQueryClient();

  // Fetch batch list
  const { data: batchResponse, isLoading: batchesLoading, refetch: refetchBatches } = useQuery({
    queryKey: ['batches'],
    queryFn: async () => {
      const response = await fetch('/api/batch/list');
      if (!response.ok) throw new Error('Failed to fetch batches');
      const data = await response.json();
      return data;
    },
    refetchInterval: 5000, // Refresh every 5 seconds for real-time updates
  });

  // Ensure batches is always an array
  const batches = Array.isArray(batchResponse) ? batchResponse : (batchResponse?.data || batchResponse?.batches || []);

  // Fetch batch details
  const { data: batchDetails, isLoading: detailsLoading } = useQuery({
    queryKey: ['batch-details', selectedBatch?.batch_id],
    queryFn: async () => {
      if (!selectedBatch?.batch_id) return null;
      const response = await fetch(`/api/batch/${selectedBatch.batch_id}/status`);
      if (!response.ok) throw new Error('Failed to fetch batch details');
      return response.json();
    },
    enabled: !!selectedBatch?.batch_id,
    refetchInterval: 2000, // More frequent updates for selected batch
  });

  // Create batch mutation
  const createBatchMutation = useMutation({
    mutationFn: async (batchData) => {
      // Parse input data as JSON array
      const inputList = JSON.parse(batchData.input_data);
      
      const response = await fetch('/api/batch/create-and-start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: batchData.name,
          workflow_id: batchData.workflow_id,
          input_list: inputList
        }),
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to create batch');
      }
      
      return response.json();
    },
    onSuccess: () => {
      toast.success('Batch created and started successfully!');
      setShowCreateModal(false);
      setNewBatch({ name: '', workflow_id: 'default_workflow', input_data: '' });
      refetchBatches();
    },
    onError: (error) => {
      toast.error(`Failed to create batch: ${error.message}`);
    },
  });

  // Cancel batch mutation
  const cancelBatchMutation = useMutation({
    mutationFn: async (batchId) => {
      const response = await fetch(`/api/batch/${batchId}/cancel`, {
        method: 'POST',
      });
      if (!response.ok) throw new Error('Failed to cancel batch');
      return response.json();
    },
    onSuccess: () => {
      toast.success('Batch cancelled successfully');
      refetchBatches();
    },
    onError: (error) => {
      toast.error(`Failed to cancel batch: ${error.message}`);
    },
  });

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'failed':
        return <XCircle className="w-5 h-5 text-red-500" />;
      case 'running':
        return <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />;
      case 'pending':
        return <Clock className="w-5 h-5 text-yellow-500" />;
      case 'cancelled':
        return <Square className="w-5 h-5 text-gray-500" />;
      default:
        return <AlertCircle className="w-5 h-5 text-gray-400" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      case 'running':
        return 'bg-blue-100 text-blue-800';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      case 'cancelled':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-600';
    }
  };

  const handleCreateBatch = () => {
    createBatchMutation.mutate(newBatch);
  };

  const handleViewDetails = (batch) => {
    setSelectedBatch(batch);
    setShowDetailsModal(true);
  };

  const handleCancelBatch = (batchId) => {
    if (window.confirm('Are you sure you want to cancel this batch?')) {
      cancelBatchMutation.mutate(batchId);
    }
  };

  const formatDuration = (seconds) => {
    if (!seconds) return 'N/A';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}m ${secs}s`;
  };

  const getSampleInputData = () => {
    return JSON.stringify([
      {
        "prospect_profile_url": "https://linkedin.com/in/sample1",
        "message_context": "Initial outreach for partnership discussion"
      },
      {
        "prospect_profile_url": "https://linkedin.com/in/sample2", 
        "message_context": "Follow-up on previous conversation"
      },
      {
        "prospect_profile_url": "https://linkedin.com/in/sample3",
        "message_context": "Introduction to new product features"
      }
    ], null, 2);
  };

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Batch Processing</h1>
              <p className="text-gray-600 mt-2">
                Process multiple workflows simultaneously with advanced queuing and progress tracking
              </p>
            </div>
            <button
              onClick={() => setShowCreateModal(true)}
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center gap-2 transition-colors"
            >
              <Plus className="w-4 h-4" />
              New Batch
            </button>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Batches</p>
                <p className="text-2xl font-bold text-gray-900">{batches.length}</p>
              </div>
              <BarChart3 className="w-8 h-8 text-blue-500" />
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Running</p>
                <p className="text-2xl font-bold text-blue-600">
                  {batches.filter(b => b.status === 'running').length}
                </p>
              </div>
              <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Completed</p>
                <p className="text-2xl font-bold text-green-600">
                  {batches.filter(b => b.status === 'completed').length}
                </p>
              </div>
              <CheckCircle className="w-8 h-8 text-green-500" />
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Failed</p>
                <p className="text-2xl font-bold text-red-600">
                  {batches.filter(b => b.status === 'failed').length}
                </p>
              </div>
              <XCircle className="w-8 h-8 text-red-500" />
            </div>
          </div>
        </div>

        {/* Batch List */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-xl font-semibold text-gray-900">Recent Batches</h2>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Batch
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Progress
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Jobs
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Created
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {batchesLoading ? (
                  <tr>
                    <td colSpan="6" className="px-6 py-12 text-center">
                      <Loader2 className="w-6 h-6 animate-spin mx-auto text-gray-400" />
                      <p className="text-gray-500 mt-2">Loading batches...</p>
                    </td>
                  </tr>
                ) : batches.length === 0 ? (
                  <tr>
                    <td colSpan="6" className="px-6 py-12 text-center">
                      <FileText className="w-12 h-12 mx-auto text-gray-400" />
                      <p className="text-gray-500 mt-2">No batches found</p>
                      <p className="text-gray-400 text-sm">Create your first batch to get started</p>
                    </td>
                  </tr>
                ) : (
                  batches.map((batch) => (
                    <tr key={batch.batch_id} className="hover:bg-gray-50">
                      <td className="px-6 py-4">
                        <div>
                          <p className="text-sm font-medium text-gray-900">{batch.name}</p>
                          <p className="text-sm text-gray-500">ID: {batch.batch_id}</p>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          {getStatusIcon(batch.status)}
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(batch.status)}`}>
                            {batch.status}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div 
                            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                            style={{ width: `${batch.progress_percentage || 0}%` }}
                          />
                        </div>
                        <p className="text-xs text-gray-500 mt-1">
                          {Math.round(batch.progress_percentage || 0)}%
                        </p>
                      </td>
                      <td className="px-6 py-4">
                        <div className="text-sm">
                          <p className="text-gray-900">
                            {batch.completed_jobs || 0} / {batch.total_jobs || 0}
                          </p>
                          {batch.failed_jobs > 0 && (
                            <p className="text-red-600">{batch.failed_jobs} failed</p>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-500">
                        {batch.created_at ? new Date(batch.created_at).toLocaleString() : 'N/A'}
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => handleViewDetails(batch)}
                            className="text-blue-600 hover:text-blue-800 p-1 rounded"
                            title="View Details"
                          >
                            <Eye className="w-4 h-4" />
                          </button>
                          {(batch.status === 'running' || batch.status === 'pending') && (
                            <button
                              onClick={() => handleCancelBatch(batch.batch_id)}
                              className="text-red-600 hover:text-red-800 p-1 rounded"
                              title="Cancel Batch"
                            >
                              <Square className="w-4 h-4" />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Create Batch Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-xl font-semibold text-gray-900">Create New Batch</h2>
            </div>

            <div className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Batch Name
                </label>
                <input
                  type="text"
                  value={newBatch.name}
                  onChange={(e) => setNewBatch({...newBatch, name: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Enter batch name"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Workflow ID
                </label>
                <select
                  value={newBatch.workflow_id}
                  onChange={(e) => setNewBatch({...newBatch, workflow_id: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="default_workflow">Default Workflow</option>
                  <option value="linkedin_workflow">LinkedIn Workflow</option>
                  <option value="email_workflow">Email Workflow</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Input Data (JSON Array)
                </label>
                <div className="space-y-2">
                  <button
                    onClick={() => setNewBatch({...newBatch, input_data: getSampleInputData()})}
                    className="text-blue-600 hover:text-blue-800 text-sm"
                  >
                    Load Sample Data
                  </button>
                  <textarea
                    value={newBatch.input_data}
                    onChange={(e) => setNewBatch({...newBatch, input_data: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                    rows="10"
                    placeholder="Enter JSON array of input objects..."
                  />
                </div>
              </div>
            </div>

            <div className="px-6 py-4 border-t border-gray-200 flex justify-end gap-3">
              <button
                onClick={() => setShowCreateModal(false)}
                className="px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateBatch}
                disabled={!newBatch.name || !newBatch.input_data || createBatchMutation.isPending}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
              >
                {createBatchMutation.isPending && <Loader2 className="w-4 h-4 animate-spin" />}
                Create & Start Batch
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Batch Details Modal */}
      {showDetailsModal && selectedBatch && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200">
              <div className="flex justify-between items-center">
                <h2 className="text-xl font-semibold text-gray-900">Batch Details</h2>
                <button
                  onClick={() => setShowDetailsModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ×
                </button>
              </div>
            </div>

            <div className="p-6">
              {detailsLoading ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
                  <span className="ml-2 text-gray-500">Loading details...</span>
                </div>
              ) : batchDetails ? (
                <div className="space-y-6">
                  {/* Basic Info */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <h3 className="text-lg font-medium text-gray-900 mb-4">Basic Information</h3>
                      <div className="space-y-3">
                        <div>
                          <p className="text-sm font-medium text-gray-500">Name</p>
                          <p className="text-sm text-gray-900">{batchDetails.name}</p>
                        </div>
                        <div>
                          <p className="text-sm font-medium text-gray-500">Batch ID</p>
                          <p className="text-sm text-gray-900 font-mono">{batchDetails.batch_id}</p>
                        </div>
                        <div>
                          <p className="text-sm font-medium text-gray-500">Workflow</p>
                          <p className="text-sm text-gray-900">{batchDetails.workflow_id}</p>
                        </div>
                        <div>
                          <p className="text-sm font-medium text-gray-500">Status</p>
                          <div className="flex items-center gap-2">
                            {getStatusIcon(batchDetails.status)}
                            <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(batchDetails.status)}`}>
                              {batchDetails.status}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>

                    <div>
                      <h3 className="text-lg font-medium text-gray-900 mb-4">Progress & Timing</h3>
                      <div className="space-y-3">
                        <div>
                          <p className="text-sm font-medium text-gray-500">Progress</p>
                          <div className="w-full bg-gray-200 rounded-full h-2 mt-1">
                            <div 
                              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                              style={{ width: `${batchDetails.progress_percentage || 0}%` }}
                            />
                          </div>
                          <p className="text-xs text-gray-500 mt-1">
                            {Math.round(batchDetails.progress_percentage || 0)}% complete
                          </p>
                        </div>
                        <div>
                          <p className="text-sm font-medium text-gray-500">Jobs</p>
                          <p className="text-sm text-gray-900">
                            {batchDetails.completed_jobs} / {batchDetails.total_jobs} completed
                            {batchDetails.failed_jobs > 0 && (
                              <span className="text-red-600 ml-2">({batchDetails.failed_jobs} failed)</span>
                            )}
                          </p>
                        </div>
                        <div>
                          <p className="text-sm font-medium text-gray-500">Average Execution Time</p>
                          <p className="text-sm text-gray-900">
                            {formatDuration(batchDetails.average_execution_time)}
                          </p>
                        </div>
                        <div>
                          <p className="text-sm font-medium text-gray-500">Estimated Completion</p>
                          <p className="text-sm text-gray-900">
                            {batchDetails.estimated_completion 
                              ? new Date(batchDetails.estimated_completion).toLocaleString()
                              : 'N/A'
                            }
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Timestamps */}
                  <div>
                    <h3 className="text-lg font-medium text-gray-900 mb-4">Timeline</h3>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div>
                        <p className="text-sm font-medium text-gray-500">Created</p>
                        <p className="text-sm text-gray-900">
                          {batchDetails.created_at ? new Date(batchDetails.created_at).toLocaleString() : 'N/A'}
                        </p>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-500">Started</p>
                        <p className="text-sm text-gray-900">
                          {batchDetails.started_at ? new Date(batchDetails.started_at).toLocaleString() : 'Not started'}
                        </p>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-500">Completed</p>
                        <p className="text-sm text-gray-900">
                          {batchDetails.completed_at ? new Date(batchDetails.completed_at).toLocaleString() : 'In progress'}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-12">
                  <p className="text-gray-500">Failed to load batch details</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default BatchProcessing;