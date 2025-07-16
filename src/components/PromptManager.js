import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Editor } from '@monaco-editor/react';
import { 
  Plus, 
  Edit, 
  Trash2, 
  Save, 
  X, 
  Play, 
  Copy, 
  FileText,
  Tag,
  Clock,
  Search,
  Filter,
  Download,
  Upload,
  History,
  MessageSquare
} from 'lucide-react';
import toast from 'react-hot-toast';
import clsx from 'clsx';

// API functions
const api = {
  getPrompts: async () => {
    const response = await fetch('/api/config/prompts');
    if (!response.ok) throw new Error('Failed to fetch prompts');
    return response.json();
  },
  
  getPrompt: async (id) => {
    const response = await fetch(`/api/config/prompts/${id}`);
    if (!response.ok) throw new Error('Failed to fetch prompt');
    return response.json();
  },
  
  savePrompt: async (id, data) => {
    const response = await fetch(`/api/config/prompts/${id}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    if (!response.ok) throw new Error('Failed to save prompt');
    return response.json();
  },
  
  deletePrompt: async (id) => {
    const response = await fetch(`/api/config/prompts/${id}`, {
      method: 'DELETE'
    });
    if (!response.ok) throw new Error('Failed to delete prompt');
    return response.json();
  },
  
  testPrompt: async (id, testData) => {
    const response = await fetch(`/api/config/test/prompt/${id}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(testData)
    });
    if (!response.ok) throw new Error('Failed to test prompt');
    return response.json();
  },
  
  getTestResults: async (id) => {
    const response = await fetch(`/api/config/test-results/prompt/${id}`);
    if (!response.ok) throw new Error('Failed to fetch test results');
    return response.json();
  },
  
  getVersionHistory: async (id) => {
    const response = await fetch(`/api/config/version-history/prompt/${id}`);
    if (!response.ok) throw new Error('Failed to fetch version history');
    return response.json();
  },
  
  rollbackToVersion: async (id, version) => {
    const response = await fetch(`/api/config/rollback/prompt/${id}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ version })
    });
    if (!response.ok) throw new Error('Failed to rollback');
    return response.json();
  }
};

function PromptManager() {
  const [selectedPrompt, setSelectedPrompt] = useState(null);
  const [isEditing, setIsEditing] = useState(false);
  const [editingPrompt, setEditingPrompt] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [channelFilter, setChannelFilter] = useState('all');
  const [testVariables, setTestVariables] = useState({});
  const [showTestPanel, setShowTestPanel] = useState(false);
  const [testResult, setTestResult] = useState(null);
  const [isTestRunning, setIsTestRunning] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [showTestResults, setShowTestResults] = useState(false);

  const queryClient = useQueryClient();

  // Fetch prompts
  const { data: prompts = [], isLoading, error } = useQuery({
    queryKey: ['prompts'],
    queryFn: api.getPrompts
  });

  // Fetch version history
  const { data: versionHistory = [] } = useQuery({
    queryKey: ['prompt-history', selectedPrompt?.id],
    queryFn: () => api.getVersionHistory(selectedPrompt.id),
    enabled: !!selectedPrompt && showHistory
  });

  // Fetch test results
  const { data: testResults = [] } = useQuery({
    queryKey: ['prompt-test-results', selectedPrompt?.id],
    queryFn: () => api.getTestResults(selectedPrompt.id),
    enabled: !!selectedPrompt && showTestResults
  });

  // Save prompt mutation
  const savePromptMutation = useMutation({
    mutationFn: ({ id, data }) => api.savePrompt(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries(['prompts']);
      toast.success('Prompt saved successfully');
      setIsEditing(false);
      setEditingPrompt(null);
    },
    onError: (error) => {
      toast.error(`Failed to save prompt: ${error.message}`);
    }
  });

  // Delete prompt mutation
  const deletePromptMutation = useMutation({
    mutationFn: api.deletePrompt,
    onSuccess: () => {
      queryClient.invalidateQueries(['prompts']);
      toast.success('Prompt deleted successfully');
      setSelectedPrompt(null);
    },
    onError: (error) => {
      toast.error(`Failed to delete prompt: ${error.message}`);
    }
  });

  // Test prompt mutation
  const testPromptMutation = useMutation({
    mutationFn: ({ id, testData }) => api.testPrompt(id, testData),
    onSuccess: (result) => {
      setTestResult(result);
      setIsTestRunning(false);
      queryClient.invalidateQueries(['prompt-test-results', selectedPrompt?.id]);
      toast.success('Prompt tested successfully');
    },
    onError: (error) => {
      setIsTestRunning(false);
      toast.error(`Failed to test prompt: ${error.message}`);
    }
  });

  // Rollback mutation
  const rollbackMutation = useMutation({
    mutationFn: ({ id, version }) => api.rollbackToVersion(id, version),
    onSuccess: () => {
      queryClient.invalidateQueries(['prompts']);
      queryClient.invalidateQueries(['prompt-history', selectedPrompt?.id]);
      toast.success('Prompt rolled back successfully');
      setShowHistory(false);
    },
    onError: (error) => {
      toast.error(`Rollback failed: ${error.message}`);
    }
  });

  // Filter prompts
  const filteredPrompts = prompts.filter(prompt => {
    const matchesSearch = prompt.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         prompt.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = categoryFilter === 'all' || prompt.category === categoryFilter;
    const matchesChannel = channelFilter === 'all' || prompt.channel === channelFilter || !prompt.channel;
    
    return matchesSearch && matchesCategory && matchesChannel;
  });

  // Get unique categories and channels
  const categories = [...new Set(prompts.map(p => p.category).filter(Boolean))];
  const channels = [...new Set(prompts.map(p => p.channel).filter(Boolean))];

  const handleEditPrompt = (prompt) => {
    setEditingPrompt({ ...prompt });
    setIsEditing(true);
  };

  const handleSavePrompt = () => {
    if (!editingPrompt.name || !editingPrompt.template) {
      toast.error('Name and template are required');
      return;
    }

    const promptData = {
      name: editingPrompt.name,
      description: editingPrompt.description || '',
      template: editingPrompt.template,
      variables: editingPrompt.variables || [],
      category: editingPrompt.category,
      channel: editingPrompt.channel || null
    };

    savePromptMutation.mutate({ 
      id: editingPrompt.id || `prompt_${Date.now()}`, 
      data: promptData 
    });
  };

  const handleDeletePrompt = (prompt) => {
    if (window.confirm(`Are you sure you want to delete "${prompt.name}"?`)) {
      deletePromptMutation.mutate(prompt.id);
    }
  };

  const handleTestPrompt = () => {
    if (!selectedPrompt) return;
    
    setIsTestRunning(true);
    testPromptMutation.mutate({
      id: selectedPrompt.id,
      testData: {
        input_data: {
          variables: testVariables
        }
      }
    });
  };

  const handleRollback = (version) => {
    if (!selectedPrompt) return;
    
    rollbackMutation.mutate({
      id: selectedPrompt.id,
      version: version
    });
  };

  const handleCreateNew = () => {
    setEditingPrompt({
      id: null,
      name: '',
      description: '',
      template: '',
      variables: [],
      category: 'profile_enrichment',
      channel: null
    });
    setIsEditing(true);
  };

  const extractVariables = (template) => {
    const matches = template.match(/\{([^}]+)\}/g) || [];
    return matches.map(match => match.slice(1, -1));
  };

  const handleTemplateChange = (value) => {
    const variables = extractVariables(value);
    setEditingPrompt(prev => ({
      ...prev,
      template: value,
      variables
    }));
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="loading-spinner"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <div className="text-error-600 mb-4">Error loading prompts</div>
        <button 
          onClick={() => queryClient.invalidateQueries(['prompts'])}
          className="btn-primary"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-secondary-900">Prompt Templates</h1>
          <p className="text-secondary-600">Manage and edit your AI prompt templates</p>
        </div>
        <button 
          onClick={handleCreateNew}
          className="btn-primary flex items-center space-x-2"
        >
          <Plus className="w-4 h-4" />
          <span>New Prompt</span>
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-4 mb-6">
        <div className="flex-1 min-w-64">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-secondary-400 w-4 h-4" />
            <input
              type="text"
              placeholder="Search prompts..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="input pl-10"
            />
          </div>
        </div>
        
        <select
          value={categoryFilter}
          onChange={(e) => setCategoryFilter(e.target.value)}
          className="input w-48"
        >
          <option value="all">All Categories</option>
          {categories.map(category => (
            <option key={category} value={category}>
              {category ? category.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()) : 'Uncategorized'}
            </option>
          ))}
        </select>
        
        <select
          value={channelFilter}
          onChange={(e) => setChannelFilter(e.target.value)}
          className="input w-48"
        >
          <option value="all">All Channels</option>
          <option value="linkedin">LinkedIn</option>
          <option value="email">Email</option>
        </select>
      </div>

      {/* Main content */}
      <div className="flex-1 grid grid-cols-12 gap-6">
        {/* Prompt list */}
        <div className="col-span-4 space-y-4">
          {filteredPrompts.map((prompt) => (
            <div
              key={prompt.id}
              className={clsx(
                'card cursor-pointer transition-all hover:shadow-md',
                selectedPrompt?.id === prompt.id && 'ring-2 ring-primary-500'
              )}
              onClick={() => setSelectedPrompt(prompt)}
            >
              <div className="card-body">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h3 className="font-semibold text-secondary-900">{prompt.name}</h3>
                    <p className="text-sm text-secondary-600 mt-1">{prompt.description}</p>
                    
                    <div className="flex items-center space-x-2 mt-3">
                      <span className="badge-primary">
                        {prompt.category ? prompt.category.replace('_', ' ') : 'Uncategorized'}
                      </span>
                      {prompt.channel && (
                        <span className="badge-secondary">{prompt.channel}</span>
                      )}
                    </div>
                  </div>
                  
                  <div className="flex space-x-1">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleEditPrompt(prompt);
                      }}
                      className="p-1 text-secondary-400 hover:text-primary-600"
                    >
                      <Edit className="w-4 h-4" />
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeletePrompt(prompt);
                      }}
                      className="p-1 text-secondary-400 hover:text-error-600"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
                
                <div className="flex items-center justify-between mt-4 text-xs text-secondary-500">
                  <span>v{prompt.version}</span>
                  <span>{new Date(prompt.updated_at).toLocaleDateString()}</span>
                </div>
              </div>
            </div>
          ))}
          
          {filteredPrompts.length === 0 && (
            <div className="text-center py-12">
              <FileText className="w-12 h-12 text-secondary-400 mx-auto mb-4" />
              <p className="text-secondary-600">No prompts found</p>
            </div>
          )}
        </div>

        {/* Prompt details/editor */}
        <div className="col-span-8">
          {isEditing ? (
            <div className="card h-full">
              <div className="card-header">
                <div className="flex items-center justify-between">
                  <h2 className="text-lg font-semibold">
                    {editingPrompt.id ? 'Edit Prompt' : 'New Prompt'}
                  </h2>
                  <div className="flex space-x-2">
                    <button
                      onClick={handleSavePrompt}
                      disabled={savePromptMutation.isLoading}
                      className="btn-primary flex items-center space-x-2"
                    >
                      <Save className="w-4 h-4" />
                      <span>Save</span>
                    </button>
                    <button
                      onClick={() => {
                        setIsEditing(false);
                        setEditingPrompt(null);
                      }}
                      className="btn-ghost"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
              
              <div className="card-body flex flex-col space-y-4">
                {/* Basic info */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-secondary-700 mb-1">
                      Name *
                    </label>
                    <input
                      type="text"
                      value={editingPrompt.name}
                      onChange={(e) => setEditingPrompt(prev => ({ ...prev, name: e.target.value }))}
                      className="input"
                      placeholder="Enter prompt name"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-secondary-700 mb-1">
                      Category *
                    </label>
                    <select
                      value={editingPrompt.category}
                      onChange={(e) => setEditingPrompt(prev => ({ ...prev, category: e.target.value }))}
                      className="input"
                    >
                      <option value="profile_enrichment">Profile Enrichment</option>
                      <option value="thread_analysis">Thread Analysis</option>
                      <option value="reply_generation">Reply Generation</option>
                      <option value="faq_answering">FAQ Answering</option>
                      <option value="escalation">Escalation</option>
                    </select>
                  </div>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-secondary-700 mb-1">
                      Description
                    </label>
                    <input
                      type="text"
                      value={editingPrompt.description}
                      onChange={(e) => setEditingPrompt(prev => ({ ...prev, description: e.target.value }))}
                      className="input"
                      placeholder="Enter prompt description"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-secondary-700 mb-1">
                      Channel
                    </label>
                    <select
                      value={editingPrompt.channel || ''}
                      onChange={(e) => setEditingPrompt(prev => ({ ...prev, channel: e.target.value || null }))}
                      className="input"
                    >
                      <option value="">Both</option>
                      <option value="linkedin">LinkedIn</option>
                      <option value="email">Email</option>
                    </select>
                  </div>
                </div>

                {/* Template editor */}
                <div className="flex-1">
                  <label className="block text-sm font-medium text-secondary-700 mb-1">
                    Template *
                  </label>
                  <div className="monaco-editor-container flex-1">
                    <Editor
                      height="400px"
                      defaultLanguage="markdown"
                      value={editingPrompt.template}
                      onChange={handleTemplateChange}
                      theme="vs-light"
                      options={{
                        minimap: { enabled: false },
                        scrollBeyondLastLine: false,
                        fontSize: 14,
                        wordWrap: 'on',
                        lineNumbers: 'on',
                        folding: true,
                        bracketMatching: 'always'
                      }}
                    />
                  </div>
                </div>

                {/* Variables */}
                {editingPrompt.variables && editingPrompt.variables.length > 0 && (
                  <div>
                    <label className="block text-sm font-medium text-secondary-700 mb-2">
                      Variables
                    </label>
                    <div className="flex flex-wrap gap-2">
                      {editingPrompt.variables.map((variable, index) => (
                        <span key={index} className="prompt-variable">
                          {variable}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ) : selectedPrompt ? (
            <div className="card h-full">
              <div className="card-header">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-lg font-semibold">{selectedPrompt.name}</h2>
                    <p className="text-sm text-secondary-600">{selectedPrompt.description}</p>
                  </div>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => setShowTestResults(!showTestResults)}
                      className="btn-secondary flex items-center space-x-2"
                    >
                      <MessageSquare className="w-4 h-4" />
                      <span>Results</span>
                    </button>
                    <button
                      onClick={() => setShowHistory(!showHistory)}
                      className="btn-secondary flex items-center space-x-2"
                    >
                      <History className="w-4 h-4" />
                      <span>History</span>
                    </button>
                    <button
                      onClick={() => setShowTestPanel(!showTestPanel)}
                      className="btn-secondary flex items-center space-x-2"
                    >
                      <Play className="w-4 h-4" />
                      <span>Test</span>
                    </button>
                    <button
                      onClick={() => handleEditPrompt(selectedPrompt)}
                      className="btn-primary flex items-center space-x-2"
                    >
                      <Edit className="w-4 h-4" />
                      <span>Edit</span>
                    </button>
                  </div>
                </div>
              </div>
              
              <div className="card-body flex flex-col space-y-4">
                {/* Metadata */}
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-secondary-700 mb-1">
                      Category
                    </label>
                    <span className="badge-primary">
                      {selectedPrompt.category ? selectedPrompt.category.replace('_', ' ') : 'Uncategorized'}
                    </span>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-secondary-700 mb-1">
                      Channel
                    </label>
                    <span className="badge-secondary">
                      {selectedPrompt.channel || 'Both'}
                    </span>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-secondary-700 mb-1">
                      Version
                    </label>
                    <span className="text-sm text-secondary-900">v{selectedPrompt.version}</span>
                  </div>
                </div>

                {/* Template preview */}
                <div className="flex-1">
                  <label className="block text-sm font-medium text-secondary-700 mb-1">
                    Template
                  </label>
                  <div className="monaco-editor-container flex-1">
                    <Editor
                      height="400px"
                      defaultLanguage="markdown"
                      value={selectedPrompt.template}
                      theme="vs-light"
                      options={{
                        readOnly: true,
                        minimap: { enabled: false },
                        scrollBeyondLastLine: false,
                        fontSize: 14,
                        wordWrap: 'on',
                        lineNumbers: 'on'
                      }}
                    />
                  </div>
                </div>

                {/* Variables */}
                {selectedPrompt.variables && selectedPrompt.variables.length > 0 && (
                  <div>
                    <label className="block text-sm font-medium text-secondary-700 mb-2">
                      Variables
                    </label>
                    <div className="flex flex-wrap gap-2">
                      {selectedPrompt.variables.map((variable, index) => (
                        <span key={index} className="prompt-variable">
                          {variable}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Version History panel */}
                {showHistory && (
                  <div className="border-t pt-4">
                    <h3 className="text-sm font-medium text-secondary-700 mb-3">Version History</h3>
                    <div className="space-y-2">
                      {versionHistory.map((version) => (
                        <div key={version.id} className="flex items-center justify-between p-2 bg-secondary-50 rounded">
                          <div className="flex-1">
                            <div className="flex items-center space-x-2">
                              <span className="font-medium">v{version.version}</span>
                              <span className="text-sm text-secondary-500">
                                {new Date(version.created_at).toLocaleString()}
                              </span>
                            </div>
                            {version.change_description && (
                              <p className="text-sm text-secondary-600 mt-1">{version.change_description}</p>
                            )}
                          </div>
                          <button
                            onClick={() => handleRollback(version.version)}
                            className="px-2 py-1 text-xs bg-primary-100 text-primary-700 rounded hover:bg-primary-200"
                          >
                            Rollback
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Test Results panel */}
                {showTestResults && (
                  <div className="border-t pt-4">
                    <h3 className="text-sm font-medium text-secondary-700 mb-3">Test Results</h3>
                    <div className="space-y-3">
                      {testResults.map((result) => (
                        <div key={result.id} className="p-3 bg-secondary-50 rounded">
                          <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center space-x-2">
                              <span className={`text-sm font-medium ${result.status === 'success' ? 'text-success-600' : 'text-error-600'}`}>
                                {result.status === 'success' ? 'Success' : 'Failed'}
                              </span>
                            </div>
                            <div className="flex items-center space-x-2 text-sm text-secondary-500">
                              <Clock className="w-4 h-4" />
                              <span>{result.execution_time.toFixed(2)}s</span>
                              <span>{new Date(result.created_at).toLocaleString()}</span>
                            </div>
                          </div>
                          <div className="text-sm">
                            <p className="text-secondary-600 mb-1">Input:</p>
                            <pre className="bg-secondary-100 p-2 rounded text-xs overflow-x-auto">
                              {result.test_input}
                            </pre>
                            <p className="text-secondary-600 mb-1 mt-2">Output:</p>
                            <pre className="bg-secondary-100 p-2 rounded text-xs overflow-x-auto">
                              {result.test_output}
                            </pre>
                            {result.error_message && (
                              <>
                                <p className="text-error-600 mb-1 mt-2">Error:</p>
                                <pre className="bg-error-50 p-2 rounded text-xs overflow-x-auto text-error-700">
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

                {/* Test panel */}
                {showTestPanel && (
                  <div className="border-t pt-4">
                    <h3 className="text-sm font-medium text-secondary-700 mb-3">Test Variables</h3>
                    <div className="grid grid-cols-2 gap-4 mb-4">
                      {selectedPrompt.variables?.map((variable) => (
                        <div key={variable}>
                          <label className="block text-sm text-secondary-600 mb-1">
                            {variable}
                          </label>
                          <input
                            type="text"
                            value={testVariables[variable] || ''}
                            onChange={(e) => setTestVariables(prev => ({
                              ...prev,
                              [variable]: e.target.value
                            }))}
                            className="input"
                            placeholder={`Enter ${variable}`}
                          />
                        </div>
                      ))}
                    </div>
                    
                    <button
                      onClick={handleTestPrompt}
                      disabled={isTestRunning}
                      className="btn-primary mb-4"
                    >
                      {isTestRunning ? 'Testing...' : 'Test Prompt'}
                    </button>
                    
                    {testResult && (
                      <div>
                        <h4 className="text-sm font-medium text-secondary-700 mb-2">Test Result</h4>
                        <div className="bg-secondary-50 p-4 rounded-lg">
                          <div className="flex items-center space-x-2 mb-2">
                            <span className={`text-sm font-medium ${testResult.status === 'success' ? 'text-success-600' : 'text-error-600'}`}>
                              {testResult.status === 'success' ? 'Success' : 'Failed'}
                            </span>
                            <span className="text-sm text-secondary-500">
                              ({testResult.execution_time.toFixed(2)}s)
                            </span>
                          </div>
                          <pre className="text-sm text-secondary-900 whitespace-pre-wrap">
                            {testResult.result.rendered_prompt || testResult.result}
                          </pre>
                          {testResult.error_message && (
                            <div className="mt-2">
                              <p className="text-error-600 text-sm font-medium">Error:</p>
                              <pre className="bg-error-50 p-2 rounded text-sm text-error-700 whitespace-pre-wrap">
                                {testResult.error_message}
                              </pre>
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="card h-full">
              <div className="card-body flex items-center justify-center">
                <div className="text-center">
                  <MessageSquare className="w-12 h-12 text-secondary-400 mx-auto mb-4" />
                  <p className="text-secondary-600">Select a prompt to view details</p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default PromptManager; 