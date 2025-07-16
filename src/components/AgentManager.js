import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'react-hot-toast';
import { Play, History, RotateCcw, Settings, TestTube, Clock, CheckCircle, XCircle, Eye, Edit3, Save, X } from 'lucide-react';
import AgentModelSelector from './AgentModelSelector';

// API functions
const api = {
  getAgents: async () => {
    const response = await fetch('/api/config/agents');
    if (!response.ok) throw new Error('Failed to fetch agents');
    return response.json();
  },
  
  getAgent: async (id) => {
    const response = await fetch(`/api/config/agents/${id}`);
    if (!response.ok) throw new Error('Failed to fetch agent');
    return response.json();
  },
  
  saveAgent: async (id, data) => {
    const response = await fetch(`/api/config/agents/${id}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    if (!response.ok) throw new Error('Failed to save agent');
    return response.json();
  },
  
  deleteAgent: async (id) => {
    const response = await fetch(`/api/config/agents/${id}`, {
      method: 'DELETE'
    });
    if (!response.ok) throw new Error('Failed to delete agent');
    return response.json();
  },
  
  testAgent: async (id, testData) => {
    const response = await fetch(`/api/config/test/agent/${id}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(testData)
    });
    if (!response.ok) throw new Error('Failed to test agent');
    return response.json();
  },
  
  getTestResults: async (id) => {
    const response = await fetch(`/api/config/test-results/agent/${id}`);
    if (!response.ok) throw new Error('Failed to fetch test results');
    return response.json();
  },
  
  getVersionHistory: async (id) => {
    const response = await fetch(`/api/config/version-history/agent/${id}`);
    if (!response.ok) throw new Error('Failed to fetch version history');
    return response.json();
  },
  
  rollbackToVersion: async (id, version) => {
    const response = await fetch(`/api/config/rollback/agent/${id}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ version })
    });
    if (!response.ok) throw new Error('Failed to rollback');
    return response.json();
  }
};

function AgentManager() {
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [isEditing, setIsEditing] = useState(false);
  const [editingAgent, setEditingAgent] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [showTestPanel, setShowTestPanel] = useState(false);
  const [testInput, setTestInput] = useState({
    task_description: '',
    expected_output: '',
    variables: {}
  });
  const [testResult, setTestResult] = useState(null);
  const [isTestRunning, setIsTestRunning] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [showTestResults, setShowTestResults] = useState(false);

  const queryClient = useQueryClient();

  // Fetch agents
  const { data: agents = [], isLoading, error } = useQuery({
    queryKey: ['agents'],
    queryFn: api.getAgents
  });

  // Fetch version history
  const { data: versionHistory = [] } = useQuery({
    queryKey: ['agent-history', selectedAgent?.id],
    queryFn: () => api.getVersionHistory(selectedAgent.id),
    enabled: !!selectedAgent && showHistory
  });

  // Fetch test results
  const { data: testResults = [] } = useQuery({
    queryKey: ['agent-test-results', selectedAgent?.id],
    queryFn: () => api.getTestResults(selectedAgent.id),
    enabled: !!selectedAgent && showTestResults
  });

  // Save agent mutation
  const saveAgentMutation = useMutation({
    mutationFn: ({ id, data }) => api.saveAgent(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries(['agents']);
      toast.success('Agent saved successfully');
      setIsEditing(false);
      setEditingAgent(null);
    },
    onError: (error) => {
      toast.error(`Failed to save agent: ${error.message}`);
    }
  });

  // Delete agent mutation
  const deleteAgentMutation = useMutation({
    mutationFn: api.deleteAgent,
    onSuccess: () => {
      queryClient.invalidateQueries(['agents']);
      toast.success('Agent deleted successfully');
      setSelectedAgent(null);
    },
    onError: (error) => {
      toast.error(`Failed to delete agent: ${error.message}`);
    }
  });

  // Test agent mutation
  const testAgentMutation = useMutation({
    mutationFn: ({ id, testData }) => api.testAgent(id, testData),
    onSuccess: (result) => {
      setTestResult(result);
      setIsTestRunning(false);
      queryClient.invalidateQueries(['agent-test-results', selectedAgent?.id]);
      toast.success('Agent test completed');
    },
    onError: (error) => {
      setIsTestRunning(false);
      toast.error(`Test failed: ${error.message}`);
    }
  });

  // Rollback mutation
  const rollbackMutation = useMutation({
    mutationFn: ({ id, version }) => api.rollbackToVersion(id, version),
    onSuccess: () => {
      queryClient.invalidateQueries(['agents']);
      queryClient.invalidateQueries(['agent-history', selectedAgent?.id]);
      toast.success('Agent rolled back successfully');
      setShowHistory(false);
    },
    onError: (error) => {
      toast.error(`Rollback failed: ${error.message}`);
    }
  });

  const filteredAgents = agents.filter(agent =>
    agent.role.toLowerCase().includes(searchTerm.toLowerCase()) ||
    agent.goal.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleEdit = (agent) => {
    setEditingAgent({ ...agent });
    setIsEditing(true);
  };

  const handleSave = () => {
    if (!editingAgent.role || !editingAgent.goal || !editingAgent.backstory) {
      toast.error('Please fill in all required fields');
      return;
    }

    saveAgentMutation.mutate({
      id: editingAgent.id,
      data: {
        role: editingAgent.role,
        goal: editingAgent.goal,
        backstory: editingAgent.backstory,
        verbose: editingAgent.verbose,
        memory: editingAgent.memory,
        max_iter: editingAgent.max_iter,
        allow_delegation: editingAgent.allow_delegation,
        temperature: editingAgent.temperature,
        max_tokens: editingAgent.max_tokens
      }
    });
  };

  const handleTest = () => {
    if (!selectedAgent) return;
    
    setIsTestRunning(true);
    testAgentMutation.mutate({
      id: selectedAgent.id,
      testData: {
        input_data: testInput
      }
    });
  };

  const handleRollback = (version) => {
    if (!selectedAgent) return;
    
    rollbackMutation.mutate({
      id: selectedAgent.id,
      version: version
    });
  };

  if (isLoading) return <div className="p-6">Loading agents...</div>;
  if (error) return <div className="p-6 text-red-600">Error: {error.message}</div>;

  return (
    <div className="flex h-full bg-gray-50">
      {/* Agent List */}
      <div className="w-1/3 bg-white border-r border-gray-200 flex flex-col">
        <div className="p-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Agents</h2>
          <input
            type="text"
            placeholder="Search agents..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        
        <div className="flex-1 overflow-y-auto">
          {filteredAgents.map((agent) => (
            <div
              key={agent.id}
              onClick={() => setSelectedAgent(agent)}
              className={`p-4 border-b border-gray-100 cursor-pointer hover:bg-gray-50 ${
                selectedAgent?.id === agent.id ? 'bg-blue-50 border-blue-200' : ''
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex-1 min-w-0">
                  <h3 className="font-medium text-gray-900 truncate">{agent.role}</h3>
                  <p className="text-sm text-gray-500 truncate">{agent.goal}</p>
                  <div className="flex items-center mt-1">
                    <span className="text-xs text-gray-400">v{agent.version}</span>
                    <span className="text-xs text-gray-400 ml-2">
                      {new Date(agent.updated_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
                <div className="flex items-center space-x-1">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setSelectedAgent(agent);
                      setShowTestPanel(true);
                    }}
                    className="p-1 text-green-600 hover:text-green-800"
                    title="Test Agent"
                  >
                    <TestTube size={16} />
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleEdit(agent);
                    }}
                    className="p-1 text-blue-600 hover:text-blue-800"
                    title="Edit Agent"
                  >
                    <Edit3 size={16} />
                  </button>
                  <AgentModelSelector agent={agent} onChange={() => queryClient.invalidateQueries(['agents'])} />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Agent Details */}
      <div className="flex-1 flex flex-col">
        {selectedAgent ? (
          <>
            {/* Header */}
            <div className="bg-white border-b border-gray-200 p-4">
              <div className="flex items-center justify-between">
                <div>
                  <h1 className="text-xl font-semibold text-gray-900">{selectedAgent.role}</h1>
                  <p className="text-sm text-gray-500">Agent Configuration</p>
                </div>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => setShowTestResults(!showTestResults)}
                    className="px-3 py-1 text-sm bg-green-100 text-green-700 rounded-md hover:bg-green-200"
                  >
                    <TestTube size={16} className="inline mr-1" />
                    Test Results
                  </button>
                  <button
                    onClick={() => setShowHistory(!showHistory)}
                    className="px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200"
                  >
                    <History size={16} className="inline mr-1" />
                    History
                  </button>
                  <button
                    onClick={() => setShowTestPanel(!showTestPanel)}
                    className="px-3 py-1 text-sm bg-purple-100 text-purple-700 rounded-md hover:bg-purple-200"
                  >
                    <Play size={16} className="inline mr-1" />
                    Test
                  </button>
                  <button
                    onClick={() => handleEdit(selectedAgent)}
                    className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200"
                  >
                    <Edit3 size={16} className="inline mr-1" />
                    Edit
                  </button>
                </div>
              </div>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto">
              {showHistory && (
                <div className="bg-white border-b border-gray-200 p-4">
                  <h3 className="font-medium text-gray-900 mb-3">Version History</h3>
                  <div className="space-y-2">
                    {versionHistory.map((version) => (
                      <div key={version.id} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                        <div className="flex-1">
                          <div className="flex items-center space-x-2">
                            <span className="font-medium">v{version.version}</span>
                            <span className="text-sm text-gray-500">
                              {new Date(version.created_at).toLocaleString()}
                            </span>
                          </div>
                          {version.change_description && (
                            <p className="text-sm text-gray-600 mt-1">{version.change_description}</p>
                          )}
                        </div>
                        <button
                          onClick={() => handleRollback(version.version)}
                          className="px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
                        >
                          <RotateCcw size={12} className="inline mr-1" />
                          Rollback
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {showTestResults && (
                <div className="bg-white border-b border-gray-200 p-4">
                  <h3 className="font-medium text-gray-900 mb-3">Test Results</h3>
                  <div className="space-y-3">
                    {testResults.map((result) => (
                      <div key={result.id} className="p-3 bg-gray-50 rounded">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center space-x-2">
                            {result.status === 'success' ? (
                              <CheckCircle size={16} className="text-green-500" />
                            ) : (
                              <XCircle size={16} className="text-red-500" />
                            )}
                            <span className="text-sm font-medium">
                              {result.status === 'success' ? 'Success' : 'Failed'}
                            </span>
                          </div>
                          <div className="flex items-center space-x-2 text-sm text-gray-500">
                            <Clock size={14} />
                            <span>{result.execution_time.toFixed(2)}s</span>
                            <span>{new Date(result.created_at).toLocaleString()}</span>
                          </div>
                        </div>
                        <div className="text-sm">
                          <p className="text-gray-600 mb-1">Input:</p>
                          <pre className="bg-gray-100 p-2 rounded text-xs overflow-x-auto">
                            {result.test_input}
                          </pre>
                          <p className="text-gray-600 mb-1 mt-2">Output:</p>
                          <pre className="bg-gray-100 p-2 rounded text-xs overflow-x-auto">
                            {result.test_output}
                          </pre>
                          {result.error_message && (
                            <>
                              <p className="text-red-600 mb-1 mt-2">Error:</p>
                              <pre className="bg-red-50 p-2 rounded text-xs overflow-x-auto text-red-700">
                                {result.error_message}
                              </pre>
                            </>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {showTestPanel && (
                <div className="bg-white border-b border-gray-200 p-4">
                  <h3 className="font-medium text-gray-900 mb-3">Test Agent</h3>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Task Description
                      </label>
                      <textarea
                        value={testInput.task_description}
                        onChange={(e) => setTestInput({...testInput, task_description: e.target.value})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        rows="3"
                        placeholder="Enter the task description for the agent..."
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Expected Output
                      </label>
                      <input
                        type="text"
                        value={testInput.expected_output}
                        onChange={(e) => setTestInput({...testInput, expected_output: e.target.value})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="Expected output format..."
                      />
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={handleTest}
                        disabled={isTestRunning || !testInput.task_description}
                        className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center space-x-2"
                      >
                        <Play size={16} />
                        <span>{isTestRunning ? 'Testing...' : 'Run Test'}</span>
                      </button>
                      <button
                        onClick={() => setShowTestPanel(false)}
                        className="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400"
                      >
                        Cancel
                      </button>
                    </div>
                    
                    {testResult && (
                      <div className="mt-4 p-4 bg-gray-50 rounded">
                        <h4 className="font-medium text-gray-900 mb-2">Test Result</h4>
                        <div className="flex items-center space-x-2 mb-2">
                          {testResult.status === 'success' ? (
                            <CheckCircle size={16} className="text-green-500" />
                          ) : (
                            <XCircle size={16} className="text-red-500" />
                          )}
                          <span className="text-sm font-medium">
                            {testResult.status === 'success' ? 'Success' : 'Failed'}
                          </span>
                          <span className="text-sm text-gray-500">
                            ({testResult.execution_time.toFixed(2)}s)
                          </span>
                        </div>
                        <pre className="bg-white p-3 rounded border text-sm overflow-x-auto">
                          {testResult.result}
                        </pre>
                        {testResult.error_message && (
                          <div className="mt-2">
                            <p className="text-red-600 text-sm font-medium">Error:</p>
                            <pre className="bg-red-50 p-2 rounded text-sm text-red-700 overflow-x-auto">
                              {testResult.error_message}
                            </pre>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Agent Configuration Display */}
              <div className="p-4 bg-white">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <h3 className="font-medium text-gray-900 mb-3">Basic Information</h3>
                    <div className="space-y-3">
                      <div>
                        <label className="block text-sm font-medium text-gray-700">Role</label>
                        <p className="text-sm text-gray-900">{selectedAgent.role}</p>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700">Goal</label>
                        <p className="text-sm text-gray-900">{selectedAgent.goal}</p>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700">Backstory</label>
                        <p className="text-sm text-gray-900 whitespace-pre-wrap">{selectedAgent.backstory}</p>
                      </div>
                    </div>
                  </div>
                  
                  <div>
                    <h3 className="font-medium text-gray-900 mb-3">Configuration</h3>
                    <div className="space-y-3">
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700">Verbose</label>
                          <p className="text-sm text-gray-900">{selectedAgent.verbose ? 'Yes' : 'No'}</p>
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700">Memory</label>
                          <p className="text-sm text-gray-900">{selectedAgent.memory ? 'Yes' : 'No'}</p>
                        </div>
                      </div>
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700">Max Iterations</label>
                          <p className="text-sm text-gray-900">{selectedAgent.max_iter}</p>
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700">Allow Delegation</label>
                          <p className="text-sm text-gray-900">{selectedAgent.allow_delegation ? 'Yes' : 'No'}</p>
                        </div>
                      </div>
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700">Temperature</label>
                          <p className="text-sm text-gray-900">{selectedAgent.temperature}</p>
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700">Max Tokens</label>
                          <p className="text-sm text-gray-900">{selectedAgent.max_tokens}</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center text-gray-500">
            <div className="text-center">
              <Settings size={48} className="mx-auto mb-4 text-gray-400" />
              <p>Select an agent to view details</p>
            </div>
          </div>
        )}
      </div>

      {/* Edit Modal */}
      {isEditing && editingAgent && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold">Edit Agent</h2>
                <button
                  onClick={() => setIsEditing(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X size={24} />
                </button>
              </div>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Role *
                  </label>
                  <input
                    type="text"
                    value={editingAgent.role}
                    onChange={(e) => setEditingAgent({...editingAgent, role: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Goal *
                  </label>
                  <textarea
                    value={editingAgent.goal}
                    onChange={(e) => setEditingAgent({...editingAgent, goal: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    rows="3"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Backstory *
                  </label>
                  <textarea
                    value={editingAgent.backstory}
                    onChange={(e) => setEditingAgent({...editingAgent, backstory: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    rows="6"
                  />
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Max Iterations
                    </label>
                    <input
                      type="number"
                      value={editingAgent.max_iter}
                      onChange={(e) => setEditingAgent({...editingAgent, max_iter: parseInt(e.target.value)})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Temperature
                    </label>
                    <input
                      type="number"
                      step="0.1"
                      min="0"
                      max="2"
                      value={editingAgent.temperature}
                      onChange={(e) => setEditingAgent({...editingAgent, temperature: parseFloat(e.target.value)})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Max Tokens
                    </label>
                    <input
                      type="number"
                      value={editingAgent.max_tokens}
                      onChange={(e) => setEditingAgent({...editingAgent, max_tokens: parseInt(e.target.value)})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="verbose"
                      checked={editingAgent.verbose}
                      onChange={(e) => setEditingAgent({...editingAgent, verbose: e.target.checked})}
                      className="mr-2"
                    />
                    <label htmlFor="verbose" className="text-sm font-medium text-gray-700">
                      Verbose
                    </label>
                  </div>
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="memory"
                      checked={editingAgent.memory}
                      onChange={(e) => setEditingAgent({...editingAgent, memory: e.target.checked})}
                      className="mr-2"
                    />
                    <label htmlFor="memory" className="text-sm font-medium text-gray-700">
                      Memory
                    </label>
                  </div>
                </div>
                
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="allow_delegation"
                    checked={editingAgent.allow_delegation}
                    onChange={(e) => setEditingAgent({...editingAgent, allow_delegation: e.target.checked})}
                    className="mr-2"
                  />
                  <label htmlFor="allow_delegation" className="text-sm font-medium text-gray-700">
                    Allow Delegation
                  </label>
                </div>
              </div>
              
              <div className="flex justify-end space-x-2 mt-6">
                <button
                  onClick={() => setIsEditing(false)}
                  className="px-4 py-2 text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSave}
                  disabled={saveAgentMutation.isPending}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-blue-400 flex items-center space-x-2"
                >
                  <Save size={16} />
                  <span>{saveAgentMutation.isPending ? 'Saving...' : 'Save'}</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default AgentManager; 