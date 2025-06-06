#!/usr/bin/env python3
"""
TruthGuard Data Validation Script
Validates scraped news articles for quality and completeness
"""

import os
import json
import logging
import pymongo
from datetime import datetime, timedelta
from dotenv import load_dotenv
import re
import sys

# Load environment variables
load_dotenv('.env.local')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('validation_logs/validation.log', mode='a'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create necessary directories
os.makedirs('validation_logs', exist_ok=True)
os.makedirs('validation_reports', exist_ok=True)

class ArticleValidator:
    def __init__(self):
        # MongoDB connection
        self.mongo_uri = os.getenv('MONGODB_URI')
        if not self.mongo_uri:
            raise ValueError("MONGODB_URI environment variable not set")
        
        self.mongo_client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.mongo_client.truthguard
        self.collection = self.db.articles
        
        # Validation statistics
        self.stats = {
            'articles_checked': 0,
            'articles_passed': 0,
            'articles_failed': 0,
            'articles_fixed': 0,
            'validation_errors': {}
        }
        
        # Validation criteria
        self.criteria = {
            'min_content_length': 200,
            'min_title_length': 10,
            'max_title_length': 200,
            'required_fields': ['title', 'url', 'content', 'source', 'scraped_at'],
            'min_word_count': 50,
            'max_age_days': 30
        }
    
    def validate_article(self, article):
        """Validate a single article against quality criteria"""
        errors = []
        
        # Check required fields
        for field in self.criteria['required_fields']:
            if field not in article or not article[field]:
                errors.append(f"Missing required field: {field}")
        
        # If missing critical fields, can't continue validation
        if 'title' not in article or 'content' not in article:
            return False, errors
        
        # Check content length
        if len(article['content']) < self.criteria['min_content_length']:
            errors.append(f"Content too short: {len(article['content'])} chars (min: {self.criteria['min_content_length']})")
        
        # Check title length
        if len(article['title']) < self.criteria['min_title_length']:
            errors.append(f"Title too short: {len(article['title'])} chars (min: {self.criteria['min_title_length']})")
        
        if len(article['title']) > self.criteria['max_title_length']:
            errors.append(f"Title too long: {len(article['title'])} chars (max: {self.criteria['max_title_length']})")
        
        # Check word count
        word_count = len(article['content'].split())
        if word_count < self.criteria['min_word_count']:
            errors.append(f"Word count too low: {word_count} words (min: {self.criteria['min_word_count']})")
        
        # Check article age
        if 'scraped_at' in article:
            try:
                scraped_at = article['scraped_at']
                if isinstance(scraped_at, str):
                    scraped_at = datetime.fromisoformat(scraped_at.replace('Z', '+00:00'))
                
                age_days = (datetime.utcnow() - scraped_at).days
                if age_days > self.criteria['max_age_days']:
                    errors.append(f"Article too old: {age_days} days (max: {self.criteria['max_age_days']})")
            except Exception as e:
                errors.append(f"Invalid scraped_at date: {e}")
        
        # Check for vector embeddings
        if 'content_embedding' not in article or article['content_embedding'] is None:
            errors.append("Missing content embedding")
        
        # Check for duplicate content (exact matches)
        if 'content_hash' in article:
            duplicate_count = self.collection.count_documents({
                'content_hash': article['content_hash'],
                '_id': {'$ne': article['_id']}
            })
            if duplicate_count > 0:
                errors.append(f"Duplicate content detected: {duplicate_count} other articles with same content hash")
        
        # Return validation result
        return len(errors) == 0, errors
    
    def fix_article(self, article, errors):
        """Attempt to fix validation issues"""
        fixed = False
        fixes_applied = []
        
        # Create a copy of the article to modify
        fixed_article = article.copy()
        
        # Fix missing word count
        if 'word_count' not in fixed_article and 'content' in fixed_article:
            fixed_article['word_count'] = len(fixed_article['content'].split())
            fixes_applied.append("Added missing word_count")
            fixed = True
        
        # Fix missing content_hash
        if 'content_hash' not in fixed_article and 'content' in fixed_article:
            import hashlib
            fixed_article['content_hash'] = hashlib.md5(fixed_article['content'].encode()).hexdigest()
            fixes_applied.append("Added missing content_hash")
            fixed = True
        
        # Fix missing processing_status
        if 'processing_status' not in fixed_article:
            fixed_article['processing_status'] = 'pending'
            fixes_applied.append("Added missing processing_status")
            fixed = True
        
        # Fix missing processed flag
        if 'processed' not in fixed_article:
            fixed_article['processed'] = False
            fixes_applied.append("Added missing processed flag")
            fixed = True
        
        # If fixes were applied, update the article in the database
        if fixed:
            try:
                self.collection.update_one({'_id': article['_id']}, {'$set': fixed_article})
                logger.info(f"Fixed article {article['_id']}: {', '.join(fixes_applied)}")
                return True, fixes_applied
            except Exception as e:
                logger.error(f"Error fixing article {article['_id']}: {e}")
                return False, []
        
        return False, []
    
    def run_validation(self, days_back=7, fix_issues=True):
        """Run validation on recently scraped articles"""
        logger.info("Starting article validation...")
        
        # Get articles scraped in the last N days
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        query = {
            'scraped_at': {'$gte': cutoff_date}
        }
        
        articles = list(self.collection.find(query))
        logger.info(f"Found {len(articles)} articles to validate")
        
        validation_results = []
        
        for article in articles:
            self.stats['articles_checked'] += 1
            
            # Validate article
            valid, errors = self.validate_article(article)
            
            if valid:
                self.stats['articles_passed'] += 1
            else:
                self.stats['articles_failed'] += 1
                
                # Track error types
                for error in errors:
                    error_type = error.split(':')[0].strip()
                    self.stats['validation_errors'][error_type] = self.stats['validation_errors'].get(error_type, 0) + 1
                
                # Try to fix issues
                if fix_issues:
                    fixed, fixes = self.fix_article(article, errors)
                    if fixed:
                        self.stats['articles_fixed'] += 1
            
            # Record validation result
            validation_results.append({
                'article_id': str(article['_id']),
                'title': article.get('title', 'Unknown'),
                'valid': valid,
                'errors': errors,
                'source': article.get('source', 'Unknown'),
                'word_count': article.get('word_count', 0)
            })
        
        # Save validation report
        self.save_validation_report(validation_results)
        
        logger.info(f"Validation complete. Stats: {self.stats}")
        return self.stats
    
    def save_validation_report(self, validation_results):
        """Save validation report to file"""
        report = {
            'validation_timestamp': datetime.utcnow().isoformat(),
            'statistics': self.stats,
            'validation_criteria': self.criteria,
            'results_sample': validation_results[:50]  # Limit for file size
        }
        
        # Save report
        filename = f"validation_reports/validation_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Validation report saved to {filename}")

if __name__ == "__main__":
    # Parse command line arguments
    days_back = 7
    fix_issues = True
    
    if len(sys.argv) > 1:
        try:
            days_back = int(sys.argv[1])
        except ValueError:
            logger.error(f"Invalid days_back value: {sys.argv[1]}. Using default: 7")
    
    if len(sys.argv) > 2:
        fix_issues = sys.argv[2].lower() in ('true', 'yes', '1', 't', 'y')
    
    validator = ArticleValidator()
    validator.run_validation(days_back=days_back, fix_issues=fix_issues)