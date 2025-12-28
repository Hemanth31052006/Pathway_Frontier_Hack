"""
Agent 3: IMPROVED Stock Selection Agent
Market cap selection based on investment amount
"""

import pandas as pd
from typing import Dict, List
from agents.base_agent import BaseAgent


class StockSelectionAgent(BaseAgent):
    """Selects stocks based on investment amount and market cap"""
    
    def __init__(self):
        super().__init__("🎯 Stock Selection")
        self.stock_universe = None
    
    def load_stocks(self, csv_path: str):
        """Load stock universe from CSV"""
        try:
            self.log(f"Loading stocks from {csv_path}...")
            self.stock_universe = pd.read_csv(csv_path)
            self.log(f"✅ Loaded {len(self.stock_universe)} stocks")
            self.log(f"   Columns: {', '.join(self.stock_universe.columns.tolist())}")
        except Exception as e:
            self.log(f"❌ Error loading stocks: {e}")
            raise
    
    def determine_market_cap_category(self, amount: float) -> List[str]:
        """
        Determine which market cap categories to invest in based on amount
        
        LOGIC:
        - < ₹10,000: Small cap only (affordable stocks)
        - ₹10,000 - ₹50,000: Small + Mid cap (diversification possible)
        - > ₹50,000: All caps (full diversification)
        
        Args:
            amount: Investment amount in INR
        
        Returns:
            List of market cap categories ['large', 'mid', 'small']
        """
        
        if amount < 10000:
            caps = ["small"]
            reason = "Small amount - focusing on affordable small cap stocks"
        elif amount < 50000:
            caps = ["small", "mid"]
            reason = "Moderate amount - small & mid caps for better diversification"
        else:
            caps = ["large", "mid", "small"]
            reason = "Large amount - all market caps for full diversification"
        
        self.log(f"💰 Investment Amount: ₹{amount:,.2f}")
        self.log(f"🎯 Market Cap Strategy: {', '.join([c.upper() for c in caps])}")
        self.log(f"📝 Reasoning: {reason}")
        
        return caps
    
    def shortlist_by_market_cap(
        self,
        amount: float,
        count: int = 30
    ) -> pd.DataFrame:
        """
        Shortlist stocks based on investment amount and market cap
        
        Args:
            amount: Investment amount
            count: Number of stocks to shortlist
        
        Returns:
            DataFrame of shortlisted stocks
        """
        
        if self.stock_universe is None:
            raise ValueError("Stock universe not loaded. Call load_stocks() first.")
        
        self.log(f"🔍 Shortlisting {count} stocks for ₹{amount:,.2f}...")
        
        # Determine market cap categories
        caps = self.determine_market_cap_category(amount)
        
        df = self.stock_universe.copy()
        
        # Build filter based on market cap categories
        filters = []
        
        if "large" in caps:
            if "in_nifty50" in df.columns:
                filters.append(df["in_nifty50"] == True)
            if "in_nifty100" in df.columns:
                filters.append(df["in_nifty100"] == True)
        
        if "mid" in caps:
            if "in_midcap100" in df.columns:
                filters.append(df["in_midcap100"] == True)
        
        if "small" in caps:
            if "in_smallcap100" in df.columns:
                filters.append(df["in_smallcap100"] == True)
        
        # Apply filters (OR logic - stock belongs to any of the categories)
        if filters:
            combined_filter = filters[0]
            for f in filters[1:]:
                combined_filter = combined_filter | f
            
            filtered = df[combined_filter]
        else:
            # Fallback: use all stocks
            filtered = df
        
        self.log(f"   ✅ After market cap filter: {len(filtered)} stocks")
        
        # Remove duplicates by company name if available
        if 'company_name' in filtered.columns:
            filtered = filtered.drop_duplicates(subset=['company_name'], keep='first')
            self.log(f"   ✅ After deduplication: {len(filtered)} unique companies")
        
        # Take top N stocks
        if len(filtered) > count:
            shortlisted = filtered.head(count)
        else:
            shortlisted = filtered
        
        self.log(f"✅ Shortlisted {len(shortlisted)} stocks")
        
        # Log market cap distribution
        cap_dist = {}
        for cap in ['in_nifty50', 'in_nifty100', 'in_midcap100', 'in_smallcap100']:
            if cap in shortlisted.columns:
                cap_count = shortlisted[cap].sum()
                if cap_count > 0:
                    cap_name = cap.replace('in_', '').replace('_', ' ').title()
                    cap_dist[cap_name] = int(cap_count)
        
        if cap_dist:
            self.log("   📊 Market Cap Distribution:")
            for cap_name, cap_count in cap_dist.items():
                self.log(f"      - {cap_name}: {cap_count} stocks")
        
        return shortlisted.reset_index(drop=True)
    
    def filter_by_price_range(
        self,
        stocks_df: pd.DataFrame,
        amount: float,
        min_stocks: int = 5,
        max_stocks: int = 10
    ) -> pd.DataFrame:
        """
        Filter stocks that fit the investment amount
        (To be called AFTER getting Yahoo Finance prices)
        
        Strategy:
        - For small amounts: prefer stocks priced ₹100-₹500
        - For medium amounts: prefer stocks priced ₹200-₹2000
        - For large amounts: any price range
        
        Args:
            stocks_df: DataFrame with 'current_price' column
            amount: Investment amount
            min_stocks: Minimum stocks to return
            max_stocks: Maximum stocks to return
        
        Returns:
            Filtered DataFrame
        """
        
        if 'current_price' not in stocks_df.columns:
            self.log("⚠️ No price data available, returning all stocks")
            return stocks_df.head(max_stocks)
        
        # Remove stocks with no price
        priced = stocks_df[stocks_df['current_price'] > 0].copy()
        
        if len(priced) == 0:
            self.log("⚠️ No stocks with valid prices")
            return stocks_df.head(max_stocks)
        
        # Determine price range preference
        if amount < 10000:
            # Small amount: prefer affordable stocks
            price_min, price_max = 50, 500
            reason = "Affordable stocks (₹50-₹500) for small amount"
        elif amount < 50000:
            # Medium amount: mid-range stocks
            price_min, price_max = 100, 2000
            reason = "Mid-range stocks (₹100-₹2,000) for medium amount"
        else:
            # Large amount: any price
            price_min, price_max = 0, float('inf')
            reason = "All price ranges for large amount"
        
        # Filter by price range
        in_range = priced[
            (priced['current_price'] >= price_min) &
            (priced['current_price'] <= price_max)
        ]
        
        self.log(f"💰 Price Filter: {reason}")
        self.log(f"   ✅ {len(in_range)} stocks in range ₹{price_min}-₹{price_max}")
        
        # If not enough stocks in range, relax filter
        if len(in_range) < min_stocks:
            self.log(f"   ⚠️ Not enough stocks, using all priced stocks")
            in_range = priced
        
        # Sort by affordability (lower price first for small amounts)
        if amount < 10000:
            in_range = in_range.sort_values('current_price', ascending=True)
        else:
            # For larger amounts, prefer mid-priced stocks
            in_range['price_score'] = (in_range['current_price'] - price_min).abs()
            in_range = in_range.sort_values('price_score', ascending=True)
        
        # Return top stocks
        result = in_range.head(max_stocks)
        
        self.log(f"✅ Selected {len(result)} stocks for investment")
        self.log(f"   Price range: ₹{result['current_price'].min():.2f} - ₹{result['current_price'].max():.2f}")
        
        return result
    
    def get_selection_summary(self, stocks_df: pd.DataFrame, amount: float) -> Dict:
        """Get summary of stock selection"""
        
        if stocks_df.empty:
            return {
                "total_stocks": 0,
                "amount": amount,
                "strategy": "No stocks selected"
            }
        
        summary = {
            "total_stocks": len(stocks_df),
            "amount": amount,
            "market_caps": self.determine_market_cap_category(amount),
            "symbols": stocks_df['symbol'].tolist() if 'symbol' in stocks_df.columns else []
        }
        
        if 'current_price' in stocks_df.columns:
            summary["price_range"] = {
                "min": float(stocks_df['current_price'].min()),
                "max": float(stocks_df['current_price'].max()),
                "avg": float(stocks_df['current_price'].mean())
            }
        
        return summary