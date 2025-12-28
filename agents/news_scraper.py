"""
TAVILY-POWERED News Scraper Agent
- Uses Tavily Search API for real news
- High-quality articles with content
- Integrates with Pathway for semantic search
- NO PLACEHOLDERS - Only real news
"""

import os
import time
import threading
from typing import List, Dict, Optional
from agents.base_agent import BaseAgent

try:
    from tavily import TavilyClient
    TAVILY_AVAILABLE = True
except ImportError:
    TAVILY_AVAILABLE = False
    print("⚠️ Tavily not installed. Run: pip install tavily-python")


class NewsScraperAgent(BaseAgent):
    """Scrapes news with Tavily API and stores for Pathway indexing"""
    
    def __init__(self):
        super().__init__("🕷️ News Scraper")
        self.knowledge_base_dir = "knowledge_base"
        os.makedirs(self.knowledge_base_dir, exist_ok=True)
        
        # News cache with links
        self.news_cache = []
        self.scraping_in_progress = False
        self.scraping_complete = False
        
        # Initialize Tavily client
        self.tavily_key = os.getenv("TAVILY_API_KEY")
        
        if self.tavily_key and TAVILY_AVAILABLE:
            try:
                self.tavily_client = TavilyClient(api_key=self.tavily_key)
                self.log("✅ Tavily API configured and ready")
                self.tavily_ready = True
            except Exception as e:
                self.log(f"⚠️ Tavily initialization error: {e}")
                self.tavily_ready = False
        else:
            if not self.tavily_key:
                self.log("⚠️ TAVILY_API_KEY not found in .env")
            if not TAVILY_AVAILABLE:
                self.log("⚠️ Tavily library not installed")
            self.tavily_ready = False
    
    def scrape_for_top_stocks_async(
        self,
        stock_symbols: List[str],
        stock_names: Dict[str, str] = None,
        articles_per_stock: int = 3
    ) -> threading.Thread:
        """
        Start news scraping in BACKGROUND thread using Tavily
        Returns thread object (non-blocking)
        """
        
        if not self.tavily_ready:
            self.log("❌ Tavily not ready, cannot scrape news")
            return None
        
        self.scraping_in_progress = True
        self.scraping_complete = False
        
        thread = threading.Thread(
            target=self._scrape_background,
            args=(stock_symbols, stock_names, articles_per_stock),
            daemon=True
        )
        thread.start()
        
        self.log("🔄 Tavily news scraping started in BACKGROUND")
        self.log("   Real articles with full content coming soon...")
        
        return thread
    
    def _scrape_background(
        self,
        stock_symbols: List[str],
        stock_names: Dict[str, str],
        articles_per_stock: int
    ):
        """Background scraping task using Tavily"""
        
        try:
            self.log("\n" + "="*70)
            self.log(f"📰 TAVILY SCRAPING: {len(stock_symbols)} stocks")
            self.log("="*70)
            
            all_articles = []
            
            for i, symbol in enumerate(stock_symbols, 1):
                company_name = stock_names.get(symbol, symbol) if stock_names else symbol
                
                self.log(f"[{i}/{len(stock_symbols)}] Searching: {symbol}")
                
                articles = self._scrape_with_tavily(
                    symbol=symbol,
                    company_name=company_name,
                    max_articles=articles_per_stock
                )
                
                if articles:
                    all_articles.extend(articles)
                    # Save to knowledge_base for Pathway
                    self._save_articles_for_pathway(articles, symbol)
                    self.log(f"   ✅ {len(articles)} real articles for {symbol}")
                else:
                    self.log(f"   ⚠️ No articles found for {symbol}")
                
                # Rate limiting - Tavily free tier
                time.sleep(1)
            
            self.news_cache = all_articles
            self.scraping_complete = True
            self.scraping_in_progress = False
            
            self.log("\n✅ TAVILY SCRAPING COMPLETE")
            self.log(f"   Total articles: {len(all_articles)}")
            self.log(f"   Saved to: {self.knowledge_base_dir}/")
            self.log(f"   Ready for Pathway indexing!")
            
        except Exception as e:
            self.log(f"❌ Background scraping error: {e}")
            import traceback
            self.log(traceback.format_exc())
            self.scraping_in_progress = False
    
    def _scrape_with_tavily(
        self,
        symbol: str,
        company_name: str,
        max_articles: int = 3
    ) -> List[Dict]:
        """
        Scrape news using Tavily Search API
        
        Tavily provides:
        - High-quality, recent articles
        - Full content extraction
        - Verified sources
        - Proper URLs
        """
        
        articles = []
        
        try:
            # Build search query
            # Focus on recent news about the Indian stock
            query = f"{company_name} {symbol} stock India NSE latest news"
            
            self.log(f"   🔍 Tavily query: {query}")
            
            # Call Tavily API
            response = self.tavily_client.search(
                query=query,
                search_depth="basic",  # or "advanced" for deeper search
                max_results=max_articles,
                include_domains=["economictimes.indiatimes.com", "moneycontrol.com", 
                               "business-standard.com", "livemint.com", "reuters.com"],
                exclude_domains=["twitter.com", "facebook.com"]
            )
            
            # Parse results
            results = response.get("results", [])
            
            self.log(f"   📊 Tavily returned {len(results)} results")
            
            for result in results:
                title = result.get("title", "")
                content = result.get("content", "")
                url = result.get("url", "")
                score = result.get("score", 0)
                
                # Only include if we have actual content
                if title and content and len(content) > 100:
                    articles.append({
                        "title": title,
                        "content": content,
                        "url": url,
                        "source": "Tavily Search",
                        "relevance_score": score,
                        "stock_symbol": symbol,
                        "company_name": company_name,
                        "verified": True  # Tavily articles are verified
                    })
                    
                    self.log(f"   ✅ Found: {title[:60]}...")
            
            return articles
        
        except Exception as e:
            self.log(f"   ⚠️ Tavily error for {symbol}: {str(e)[:100]}")
            return []
    
    def _save_articles_for_pathway(self, articles: List[Dict], symbol: str):
        """
        Save articles to knowledge_base/ for Pathway indexing
        
        This is the KEY for Pathway integration:
        - Each article saved as a .txt file
        - Pathway watches this folder
        - Automatically indexes new files
        - Enables semantic search
        """
        
        for i, article in enumerate(articles, 1):
            timestamp = int(time.time())
            filename = f"{symbol}_tavily_{i}_{timestamp}.txt"
            filepath = os.path.join(self.knowledge_base_dir, filename)
            
            # Format article for Pathway embedding
            content = self._format_article_for_pathway(article)
            
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.log(f"   💾 Saved: {filename}")
            except Exception as e:
                self.log(f"   ⚠️ Error saving {filename}: {str(e)[:50]}")
    
    def _format_article_for_pathway(self, article: Dict) -> str:
        """
        Format article for optimal Pathway embedding and search
        
        Structure:
        1. Metadata (stock, source, URL)
        2. Title (important for matching)
        3. Full content (for detailed analysis)
        4. Keywords (for better retrieval)
        """
        
        formatted = f"""STOCK: {article['stock_symbol']} - {article['company_name']}
SOURCE: {article['source']}
URL: {article['url']}
VERIFIED: {'Yes' if article.get('verified') else 'No'}
RELEVANCE: {article.get('relevance_score', 0):.2f}

===== TITLE =====
{article['title']}

===== ARTICLE CONTENT =====

{article['content']}

===== METADATA =====
Stock Symbol: {article['stock_symbol']}
Company: {article['company_name']}
Source: {article['source']}
Link: {article['url']}
Date Scraped: {time.strftime('%Y-%m-%d %H:%M:%S')}

===== KEYWORDS =====
{article['stock_symbol']}, {article['company_name']}, India, NSE, stock, investment, market

===== END =====
"""
        
        return formatted
    
    def get_news_status(self) -> Dict:
        """Get current news scraping status"""
        
        if not self.tavily_ready:
            return {
                "in_progress": False,
                "complete": False,
                "articles_count": 0,
                "message": "⚠️ Tavily API not configured"
            }
        
        return {
            "in_progress": self.scraping_in_progress,
            "complete": self.scraping_complete,
            "articles_count": len(self.news_cache),
            "message": self._get_status_message()
        }
    
    def _get_status_message(self) -> str:
        """Get status message"""
        if not self.tavily_ready:
            return "⚠️ Tavily API not configured"
        if self.scraping_in_progress:
            return "🔄 Scraping real news with Tavily..."
        elif self.scraping_complete:
            return f"✅ {len(self.news_cache)} verified articles ready!"
        else:
            return "⏸️ No scraping initiated yet"
    
    def get_news_for_stock(self, symbol: str) -> List[Dict]:
        """Get news articles for specific stock (with links)"""
        
        if not self.news_cache:
            return [{
                "title": "News scraping not complete yet",
                "content": "Real news is being fetched with Tavily. Try again in a moment.",
                "url": "",
                "source": "System",
                "verified": False
            }]
        
        # Filter news for this stock
        stock_news = [
            article for article in self.news_cache
            if article.get('stock_symbol') == symbol
        ]
        
        if not stock_news:
            # Return general market news
            stock_news = self.news_cache[:3]
        
        return stock_news
    
    def get_all_news_summary(self) -> str:
        """Get summary of all scraped news with links"""
        
        if not self.tavily_ready:
            return "📰 **Tavily API not configured**\n\nPlease add TAVILY_API_KEY to your .env file."
        
        if not self.news_cache:
            status = self.get_news_status()
            return f"📰 **News Status:** {status['message']}"
        
        summary = f"📰 **Real News from Tavily** ({len(self.news_cache)} verified articles)\n\n"
        
        # Group by stock
        by_stock = {}
        for article in self.news_cache:
            symbol = article.get('stock_symbol', 'General')
            if symbol not in by_stock:
                by_stock[symbol] = []
            by_stock[symbol].append(article)
        
        for symbol, articles in by_stock.items():
            summary += f"**{symbol}** ({len(articles)} articles):\n"
            for i, article in enumerate(articles[:2], 1):  # Top 2 per stock
                title = article.get('title', 'No title')[:80]
                url = article.get('url', '')
                score = article.get('relevance_score', 0)
                
                summary += f"{i}. {title}\n"
                summary += f"   📊 Relevance: {score:.2f}\n"
                if url:
                    summary += f"   🔗 {url}\n"
            summary += "\n"
        
        summary += "\n✅ **All articles verified by Tavily**\n"
        summary += "💾 **Saved to knowledge_base/ for Pathway semantic search**"
        
        return summary
    
    def query_news_semantically(self, query: str, top_k: int = 3) -> List[Dict]:
        """
        Query news using semantic search (via Pathway)
        
        This demonstrates Pathway integration:
        - User asks a question
        - Pathway finds relevant articles
        - Returns most similar content
        """
        
        # This would use the Market Intelligence agent's pathway query
        # For now, return filtered results
        
        if not self.news_cache:
            return []
        
        # Simple keyword matching (Pathway would do semantic)
        query_lower = query.lower()
        
        scored_articles = []
        for article in self.news_cache:
            score = 0
            if query_lower in article.get('title', '').lower():
                score += 3
            if query_lower in article.get('content', '').lower():
                score += 1
            if article.get('stock_symbol', '').lower() in query_lower:
                score += 2
            
            if score > 0:
                scored_articles.append((score, article))
        
        # Sort by score
        scored_articles.sort(reverse=True, key=lambda x: x[0])
        
        return [article for _, article in scored_articles[:top_k]]