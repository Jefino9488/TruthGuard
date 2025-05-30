#!/usr/bin/env python3
"""
TruthGuard News Scraper
Automated news collection from multiple sources
"""

import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
import pymongo
from urllib.parse import urljoin, urlparse
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# News sources to scrape
NEWS_SOURCES = [
    {
        'name': 'Reuters',
        'url': 'https://www.reuters.com/world/',
        'selectors': {
            'articles': 'article',
            'title': 'h3 a, h2 a',
            'link': 'h3 a, h2 a'
        }
    },
    {
        'name': 'AP News',
        'url': 'https://apnews.com/',
        'selectors': {
            'articles': '.PagePromo',
            'title': '.PagePromo-title a',
            'link': '.PagePromo-title a'
        }
    },
    {
        'name': 'BBC',
        'url': 'https://www.bbc.com/news',
        'selectors': {
            'articles': '[data-testid="card-headline"]',
            'title': 'h3',
            'link': 'a'
        }
    }
]

class NewsScaper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # MongoDB connection
        self.mongo_client = pymongo.MongoClient(os.getenv('MONGODB_URI'))
        self.db = self.mongo_client.truthguard
        self.collection = self.db.articles
        
    def scrape_source(self, source):
        """Scrape articles from a single news source"""
        try:
            logger.info(f"Scraping {source['name']}...")
            response = self.session.get(source['url'], timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            articles = []
            
            # Find article elements
            article_elements = soup.select(source['selectors']['articles'])
            
            for element in article_elements[:10]:  # Limit to 10 articles per source
                try:
                    title_elem = element.select_one(source['selectors']['title'])
                    link_elem = element.select_one(source['selectors']['link'])
                    
                    if title_elem and link_elem:
                        title = title_elem.get_text(strip=True)
                        link = link_elem.get('href')
                        
                        if link and not link.startswith('http'):
                            link = urljoin(source['url'], link)
                        
                        if title and link:
                            article_content = self.scrape_article_content(link)
                            
                            article = {
                                'title': title,
                                'url': link,
                                'source': source['name'],
                                'content': article_content,
                                'scraped_at': datetime.utcnow(),
                                'processed': False
                            }
                            
                            articles.append(article)
                            
                except Exception as e:
                    logger.error(f"Error processing article element: {e}")
                    continue
            
            logger.info(f"Scraped {len(articles)} articles from {source['name']}")
            return articles
            
        except Exception as e:
            logger.error(f"Error scraping {source['name']}: {e}")
            return []
    
    def scrape_article_content(self, url):
        """Scrape full article content"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try different content selectors
            content_selectors = [
                'article',
                '.article-body',
                '.story-body',
                '.post-content',
                '[data-testid="article-body"]'
            ]
            
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    # Extract text from paragraphs
                    paragraphs = content_elem.find_all('p')
                    content = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
                    
                    if len(content) > 200:  # Ensure we have substantial content
                        return content
            
            # Fallback: get all paragraph text
            paragraphs = soup.find_all('p')
            content = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 50])
            
            return content[:5000]  # Limit content length
            
        except Exception as e:
            logger.error(f"Error scraping article content from {url}: {e}")
            return "Content could not be extracted"
    
    def store_articles(self, articles):
        """Store articles in MongoDB"""
        if not articles:
            return
        
        try:
            # Insert articles that don't already exist
            for article in articles:
                existing = self.collection.find_one({'url': article['url']})
                if not existing:
                    self.collection.insert_one(article)
                    logger.info(f"Stored: {article['title'][:50]}...")
                else:
                    logger.info(f"Already exists: {article['title'][:50]}...")
                    
        except Exception as e:
            logger.error(f"Error storing articles: {e}")
    
    def run(self):
        """Run the complete scraping process"""
        logger.info("Starting TruthGuard news scraping...")
        
        all_articles = []
        
        for source in NEWS_SOURCES:
            articles = self.scrape_source(source)
            all_articles.extend(articles)
            time.sleep(2)  # Be respectful to servers
        
        # Store articles in MongoDB
        self.store_articles(all_articles)
        
        # Save to file for GitLab artifacts
        os.makedirs('scraped_data', exist_ok=True)
        with open('scraped_data/articles.json', 'w') as f:
            json.dump(all_articles, f, default=str, indent=2)
        
        logger.info(f"Scraping complete. Total articles: {len(all_articles)}")
        
        return all_articles

if __name__ == "__main__":
    scraper = NewsScaper()
    scraper.run()
