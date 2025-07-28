import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  MessageSquare, 
  Star, 
  ThumbsUp, 
  ThumbsDown, 
  Send, 
  CheckCircle,
  AlertCircle,
  Clock,
  User,
  Loader2,
  TrendingUp,
  Filter,
  Search
} from 'lucide-react';
import { toast } from 'react-hot-toast';

const FeedbackSystem = ({ executionId, workflowId, outputContent }) => {
  const [showFeedbackForm, setShowFeedbackForm] = useState(false);
  const [feedbackData, setFeedbackData] = useState({
    type: 'rating',
    rating: 5,
    content: '',
    suggested_improvement: '',
    original_output: outputContent || '',
    improved_output: ''
  });

  const queryClient = useQueryClient();

  // Submit feedback mutation
  const submitFeedbackMutation = useMutation({
    mutationFn: async (feedback) => {
      const response = await fetch('/api/feedback/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          execution_id: executionId,
          workflow_id: workflowId,
          feedback_type: feedback.type,
          source: 'user_interface',
          rating: feedback.rating,
          content: feedback.content,
          suggested_improvement: feedback.suggested_improvement,
          original_output: feedback.original_output,
          improved_output: feedback.improved_output
        }),
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to submit feedback');
      }
      
      return response.json();
    },
    onSuccess: () => {
      toast.success('Feedback submitted successfully!');
      setShowFeedbackForm(false);
      setFeedbackData({
        type: 'rating',
        rating: 5,
        content: '',
        suggested_improvement: '',
        original_output: outputContent || '',
        improved_output: ''
      });
      queryClient.invalidateQueries(['feedback']);
    },
    onError: (error) => {
      toast.error(`Failed to submit feedback: ${error.message}`);
    },
  });

  const handleQuickFeedback = (type, rating = null) => {
    const quickFeedback = {
      type,
      rating,
      content: type === 'praise' ? 'Great output!' : type === 'complaint' ? 'Needs improvement' : '',
      suggested_improvement: '',
      original_output: outputContent || '',
      improved_output: ''
    };
    
    submitFeedbackMutation.mutate(quickFeedback);
  };

  const handleSubmitDetailed = () => {
    if (!feedbackData.content.trim()) {
      toast.error('Please provide feedback content');
      return;
    }
    
    submitFeedbackMutation.mutate(feedbackData);
  };

  const renderStars = (rating, setRating) => {
    return (
      <div className="flex gap-1">
        {[1, 2, 3, 4, 5].map((star) => (
          <button
            key={star}
            onClick={() => setRating(star)}
            className={`p-1 rounded transition-colors ${
              star <= rating 
                ? 'text-yellow-400 hover:text-yellow-500' 
                : 'text-gray-300 hover:text-gray-400'
            }`}
          >
            <Star className="w-5 h-5 fill-current" />
          </button>
        ))}
      </div>
    );
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-medium text-gray-900">Feedback</h3>
        <div className="flex items-center gap-2">
          {/* Quick feedback buttons */}
          <button
            onClick={() => handleQuickFeedback('praise', 5)}
            disabled={submitFeedbackMutation.isPending}
            className="flex items-center gap-1 px-3 py-1 text-sm bg-green-100 text-green-800 rounded-full hover:bg-green-200 transition-colors disabled:opacity-50"
          >
            <ThumbsUp className="w-4 h-4" />
            Good
          </button>
          <button
            onClick={() => handleQuickFeedback('complaint', 2)}
            disabled={submitFeedbackMutation.isPending}
            className="flex items-center gap-1 px-3 py-1 text-sm bg-red-100 text-red-800 rounded-full hover:bg-red-200 transition-colors disabled:opacity-50"
          >
            <ThumbsDown className="w-4 h-4" />
            Poor
          </button>
          <button
            onClick={() => setShowFeedbackForm(!showFeedbackForm)}
            className="flex items-center gap-1 px-3 py-1 text-sm bg-blue-100 text-blue-800 rounded-full hover:bg-blue-200 transition-colors"
          >
            <MessageSquare className="w-4 h-4" />
            Detailed
          </button>
        </div>
      </div>

      {showFeedbackForm && (
        <div className="space-y-4 border-t border-gray-200 pt-4">
          {/* Feedback Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Feedback Type
            </label>
            <select
              value={feedbackData.type}
              onChange={(e) => setFeedbackData({...feedbackData, type: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="rating">Rating</option>
              <option value="detailed">Detailed Feedback</option>
              <option value="correction">Correction</option>
              <option value="suggestion">Suggestion</option>
              <option value="complaint">Complaint</option>
              <option value="praise">Praise</option>
            </select>
          </div>

          {/* Rating */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Rating (1-5 stars)
            </label>
            {renderStars(feedbackData.rating, (rating) => 
              setFeedbackData({...feedbackData, rating})
            )}
          </div>

          {/* Feedback Content */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Feedback Details
            </label>
            <textarea
              value={feedbackData.content}
              onChange={(e) => setFeedbackData({...feedbackData, content: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows="3"
              placeholder="Describe your feedback in detail..."
            />
          </div>

          {/* Suggested Improvement */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Suggested Improvement (Optional)
            </label>
            <textarea
              value={feedbackData.suggested_improvement}
              onChange={(e) => setFeedbackData({...feedbackData, suggested_improvement: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows="2"
              placeholder="How could this output be improved?"
            />
          </div>

          {/* Improved Output */}
          {feedbackData.type === 'correction' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Corrected Output
              </label>
              <textarea
                value={feedbackData.improved_output}
                onChange={(e) => setFeedbackData({...feedbackData, improved_output: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                rows="4"
                placeholder="Provide the corrected version of the output..."
              />
            </div>
          )}

          {/* Submit Button */}
          <div className="flex justify-end gap-3">
            <button
              onClick={() => setShowFeedbackForm(false)}
              className="px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleSubmitDetailed}
              disabled={submitFeedbackMutation.isPending || !feedbackData.content.trim()}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
            >
              {submitFeedbackMutation.isPending && <Loader2 className="w-4 h-4 animate-spin" />}
              <Send className="w-4 h-4" />
              Submit Feedback
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

const FeedbackList = ({ workflowId, executionId }) => {
  const [statusFilter, setStatusFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');

  // Fetch feedback list
  const { data: feedbackList = [], isLoading } = useQuery({
    queryKey: ['feedback-list', workflowId, executionId],
    queryFn: async () => {
      const url = executionId 
        ? `/api/feedback/execution/${executionId}`
        : `/api/feedback/workflow/${workflowId}`;
      
      const response = await fetch(url);
      if (!response.ok) throw new Error('Failed to fetch feedback');
      return response.json();
    },
    enabled: !!(workflowId || executionId),
  });

  const getStatusIcon = (status) => {
    switch (status) {
      case 'reviewed':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'implemented':
        return <CheckCircle className="w-4 h-4 text-blue-500" />;
      case 'rejected':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      default:
        return <Clock className="w-4 h-4 text-yellow-500" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'reviewed':
        return 'bg-green-100 text-green-800';
      case 'implemented':
        return 'bg-blue-100 text-blue-800';
      case 'rejected':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-yellow-100 text-yellow-800';
    }
  };

  const filteredFeedback = feedbackList.filter(feedback => {
    const matchesStatus = statusFilter === 'all' || feedback.status === statusFilter;
    const matchesSearch = !searchTerm || 
      feedback.content?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      feedback.feedback_type.toLowerCase().includes(searchTerm.toLowerCase());
    
    return matchesStatus && matchesSearch;
  });

  return (
    <div className="bg-white border border-gray-200 rounded-lg">
      <div className="p-4 border-b border-gray-200">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-medium text-gray-900">Feedback History</h3>
          <div className="flex items-center gap-3">
            {/* Search */}
            <div className="relative">
              <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                placeholder="Search feedback..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
              />
            </div>
            
            {/* Filter */}
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
            >
              <option value="all">All Status</option>
              <option value="pending">Pending</option>
              <option value="reviewed">Reviewed</option>
              <option value="implemented">Implemented</option>
              <option value="rejected">Rejected</option>
            </select>
          </div>
        </div>
      </div>

      <div className="max-h-96 overflow-y-auto">
        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
            <span className="ml-2 text-gray-500">Loading feedback...</span>
          </div>
        ) : filteredFeedback.length === 0 ? (
          <div className="text-center py-8">
            <MessageSquare className="w-12 h-12 mx-auto text-gray-400" />
            <p className="text-gray-500 mt-2">No feedback found</p>
            <p className="text-gray-400 text-sm">
              {searchTerm || statusFilter !== 'all' 
                ? 'Try adjusting your search or filter'
                : 'Be the first to provide feedback'}
            </p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {filteredFeedback.map((feedback) => (
              <div key={feedback.id} className="p-4">
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3">
                    <div className="mt-1">
                      {feedback.feedback_type === 'rating' ? (
                        <div className="flex">
                          {[1, 2, 3, 4, 5].map((star) => (
                            <Star
                              key={star}
                              className={`w-4 h-4 ${
                                star <= (feedback.rating || 0)
                                  ? 'text-yellow-400 fill-current'
                                  : 'text-gray-300'
                              }`}
                            />
                          ))}
                        </div>
                      ) : (
                        <User className="w-5 h-5 text-gray-400" />
                      )}
                    </div>
                    
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-sm font-medium text-gray-900 capitalize">
                          {feedback.feedback_type.replace('_', ' ')}
                        </span>
                        <div className="flex items-center gap-1">
                          {getStatusIcon(feedback.status)}
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(feedback.status)}`}>
                            {feedback.status}
                          </span>
                        </div>
                      </div>
                      
                      {feedback.content && (
                        <p className="text-sm text-gray-700 mb-2">
                          {feedback.content}
                        </p>
                      )}
                      
                      {feedback.suggested_improvement && (
                        <div className="bg-blue-50 p-2 rounded text-sm">
                          <p className="font-medium text-blue-900">Suggested Improvement:</p>
                          <p className="text-blue-800">{feedback.suggested_improvement}</p>
                        </div>
                      )}
                      
                      <p className="text-xs text-gray-500 mt-2">
                        {feedback.created_at ? new Date(feedback.created_at).toLocaleString() : 'Unknown date'}
                        {feedback.user_id && ` • by ${feedback.user_id}`}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

const FeedbackSummary = ({ workflowId }) => {
  // Fetch feedback summary
  const { data: summary, isLoading } = useQuery({
    queryKey: ['feedback-summary', workflowId],
    queryFn: async () => {
      const url = workflowId 
        ? `/api/feedback/summary?workflow_id=${workflowId}`
        : '/api/feedback/summary';
      
      const response = await fetch(url);
      if (!response.ok) throw new Error('Failed to fetch feedback summary');
      return response.json();
    },
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  if (isLoading) {
    return (
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="flex items-center justify-center">
          <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
          <span className="ml-2 text-gray-500">Loading summary...</span>
        </div>
      </div>
    );
  }

  if (!summary) {
    return null;
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      <h3 className="text-lg font-medium text-gray-900 mb-4">Feedback Summary</h3>
      
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="text-center">
          <p className="text-2xl font-bold text-gray-900">{summary.total_feedback}</p>
          <p className="text-sm text-gray-600">Total Feedback</p>
        </div>
        
        <div className="text-center">
          <p className="text-2xl font-bold text-yellow-600">
            {summary.average_rating ? summary.average_rating.toFixed(1) : 'N/A'}
          </p>
          <p className="text-sm text-gray-600">Avg Rating</p>
        </div>
        
        <div className="text-center">
          <p className="text-2xl font-bold text-blue-600">{summary.improvement_suggestions}</p>
          <p className="text-sm text-gray-600">Suggestions</p>
        </div>
        
        <div className="text-center">
          <p className="text-2xl font-bold text-green-600">{summary.implemented_improvements}</p>
          <p className="text-sm text-gray-600">Implemented</p>
        </div>
      </div>

      {summary.common_issues && summary.common_issues.length > 0 && (
        <div className="mt-6">
          <h4 className="text-sm font-medium text-gray-900 mb-2">Common Issues</h4>
          <div className="flex flex-wrap gap-2">
            {summary.common_issues.map((issue, index) => (
              <span
                key={index}
                className="inline-flex px-2 py-1 text-xs font-medium bg-red-100 text-red-800 rounded-full"
              >
                {issue.replace('_', ' ')}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export { FeedbackSystem, FeedbackList, FeedbackSummary };