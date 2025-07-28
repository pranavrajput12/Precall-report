import React from 'react';
import { Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom';
import {
  GitBranch,
  Play,
  List,
  Plus,
  ChevronRight
} from 'lucide-react';
import clsx from 'clsx';
import WorkflowBuilder from '../components/WorkflowBuilder';
import RunWorkflow from './RunWorkflow';
import AllRuns from './AllRuns';

function WorkflowsPage() {
  const navigate = useNavigate();
  const location = useLocation();
  
  // Extract the current tab from the URL path
  const getActiveTab = () => {
    const path = location.pathname;
    if (path.includes('/workflows/run')) return 'run';
    if (path.includes('/workflows/history')) return 'history';
    if (path.includes('/workflows/builder')) return 'builder';
    return 'builder'; // default
  };

  const activeTab = getActiveTab();

  const tabs = [
    {
      id: 'builder',
      label: 'Build & Edit',
      icon: GitBranch,
      path: '/workflows/builder',
      description: 'Create and edit workflow configurations'
    },
    {
      id: 'run',
      label: 'Run Workflow',
      icon: Play,
      path: '/workflows/run',
      description: 'Execute workflows with real inputs'
    },
    {
      id: 'history',
      label: 'Execution History',
      icon: List,
      path: '/workflows/history',
      description: 'View all past workflow runs'
    }
  ];

  const handleTabClick = (tab) => {
    navigate(tab.path);
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="bg-gradient-to-r from-blue-50 to-blue-100 rounded-xl p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="w-12 h-12 bg-blue-600 rounded-xl flex items-center justify-center">
              <GitBranch className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-blue-900">Workflows</h1>
              <p className="text-blue-700">Build, run, and track your AI workflow executions</p>
            </div>
          </div>
          
          {activeTab === 'builder' && (
            <button
              onClick={() => navigate('/workflows/run')}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              <Play className="w-4 h-4" />
              Run Workflow
              <ChevronRight className="w-4 h-4" />
            </button>
          )}
          
          {activeTab === 'run' && (
            <button
              onClick={() => navigate('/workflows/history')}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              <List className="w-4 h-4" />
              View History
              <ChevronRight className="w-4 h-4" />
            </button>
          )}
          
          {activeTab === 'history' && (
            <button
              onClick={() => navigate('/workflows/builder')}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              <Plus className="w-4 h-4" />
              Create New
              <ChevronRight className="w-4 h-4" />
            </button>
          )}
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
                      ? 'border-blue-600 text-blue-600'
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

      {/* Tab Content */}
      <div className="min-h-[600px]">
        <Routes>
          <Route path="/" element={<Navigate to="/workflows/builder" replace />} />
          <Route path="/builder" element={<WorkflowBuilder />} />
          <Route path="/run" element={<RunWorkflow />} />
          <Route path="/history" element={<AllRuns />} />
        </Routes>
      </div>
    </div>
  );
}

export default WorkflowsPage;