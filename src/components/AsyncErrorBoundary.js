import React, { useState, useEffect } from 'react';
import ErrorBoundary from './ErrorBoundary';

// Hook for handling async errors
export function useAsyncError() {
  const [, setError] = useState();
  return React.useCallback(
    error => {
      setError(() => {
        throw error;
      });
    },
    [setError],
  );
}

// Component for handling async errors with retry logic
export function AsyncErrorBoundary({ children, fallback, onError }) {
  const [asyncError, setAsyncError] = useState(null);
  const [retryCount, setRetryCount] = useState(0);

  // Listen for unhandled promise rejections
  useEffect(() => {
    const handleUnhandledRejection = (event) => {
      console.error('Unhandled promise rejection:', event.reason);
      setAsyncError(event.reason);
      if (onError) {
        onError(event.reason);
      }
    };

    window.addEventListener('unhandledrejection', handleUnhandledRejection);
    
    return () => {
      window.removeEventListener('unhandledrejection', handleUnhandledRejection);
    };
  }, [onError]);

  const handleRetry = () => {
    setAsyncError(null);
    setRetryCount(prev => prev + 1);
  };

  if (asyncError) {
    if (fallback) {
      return fallback(asyncError, handleRetry, retryCount);
    }

    return (
      <div className="p-4 bg-red-50 border border-red-200 rounded-md">
        <h3 className="text-red-800 font-medium">Async Error</h3>
        <p className="text-red-600 text-sm mt-1">
          {asyncError.message || 'An asynchronous error occurred'}
        </p>
        <button
          onClick={handleRetry}
          className="mt-2 text-sm text-red-600 underline hover:text-red-800"
        >
          Retry ({retryCount})
        </button>
      </div>
    );
  }

  return (
    <ErrorBoundary>
      {children}
    </ErrorBoundary>
  );
}

// HOC for wrapping components with error boundary
export function withErrorBoundary(Component, errorFallback) {
  return function WrappedComponent(props) {
    return (
      <ErrorBoundary fallback={errorFallback}>
        <Component {...props} />
      </ErrorBoundary>
    );
  };
}

// Hook for error handling in functional components
export function useErrorHandler() {
  const [error, setError] = useState(null);
  
  const resetError = () => setError(null);
  
  const captureError = (error) => {
    console.error('Error captured:', error);
    setError(error);
    
    // Report to error tracking
    if (window.Sentry) {
      window.Sentry.captureException(error);
    }
  };

  // Throw error to be caught by error boundary
  if (error) {
    throw error;
  }

  return { captureError, resetError };
}

export default AsyncErrorBoundary;