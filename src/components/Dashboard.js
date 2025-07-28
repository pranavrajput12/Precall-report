import React, { useState, useCallback, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Activity,
  CheckCircle,
  Database,
  Bot,
  RefreshCw,
  GitBranch,
  MessageSquare,
  Wrench,
  TrendingUp,
  Sparkles,
  BarChart3,
  ChevronRight,
  Play,
  Square,
  AlertCircle
} from 'lucide-react';
import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  BackgroundVariant,
  MarkerType,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import toast from 'react-hot-toast';
import clsx from 'clsx';
import { useData } from '../contexts/DataContext';


// Custom Node Components for workflow visualization
const AgentNode = ({ data, selected }) => {
  const { agent, status = 'idle', progress = 0, result, error } = data;
  
  const getStatusIcon = () => {
    switch (status) {
      case 'running':
        return <RefreshCw className="w-4 h-4 text-yellow-600 animate-spin" />;
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-600" />;
      case 'error':
        return <AlertCircle className="w-4 h-4 text-red-600" />;
      default:
        return <Bot className="w-4 h-4 text-gray-600" />;
    }
  };
  
  return (
    <div className={clsx(
      'px-4 py-3 rounded-lg border-2 min-w-48 shadow-md relative',
      status === 'running' ? 'border-yellow-400 bg-yellow-50' : 
      status === 'completed' ? 'border-green-400 bg-green-50' :
      status === 'error' ? 'border-red-400 bg-red-50' :
      'border-gray-300 bg-white',
      selected ? 'ring-2 ring-blue-500' : ''
    )}>
      <div className="absolute -left-2 top-1/2 w-4 h-4 bg-gray-400 rounded-full border-2 border-white transform -translate-y-1/2" />
      
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center space-x-2">
          {getStatusIcon()}
          <h3 className="font-semibold text-sm text-gray-900">{agent.name}</h3>
        </div>
        <span className="text-xs text-gray-500 capitalize">{status}</span>
      </div>
      
      <p className="text-xs text-gray-600 mb-2">{agent.role}</p>
      
      {status === 'running' && (
        <div className="w-full bg-gray-200 rounded-full h-1.5 mb-2">
          <div 
            className="bg-yellow-500 h-1.5 rounded-full transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
      )}
    </div>
  );
};

const WorkflowConfigNode = ({ data, selected }) => {
  return (
    <div className={clsx(
      'px-6 py-4 rounded-xl border-2 bg-gradient-to-r from-blue-50 to-blue-100 min-w-64 shadow-md relative',
      selected ? 'border-blue-500 ring-2 ring-blue-500' : 'border-blue-200'
    )}>
      <div className="absolute -right-2 top-1/2 w-4 h-4 bg-blue-500 rounded-full border-2 border-white transform -translate-y-1/2" />
      
      <div className="flex items-center space-x-3 mb-2">
        <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
          <GitBranch className="w-5 h-5 text-white" />
        </div>
        <div>
          <h3 className="font-semibold text-blue-900">{data.name}</h3>
          <p className="text-sm text-blue-700">Workflow Configuration</p>
        </div>
      </div>
      
      <div className="flex items-center space-x-2">
        <span className="px-2 py-1 bg-blue-200 text-blue-800 rounded text-xs">
          {data.steps?.length || 0} steps
        </span>
      </div>
    </div>
  );
};

const nodeTypes = {
  agent: AgentNode,
  workflowConfig: WorkflowConfigNode,
};

