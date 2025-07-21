import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
  Play,
  Activity,
  BarChart2,
  FileText,
  TrendingUp,
  TrendingDown,
  Zap,
  RefreshCw,
  MessageSquare,
  Send
} from 'lucide-react';
import toast from 'react-hot-toast';

const fetchExecutionHistory = async () => {
  const response = await fetch('/api/execution-history');
  if (!response.ok) throw new Error('Failed to fetch execution history');
  const data = await response.json();
  console.log('Execution history data:', data);
  console.log('Executions array:', data.executions);
  return data.executions || [];
};

const fetchTestResults = async () => {
  const response = await fetch('/api/test-results');
  if (!response.ok) throw new Error('Failed to fetch test results');
  const data = await response.json();
  return data.test_results || [];
};

const ExecutionHistory = () => {
  const [activeTab, setActiveTab] = useState('executions');
  const [selectedExecution, setSelectedExecution] = useState(null);
  const [selectedTest, setSelectedTest] = useState(null);
  const [workflowForm, setWorkflowForm] = useState({
    conversation_thread: '',
    channel: 'LinkedIn',
    prospect_profile_url: '',
    prospect_company_url: '',
    prospect_company_website: '',
    qubit_context: ''
  });
  const [isRunningWorkflow, setIsRunningWorkflow] = useState(false);

  const { data: executions = [], isLoading: execLoading, refetch: refetchExecutions } = useQuery({
    queryKey: ['execution-history'],
    queryFn: fetchExecutionHistory,
    refetchInterval: 5000 // Auto-refresh every 5 seconds
  });

  const createDemoExecution = async () => {
    try {
      const response = await fetch('/api/demo-execution', { method: 'POST' });
      if (response.ok) {
        toast.success('Demo execution created!');
        refetchExecutions();
      } else {
        toast.error('Failed to create demo execution');
      }
    } catch (error) {
      toast.error('Error creating demo execution');
    }
  };

  const runWorkflow = async () => {
    setIsRunningWorkflow(true);
    try {
      const response = await fetch('/run', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(workflowForm),
      });
      
      if (response.ok) {
        await response.json();
        toast.success('Workflow started successfully!');
        refetchExecutions();
        // Reset form
        setWorkflowForm({
          conversation_thread: '',
          channel: 'LinkedIn',
          prospect_profile_url: '',
          prospect_company_url: '',
          prospect_company_website: '',
          qubit_context: ''
        });
      } else {
        const error = await response.json();
        toast.error(`Failed to run workflow: ${error.error || 'Unknown error'}`);
      }
    } catch (error) {
      toast.error('Error running workflow');
    } finally {
      setIsRunningWorkflow(false);
    }
  };

  const { data: testResults = [], isLoading: testLoading, refetch: refetchTests } = useQuery({
    queryKey: ['test-results'],
    queryFn: fetchTestResults,
    refetchInterval: 30000 // Auto-refresh every 30 seconds
  });

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
      case 'passed':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'failed':
        return <XCircle className="w-5 h-5 text-red-500" />;
      case 'running':
        return <RefreshCw className="w-5 h-5 text-yellow-500 animate-spin" />;
      case 'warning':
        return <AlertCircle className="w-5 h-5 text-yellow-500" />;
      default:
        return <Activity className="w-5 h-5 text-gray-500" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
      case 'passed':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'failed':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'running':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'warning':
        return 'bg-orange-100 text-orange-800 border-orange-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const formatDuration = (seconds) => {
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (execLoading || testLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <RefreshCw className="w-8 h-8 animate-spin text-blue-600 mx-auto mb-2" />
          <p className="text-gray-600">Loading data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-6 flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Execution History & Test Results</h1>
          <p className="text-gray-600">Monitor workflow executions and test performance</p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={createDemoExecution}
            className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg flex items-center gap-2 transition-colors"
          >
            <Play className="w-4 h-4" />
            Create Demo
          </button>
          <button
            onClick={() => window.location.href = '/all-runs'}
            className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg flex items-center gap-2 transition-colors"
          >
            <MessageSquare className="w-4 h-4" />
            View All Runs
          </button>
          <button
            onClick={() => window.location.href = '/run'}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center gap-2 transition-colors"
          >
            <Zap className="w-4 h-4" />
            Run New Workflow
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('executions')}
            className={`py-2 px-1 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'executions'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4" />
              Executions ({executions.length})
            </div>
          </button>
          <button
            onClick={() => setActiveTab('tests')}
            className={`py-2 px-1 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'tests'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <div className="flex items-center gap-2">
              <BarChart2 className="w-4 h-4" />
              Test Results ({testResults.length})
            </div>
          </button>
          <button
            onClick={() => setActiveTab('run')}
            className={`py-2 px-1 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'run'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <div className="flex items-center gap-2">
              <Zap className="w-4 h-4" />
              Run Workflow
            </div>
          </button>
        </nav>
      </div>

      {/* Content */}
      {activeTab === 'executions' ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Execution List */}
          <div className="lg:col-span-2 space-y-4">
            {executions.map((execution) => (
              <div
                key={execution.id}
                onClick={() => setSelectedExecution(execution)}
                className={`bg-white rounded-lg border p-4 cursor-pointer hover:shadow-md transition-shadow ${
                  selectedExecution?.id === execution.id ? 'ring-2 ring-blue-500' : ''
                }`}
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-3">
                    {getStatusIcon(execution.status)}
                    <div>
                      <h3 className="font-medium text-gray-900">{execution.workflow_name}</h3>
                      <p className="text-sm text-gray-600">ID: {execution.id}</p>
                    </div>
                  </div>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(execution.status)}`}>
                    {execution.status}
                  </span>
                </div>

                <div className="mt-3 space-y-1 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Started:</span>
                    <span className="font-medium">{formatDate(execution.started_at)}</span>
                  </div>
                  {execution.completed_at && (
                    <div className="flex justify-between">
                      <span className="text-gray-600">Duration:</span>
                      <span className="font-medium">{formatDuration(execution.duration)}</span>
                    </div>
                  )}
                  {execution.current_step && (
                    <div className="flex justify-between">
                      <span className="text-gray-600">Current Step:</span>
                      <span className="font-medium">{execution.current_step}</span>
                    </div>
                  )}
                </div>

                {/* Progress bar for running executions */}
                {execution.status === 'running' && execution.progress && (
                  <div className="mt-3">
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-yellow-500 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${execution.progress}%` }}
                      />
                    </div>
                    <p className="text-xs text-gray-600 mt-1">{execution.progress}% complete</p>
                  </div>
                )}

                {/* Step indicators */}
                <div className="mt-3 flex gap-1">
                  {execution.steps?.map((step, index) => (
                    <div
                      key={index}
                      className={`flex-1 h-1 rounded-full ${
                        step.status === 'completed' ? 'bg-green-500' :
                        step.status === 'running' ? 'bg-yellow-500' :
                        step.status === 'failed' ? 'bg-red-500' :
                        'bg-gray-300'
                      }`}
                    />
                  ))}
                </div>
              </div>
            ))}
          </div>

          {/* Execution Details */}
          <div className="lg:col-span-1">
            {selectedExecution ? (
              <div className="bg-white rounded-lg border p-4">
                <h3 className="font-semibold text-gray-900 mb-4">Execution Details</h3>
                
                {/* Input Data */}
                <div className="mb-4">
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Input Data</h4>
                  <div className="bg-gray-50 rounded p-3 text-sm space-y-1">
                    {Object.entries(selectedExecution.input_data || {}).map(([key, value]) => (
                      <div key={key} className="flex justify-between">
                        <span className="text-gray-600">{key}:</span>
                        <span className="font-medium text-gray-900 truncate ml-2" title={value}>
                          {value}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Steps */}
                <div className="mb-4">
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Steps</h4>
                  <div className="space-y-2">
                    {selectedExecution.steps?.map((step, index) => (
                      <div key={index} className="bg-gray-50 rounded p-3">
                        <div className="flex items-center justify-between mb-1">
                          <span className="font-medium text-sm">{step.name}</span>
                          {getStatusIcon(step.status)}
                        </div>
                        <p className="text-xs text-gray-600">{step.result}</p>
                        {step.error && (
                          <p className="text-xs text-red-600 mt-1">{step.error}</p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>

                {/* Output */}
                {selectedExecution.output && (
                  <div className="mt-6">
                    <h4 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                      <MessageSquare className="w-5 h-5 text-blue-600" />
                      Generated Output
                    </h4>
                    <div className="bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-200 rounded-xl p-6">
                      <div className="space-y-4">
                        {/* Metrics Row */}
                        <div className="grid grid-cols-2 gap-4">
                          <div className="bg-white rounded-lg p-3 border border-blue-100">
                            <div className="text-xs text-gray-600 mb-1">Quality Score</div>
                            <div className="text-2xl font-bold text-green-600">
                              {selectedExecution.output.quality_score}%
                            </div>
                          </div>
                          <div className="bg-white rounded-lg p-3 border border-blue-100">
                            <div className="text-xs text-gray-600 mb-1">Response Rate</div>
                            <div className="text-2xl font-bold text-blue-600">
                              {(selectedExecution.output.predicted_response_rate * 100).toFixed(0)}%
                            </div>
                          </div>
                        </div>
                        
                        {/* Generated Message */}
                        <div>
                          <h5 className="text-base font-semibold text-gray-800 mb-3 flex items-center gap-2">
                            <Send className="w-4 h-4 text-gray-600" />
                            Generated Message
                          </h5>
                          <div className="bg-white border-2 border-gray-200 rounded-xl p-5 text-sm leading-relaxed max-h-80 overflow-y-auto shadow-sm">
                            <div className="whitespace-pre-wrap font-medium text-gray-900">
                              {selectedExecution.output.message}
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Error */}
                {selectedExecution.error && (
                  <div className="mt-4 p-3 bg-red-50 rounded">
                    <p className="text-sm text-red-800">{selectedExecution.error}</p>
                  </div>
                )}
              </div>
            ) : (
              <div className="bg-gray-50 rounded-lg p-8 text-center">
                <FileText className="w-12 h-12 text-gray-400 mx-auto mb-2" />
                <p className="text-gray-600">Select an execution to view details</p>
              </div>
            )}
          </div>
        </div>
      ) : activeTab === 'run' ? (
        <div className="max-w-2xl mx-auto">
          <div className="bg-white rounded-lg border p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Run LinkedIn Outreach Workflow</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Conversation Thread
                </label>
                <textarea
                  value={workflowForm.conversation_thread}
                  onChange={(e) => setWorkflowForm({...workflowForm, conversation_thread: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  rows={3}
                  placeholder="Enter the conversation thread or context..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Channel
                </label>
                <select
                  value={workflowForm.channel}
                  onChange={(e) => setWorkflowForm({...workflowForm, channel: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="LinkedIn">LinkedIn</option>
                  <option value="Email">Email</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Prospect Profile URL
                </label>
                <input
                  type="url"
                  value={workflowForm.prospect_profile_url}
                  onChange={(e) => setWorkflowForm({...workflowForm, prospect_profile_url: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="https://linkedin.com/in/example"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Company LinkedIn URL
                </label>
                <input
                  type="url"
                  value={workflowForm.prospect_company_url}
                  onChange={(e) => setWorkflowForm({...workflowForm, prospect_company_url: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="https://linkedin.com/company/example"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Company Website
                </label>
                <input
                  type="url"
                  value={workflowForm.prospect_company_website}
                  onChange={(e) => setWorkflowForm({...workflowForm, prospect_company_website: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="https://example.com"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Qubit Context (Optional)
                </label>
                <textarea
                  value={workflowForm.qubit_context}
                  onChange={(e) => setWorkflowForm({...workflowForm, qubit_context: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  rows={2}
                  placeholder="Additional context about Qubit Capital or investment focus..."
                />
              </div>

              <div className="pt-4">
                <button
                  onClick={runWorkflow}
                  disabled={isRunningWorkflow || !workflowForm.conversation_thread || !workflowForm.prospect_profile_url}
                  className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white px-6 py-3 rounded-lg flex items-center justify-center gap-2 transition-colors"
                >
                  {isRunningWorkflow ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      Running Workflow...
                    </>
                  ) : (
                    <>
                      <Zap className="w-4 h-4" />
                      Run Workflow
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Test Results List */}
          <div className="lg:col-span-2 space-y-4">
            {testResults.map((test) => (
              <div
                key={test.id}
                onClick={() => setSelectedTest(test)}
                className={`bg-white rounded-lg border p-4 cursor-pointer hover:shadow-md transition-shadow ${
                  selectedTest?.id === test.id ? 'ring-2 ring-blue-500' : ''
                }`}
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-3">
                    {getStatusIcon(test.status)}
                    <div>
                      <h3 className="font-medium text-gray-900">{test.test_name}</h3>
                      <p className="text-sm text-gray-600">{test.entity_name}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(test.status)}`}>
                      {test.status}
                    </span>
                    <span className="px-2 py-1 bg-gray-100 text-gray-600 rounded-full text-xs font-medium">
                      {test.test_type}
                    </span>
                  </div>
                </div>

                <div className="mt-3 grid grid-cols-2 gap-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Executed:</span>
                    <span className="font-medium">{formatDate(test.executed_at)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Duration:</span>
                    <span className="font-medium">{test.duration.toFixed(1)}s</span>
                  </div>
                </div>

                {/* Metrics Preview */}
                <div className="mt-3 flex gap-2">
                  {Object.entries(test.metrics || {}).slice(0, 3).map(([key, value]) => (
                    <div key={key} className="bg-gray-50 rounded px-2 py-1">
                      <p className="text-xs text-gray-600">{key}</p>
                      <p className="text-sm font-medium">
                        {typeof value === 'number' ? 
                          (value < 1 ? `${(value * 100).toFixed(0)}%` : value.toFixed(1)) : 
                          value
                        }
                      </p>
                    </div>
                  ))}
                  {Object.keys(test.metrics || {}).length > 3 && (
                    <div className="bg-gray-50 rounded px-2 py-1">
                      <p className="text-xs text-gray-600">+{Object.keys(test.metrics).length - 3} more</p>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Test Details */}
          <div className="lg:col-span-1">
            {selectedTest ? (
              <div className="bg-white rounded-lg border p-4">
                <h3 className="font-semibold text-gray-900 mb-4">Test Details</h3>
                
                {/* Test Info */}
                <div className="mb-4 space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Entity Type:</span>
                    <span className="font-medium capitalize">{selectedTest.entity_type}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Test Type:</span>
                    <span className="font-medium capitalize">{selectedTest.test_type}</span>
                  </div>
                </div>

                {/* Metrics */}
                <div className="mb-4">
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Metrics</h4>
                  <div className="bg-gray-50 rounded p-3 space-y-2">
                    {Object.entries(selectedTest.metrics || {}).map(([key, value]) => (
                      <div key={key} className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">{key}:</span>
                        <div className="flex items-center gap-1">
                          {typeof value === 'number' && value < 1 && (
                            value > 0.8 ? <TrendingUp className="w-3 h-3 text-green-500" /> :
                            value < 0.6 ? <TrendingDown className="w-3 h-3 text-red-500" /> : null
                          )}
                          <span className="font-medium text-sm">
                            {typeof value === 'number' ? 
                              (value < 1 ? `${(value * 100).toFixed(0)}%` : value.toFixed(1)) : 
                              value
                            }
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Test Cases */}
                <div className="mb-4">
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Test Cases</h4>
                  <div className="space-y-2">
                    {selectedTest.test_cases?.map((testCase, index) => (
                      <div key={index} className="bg-gray-50 rounded p-3">
                        <div className="flex items-center justify-between mb-1">
                          <span className="font-medium text-sm">{testCase.name}</span>
                          {getStatusIcon(testCase.status)}
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-xs text-gray-600">Score:</span>
                          <span className="text-xs font-medium">{(testCase.score * 100).toFixed(0)}%</span>
                        </div>
                        <p className="text-xs text-gray-600 mt-1">{testCase.details}</p>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Warnings/Errors */}
                {selectedTest.warnings && selectedTest.warnings.length > 0 && (
                  <div className="mt-4 p-3 bg-yellow-50 rounded">
                    <h4 className="text-sm font-medium text-yellow-800 mb-1">Warnings</h4>
                    {selectedTest.warnings.map((warning, index) => (
                      <p key={index} className="text-xs text-yellow-700">{warning}</p>
                    ))}
                  </div>
                )}
                {selectedTest.errors && selectedTest.errors.length > 0 && (
                  <div className="mt-4 p-3 bg-red-50 rounded">
                    <h4 className="text-sm font-medium text-red-800 mb-1">Errors</h4>
                    {selectedTest.errors.map((error, index) => (
                      <p key={index} className="text-xs text-red-700">{error}</p>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <div className="bg-gray-50 rounded-lg p-8 text-center">
                <BarChart2 className="w-12 h-12 text-gray-400 mx-auto mb-2" />
                <p className="text-gray-600">Select a test result to view details</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Refresh Button */}
      <button
        onClick={() => {
          refetchExecutions();
          refetchTests();
          toast.success('Data refreshed');
        }}
        className="fixed bottom-6 right-6 bg-blue-600 hover:bg-blue-700 text-white p-3 rounded-full shadow-lg transition-colors"
      >
        <RefreshCw className="w-5 h-5" />
      </button>
    </div>
  );
};

export default ExecutionHistory;