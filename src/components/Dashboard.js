import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { 
  Bot, 
  MessageSquare, 
  GitBranch, 
  Wrench, 
  Activity, 
  CheckCircle, 
  AlertCircle,
  Clock,
  TrendingUp,
  Zap,
  Users,
  Database
} from 'lucide-react';

// API functions
const api = {
  getSystemStatus: async () => {
    const response = await fetch('/api/config/health');
    if (!response.ok) throw new Error('Failed to fetch system status');
    return response.json();
  },
  
  getAgents: async () => {
    const response = await fetch('/api/config/agents');
    if (!response.ok) throw new Error('Failed to fetch agents');
    return response.json();
  },
  
  getPrompts: async () => {
    const response = await fetch('/api/config/prompts');
    if (!response.ok) throw new Error('Failed to fetch prompts');
    return response.json();
  },
  
  getWorkflows: async () => {
    const response = await fetch('/api/config/workflows');
    if (!response.ok) throw new Error('Failed to fetch workflows');
    return response.json();
  },
  
  getTools: async () => {
    const response = await fetch('/api/config/tools');
    if (!response.ok) throw new Error('Failed to fetch tools');
    return response.json();
  }
};

function Dashboard() {
  // Fetch all data
  const { data: systemStatus } = useQuery({
    queryKey: ['system-status'],
    queryFn: api.getSystemStatus,
    refetchInterval: 30000 // Refresh every 30 seconds
  });

  const { data: agents = [] } = useQuery({
    queryKey: ['agents'],
    queryFn: api.getAgents
  });

  const { data: prompts = [] } = useQuery({
    queryKey: ['prompts'],
    queryFn: api.getPrompts
  });

  const { data: workflows = [] } = useQuery({
    queryKey: ['workflows'],
    queryFn: api.getWorkflows
  });

  const { data: tools = [] } = useQuery({
    queryKey: ['tools'],
    queryFn: api.getTools
  });

  // Calculate stats
  const stats = {
    agents: {
      total: agents.length,
      active: agents.filter(a => a.verbose).length,
      icon: Bot,
      color: 'primary'
    },
    prompts: {
      total: prompts.length,
      categories: [...new Set(prompts.map(p => p.category))].length,
      icon: MessageSquare,
      color: 'success'
    },
    workflows: {
      total: workflows.length,
      active: workflows.filter(w => w.settings?.parallel_execution).length,
      icon: GitBranch,
      color: 'warning'
    },
    tools: {
      total: tools.length,
      enabled: tools.filter(t => t.enabled).length,
      icon: Wrench,
      color: 'secondary'
    }
  };

  const StatCard = ({ title, value, subtitle, icon: Icon, color, trend }) => (
    <div className="card">
      <div className="card-body">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-secondary-600">{title}</p>
            <p className="text-2xl font-bold text-secondary-900">{value}</p>
            {subtitle && (
              <p className="text-sm text-secondary-500">{subtitle}</p>
            )}
          </div>
          <div className={`w-12 h-12 bg-${color}-100 rounded-lg flex items-center justify-center`}>
            <Icon className={`w-6 h-6 text-${color}-600`} />
          </div>
        </div>
        {trend && (
          <div className="mt-4 flex items-center">
            <TrendingUp className="w-4 h-4 text-success-600 mr-1" />
            <span className="text-sm text-success-600">{trend}</span>
          </div>
        )}
      </div>
    </div>
  );

  const RecentActivity = () => (
    <div className="card">
      <div className="card-header">
        <h3 className="text-lg font-semibold">Recent Activity</h3>
      </div>
      <div className="card-body">
        <div className="space-y-4">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-success-100 rounded-full flex items-center justify-center">
              <CheckCircle className="w-4 h-4 text-success-600" />
            </div>
            <div className="flex-1">
              <p className="text-sm font-medium text-secondary-900">Profile enrichment agent updated</p>
              <p className="text-xs text-secondary-500">2 minutes ago</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center">
              <MessageSquare className="w-4 h-4 text-primary-600" />
            </div>
            <div className="flex-1">
              <p className="text-sm font-medium text-secondary-900">New prompt template created</p>
              <p className="text-xs text-secondary-500">15 minutes ago</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-warning-100 rounded-full flex items-center justify-center">
              <GitBranch className="w-4 h-4 text-warning-600" />
            </div>
            <div className="flex-1">
              <p className="text-sm font-medium text-secondary-900">Workflow executed successfully</p>
              <p className="text-xs text-secondary-500">1 hour ago</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-secondary-100 rounded-full flex items-center justify-center">
              <Wrench className="w-4 h-4 text-secondary-600" />
            </div>
            <div className="flex-1">
              <p className="text-sm font-medium text-secondary-900">FAQ tool configuration updated</p>
              <p className="text-xs text-secondary-500">3 hours ago</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  const SystemHealth = () => (
    <div className="card">
      <div className="card-header">
        <h3 className="text-lg font-semibold">System Health</h3>
      </div>
      <div className="card-body">
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-success-500 rounded-full"></div>
              <span className="text-sm font-medium text-secondary-900">API Server</span>
            </div>
            <span className="text-sm text-success-600">Operational</span>
          </div>
          
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-success-500 rounded-full"></div>
              <span className="text-sm font-medium text-secondary-900">Azure OpenAI</span>
            </div>
            <span className="text-sm text-success-600">Connected</span>
          </div>
          
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-success-500 rounded-full"></div>
              <span className="text-sm font-medium text-secondary-900">Configuration Store</span>
            </div>
            <span className="text-sm text-success-600">Healthy</span>
          </div>
          
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-warning-500 rounded-full"></div>
              <span className="text-sm font-medium text-secondary-900">Cache Layer</span>
            </div>
            <span className="text-sm text-warning-600">Degraded</span>
          </div>
        </div>
      </div>
    </div>
  );

  const QuickActions = () => (
    <div className="card">
      <div className="card-header">
        <h3 className="text-lg font-semibold">Quick Actions</h3>
      </div>
      <div className="card-body">
        <div className="grid grid-cols-2 gap-3">
          <button className="btn-primary flex items-center justify-center space-x-2 py-3">
            <Bot className="w-4 h-4" />
            <span>New Agent</span>
          </button>
          
          <button className="btn-secondary flex items-center justify-center space-x-2 py-3">
            <MessageSquare className="w-4 h-4" />
            <span>New Prompt</span>
          </button>
          
          <button className="btn-success flex items-center justify-center space-x-2 py-3">
            <GitBranch className="w-4 h-4" />
            <span>Run Workflow</span>
          </button>
          
          <button className="btn-warning flex items-center justify-center space-x-2 py-3">
            <Database className="w-4 h-4" />
            <span>Backup Config</span>
          </button>
        </div>
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Welcome message */}
      <div className="bg-gradient-to-r from-primary-50 to-primary-100 rounded-xl p-6">
        <div className="flex items-center space-x-4">
          <div className="w-12 h-12 bg-primary-600 rounded-xl flex items-center justify-center">
            <Activity className="w-6 h-6 text-white" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-primary-900">Welcome to CrewAI Configuration Manager</h2>
            <p className="text-primary-700">Manage your AI agents, prompts, and workflows from one central dashboard</p>
          </div>
        </div>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="AI Agents"
          value={stats.agents.total}
          subtitle={`${stats.agents.active} active`}
          icon={stats.agents.icon}
          color={stats.agents.color}
          trend="+12% this week"
        />
        
        <StatCard
          title="Prompt Templates"
          value={stats.prompts.total}
          subtitle={`${stats.prompts.categories} categories`}
          icon={stats.prompts.icon}
          color={stats.prompts.color}
          trend="+5% this week"
        />
        
        <StatCard
          title="Workflows"
          value={stats.workflows.total}
          subtitle={`${stats.workflows.active} parallel`}
          icon={stats.workflows.icon}
          color={stats.workflows.color}
          trend="+8% this week"
        />
        
        <StatCard
          title="Tools"
          value={stats.tools.total}
          subtitle={`${stats.tools.enabled} enabled`}
          icon={stats.tools.icon}
          color={stats.tools.color}
          trend="Stable"
        />
      </div>

      {/* Main content grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left column - spans 2 columns */}
        <div className="lg:col-span-2 space-y-6">
          <RecentActivity />
          <SystemHealth />
        </div>
        
        {/* Right column */}
        <div className="space-y-6">
          <QuickActions />
          
          {/* Performance metrics */}
          <div className="card">
            <div className="card-header">
              <h3 className="text-lg font-semibold">Performance</h3>
            </div>
            <div className="card-body">
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-secondary-600">Average Response Time</span>
                    <span className="text-secondary-900">1.2s</span>
                  </div>
                  <div className="w-full bg-secondary-200 rounded-full h-2">
                    <div className="bg-success-600 h-2 rounded-full" style={{ width: '75%' }}></div>
                  </div>
                </div>
                
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-secondary-600">Success Rate</span>
                    <span className="text-secondary-900">98.5%</span>
                  </div>
                  <div className="w-full bg-secondary-200 rounded-full h-2">
                    <div className="bg-success-600 h-2 rounded-full" style={{ width: '98.5%' }}></div>
                  </div>
                </div>
                
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-secondary-600">Cache Hit Rate</span>
                    <span className="text-secondary-900">87%</span>
                  </div>
                  <div className="w-full bg-secondary-200 rounded-full h-2">
                    <div className="bg-primary-600 h-2 rounded-full" style={{ width: '87%' }}></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Dashboard; 