import React, { useState, useCallback, useEffect, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  ReactFlow,
  ReactFlowProvider,
  useNodesState,
  useEdgesState,
  addEdge,
  Controls,
  MiniMap,
  Background,
  Panel,
  Position,
  MarkerType,
} from '@xyflow/react';
import dagre from 'dagre';
import { Play, Pause, Square, Save, Edit, Trash2, Plus, Settings, Wrench, Eye, EyeOff, Clock, Download, Upload, MessageSquare, Zap, Bot, CheckCircle, AlertCircle, RefreshCw } from 'lucide-react';
import '@xyflow/react/dist/style.css';
import toast from 'react-hot-toast';
import clsx from 'clsx';

const PYTHON_STEP_TYPE = 'python';
const AGENT_STEP_TYPE = 'agent';

// Custom Node Components
const WorkflowConfigNode = ({ data, selected }) => {
  return (
    <div className={clsx(
      'px-6 py-4 rounded-xl border-2 bg-gradient-to-r from-primary-50 to-primary-100 min-w-64',
      selected ? 'border-primary-500 shadow-lg' : 'border-primary-200 shadow-md'
    )}>
      <div className="flex items-center space-x-3">
        <div className="w-10 h-10 bg-primary-600 rounded-lg flex items-center justify-center">
          <Settings className="w-5 h-5 text-white" />
        </div>
        <div>
          <h3 className="font-semibold text-primary-900">Workflow Configuration</h3>
          <p className="text-sm text-primary-700">{data.name}</p>
        </div>
      </div>
      {data.description && (
        <p className="text-xs text-primary-600 mt-2">{data.description}</p>
      )}
      <div className="flex items-center space-x-2 mt-3">
        <span className="badge-primary text-xs">
          {data.steps?.length || 0} steps
        </span>
        {data.settings?.parallel_execution && (
          <span className="badge-success text-xs">Parallel</span>
        )}
      </div>
    </div>
  );
};

