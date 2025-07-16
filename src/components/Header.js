import React from 'react';
import { Menu, Bell, User, Settings, LogOut } from 'lucide-react';
import clsx from 'clsx';

function Header({ onMenuClick, currentPage }) {
  const getPageTitle = (page) => {
    switch (page) {
      case 'dashboard': return 'Dashboard';
      case 'agents': return 'AI Agents';
      case 'prompts': return 'Prompt Templates';
      case 'workflows': return 'Workflow Builder';
      case 'tools': return 'Tools & Integrations';
      case 'settings': return 'Settings';
      default: return 'CrewAI Configuration';
    }
  };

  return (
    <header className="h-16 bg-white border-b border-secondary-200 flex items-center justify-between px-6">
      {/* Left side */}
      <div className="flex items-center space-x-4">
        <button
          onClick={onMenuClick}
          className="lg:hidden p-2 rounded-md text-secondary-400 hover:text-secondary-600 hover:bg-secondary-100"
        >
          <Menu className="w-5 h-5" />
        </button>
        
        <div>
          <h1 className="text-xl font-semibold text-secondary-900">
            {getPageTitle(currentPage)}
          </h1>
        </div>
      </div>

      {/* Right side */}
      <div className="flex items-center space-x-4">
        {/* Notifications */}
        <button className="p-2 rounded-md text-secondary-400 hover:text-secondary-600 hover:bg-secondary-100 relative">
          <Bell className="w-5 h-5" />
          <span className="absolute -top-1 -right-1 w-3 h-3 bg-primary-600 rounded-full"></span>
        </button>

        {/* User menu */}
        <div className="relative">
          <button className="flex items-center space-x-2 p-2 rounded-md text-secondary-600 hover:text-secondary-900 hover:bg-secondary-100">
            <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center">
              <User className="w-4 h-4 text-primary-600" />
            </div>
            <span className="text-sm font-medium">Admin</span>
          </button>
        </div>
      </div>
    </header>
  );
}

export default Header; 