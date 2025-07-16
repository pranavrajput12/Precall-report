import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { Bot, Zap, Settings, ArrowRight, CheckCircle, AlertCircle, Edit, Save, X } from 'lucide-react';

const fetchModelAssignments = async () => {
  const res = await fetch('/api/config/model-assignments');
  if (!res.ok) throw new Error('Failed to fetch model assignments');
  return res.json();
};

const fetchAgents = async () => {
  const res = await fetch('/api/config/agents');
  if (!res.ok) throw new Error('Failed to fetch agents');
  return res.json();
};

const fetchModels = async () => {
  const res = await fetch('/api/config/models');
  if (!res.ok) throw new Error('Failed to fetch models');
  return res.json();
};

const updateAssignment = async ({ agentId, modelId }) => {
  const res = await fetch(`/api/config/model-assignments/${agentId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ modelId }),
  });
  if (!res.ok) throw new Error('Failed to update assignment');
  return res.json();
};

export default function ModelAssignments() {
  const queryClient = useQueryClient();
  const [editingAgent, setEditingAgent] = useState(null);
  const [selectedModel, setSelectedModel] = useState('');

  const { data: assignments = [], isLoading: assignmentsLoading } = useQuery({
    queryKey: ['model-assignments'],
    queryFn: fetchModelAssignments,
  });

  const { data: agents = [], isLoading: agentsLoading } = useQuery({
    queryKey: ['agents'],
    queryFn: fetchAgents,
  });

  const { data: models = [], isLoading: modelsLoading } = useQuery({
    queryKey: ['models'],
    queryFn: fetchModels,
  });

  const updateMutation = useMutation({
    mutationFn: updateAssignment,
    onSuccess: () => {
      toast.success('Model assignment updated successfully!');
      queryClient.invalidateQueries({ queryKey: ['model-assignments'] });
      setEditingAgent(null);
      setSelectedModel('');
    },
    onError: (e) => toast.error(e.message),
  });

  const getAgentById = (agentId) => agents.find(a => a.id === agentId);
  const getModelById = (modelId) => models.find(m => m.id === modelId);

  const handleEdit = (assignment) => {
    setEditingAgent(assignment.agent_id);
    setSelectedModel(assignment.model_id);
  };

  const handleSave = (agentId) => {
    if (!selectedModel) {
      toast.error('Please select a model');
      return;
    }
    updateMutation.mutate({ agentId, modelId: selectedModel });
  };

  const handleCancel = () => {
    setEditingAgent(null);
    setSelectedModel('');
  };

  if (assignmentsLoading || agentsLoading || modelsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Model Assignments</h1>
        <p className="text-gray-600 mt-2">Assign AI models to your agents for optimal performance</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Assignments</p>
              <p className="text-2xl font-bold text-gray-900">{assignments.length}</p>
            </div>
            <Bot className="w-8 h-8 text-blue-500" />
          </div>
        </div>
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Active Agents</p>
              <p className="text-2xl font-bold text-green-600">{agents.filter(a => a.status === 'active').length}</p>
            </div>
            <CheckCircle className="w-8 h-8 text-green-500" />
          </div>
        </div>
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Available Models</p>
              <p className="text-2xl font-bold text-purple-600">{models.length}</p>
            </div>
            <Zap className="w-8 h-8 text-purple-500" />
          </div>
        </div>
      </div>

      {/* Assignments List */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Agent-Model Assignments</h2>
        </div>
        <div className="divide-y divide-gray-200">
          {assignments.map((assignment) => {
            const agent = getAgentById(assignment.agent_id);
            const model = getModelById(assignment.model_id);
            const isEditing = editingAgent === assignment.agent_id;

            return (
              <div key={assignment.agent_id} className="p-6 hover:bg-gray-50 transition-colors">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-6 flex-1">
                    {/* Agent Info */}
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                        <Bot className="w-5 h-5 text-blue-600" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-gray-900">{agent?.name || 'Unknown Agent'}</h3>
                        <p className="text-sm text-gray-600">{agent?.role || 'No role'}</p>
                      </div>
                    </div>

                    {/* Arrow */}
                    <ArrowRight className="w-5 h-5 text-gray-400" />

                    {/* Model Info */}
                    <div className="flex items-center gap-3 flex-1">
                      {isEditing ? (
                        <select
                          value={selectedModel}
                          onChange={(e) => setSelectedModel(e.target.value)}
                          className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        >
                          <option value="">Select a model...</option>
                          {models.map((m) => (
                            <option key={m.id} value={m.id}>
                              {m.name} ({m.provider})
                            </option>
                          ))}
                        </select>
                      ) : (
                        <>
                          <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                            <Zap className="w-5 h-5 text-green-600" />
                          </div>
                          <div>
                            <h3 className="font-semibold text-gray-900">{model?.name || 'Unknown Model'}</h3>
                            <p className="text-sm text-gray-600 capitalize">{model?.provider || 'No provider'}</p>
                          </div>
                        </>
                      )}
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-2">
                    {isEditing ? (
                      <>
                        <button
                          onClick={() => handleSave(assignment.agent_id)}
                          disabled={updateMutation.isPending}
                          className="bg-green-600 hover:bg-green-700 text-white px-3 py-1.5 rounded-lg flex items-center gap-1 transition-colors disabled:opacity-50"
                        >
                          <Save className="w-4 h-4" />
                          Save
                        </button>
                        <button
                          onClick={handleCancel}
                          className="bg-gray-100 hover:bg-gray-200 text-gray-700 px-3 py-1.5 rounded-lg flex items-center gap-1 transition-colors"
                        >
                          <X className="w-4 h-4" />
                          Cancel
                        </button>
                      </>
                    ) : (
                      <button
                        onClick={() => handleEdit(assignment)}
                        className="bg-blue-100 hover:bg-blue-200 text-blue-700 px-3 py-1.5 rounded-lg flex items-center gap-1 transition-colors"
                      >
                        <Edit className="w-4 h-4" />
                        Edit
                      </button>
                    )}
                  </div>
                </div>

                {/* Agent Description */}
                {agent?.backstory && (
                  <div className="mt-4 pl-16">
                    <p className="text-sm text-gray-600 bg-gray-50 p-3 rounded-lg">
                      {agent.backstory}
                    </p>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Model Performance Insights */}
      <div className="mt-8 bg-white rounded-xl shadow-sm border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Model Performance Insights</h2>
        </div>
        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <h3 className="font-medium text-gray-900">Most Used Models</h3>
              {models.slice(0, 3).map((model) => {
                const usage = assignments.filter(a => a.model_id === model.id).length;
                return (
                  <div key={model.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center gap-3">
                      <Zap className="w-4 h-4 text-blue-500" />
                      <span className="font-medium">{model.name}</span>
                    </div>
                    <span className="text-sm text-gray-600">{usage} agents</span>
                  </div>
                );
              })}
            </div>
            <div className="space-y-4">
              <h3 className="font-medium text-gray-900">Agent Distribution</h3>
              {agents.slice(0, 3).map((agent) => (
                <div key={agent.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center gap-3">
                    <Bot className="w-4 h-4 text-green-500" />
                    <span className="font-medium">{agent.name}</span>
                  </div>
                  <span className="text-sm text-gray-600 capitalize">{agent.role}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 