const AgentNode = ({ data, selected }) => {
  const getAgentIcon = (role) => {
    if (role.includes('Analyzer')) return MessageSquare;
    if (role.includes('Generator')) return Edit;
    if (role.includes('Enricher')) return Zap;
    return Bot;
  };

  const Icon = getAgentIcon(data.role);

  return (
    <div className={clsx(
      'px-4 py-3 rounded-lg border-2 bg-white min-w-48',
      selected ? 'border-primary-500 shadow-lg' : 'border-secondary-200 shadow-md',
      data.status === 'running' && 'border-warning-400 bg-warning-50',
      data.status === 'completed' && 'border-success-400 bg-success-50',
      data.status === 'error' && 'border-error-400 bg-error-50'
    )}>
      <div className="flex items-center space-x-2">
        <div className={clsx(
          'w-8 h-8 rounded-lg flex items-center justify-center',
          data.status === 'running' ? 'bg-warning-100' : 'bg-primary-100'
        )}>
          <Icon className={clsx(
            'w-4 h-4',
            data.status === 'running' ? 'text-warning-600' : 'text-primary-600'
          )} />
        </div>
        <div className="flex-1">
          <h4 className="font-medium text-secondary-900 text-sm">{data.role}</h4>
          <p className="text-xs text-secondary-600 line-clamp-1">{data.goal}</p>
        </div>
        {data.status === 'running' && (
          <div className="w-2 h-2 bg-warning-500 rounded-full animate-pulse"></div>
        )}
        {data.status === 'completed' && (
          <CheckCircle className="w-4 h-4 text-success-600" />
        )}
        {data.status === 'error' && (
          <AlertCircle className="w-4 h-4 text-error-600" />
        )}
      </div>
      
      {data.expanded && (
        <div className="mt-3 pt-3 border-t border-secondary-200">
          <div className="space-y-2">
            <div>
              <span className="text-xs font-medium text-secondary-700">Temperature:</span>
              <span className="text-xs text-secondary-600 ml-1">{data.temperature}</span>
            </div>
            <div>
              <span className="text-xs font-medium text-secondary-700">Max Iterations:</span>
              <span className="text-xs text-secondary-600 ml-1">{data.max_iter}</span>
            </div>
            {data.prompt_id && (
              <div>
                <span className="text-xs font-medium text-secondary-700">Prompt:</span>
                <span className="text-xs text-secondary-600 ml-1">{data.prompt_id}</span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

const OutputNode = ({ data, selected }) => {
  return (
    <div className={clsx(
      'px-4 py-3 rounded-lg border-2 bg-gradient-to-r from-success-50 to-success-100 min-w-48',
      selected ? 'border-success-500 shadow-lg' : 'border-success-200 shadow-md'
    )}>
      <div className="flex items-center space-x-2">
        <div className="w-8 h-8 bg-success-600 rounded-lg flex items-center justify-center">
          <CheckCircle className="w-4 h-4 text-white" />
        </div>
        <div>
          <h4 className="font-medium text-success-900 text-sm">{data.name}</h4>
          <p className="text-xs text-success-700">{data.description}</p>
        </div>
      </div>
      
      {data.quality_score && (
        <div className="mt-2">
          <div className="flex items-center justify-between">
            <span className="text-xs text-success-700">Quality Score</span>
            <span className="text-xs font-medium text-success-900">
              {(data.quality_score * 100).toFixed(0)}%
            </span>
          </div>
          <div className="w-full bg-success-200 rounded-full h-1.5 mt-1">
            <div 
              className="bg-success-600 h-1.5 rounded-full transition-all duration-300"
              style={{ width: `${data.quality_score * 100}%` }}
            ></div>
          </div>
        </div>
      )}
    </div>
  );
};

const nodeTypes = {
  workflowConfig: WorkflowConfigNode,
  agent: AgentNode,
  output: OutputNode,
};

// Layout algorithm using Dagre
const getLayoutedElements = (nodes, edges, direction = 'TB') => {
  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setDefaultEdgeLabel(() => ({}));
  dagreGraph.setGraph({ rankdir: direction });

  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: node.width || 250, height: node.height || 100 });
  });

  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  dagre.layout(dagreGraph);

  nodes.forEach((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);
    node.targetPosition = Position.Top;
    node.sourcePosition = Position.Bottom;
    node.position = {
      x: nodeWithPosition.x - (node.width || 250) / 2,
      y: nodeWithPosition.y - (node.height || 100) / 2,
    };
  });

  return { nodes, edges };
};

// API functions
const api = {
  getWorkflows: async () => {
    const response = await fetch('/api/config/workflows');
    if (!response.ok) throw new Error('Failed to fetch workflows');
    return response.json();
  },
  
  getWorkflow: async (id) => {
    const response = await fetch(`/api/config/workflows/${id}`);
    if (!response.ok) throw new Error('Failed to fetch workflow');
    return response.json();
  },
  
  saveWorkflow: async (id, data) => {
    const response = await fetch(`/api/config/workflows/${id}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    if (!response.ok) throw new Error('Failed to save workflow');
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
  
  runWorkflow: async (workflowId, data) => {
    const response = await fetch('/api/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    if (!response.ok) throw new Error('Failed to run workflow');
    return response.json();
  }
};

function WorkflowBuilder() {
  const [selectedWorkflow, setSelectedWorkflow] = useState(null);
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [isRunning, setIsRunning] = useState(false);
  const [runningStep, setRunningStep] = useState(null);
  const [showDetails, setShowDetails] = useState(false);
  const [selectedNode, setSelectedNode] = useState(null);
  const [showAddStep, setShowAddStep] = useState(false);
  const [newStep, setNewStep] = useState({
    name: '',
    id: '',
    type: AGENT_STEP_TYPE,
    agent_id: '',
    prompt_id: '',
    code: '',
    inputVars: '',
    order: (selectedWorkflow?.steps?.length || 0) + 1,
    enabled: true,
    description: ''
  });
  const [inputData, setInputData] = useState({});

  const queryClient = useQueryClient();

  // Fetch data
  const { data: workflows = [], isLoading: workflowsLoading } = useQuery({
    queryKey: ['workflows'],
    queryFn: api.getWorkflows
  });

  const { data: agents = [] } = useQuery({
    queryKey: ['agents'],
    queryFn: api.getAgents
  });

  const { data: prompts = [] } = useQuery({
    queryKey: ['prompts'],
    queryFn: api.getPrompts
  });

  // Save workflow mutation
  const saveWorkflowMutation = useMutation({
    mutationFn: ({ id, data }) => api.saveWorkflow(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries(['workflows']);
      toast.success('Workflow saved successfully');
    },
    onError: (error) => {
      toast.error(`Failed to save workflow: ${error.message}`);
    }
  });

  // Run workflow mutation
  const runWorkflowMutation = useMutation({
    mutationFn: ({ workflowId, data }) => api.runWorkflow(workflowId, data),
    onSuccess: (result) => {
      setIsRunning(false);
      setRunningStep(null);
      toast.success('Workflow completed successfully');
      // Update node statuses
      updateNodeStatuses('completed');
    },
    onError: (error) => {
      setIsRunning(false);
      setRunningStep(null);
      toast.error(`Workflow failed: ${error.message}`);
      updateNodeStatuses('error');
    }
  });

  // Generate workflow visualization
  const generateWorkflowVisualization = useCallback((workflow) => {
    if (!workflow || !workflow.steps) return;

    const workflowNodes = [];
    const workflowEdges = [];

    // Create workflow config node
    const configNode = {
      id: 'workflow-config',
      type: 'workflowConfig',
      position: { x: 0, y: 0 },
      data: {
        name: workflow.name,
        description: workflow.description,
        steps: workflow.steps,
        settings: workflow.settings
      }
    };
    workflowNodes.push(configNode);

    // Create agent nodes
    const enabledSteps = workflow.steps.filter(step => step.enabled);
    enabledSteps.forEach((step, index) => {
      const agent = agents.find(a => a.id === step.agent_id);
      const prompt = prompts.find(p => p.id === step.prompt_id);
      
      const agentNode = {
        id: step.id,
        type: 'agent',
        position: { x: 0, y: 0 },
        data: {
          role: agent?.role || step.name,
          goal: agent?.goal || step.description,
          temperature: agent?.temperature || 0.3,
          max_iter: agent?.max_iter || 3,
          prompt_id: prompt?.name,
          status: 'pending',
          expanded: false
        }
      };
      workflowNodes.push(agentNode);

      // Create edge from previous step or config
      const sourceId = index === 0 ? 'workflow-config' : enabledSteps[index - 1].id;
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
        },
        label: step.name,
        labelStyle: {
          fontSize: 12,
          fontWeight: 500,
          fill: '#374151'
        }
      };
      workflowEdges.push(edge);
    });

    // Create output node
    const outputNode = {
      id: 'workflow-output',
      type: 'output',
      position: { x: 0, y: 0 },
      data: {
        name: 'Workflow Output',
        description: 'Final result with context and reply',
        quality_score: null
      }
    };
    workflowNodes.push(outputNode);

    // Create edge to output
    if (enabledSteps.length > 0) {
      const lastStep = enabledSteps[enabledSteps.length - 1];
      const outputEdge = {
        id: `${lastStep.id}-output`,
        source: lastStep.id,
        target: 'workflow-output',
        type: 'smoothstep',
        animated: false,
        markerEnd: {
          type: MarkerType.ArrowClosed,
          width: 20,
          height: 20,
          color: '#10b981'
        },
        style: {
          strokeWidth: 2,
          stroke: '#10b981'
        },
        label: 'Final Output',
        labelStyle: {
          fontSize: 12,
          fontWeight: 500,
          fill: '#059669'
        }
      };
      workflowEdges.push(outputEdge);
    }

    // Apply layout
    const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(
      workflowNodes,
      workflowEdges
    );

    setNodes(layoutedNodes);
    setEdges(layoutedEdges);
  }, [agents, prompts, setNodes, setEdges]);

  // Update node statuses during workflow execution
  const updateNodeStatuses = (status) => {
    setNodes(nodes => 
      nodes.map(node => 
        node.type === 'agent' 
          ? { ...node, data: { ...node.data, status } }
          : node
      )
    );
  };

  // Handle workflow selection
  const handleWorkflowSelect = (workflow) => {
    setSelectedWorkflow(workflow);
    generateWorkflowVisualization(workflow);
  };

  // Handle node click
  const onNodeClick = useCallback((event, node) => {
    setSelectedNode(node);
    setShowDetails(true);
    
    // Toggle expanded state for agent nodes
    if (node.type === 'agent') {
      setNodes(nodes => 
        nodes.map(n => 
          n.id === node.id 
            ? { ...n, data: { ...n.data, expanded: !n.data.expanded } }
            : n
        )
      );
    }
  }, [setNodes]);

  // Handle workflow execution
  const handleRunWorkflow = async () => {
    if (!selectedWorkflow) return;
    
    setIsRunning(true);
    setRunningStep(0);
    
    // Simulate step-by-step execution
    const enabledSteps = selectedWorkflow.steps.filter(step => step.enabled);
    
    for (let i = 0; i < enabledSteps.length; i++) {
      setRunningStep(i);
      
      // Update node status to running
      setNodes(nodes => 
        nodes.map(node => 
          node.id === enabledSteps[i].id 
            ? { ...node, data: { ...node.data, status: 'running' } }
            : node
        )
      );
      
      // Update edge animation
      setEdges(edges => 
        edges.map(edge => 
          edge.target === enabledSteps[i].id 
            ? { ...edge, animated: true, style: { ...edge.style, stroke: '#f59e0b' } }
            : edge
        )
      );
      
      // Simulate processing time
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Update node status to completed
      setNodes(nodes => 
        nodes.map(node => 
          node.id === enabledSteps[i].id 
            ? { ...node, data: { ...node.data, status: 'completed' } }
            : node
        )
      );
      
      // Reset edge animation
      setEdges(edges => 
        edges.map(edge => 
          edge.target === enabledSteps[i].id 
            ? { ...edge, animated: false, style: { ...edge.style, stroke: '#10b981' } }
            : edge
        )
      );
    }
    
    // Update output node with quality score
    setNodes(nodes => 
      nodes.map(node => 
        node.id === 'workflow-output' 
          ? { ...node, data: { ...node.data, quality_score: 0.87 } }
          : node
      )
    );
    
    setIsRunning(false);
    setRunningStep(null);
    toast.success('Workflow completed successfully!');
  };

  // Add Step Handler
  const handleAddStep = () => {
    if (!selectedWorkflow) return;
    const step = { ...newStep };
    if (step.type === PYTHON_STEP_TYPE) {
      step.code = newStep.code;
      step.agent_id = undefined;
      step.prompt_id = undefined;
    } else {
      step.code = undefined;
    }
    // Generate unique id if not set
    if (!step.id) step.id = `${step.name.toLowerCase().replace(/\s+/g, '_')}_${Date.now()}`;
    // Add to workflow steps
    const updatedWorkflow = {
      ...selectedWorkflow,
      steps: [...(selectedWorkflow.steps || []), step]
    };
    setSelectedWorkflow(updatedWorkflow);
    setShowAddStep(false);
    setNewStep({
      name: '', id: '', type: AGENT_STEP_TYPE, agent_id: '', prompt_id: '', code: '', inputVars: '', order: (updatedWorkflow.steps.length || 0) + 1, enabled: true, description: ''
    });
    generateWorkflowVisualization(updatedWorkflow);
  };

  // Input form for workflow input data
  const handleInputChange = (e) => {
    setInputData({ ...inputData, [e.target.name]: e.target.value });
  };

  // Auto-select first workflow
  useEffect(() => {
    if (workflows.length > 0 && !selectedWorkflow) {
      handleWorkflowSelect(workflows[0]);
    }
  }, [workflows, selectedWorkflow]);

  if (workflowsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="loading-spinner"></div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-secondary-900">Workflow Builder</h1>
          <p className="text-secondary-600">Visual workflow editor and execution monitor</p>
        </div>
        <div className="flex items-center space-x-3">
          {/* Workflow selector */}
          <select
            value={selectedWorkflow?.id || ''}
            onChange={(e) => {
              const workflow = workflows.find(w => w.id === e.target.value);
              handleWorkflowSelect(workflow);
            }}
            className="input w-64"
          >
            <option value="">Select workflow...</option>
            {workflows.map(workflow => (
              <option key={workflow.id} value={workflow.id}>
                {workflow.name}
              </option>
            ))}
          </select>
          {/* Add Step Button */}
          <button
            className="btn btn-primary"
            onClick={() => setShowAddStep(true)}
          >
            <Plus className="w-4 h-4 mr-1" /> Add Step
          </button>
          {/* Controls */}
          <button
            onClick={handleRunWorkflow}
            disabled={isRunning || !selectedWorkflow}
            className={clsx(
              'btn flex items-center space-x-2',
              isRunning ? 'btn-warning' : 'btn-success'
            )}
          >
            {isRunning ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span>Running...</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4" />
                <span>Run Workflow</span>
              </>
            )}
          </button>
          <button
            onClick={() => setShowDetails(!showDetails)}
            className="btn-secondary"
          >
            <Eye className="w-4 h-4" />
          </button>
        </div>
      </div>
      {/* Add Step Modal/Form */}
      {showAddStep && (
        <div className="fixed inset-0 bg-black bg-opacity-30 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-lg p-6 w-full max-w-lg">
            <h2 className="text-lg font-semibold mb-4">Add Workflow Step</h2>
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium mb-1">Step Name</label>
                <input type="text" className="input w-full" value={newStep.name} onChange={e => setNewStep({ ...newStep, name: e.target.value })} />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Description</label>
                <input type="text" className="input w-full" value={newStep.description} onChange={e => setNewStep({ ...newStep, description: e.target.value })} />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Type</label>
                <select className="input w-full" value={newStep.type} onChange={e => setNewStep({ ...newStep, type: e.target.value })}>
                  <option value={AGENT_STEP_TYPE}>Agent</option>
                  <option value={PYTHON_STEP_TYPE}>Python</option>
                </select>
              </div>
              {newStep.type === AGENT_STEP_TYPE && (
                <>
                  <div>
                    <label className="block text-sm font-medium mb-1">Agent</label>
                    <select className="input w-full" value={newStep.agent_id} onChange={e => setNewStep({ ...newStep, agent_id: e.target.value })}>
                      <option value="">Select agent...</option>
                      {agents.map(agent => (
                        <option key={agent.id} value={agent.id}>{agent.role}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Prompt</label>
                    <select className="input w-full" value={newStep.prompt_id} onChange={e => setNewStep({ ...newStep, prompt_id: e.target.value })}>
                      <option value="">Select prompt...</option>
                      {prompts.map(prompt => (
                        <option key={prompt.id} value={prompt.id}>{prompt.name}</option>
                      ))}
                    </select>
                  </div>
                </>
              )}
              {newStep.type === PYTHON_STEP_TYPE && (
                <>
                  <div>
                    <label className="block text-sm font-medium mb-1">Python Code</label>
                    <textarea className="input w-full font-mono min-h-32" value={newStep.code} onChange={e => setNewStep({ ...newStep, code: e.target.value })} placeholder="# Write your Python code here. Use 'input_data' for inputs and set 'result' variable for output." />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Input Variables (comma separated)</label>
                    <input className="input w-full" value={newStep.inputVars} onChange={e => setNewStep({ ...newStep, inputVars: e.target.value })} placeholder="e.g. a, b, data" />
                  </div>
                </>
              )}
            </div>
            <div className="flex items-center justify-end space-x-2 mt-6">
              <button className="btn btn-secondary" onClick={() => setShowAddStep(false)}>Cancel</button>
              <button className="btn btn-primary" onClick={handleAddStep}>Add Step</button>
            </div>
          </div>
        </div>
      )}
      {/* Input Data Form */}
      <div className="bg-secondary-50 border border-secondary-200 rounded-lg p-4 mb-4 max-w-2xl">
        <h3 className="font-semibold text-secondary-800 mb-2">Workflow Inputs</h3>
        <div className="grid grid-cols-2 gap-4">
          {selectedWorkflow?.steps?.filter(s => s.type === PYTHON_STEP_TYPE && s.inputVars)?.map((step, idx) => (
            step.inputVars.split(',').map(varName => (
              <div key={varName.trim() + idx}>
                <label className="block text-xs font-medium mb-1">{varName.trim()}</label>
                <input
                  className="input w-full"
                  name={varName.trim()}
                  value={inputData[varName.trim()] || ''}
                  onChange={handleInputChange}
                  placeholder={`Enter value for ${varName.trim()}`}
                />
              </div>
            ))
          ))}
        </div>
      </div>
      {/* Main content */}
      <div className="flex-1 grid grid-cols-12 gap-6">
        {/* Workflow visualization */}
        <div className={clsx(
          'bg-white rounded-xl border border-secondary-200 relative',
          showDetails ? 'col-span-9' : 'col-span-12'
        )}>
          <ReactFlowProvider>
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onNodeClick={onNodeClick}
              nodeTypes={nodeTypes}
              fitView
              fitViewOptions={{
                padding: 0.2,
                includeHiddenNodes: false,
              }}
              defaultViewport={{ x: 0, y: 0, zoom: 1 }}
              minZoom={0.5}
              maxZoom={2}
              attributionPosition="bottom-left"
            >
              <Controls />
              <MiniMap 
                nodeColor={(node) => {
                  switch (node.type) {
                    case 'workflowConfig': return '#3b82f6';
                    case 'agent': return '#6b7280';
                    case 'output': return '#10b981';
                    default: return '#6b7280';
                  }
                }}
                maskColor="rgb(240, 242, 247, 0.7)"
              />
              <Background variant="dots" gap={12} size={1} />
              
              {/* Status overlay */}
              {isRunning && (
                <Panel position="top-center">
                  <div className="bg-warning-100 border border-warning-300 rounded-lg px-4 py-2">
                    <div className="flex items-center space-x-2">
                      <RefreshCw className="w-4 h-4 animate-spin text-warning-600" />
                      <span className="text-sm font-medium text-warning-800">
                        Executing step {runningStep + 1}...
                      </span>
                    </div>
                  </div>
                </Panel>
              )}
            </ReactFlow>
          </ReactFlowProvider>
        </div>

        {/* Details panel */}
        {showDetails && (
          <div className="col-span-3 space-y-4">
            {selectedNode ? (
              <div className="card">
                <div className="card-header">
                  <h3 className="text-lg font-semibold">Node Details</h3>
                </div>
                <div className="card-body">
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-secondary-700 mb-1">
                        Type
                      </label>
                      <span className="badge-primary">{selectedNode.type}</span>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-secondary-700 mb-1">
                        ID
                      </label>
                      <span className="text-sm text-secondary-900 font-mono">{selectedNode.id}</span>
                    </div>
                    
                    {selectedNode.data.role && (
                      <div>
                        <label className="block text-sm font-medium text-secondary-700 mb-1">
                          Role
                        </label>
                        <span className="text-sm text-secondary-900">{selectedNode.data.role}</span>
                      </div>
                    )}
                    
                    {selectedNode.data.goal && (
                      <div>
                        <label className="block text-sm font-medium text-secondary-700 mb-1">
                          Goal
                        </label>
                        <p className="text-sm text-secondary-900">{selectedNode.data.goal}</p>
                      </div>
                    )}
                    
                    {selectedNode.data.status && (
                      <div>
                        <label className="block text-sm font-medium text-secondary-700 mb-1">
                          Status
                        </label>
                        <span className={clsx(
                          'badge text-xs',
                          selectedNode.data.status === 'completed' && 'badge-success',
                          selectedNode.data.status === 'running' && 'badge-warning',
                          selectedNode.data.status === 'error' && 'badge-error',
                          selectedNode.data.status === 'pending' && 'badge-secondary'
                        )}>
                          {selectedNode.data.status}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ) : (
              <div className="card">
                <div className="card-body flex items-center justify-center py-12">
                  <div className="text-center">
                    <Eye className="w-8 h-8 text-secondary-400 mx-auto mb-2" />
                    <p className="text-secondary-600">Click a node to view details</p>
                  </div>
                </div>
              </div>
            )}
            
            {/* Workflow info */}
            {selectedWorkflow && (
              <div className="card">
                <div className="card-header">
                  <h3 className="text-lg font-semibold">Workflow Info</h3>
                </div>
                <div className="card-body">
                  <div className="space-y-3">
                    <div>
                      <label className="block text-sm font-medium text-secondary-700 mb-1">
                        Name
                      </label>
                      <span className="text-sm text-secondary-900">{selectedWorkflow.name}</span>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-secondary-700 mb-1">
                        Description
                      </label>
                      <p className="text-sm text-secondary-900">{selectedWorkflow.description}</p>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-secondary-700 mb-1">
                        Steps
                      </label>
                      <span className="text-sm text-secondary-900">
                        {selectedWorkflow.steps?.filter(s => s.enabled).length || 0} enabled
                      </span>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-secondary-700 mb-1">
                        Parallel Execution
                      </label>
                      <span className={clsx(
                        'text-sm',
                        selectedWorkflow.settings?.parallel_execution ? 'text-success-600' : 'text-secondary-600'
                      )}>
                        {selectedWorkflow.settings?.parallel_execution ? 'Enabled' : 'Disabled'}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            )}
            {selectedNode && selectedNode.type === 'agent' && selectedWorkflow?.steps && (() => {
              const step = selectedWorkflow.steps.find(s => s.id === selectedNode.id);
              if (step && step.type === PYTHON_STEP_TYPE) {
                return (
                  <div className="mt-4">
                    <label className="block text-sm font-medium text-secondary-700 mb-1">Python Code</label>
                    <pre className="bg-secondary-50 rounded p-2 text-xs text-secondary-800 overflow-x-auto max-h-48">{step.code}</pre>
                  </div>
                );
              }
              return null;
            })()}
          </div>
        )}
      </div>
    </div>
  );
}

export default WorkflowBuilder; 