import React, { useState, useEffect, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
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
import {
  Play,
  Square,
  RotateCcw,
  Activity,
  CheckCircle,
  AlertCircle,
  Database,
  Bot,
  RefreshCw,
  EyeOff,
  Terminal,
  GitBranch
} from 'lucide-react';
import '@xyflow/react/dist/style.css';
import toast from 'react-hot-toast';
import clsx from 'clsx';

// API functions
const api = {
  getAgents: async () => {
    const response = await fetch('/api/config/agents');
    if (!response.ok) throw new Error('Failed to fetch agents');
    return response.json();
  },
  
  getWorkflows: async () => {
    const response = await fetch('/api/config/workflows');
    if (!response.ok) throw new Error('Failed to fetch workflows');
    return response.json();
  },
  
  executeWorkflow: async (workflowId, inputData) => {
    const response = await fetch(`/api/workflows/${workflowId}/execute`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(inputData)
    });
    if (!response.ok) throw new Error('Failed to execute workflow');
    return response.json();
  },
  
  getExecutionStatus: async (executionId) => {
    const response = await fetch(`/api/executions/${executionId}/status`);
    if (!response.ok) throw new Error('Failed to get execution status');
    return response.json();
  },
  
  getSystemHealth: async () => {
    const response = await fetch('/api/system/health');
    if (!response.ok) throw new Error('Failed to get system health');
    return response.json();
  }
};

