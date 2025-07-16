import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import { scan } from 'react-scan';
import AgentManager from './components/AgentManager';
import PromptManager from './components/PromptManager';
import WorkflowVisualization from './components/WorkflowVisualization';
import InteractiveDashboard from './components/InteractiveDashboard';
import PerformanceDashboard from './components/PerformanceDashboard';
import EnhancedPromptEditor from './components/EnhancedPromptEditor';
import ObservabilityDashboard from './pages/ObservabilityDashboard';
import EvaluationDashboard from './pages/EvaluationDashboard';
import ModelManagement from './pages/ModelManagement';
import ModelAssignments from './pages/ModelAssignments';
import WorkflowBuilder from './components/WorkflowBuilder';
import ToolManager from './components/ToolManager';
import Settings from './components/Settings';
import Sidebar from './components/Sidebar';
import ExecutionHistory from './components/ExecutionHistory';
import KnowledgeBase from './components/KnowledgeBase';
import './App.css';

// Initialize React Scan for performance monitoring
if (process.env.NODE_ENV === 'development') {
  scan({
    enabled: true,
    log: false,
    showToolbar: true,
    animationSpeed: 'fast',
  });
}

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
    mutations: {
      retry: 1,
    },
  },
});

function App() {
  const [sidebarOpen, setSidebarOpen] = React.useState(false);
  const [currentPage, setCurrentPage] = React.useState('dashboard');
  const [agents, setAgents] = React.useState([]);
  const [prompts, setPrompts] = React.useState([]);
  const [executionHistory, setExecutionHistory] = React.useState([]);
  const [testResults, setTestResults] = React.useState([]);
  const [selectedAgent, setSelectedAgent] = React.useState(null);
  const [selectedPrompt, setSelectedPrompt] = React.useState(null);
  const [isLoading, setIsLoading] = React.useState(true);
  const [activeTab, setActiveTab] = React.useState('agents');

  // Load initial data
  React.useEffect(() => {
    const loadData = async () => {
      try {
        setIsLoading(true);
        
        // Load agents
        const agentsResponse = await fetch('/api/config/agents');
        if (agentsResponse.ok) {
          const agentsData = await agentsResponse.json();
          setAgents(agentsData);
        }

        // Load prompts
        const promptsResponse = await fetch('/api/config/prompts');
        if (promptsResponse.ok) {
          const promptsData = await promptsResponse.json();
          setPrompts(promptsData);
        }

        // Load execution history
        const historyResponse = await fetch('/api/execution-history');
        if (historyResponse.ok) {
          const historyData = await historyResponse.json();
          setExecutionHistory(historyData);
        }

        // Load test results
        const testResponse = await fetch('/api/test-results');
        if (testResponse.ok) {
          const testData = await testResponse.json();
          setTestResults(testData);
        }
      } catch (error) {
        console.error('Error loading data:', error);
      } finally {
        setIsLoading(false);
      }
    };

    loadData();
  }, []);

  const handleAgentSelect = (agent) => {
    setSelectedAgent(agent);
    setActiveTab('agents');
  };

  const handlePromptSelect = (prompt) => {
    setSelectedPrompt(prompt);
    setActiveTab('prompts');
  };

  const handleTabChange = (tab) => {
    setActiveTab(tab);
  };

  if (isLoading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Loading CrewAI Workflow System...</p>
      </div>
    );
  }

  return (
    <QueryClientProvider client={queryClient}>
      <Router 
        future={{
          v7_startTransition: true,
          v7_relativeSplatPath: true
        }}
      >
        <div className="flex">
          <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} currentPage={currentPage} onPageChange={setCurrentPage} />
          <div className="flex-1 min-h-screen bg-gray-50">
            <Toaster position="top-right" />
            <main className="p-6">
              <Routes>
                <Route path="/" element={<Navigate to="/dashboard" replace />} />
                <Route path="/dashboard" element={<InteractiveDashboard />} />
                <Route path="/agents" element={<AgentManager selectedAgent={selectedAgent} onAgentSelect={setSelectedAgent} />} />
                <Route path="/prompts" element={<PromptManager selectedPrompt={selectedPrompt} onPromptSelect={setSelectedPrompt} />} />
                <Route path="/workflows" element={<WorkflowBuilder />} />
                <Route path="/models" element={<ModelManagement />} />
                <Route path="/model-assignments" element={<ModelAssignments />} />
                <Route path="/performance" element={<PerformanceDashboard agents={agents} executionHistory={executionHistory} testResults={testResults} refreshInterval={5000} />} />
                <Route path="/editor" element={<EnhancedPromptEditor />} />
                <Route path="/observability" element={<ObservabilityDashboard />} />
                <Route path="/evals" element={<EvaluationDashboard />} />
                <Route path="/tools" element={<ToolManager />} />
                <Route path="/settings" element={<Settings />} />
                <Route path="/history" element={<ExecutionHistory />} />
                <Route path="/knowledge-base" element={<KnowledgeBase />} />
                {/* Add more routes as needed */}
              </Routes>
            </main>
          </div>
        </div>
      </Router>
    </QueryClientProvider>
  );
}

export default App; 