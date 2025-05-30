#!/usr/bin/env python3
"""
Google Gemini AI Analysis for TruthGuard
Advanced bias detection and content analysis
"""

import os
import json
import logging
from datetime import datetime
import pymongo
import google.generativeai as genai
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('analysis_reports/gemini_analysis.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class GeminiAnalyzer:
    def __init__(self):
        # Configure Gemini
        genai.configure(api_key=os.getenv('GOOGLE_AI_API_KEY'))
        self.model = genai.GenerativeModel('gemini-1.5-pro')
        
        # MongoDB connection
        self.mongo_client = pymongo.MongoClient(os.getenv('MONGODB_URI',
    'mongodb+srv://TruthGuard:TruthGuard@cluster0.dhlp73u.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0'))
        self.db = self.mongo_client.truthguard
        self.collection = self.db.articles
        
        # Create directories
        os.makedirs('analysis_results', exist_ok=True)
        os.makedirs('analysis_reports', exist_ok=True)
        
        # Statistics
        self.stats = {
            'articles_analyzed': 0,
            'high_bias_detected': 0,
            'misinformation_flagged': 0,
            'processing_errors': 0
        }
    
    def analyze_article_comprehensive(self, article):
        """Comprehensive analysis using Gemini AI"""
        try:
            prompt = f"""
            You are TruthGuard AI, an expert media bias and misinformation detection system.
            
            Analyze this news article comprehensively and provide a detailed JSON response:
            
            Title: {article['title']}
            Source: {article['source']}
            Content: {article['content'][:8000]}
            
            Provide analysis in this exact JSON format:
            {{
                "bias_analysis": {{
                    "overall_score": 0.0-1.0,
                    "political_leaning": "far-left/left/center-left/center/center-right/right/far-right",
                    "bias_indicators": ["specific indicators"],
                    "language_bias": 0.0-1.0,
                    "source_bias": 0.0-1.0,
                    "framing_bias": 0.0-1.0
                }},
                "misinformation_analysis": {{
                    "risk_score": 0.0-1.0,
                    "fact_checks": [
                        {{
                            "claim": "specific claim",
                            "verdict": "true/false/misleading/unverified",
                            "confidence": 0.0-1.0,
                            "explanation": "explanation"
                        }}
                    ],
                    "red_flags": ["indicators"]
                }},
                "sentiment_analysis": {{
                    "overall_sentiment": -1.0 to 1.0,
                    "emotional_tone": "tone",
                    "key_phrases": ["phrases"]
                }},
                "credibility_assessment": {{
                    "overall_score": 0.0-1.0,
                    "evidence_quality": 0.0-1.0,
                    "source_reliability": 0.0-1.0
                }},
                "confidence": 0.0-1.0
            }}
            
            Respond only with valid JSON.
            """
            
            response = self.model.generate_content(prompt)
            
            try:
                analysis = json.loads(response.text)
                
                # Update article in MongoDB
                self.collection.update_one(
                    {'_id': article['_id']},
                    {
                        '$set': {
                            'ai_analysis': analysis,
                            'bias_score': analysis['bias_analysis']['overall_score'],
                            'misinformation_risk': analysis['misinformation_analysis']['risk_score'],
                            'sentiment': analysis['sentiment_analysis']['overall_sentiment'],
                            'credibility_score': analysis['credibility_assessment']['overall_score'],
                            'processing_status': 'analyzed',
                            'analyzed_at': datetime.utcnow(),
                            'analysis_model': 'gemini-1.5-pro'
                        }
                    }
                )
                
                # Update statistics
                self.stats['articles_analyzed'] += 1
                if analysis['bias_analysis']['overall_score'] > 0.7:
                    self.stats['high_bias_detected'] += 1
                if analysis['misinformation_analysis']['risk_score'] > 0.6:
                    self.stats['misinformation_flagged'] += 1
                
                logger.info(f"Analyzed: {article['title'][:50]}...")
                return analysis
                
            except json.JSONDecodeError:
                logger.error(f"Failed to parse Gemini response for article {article['_id']}")
                return self.generate_fallback_analysis(article)
                
        except Exception as e:
            logger.error(f"Error analyzing article {article['_id']}: {e}")
            self.stats['processing_errors'] += 1
            return self.generate_fallback_analysis(article)
    
    def generate_fallback_analysis(self, article):
        """Generate fallback analysis when Gemini fails"""
        content = article['content'].lower()
        
        # Simple keyword-based analysis
        bias_keywords = {
            'left': ['progressive', 'liberal', 'social justice', 'inequality'],
            'right': ['conservative', 'traditional', 'free market', 'law and order']
        }
        
        left_score = sum(1 for word in bias_keywords['left'] if word in content)
        right_score = sum(1 for word in bias_keywords['right'] if word in content)
        bias_score = min((left_score + right_score) / 10, 1.0)
        
        analysis = {
            'bias_analysis': {
                'overall_score': bias_score,
                'political_leaning': 'center',
                'bias_indicators': [],
                'language_bias': bias_score,
                'source_bias': 0.3,
                'framing_bias': bias_score * 0.8
            },
            'misinformation_analysis': {
                'risk_score': 0.3,
                'fact_checks': [],
                'red_flags': []
            },
            'sentiment_analysis': {
                'overall_sentiment': 0.0,
                'emotional_tone': 'neutral',
                'key_phrases': []
            },
            'credibility_assessment': {
                'overall_score': 0.7,
                'evidence_quality': 0.6,
                'source_reliability': 0.7
            },
            'confidence': 0.5
        }
        
        # Update MongoDB with fallback analysis
        self.collection.update_one(
            {'_id': article['_id']},
            {
                '$set': {
                    'ai_analysis': analysis,
                    'bias_score': analysis['bias_analysis']['overall_score'],
                    'misinformation_risk': analysis['misinformation_analysis']['risk_score'],
                    'sentiment': analysis['sentiment_analysis']['overall_sentiment'],
                    'credibility_score': analysis['credibility_assessment']['overall_score'],
                    'processing_status': 'analyzed_fallback',
                    'analyzed_at': datetime.utcnow(),
                    'analysis_model': 'fallback'
                }
            }
        )
        
        return analysis
    
    def run_batch_analysis(self, batch_size=50):
        """Run analysis on unprocessed articles"""
        logger.info("Starting Gemini AI batch analysis...")
        
        # Get unprocessed articles
        unprocessed = list(self.collection.find({
            'processing_status': {'$in': ['pending', None]}
        }).limit(batch_size))
        
        logger.info(f"Found {len(unprocessed)} articles to analyze")
        
        # Process with limited concurrency to respect API limits
        with ThreadPoolExecutor(max_workers=2) as executor:
            future_to_article = {
                executor.submit(self.analyze_article_comprehensive, article): article
                for article in unprocessed
            }
            
            for future in as_completed(future_to_article):
                article = future_to_article[future]
                try:
                    analysis = future.result()
                    time.sleep(1)  # Rate limiting
                except Exception as e:
                    logger.error(f"Analysis failed for {article['_id']}: {e}")
        
        # Save analysis summary
        self.save_analysis_summary()
        
        logger.info(f"Analysis complete. Stats: {self.stats}")
    
    def save_analysis_summary(self):
        """Save analysis summary for GitLab artifacts"""
        summary = {
            'analysis_timestamp': datetime.utcnow().isoformat(),
            'statistics': self.stats,
            'model_used': 'gemini-1.5-pro',
            'analysis_version': '2.0'
        }
        
        with open('analysis_results/gemini_summary.json', 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        logger.info("Analysis summary saved")

if __name__ == "__main__":
    analyzer = GeminiAnalyzer()
    analyzer.run_batch_analysis()