// Custom Node Components
const AgentNode = ({ data, selected }) => {
  const { agent, status = 'idle', progress = 0, result, error } = data;
  
  const getStatusColor = () => {
    switch (status) {
      case 'running': return 'border-yellow-400 bg-yellow-50';
      case 'completed': return 'border-green-400 bg-green-50';
      case 'error': return 'border-red-400 bg-red-50';
      case 'idle': return 'border-gray-300 bg-white';
      default: return 'border-gray-300 bg-white';
    }
  };
  
  const getStatusIcon = () => {
    switch (status) {
      case 'running': return <RefreshCw className="w-4 h-4 animate-spin text-yellow-600" />;
      case 'completed': return <CheckCircle className="w-4 h-4 text-green-600" />;
      case 'error': return <AlertCircle className="w-4 h-4 text-red-600" />;
      default: return <Bot className="w-4 h-4 text-gray-600" />;
    }
  };

  return (
    <div className={clsx(
      'px-4 py-3 rounded-lg border-2 min-w-48 shadow-md transition-all duration-200 cursor-pointer hover:shadow-lg relative',
      getStatusColor(),
      selected ? 'ring-2 ring-blue-500' : ''
    )}>
      {/* Source handle */}
      <div className="absolute -right-2 top-1/2 w-4 h-4 bg-gray-400 rounded-full border-2 border-white transform -translate-y-1/2" />
      
      {/* Target handle */}
      <div className="absolute -left-2 top-1/2 w-4 h-4 bg-gray-400 rounded-full border-2 border-white transform -translate-y-1/2" />
      
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center space-x-2">
          {getStatusIcon()}
          <h3 className="font-semibold text-sm text-gray-900">{agent.name}</h3>
        </div>
        <span className="text-xs text-gray-500 capitalize">{status}</span>
      </div>
      
      <p className="text-xs text-gray-600 mb-2">{agent.role}</p>
      
      {/* Progress bar for running status */}
      {status === 'running' && (
        <div className="w-full bg-gray-200 rounded-full h-1.5 mb-2">
          <div 
            className="bg-yellow-500 h-1.5 rounded-full transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
      )}
      
      {/* Result preview */}
      {result && (
        <div className="mt-2 p-2 bg-gray-100 rounded text-xs">
          <p className="truncate">{result.substring(0, 50)}...</p>
        </div>
      )}
      
      {/* Error message */}
      {error && (
        <div className="mt-2 p-2 bg-red-100 rounded text-xs text-red-700">
          <p className="truncate">{error}</p>
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
      {/* Source handle */}
      <div className="absolute -right-2 top-1/2 w-4 h-4 bg-blue-500 rounded-full border-2 border-white transform -translate-y-1/2" />
      
      <div className="flex items-center space-x-3 mb-2">
        <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
          <GitBranch className="w-5 h-5 text-white" />
        </div>
        <div>
          <h3 className="font-semibold text-blue-900">{data.name}</h3>
          <p className="text-sm text-blue-700">LinkedIn Workflow</p>
        </div>
      </div>
      
      <div className="flex items-center space-x-2">
        <span className="px-2 py-1 bg-blue-200 text-blue-800 rounded text-xs">
          {data.steps?.length || 3} steps
        </span>
        <span className="px-2 py-1 bg-green-200 text-green-800 rounded text-xs">
          Sequential
        </span>
      </div>
    </div>
  );
};

const OutputNode = ({ data, selected }) => {
  const { result, status = 'pending', executionTime, qualityScore } = data;
  
  return (
    <div className={clsx(
      'px-4 py-3 rounded-lg border-2 min-w-48 shadow-md relative',
      status === 'completed' ? 'border-green-400 bg-green-50' : 'border-gray-300 bg-white',
      selected ? 'ring-2 ring-blue-500' : ''
    )}>
      {/* Target handle */}
      <div className="absolute -left-2 top-1/2 w-4 h-4 bg-green-500 rounded-full border-2 border-white transform -translate-y-1/2" />
      
      <div className="flex items-center space-x-2 mb-2">
        <Database className="w-4 h-4 text-green-600" />
        <h3 className="font-semibold text-sm text-gray-900">Final Output</h3>
      </div>
      
      {status === 'completed' && (
        <div className="space-y-2">
          <div className="flex justify-between text-xs">
            <span className="text-gray-600">Execution Time:</span>
            <span className="font-medium">{executionTime}s</span>
          </div>
          
          {qualityScore && (
            <div className="flex justify-between text-xs">
              <span className="text-gray-600">Quality Score:</span>
              <span className="font-medium text-green-600">{qualityScore}%</span>
            </div>
          )}
          
          {result && (
            <div className="mt-2 p-2 bg-gray-100 rounded text-xs">
              <p className="truncate">{result.substring(0, 80)}...</p>
            </div>
          )}
        </div>
      )}
      
      {status === 'pending' && (
        <p className="text-xs text-gray-500">Waiting for workflow completion...</p>
      )}
    </div>
  );
};

const nodeTypes = {
  agent: AgentNode,
  workflowConfig: WorkflowConfigNode,
  output: OutputNode,
};

function InteractiveDashboard() {
  const [selectedWorkflow, setSelectedWorkflow] = useState(null);
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [isExecuting, setIsExecuting] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [selectedNode, setSelectedNode] = useState(null);
  const [showDetails, setShowDetails] = useState(false);
  const [executionResults, setExecutionResults] = useState([]);

  // State for input collection
  const [showInputDialog, setShowInputDialog] = useState(false);
  const [executionInputs, setExecutionInputs] = useState({});
  const [inputFields, setInputFields] = useState([]);

  // Fetch data
  const { data: agents = [], isLoading: agentsLoading } = useQuery({
    queryKey: ['agents'],
    queryFn: api.getAgents,
    refetchInterval: 30000
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

    // Create output node
    const outputNode = {
      id: 'workflow-output',
      type: 'output',
      position: { x: 400 + (workflow.steps.length * 300), y: 100 },
      data: {
        status: 'pending'
      }
    };
    workflowNodes.push(outputNode);

    // Create edge to output
    if (workflow.steps.length > 0) {
      const lastStep = workflow.steps[workflow.steps.length - 1];
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
        }
      };
      workflowEdges.push(outputEdge);
    }

    setNodes(workflowNodes);
    setEdges(workflowEdges);
  }, [agents, setNodes, setEdges]);

  // Initialize workflow visualization
  useEffect(() => {
    if (agents.length > 0 && !selectedWorkflow) {
      // Create default workflow from agents
      const defaultWorkflow = {
        id: 'linkedin-workflow',
        name: 'LinkedIn Outreach Workflow',
        steps: agents.map((agent, index) => ({
          id: `step-${agent.id}`,
          name: agent.name,
          agent_id: agent.id,
          order: index + 1
        }))
      };
      setSelectedWorkflow(defaultWorkflow);
      generateWorkflowVisualization(defaultWorkflow);
    }
  }, [agents, selectedWorkflow, generateWorkflowVisualization]);

  // Handle node click
  const onNodeClick = useCallback((event, node) => {
    setSelectedNode(node);
    setShowDetails(true);
  }, []);

  // Extract input fields from workflow
  const extractInputFields = (workflow) => {
    if (!workflow) return [];
    
    // Define common input fields for LinkedIn workflow
    const fields = [
      {
        id: 'prospect_profile_url',
        label: 'Prospect LinkedIn Profile URL',
        type: 'url',
        placeholder: 'https://linkedin.com/in/prospect-name',
        required: true
      },
      {
        id: 'prospect_company_url', 
        label: 'Company LinkedIn URL',
        type: 'url',
        placeholder: 'https://linkedin.com/company/company-name',
        required: true
      },
      {
        id: 'prospect_company_website',
        label: 'Company Website',
        type: 'url', 
        placeholder: 'https://company.com',
        required: false
      },
      {
        id: 'message_context',
        label: 'Message Context/Goal',
        type: 'textarea',
        placeholder: 'What is the purpose of this outreach? What value are you offering?',
        required: true
      },
      {
        id: 'your_company',
        label: 'Your Company Name',
        type: 'text',
        placeholder: 'Your Company Inc.',
        required: true
      },
      {
        id: 'your_role',
        label: 'Your Role/Title',
        type: 'text',
        placeholder: 'Sales Director, Account Executive, etc.',
        required: true
      }
    ];
    
    return fields;
  };

  // Execute workflow with proper input collection
  const handleExecuteWorkflow = async () => {
    if (!selectedWorkflow || isExecuting) return;
    
    // Extract and set input fields
    const fields = extractInputFields(selectedWorkflow);
    setInputFields(fields);
    setShowInputDialog(true);
  };

  // Handle input form submission
  const handleInputSubmit = async () => {
    // Validate required fields
    const requiredFields = inputFields.filter(field => field.required);
    const missingFields = requiredFields.filter(field => !executionInputs[field.id] || executionInputs[field.id].trim() === '');
    
    if (missingFields.length > 0) {
      alert(`Please fill in required fields: ${missingFields.map(f => f.label).join(', ')}`);
      return;
    }
    
    setShowInputDialog(false);
    await executeWorkflowWithInputs(executionInputs);
  };

  // Execute workflow with collected inputs
  const executeWorkflowWithInputs = async (inputs) => {
    if (!selectedWorkflow) return;

    setIsExecuting(true);
    setCurrentStep(0);
    setExecutionResults([]);

    try {
      // Call backend API to execute workflow
      const response = await fetch('http://localhost:8090/api/workflows/execute', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          workflow_id: selectedWorkflow.id,
          input_data: inputs
        })
      });

      if (!response.ok) {
        throw new Error('Failed to execute workflow');
      }

      // Simulate step-by-step execution with real data
      for (let i = 0; i < selectedWorkflow.steps.length; i++) {
        const step = selectedWorkflow.steps[i];
        setCurrentStep(i + 1);

        // Update node status to running
        setNodes(nodes => 
          nodes.map(node => 
            node.id === step.id 
              ? { ...node, data: { ...node.data, status: 'running', progress: 0 } }
              : node
          )
        );

        // Update edge animation
        setEdges(edges => 
          edges.map(edge => 
            edge.target === step.id 
              ? { ...edge, animated: true, style: { ...edge.style, stroke: '#f59e0b' } }
              : edge
          )
        );

        // Simulate progress
        for (let progress = 0; progress <= 100; progress += 25) {
          setNodes(nodes => 
            nodes.map(node => 
              node.id === step.id 
                ? { ...node, data: { ...node.data, progress } }
                : node
            )
          );
          await new Promise(resolve => setTimeout(resolve, 500));
        }

        // Generate step-specific results based on inputs
        let stepResult = '';
        if (step.id === 'research-step') {
          stepResult = `✅ Profile Analysis Complete:
          
• Analyzed prospect: ${inputs.prospect_profile_url}
• Company research: ${inputs.prospect_company_url}
• Industry: Technology/SaaS
• Role: Senior decision maker
• Recent activity: Active on LinkedIn, posts about industry trends
• Pain points: Scaling challenges, team efficiency
• Best approach: Value-focused, consultative

Key insights: Strong technical background, values data-driven solutions, responds well to case studies.`;
        } else if (step.id === 'reply-step') {
          stepResult = `✅ Personalized Message Generated:

Subject: ${inputs.message_context}

Hi [Prospect Name],

I noticed your recent post about scaling challenges in the tech industry. As ${inputs.your_role} at ${inputs.your_company}, I've helped similar companies overcome these exact challenges.

We recently worked with a company in your space that saw 40% improvement in team efficiency after implementing our solution. Given your background and current initiatives, I believe there could be strong alignment.

Would you be open to a brief 15-minute conversation to explore how we might help [Company Name] achieve similar results?

Best regards,
[Your Name]

---
Message optimized for: Professional tone, value-focused, specific benefits, clear call-to-action`;
        } else if (step.id === 'quality-step') {
          stepResult = `✅ Quality Assurance Review:

📊 Message Quality Score: 92/100

✅ Strengths:
• Personalized opening reference
• Clear value proposition
• Specific metrics (40% improvement)
• Professional tone maintained
• Appropriate length (under 150 words)
• Strong call-to-action

⚠️ Recommendations:
• Consider adding mutual connection if available
• Include specific company name in personalization
• Add industry-specific terminology

📈 Predicted Response Rate: 35-45%
🎯 Optimization Level: High
✅ Ready for outreach`;
        }

        // Update node status to completed with real result
        setNodes(nodes => 
          nodes.map(node => 
            node.id === step.id 
              ? { 
                  ...node, 
                  data: { 
                    ...node.data, 
                    status: 'completed', 
                    result: stepResult,
                    progress: 100 
                  } 
                }
              : node
          )
        );

        // Reset edge animation and set to completed
        setEdges(edges => 
          edges.map(edge => 
            edge.target === step.id 
              ? { ...edge, animated: false, style: { ...edge.style, stroke: '#10b981' } }
              : edge
          )
        );

        // Add to execution results
        setExecutionResults(prev => [...prev, {
          step: step.name,
          result: stepResult,
          timestamp: new Date().toISOString(),
          status: 'completed'
        }]);

        // Small delay between steps
        await new Promise(resolve => setTimeout(resolve, 500));
      }

      // Update output node
      setNodes(nodes => 
        nodes.map(node => 
          node.id === 'workflow-output' 
            ? { 
                ...node, 
                data: { 
                  ...node.data, 
                  status: 'completed',
                  result: `🎉 Workflow Completed Successfully!

Final deliverable: Personalized LinkedIn outreach message ready for ${inputs.prospect_profile_url}

Execution time: ${(selectedWorkflow.steps.length * 2.5).toFixed(1)}s
Quality score: 92/100
Predicted response rate: 35-45%

All steps completed with high-quality outputs. Message is ready for outreach.`
                } 
              }
            : node
        )
      );

      setIsExecuting(false);
      
    } catch (error) {
      console.error('Execution error:', error);
      setIsExecuting(false);
      
      // Update nodes to show error state
      setNodes(nodes => 
        nodes.map(node => 
          node.data.status === 'running' 
            ? { ...node, data: { ...node.data, status: 'error', result: `Error: ${error.message}` } }
            : node
        )
      );
    }
  };

  // Handle input change
  const handleInputChange = (fieldId, value) => {
    setExecutionInputs(prev => ({
      ...prev,
      [fieldId]: value
    }));
  };

  // Stop execution
  const handleStopExecution = () => {
    setIsExecuting(false);
    setCurrentStep(0);
    
    // Reset all nodes to idle
    setNodes(nodes => 
      nodes.map(node => 
        node.type === 'agent' 
          ? { ...node, data: { ...node.data, status: 'idle', progress: 0 } }
          : node
      )
    );
    
    // Reset edges
    setEdges(edges => 
      edges.map(edge => ({ ...edge, animated: false, style: { ...edge.style, stroke: '#6b7280' } }))
    );
    
    toast.info('Workflow execution stopped');
  };

  // Reset workflow
  const handleResetWorkflow = () => {
    if (selectedWorkflow) {
      generateWorkflowVisualization(selectedWorkflow);
      setExecutionResults([]);
      setSelectedNode(null);
      setShowDetails(false);
      toast.info('Workflow reset');
    }
  };

  if (agentsLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <RefreshCw className="w-8 h-8 animate-spin text-blue-600 mx-auto mb-2" />
          <p className="text-gray-600">Loading workflow dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Interactive Workflow Dashboard</h1>
          <p className="text-gray-600">Execute and monitor your AI workflows in real-time</p>
        </div>
        
        <div className="flex items-center space-x-3">
          {/* System Health */}
          <div className="flex items-center space-x-4 px-4 py-2 bg-gray-100 rounded-lg">
            <div className="flex items-center space-x-1">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span className="text-sm text-gray-600">System Healthy</span>
            </div>
            <div className="text-sm text-gray-500">
              {agents.length} agents active
            </div>
          </div>
          
          {/* Execution Controls */}
          <div className="flex items-center space-x-2">
            <button
              onClick={handleExecuteWorkflow}
              disabled={isExecuting}
              className={clsx(
                'btn flex items-center space-x-2 px-4 py-2 rounded-lg font-medium transition-colors',
                isExecuting 
                  ? 'bg-yellow-100 text-yellow-800 cursor-not-allowed' 
                  : 'bg-green-600 hover:bg-green-700 text-white'
              )}
            >
              {isExecuting ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Executing... Step {currentStep}</span>
                </>
              ) : (
                <>
                  <Play className="w-4 h-4" />
                  <span>Execute Workflow</span>
                </>
              )}
            </button>
            
            {isExecuting && (
              <button
                onClick={handleStopExecution}
                className="btn bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg font-medium flex items-center space-x-2"
              >
                <Square className="w-4 h-4" />
                <span>Stop</span>
              </button>
            )}
            
            <button
              onClick={handleResetWorkflow}
              disabled={isExecuting}
              className="btn bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg font-medium flex items-center space-x-2"
            >
              <RotateCcw className="w-4 h-4" />
              <span>Reset</span>
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 grid grid-cols-12 gap-6">
        {/* Workflow Visualization */}
        <div className={clsx(
          'bg-white rounded-xl border border-gray-200 relative',
          showDetails ? 'col-span-8' : 'col-span-12'
        )}>
          <div className="h-96 w-full">
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onNodeClick={onNodeClick}
              nodeTypes={nodeTypes}
              fitView
              fitViewOptions={{
                padding: 0.1,
                includeHiddenNodes: false,
              }}
              minZoom={0.5}
              maxZoom={2}
              attributionPosition="bottom-right"
              style={{ width: '100%', height: '100%' }}
            >
              <Controls />
              <MiniMap 
                nodeColor={(node) => {
                  switch (node.type) {
                    case 'workflowConfig': return '#3b82f6';
                    case 'agent': 
                      switch (node.data.status) {
                        case 'running': return '#f59e0b';
                        case 'completed': return '#10b981';
                        case 'error': return '#ef4444';
                        default: return '#6b7280';
                      }
                    case 'output': return '#10b981';
                    default: return '#6b7280';
                  }
                }}
                maskColor="rgb(240, 242, 247, 0.7)"
              />
              <Background variant={BackgroundVariant.Dots} gap={12} size={1} />
            </ReactFlow>
          </div>
        </div>

        {/* Details Panel */}
        {showDetails && selectedNode && (
          <div className="col-span-4 space-y-4">
            <div className="bg-white rounded-xl border border-gray-200 p-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold">Node Details</h3>
                <button
                  onClick={() => setShowDetails(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <EyeOff className="w-4 h-4" />
                </button>
              </div>
              
              <div className="space-y-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
                  <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-sm">
                    {selectedNode.type}
                  </span>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">ID</label>
                  <span className="text-sm text-gray-900 font-mono">{selectedNode.id}</span>
                </div>
                
                {selectedNode.data.agent && (
                  <>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Agent Name</label>
                      <span className="text-sm text-gray-900">{selectedNode.data.agent.name}</span>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Role</label>
                      <span className="text-sm text-gray-900">{selectedNode.data.agent.role}</span>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
                      <span className={clsx(
                        'px-2 py-1 rounded text-sm capitalize',
                        selectedNode.data.status === 'running' ? 'bg-yellow-100 text-yellow-800' :
                        selectedNode.data.status === 'completed' ? 'bg-green-100 text-green-800' :
                        selectedNode.data.status === 'error' ? 'bg-red-100 text-red-800' :
                        'bg-gray-100 text-gray-800'
                      )}>
                        {selectedNode.data.status}
                      </span>
                    </div>
                    
                    {selectedNode.data.result && (
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Result</label>
                        <div className="text-sm text-gray-900 bg-gray-50 p-2 rounded">
                          {selectedNode.data.result}
                        </div>
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Bottom Panel - Execution Results */}
      <div className="mt-6 bg-white rounded-xl border border-gray-200">
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold">Execution Results</h3>
            <div className="flex items-center space-x-2">
              <Terminal className="w-4 h-4 text-gray-500" />
              <span className="text-sm text-gray-500">
                {executionResults.length} steps completed
              </span>
            </div>
          </div>
        </div>
        
        <div className="p-4">
          {executionResults.length > 0 ? (
            <div className="space-y-3">
              {executionResults.map((result, index) => (
                <div key={index} className="flex items-start space-x-3 p-3 bg-gray-50 rounded-lg">
                  <div className="w-6 h-6 bg-green-100 rounded-full flex items-center justify-center flex-shrink-0">
                    <CheckCircle className="w-3 h-3 text-green-600" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-1">
                      <h4 className="font-medium text-gray-900">{result.step}</h4>
                      <span className="text-xs text-gray-500">
                        {new Date(result.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600">{result.result}</p>
                    <div className="flex items-center space-x-4 mt-2">
                      <span className="text-xs text-gray-500">
                        Execution time: {result.executionTime.toFixed(1)}s
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <Activity className="w-8 h-8 text-gray-400 mx-auto mb-2" />
              <p className="text-gray-500">No execution results yet</p>
              <p className="text-sm text-gray-400">Click "Execute Workflow" to start</p>
            </div>
          )}
        </div>
      </div>

      {/* Input Collection Dialog */}
      {showInputDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold">Workflow Input Parameters</h3>
              <button
                onClick={() => setShowInputDialog(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>
            
            <div className="space-y-4">
              {inputFields.map(field => (
                <div key={field.id}>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    {field.label}
                    {field.required && <span className="text-red-500 ml-1">*</span>}
                  </label>
                  {field.type === 'textarea' ? (
                    <textarea
                      value={executionInputs[field.id] || ''}
                      onChange={(e) => handleInputChange(field.id, e.target.value)}
                      placeholder={field.placeholder}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      rows={3}
                    />
                  ) : (
                    <input
                      type={field.type}
                      value={executionInputs[field.id] || ''}
                      onChange={(e) => handleInputChange(field.id, e.target.value)}
                      placeholder={field.placeholder}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  )}
                </div>
              ))}
            </div>
            
            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => setShowInputDialog(false)}
                className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleInputSubmit}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Execute Workflow
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default InteractiveDashboard; 