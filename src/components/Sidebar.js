import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Bot, 
  MessageSquare, 
  GitBranch, 
  Wrench, 
  Settings,
  X,
  Sparkles,
  Activity,
  Users,
  Database,
  Eye,
  BarChart3,
  ListChecks,
  BookOpen,
  List
} from 'lucide-react';
import clsx from 'clsx';

const navigationItems = [
  {
    name: 'Run Workflow',
    href: '/run',
    icon: Sparkles,
    description: 'Test your workflow',
    highlight: true
  },
  {
    name: 'Dashboard',
    href: '/dashboard',
    icon: LayoutDashboard,
    description: 'Overview and system status'
  },
  {
    name: 'Agents',
    href: '/agents',
    icon: Bot,
    description: 'Configure AI agents'
  },
  {
    name: 'Prompts',
    href: '/prompts',
    icon: MessageSquare,
    description: 'Manage prompt templates'
  },
  {
    name: 'Workflows',
    href: '/workflows',
    icon: GitBranch,
    description: 'Build and edit workflows'
  },
  {
    name: 'Model Management',
    href: '/models',
    icon: Database,
    description: 'Add and manage Azure OpenAI models'
  },
  {
    name: 'Model Assignments',
    href: '/model-assignments',
    icon: ListChecks,
    description: 'Review agent/model assignments'
  },
  {
    name: 'Observability',
    href: '/observability',
    icon: Eye,
    description: 'Traces, metrics, and system health'
  },
  {
    name: 'Evals',
    href: '/evals',
    icon: BarChart3,
    description: 'LLM output evaluation and feedback'
  },
  {
    name: 'All Runs',
    href: '/all-runs',
    icon: List,
    description: 'View all workflow runs',
    highlight: true
  },
  {
    name: 'Knowledge Base',
    href: '/knowledge-base',
    icon: BookOpen,
    description: 'FAQ management system'
  },
  {
    name: 'Tools',
    href: '/tools',
    icon: Wrench,
    description: 'Configure integrations'
  },
  {
    name: 'Settings',
    href: '/settings',
    icon: Settings,
    description: 'System settings'
  }
];

function Sidebar({ open, onClose, currentPage, onPageChange }) {
  const location = useLocation();

  return (
    <>
      {/* Mobile backdrop */}
      {open && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={onClose}
        />
      )}
      
      {/* Sidebar */}
      <div className={clsx(
        'fixed inset-y-0 left-0 z-50 w-64 bg-white shadow-lg transform transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0',
        open ? 'translate-x-0' : '-translate-x-full'
      )}>
        {/* Header */}
        <div className="flex items-center justify-between h-16 px-6 border-b border-secondary-200">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-semibold text-secondary-900">CrewAI</h1>
              <p className="text-xs text-secondary-500">Configuration Manager</p>
            </div>
          </div>
          
          {/* Close button for mobile */}
          <button
            onClick={onClose}
            className="lg:hidden p-2 rounded-md text-secondary-400 hover:text-secondary-600 hover:bg-secondary-100"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        
        {/* Navigation */}
        <nav className="flex-1 px-4 py-6 space-y-2">
          {navigationItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.href;
            
            return (
              <Link
                key={item.name}
                to={item.href}
                onClick={() => {
                  onPageChange(item.name.toLowerCase());
                  onClose(); // Close sidebar on mobile after navigation
                }}
                className={clsx(
                  'group flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors',
                  item.highlight && !isActive
                    ? 'bg-blue-600 text-white hover:bg-blue-700'
                    : isActive
                    ? 'bg-primary-50 text-primary-700 border-r-2 border-primary-600'
                    : 'text-secondary-600 hover:bg-secondary-50 hover:text-secondary-900'
                )}
              >
                <Icon className={clsx(
                  'mr-3 h-5 w-5 flex-shrink-0',
                  item.highlight && !isActive
                    ? 'text-white'
                    : isActive
                    ? 'text-primary-600'
                    : 'text-secondary-400 group-hover:text-secondary-600'
                )} />
                <div className="flex-1">
                  <div className="text-sm font-medium">{item.name}</div>
                  <div className="text-xs text-secondary-500 mt-0.5">{item.description}</div>
                </div>
              </Link>
            );
          })}
        </nav>
        
        {/* Footer */}
        <div className="p-4 border-t border-secondary-200">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-success-100 rounded-full flex items-center justify-center">
              <Activity className="w-4 h-4 text-success-600" />
            </div>
            <div className="flex-1">
              <div className="text-sm font-medium text-secondary-900">System Status</div>
              <div className="text-xs text-success-600">All systems operational</div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

export default Sidebar; 