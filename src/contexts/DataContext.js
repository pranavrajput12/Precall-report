import React, { createContext, useContext, useState, useEffect } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';

// Create the context
const DataContext = createContext(null);

// API functions
const api = {
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
  },
  
  getExecutionHistory: async () => {
    const response = await fetch('/api/execution-history');
    if (!response.ok) throw new Error('Failed to fetch execution history');
    const data = await response.json();
    return data.items || [];
  },
  
  getTestResults: async () => {
    const response = await fetch('/api/test-results');
    if (!response.ok) throw new Error('Failed to fetch test results');
    return response.json();
  },
  
  getSystemHealth: async () => {
    const response = await fetch('/api/system/health');
    if (!response.ok) throw new Error('Failed to fetch system health');
    return response.json();
  },
  
  // Composite endpoint for dashboard data
  getDashboardData: async () => {
    try {
      const response = await fetch('/api/dashboard/data');
      if (response.ok) {
        return response.json();
      }
    } catch (error) {
      console.log('Composite endpoint not available, falling back to individual calls');
    }
    
    // Fallback to individual calls if composite endpoint doesn't exist
    const [agents, prompts, workflows, tools, health] = await Promise.all([
      api.getAgents(),
      api.getPrompts(),
      api.getWorkflows(),
      api.getTools(),
      api.getSystemHealth()
    ]);
    
    return { agents, prompts, workflows, tools, health };
  }
};

