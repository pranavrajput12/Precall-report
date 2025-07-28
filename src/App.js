import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import { scan } from 'react-scan';
import { DataProvider } from './contexts/DataContext';
import ErrorBoundary from './components/ErrorBoundary';
import { AsyncErrorBoundary } from './components/AsyncErrorBoundary';
import Dashboard from './components/Dashboard';
import AgentManager from './components/AgentManager';
import PromptManager from './components/PromptManager';
import PerformanceDashboard from './components/PerformanceDashboard';
import ObservabilityDashboard from './pages/ObservabilityDashboard';
import EvaluationDashboard from './pages/EvaluationDashboard';
import WorkflowsPage from './pages/WorkflowsPage';
import ModelsPage from './pages/ModelsPage';
import BatchProcessing from './pages/BatchProcessing';
import AgentPerformanceDashboard from './pages/AgentPerformanceDashboard';
import FeedbackDashboard from './pages/FeedbackDashboard';
import ToolManager from './components/ToolManager';
import Settings from './components/Settings';
import Sidebar from './components/Sidebar';
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

  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <DataProvider>
          <AsyncErrorBoundary>
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
                    <ErrorBoundary>
                      <Routes>
                        <Route path="/" element={<Navigate to="/dashboard" replace />} />
                        <Route path="/dashboard" element={<Dashboard />} />
                        <Route path="/workflows/*" element={<WorkflowsPage />} />
                        <Route path="/agents" element={<AgentManager />} />
                        <Route path="/prompts" element={<PromptManager />} />
                        <Route path="/models/*" element={<ModelsPage />} />
                        <Route path="/performance" element={<PerformanceDashboard />} />
                        <Route path="/observability" element={<ObservabilityDashboard />} />
                        <Route path="/evals" element={<EvaluationDashboard />} />
                        <Route path="/batch-processing" element={<BatchProcessing />} />
                        <Route path="/agent-performance" element={<AgentPerformanceDashboard />} />
                        <Route path="/feedback" element={<FeedbackDashboard />} />
                        <Route path="/tools" element={<ToolManager />} />
                        <Route path="/settings" element={<Settings />} />
                        <Route path="/knowledge-base" element={<KnowledgeBase />} />
                      </Routes>
                    </ErrorBoundary>
                  </main>
                </div>
              </div>
            </Router>
          </AsyncErrorBoundary>
        </DataProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  );
}

export default App; 