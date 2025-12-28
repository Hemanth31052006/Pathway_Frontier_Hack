"""
FIXED Recommendation Engine
- Uses ACTUAL selected stocks (not made-up ones)
- Proper formatting with real data
- Clear allocation breakdown
"""

import pandas as pd
from typing import Dict, List
from agents.base_agent import BaseAgent


class RecommendationAgent(BaseAgent):
    """Generates final investment recommendations using ACTUAL stocks"""
    
    def __init__(self):
        super().__init__("💡 Recommendation Engine")
    
    def generate(
        self, 
        user_profile: Dict, 
        stock_data: pd.DataFrame,
        insights: List[str]
    ) -> str:
        """
        Generate personalized investment recommendations using ACTUAL stocks
        """
        
        self.log("Generating personalized recommendations with Groq LLM...")
        
        amount = user_profile["investment_capacity"]
        risk = user_profile["risk_profile"]
        
        # Filter stocks with shares > 0
        if not stock_data.empty:
            investable_stocks = stock_data[stock_data['shares_to_buy'] > 0].copy()
            
            if investable_stocks.empty:
                self.log("⚠️ No stocks with shares > 0, using all stocks")
                investable_stocks = stock_data.copy()
            
            # Create detailed stock list for LLM
            stock_details = []
            for _, row in investable_stocks.iterrows():
                details = (
                    f"- {row['symbol']} ({row.get('company', row['symbol'])})\n"
                    f"  Price: ₹{row['current_price']:.2f}\n"
                    f"  Shares: {row['shares_to_buy']:.2f}\n"
                    f"  Investment: ₹{row['actual_investment']:.2f}\n"
                    f"  Allocation: {row['allocation_percentage']:.1f}%\n"
                    f"  Sector: {row.get('sector', 'N/A')}\n"
                    f"  Risk: {row.get('risk_level', 'N/A')}\n"
                    f"  Quality Score: {row.get('quality_score', 0):.1f}/100\n"
                    f"  Popularity: {row.get('popularity_score', 0):.1f}/100"
                )
                stock_details.append(details)
            
            stock_summary = "\n\n".join(stock_details)
            total_invested = investable_stocks['actual_investment'].sum()
        else:
            stock_summary = "No stock data available"
            investable_stocks = stock_data
            total_invested = 0
        
        # Prepare insights
        insights_text = "\n".join([f"• {ins[:200]}" for ins in insights])
        
        # Build prompt - FORCE LLM to use these exact stocks
        prompt = f"""You are an expert investment advisor. Create a detailed, personalized investment plan.

═══════════════════════════════════════════════════════════════
USER PROFILE
═══════════════════════════════════════════════════════════════
💰 Investment Amount: ₹{amount:,.0f}
📊 Risk Profile: {risk}
💵 Monthly Income: ₹{user_profile['monthly_income']:,.0f}
📉 Past Win Rate: {user_profile['profit_loss_ratio']:.1f}%
🎯 Total Trades: {user_profile['total_trades']}
🏆 Profitable Trades: {user_profile['profitable_trades']}
💼 Avg Trade Size: ₹{user_profile['avg_trade_size']:,.0f}
🏢 Preferred Sectors: {', '.join(user_profile['preferred_sectors'])}

═══════════════════════════════════════════════════════════════
SELECTED STOCKS (YOU MUST USE THESE EXACT STOCKS)
═══════════════════════════════════════════════════════════════
Total Allocated: ₹{total_invested:,.2f} / ₹{amount:,.0f}

{stock_summary}

═══════════════════════════════════════════════════════════════
MARKET INSIGHTS
═══════════════════════════════════════════════════════════════
{insights_text}

═══════════════════════════════════════════════════════════════
YOUR TASK - CRITICAL INSTRUCTIONS
═══════════════════════════════════════════════════════════════

**YOU MUST USE ONLY THE STOCKS LISTED ABOVE. DO NOT SUGGEST ANY OTHER STOCKS.**

Create a detailed investment plan with the following structure:

## 📊 Portfolio Overview

Provide a summary of the total investment and allocation strategy.

## 🎯 Stock-by-Stock Breakdown

**IMPORTANT: Use ONLY the stocks listed above. For EACH stock, provide:**

### 1. [Stock Symbol] - [Company Name]
- **Current Price**: ₹[from data above]
- **Shares to Buy**: [exact number from data above]
- **Total Investment**: ₹[exact amount from data above]
- **Portfolio %**: [percentage from data above]
- **Sector**: [from data above]
- **Why This Stock**: 2-3 sentences explaining why this stock fits the user's profile
- **Risk Level**: [from data above]
- **Expected Holding Period**: [Your recommendation: Short/Medium/Long term]

**REPEAT THIS FORMAT FOR EVERY STOCK IN THE LIST ABOVE**

## 📈 Entry Strategy

- Recommended entry approach (lump sum vs SIP-style)
- Timing considerations
- Key price levels to watch

## ⚠️ Risk Management

- Stop-loss recommendations (as % below purchase price)
- Portfolio rebalancing triggers
- What to do if market corrects

## 📅 Review & Monitoring

- Review frequency recommendation
- Key metrics to track for each stock
- When to book profits or exit

═══════════════════════════════════════════════════════════════
CRITICAL RULES
═══════════════════════════════════════════════════════════════

1. **USE ONLY THE STOCKS LISTED ABOVE** - Do not add HDFC, Infosys, or any other stocks
2. **USE EXACT NUMBERS** - Shares, prices, and amounts must match the data above
3. **EXPLAIN EACH STOCK** - Why it fits this user's profile and risk level
4. **BE SPECIFIC** - Use the actual sector, quality, and popularity data provided
5. **MATCH RISK PROFILE** - Align recommendations with {risk} risk tolerance

Generate the complete investment plan now:"""

        try:
            response = self.chat([
                {
                    "role": "system", 
                    "content": "You are a professional investment advisor. You MUST use only the stocks provided in the user's message. Do not suggest any stocks that are not in the provided list. Be specific and use exact numbers from the data."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ], temperature=0.5, max_tokens=4000)
            
            self.log("✅ Recommendations generated successfully")
            self.log(f"   Response length: {len(response)} characters")
            
            # Add summary at the end
            summary = f"""

---

## 💰 Investment Summary

- **Total Amount**: ₹{amount:,.2f}
- **Total Allocated**: ₹{total_invested:,.2f}
- **Utilization**: {(total_invested/amount)*100:.1f}%
- **Number of Stocks**: {len(investable_stocks)}
- **Risk Profile**: {risk}

**All prices and allocations are based on current Yahoo Finance data.**
"""
            
            return response + summary
            
        except Exception as e:
            self.log(f"❌ Error generating recommendations: {e}")
            return self._get_fallback_recommendation(user_profile, investable_stocks)
    
    def _get_fallback_recommendation(
        self, 
        user_profile: Dict, 
        stock_data: pd.DataFrame
    ) -> str:
        """Generate basic fallback recommendation if LLM fails"""
        
        amount = user_profile["investment_capacity"]
        risk = user_profile["risk_profile"]
        
        recommendation = f"""
# Investment Recommendation

## Summary
- **Investment Amount**: ₹{amount:,.0f}
- **Risk Profile**: {risk}
- **Strategy**: Diversified portfolio approach

## Selected Stocks

"""
        
        if not stock_data.empty:
            for _, row in stock_data.iterrows():
                if row['shares_to_buy'] > 0:
                    recommendation += f"""
### {row['symbol']} - {row.get('company', row['symbol'])}
- **Price**: ₹{row['current_price']:.2f}
- **Shares**: {row['shares_to_buy']:.2f}
- **Investment**: ₹{row['actual_investment']:.2f}
- **Allocation**: {row['allocation_percentage']:.1f}%
- **Sector**: {row.get('sector', 'N/A')}
- **Risk**: {row.get('risk_level', 'N/A')}

"""
        else:
            recommendation += "No stock data available.\n"
        
        recommendation += """
## Next Steps
1. Review the stock list above
2. Consider your risk tolerance
3. Start with small positions
4. Monitor regularly

**Note**: This is a basic template. For detailed recommendations, please try again.
"""
        return recommendation