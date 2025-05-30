#!/usr/bin/env python3
"""
Enhanced TruthGuard News Scraper for GitLab CI/CD
Comprehensive news collection with MongoDB integration
"""

import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime, timedelta
import pymongo
from urllib.parse import urljoin, urlparse
import time
import logging
import feedparser
import newspaper
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraping_logs/scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Enhanced news sources with RSS feeds and multiple endpoints
NEWS_SOURCES = [
    {
        'name': 'Reuters',
        'urls': [
            'https://www.reuters.com/world/',
            'https://www.reuters.com/business/',
            'https://www.reuters.com/technology/'
        ],
        'rss': 'https://www.reuters.com/arc/outboundfeeds/rss/',
        'selectors': {
            'articles': 'article, .story-card',
            'title': 'h3 a, h2 a, .story-title',
            'link': 'h3 a, h2 a, .story-title a'
        }
    },
    {
        'name': 'Associated Press',
        'urls': [
            'https://apnews.com/',
            'https://apnews.com/hub/politics',
            'https://apnews.com/hub/business'
        ],
        'rss': 'https://apnews.com/index.rss',
        'selectors': {
            'articles': '.PagePromo, .CardHeadline',
            'title': '.PagePromo-title a, .CardHeadline-headline',
            'link': '.PagePromo-title a, .CardHeadline-headline a'
        }
    },
    {
        'name': 'BBC',
        'urls': [
            'https://www.bbc.com/news',
            'https://www.bbc.com/news/world',
            'https://www.bbc.com/news/business'
        ],
        'rss': 'http://feeds.bbci.co.uk/news/rss.xml',
        'selectors': {
            'articles': '[data-testid="card-headline"], .media__content',
            'title': 'h3, .media__title',
            'link': 'a'
        }
    },
    {
        'name': 'CNN',
        'urls': [
            'https://www.cnn.com/',
            'https://www.cnn.com/politics',
            'https://www.cnn.com/business'
        ],
        'rss': 'http://rss.cnn.com/rss/edition.rss',
        'selectors': {
            'articles': '.card, .cd__content',
            'title': '.cd__headline, .card__title',
            'link': '.cd__headline a, .card__title a'
        }
    },
    {
        'name': 'Fox News',
        'urls': [
            'https://www.foxnews.com/',
            'https://www.foxnews.com/politics',
            'https://www.foxnews.com/us'
        ],
        'rss': 'https://feeds.foxnews.com/foxnews/latest',
        'selectors': {
            'articles': '.article, .content',
            'title': '.title a, h2 a, h3 a',
            'link': '.title a, h2 a, h3 a'
        }
    }
]

class EnhancedNewsScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        
        # MongoDB connection
        self.mongo_client = pymongo.MongoClient(os.getenv('MONGODB_URI', 
    'mongodb+srv://TruthGuard:TruthGuard@cluster0.dhlp73u.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0'))
        self.db = self.mongo_client.truthguard
        self.collection = self.db.articles
        
        # Create directories
        os.makedirs('scraped_data', exist_ok=True)
        os.makedirs('scraping_logs', exist_ok=True)
        
        # Statistics
        self.stats = {
            'sources_processed': 0,
            'articles_found': 0,
            'articles_stored': 0,
            'duplicates_skipped': 0,
            'errors': 0
        }
        
    def scrape_rss_feed(self, rss_url, source_name):
        """Scrape articles from RSS feed"""
        try:
            logger.info(f"Scraping RSS feed for {source_name}: {rss_url}")
            feed = feedparser.parse(rss_url)
            articles = []
            
            for entry in feed.entries[:10]:  # Limit to 10 most recent
                try:
                    article_url = entry.link
                    title = entry.title
                    
                    # Get full article content
                    article_content = self.scrape_article_with_newspaper(article_url)
                    
                    if article_content:
                        article = {
                            'title': title,
                            'url': article_url,
                            'source': source_name,
                            'content': article_content['content'],
                            'author': article_content.get('author', 'Unknown'),
                            'publish_date': article_content.get('publish_date'),
                            'scraped_at': datetime.utcnow(),
                            'content_hash': hashlib.md5(article_content['content'].encode()).hexdigest(),
                            'scraping_method': 'rss_feed'
                        }
                        articles.append(article)
                        
                except Exception as e:
                    logger.error(f"Error processing RSS entry: {e}")
                    continue
            
            logger.info(f"Extracted {len(articles)} articles from RSS feed")
            return articles
            
        except Exception as e:
            logger.error(f"Error scraping RSS feed {rss_url}: {e}")
            return []
    
    def scrape_article_with_newspaper(self, url):
        """Enhanced article scraping using newspaper3k library"""
        try:
            article = newspaper.Article(url)
            article.download()
            article.parse()
            
            if len(article.text) < 100:
                # Fallback to manual scraping
                return self.scrape_article_manual(url)
            
            return {
                'content': article.text,
                'author': ', '.join(article.authors) if article.authors else 'Unknown',
                'publish_date': article.publish_date.isoformat() if article.publish_date else datetime.utcnow().isoformat(),
                'top_image': article.top_image,
                'keywords': article.keywords
            }
            
        except Exception as e:
            logger.error(f"Newspaper3k failed for {url}: {e}")
            return self.scrape_article_manual(url)
    
    def scrape_article_manual(self, url):
        """Manual article scraping as fallback"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract content using multiple strategies
            content = self.extract_content_advanced(soup)
            author = self.extract_author_advanced(soup)
            publish_date = self.extract_publish_date_advanced(soup)
            
            if len(content) < 100:
                return None
            
            return {
                'content': content,
                'author': author,
                'publish_date': publish_date,
                'top_image': None,
                'keywords': []
            }
            
        except Exception as e:
            logger.error(f"Manual scraping failed for {url}: {e}")
            return None
    
    def extract_content_advanced(self, soup):
        """Advanced content extraction with multiple fallbacks"""
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            element.decompose()
        
        # Try multiple content selectors
        content_selectors = [
            'article',
            '.article-body',
            '.story-body',
            '.post-content',
            '.entry-content',
            '[data-testid="article-body"]',
            '.content',
            '.article-content',
            '.story-content',
            '.main-content'
        ]
        
        for selector in content_selectors:
            element = soup.select_one(selector)
            if element:
                # Extract text from paragraphs
                paragraphs = element.find_all('p')
                content = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
                
                if len(content) > 200:
                    return content
        
        # Final fallback: all paragraphs
        paragraphs = soup.find_all('p')
        content = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 30])
        
        return content[:10000]  # Limit content length
    
    def extract_author_advanced(self, soup):
        """Advanced author extraction"""
        author_selectors = [
            '[rel="author"]',
            '.author',
            '.byline',
            '[data-testid="author"]',
            '.article-author',
            '.story-author',
            '[name="author"]',
            '[property="article:author"]'
        ]
        
        for selector in author_selectors:
            element = soup.select_one(selector)
            if element:
                author = element.get('content') or element.get_text(strip=True)
                if author:
                    return author
        
        return 'Unknown Author'
    
    def extract_publish_date_advanced(self, soup):
        """Advanced publish date extraction"""
        date_selectors = [
            '[property="article:published_time"]',
            '[name="publish_date"]',
            '.publish-date',
            '.article-date',
            'time[datetime]',
            '.date',
            '.story-date'
        ]
        
        for selector in date_selectors:
            element = soup.select_one(selector)
            if element:
                date_value = (element.get('content') or 
                             element.get('datetime') or 
                             element.get_text(strip=True))
                
                if date_value:
                    try:
                        return datetime.fromisoformat(date_value.replace('Z', '+00:00')).isoformat()
                    except:
                        try:
                            return datetime.strptime(date_value, '%Y-%m-%d').isoformat()
                        except:
                            continue
        
        return datetime.utcnow().isoformat()
    
    def scrape_source_comprehensive(self, source):
        """Comprehensive scraping from multiple source endpoints"""
        all_articles = []
        
        # First try RSS feed
        if source.get('rss'):
            rss_articles = self.scrape_rss_feed(source['rss'], source['name'])
            all_articles.extend(rss_articles)
        
        # Then scrape web pages
        for url in source['urls']:
            try:
                web_articles = self.scrape_web_page(url, source)
                all_articles.extend(web_articles)
                time.sleep(2)  # Be respectful
            except Exception as e:
                logger.error(f"Error scraping {url}: {e}")
                self.stats['errors'] += 1
        
        # Remove duplicates based on content hash
        unique_articles = {}
        for article in all_articles:
            content_hash = article.get('content_hash')
            if content_hash and content_hash not in unique_articles:
                unique_articles[content_hash] = article
        
        return list(unique_articles.values())
    
    def scrape_web_page(self, url, source):
        """Scrape articles from a web page"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            articles = []
            
            # Extract article links
            article_links = self.extract_article_links_advanced(soup, url, source['selectors'])
            
            # Process each article link
            for link_info in article_links[:5]:  # Limit per page
                try:
                    article_content = self.scrape_article_with_newspaper(link_info['url'])
                    
                    if article_content:
                        article = {
                            'title': link_info['title'],
                            'url': link_info['url'],
                            'source': source['name'],
                            'content': article_content['content'],
                            'author': article_content.get('author', 'Unknown'),
                            'publish_date': article_content.get('publish_date'),
                            'scraped_at': datetime.utcnow(),
                            'content_hash': hashlib.md5(article_content['content'].encode()).hexdigest(),
                            'scraping_method': 'web_page',
                            'source_url': url
                        }
                        articles.append(article)
                        
                except Exception as e:
                    logger.error(f"Error processing article {link_info['url']}: {e}")
                    continue
            
            return articles
            
        except Exception as e:
            logger.error(f"Error scraping web page {url}: {e}")
            return []
    
    def extract_article_links_advanced(self, soup, base_url, selectors):
        """Advanced article link extraction"""
        links = []
        
        # Try source-specific selectors first
        try:
            article_elements = soup.select(selectors['articles'])
            
            for element in article_elements:
                title_elem = element.select_one(selectors['title'])
                link_elem = element.select_one(selectors['link'])
                
                if title_elem and link_elem:
                    title = title_elem.get_text(strip=True)
                    href = link_elem.get('href')
                    
                    if href and title and len(title) > 10:
                        full_url = urljoin(base_url, href) if not href.startswith('http') else href
                        links.append({'url': full_url, 'title': title})
        except:
            pass
        
        # Fallback to generic selectors
        if not links:
            generic_selectors = [
                'a[href*="/article/"]',
                'a[href*="/story/"]',
                'a[href*="/news/"]',
                'h1 a', 'h2 a', 'h3 a'
            ]
            
            for selector in generic_selectors:
                elements = soup.select(selector)
                for element in elements[:10]:
                    href = element.get('href')
                    title = element.get_text(strip=True)
                    
                    if href and title and len(title) > 10:
                        full_url = urljoin(base_url, href) if not href.startswith('http') else href
                        if not any(l['url'] == full_url for l in links):
                            links.append({'url': full_url, 'title': title})
        
        return links
    
    def store_articles_batch(self, articles):
        """Store articles in MongoDB with duplicate checking"""
        if not articles:
            return
        
        stored_count = 0
        duplicate_count = 0
        
        for article in articles:
            try:
                # Check for existing article by URL or content hash
                existing = self.collection.find_one({
                    '$or': [
                        {'url': article['url']},
                        {'content_hash': article['content_hash']}
                    ]
                })
                
                if not existing:
                    # Add additional metadata
                    article['processing_status'] = 'pending'
                    article['analysis_version'] = '2.0'
                    article['word_count'] = len(article['content'].split())
                    
                    self.collection.insert_one(article)
                    stored_count += 1
                    logger.info(f"Stored: {article['title'][:50]}...")
                else:
                    duplicate_count += 1
                    logger.debug(f"Duplicate skipped: {article['title'][:50]}...")
                    
            except Exception as e:
                logger.error(f"Error storing article: {e}")
                self.stats['errors'] += 1
        
        self.stats['articles_stored'] += stored_count
        self.stats['duplicates_skipped'] += duplicate_count
        
        logger.info(f"Batch processed: {stored_count} stored, {duplicate_count} duplicates")
    
    def run_comprehensive_scraping(self):
        """Run comprehensive scraping with parallel processing"""
        logger.info("Starting comprehensive TruthGuard news scraping...")
        
        all_articles = []
        
        # Use ThreadPoolExecutor for parallel processing
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_source = {
                executor.submit(self.scrape_source_comprehensive, source): source 
                for source in NEWS_SOURCES
            }
            
            for future in as_completed(future_to_source):
                source = future_to_source[future]
                try:
                    articles = future.result()
                    all_articles.extend(articles)
                    self.stats['sources_processed'] += 1
                    self.stats['articles_found'] += len(articles)
                    
                    logger.info(f"Completed {source['name']}: {len(articles)} articles")
                    
                    # Store articles immediately to avoid memory issues
                    self.store_articles_batch(articles)
                    
                except Exception as e:
                    logger.error(f"Error processing {source['name']}: {e}")
                    self.stats['errors'] += 1
        
        # Save summary data for GitLab artifacts
        self.save_scraping_summary(all_articles)
        
        logger.info(f"Scraping complete. Stats: {self.stats}")
        return all_articles
    
    def save_scraping_summary(self, articles):
        """Save scraping summary and sample data"""
        summary = {
            'scraping_timestamp': datetime.utcnow().isoformat(),
            'statistics': self.stats,
            'sample_articles': [
                {
                    'title': article['title'],
                    'source': article['source'],
                    'url': article['url'],
                    'word_count': article.get('word_count', 0),
                    'author': article.get('author', 'Unknown')
                }
                for article in articles[:10]  # Sample of first 10
            ],
            'sources_processed': [source['name'] for source in NEWS_SOURCES]
        }
        
        # Save summary
        with open('scraped_data/scraping_summary.json', 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        # Save full article data (limited for artifact size)
        limited_articles = [
            {
                'title': article['title'],
                'source': article['source'],
                'url': article['url'],
                'content_preview': article['content'][:500] + '...',
                'scraped_at': article['scraped_at']
            }
            for article in articles[:50]  # Limit for artifact size
        ]
        
        with open('scraped_data/articles_sample.json', 'w') as f:
            json.dump(limited_articles, f, indent=2, default=str)
        
        logger.info("Scraping summary saved to artifacts")

if __name__ == "__main__":
    scraper = EnhancedNewsScraper()
    scraper.run_comprehensive_scraping()
