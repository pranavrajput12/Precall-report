import React, { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Settings as SettingsIcon, Database, Download, Upload, RefreshCw, Save, AlertCircle, CheckCircle, Monitor, Shield, Bell, Palette } from 'lucide-react';
import toast from 'react-hot-toast';

const fetchSystemHealth = async () => {
  const response = await fetch('http://localhost:8090/api/system/health');
  if (!response.ok) throw new Error('Failed to fetch system health');
  return response.json();
};

const fetchSystemConfig = async () => {
  const response = await fetch('http://localhost:8090/api/config/system');
  if (!response.ok) throw new Error('Failed to fetch system config');
  return response.json();
};

function Settings() {
  const [activeTab, setActiveTab] = useState('general');
  const [systemConfig, setSystemConfig] = useState({
    api_timeout: 30,
    max_concurrent_executions: 5,
    log_level: 'INFO',
    enable_monitoring: true,
    enable_notifications: true,
    theme: 'light'
  });

  const { data: systemHealth, isLoading: healthLoading } = useQuery({
    queryKey: ['system-health'],
    queryFn: fetchSystemHealth,
    refetchInterval: 5000
  });

  const saveConfigMutation = useMutation({
    mutationFn: async (config) => {
      const response = await fetch('http://localhost:8090/api/config/system', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      });
      if (!response.ok) throw new Error('Failed to save configuration');
      return response.json();
    },
    onSuccess: () => {
      toast.success('Configuration saved successfully');
    },
    onError: (error) => {
      toast.error(`Failed to save configuration: ${error.message}`);
    }
  });

  const createBackupMutation = useMutation({
    mutationFn: async () => {
      const response = await fetch('http://localhost:8090/api/system/backup', {
        method: 'POST'
      });
      if (!response.ok) throw new Error('Failed to create backup');
      return response.json();
    },
    onSuccess: () => {
      toast.success('Backup created successfully');
    },
    onError: (error) => {
      toast.error(`Failed to create backup: ${error.message}`);
    }
  });

  const refreshSystemMutation = useMutation({
    mutationFn: async () => {
      const response = await fetch('http://localhost:8090/api/system/refresh', {
        method: 'POST'
      });
      if (!response.ok) throw new Error('Failed to refresh system');
      return response.json();
    },
    onSuccess: () => {
      toast.success('System refreshed successfully');
    },
    onError: (error) => {
      toast.error(`Failed to refresh system: ${error.message}`);
    }
  });

  const handleSaveConfig = () => {
    saveConfigMutation.mutate(systemConfig);
  };

  const handleCreateBackup = () => {
    createBackupMutation.mutate();
  };

  const handleRefreshSystem = () => {
    refreshSystemMutation.mutate();
  };

  const tabs = [
    { id: 'general', label: 'General', icon: SettingsIcon },
    { id: 'performance', label: 'Performance', icon: Monitor },
    { id: 'security', label: 'Security', icon: Shield },
    { id: 'notifications', label: 'Notifications', icon: Bell },
    { id: 'appearance', label: 'Appearance', icon: Palette }
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-600">System configuration and maintenance</p>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center space-x-2 py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <tab.icon className="w-4 h-4" />
              <span>{tab.label}</span>
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {activeTab === 'general' && (
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold mb-4">General Settings</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    API Timeout (seconds)
                  </label>
                  <input
                    type="number"
                    value={systemConfig.api_timeout}
                    onChange={(e) => setSystemConfig({...systemConfig, api_timeout: parseInt(e.target.value)})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Max Concurrent Executions
                  </label>
                  <input
                    type="number"
                    value={systemConfig.max_concurrent_executions}
                    onChange={(e) => setSystemConfig({...systemConfig, max_concurrent_executions: parseInt(e.target.value)})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Log Level
                  </label>
                  <select
                    value={systemConfig.log_level}
                    onChange={(e) => setSystemConfig({...systemConfig, log_level: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="DEBUG">Debug</option>
                    <option value="INFO">Info</option>
                    <option value="WARNING">Warning</option>
                    <option value="ERROR">Error</option>
                  </select>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'performance' && (
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold mb-4">Performance Settings</h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">
                      Enable Monitoring
                    </label>
                    <p className="text-sm text-gray-500">Monitor system performance and health</p>
                  </div>
                  <input
                    type="checkbox"
                    checked={systemConfig.enable_monitoring}
                    onChange={(e) => setSystemConfig({...systemConfig, enable_monitoring: e.target.checked})}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                </div>
              </div>
            </div>
          )}

          {activeTab === 'notifications' && (
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold mb-4">Notification Settings</h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">
                      Enable Notifications
                    </label>
                    <p className="text-sm text-gray-500">Receive notifications for system events</p>
                  </div>
                  <input
                    type="checkbox"
                    checked={systemConfig.enable_notifications}
                    onChange={(e) => setSystemConfig({...systemConfig, enable_notifications: e.target.checked})}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                </div>
              </div>
            </div>
          )}

          {activeTab === 'appearance' && (
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold mb-4">Appearance Settings</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Theme
                  </label>
                  <select
                    value={systemConfig.theme}
                    onChange={(e) => setSystemConfig({...systemConfig, theme: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="light">Light</option>
                    <option value="dark">Dark</option>
                    <option value="auto">Auto</option>
                  </select>
                </div>
              </div>
            </div>
          )}

          {/* Save Button */}
          <div className="flex justify-end">
            <button
              onClick={handleSaveConfig}
              disabled={saveConfigMutation.isLoading}
              className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              <Save className="w-4 h-4" />
              <span>{saveConfigMutation.isLoading ? 'Saving...' : 'Save Changes'}</span>
            </button>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* System Health */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold mb-4">System Health</h3>
            {healthLoading ? (
              <div className="text-center py-4">
                <RefreshCw className="w-6 h-6 animate-spin text-blue-600 mx-auto mb-2" />
                <p className="text-sm text-gray-500">Loading...</p>
              </div>
            ) : systemHealth ? (
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Status</span>
                  <div className="flex items-center space-x-1">
                    <CheckCircle className="w-4 h-4 text-green-500" />
                    <span className="text-sm text-green-600">Healthy</span>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">CPU Usage</span>
                  <span className="text-sm text-gray-600">{systemHealth.system_metrics?.cpu_usage || 0}%</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Memory Usage</span>
                  <span className="text-sm text-gray-600">{systemHealth.system_metrics?.memory_usage || 0}%</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Uptime</span>
                  <span className="text-sm text-gray-600">{systemHealth.system_metrics?.uptime || 'N/A'}</span>
                </div>
              </div>
            ) : (
              <div className="text-center py-4">
                <AlertCircle className="w-6 h-6 text-red-500 mx-auto mb-2" />
                <p className="text-sm text-red-600">Health data unavailable</p>
              </div>
            )}
          </div>

          {/* Backup & Restore */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold mb-4">Backup & Restore</h3>
            <div className="space-y-3">
              <button
                onClick={handleCreateBackup}
                disabled={createBackupMutation.isLoading}
                className="w-full flex items-center justify-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50"
              >
                <Download className="w-4 h-4" />
                <span>{createBackupMutation.isLoading ? 'Creating...' : 'Create Backup'}</span>
              </button>
              
              <button className="w-full flex items-center justify-center space-x-2 px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700">
                <Upload className="w-4 h-4" />
                <span>Restore Backup</span>
              </button>
            </div>
          </div>

          {/* System Actions */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold mb-4">System Actions</h3>
            <div className="space-y-3">
              <button
                onClick={handleRefreshSystem}
                disabled={refreshSystemMutation.isLoading}
                className="w-full flex items-center justify-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
              >
                <RefreshCw className="w-4 h-4" />
                <span>{refreshSystemMutation.isLoading ? 'Refreshing...' : 'Refresh System'}</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Settings; 