function Dashboard() {
  const navigate = useNavigate();
  const { agents, prompts, workflows, tools, systemHealth, refreshAll } = useData();
  const [activeTab, setActiveTab] = useState('overview');
  
  // Workflow visualization state
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [selectedWorkflow, setSelectedWorkflow] = useState(null);
  const [isExecuting, setIsExecuting] = useState(false);

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

  // Generate workflow visualization
  const generateWorkflowVisualization = useCallback((workflow) => {
    if (!workflow || !workflow.steps) return;

    const workflowNodes = [];
    const workflowEdges = [];

    // Create workflow config node
    const configNode = {
      id: 'workflow-config',
      type: 'workflowConfig',
      position: { x: 100, y: 100 },
      data: {
        name: workflow.name,
        steps: workflow.steps
      }
    };
    workflowNodes.push(configNode);

    // Create agent nodes
    workflow.steps.forEach((step, index) => {
      const agent = agents.find(a => a.id === step.agent_id);
      if (!agent) return;

      const agentNode = {
        id: step.id,
        type: 'agent',
        position: { x: 400 + (index * 300), y: 100 },
        data: {
          agent: agent,
          status: 'idle',
          progress: 0
        }
      };
      workflowNodes.push(agentNode);

      // Create edge from previous step or config
      const sourceId = index === 0 ? 'workflow-config' : workflow.steps[index - 1].id;
      const edge = {
        id: `${sourceId}-${step.id}`,
        source: sourceId,
        target: step.id,
        type: 'smoothstep',
        animated: false,
        markerEnd: {
          type: MarkerType.ArrowClosed,
          width: 20,
          height: 20,
          color: '#6b7280'
        },
        style: {
          strokeWidth: 2,
          stroke: '#6b7280'
        }
      };
      workflowEdges.push(edge);
    });

    setNodes(workflowNodes);
    setEdges(workflowEdges);
  }, [agents, setNodes, setEdges]);

  // Initialize workflow visualization
  useEffect(() => {
    if (activeTab === 'workflow' && workflows.length > 0 && agents.length > 0) {
      const workflow = workflows[0]; // Use first workflow
      setSelectedWorkflow(workflow);
      generateWorkflowVisualization(workflow);
    }
  }, [activeTab, workflows, agents, generateWorkflowVisualization]);

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
        </div>
      </div>
    </div>
  );

  const SystemHealthCard = () => (
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
              <span className="text-sm font-medium text-secondary-900">Observability</span>
            </div>
            <span className="text-sm text-success-600">{systemHealth?.observability?.initialized ? 'Active' : 'Inactive'}</span>
          </div>
          
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-success-500 rounded-full"></div>
              <span className="text-sm font-medium text-secondary-900">Performance Monitor</span>
            </div>
            <span className="text-sm text-success-600">{systemHealth?.performance?.monitoring_active ? 'Active' : 'Inactive'}</span>
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
          <button 
            onClick={() => navigate('/agents')}
            className="btn-primary flex items-center justify-center space-x-2 py-3"
          >
            <Bot className="w-4 h-4" />
            <span>New Agent</span>
          </button>
          
          <button 
            onClick={() => navigate('/prompts')}
            className="btn-secondary flex items-center justify-center space-x-2 py-3"
          >
            <MessageSquare className="w-4 h-4" />
            <span>New Prompt</span>
          </button>
          
          <button 
            onClick={() => navigate('/workflows/run')}
            className="btn-success flex items-center justify-center space-x-2 py-3"
          >
            <GitBranch className="w-4 h-4" />
            <span>Run Workflow</span>
          </button>
          
          <button 
            onClick={() => toast.success('Backup feature coming soon!')}
            className="btn-warning flex items-center justify-center space-x-2 py-3"
          >
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
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="w-12 h-12 bg-primary-600 rounded-xl flex items-center justify-center">
              <Activity className="w-6 h-6 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-primary-900">Welcome to CrewAI Configuration Manager</h2>
              <p className="text-primary-700">Manage your AI agents, prompts, and workflows from one central dashboard</p>
            </div>
          </div>
          <button
            onClick={refreshAll}
            className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh All
          </button>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="border-b border-gray-200">
          <div className="flex space-x-8 px-6">
            <button
              onClick={() => setActiveTab('overview')}
              className={clsx(
                'py-3 px-1 border-b-2 font-medium text-sm transition-colors',
                activeTab === 'overview'
                  ? 'border-primary-600 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              )}
            >
              <div className="flex items-center space-x-2">
                <BarChart3 className="w-4 h-4" />
                <span>Overview</span>
              </div>
            </button>
            <button
              onClick={() => setActiveTab('workflow')}
              className={clsx(
                'py-3 px-1 border-b-2 font-medium text-sm transition-colors',
                activeTab === 'workflow'
                  ? 'border-primary-600 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              )}
            >
              <div className="flex items-center space-x-2">
                <GitBranch className="w-4 h-4" />
                <span>Workflow Execution</span>
              </div>
            </button>
          </div>
        </div>
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <>
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
              <SystemHealthCard />
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
        </>
      )}

      {activeTab === 'workflow' && (
        <div className="space-y-6">
          {/* Workflow Execution Controls */}
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-gray-900">Interactive Workflow Execution</h3>
              <p className="text-gray-600">View and monitor your AI workflows in real-time</p>
            </div>
            
            <div className="flex items-center space-x-3">
              {selectedWorkflow && (
                <span className="text-sm text-gray-600">
                  Current: <span className="font-medium">{selectedWorkflow.name}</span>
                </span>
              )}
              <button
                onClick={() => navigate('/workflows/run')}
                className="btn bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg font-medium flex items-center space-x-2"
              >
                <Play className="w-4 h-4" />
                <span>Run Workflow</span>
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Workflow Visualization */}
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden" style={{ height: '500px' }}>
            {workflows.length > 0 && agents.length > 0 ? (
              <ReactFlow
                nodes={nodes}
                edges={edges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                nodeTypes={nodeTypes}
                fitView
                fitViewOptions={{ padding: 0.2 }}
              >
                <Background color="#aaa" gap={16} variant={BackgroundVariant.Dots} />
                <Controls />
                <MiniMap />
              </ReactFlow>
            ) : (
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <GitBranch className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                  <h4 className="text-lg font-medium text-gray-900 mb-2">No Workflows Available</h4>
                  <p className="text-gray-600 mb-6">
                    Create a workflow to see the visualization here
                  </p>
                  <button
                    onClick={() => navigate('/workflows/builder')}
                    className="btn bg-primary-600 hover:bg-primary-700 text-white px-6 py-2 rounded-lg"
                  >
                    Create Workflow
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Quick Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white rounded-lg border p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Total Workflows</p>
                  <p className="text-2xl font-bold text-gray-900">{workflows.length}</p>
                </div>
                <GitBranch className="w-8 h-8 text-blue-500" />
              </div>
            </div>
            
            <div className="bg-white rounded-lg border p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Active Agents</p>
                  <p className="text-2xl font-bold text-gray-900">{agents.length}</p>
                </div>
                <Bot className="w-8 h-8 text-green-500" />
              </div>
            </div>
            
            <div className="bg-white rounded-lg border p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">System Status</p>
                  <p className="text-2xl font-bold text-green-600">Healthy</p>
                </div>
                <Activity className="w-8 h-8 text-green-500" />
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default Dashboard;