// Data Provider Component
export function DataProvider({ children }) {
  const queryClient = useQueryClient();
  const [isInitialized, setIsInitialized] = useState(false);

  // Fetch all data with React Query
  const { data: agents = [], isLoading: agentsLoading } = useQuery({
    queryKey: ['agents'],
    queryFn: api.getAgents,
    staleTime: 5 * 60 * 1000, // 5 minutes
    cacheTime: 10 * 60 * 1000, // 10 minutes
  });

  const { data: prompts = [], isLoading: promptsLoading } = useQuery({
    queryKey: ['prompts'],
    queryFn: api.getPrompts,
    staleTime: 5 * 60 * 1000,
    cacheTime: 10 * 60 * 1000,
  });

  const { data: workflows = [], isLoading: workflowsLoading } = useQuery({
    queryKey: ['workflows'],
    queryFn: api.getWorkflows,
    staleTime: 5 * 60 * 1000,
    cacheTime: 10 * 60 * 1000,
  });

  const { data: tools = [], isLoading: toolsLoading } = useQuery({
    queryKey: ['tools'],
    queryFn: api.getTools,
    staleTime: 5 * 60 * 1000,
    cacheTime: 10 * 60 * 1000,
  });

  const { data: executionHistory = [], isLoading: historyLoading } = useQuery({
    queryKey: ['execution-history'],
    queryFn: api.getExecutionHistory,
    staleTime: 30 * 1000, // 30 seconds - more frequent updates
    cacheTime: 60 * 1000, // 1 minute
    refetchInterval: 30 * 1000, // Auto-refresh every 30 seconds
  });

  const { data: testResults = [], isLoading: testResultsLoading } = useQuery({
    queryKey: ['test-results'],
    queryFn: api.getTestResults,
    staleTime: 60 * 1000,
    cacheTime: 5 * 60 * 1000,
  });

  const { data: systemHealth = {}, isLoading: healthLoading } = useQuery({
    queryKey: ['system-health'],
    queryFn: api.getSystemHealth,
    staleTime: 10 * 1000, // 10 seconds
    cacheTime: 30 * 1000,
    refetchInterval: 30 * 1000, // Auto-refresh every 30 seconds
  });

  // Dashboard data with composite endpoint
  const { data: dashboardData, isLoading: dashboardLoading } = useQuery({
    queryKey: ['dashboard-data'],
    queryFn: api.getDashboardData,
    staleTime: 60 * 1000,
    cacheTime: 5 * 60 * 1000,
  });

  // Track initialization
  useEffect(() => {
    if (!agentsLoading && !promptsLoading && !workflowsLoading && !toolsLoading) {
      setIsInitialized(true);
    }
  }, [agentsLoading, promptsLoading, workflowsLoading, toolsLoading]);

  // Refresh functions
  const refreshAgents = async () => {
    await queryClient.invalidateQueries({ queryKey: ['agents'] });
    toast.success('Agents refreshed');
  };

  const refreshPrompts = async () => {
    await queryClient.invalidateQueries({ queryKey: ['prompts'] });
    toast.success('Prompts refreshed');
  };

  const refreshWorkflows = async () => {
    await queryClient.invalidateQueries({ queryKey: ['workflows'] });
    toast.success('Workflows refreshed');
  };

  const refreshTools = async () => {
    await queryClient.invalidateQueries({ queryKey: ['tools'] });
    toast.success('Tools refreshed');
  };

  const refreshExecutionHistory = async () => {
    await queryClient.invalidateQueries({ queryKey: ['execution-history'] });
    toast.success('Execution history refreshed');
  };

  const refreshAll = async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ['agents'] }),
      queryClient.invalidateQueries({ queryKey: ['prompts'] }),
      queryClient.invalidateQueries({ queryKey: ['workflows'] }),
      queryClient.invalidateQueries({ queryKey: ['tools'] }),
      queryClient.invalidateQueries({ queryKey: ['execution-history'] }),
      queryClient.invalidateQueries({ queryKey: ['test-results'] }),
      queryClient.invalidateQueries({ queryKey: ['system-health'] }),
      queryClient.invalidateQueries({ queryKey: ['dashboard-data'] }),
    ]);
    toast.success('All data refreshed');
  };

  // Loading state
  const isLoading = agentsLoading || promptsLoading || workflowsLoading || 
                    toolsLoading || historyLoading || testResultsLoading || 
                    healthLoading || dashboardLoading;

  // Context value
  const value = {
    // Data
    agents,
    prompts,
    workflows,
    tools,
    executionHistory,
    testResults,
    systemHealth,
    dashboardData,
    
    // Loading states
    isLoading,
    isInitialized,
    agentsLoading,
    promptsLoading,
    workflowsLoading,
    toolsLoading,
    historyLoading,
    testResultsLoading,
    healthLoading,
    dashboardLoading,
    
    // Refresh functions
    refreshAgents,
    refreshPrompts,
    refreshWorkflows,
    refreshTools,
    refreshExecutionHistory,
    refreshAll,
    
    // Query client for advanced usage
    queryClient,
  };

  return (
    <DataContext.Provider value={value}>
      {children}
    </DataContext.Provider>
  );
}

// Custom hook to use the data context
export function useData() {
  const context = useContext(DataContext);
  if (!context) {
    throw new Error('useData must be used within a DataProvider');
  }
  return context;
}

// Export individual hooks for convenience
export function useAgents() {
  const { agents, agentsLoading, refreshAgents } = useData();
  return { agents, isLoading: agentsLoading, refresh: refreshAgents };
}

export function usePrompts() {
  const { prompts, promptsLoading, refreshPrompts } = useData();
  return { prompts, isLoading: promptsLoading, refresh: refreshPrompts };
}

export function useWorkflows() {
  const { workflows, workflowsLoading, refreshWorkflows } = useData();
  return { workflows, isLoading: workflowsLoading, refresh: refreshWorkflows };
}

export function useTools() {
  const { tools, toolsLoading, refreshTools } = useData();
  return { tools, isLoading: toolsLoading, refresh: refreshTools };
}

export function useExecutionHistory() {
  const { executionHistory, historyLoading, refreshExecutionHistory } = useData();
  return { executionHistory, isLoading: historyLoading, refresh: refreshExecutionHistory };
}

export function useSystemHealth() {
  const { systemHealth, healthLoading } = useData();
  return { systemHealth, isLoading: healthLoading };
}