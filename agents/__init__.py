"""
Agents Package
Multi-agent system for investment advisory
"""

from .base_agent import BaseAgent
from .user_profile_agent import UserProfileAgent  # New comprehensive agent
from .market_intelligence import MarketIntelligenceAgent
from .stock_selection import StockSelectionAgent
from .data_enrichment import DataEnrichmentAgent
from .recommendation import RecommendationAgent
from .news_scraper import NewsScraperAgent

# Keep old agent for backward compatibility
from .financial_analyzer import FinancialAnalyzerAgent

__all__ = [
    'BaseAgent',
    'UserProfileAgent',  # New primary agent
    'FinancialAnalyzerAgent',  # Deprecated but kept for compatibility
    'MarketIntelligenceAgent',
    'StockSelectionAgent',
    'DataEnrichmentAgent',
    'RecommendationAgent',
    'NewsScraperAgent',
]