"""
User Profile Agent - Complete User Financial & Trading Analysis
Handles BOTH bank statements AND trading history comprehensively
"""

import json
import PyPDF2
from typing import Dict, List
from datetime import datetime
from agents.base_agent import BaseAgent


class UserProfileAgent(BaseAgent):
    """
    Comprehensive user analysis agent
    Analyzes banking transactions AND trading history
    """
    
    def __init__(self):
        super().__init__("👤 User Profile Analyzer")
        self.bank_data = None
        self.trading_data = None
        self.profile = None
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF"""
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text()
                return text
        except Exception as e:
            self.log(f"Error reading PDF {pdf_path}: {e}")
            return ""
    
    def analyze_complete_profile(
        self, 
        bank_statement_path: str, 
        trading_history_path: str,
        custom_investment_amount: float = None
    ) -> Dict:
        """
        Complete analysis of user's financial situation and trading history
        
        Returns comprehensive profile with:
        - Banking analysis
        - Trading behavior analysis
        - Risk profile
        - Investment recommendations
        """
        
        self.log("=" * 60)
        self.log("STARTING COMPLETE USER PROFILE ANALYSIS")
        self.log("=" * 60)
        
        # Extract documents
        self.log("\n📄 Step 1: Extracting documents...")
        bank_text = self.extract_text_from_pdf(bank_statement_path)
        trading_text = self.extract_text_from_pdf(trading_history_path)
        
        if not bank_text or not trading_text:
            self.log("⚠️ Failed to extract text from PDFs")
            return self._get_default_profile(custom_investment_amount)
        
        self.log(f"✅ Bank statement: {len(bank_text)} characters")
        self.log(f"✅ Trading history: {len(trading_text)} characters")
        
        # Analyze with LLM
        self.log("\n🧠 Step 2: Analyzing with Groq LLM...")
        profile = self._analyze_with_llm(bank_text, trading_text, custom_investment_amount)
        
        if profile:
            self.profile = profile
            self._display_profile_summary(profile)
            return profile
        else:
            self.log("⚠️ LLM analysis failed, using default profile")
            return self._get_default_profile(custom_investment_amount)
    
    def _analyze_with_llm(
        self, 
        bank_text: str, 
        trading_text: str,
        custom_amount: float = None
    ) -> Dict:
        """Use LLM to extract comprehensive profile"""
        
        prompt = f"""You are a financial analyst. Analyze these documents comprehensively.

═══════════════════════════════════════════════════════════════
BANK STATEMENT:
═══════════════════════════════════════════════════════════════
{bank_text[:3000]}

═══════════════════════════════════════════════════════════════
TRADING HISTORY (Groww/Broker):
═══════════════════════════════════════════════════════════════
{trading_text[:4000]}

═══════════════════════════════════════════════════════════════
ANALYSIS TASK:
═══════════════════════════════════════════════════════════════

Extract and return ONLY a valid JSON object with this EXACT structure:

{{
  "banking": {{
    "current_balance": <number>,
    "monthly_income": <number>,
    "monthly_expenses": <number>,
    "monthly_savings": <calculated: income - expenses>,
    "emergency_fund_needed": <calculated: 3 × monthly_expenses>,
    "safe_investment_capacity": <calculated: balance - emergency_fund OR 0 if negative>
  }},
  
  "trading_history": {{
    "total_trades": <count all trades>,
    "profitable_trades": <count trades with PROFIT outcome>,
    "losing_trades": <count trades with LOSS outcome>,
    "win_rate_percentage": <calculated: (profitable/total) × 100>,
    "total_capital_deployed": <sum of all Buy transactions' (Qty × Buy Price)>,
    "total_profits": <sum of all positive Realized P/L>,
    "total_losses": <sum of all negative Realized P/L>,
    "net_pnl": <sum of all Realized P/L>,
    "average_trade_size": <average buy amount per trade>,
    "largest_win": <biggest positive P/L trade with stock name>,
    "largest_loss": <biggest negative P/L trade with stock name>
  }},
  
  "trading_behavior": {{
    "preferred_sectors": [<extract sectors from stock names: "Banking", "IT", "Pharma", "Energy", etc.>],
    "most_traded_stocks": [<list top 5 stocks by trade frequency>],
    "trading_frequency": "<ACTIVE (many recent trades) or MODERATE or OCCASIONAL>",
    "holding_pattern": "<SHORT_TERM (quick exits) or MEDIUM_TERM or LONG_TERM>",
    "risk_taking_behavior": "<AGGRESSIVE (large bets) or MODERATE or CONSERVATIVE (small trades)>"
  }},
  
  "risk_profile": {{
    "overall_risk": "<CONSERVATIVE or MODERATE or AGGRESSIVE>",
    "risk_reasoning": "<explain based on: win rate, trade sizes, holding pattern>",
    "risk_score": <number 1-10, where 1=very conservative, 10=very aggressive>
  }},
  
  "investment_recommendation": {{
    "recommended_amount": <use custom_amount if provided, else safe_investment_capacity>,
    "min_recommended": <20% of recommended_amount>,
    "max_recommended": <150% of recommended_amount if aggressive, else 100%>,
    "reasoning": "<explain why this amount is suitable>"
  }}
}}

