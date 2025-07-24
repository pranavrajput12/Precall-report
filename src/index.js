import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

// React Scan for performance monitoring
import { scan } from 'react-scan';

// Initialize React Scan with production-ready configuration
if (process.env.NODE_ENV === 'development') {
  scan({
    enabled: true,
    log: true, // Log performance issues to console
    showToolbar: true, // Show performance toolbar
    alwaysShowLabels: false, // Only show labels when scanning
    renderCountThreshold: 5, // Alert when component renders more than 5 times
    excludeCommits: (fiber) => {
      // Exclude React Flow and other third-party library components from monitoring
      return fiber.elementType?.displayName?.includes('ReactFlow') ||
             fiber.elementType?.displayName?.includes('Handle') ||
             fiber.type?.name?.includes('Flow');
    }
  });
} else if (process.env.NODE_ENV === 'production' && process.env.REACT_APP_ENABLE_MONITORING === 'true') {
  // Production monitoring with reduced verbosity
  scan({
    enabled: true,
    log: false, // Disable console logs in production
    showToolbar: false, // Hide toolbar in production
    renderCountThreshold: 10, // Higher threshold for production
    onPerfIssue: (fiber, renderCount) => {
      // Send performance issues to monitoring service
      console.warn(`Performance issue detected: ${fiber.elementType?.name || 'Unknown'} rendered ${renderCount} times`);
      
      // Here you could send to your monitoring service:
      // sendToMonitoring({
      //   component: fiber.elementType?.name,
      //   renderCount,
      //   timestamp: Date.now()
      // });
    }
  });
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
); 