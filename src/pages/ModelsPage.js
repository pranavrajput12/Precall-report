import React from 'react';
import { Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom';
import {
  Database,
  Settings,
  ListChecks,
  ChevronRight,
  Cpu,
  Zap
} from 'lucide-react';
import clsx from 'clsx';
import ModelManagement from './ModelManagement';
import ModelAssignments from './ModelAssignments';

function ModelsPage() {
  const navigate = useNavigate();
  const location = useLocation();
  
  // Extract the current tab from the URL path
  const getActiveTab = () => {
    const path = location.pathname;
    if (path.includes('/models/configuration')) return 'configuration';
    if (path.includes('/models/assignments')) return 'assignments';
    return 'configuration'; // default
  };

  const activeTab = getActiveTab();

  const tabs = [
    {
      id: 'configuration',
      label: 'Model Configuration',
      icon: Settings,
      path: '/models/configuration',
      description: 'Add and configure Azure OpenAI models'
    },
    {
      id: 'assignments',
      label: 'Agent Assignments',
      icon: ListChecks,
      path: '/models/assignments',
      description: 'Review and manage model assignments to agents'
    }
  ];

  const handleTabClick = (tab) => {
    navigate(tab.path);
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="bg-gradient-to-r from-purple-50 to-purple-100 rounded-xl p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="w-12 h-12 bg-purple-600 rounded-xl flex items-center justify-center">
              <Database className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-purple-900">Model Management</h1>
              <p className="text-purple-700">Configure AI models and manage agent assignments</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-2 px-4 py-2 bg-purple-100 rounded-lg">
              <Cpu className="w-4 h-4 text-purple-600" />
              <span className="text-sm font-medium text-purple-700">Azure OpenAI</span>
            </div>
            
            {activeTab === 'configuration' && (
              <button
                onClick={() => navigate('/models/assignments')}
                className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
              >
                <ListChecks className="w-4 h-4" />
                View Assignments
                <ChevronRight className="w-4 h-4" />
              </button>
            )}
            
            {activeTab === 'assignments' && (
              <button
                onClick={() => navigate('/models/configuration')}
                className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
              >
                <Settings className="w-4 h-4" />
                Configure Models
                <ChevronRight className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="border-b border-gray-200">
          <div className="flex space-x-8 px-6">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              
              return (
                <button
                  key={tab.id}
                  onClick={() => handleTabClick(tab)}
                  className={clsx(
                    'py-4 px-1 border-b-2 font-medium text-sm transition-all duration-200',
                    isActive
                      ? 'border-purple-600 text-purple-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  )}
                >
                  <div className="flex items-center space-x-2">
                    <Icon className="w-4 h-4" />
                    <span>{tab.label}</span>
                  </div>
                  {isActive && (
                    <p className="text-xs text-gray-500 mt-1">{tab.description}</p>
                  )}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg border p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Active Models</p>
              <p className="text-2xl font-bold text-gray-900">3</p>
              <p className="text-xs text-gray-500 mt-1">GPT-4, GPT-3.5</p>
            </div>
            <Database className="w-8 h-8 text-purple-500" />
          </div>
        </div>
        
        <div className="bg-white rounded-lg border p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Assignments</p>
              <p className="text-2xl font-bold text-gray-900">8</p>
              <p className="text-xs text-gray-500 mt-1">Across all agents</p>
            </div>
            <ListChecks className="w-8 h-8 text-green-500" />
          </div>
        </div>
        
        <div className="bg-white rounded-lg border p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Model Health</p>
              <p className="text-2xl font-bold text-green-600">Optimal</p>
              <p className="text-xs text-gray-500 mt-1">All systems operational</p>
            </div>
            <Zap className="w-8 h-8 text-green-500" />
          </div>
        </div>
      </div>

      {/* Tab Content */}
      <div className="min-h-[600px]">
        <Routes>
          <Route path="/" element={<Navigate to="/models/configuration" replace />} />
          <Route path="/configuration" element={<ModelManagement />} />
          <Route path="/assignments" element={<ModelAssignments />} />
        </Routes>
      </div>
    </div>
  );
}

export default ModelsPage;