# API Reference

## Base URL
```
http://localhost:8100/api
```

## Authentication
Currently, the API does not require authentication. In production, implement appropriate authentication mechanisms.

## Endpoints

### Workflow Execution

#### Execute Single Workflow
```http
POST /api/workflow/execute
```

**Request Body:**
```json
{
  "workflow_id": "linkedin-outreach",
  "input_data": {
    "channel": "LinkedIn",
    "prospect_company_url": "https://roam.com",
    "personalization_data": {
      "explicit_questions": ["What is your pricing?"],
      "implicit_needs": ["cost optimization", "scalability"]
    }
  }
}
```

**Response:**
```json
{
  "execution_id": "exec_017",
  "status": "completed",
  "output": {
    "message": "Personalized message content...",
    "quality_score": 85,
    "predicted_response_rate": 0.35,
    "immediate_response": {
      "message": "Hi [Name], I noticed your company...",
      "word_count": 95
    },
    "follow_up_sequence": [
      {
        "timing": "3 days later",
        "subject": "Quick follow-up on [topic]",
        "message": "Hope you had a chance to review...",
        "word_count": 87
      }
    ],
    "word_count_info": {
      "immediate_response": 95,
      "follow_ups": [87, 92, 89],
      "total": 363
    },
    "quality_assessment": {
      "score": 85,
      "criteria": {
        "personalization": 90,
        "value_proposition": 85,
        "call_to_action": 80,
        "tone": 85
      }
    }
  },
  "duration": 12.5
}
```

#### Batch Workflow Execution
```http
POST /api/batch
```

**Request Body:**
```json
{
  "requests": [
    {
      "workflow_id": "linkedin-outreach",
      "input_data": {...}
    }
  ],
  "parallel": true,
  "max_concurrent": 10
}
```

### Execution History

#### Get All Executions
```http
GET /api/execution-history
```

**Response:**
```json
{
  "executions": [
    {
      "id": "exec_017",
      "workflow_name": "LinkedIn Outreach Workflow",
      "status": "completed",
      "started_at": "2025-01-22T10:30:00Z",
      "duration": 12.5,
      "input_data": {
        "channel": "LinkedIn",
        "prospect_company_url": "https://example.com",
        "personalization_data": {
          "explicit_questions": ["What is your pricing?"],
          "implicit_needs": ["scalability", "integration"]
        }
      },
      "output": {
        "immediate_response": {
          "message": "Hi [Name], I noticed your company...",
          "word_count": 95
        },
        "follow_up_sequence": [
          {
            "timing": "3 days later",
            "subject": "Quick follow-up",
            "message": "Hope you had a chance to review...",
            "word_count": 87
          }
        ],
        "quality_score": 85,
        "predicted_response_rate": 0.35,
        "channel": "linkedin"
      }
    }
  ]
}
```

#### Get Single Execution
```http
GET /api/execution-history/{execution_id}
```

### FAQ Management

#### List All FAQs
```http
GET /api/faq
```

**Response:**
```json
[
  {
    "question": "What is Qubit Capital?",
    "answer": "Qubit Capital is a leading fundraising platform...",
    "category": "General",
    "keywords": "about,overview,company"
  }
]
```

#### Search FAQs
```http
GET /api/faq/search?q=pricing
```

#### Add FAQ Entry
```http
POST /api/faq
```

**Request Body:**
```json
{
  "question": "What is your pricing model?",
  "answer": "Our pricing is based on success fees...",
  "category": "Pricing",
  "keywords": "cost,fees,pricing,payment"
}
```

#### Get Intelligent FAQ Answer
```http
POST /api/faq/intelligent-answer
```

**Request Body:**
```json
{
  "question": "How does your service compare to traditional VCs?",
  "context": {
    "industry": "healthcare",
    "stage": "Series A"
  }
}
```

**Response:**
```json
{
  "answer": "Comprehensive answer with context...",
  "confidence": 0.92,
  "sources": [
    {
      "question": "Original FAQ question",
      "answer": "Original FAQ answer",
      "similarity_score": 0.85
    }
  ],
  "analysis": {
    "question_type": "comparison",
    "main_intent": "Understanding value proposition vs VCs",
    "key_topics": ["comparison", "traditional VCs"],
    "implicit_concerns": ["control", "terms"],
    "urgency_level": "medium",
    "suggested_follow_ups": ["What are typical terms?"]
  }
}
```

