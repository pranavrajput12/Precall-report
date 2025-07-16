# faq.py

import csv
import json
import os
import time
from typing import Dict, List, Optional
import threading
import shutil
from datetime import datetime

from cache import cache_result, metrics_collector, workflow_cache

# CSV file path
FAQ_CSV_PATH = os.path.join(os.path.dirname(__file__), "faq_knowledge_base.csv")
FAQ_CSV_BACKUP_PATH = os.path.join(os.path.dirname(__file__), "faq_knowledge_base_backup.csv")

# Thread lock for file operations
file_lock = threading.Lock()

class FAQManager:
    """Manages FAQ data from CSV file with CRUD operations"""
    
    def __init__(self):
        self.csv_path = FAQ_CSV_PATH
        self.backup_path = FAQ_CSV_BACKUP_PATH
        self._ensure_csv_exists()
    
    def _ensure_csv_exists(self):
        """Ensure CSV file exists"""
        if not os.path.exists(self.csv_path):
            # Create empty CSV with headers
            with open(self.csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Answer', 'Question', 'Category', 'Keywords'])
    
    def _create_backup(self):
        """Create backup of current CSV"""
        if os.path.exists(self.csv_path):
            shutil.copy2(self.csv_path, self.backup_path)
    
    def load_all_faqs(self) -> List[Dict]:
        """Load all FAQs from CSV"""
        faqs = []
        with file_lock:
            try:
                with open(self.csv_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for idx, row in enumerate(reader):
                        faq_item = {
                            'id': idx + 1,
                            'answer': row.get('Answer', '').strip(),
                            'question': row.get('Question', '').strip(),
                            'category': row.get('Category', '').strip() if 'Category' in row else '',
                            'keywords': row.get('Keywords', '').strip() if 'Keywords' in row else ''
                        }
                        # Skip empty rows
                        if faq_item['answer'] or faq_item['question']:
                            faqs.append(faq_item)
                return faqs
            except Exception as e:
                metrics_collector.increment_counter("faq_load_error")
                print(f"Error loading FAQs: {e}")
                return []
    
    def save_all_faqs(self, faqs: List[Dict]) -> bool:
        """Save all FAQs to CSV"""
        with file_lock:
            try:
                # Create backup before saving
                self._create_backup()
                
                with open(self.csv_path, 'w', newline='', encoding='utf-8') as f:
                    fieldnames = ['Answer', 'Question', 'Category', 'Keywords']
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    
                    for faq in faqs:
                        writer.writerow({
                            'Answer': faq.get('answer', ''),
                            'Question': faq.get('question', ''),
                            'Category': faq.get('category', ''),
                            'Keywords': faq.get('keywords', '')
                        })
                
                # Clear cache after update
                # Note: cache clearing would be done here if cache system supports it
                metrics_collector.increment_counter("faq_save_success")
                return True
            except Exception as e:
                metrics_collector.increment_counter("faq_save_error")
                print(f"Error saving FAQs: {e}")
                # Restore from backup if save failed
                if os.path.exists(self.backup_path):
                    shutil.copy2(self.backup_path, self.csv_path)
                return False
    
    def add_faq(self, question: str, answer: str, category: str = "", keywords: str = "") -> Dict:
        """Add new FAQ entry"""
        faqs = self.load_all_faqs()
        new_id = max([faq['id'] for faq in faqs], default=0) + 1
        
        new_faq = {
            'id': new_id,
            'question': question,
            'answer': answer,
            'category': category,
            'keywords': keywords
        }
        
        faqs.append(new_faq)
        
        if self.save_all_faqs(faqs):
            return new_faq
        else:
            raise Exception("Failed to add FAQ")
    
    def update_faq(self, faq_id: int, updates: Dict) -> Dict:
        """Update existing FAQ entry"""
        faqs = self.load_all_faqs()
        
        for i, faq in enumerate(faqs):
            if faq['id'] == faq_id:
                # Update fields
                if 'question' in updates:
                    faqs[i]['question'] = updates['question']
                if 'answer' in updates:
                    faqs[i]['answer'] = updates['answer']
                if 'category' in updates:
                    faqs[i]['category'] = updates['category']
                if 'keywords' in updates:
                    faqs[i]['keywords'] = updates['keywords']
                
                if self.save_all_faqs(faqs):
                    return faqs[i]
                else:
                    raise Exception("Failed to update FAQ")
        
        raise Exception(f"FAQ with id {faq_id} not found")
    
    def delete_faq(self, faq_id: int) -> bool:
        """Delete FAQ entry"""
        faqs = self.load_all_faqs()
        original_length = len(faqs)
        
        faqs = [faq for faq in faqs if faq['id'] != faq_id]
        
        if len(faqs) < original_length:
            return self.save_all_faqs(faqs)
        else:
            raise Exception(f"FAQ with id {faq_id} not found")
    
    def search_faqs(self, query: str, limit: int = 10) -> List[Dict]:
        """Search FAQs by query"""
        faqs = self.load_all_faqs()
        query_lower = query.lower()
        results = []
        
        for faq in faqs:
            score = 0
            
            # Score based on question match
            if query_lower in faq['question'].lower():
                score += 10
            
            # Score based on answer match
            if query_lower in faq['answer'].lower():
                score += 5
            
            # Score based on keywords match
            if faq.get('keywords'):
                keywords = faq['keywords'].lower().split(',')
                for keyword in keywords:
                    if query_lower in keyword.strip() or keyword.strip() in query_lower:
                        score += 7
            
            # Score based on category match
            if faq.get('category') and query_lower in faq['category'].lower():
                score += 3
            
            # Word-by-word matching
            query_words = query_lower.split()
            for word in query_words:
                if len(word) > 2:  # Skip very short words
                    if word in faq['question'].lower():
                        score += 2
                    if word in faq['answer'].lower():
                        score += 1
            
            if score > 0:
                results.append({
                    **faq,
                    'score': score
                })
        
        # Sort by score and limit
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:limit]

# Global FAQ manager instance
faq_manager = FAQManager()

@cache_result(ttl=3600, key_prefix="faq")  # 1 hour cache
def get_faq_answer(question: str) -> str:
    """
    Get FAQ answer for a question using semantic search
    """
    start_time = time.time()
    
    try:
        # Search for relevant FAQs
        results = faq_manager.search_faqs(question, limit=3)
        
        if results and results[0]['score'] > 5:
            answer = results[0]['answer']
            
            # Record metrics
            metrics_collector.record_timing("faq_lookup", time.time() - start_time)
            metrics_collector.increment_counter("faq_success")
            
            return answer
        else:
            metrics_collector.increment_counter("faq_no_match")
            return "I couldn't find a specific answer to your question. Please contact our support team for assistance."
    
    except Exception as e:
        metrics_collector.increment_counter("faq_error")
        return f"Error retrieving FAQ answer: {str(e)}"

def get_all_faq_topics() -> List[Dict]:
    """Get all available FAQ topics"""
    return faq_manager.load_all_faqs()

def add_faq_item(question: str, answer: str, category: str = "", keywords: str = "") -> Dict:
    """Add a new FAQ item"""
    try:
        result = faq_manager.add_faq(question, answer, category, keywords)
        metrics_collector.increment_counter("faq_item_added")
        return result
    except Exception as e:
        metrics_collector.increment_counter("faq_add_error")
        raise e

def update_faq_item(faq_id: int, updates: Dict) -> Dict:
    """Update an existing FAQ item"""
    try:
        result = faq_manager.update_faq(faq_id, updates)
        metrics_collector.increment_counter("faq_item_updated")
        return result
    except Exception as e:
        metrics_collector.increment_counter("faq_update_error")
        raise e

def delete_faq_item(faq_id: int) -> bool:
    """Delete an FAQ item"""
    try:
        result = faq_manager.delete_faq(faq_id)
        metrics_collector.increment_counter("faq_item_deleted")
        return result
    except Exception as e:
        metrics_collector.increment_counter("faq_delete_error")
        raise e

def search_faq(query: str, limit: int = 5) -> List[Dict]:
    """Search FAQ entries by query"""
    start_time = time.time()
    
    try:
        results = faq_manager.search_faqs(query, limit)
        
        # Record metrics
        metrics_collector.record_timing("faq_search", time.time() - start_time)
        metrics_collector.increment_counter("faq_search_performed")
        
        return results
    except Exception as e:
        metrics_collector.increment_counter("faq_search_error")
        return []

def get_faq_stats() -> dict:
    """Get FAQ usage statistics"""
    try:
        faqs = faq_manager.load_all_faqs()
        categories = {}
        
        for faq in faqs:
            cat = faq.get('category', 'Uncategorized')
            categories[cat] = categories.get(cat, 0) + 1
        
        return {
            "total_faqs": len(faqs),
            "categories": categories,
            "last_updated": datetime.now().isoformat(),
            "csv_path": FAQ_CSV_PATH
        }
    except Exception as e:
        return {"error": str(e)}

def export_to_csv() -> str:
    """Export FAQs to CSV and return the path"""
    return FAQ_CSV_PATH

def import_from_csv(csv_content: str) -> Dict:
    """Import FAQs from CSV content"""
    try:
        # Parse CSV content
        import io
        reader = csv.DictReader(io.StringIO(csv_content))
        
        faqs = []
        for row in reader:
            faq_item = {
                'answer': row.get('Answer', '').strip(),
                'question': row.get('Question', '').strip(),
                'category': row.get('Category', '').strip() if 'Category' in row else '',
                'keywords': row.get('Keywords', '').strip() if 'Keywords' in row else ''
            }
            if faq_item['answer'] or faq_item['question']:
                faqs.append(faq_item)
        
        # Save all FAQs
        if faq_manager.save_all_faqs(faqs):
            return {"success": True, "count": len(faqs)}
        else:
            return {"success": False, "error": "Failed to save FAQs"}
    
    except Exception as e:
        return {"success": False, "error": str(e)}