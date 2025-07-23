# Workflow Output Formats Technical Reference

This document provides detailed technical specifications for the output formats used by different workflow types in the CrewAI Workflow Orchestration Platform.

## Overview

The platform supports multiple output formats depending on the channel (LinkedIn, Email) and workflow type. All outputs include quality assessment, word count tracking, and structured message data.

## LinkedIn Workflow Output Format

### Structure
```json
{
  "immediate_response": {
    "message": "string (80-100 words)",
    "word_count": number
  },
  "follow_up_sequence": [
    {
      "timing": "string (e.g., '3 days later')",
      "message": "string (75-125 words)",
      "word_count": number
    }
  ],
  "word_count_info": {
    "immediate_response": number,
    "follow_ups": [number, number, number],
    "total": number
  },
  "quality_assessment": {
    "score": number (0-100),
    "criteria": {
      "personalization": number,
      "value_proposition": number,
      "call_to_action": number,
      "tone": number
    }
  },
  "predicted_response_rate": number (0-1),
  "channel": "linkedin"
}
```

### Word Count Requirements
- **Immediate Response**: 80-100 words (strictly enforced)
- **Follow-up Messages**: 75-125 words each
- **Number of Follow-ups**: Exactly 3

### Example Output
```json
{
  "immediate_response": {
    "message": "Hi John, I noticed your company is scaling rapidly in the healthcare AI space. Given your focus on patient data analytics, I thought you might be interested in how we've helped similar companies like HealthTech Inc reduce their data processing costs by 40% while improving accuracy. We specialize in optimizing ML pipelines for healthcare applications, ensuring HIPAA compliance while maximizing performance. Would you be open to a brief 15-minute call next week to discuss how we could help accelerate your data initiatives?",
    "word_count": 87
  },
  "follow_up_sequence": [
    {
      "timing": "3 days later",
      "message": "Hi John, I wanted to follow up on my previous message about optimizing your ML pipelines. I just came across your recent article on predictive analytics in healthcare - impressive work! Your approach to patient risk stratification aligns perfectly with our optimization framework. We recently helped MedAnalytics achieve 3x faster model training while reducing cloud costs. I'd love to share some specific strategies that could benefit your team. Are you available for a quick chat this week?",
      "word_count": 82
    },
    {
      "timing": "5 days later",
      "message": "John, I understand you're busy leading innovative projects at your company. I'll keep this brief - we have a case study showing how a company similar to yours reduced their ML infrastructure costs by $200K annually while improving model performance. The implementation took just 6 weeks with minimal disruption. If this could be valuable for your team, I can send over the case study. Would that be helpful? Either way, I wish you continued success with your healthcare AI initiatives.",
      "word_count": 85
    },
    {
      "timing": "7 days later",
      "message": "Hi John, this will be my final follow-up. I recognize that optimizing ML pipelines might not be a current priority for your team. If circumstances change and you'd like to explore how we can help reduce costs while improving performance, I'll be here. In the meantime, I'd be happy to connect on LinkedIn to stay in touch and share relevant insights from the healthcare AI space. Best of luck with your continued growth!",
      "word_count": 78
    }
  ],
  "word_count_info": {
    "immediate_response": 87,
    "follow_ups": [82, 85, 78],
    "total": 332
  },
  "quality_assessment": {
    "score": 92,
    "criteria": {
      "personalization": 95,
      "value_proposition": 90,
      "call_to_action": 88,
      "tone": 94
    }
  },
  "predicted_response_rate": 0.42,
  "channel": "linkedin"
}
```

## Email Workflow Output Format

### Structure
```json
{
  "immediate_response": {
    "subject": "string",
    "message": "string",
    "word_count": number
  },
  "follow_up_sequence": [
    {
      "timing": "string (e.g., '6 days later')",
      "subject": "string",
      "message": "string",
      "word_count": number
    }
  ],
  "parsed_messages": [
    {
      "subject": "string",
      "body": "string",
      "timing": "string (immediate or X days later)"
    }
  ],
  "quality_assessment": {
    "score": number (0-100),
    "criteria": {
      "personalization": number,
      "value_proposition": number,
      "call_to_action": number,
      "tone": number,
      "clarity": number,
      "urgency": number
    }
  },
  "predicted_response_rate": number (0-1),
  "channel": "email"
}
```

### Email-Specific Features
- **Subject Lines**: Required for all emails
- **Longer Content**: No strict word limits like LinkedIn
- **Timing**: Typically longer intervals (6-9 days)
- **Additional Quality Criteria**: Clarity and urgency scores

