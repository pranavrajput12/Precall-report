import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { 
  Plus, 
  Edit, 
  Trash2, 
  Settings, 
  Wrench, 
  CheckCircle, 
  AlertCircle, 
  Clock,
  Globe,
  Database,
  Zap,
  Code,
  Search,
  MessageSquare
} from 'lucide-react';

const fetchTools = async () => {
  const response = await fetch('/api/config/tools');
  if (!response.ok) throw new Error('Failed to fetch tools');
  return response.json();
};

const saveTool = async (tool) => {
  const response = await fetch(`/api/config/tools/${tool.id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(tool),
  });
  if (!response.ok) throw new Error('Failed to save tool');
  return response.json();
};

const deleteTool = async (id) => {
  const response = await fetch(`/api/config/tools/${id}`, {
    method: 'DELETE',
  });
  if (!response.ok) throw new Error('Failed to delete tool');
  return response.json();
};

const getToolIcon = (name) => {
  const iconName = name.toLowerCase();
  if (iconName.includes('scraper') || iconName.includes('linkedin')) return <Globe className="w-5 h-5 text-blue-500" />;
  if (iconName.includes('analyzer') || iconName.includes('company')) return <Database className="w-5 h-5 text-green-500" />;
  if (iconName.includes('generator') || iconName.includes('text')) return <MessageSquare className="w-5 h-5 text-purple-500" />;
  if (iconName.includes('search')) return <Search className="w-5 h-5 text-orange-500" />;
  if (iconName.includes('code')) return <Code className="w-5 h-5 text-red-500" />;
  return <Wrench className="w-5 h-5 text-gray-500" />;
};

const getStatusColor = (status) => {
  switch (status) {
    case 'active': return 'text-green-600 bg-green-100';
    case 'inactive': return 'text-red-600 bg-red-100';
    case 'maintenance': return 'text-yellow-600 bg-yellow-100';
    default: return 'text-gray-600 bg-gray-100';
  }
};

export default function ToolManager() {
  const queryClient = useQueryClient();
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingTool, setEditingTool] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [form, setForm] = useState({
    id: '',
    name: '',
    description: '',
    status: 'active',
    category: 'general',
    config: {}
  });

  const { data: tools = [], isLoading } = useQuery({
    queryKey: ['tools'],
    queryFn: fetchTools,
  });

  const saveToolMutation = useMutation({
    mutationFn: saveTool,
    onSuccess: () => {
      toast.success('Tool saved successfully!');
      queryClient.invalidateQueries({ queryKey: ['tools'] });
      setShowAddModal(false);
      resetForm();
    },
    onError: (e) => toast.error(e.message),
  });

  const deleteToolMutation = useMutation({
    mutationFn: deleteTool,
    onSuccess: () => {
      toast.success('Tool deleted successfully!');
      queryClient.invalidateQueries({ queryKey: ['tools'] });
    },
    onError: (e) => toast.error(e.message),
  });

  const resetForm = () => {
    setForm({
      id: '',
      name: '',
      description: '',
      status: 'active',
      category: 'general',
      config: {}
    });
    setEditingTool(null);
  };

  const handleEdit = (tool) => {
    setForm(tool);
    setEditingTool(tool);
    setShowAddModal(true);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!form.name || !form.id) {
      toast.error('Tool ID and name are required');
      return;
    }
    saveToolMutation.mutate(form);
  };

  const filteredTools = tools.filter(tool =>
    tool.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    tool.description.toLowerCase().includes(searchTerm.toLowerCase())
  );

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
            <h1 className="text-3xl font-bold text-gray-900">Tool Management</h1>
            <p className="text-gray-600 mt-2">Manage your AI agent tools and integrations</p>
          </div>
          <button
            onClick={() => setShowAddModal(true)}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center gap-2 transition-colors"
          >
            <Plus className="w-4 h-4" />
            Add Tool
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Tools</p>
              <p className="text-2xl font-bold text-gray-900">{tools.length}</p>
            </div>
            <Wrench className="w-8 h-8 text-blue-500" />
          </div>
        </div>
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Active Tools</p>
              <p className="text-2xl font-bold text-green-600">{tools.filter(t => t.status === 'active').length}</p>
            </div>
            <CheckCircle className="w-8 h-8 text-green-500" />
          </div>
        </div>
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Categories</p>
              <p className="text-2xl font-bold text-purple-600">{new Set(tools.map(t => t.category || 'general')).size}</p>
            </div>
            <Settings className="w-8 h-8 text-purple-500" />
          </div>
        </div>
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Maintenance</p>
              <p className="text-2xl font-bold text-yellow-600">{tools.filter(t => t.status === 'maintenance').length}</p>
            </div>
            <Clock className="w-8 h-8 text-yellow-500" />
          </div>
        </div>
      </div>

      {/* Search Bar */}
      <div className="mb-6">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
          <input
            type="text"
            placeholder="Search tools..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
      </div>

      {/* Tools Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredTools.map((tool) => (
          <div key={tool.id} className="bg-white rounded-xl p-6 shadow-sm border border-gray-200 hover:shadow-md transition-shadow">
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center gap-3">
                {getToolIcon(tool.name)}
                <div>
                  <h3 className="font-semibold text-gray-900">{tool.name}</h3>
                  <p className="text-sm text-gray-600">{tool.id}</p>
                </div>
              </div>
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(tool.status)}`}>
                {tool.status}
              </span>
            </div>
            
            <p className="text-sm text-gray-600 mb-4 line-clamp-2">{tool.description}</p>
            
            <div className="space-y-2 mb-4">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Category:</span>
                <span className="font-medium capitalize">{tool.category || 'General'}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Type:</span>
                <span className="font-medium">Integration</span>
              </div>
            </div>
            
            <div className="flex gap-2">
              <button
                onClick={() => handleEdit(tool)}
                className="flex-1 bg-gray-100 hover:bg-gray-200 text-gray-700 px-3 py-2 rounded-lg flex items-center justify-center gap-2 transition-colors"
              >
                <Edit className="w-4 h-4" />
                Edit
              </button>
              <button
                onClick={() => deleteToolMutation.mutate(tool.id)}
                className="flex-1 bg-red-100 hover:bg-red-200 text-red-700 px-3 py-2 rounded-lg flex items-center justify-center gap-2 transition-colors"
              >
                <Trash2 className="w-4 h-4" />
                Delete
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Empty State */}
      {filteredTools.length === 0 && (
        <div className="text-center py-12">
          <Wrench className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No tools found</h3>
          <p className="text-gray-600">
            {searchTerm ? 'Try adjusting your search terms' : 'Get started by adding your first tool'}
          </p>
        </div>
      )}

      {/* Add/Edit Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl p-6 w-full max-w-md">
            <h2 className="text-xl font-bold mb-4">
              {editingTool ? 'Edit Tool' : 'Add New Tool'}
            </h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Tool ID</label>
                <input
                  type="text"
                  value={form.id}
                  onChange={(e) => setForm({ ...form, id: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="e.g., linkedin_scraper"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Tool Name</label>
                <input
                  type="text"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="e.g., LinkedIn Scraper"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                <textarea
                  value={form.description}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  rows="3"
                  placeholder="Describe what this tool does..."
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Category</label>
                <select
                  value={form.category}
                  onChange={(e) => setForm({ ...form, category: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="general">General</option>
                  <option value="data">Data Processing</option>
                  <option value="web">Web Scraping</option>
                  <option value="analysis">Analysis</option>
                  <option value="communication">Communication</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
                <select
                  value={form.status}
                  onChange={(e) => setForm({ ...form, status: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="active">Active</option>
                  <option value="inactive">Inactive</option>
                  <option value="maintenance">Maintenance</option>
                </select>
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
                  disabled={saveToolMutation.isPending}
                  className="flex-1 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors disabled:opacity-50"
                >
                  {saveToolMutation.isPending ? 'Saving...' : editingTool ? 'Update' : 'Add Tool'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
} 