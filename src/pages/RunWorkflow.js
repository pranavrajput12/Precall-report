import React, { useState } from 'react';
import { Send, Loader, CheckCircle, AlertCircle, FileText, Sparkles } from 'lucide-react';
import { useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';

const RunWorkflow = () => {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [inputs, setInputs] = useState({
    conversation_thread: '',
    channel: 'linkedin',
    prospect_profile_url: '',
    prospect_company_url: '',
    prospect_company_website: '',
    qubit_context: ''
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);

    try {
      // Trim all input values to remove trailing/leading spaces
      const trimmedInputs = Object.keys(inputs).reduce((acc, key) => {
        acc[key] = typeof inputs[key] === 'string' ? inputs[key].trim() : inputs[key];
        return acc;
      }, {});
      
      console.log('Submitting inputs:', trimmedInputs);
      const response = await fetch('/run', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(trimmedInputs),
      });

      if (!response.ok) {
        const errorData = await response.json();
        console.error('API Error:', errorData);
        
        // Handle validation errors
        if (response.status === 422 && errorData.detail && Array.isArray(errorData.detail)) {
          const errors = errorData.detail.map(err => {
            const field = err.loc[err.loc.length - 1];
            return `${field}: ${err.msg}`;
          }).join('\n');
          throw new Error(`Validation failed:\n${errors}`);
        }
        
        throw new Error(errorData.detail || 'Failed to run workflow');
      }

      const data = await response.json();
      setResult(data);
      
      // Invalidate React Query caches to refresh data across pages
      queryClient.invalidateQueries({ queryKey: ['all-runs'] });
      queryClient.invalidateQueries({ queryKey: ['performance-metrics'] });
      queryClient.invalidateQueries({ queryKey: ['agent-performance'] });
      queryClient.invalidateQueries({ queryKey: ['system-performance'] });
      
      toast.success('Workflow completed successfully!');
    } catch (error) {
      toast.error(error.message);
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setInputs(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const sampleData = {
    conversation_thread: "Hi, I noticed you're working on AI projects. We have a tool that might help with your LLM workflows.",
    prospect_profile_url: "https://linkedin.com/in/john-doe",
    prospect_company_url: "https://linkedin.com/company/acme-corp",
    prospect_company_website: "https://acme-corp.com",
    qubit_context: "Focus on AI implementation for customer service"
  };

  const fillSampleData = () => {
    setInputs({
      ...inputs,
      ...sampleData
    });
    toast.success('Sample data filled!');
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Run Workflow</h1>
          <p className="text-gray-600">Test your CrewAI workflow with real inputs</p>
        </div>

        {/* Main Form */}
        <div className="bg-white rounded-lg shadow-lg p-6">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Quick Actions */}
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold text-gray-900">Workflow Inputs</h2>
              <button
                type="button"
                onClick={fillSampleData}
                className="text-sm text-blue-600 hover:text-blue-700 flex items-center gap-1"
              >
                <Sparkles className="w-4 h-4" />
                Use Sample Data
              </button>
            </div>

            {/* Conversation Thread */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Conversation Thread <span className="text-red-500">*</span>
              </label>
              <textarea
                name="conversation_thread"
                value={inputs.conversation_thread}
                onChange={handleInputChange}
                rows={4}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Paste the conversation thread here..."
              />
            </div>

            {/* Channel Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Channel <span className="text-red-500">*</span>
              </label>
              <select
                name="channel"
                value={inputs.channel}
                onChange={handleInputChange}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="linkedin">LinkedIn</option>
                <option value="email">Email</option>
              </select>
            </div>

            {/* URLs Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Prospect LinkedIn URL <span className="text-red-500">*</span>
                </label>
                <input
                  type="url"
                  name="prospect_profile_url"
                  value={inputs.prospect_profile_url}
                  onChange={handleInputChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="https://linkedin.com/in/john-doe"
                />
                <p className="mt-1 text-xs text-gray-500">Format: https://linkedin.com/in/username</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Company LinkedIn URL <span className="text-red-500">*</span>
                </label>
                <input
                  type="url"
                  name="prospect_company_url"
                  value={inputs.prospect_company_url}
                  onChange={handleInputChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="https://linkedin.com/company/acme-corp"
                />
                <p className="mt-1 text-xs text-gray-500">Format: https://linkedin.com/company/company-name</p>
              </div>
            </div>

            {/* Company Website */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Company Website <span className="text-red-500">*</span>
              </label>
              <input
                type="url"
                name="prospect_company_website"
                value={inputs.prospect_company_website}
                onChange={handleInputChange}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="https://example.com"
              />
            </div>

            {/* Additional Context */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Additional Context (Optional)
              </label>
              <textarea
                name="qubit_context"
                value={inputs.qubit_context}
                onChange={handleInputChange}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Any additional context or requirements..."
              />
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 text-white py-3 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <Loader className="w-5 h-5 animate-spin" />
                  Processing...
                </>
              ) : (
                <>
                  <Send className="w-5 h-5" />
                  Run Workflow
                </>
              )}
            </button>
          </form>
        </div>

        {/* Results Section */}
        {result && (
          <div className="mt-8 bg-white rounded-lg shadow-lg p-6">
            <div className="flex items-center gap-2 mb-4">
              <CheckCircle className="w-6 h-6 text-green-500" />
              <h2 className="text-lg font-semibold text-gray-900">Workflow Results</h2>
            </div>

            {/* Processing Time */}
            <div className="mb-4 p-3 bg-gray-50 rounded-md">
              <p className="text-sm text-gray-600">
                Processing Time: <span className="font-medium">{result.processing_time || 'N/A'}</span>
              </p>
            </div>

            {/* Generated Reply */}
            {result.reply && (
              <div className="mb-6">
                <h3 className="text-md font-medium text-gray-700 mb-2">Generated Reply:</h3>
                <div className="p-4 bg-blue-50 border border-blue-200 rounded-md">
                  <p className="text-gray-800 whitespace-pre-wrap">{result.reply}</p>
                </div>
              </div>
            )}

            {/* Context Analysis */}
            {result.context && (
              <div className="space-y-4">
                <h3 className="text-md font-medium text-gray-700">Analysis Details:</h3>
                
                {/* Profile Summary */}
                {result.context.profile_summary && (
                  <div className="p-3 bg-gray-50 rounded-md">
                    <h4 className="text-sm font-medium text-gray-600 mb-1">Profile Summary</h4>
                    <p className="text-sm text-gray-700">{result.context.profile_summary}</p>
                  </div>
                )}

                {/* Thread Analysis */}
                {result.context.thread_analysis && (
                  <div className="p-3 bg-gray-50 rounded-md">
                    <h4 className="text-sm font-medium text-gray-600 mb-1">Thread Analysis</h4>
                    <p className="text-sm text-gray-700">{result.context.thread_analysis}</p>
                  </div>
                )}

                {/* Questions Answered */}
                {result.context.faq_answers && result.context.faq_answers.length > 0 && (
                  <div className="p-3 bg-gray-50 rounded-md">
                    <h4 className="text-sm font-medium text-gray-600 mb-2">Questions Addressed</h4>
                    <ul className="space-y-2">
                      {result.context.faq_answers.map((faq, index) => (
                        <li key={index} className="text-sm">
                          <p className="font-medium text-gray-700">Q: {faq.question}</p>
                          <p className="text-gray-600 ml-3">A: {faq.answer}</p>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}

            {/* View Full Details */}
            <div className="mt-4 pt-4 border-t border-gray-200 flex items-center justify-between">
              <button
                onClick={() => console.log('Full result:', result)}
                className="text-sm text-blue-600 hover:text-blue-700 flex items-center gap-1"
              >
                <FileText className="w-4 h-4" />
                View Full Response in Console
              </button>
              
              <button
                onClick={() => navigate('/all-runs')}
                className="px-4 py-2 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 flex items-center gap-2"
              >
                <CheckCircle className="w-4 h-4" />
                View All Runs
              </button>
            </div>
          </div>
        )}

        {/* Help Text */}
        <div className="mt-8 p-4 bg-blue-50 rounded-lg">
          <div className="flex items-start gap-2">
            <AlertCircle className="w-5 h-5 text-blue-600 mt-0.5" />
            <div className="text-sm text-blue-800">
              <p className="font-medium mb-1">How to use:</p>
              <ol className="list-decimal list-inside space-y-1">
                <li>Fill in the conversation thread you want to analyze</li>
                <li>Provide the LinkedIn URLs for the prospect and their company</li>
                <li>Add the company website URL</li>
                <li>Optionally add any specific context or requirements</li>
                <li>Click "Run Workflow" to generate a personalized response</li>
              </ol>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RunWorkflow;