### Example Output
```json
{
  "immediate_response": {
    "subject": "Partnership Opportunity: Expanding Your Healthcare AI Reach",
    "message": "Dear Dr. Smith,\n\nI hope this email finds you well. I'm reaching out because I've been following your company's impressive work in healthcare AI, particularly your recent breakthrough in predictive diagnostics.\n\nWe specialize in helping healthcare AI companies like yours expand their market reach while optimizing operational costs. Our clients typically see:\n\n• 40% reduction in infrastructure costs\n• 3x faster time-to-market for new features\n• 60% improvement in model deployment efficiency\n\nI believe we could help accelerate your growth trajectory significantly. Would you be open to a brief 20-minute call next week to explore potential synergies?\n\nBest regards,\nSarah Johnson\nVP of Partnerships",
    "word_count": 112
  },
  "follow_up_sequence": [
    {
      "timing": "6 days later",
      "subject": "Re: Partnership Opportunity: Expanding Your Healthcare AI Reach",
      "message": "Dr. Smith,\n\nI wanted to follow up on my previous email about helping expand your healthcare AI platform's reach.\n\nI just read your team's paper on using transformer models for early disease detection - fascinating approach! This aligns perfectly with our recent work helping MedTech Innovations scale their similar platform to 10x more hospitals in just 8 months.\n\nWould you be interested in a case study showing how they achieved this growth while actually reducing operational complexity?\n\nLooking forward to your thoughts.\n\nBest regards,\nSarah",
      "word_count": 88
    },
    {
      "timing": "9 days later",
      "subject": "Final Follow-up: Healthcare AI Expansion Opportunity",
      "message": "Dr. Smith,\n\nI understand you have many priorities competing for your attention. I'll keep this brief.\n\nWe have a proven framework that's helped 12 healthcare AI companies achieve profitable growth in the past year. The average ROI has been 320% within 18 months.\n\nIf expanding market reach while optimizing costs becomes a priority, I'd be happy to share our approach. Otherwise, I wish you continued success with your groundbreaking work in predictive diagnostics.\n\nAll the best,\nSarah",
      "word_count": 82
    }
  ],
  "parsed_messages": [
    {
      "subject": "Partnership Opportunity: Expanding Your Healthcare AI Reach",
      "body": "Dear Dr. Smith,\n\nI hope this email finds you well...",
      "timing": "immediate"
    },
    {
      "subject": "Re: Partnership Opportunity: Expanding Your Healthcare AI Reach",
      "body": "Dr. Smith,\n\nI wanted to follow up on my previous email...",
      "timing": "6 days later"
    },
    {
      "subject": "Final Follow-up: Healthcare AI Expansion Opportunity",
      "body": "Dr. Smith,\n\nI understand you have many priorities...",
      "timing": "9 days later"
    }
  ],
  "quality_assessment": {
    "score": 88,
    "criteria": {
      "personalization": 90,
      "value_proposition": 92,
      "call_to_action": 85,
      "tone": 91,
      "clarity": 89,
      "urgency": 82
    }
  },
  "predicted_response_rate": 0.38,
  "channel": "email"
}
```

## Parsing Logic

### Email Parsing Function
The `parse_email_messages()` function in `workflow.py` handles multiple AI output formats:

1. **Primary Pattern**: Looks for "### **Email X:**" format
2. **Secondary Pattern**: Falls back to "---" delimiters
3. **Timing Extraction**: Parses "X days later" from follow-up messages
4. **Subject/Body Separation**: Extracts subject lines and body content

### Supported AI Output Formats

#### Format 1: Structured with Headers
```
### **Email 1:**
**Subject:** Your Subject Here
**Body:**
Email content here...

### **Email 2: 6 days later**
**Subject:** Follow-up Subject
**Body:**
Follow-up content...
```

#### Format 2: Delimiter-Based
```
Subject: Your Subject Here

Email content here...

---

Email 2 (6 days later):
Subject: Follow-up Subject

Follow-up content...
```

#### Format 3: Simple Sequential
```
Immediate Response:
Email content here...

Follow-up 1 (3 days later):
Follow-up content...
```

## Frontend Handling

### AllRuns Component Compatibility
The `AllRuns.js` component handles both legacy and new formats:

1. **Legacy Format**: `immediate_response` as object with `message` property
2. **New Format**: `immediate_response` as object with `message` and `word_count`
3. **String Fallback**: Direct string content for backward compatibility

### Data Extraction Logic
```javascript
// Extract message content
const getMessageContent = (response) => {
  if (typeof response === 'string') return response;
  if (response?.message) return response.message;
  if (response?.reply) return response.reply;
  return '';
};

// Extract quality score
const getQualityScore = (output) => {
  return output?.quality_assessment?.score || 
         output?.quality_score || 
         0;
};
```

## Quality Assessment Criteria

### Common Criteria (All Channels)
- **Personalization** (0-100): How well the message is tailored to the recipient
- **Value Proposition** (0-100): Clarity and strength of the value offered
- **Call to Action** (0-100): Effectiveness of the requested action
- **Tone** (0-100): Appropriateness of the communication style

### Email-Specific Criteria
- **Clarity** (0-100): How clear and easy to understand the message is
- **Urgency** (0-100): Appropriate level of urgency without being pushy

### Response Rate Prediction
- Range: 0.0 to 1.0 (0% to 100%)
- Based on: Message quality, personalization level, value proposition strength
- Factors: Industry, timing, follow-up sequence quality

## Error Handling

### Parsing Failures
When parsing fails, the system returns a fallback structure:
```json
{
  "immediate_response": {
    "message": "[Original unparsed content]",
    "word_count": 0
  },
  "follow_up_sequence": [],
  "error": "Failed to parse message format"
}
```

### Missing Data Handling
- Missing word counts default to 0
- Missing quality scores default to 0
- Missing follow-ups return empty array
- Channel defaults to "unknown" if not specified

## Best Practices

### For AI Agents
1. Use consistent formatting (prefer ### **Email X:** format)
2. Always include subject lines for emails
3. Specify timing for follow-ups explicitly
4. Keep LinkedIn messages within word limits

### For Frontend Development
1. Always check data type before accessing properties
2. Use fallback values for missing data
3. Handle both legacy and new formats
4. Validate word counts before display

### For API Integration
1. Validate output structure before storing
2. Ensure backward compatibility
3. Log parsing failures for debugging
4. Maintain consistent channel identification

## Migration Guide

### From Legacy to New Format
1. Old: `output.immediate_response` (string)
2. New: `output.immediate_response.message` (string within object)
3. Migration: Check type and extract accordingly

### Database Considerations
- Store full structured output in JSON columns
- Index by channel for filtering
- Maintain quality_score at top level for queries
- Preserve original AI output for debugging