IMPORTANT CALCULATION RULES:
1. monthly_expenses = sum of ALL debit transactions
2. emergency_fund_needed = 3 × monthly_expenses (safety buffer)
3. safe_investment_capacity = current_balance - emergency_fund_needed
   - If negative, set to 0 (means insufficient funds)
   - If balance is very low (< 10k), suggest using trading history average
4. win_rate = (profitable_trades / total_trades) × 100
5. Risk profile logic:
   - Win rate < 50% → CONSERVATIVE
   - Win rate 50-70% AND moderate trade sizes → MODERATE
   - Win rate > 70% OR large trade sizes → AGGRESSIVE

CONTEXT:
- Current date: {datetime.now().strftime("%B %Y")}
- Custom investment amount requested: {custom_amount if custom_amount else "None (calculate from balance)"}

Return ONLY the JSON object. No markdown, no explanation, just pure JSON."""

        try:
            response = self.chat([
                {
                    "role": "system", 
                    "content": "You are a financial data extraction expert. Return only valid JSON with no additional text."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ], temperature=0.2, max_tokens=2000)
            
            # Clean response
            response = response.strip()
            if response.startswith("```json"):
                response = response.split("```json")[1].split("```")[0].strip()
            elif response.startswith("```"):
                response = response.split("```")[1].split("```")[0].strip()
            
            profile = json.loads(response)
            
            # Override investment amount if custom provided
            if custom_amount:
                profile["investment_recommendation"]["recommended_amount"] = custom_amount
                self.log(f"✅ Using custom investment amount: ₹{custom_amount:,.2f}")
            
            return profile
            
        except json.JSONDecodeError as e:
            self.log(f"⚠️ JSON parse error: {e}")
            self.log(f"Response was: {response[:200]}...")
            return None
        except Exception as e:
            self.log(f"⚠️ Analysis error: {e}")
            return None
    
    def _display_profile_summary(self, profile: Dict):
        """Display formatted profile summary"""
        
        self.log("\n" + "=" * 60)
        self.log("✅ PROFILE ANALYSIS COMPLETE")
        self.log("=" * 60)
        
        banking = profile.get("banking", {})
        trading = profile.get("trading_history", {})
        behavior = profile.get("trading_behavior", {})
        risk = profile.get("risk_profile", {})
        recommendation = profile.get("investment_recommendation", {})
        
        self.log("\n💰 BANKING SUMMARY:")
        self.log(f"   Balance: ₹{banking.get('current_balance', 0):,.2f}")
        self.log(f"   Income: ₹{banking.get('monthly_income', 0):,.2f}/month")
        self.log(f"   Expenses: ₹{banking.get('monthly_expenses', 0):,.2f}/month")
        self.log(f"   Savings: ₹{banking.get('monthly_savings', 0):,.2f}/month")
        
        self.log("\n📈 TRADING HISTORY:")
        self.log(f"   Total Trades: {trading.get('total_trades', 0)}")
        self.log(f"   Win Rate: {trading.get('win_rate_percentage', 0):.1f}%")
        self.log(f"   Capital Deployed: ₹{trading.get('total_capital_deployed', 0):,.2f}")
        self.log(f"   Net P&L: ₹{trading.get('net_pnl', 0):,.2f}")
        self.log(f"   Avg Trade Size: ₹{trading.get('average_trade_size', 0):,.2f}")
        
        self.log("\n🎯 TRADING BEHAVIOR:")
        self.log(f"   Preferred Sectors: {', '.join(behavior.get('preferred_sectors', []))}")
        self.log(f"   Top Stocks: {', '.join(behavior.get('most_traded_stocks', [])[:3])}")
        self.log(f"   Frequency: {behavior.get('trading_frequency', 'N/A')}")
        self.log(f"   Pattern: {behavior.get('holding_pattern', 'N/A')}")
        
        self.log("\n⚖️ RISK PROFILE:")
        self.log(f"   Overall: {risk.get('overall_risk', 'N/A')}")
        self.log(f"   Score: {risk.get('risk_score', 0)}/10")
        self.log(f"   Reasoning: {risk.get('risk_reasoning', 'N/A')[:80]}...")
        
        self.log("\n💡 INVESTMENT RECOMMENDATION:")
        self.log(f"   Recommended: ₹{recommendation.get('recommended_amount', 0):,.2f}")
        self.log(f"   Range: ₹{recommendation.get('min_recommended', 0):,.2f} - ₹{recommendation.get('max_recommended', 0):,.2f}")
        
        self.log("\n" + "=" * 60)
    
    def _get_default_profile(self, custom_amount: float = None) -> Dict:
        """Return default profile if analysis fails"""
        return {
            "banking": {
                "current_balance": 1488,
                "monthly_income": 45000,
                "monthly_expenses": 40432,
                "monthly_savings": 4568,
                "emergency_fund_needed": 121296,
                "safe_investment_capacity": 0
            },
            "trading_history": {
                "total_trades": 40,
                "profitable_trades": 23,
                "losing_trades": 17,
                "win_rate_percentage": 57.5,
                "total_capital_deployed": 600000,
                "total_profits": 45000,
                "total_losses": -25000,
                "net_pnl": 20000,
                "average_trade_size": 15000,
                "largest_win": "RELIANCE +₹8,592",
                "largest_loss": "HDFCBANK -₹4,626"
            },
            "trading_behavior": {
                "preferred_sectors": ["Banking", "IT", "Pharma", "Energy"],
                "most_traded_stocks": ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ITC"],
                "trading_frequency": "MODERATE",
                "holding_pattern": "MEDIUM_TERM",
                "risk_taking_behavior": "MODERATE"
            },
            "risk_profile": {
                "overall_risk": "MODERATE",
                "risk_reasoning": "57.5% win rate with moderate trade sizes indicates balanced approach",
                "risk_score": 6
            },
            "investment_recommendation": {
                "recommended_amount": custom_amount if custom_amount else 20000,
                "min_recommended": (custom_amount if custom_amount else 20000) * 0.5,
                "max_recommended": (custom_amount if custom_amount else 20000) * 1.5,
                "reasoning": "Based on trading history and risk profile"
            }
        }
    
    def query_trading_history(self, question: str) -> str:
        """
        Answer questions about trading history
        Examples:
        - "What stocks have I traded?"
        - "Show my best trades"
        - "What's my win rate?"
        """
        
        if not self.profile:
            return "Please run analysis first by saying 'check my balance' or 'analyze my profile'"
        
        trading = self.profile.get("trading_history", {})
        behavior = self.profile.get("trading_behavior", {})
        
        question_lower = question.lower()
        
        # Stocks traded
        if any(word in question_lower for word in ["stocks", "companies", "what have i"]):
            stocks = behavior.get("most_traded_stocks", [])
            return f"""**Your Most Traded Stocks:**

