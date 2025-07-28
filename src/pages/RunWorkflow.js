import React, { useState, useEffect } from 'react';
import { Send, Loader, CheckCircle, AlertCircle, FileText, Sparkles, Info, AlertTriangle, X, ChevronDown, ChevronUp, Lightbulb, RefreshCw } from 'lucide-react';
import { useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import clsx from 'clsx';

const RunWorkflow = () => {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [validating, setValidating] = useState(false);
  const [enriching, setEnriching] = useState(false);
  const [executionStatus, setExecutionStatus] = useState('');
  const [result, setResult] = useState(null);
  const [showDuplicateDialog, setShowDuplicateDialog] = useState(false);
  const [duplicateExecution, setDuplicateExecution] = useState(null);
  const [validationResult, setValidationResult] = useState(null);
  const [showTemplates, setShowTemplates] = useState(false);
  const [templates, setTemplates] = useState([]);
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [enrichments, setEnrichments] = useState(null);
  const [showEnrichments, setShowEnrichments] = useState(false);
  
  const [inputs, setInputs] = useState({
    conversation_thread: '',
    channel: 'linkedin',
    prospect_profile_url: '',
    prospect_company_url: '',
    prospect_company_website: '',
    message_context: '',
    your_company: '',
    your_role: ''
  });

  // Load templates on mount
  useEffect(() => {
    fetchTemplates();
  }, []);

  // Validate inputs on change with debouncing
  useEffect(() => {
    const timer = setTimeout(() => {
      if (Object.values(inputs).some(v => v.trim())) {
        validateInputs();
      }
    }, 500);
    return () => clearTimeout(timer);
  }, [inputs]);

  const fetchTemplates = async () => {
    try {
      const response = await fetch('/api/input-templates');
      if (response.ok) {
        const data = await response.json();
        setTemplates(data.templates || []);
      }
    } catch (error) {
      console.error('Failed to fetch templates:', error);
    }
  };

  const validateInputs = async () => {
    setValidating(true);
    try {
      const response = await fetch('/api/validate/inputs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(inputs)
      });
      
      if (response.ok) {
        const result = await response.json();
        setValidationResult(result);
        
        // Apply auto-corrections if any
        if (result.auto_corrections && Object.keys(result.auto_corrections).length > 0) {
          setInputs(prev => ({ ...prev, ...result.auto_corrections }));
          toast.success('Applied auto-corrections to your inputs');
        }
      }
    } catch (error) {
      console.error('Validation error:', error);
    } finally {
      setValidating(false);
    }
  };

  const enrichContext = async () => {
    setEnriching(true);
    try {
      const response = await fetch('/api/enrich/context', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(inputs)
      });
      
      if (response.ok) {
        const enrichedData = await response.json();
        setEnrichments(enrichedData.enrichments);
        setShowEnrichments(true);
        
        // Apply suggested values if user hasn't provided them
        if (enrichedData.enrichments) {
          const updates = {};
          if (!inputs.message_context && enrichedData.enrichments.suggested_message_context) {
            updates.message_context = enrichedData.enrichments.suggested_message_context;
          }
          if (Object.keys(updates).length > 0) {
            setInputs(prev => ({ ...prev, ...updates }));
            toast.success('Added suggested context to your inputs');
          }
        }
      }
    } catch (error) {
      console.error('Enrichment error:', error);
      toast.error('Failed to enrich context');
    } finally {
      setEnriching(false);
    }
  };

  const applyTemplate = (template) => {
    const updates = {};
    
    // Apply template fields
    Object.keys(template.fields).forEach(key => {
      if (key !== 'variables' && inputs.hasOwnProperty(key)) {
        updates[key] = template.fields[key];
      }
    });
    
    setInputs(prev => ({ ...prev, ...updates }));
    setSelectedTemplate(template);
    setShowTemplates(false);
    toast.success(`Applied "${template.name}" template`);
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setInputs(prev => ({ ...prev, [name]: value }));
  };

  const applySuggestion = (field, value) => {
    setInputs(prev => ({ ...prev, [field]: value }));
    toast.success(`Applied suggestion for ${field}`);
  };

  // Function to check for recent duplicate executions
  const checkForDuplicates = async (trimmedInputs) => {
    try {
      const response = await fetch('/api/execution-history?page=1&page_size=10');
      if (!response.ok) return null;
      
      const data = await response.json();
      const recentExecutions = data.items || [];
      
      // Look for executions in the last 5 minutes with matching inputs
      const fiveMinutesAgo = new Date(Date.now() - 5 * 60 * 1000);
      
      for (const execution of recentExecutions) {
        if (!execution.created_at) continue;
        
        const executionTime = new Date(execution.created_at);
        if (executionTime < fiveMinutesAgo) continue;
        
        // Check if inputs match (excluding context fields which can vary)
        const executionInputs = execution.input_data || {};
        const inputsMatch = (
          executionInputs.conversation_thread?.trim() === trimmedInputs.conversation_thread &&
          executionInputs.channel === trimmedInputs.channel &&
          executionInputs.prospect_profile_url?.trim() === trimmedInputs.prospect_profile_url &&
          executionInputs.prospect_company_url?.trim() === trimmedInputs.prospect_company_url
        );
        
        if (inputsMatch) {
          return execution;
        }
      }
      
      return null;
    } catch (error) {
      console.error('Error checking for duplicates:', error);
      return null;
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Check validation result
    if (validationResult && !validationResult.is_valid) {
      toast.error('Please fix validation errors before submitting');
      return;
    }
    
    setLoading(true);
    setResult(null);
    setExecutionStatus('Preparing workflow...');

    try {
      // Trim all input values
      const trimmedInputs = Object.keys(inputs).reduce((acc, key) => {
        acc[key] = typeof inputs[key] === 'string' ? inputs[key].trim() : inputs[key];
        return acc;
      }, {});
      
      // Check for recent duplicate executions
      setExecutionStatus('Checking for duplicates...');
      const duplicateExec = await checkForDuplicates(trimmedInputs);
      if (duplicateExec) {
        setDuplicateExecution(duplicateExec);
        setShowDuplicateDialog(true);
        setLoading(false);
        setExecutionStatus('');
        return;
      }
      
      setExecutionStatus('Starting workflow execution...');
      const response = await fetch('/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(trimmedInputs),
      });

      setExecutionStatus('Processing workflow response...');

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to execute workflow');
      }

      const data = await response.json();
      setResult(data.result);
      setExecutionStatus('');
      
      // Invalidate queries to refresh data
      queryClient.invalidateQueries(['execution-history']);
      
      toast.success('Workflow executed successfully!');
    } catch (error) {
      console.error('Error:', error);
      toast.error(error.message || 'Failed to execute workflow');
      setExecutionStatus('');
    } finally {
      setLoading(false);
    }
  };

  const continueDespiteDuplicate = () => {
    setShowDuplicateDialog(false);
    setDuplicateExecution(null);
    handleSubmit(new Event('submit'));
  };

  const viewDuplicateResult = () => {
    if (duplicateExecution?.output_data) {
      setResult(duplicateExecution.output_data);
      setShowDuplicateDialog(false);
    }
  };

  const fillSampleData = () => {
    setInputs({
      conversation_thread: "Hi Sarah, I noticed your recent post about scaling engineering teams at TechCorp. As someone who's helped similar companies optimize their development workflows, I'd love to share some insights that might be relevant to your current challenges.",
      channel: 'linkedin',
      prospect_profile_url: 'https://linkedin.com/in/sarah-johnson',
      prospect_company_url: 'https://linkedin.com/company/techcorp',
      prospect_company_website: 'https://techcorp.com',
      message_context: 'Introducing our developer productivity platform that helps engineering teams ship 40% faster',
      your_company: 'DevTools Inc',
      your_role: 'Head of Partnerships'
    });
    toast.success('Sample data filled!');
  };

  const ValidationMessage = ({ type, message, field, suggestion }) => {
    const icons = {
      error: <X className="w-4 h-4 text-red-500" />,
      warning: <AlertTriangle className="w-4 h-4 text-yellow-500" />,
      suggestion: <Lightbulb className="w-4 h-4 text-blue-500" />
    };

    const bgColors = {
      error: 'bg-red-50 border-red-200',
      warning: 'bg-yellow-50 border-yellow-200',
      suggestion: 'bg-blue-50 border-blue-200'
    };

    return (
      <div className={clsx('p-3 rounded-lg border flex items-start gap-2', bgColors[type])}>
        {icons[type]}
        <div className="flex-1">
          <p className="text-sm font-medium text-gray-900">{field}: {message}</p>
          {suggestion && (
            <div className="mt-1 flex items-center gap-2">
              <p className="text-xs text-gray-600">{suggestion}</p>
              {type === 'suggestion' && suggestion.suggested_value && (
                <button
                  type="button"
                  onClick={() => applySuggestion(field, suggestion.suggested_value)}
                  className="text-xs text-blue-600 hover:text-blue-700 underline"
                >
                  Apply
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Run AI Workflow</h1>
        <p className="text-gray-600">Execute the AI workflow to generate personalized responses</p>
      </div>

      {/* Template Selector */}
      <div className="mb-6">
        <button
          type="button"
          onClick={() => setShowTemplates(!showTemplates)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-50 text-blue-700 rounded-lg hover:bg-blue-100 transition-colors"
        >
          <FileText className="w-4 h-4" />
          Use Template
          {showTemplates ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>
        
        {showTemplates && templates.length > 0 && (
          <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-3">
            {templates.map(template => (
              <div
                key={template.id}
                className="p-4 bg-white border rounded-lg hover:border-blue-400 cursor-pointer transition-colors"
                onClick={() => applyTemplate(template)}
              >
                <h4 className="font-medium text-gray-900">{template.name}</h4>
                <p className="text-sm text-gray-600 mt-1">{template.description}</p>
                <div className="mt-2 flex items-center gap-2">
                  <span className="text-xs px-2 py-1 bg-gray-100 rounded">{template.category}</span>
                  <span className="text-xs px-2 py-1 bg-gray-100 rounded">{template.channel}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Validation Messages */}
      {validationResult && (
        <div className="mb-6 space-y-2">
          {validationResult.errors?.map((error, idx) => (
            <ValidationMessage key={`error-${idx}`} type="error" {...error} />
          ))}
          {validationResult.warnings?.map((warning, idx) => (
            <ValidationMessage key={`warning-${idx}`} type="warning" {...warning} />
          ))}
          {validationResult.suggestions?.map((suggestion, idx) => (
            <ValidationMessage key={`suggestion-${idx}`} type="suggestion" {...suggestion} />
          ))}
        </div>
      )}

      {/* Enrichments Display */}
      {showEnrichments && enrichments && (
        <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
          <div className="flex items-start gap-2">
            <Info className="w-5 h-5 text-green-600 mt-0.5" />
            <div className="flex-1">
              <h4 className="font-medium text-green-900 mb-2">Context Enrichments</h4>
              <div className="space-y-1 text-sm text-green-800">
                {enrichments.detected_industry && (
                  <p>• Industry: {enrichments.detected_industry} ({(enrichments.industry_confidence * 100).toFixed(0)}% confidence)</p>
                )}
                {enrichments.company_size && (
                  <p>• Company Size: {enrichments.company_size}</p>
                )}
                {enrichments.suggested_talking_points && (
                  <div>
                    <p>• Suggested Talking Points:</p>
                    <ul className="ml-4 list-disc">
                      {enrichments.suggested_talking_points.map((point, idx) => (
                        <li key={idx}>{point}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="bg-white rounded-lg shadow-lg p-6">
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Quick Actions */}
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Workflow Inputs</h2>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={enrichContext}
                disabled={enriching}
                className="text-sm text-green-600 hover:text-green-700 flex items-center gap-1"
              >
                {enriching ? (
                  <RefreshCw className="w-4 h-4 animate-spin" />
                ) : (
                  <Sparkles className="w-4 h-4" />
                )}
                Auto-Enrich
              </button>
              <button
                type="button"
                onClick={fillSampleData}
                className="text-sm text-blue-600 hover:text-blue-700 flex items-center gap-1"
              >
                <FileText className="w-4 h-4" />
                Use Sample Data
              </button>
            </div>
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
              className={clsx(
                "w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500",
                validationResult?.errors?.some(e => e.field === 'conversation_thread') 
                  ? 'border-red-300' 
                  : 'border-gray-300'
              )}
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
                Prospect LinkedIn Profile <span className="text-red-500">*</span>
              </label>
              <input
                type="url"
                name="prospect_profile_url"
                value={inputs.prospect_profile_url}
                onChange={handleInputChange}
                required
                className={clsx(
                  "w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500",
                  validationResult?.errors?.some(e => e.field === 'prospect_profile_url') 
                    ? 'border-red-300' 
                    : 'border-gray-300'
                )}
                placeholder="https://linkedin.com/in/..."
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Company LinkedIn Profile <span className="text-red-500">*</span>
              </label>
              <input
                type="url"
                name="prospect_company_url"
                value={inputs.prospect_company_url}
                onChange={handleInputChange}
                required
                className={clsx(
                  "w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500",
                  validationResult?.errors?.some(e => e.field === 'prospect_company_url') 
                    ? 'border-red-300' 
                    : 'border-gray-300'
                )}
                placeholder="https://linkedin.com/company/..."
              />
            </div>
          </div>

          {/* Company Website */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Company Website
            </label>
            <input
              type="url"
              name="prospect_company_website"
              value={inputs.prospect_company_website}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="https://example.com"
            />
          </div>

          {/* Message Context */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Message Context
            </label>
            <textarea
              name="message_context"
              value={inputs.message_context}
              onChange={handleInputChange}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="What is the goal of this outreach? What value are you offering?"
            />
          </div>

          {/* Your Info Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Your Company <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                name="your_company"
                value={inputs.your_company}
                onChange={handleInputChange}
                required
                className={clsx(
                  "w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500",
                  validationResult?.errors?.some(e => e.field === 'your_company') 
                    ? 'border-red-300' 
                    : 'border-gray-300'
                )}
                placeholder="Your Company Inc."
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Your Role <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                name="your_role"
                value={inputs.your_role}
                onChange={handleInputChange}
                required
                className={clsx(
                  "w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500",
                  validationResult?.errors?.some(e => e.field === 'your_role') 
                    ? 'border-red-300' 
                    : 'border-gray-300'
                )}
                placeholder="Sales Director, Account Executive, etc."
              />
            </div>
          </div>

          {/* Submit Button */}
          <div className="flex justify-end">
            <button
              type="submit"
              disabled={loading || (validationResult && !validationResult.is_valid)}
              className={clsx(
                "flex items-center gap-2 px-6 py-3 rounded-md text-white font-medium transition-colors",
                loading || (validationResult && !validationResult.is_valid)
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-blue-600 hover:bg-blue-700'
              )}
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
          </div>
        </form>
      </div>

      {/* Execution Status */}
      {executionStatus && (
        <div className="mt-6 p-4 bg-blue-50 rounded-lg flex items-center gap-3">
          <Loader className="w-5 h-5 animate-spin text-blue-600" />
          <p className="text-blue-800">{executionStatus}</p>
        </div>
      )}

      {/* Result Display */}
      {result && (
        <div className="mt-8 bg-white rounded-lg shadow-lg p-6">
          <div className="flex items-center gap-2 mb-4">
            <CheckCircle className="w-6 h-6 text-green-600" />
            <h2 className="text-xl font-semibold text-gray-900">Workflow Result</h2>
          </div>

          {/* Display the generated message */}
          {result.reply && (
            <div className="mb-6">
              <h3 className="text-lg font-medium text-gray-800 mb-2">Generated Message:</h3>
              <div className="p-4 bg-gray-50 rounded-lg">
                <p className="text-gray-700 whitespace-pre-wrap">{result.reply}</p>
              </div>
            </div>
          )}

          {/* Quality Metrics */}
          {result.quality_assessment && (
            <div className="mt-6 p-4 bg-blue-50 rounded-lg">
              <h3 className="text-lg font-medium text-gray-800 mb-3">Quality Assessment</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <p className="text-sm text-gray-600">Quality Score</p>
                  <p className="text-xl font-semibold text-blue-600">
                    {result.quality_assessment.quality_score || 0}%
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Personalization</p>
                  <p className="text-xl font-semibold text-blue-600">
                    {result.quality_assessment.personalization_score || 0}%
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Relevance</p>
                  <p className="text-xl font-semibold text-blue-600">
                    {result.quality_assessment.relevance_score || 0}%
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Response Rate</p>
                  <p className="text-xl font-semibold text-green-600">
                    {((result.quality_assessment.predicted_response_rate || 0) * 100).toFixed(1)}%
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* View Full Results Button */}
          <div className="mt-6 flex justify-end">
            <button
              onClick={() => navigate('/workflows/history')}
              className="text-blue-600 hover:text-blue-700 font-medium"
            >
              View in Execution History →
            </button>
          </div>
        </div>
      )}

      {/* Duplicate Execution Dialog */}
      {showDuplicateDialog && duplicateExecution && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex items-start gap-3 mb-4">
              <AlertTriangle className="w-6 h-6 text-yellow-500 flex-shrink-0 mt-1" />
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Duplicate Execution Detected</h3>
                <p className="text-gray-600 mt-1">
                  A similar workflow was executed {new Date(duplicateExecution.created_at).toLocaleString()}.
                </p>
              </div>
            </div>
            
            <div className="space-y-3">
              <button
                onClick={viewDuplicateResult}
                className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                View Previous Result
              </button>
              <button
                onClick={continueDespiteDuplicate}
                className="w-full px-4 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300"
              >
                Run Again Anyway
              </button>
              <button
                onClick={() => setShowDuplicateDialog(false)}
                className="w-full px-4 py-2 text-gray-600 hover:text-gray-800"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default RunWorkflow;