#### Analyze FAQ Questions Batch
```http
POST /api/faq/analyze-batch
```

**Request Body:**
```json
{
  "questions": [
    "What is your pricing?",
    "How long does the process take?"
  ],
  "context": {
    "company": "TechStartup Inc"
  }
}
```

#### Evaluate FAQ Answer Quality
```http
POST /api/faq/evaluate
```

**Request Body:**
```json
{
  "question": "What is your pricing?",
  "answer": "Contact us for pricing",
  "feedback": "Too vague, need more specific information"
}
```

**Response:**
```json
{
  "overall_score": 45,
  "completeness": 30,
  "clarity": 50,
  "accuracy": 60,
  "actionability": 40,
  "tone": 50,
  "strengths": ["Professional tone"],
  "improvements": ["Add specific pricing tiers", "Include examples"],
  "suggested_revision": "Our pricing starts at $X for startups..."
}
```

#### Suggest New FAQs
```http
POST /api/faq/suggest
```

**Request Body:**
```json
{
  "unanswered_questions": [
    "Do you work with international startups?",
    "What documents do I need to prepare?"
  ]
}
```

### Configuration Management

#### Get Agent Configurations
```http
GET /api/config/agents
```

#### Update Agent Configuration
```http
PUT /api/config/agents/{agent_id}
```

#### Get Workflow Configurations
```http
GET /api/config/workflows
```

### Observability

#### Get Performance Metrics
```http
GET /api/observability/metrics
```

**Response:**
```json
{
  "total_executions": 150,
  "success_rate": 0.92,
  "average_duration": 8.5,
  "average_quality_score": 82,
  "cache_hit_rate": 0.85
}
```

#### Get Execution Traces
```http
GET /api/observability/traces?execution_id=exec_017
```

### Evaluation

#### Get Evaluation Reports
```http
GET /api/evaluation/reports
```

#### Run Quality Evaluation
```http
POST /api/evaluation/evaluate
```

**Request Body:**
```json
{
  "message": "Generated message content...",
  "context": {
    "channel": "LinkedIn",
    "prospect": "John Doe"
  }
}
```

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid input data: missing required field 'workflow_id'"
}
```

### 404 Not Found
```json
{
  "detail": "Execution not found: exec_999"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error",
  "error": "Detailed error message for debugging"
}
```

## Rate Limiting
- Default: 100 requests per minute per IP
- Batch operations: 10 requests per minute per IP

## WebSocket Support
Connect to `ws://localhost:8100/ws` for real-time updates during workflow execution.

## Health Check
```http
GET /api/health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "redis": "connected",
  "database": "connected"
}
```

## Output Format Documentation

### LinkedIn Message Format
```json
{
  "immediate_response": {
    "message": "Message content (80-100 words)",
    "word_count": 95
  },
  "follow_up_sequence": [
    {
      "timing": "3 days later",
      "message": "Follow-up content (75-125 words)",
      "word_count": 110
    }
  ],
  "word_count_info": {
    "immediate_response": 95,
    "follow_ups": [110, 98, 102],
    "total": 405
  }
}
```

### Email Message Format
```json
{
  "immediate_response": {
    "subject": "Email subject line",
    "message": "Email body content",
    "word_count": 150
  },
  "follow_up_sequence": [
    {
      "timing": "6 days later",
      "subject": "Follow-up subject",
      "message": "Follow-up body",
      "word_count": 120
    }
  ],
  "parsed_messages": [
    {
      "subject": "Subject line",
      "body": "Full email body text",
      "timing": "immediate"
    }
  ]
}
```

### Quality Assessment Structure
```json
{
  "quality_assessment": {
    "score": 85,
    "criteria": {
      "personalization": 90,
      "value_proposition": 85,
      "call_to_action": 80,
      "tone": 85,
      "clarity": 88,
      "urgency": 75
    },
    "feedback": "Message effectively personalizes the approach..."
  }
}
```