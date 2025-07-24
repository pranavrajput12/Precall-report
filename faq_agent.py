# faq_agent.py

import json
import logging
from typing import List, Dict, Any, Optional
from crewai import Agent, Task, Crew
from langchain_openai import AzureChatOpenAI
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from faq import faq_manager, get_faq_answer
from agents import llm  # Use the existing LLM configuration
from logging_config import log_info, log_error, log_warning, log_debug

logger = logging.getLogger(__name__)

class FAQAgent:
    """Dedicated CrewAI agent for intelligent FAQ management and retrieval"""
    
    def __init__(self):
        self.semantic_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.faq_cache = {}
        self._load_faq_embeddings()
        
        # Create the FAQ specialist agent
        self.agent = Agent(
            role='FAQ Specialist',
            goal='Intelligently understand questions and provide accurate, relevant answers from the knowledge base',
            backstory="""You are an expert FAQ specialist with deep knowledge of Qubit Capital's services, 
            processes, and value propositions. You excel at understanding both explicit and implicit questions, 
            identifying underlying concerns, and providing comprehensive answers that address the real needs 
            behind the questions. You can also identify when multiple FAQ entries might be relevant to a 
            single question and synthesize them into a coherent response.""",
            verbose=True,
            allow_delegation=False,
            llm=llm
        )
    
    def _load_faq_embeddings(self):
        """Pre-compute embeddings for all FAQ entries for semantic search"""
        try:
            faqs = faq_manager.load_all_faqs()
            self.faq_embeddings = []
            self.faq_data = []
            
            for faq in faqs:
                # Create a combined text for embedding
                combined_text = f"{faq['question']} {faq['answer']} {faq.get('keywords', '')}"
                embedding = self.semantic_model.encode(combined_text)
                self.faq_embeddings.append(embedding)
                self.faq_data.append(faq)
            
            self.faq_embeddings = np.array(self.faq_embeddings) if self.faq_embeddings else np.array([])
            log_info(logger, f"Loaded {len(self.faq_data)} FAQ embeddings")
        except Exception as e:
            log_error(logger, "Error loading FAQ embeddings", e)
            self.faq_embeddings = np.array([])
            self.faq_data = []
    
    def semantic_search(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Perform semantic search to find most relevant FAQ entries.
        
        This method uses a sentence transformer model to encode the query into
        a vector embedding, then calculates cosine similarity with pre-computed
        FAQ embeddings to find the most semantically similar entries.
        
        Args:
            query (str): The search query or question to find relevant FAQs for
            top_k (int, optional): Maximum number of results to return. Defaults to 5.
            
        Returns:
            List[Dict]: List of relevant FAQ entries with similarity scores,
                        sorted by relevance (highest similarity first)
        """
        if len(self.faq_embeddings) == 0:
            return []
        
        try:
            # Encode the query
            query_embedding = self.semantic_model.encode(query)
            
            # Calculate cosine similarities
            similarities = cosine_similarity([query_embedding], self.faq_embeddings)[0]
            
            # Get top-k most similar entries
            top_indices = similarities.argsort()[-top_k:][::-1]
            
            results = []
            for idx in top_indices:
                if similarities[idx] > 0.3:  # Threshold for relevance
                    result = self.faq_data[idx].copy()
                    result['similarity_score'] = float(similarities[idx])
                    results.append(result)
            
            return results
        except Exception as e:
            log_error(logger, "Error in semantic search", e)
            return []
    
    def analyze_question(self, question: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analyze a question to understand intent and extract key information.
        
        This method uses the LLM to analyze a question and extract structured
        information about its intent, type, and key entities. The analysis helps
        in providing more accurate and contextually relevant answers.
        
        Args:
            question (str): The question to analyze
            context (Dict[str, Any], optional): Additional context that might help
                                               with question analysis. Defaults to None.
            
        Returns:
            Dict[str, Any]: Structured analysis of the question including:
                            - question_type: The type of question (factual, comparison, etc.)
                            - intent: The underlying intent of the question
                            - key_entities: Important entities mentioned in the question
                            - implied_needs: Needs implied by the question
                            - suggested_faq_categories: Relevant FAQ categories
        """
        
        analysis_prompt = f"""
        Analyze this question from a prospect and extract key information:
        
        Question: {question}
        
        Context: {json.dumps(context, indent=2) if context else 'No additional context'}
        
        Provide your analysis in JSON format:
        {{
            "question_type": "factual|comparison|process|concern|objection",
            "main_intent": "What is the prospect really trying to understand?",
            "key_topics": ["topic1", "topic2"],
            "implicit_concerns": ["concern1", "concern2"],
            "urgency_level": "high|medium|low",
            "follow_up_questions": ["What else might they want to know?"],
            "recommended_approach": "How should we structure our response?"
        }}
        """
        
        try:
            result = llm.invoke(analysis_prompt)
            analysis = json.loads(result.content)
            return analysis
        except Exception as e:
            log_error(logger, "Error analyzing question", e)
            return {
                "question_type": "unknown",
                "main_intent": question,
                "key_topics": [],
                "implicit_concerns": [],
                "urgency_level": "medium",
                "follow_up_questions": [],
                "recommended_approach": "Provide direct answer"
            }
    
    def get_intelligent_answer(self, question: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get intelligent answer combining semantic search and LLM reasoning"""
        
        # Analyze the question
        analysis = self.analyze_question(question, context)
        
        # Perform semantic search
        relevant_faqs = self.semantic_search(question, top_k=5)
        
        # Also search for implicit concerns
        all_relevant = relevant_faqs.copy()
        for concern in analysis.get('implicit_concerns', []):
            implicit_results = self.semantic_search(concern, top_k=3)
            for result in implicit_results:
                if result not in all_relevant:
                    all_relevant.append(result)
        
        if not all_relevant:
            return {
                "answer": "I don't have specific information about that in our FAQ database. Please contact our team for a personalized response.",
                "confidence": 0.0,
                "sources": [],
                "analysis": analysis
            }
        
        # Create a comprehensive answer using the FAQ agent
        answer_task = Task(
            description=f"""
            Based on the question analysis and relevant FAQ entries, provide a comprehensive answer.
            
            Question: {question}
            
            Question Analysis:
            {json.dumps(analysis, indent=2)}
            
            Relevant FAQ Entries:
            {json.dumps(all_relevant, indent=2)}
            
            Requirements:
            1. Synthesize information from multiple FAQ entries if relevant
            2. Address both explicit question and implicit concerns
            3. Provide specific, actionable information
            4. Include relevant statistics, examples, or case studies from FAQs
            5. Suggest logical next steps or follow-up topics
            6. Maintain Qubit Capital's professional, helpful tone
            
            Format your response as:
            - Direct answer to the question
            - Additional relevant context
            - Suggested next steps or related topics
            """,
            expected_output="A comprehensive, professional answer that directly addresses the question with specific information from our FAQ database",
            agent=self.agent
        )
        
        crew = Crew(
            agents=[self.agent],
            tasks=[answer_task],
            verbose=True
        )
        
        try:
            # For now, let's use a direct LLM call instead of CrewAI to avoid complexity
            prompt = f"""
            Based on the question analysis and relevant FAQ entries, provide a comprehensive answer.
            
            Question: {question}
            
            Question Analysis:
            {json.dumps(analysis, indent=2)}
            
            Relevant FAQ Entries:
            {json.dumps(all_relevant, indent=2)}
            
            Requirements:
            1. Synthesize information from multiple FAQ entries if relevant
            2. Address both explicit question and implicit concerns
            3. Provide specific, actionable information
            4. Include relevant statistics, examples, or case studies from FAQs
            5. Suggest logical next steps or follow-up topics
            6. Maintain Qubit Capital's professional, helpful tone
            
            Format your response as:
            - Direct answer to the question
            - Additional relevant context
            - Suggested next steps or related topics
            """
            
            result = llm.invoke(prompt)
            answer_text = result.content
            
            # Calculate confidence based on relevance scores
            avg_similarity = np.mean([faq['similarity_score'] for faq in all_relevant[:3]])
            confidence = min(0.95, avg_similarity * 1.2)  # Scale and cap at 95%
            
            return {
                "answer": answer_text,
                "confidence": confidence,
                "sources": all_relevant[:3],
                "analysis": analysis,
                "suggested_follow_ups": analysis.get('follow_up_questions', [])
            }
            
        except Exception as e:
            log_error(logger, "Error generating intelligent answer", e)
            # Fallback to simple FAQ lookup
            if all_relevant:
                # Use the best matching FAQ entry
                best_faq = all_relevant[0]
                return {
                    "answer": best_faq['answer'],
                    "confidence": best_faq['similarity_score'],
                    "sources": all_relevant[:3],
                    "analysis": analysis
                }
            else:
                return {
                    "answer": "I don't have specific information about that in our FAQ database. Please contact our team for a personalized response.",
                    "confidence": 0.0,
                    "sources": [],
                    "analysis": analysis
                }
    
    def suggest_new_faqs(self, unanswered_questions: List[str]) -> List[Dict[str, str]]:
        """Analyze unanswered questions and suggest new FAQ entries"""
        
        suggestion_task = Task(
            description=f"""
            Analyze these unanswered questions and suggest new FAQ entries for Qubit Capital.
            
            Unanswered Questions:
            {json.dumps(unanswered_questions, indent=2)}
            
            For each suggested FAQ entry, provide:
            1. A clear, concise question
            2. A comprehensive answer based on Qubit Capital's services
            3. Relevant keywords for search
            4. Category classification
            
            Format as JSON array:
            [
                {{
                    "question": "Clear question",
                    "answer": "Comprehensive answer",
                    "keywords": "keyword1, keyword2, keyword3",
                    "category": "Fundraising|Process|Technology|General"
                }}
            ]
            """,
            expected_output="A JSON array of suggested FAQ entries with questions, answers, keywords, and categories",
            agent=self.agent
        )
        
        try:
            # Use direct LLM call instead of CrewAI
            result = llm.invoke(suggestion_task.description)
            suggestions = json.loads(result.content)
            return suggestions
        except Exception as e:
            log_error(logger, "Error suggesting new FAQs", e)
            return []
    
    def evaluate_answer_quality(self, question: str, answer: str, feedback: Optional[str] = None) -> Dict[str, Any]:
        """Evaluate the quality of an FAQ answer and suggest improvements"""
        
        evaluation_task = Task(
            description=f"""
            Evaluate the quality of this FAQ answer and suggest improvements.
            
            Question: {question}
            Answer: {answer}
            User Feedback: {feedback if feedback else "No feedback provided"}
            
            Evaluate based on:
            1. Completeness - Does it fully address the question?
            2. Clarity - Is it easy to understand?
            3. Accuracy - Is the information correct and up-to-date?
            4. Actionability - Does it provide clear next steps?
            5. Tone - Is it professional and helpful?
            
            Provide evaluation as JSON:
            {{
                "overall_score": 0-100,
                "completeness": 0-100,
                "clarity": 0-100,
                "accuracy": 0-100,
                "actionability": 0-100,
                "tone": 0-100,
                "strengths": ["strength1", "strength2"],
                "improvements": ["improvement1", "improvement2"],
                "suggested_revision": "Improved answer text if needed"
            }}
            """,
            expected_output="A JSON object with scores, strengths, improvements, and suggested revision for the FAQ answer",
            agent=self.agent
        )
        
        try:
            # Use direct LLM call instead of CrewAI
            result = llm.invoke(evaluation_task.description)
            evaluation = json.loads(result.content)
            return evaluation
        except Exception as e:
            log_error(logger, "Error evaluating answer quality", e)
            return {
                "overall_score": 70,
                "error": str(e)
            }

# Global FAQ agent instance
faq_agent = FAQAgent()

# Convenience functions for workflow integration
def get_intelligent_faq_answer(question: str, context: Dict[str, Any] = None) -> str:
    """Get an intelligent FAQ answer for workflow integration"""
    result = faq_agent.get_intelligent_answer(question, context)
    return result['answer']

def analyze_questions_batch(questions: List[str], context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """Analyze a batch of questions and return intelligent answers"""
    results = []
    for question in questions:
        result = faq_agent.get_intelligent_answer(question, context)
        results.append({
            'question': question,
            'answer': result['answer'],
            'confidence': result['confidence'],
            'analysis': result.get('analysis', {})
        })
    return results