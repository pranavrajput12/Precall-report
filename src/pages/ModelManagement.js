import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { Plus, Edit, Trash2, Settings, Zap, Database, Globe, Lock, CheckCircle, AlertCircle, Clock } from 'lucide-react';

const fetchModels = async () => {
  const res = await fetch('/api/config/models');
  if (!res.ok) throw new Error('Failed to fetch models');
  return res.json();
};

const addModel = async (model) => {
  const res = await fetch('/api/config/models', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(model),
  });
  if (!res.ok) throw new Error('Failed to add model');
  return res.json();
};

const deleteModel = async (modelId) => {
  const res = await fetch(`/api/config/models/${modelId}`, { method: 'DELETE' });
  if (!res.ok) throw new Error('Failed to delete model');
  return res.json();
};

const getProviderIcon = (provider) => {
  switch (provider.toLowerCase()) {
    case 'openai': return <Zap className="w-5 h-5 text-green-500" />;
    case 'anthropic': return <Database className="w-5 h-5 text-blue-500" />;
    case 'azure': return <Globe className="w-5 h-5 text-blue-600" />;
    default: return <Settings className="w-5 h-5 text-gray-500" />;
  }
};

const getStatusIcon = (status) => {
  switch (status) {
    case 'active': return <CheckCircle className="w-4 h-4 text-green-500" />;
    case 'inactive': return <AlertCircle className="w-4 h-4 text-red-500" />;
    case 'maintenance': return <Clock className="w-4 h-4 text-yellow-500" />;
    default: return <AlertCircle className="w-4 h-4 text-gray-500" />;
  }
};

export default function ModelManagement() {
  const queryClient = useQueryClient();
  const { data: models = [], isLoading } = useQuery({ queryKey: ['models'], queryFn: fetchModels });
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingModel, setEditingModel] = useState(null);
  const [form, setForm] = useState({
    id: '',
    name: '',
    provider: 'openai',
    type: 'chat',
    config: {
      temperature: 0.3,
      max_tokens: 2048,
      streaming: true,
    },
    status: 'active',
  });

  const addMutation = useMutation({
    mutationFn: addModel,
    onSuccess: () => {
      toast.success('Model added successfully!');
      queryClient.invalidateQueries({ queryKey: ['models'] });
      setShowAddModal(false);
      resetForm();
    },
    onError: (e) => toast.error(e.message),
  });

  const deleteMutation = useMutation({
    mutationFn: deleteModel,
    onSuccess: () => {
      toast.success('Model deleted successfully!');
      queryClient.invalidateQueries({ queryKey: ['models'] });
    },
    onError: (e) => toast.error(e.message),
  });

  const resetForm = () => {
    setForm({
      id: '',
      name: '',
      provider: 'openai',
      type: 'chat',
      config: {
        temperature: 0.3,
        max_tokens: 2048,
        streaming: true,
      },
      status: 'active',
    });
    setEditingModel(null);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!form.name || !form.id) {
      toast.error('Model ID and name are required');
      return;
    }
    addMutation.mutate(form);
  };

  const handleEdit = (model) => {
    setForm(model);
    setEditingModel(model);
    setShowAddModal(true);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Model Management</h1>
            <p className="text-gray-600 mt-2">Manage your AI models and their configurations</p>
          </div>
          <button
            onClick={() => setShowAddModal(true)}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center gap-2 transition-colors"
          >
            <Plus className="w-4 h-4" />
            Add Model
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Models</p>
              <p className="text-2xl font-bold text-gray-900">{models.length}</p>
            </div>
            <Database className="w-8 h-8 text-blue-500" />
          </div>
        </div>
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Active Models</p>
              <p className="text-2xl font-bold text-green-600">{models.filter(m => m.status === 'active').length}</p>
            </div>
            <CheckCircle className="w-8 h-8 text-green-500" />
          </div>
        </div>
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Providers</p>
              <p className="text-2xl font-bold text-purple-600">{new Set(models.map(m => m.provider)).size}</p>
            </div>
            <Globe className="w-8 h-8 text-purple-500" />
          </div>
        </div>
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Chat Models</p>
              <p className="text-2xl font-bold text-orange-600">{models.filter(m => m.type === 'chat').length}</p>
            </div>
            <Zap className="w-8 h-8 text-orange-500" />
          </div>
        </div>
      </div>

      {/* Models Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {models.map((model) => (
          <div key={model.id} className="bg-white rounded-xl p-6 shadow-sm border border-gray-200 hover:shadow-md transition-shadow">
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center gap-3">
                {getProviderIcon(model.provider)}
                <div>
                  <h3 className="font-semibold text-gray-900">{model.name}</h3>
                  <p className="text-sm text-gray-600">{model.id}</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                {getStatusIcon(model.status)}
                <span className="text-sm capitalize text-gray-600">{model.status}</span>
              </div>
            </div>
            
            <div className="space-y-2 mb-4">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Provider:</span>
                <span className="font-medium capitalize">{model.provider}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Type:</span>
                <span className="font-medium capitalize">{model.type}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Temperature:</span>
                <span className="font-medium">{model.config?.temperature || 0.3}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Max Tokens:</span>
                <span className="font-medium">{model.config?.max_tokens || 2048}</span>
              </div>
            </div>
            
            <div className="flex gap-2">
              <button
                onClick={() => handleEdit(model)}
                className="flex-1 bg-gray-100 hover:bg-gray-200 text-gray-700 px-3 py-2 rounded-lg flex items-center justify-center gap-2 transition-colors"
              >
                <Edit className="w-4 h-4" />
                Edit
              </button>
              <button
                onClick={() => deleteMutation.mutate(model.id)}
                className="flex-1 bg-red-100 hover:bg-red-200 text-red-700 px-3 py-2 rounded-lg flex items-center justify-center gap-2 transition-colors"
              >
                <Trash2 className="w-4 h-4" />
                Delete
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Add/Edit Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl p-6 w-full max-w-md">
            <h2 className="text-xl font-bold mb-4">
              {editingModel ? 'Edit Model' : 'Add New Model'}
            </h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Model ID</label>
                <input
                  type="text"
                  value={form.id}
                  onChange={(e) => setForm({ ...form, id: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="e.g., gpt-4"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Model Name</label>
                <input
                  type="text"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="e.g., GPT-4"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Provider</label>
                <select
                  value={form.provider}
                  onChange={(e) => setForm({ ...form, provider: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="openai">OpenAI</option>
                  <option value="anthropic">Anthropic</option>
                  <option value="azure">Azure OpenAI</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
                <select
                  value={form.type}
                  onChange={(e) => setForm({ ...form, type: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="chat">Chat</option>
                  <option value="completion">Completion</option>
                  <option value="embedding">Embedding</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Temperature</label>
                <input
                  type="number"
                  min="0"
                  max="2"
                  step="0.1"
                  value={form.config.temperature}
                  onChange={(e) => setForm({ ...form, config: { ...form.config, temperature: parseFloat(e.target.value) } })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Max Tokens</label>
                <input
                  type="number"
                  min="1"
                  max="32000"
                  value={form.config.max_tokens}
                  onChange={(e) => setForm({ ...form, config: { ...form.config, max_tokens: parseInt(e.target.value) } })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => {
                    setShowAddModal(false);
                    resetForm();
                  }}
                  className="flex-1 bg-gray-100 hover:bg-gray-200 text-gray-700 px-4 py-2 rounded-lg transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={addMutation.isPending}
                  className="flex-1 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors disabled:opacity-50"
                >
                  {addMutation.isPending ? 'Saving...' : editingModel ? 'Update' : 'Add Model'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
} 