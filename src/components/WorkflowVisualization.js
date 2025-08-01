import React, { useCallback, useMemo } from 'react';
import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
  BackgroundVariant,
  Position,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import toast from 'react-hot-toast';

const WorkflowVisualization = ({ agents = [], onNodeClick, onNodeDoubleClick }) => {
  // Create nodes from agents
  const initialNodes = useMemo(() => {
    if (!agents || agents.length === 0) return [];
    
    const nodeSpacing = 200;
    const startX = 100;
    const startY = 100;
    
    return agents.map((agent, index) => {
      // Ensure unique and valid node ID
      const nodeId = agent.id || `agent-${index}`;
      
      return {
        id: nodeId,
        type: 'default',
        position: { 
          x: startX + (index % 3) * nodeSpacing, 
          y: startY + Math.floor(index / 3) * nodeSpacing 
        },
        data: { 
          label: (
            <div className="agent-node">
              <div className="agent-title">{agent.name || 'Unnamed Agent'}</div>
              <div className="agent-role">{agent.role || 'No role defined'}</div>
              <div className="agent-status">
                <span className={`status-indicator ${agent.status || 'ready'}`}></span>
                {agent.status || 'Ready'}
              </div>
            </div>
          ),
          agent: agent
        },
        sourcePosition: Position.Right,
        targetPosition: Position.Left,
        style: {
          background: '#ffffff',
          border: '2px solid #e2e8f0',
          borderRadius: '8px',
          padding: '10px',
          minWidth: '180px',
          boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
        },
      };
    });
  }, [agents]);

  // Create edges based on agent dependencies
  const initialEdges = useMemo(() => {
    if (!agents || agents.length === 0) return [];
    
    const edges = [];
    agents.forEach((agent, index) => {
      // Create connections based on agent order (simple sequential flow)
      if (index > 0 && agents[index - 1] && agent) {
        const sourceId = agents[index - 1].id || `agent-${index - 1}`;
        const targetId = agent.id || `agent-${index}`;
        
        // Ensure edge has unique ID and proper configuration
        const edgeId = `${sourceId}-to-${targetId}`;
        
        edges.push({
          id: edgeId,
          source: sourceId,
          target: targetId,
          type: 'smoothstep',
          animated: true,
          style: {
            stroke: '#3b82f6',
            strokeWidth: 2,
          },
          markerEnd: {
            type: 'arrowclosed',
            color: '#3b82f6',
          },
        });
      }
    });
    return edges;
  }, [agents]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  const onConnect = useCallback(
    (params) => {
      // Validate connection parameters to prevent React Flow errors
      if (!params.source || !params.target) {
        console.warn('Invalid connection parameters:', params);
        toast.error('Invalid connection - missing source or target');
        return;
      }
      
      // Create edge with proper configuration and check for duplicates in the setter
      const newEdge = {
        ...params,
        id: `${params.source}-to-${params.target}-${Date.now()}`, // Add timestamp to ensure uniqueness
        type: 'smoothstep',
        animated: true,
        style: {
          stroke: '#3b82f6',
          strokeWidth: 2,
        },
        markerEnd: {
          type: 'arrowclosed',
          color: '#3b82f6',
        },
      };
      
      setEdges((currentEdges) => {
        // Check if this connection already exists
        const connectionExists = currentEdges.some(edge => 
          edge.source === params.source && edge.target === params.target
        );
        
        if (connectionExists) {
          toast.warn('Connection already exists');
          return currentEdges; // Return unchanged edges
        }
        
        return addEdge(newEdge, currentEdges);
      });
      toast.success('Connected agents in workflow');
    },
    [setEdges]
  );

  const onNodeClickHandler = useCallback((event, node) => {
    if (onNodeClick) {
      onNodeClick(node.data.agent);
    }
    toast(`Selected agent: ${node.data.agent.name}`);
  }, [onNodeClick]);

  const onNodeDoubleClickHandler = useCallback((event, node) => {
    if (onNodeDoubleClick) {
      onNodeDoubleClick(node.data.agent);
    }
    toast(`Editing agent: ${node.data.agent.name}`);
  }, [onNodeDoubleClick]);

  return (
    <div className="workflow-visualization" style={{ width: '100%', height: '600px' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onNodeClick={onNodeClickHandler}
        onNodeDoubleClick={onNodeDoubleClickHandler}
        fitView
        attributionPosition="top-right"
      >
        <Controls />
        <MiniMap 
          nodeColor={(node) => {
            const status = node.data.agent?.status || 'ready';
            switch (status) {
              case 'running': return '#f59e0b';
              case 'completed': return '#10b981';
              case 'error': return '#ef4444';
              default: return '#6b7280';
            }
          }}
        />
        <Background variant={BackgroundVariant.Dots} gap={12} size={1} />
      </ReactFlow>
      
      <style>{`
        .workflow-visualization {
          border: 1px solid #e2e8f0;
          border-radius: 8px;
          overflow: hidden;
        }
        
        .react-flow__node {
          border: 2px solid #e2e8f0;
          border-radius: 8px;
          background: white;
          padding: 12px;
          min-width: 120px;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        
        .react-flow__node.selected {
          border-color: #3b82f6;
        }
        
        .agent-name {
          font-weight: 600;
          font-size: 12px;
          color: #1f2937;
        }
        
        .agent-role {
          color: #6b7280;
          margin-bottom: 8px;
          font-size: 10px;
        }
        
        .agent-status {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 4px;
          font-size: 10px;
        }
        
        .status-indicator {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background: #6b7280;
        }
        
        .status-indicator.ready {
          background: #6b7280;
        }
        
        .status-indicator.running {
          background: #f59e0b;
          animation: pulse 2s infinite;
        }
        
        .status-indicator.completed {
          background: #10b981;
        }
        
        .status-indicator.error {
          background: #ef4444;
        }
        
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
      `}</style>
    </div>
  );
};

export default WorkflowVisualization; 