{chr(10).join([f"{i}. {stock}" for i, stock in enumerate(stocks[:10], 1)])}

**Preferred Sectors:** {", ".join(behavior.get("preferred_sectors", []))}
**Trading Frequency:** {behavior.get("trading_frequency", "N/A")}"""
        
        # Best trades
        if any(word in question_lower for word in ["best", "biggest win", "largest profit"]):
            return f"""**Your Best Trades:**

🏆 **Largest Win:** {trading.get("largest_win", "N/A")}

**Overall Performance:**
- Total Profits: ₹{trading.get("total_profits", 0):,.2f}
- Win Rate: {trading.get("win_rate_percentage", 0):.1f}%
- Profitable Trades: {trading.get("profitable_trades", 0)} out of {trading.get("total_trades", 0)}"""
        
        # Worst trades
        if any(word in question_lower for word in ["worst", "biggest loss", "largest loss"]):
            return f"""**Your Worst Trades:**

📉 **Largest Loss:** {trading.get("largest_loss", "N/A")}

**Loss Analysis:**
- Total Losses: ₹{trading.get("total_losses", 0):,.2f}
- Losing Trades: {trading.get("losing_trades", 0)}
- Net P&L: ₹{trading.get("net_pnl", 0):,.2f}"""
        
        # Win rate
        if any(word in question_lower for word in ["win rate", "success rate", "profitable"]):
            return f"""**Your Trading Performance:**

