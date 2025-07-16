import React, { useState, useEffect, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Plus,
  Trash2,
  Save,
  Download,
  Upload,
  Search,
  Edit2,
  X,
  Check,
  FileSpreadsheet,
  AlertCircle,
  RefreshCw
} from 'lucide-react';
import toast from 'react-hot-toast';

const fetchFAQs = async () => {
  const response = await fetch('/api/faq');
  if (!response.ok) throw new Error('Failed to fetch FAQs');
  return response.json();
};

const KnowledgeBase = () => {
  const queryClient = useQueryClient();
  const fileInputRef = useRef(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [editingId, setEditingId] = useState(null);
  const [editingData, setEditingData] = useState({});
  const [newRow, setNewRow] = useState({
    question: '',
    answer: '',
    category: '',
    keywords: ''
  });
  const [showNewRow, setShowNewRow] = useState(false);

  const { data: faqs = [], isLoading, refetch } = useQuery({
    queryKey: ['faqs'],
    queryFn: fetchFAQs
  });

  // Mutations
  const createMutation = useMutation({
    mutationFn: async (data) => {
      const response = await fetch('/api/faq', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      if (!response.ok) throw new Error('Failed to create FAQ');
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['faqs']);
      toast.success('FAQ added successfully');
      setShowNewRow(false);
      setNewRow({ question: '', answer: '', category: '', keywords: '' });
    },
    onError: (error) => {
      toast.error(`Failed to add FAQ: ${error.message}`);
    }
  });

  const updateMutation = useMutation({
    mutationFn: async ({ id, data }) => {
      const response = await fetch(`/api/faq/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      if (!response.ok) throw new Error('Failed to update FAQ');
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['faqs']);
      toast.success('FAQ updated successfully');
      setEditingId(null);
      setEditingData({});
    },
    onError: (error) => {
      toast.error(`Failed to update FAQ: ${error.message}`);
    }
  });

  const deleteMutation = useMutation({
    mutationFn: async (id) => {
      const response = await fetch(`/api/faq/${id}`, {
        method: 'DELETE'
      });
      if (!response.ok) throw new Error('Failed to delete FAQ');
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['faqs']);
      toast.success('FAQ deleted successfully');
    },
    onError: (error) => {
      toast.error(`Failed to delete FAQ: ${error.message}`);
    }
  });

  // Handlers
  const handleEdit = (faq) => {
    setEditingId(faq.id);
    setEditingData({
      question: faq.question,
      answer: faq.answer,
      category: faq.category || '',
      keywords: faq.keywords || ''
    });
  };

  const handleSave = () => {
    updateMutation.mutate({ id: editingId, data: editingData });
  };

  const handleCancel = () => {
    setEditingId(null);
    setEditingData({});
  };

  const handleDelete = (id) => {
    if (window.confirm('Are you sure you want to delete this FAQ?')) {
      deleteMutation.mutate(id);
    }
  };

  const handleAddNew = () => {
    if (!newRow.question || !newRow.answer) {
      toast.error('Question and Answer are required');
      return;
    }
    createMutation.mutate(newRow);
  };

  const handleExport = () => {
    window.location.href = '/api/faq/export';
    toast.success('FAQ data exported');
  };

  const handleImport = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('/api/faq/import', {
        method: 'POST',
        body: formData
      });
      
      const result = await response.json();
      
      if (result.success) {
        toast.success(`Imported ${result.count} FAQs`);
        refetch();
      } else {
        toast.error(result.error || 'Import failed');
      }
    } catch (error) {
      toast.error('Failed to import file');
    }

    // Reset file input
    event.target.value = '';
  };

  // Filter FAQs based on search
  const filteredFAQs = faqs.filter(faq => {
    const searchLower = searchQuery.toLowerCase();
    return (
      faq.question?.toLowerCase().includes(searchLower) ||
      faq.answer?.toLowerCase().includes(searchLower) ||
      faq.category?.toLowerCase().includes(searchLower) ||
      faq.keywords?.toLowerCase().includes(searchLower)
    );
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <RefreshCw className="w-8 h-8 animate-spin text-blue-600 mx-auto mb-2" />
          <p className="text-gray-600">Loading knowledge base...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-full mx-auto">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 mb-2">FAQ Knowledge Base</h1>
            <p className="text-gray-600">Manage your FAQ entries in a spreadsheet-like interface</p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleExport}
              className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg flex items-center gap-2 transition-colors"
            >
              <Download className="w-4 h-4" />
              Export CSV
            </button>
            <button
              onClick={() => fileInputRef.current?.click()}
              className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg flex items-center gap-2 transition-colors"
            >
              <Upload className="w-4 h-4" />
              Import CSV
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv"
              onChange={handleImport}
              style={{ display: 'none' }}
            />
            <button
              onClick={() => setShowNewRow(true)}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg flex items-center gap-2 transition-colors"
            >
              <Plus className="w-4 h-4" />
              Add FAQ
            </button>
          </div>
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
          <input
            type="text"
            placeholder="Search FAQs..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
      </div>

      {/* Stats */}
      <div className="mb-4 flex items-center gap-4 text-sm">
        <div className="flex items-center gap-2">
          <FileSpreadsheet className="w-4 h-4 text-gray-500" />
          <span className="text-gray-600">
            Total FAQs: <span className="font-medium text-gray-900">{faqs.length}</span>
          </span>
        </div>
        {searchQuery && (
          <div className="flex items-center gap-2">
            <span className="text-gray-600">
              Showing: <span className="font-medium text-gray-900">{filteredFAQs.length}</span> results
            </span>
          </div>
        )}
      </div>

      {/* Table */}
      <div className="bg-white rounded-lg border overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-12">#</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Question</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Answer</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-32">Category</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-40">Keywords</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-24">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {/* New Row */}
              {showNewRow && (
                <tr className="bg-blue-50">
                  <td className="px-4 py-3 text-sm text-gray-500">New</td>
                  <td className="px-4 py-3">
                    <textarea
                      value={newRow.question}
                      onChange={(e) => setNewRow({ ...newRow, question: e.target.value })}
                      className="w-full px-2 py-1 border border-gray-300 rounded resize-none"
                      rows="2"
                      placeholder="Enter question..."
                    />
                  </td>
                  <td className="px-4 py-3">
                    <textarea
                      value={newRow.answer}
                      onChange={(e) => setNewRow({ ...newRow, answer: e.target.value })}
                      className="w-full px-2 py-1 border border-gray-300 rounded resize-none"
                      rows="2"
                      placeholder="Enter answer..."
                    />
                  </td>
                  <td className="px-4 py-3">
                    <input
                      type="text"
                      value={newRow.category}
                      onChange={(e) => setNewRow({ ...newRow, category: e.target.value })}
                      className="w-full px-2 py-1 border border-gray-300 rounded"
                      placeholder="Category"
                    />
                  </td>
                  <td className="px-4 py-3">
                    <input
                      type="text"
                      value={newRow.keywords}
                      onChange={(e) => setNewRow({ ...newRow, keywords: e.target.value })}
                      className="w-full px-2 py-1 border border-gray-300 rounded"
                      placeholder="keyword1, keyword2"
                    />
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-1">
                      <button
                        onClick={handleAddNew}
                        className="p-1 text-green-600 hover:bg-green-100 rounded"
                        title="Save"
                      >
                        <Check className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => {
                          setShowNewRow(false);
                          setNewRow({ question: '', answer: '', category: '', keywords: '' });
                        }}
                        className="p-1 text-red-600 hover:bg-red-100 rounded"
                        title="Cancel"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              )}

              {/* Existing Rows */}
              {filteredFAQs.map((faq) => (
                <tr key={faq.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm text-gray-500">{faq.id}</td>
                  
                  {/* Question */}
                  <td className="px-4 py-3">
                    {editingId === faq.id ? (
                      <textarea
                        value={editingData.question}
                        onChange={(e) => setEditingData({ ...editingData, question: e.target.value })}
                        className="w-full px-2 py-1 border border-gray-300 rounded resize-none"
                        rows="2"
                      />
                    ) : (
                      <div className="text-sm text-gray-900 max-w-xs overflow-hidden">
                        {faq.question}
                      </div>
                    )}
                  </td>

                  {/* Answer */}
                  <td className="px-4 py-3">
                    {editingId === faq.id ? (
                      <textarea
                        value={editingData.answer}
                        onChange={(e) => setEditingData({ ...editingData, answer: e.target.value })}
                        className="w-full px-2 py-1 border border-gray-300 rounded resize-none"
                        rows="2"
                      />
                    ) : (
                      <div className="text-sm text-gray-900 max-w-md overflow-hidden">
                        {faq.answer?.substring(0, 150)}{faq.answer?.length > 150 && '...'}
                      </div>
                    )}
                  </td>

                  {/* Category */}
                  <td className="px-4 py-3">
                    {editingId === faq.id ? (
                      <input
                        type="text"
                        value={editingData.category}
                        onChange={(e) => setEditingData({ ...editingData, category: e.target.value })}
                        className="w-full px-2 py-1 border border-gray-300 rounded"
                      />
                    ) : (
                      <span className="text-sm text-gray-600">{faq.category || '-'}</span>
                    )}
                  </td>

                  {/* Keywords */}
                  <td className="px-4 py-3">
                    {editingId === faq.id ? (
                      <input
                        type="text"
                        value={editingData.keywords}
                        onChange={(e) => setEditingData({ ...editingData, keywords: e.target.value })}
                        className="w-full px-2 py-1 border border-gray-300 rounded"
                        placeholder="keyword1, keyword2"
                      />
                    ) : (
                      <div className="flex flex-wrap gap-1">
                        {faq.keywords ? (
                          faq.keywords.split(',').map((keyword, idx) => (
                            <span
                              key={idx}
                              className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded"
                            >
                              {keyword.trim()}
                            </span>
                          ))
                        ) : (
                          <span className="text-sm text-gray-400">-</span>
                        )}
                      </div>
                    )}
                  </td>

                  {/* Actions */}
                  <td className="px-4 py-3">
                    {editingId === faq.id ? (
                      <div className="flex items-center gap-1">
                        <button
                          onClick={handleSave}
                          className="p-1 text-green-600 hover:bg-green-100 rounded"
                          title="Save"
                        >
                          <Check className="w-4 h-4" />
                        </button>
                        <button
                          onClick={handleCancel}
                          className="p-1 text-red-600 hover:bg-red-100 rounded"
                          title="Cancel"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      </div>
                    ) : (
                      <div className="flex items-center gap-1">
                        <button
                          onClick={() => handleEdit(faq)}
                          className="p-1 text-blue-600 hover:bg-blue-100 rounded"
                          title="Edit"
                        >
                          <Edit2 className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleDelete(faq.id)}
                          className="p-1 text-red-600 hover:bg-red-100 rounded"
                          title="Delete"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
              ))}

              {filteredFAQs.length === 0 && !showNewRow && (
                <tr>
                  <td colSpan="6" className="px-4 py-8 text-center">
                    <AlertCircle className="w-12 h-12 text-gray-400 mx-auto mb-2" />
                    <p className="text-gray-600">
                      {searchQuery ? 'No FAQs found matching your search' : 'No FAQs available'}
                    </p>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Info */}
      <div className="mt-4 text-sm text-gray-500">
        <p>💡 Tips:</p>
        <ul className="list-disc list-inside mt-1 space-y-1">
          <li>Click on any cell to edit inline</li>
          <li>Use keywords to improve search accuracy</li>
          <li>Export your data regularly for backup</li>
          <li>Import CSV files must have columns: Answer, Question, Category, Keywords</li>
        </ul>
      </div>
    </div>
  );
};

export default KnowledgeBase;