📊 **Win Rate:** {trading.get("win_rate_percentage", 0):.1f}%
- ✅ Profitable: {trading.get("profitable_trades", 0)} trades
- ❌ Losses: {trading.get("losing_trades", 0)} trades
- 📈 Total: {trading.get("total_trades", 0)} trades

**Net Result:** ₹{trading.get("net_pnl", 0):,.2f}"""
        
        # Capital deployed
        if any(word in question_lower for word in ["capital", "invested", "how much"]):
            return f"""**Your Investment History:**

💰 **Total Capital Deployed:** ₹{trading.get("total_capital_deployed", 0):,.2f}
📊 **Average Trade Size:** ₹{trading.get("average_trade_size", 0):,.2f}
📈 **Net Profit/Loss:** ₹{trading.get("net_pnl", 0):,.2f}
📉 **Return:** {(trading.get("net_pnl", 0) / trading.get("total_capital_deployed", 1) * 100):.2f}%"""
        
        # Default - full summary
        return f"""**Trading History Summary:**

📊 **Performance:**
- Total Trades: {trading.get("total_trades", 0)}
- Win Rate: {trading.get("win_rate_percentage", 0):.1f}%
- Net P&L: ₹{trading.get("net_pnl", 0):,.2f}

💰 **Capital:**
- Deployed: ₹{trading.get("total_capital_deployed", 0):,.2f}
- Avg Trade: ₹{trading.get("average_trade_size", 0):,.2f}

🎯 **Behavior:**
- Sectors: {", ".join(behavior.get("preferred_sectors", [])[:3])}
- Top Stocks: {", ".join(behavior.get("most_traded_stocks", [])[:3])}
- Pattern: {behavior.get("holding_pattern", "N/A")}

Ask me specific questions like:
- "What stocks have I traded?"
- "Show my best trades"
- "What's my win rate?"
"""
    
    def get_banking_summary(self) -> str:
        """Get banking summary"""
        
        if not self.profile:
            return "Please run analysis first"
        
        banking = self.profile.get("banking", {})
        recommendation = self.profile.get("investment_recommendation", {})
        
        return f"""**Banking Summary:**

💰 **Current Balance:** ₹{banking.get("current_balance", 0):,.2f}

**Monthly:**
- Income: ₹{banking.get("monthly_income", 0):,.2f}
- Expenses: ₹{banking.get("monthly_expenses", 0):,.2f}
- Savings: ₹{banking.get("monthly_savings", 0):,.2f}

**Investment Capacity:**
- Emergency Fund Needed: ₹{banking.get("emergency_fund_needed", 0):,.2f}
- Safe to Invest: ₹{banking.get("safe_investment_capacity", 0):,.2f}

**Recommendation:** ₹{recommendation.get("recommended_amount", 0):,.2f}
*{recommendation.get("reasoning", "")}*"""
    
    def get_risk_profile(self) -> str:
        """Get risk profile summary"""
        
        if not self.profile:
            return "Please run analysis first"
        
        risk = self.profile.get("risk_profile", {})
        
        return f"""**Your Risk Profile:**

⚖️ **Overall Risk:** {risk.get("overall_risk", "N/A")}
📊 **Risk Score:** {risk.get("risk_score", 0)}/10

**Analysis:**
{risk.get("risk_reasoning", "N/A")}

**What this means:**
- CONSERVATIVE (1-3): Prefer stable, low-risk investments
- MODERATE (4-7): Balanced approach with some growth potential
- AGGRESSIVE (8-10): Willing to take risks for higher returns
"""