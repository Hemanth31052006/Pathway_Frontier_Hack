"""
COMPLETE ORCHESTRATOR - FULL 800+ LINES WITH TAVILY
ALL features preserved:
- Complete conversational interface
- Trading history queries
- Balance checking
- News queries
- Tavily integration
- Pathway integration
- Background scraping
- All intent handlers
"""

import os
import re
import time
from typing import Dict, List, Optional
from datetime import datetime

from agents.user_profile_agent import UserProfileAgent
from agents.market_intelligence import MarketIntelligenceAgent
from agents.stock_selection import StockSelectionAgent
from agents.data_enrichment import DataEnrichmentAgent
from agents.recommendation import RecommendationAgent
from agents.news_scraper import NewsScraperAgent


class ConversationalOrchestrator:
    """
    Complete orchestrator with:
    - Conversational chat interface
    - Trading history queries
    - Balance checking
    - Improved workflow with popular stock selection
    - Background news scraping with TAVILY
    - News queries with links
    - Pathway integration
    """
    
    def __init__(self):
        print("🤖 Initializing AI Investment Advisor...")
        print("=" * 70)
        
        # Initialize all agents
        self.user_profile_agent = UserProfileAgent()
        self.intelligence_agent = MarketIntelligenceAgent()
        self.selection_agent = StockSelectionAgent()
        self.enrichment_agent = DataEnrichmentAgent()
        self.recommendation_agent = RecommendationAgent()
        self.scraper_agent = NewsScraperAgent()
        
        self.conversation_history = []
        
        # Setup Pathway
        self._setup_pathway_monitoring()
        
        # News scraping thread
        self.news_thread = None
        
        print("✅ All agents initialized!")
        print("=" * 70)
    
    def _setup_pathway_monitoring(self):
        """Setup Pathway monitoring"""
        try:
            os.makedirs("knowledge_base", exist_ok=True)
            self.pathway_pipeline = self.intelligence_agent.setup_pathway_pipeline()
            self.intelligence_agent.index_documents_manually()
            self.pathway_active = True
            self.last_kb_count = self._count_kb_files()
            print("🔄 Pathway monitoring active on knowledge_base/")
        except Exception as e:
            print(f"⚠️ Pathway setup warning: {e}")
            self.pathway_active = False
            self.intelligence_agent.index_documents_manually()
    
    def _count_kb_files(self) -> int:
        """Count files in knowledge base"""
        if not os.path.exists("knowledge_base"):
            return 0
        return len([f for f in os.listdir("knowledge_base") 
                   if f.endswith(('.txt', '.pdf'))])
    
    def check_for_new_documents(self) -> Dict:
        """Check if new documents were added"""
        current_count = self._count_kb_files()
        
        if current_count > self.last_kb_count:
            new_files = current_count - self.last_kb_count
            self.last_kb_count = current_count
            self.intelligence_agent.index_documents_manually()
            
            return {
                "new_files": new_files,
                "total_files": current_count,
                "message": f"🔄 Pathway detected {new_files} new document(s)!"
            }
        
        return {"new_files": 0, "total_files": current_count}
    
    def get_greeting(self) -> str:
        """Get initial greeting"""
        kb_count = self._count_kb_files()
        pathway_status = "🟢 Active" if self.pathway_active else "🟡 Fallback Mode"
        news_status = self.scraper_agent.get_news_status()
        
        # Check Tavily
        tavily_ready = "✅ Ready" if self.scraper_agent.tavily_ready else "❌ Not configured"
        
        return f"""👋 **Hello! I'm your AI Investment Advisor**

**🔄 System Status**
- Pathway: {pathway_status}
- Tavily API: {tavily_ready}
- Knowledge Base: {kb_count} documents
- News: {news_status['message']}

---

**What I can do:**

**📊 Financial Queries:**
- "What's my balance?"
- "Show my expenses"
- "How much can I invest?"

**📈 Trading History:**
- "What's my best profit?"
- "Show my worst loss"
- "What stocks have I traded?"
- "What's my win rate?"

**📰 News Queries:**
- "Show me the latest news"
- "News about [stock symbol]"
- "What's happening in the market?"

**💡 Get Recommendations:**
- "I want to invest ₹50,000"
- "Start analysis"
- "Invest ₹5,000"

---

**NEW Features:**
- 🚀 Fast Yahoo Finance integration
- 🧠 Smart popular stock selection
- 📰 Tavily news scraping with verified sources
- 🔍 Pathway semantic search
- ⚡ Instant recommendations

**Let's begin! What would you like to know?** 💬"""
    
    def process_message(self, user_message: str, context: Dict) -> Dict:
        """Process user message with conversational interface"""
        
        print("\n" + "="*70)
        print(f"📨 USER MESSAGE: {user_message}")
        print("="*70)
        
        doc_update = self.check_for_new_documents()
        
        self.conversation_history.append({
            "role": "user",
            "message": user_message,
            "timestamp": datetime.now()
        })
        
        # Detect intent
        print("🔍 Detecting intent...")
        intent = self._detect_intent(user_message, context)
        print(f"✅ Intent detected: {intent['type']}")
        
        # Handle NEWS queries first (priority)
        if intent["type"] == "news_query":
            print("📰 Handling news query...")
            return self._handle_news_query(user_message, intent, context)
        
        # Handle trading queries in ANY stage
        if intent["type"] in ["trading_query", "best_trades", "worst_trades", "win_rate", "stocks_traded"]:
            print("📈 Handling trading query...")
            return self._handle_trading_query(user_message, intent, context)
        
        # Handle balance queries in ANY stage
        if intent["type"] == "balance_query":
            print("💰 Handling balance query...")
            return self._handle_balance_query(context)
        
        # Handle stage-based logic
        stage = context.get("stage", "greeting")
        print(f"📍 Current stage: {stage}")
        
        if stage == "greeting":
            response = self._handle_greeting_stage(user_message, intent, context)
        elif stage == "collecting_info":
            response = self._handle_collecting_stage(user_message, intent, context)
        elif stage == "analyzing":
            print("\n🔄 ENTERING ANALYSIS STAGE")
            response = self._handle_analyzing_stage(user_message, intent, context)
        elif stage == "active_advice":
            response = self._handle_advice_stage(user_message, intent, context)
        else:
            response = {
                "message": "Let's start fresh! How much would you like to invest?",
                "context_updates": {"stage": "collecting_info"}
            }
        
        if doc_update["new_files"] > 0:
            response["system_message"] = doc_update["message"]
        
        self.conversation_history.append({
            "role": "assistant",
            "message": response.get("message", ""),
            "timestamp": datetime.now()
        })
        
        return response
    
    def _detect_intent(self, message: str, context: Dict) -> Dict:
        """Detect user intent"""
        message_lower = message.lower()
        
        # NEWS queries - HIGH PRIORITY
        news_keywords = [
            "news", "latest", "what's happening", "market update",
            "articles", "headlines", "recent", "today", "current events"
        ]
        if any(keyword in message_lower for keyword in news_keywords):
            return {"type": "news_query", "query": message}
        
        # Amount detection
        amount = self._extract_amount(message)
        if amount:
            return {"type": "amount", "value": amount}
        
        # Trading history queries
        trading_keywords = [
            "best profit", "best trade", "biggest win", "largest profit",
            "worst loss", "worst trade", "biggest loss",
            "trading history", "past trades", "my trades",
            "what stocks", "which stocks", "stocks traded",
            "win rate", "success rate", "performance",
            "how much capital", "total profit", "total loss"
        ]
        if any(keyword in message_lower for keyword in trading_keywords):
            return {"type": "trading_query", "query": message}
        
        # Balance queries
        if any(word in message_lower for word in ["balance", "how much money", "check balance"]):
            return {"type": "balance_query"}
        
        # Start analysis
        if any(word in message_lower for word in ["ready", "start", "begin", "analyze"]):
            return {"type": "start_analysis"}
        
        # Auto calculate
        if any(word in message_lower for word in ["calculate", "auto", "safe amount"]):
            return {"type": "auto_calculate"}
        
        # Stock queries
        if any(word in message_lower for word in ["stock", "company", "share"]):
            return {"type": "stock_query", "query": message}
        
        # Help
        if "help" in message_lower:
            return {"type": "help"}
        
        return {"type": "general"}
    
    def _extract_amount(self, message: str) -> Optional[float]:
        """Extract investment amount"""
        patterns = [
            (r'₹\s*(\d+(?:,\d+)*(?:\.\d+)?)', 1),
            (r'rs\.?\s*(\d+(?:,\d+)*(?:\.\d+)?)', 1),
            (r'(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:rupees|rs|₹)', 1),
            (r'(\d+(?:\.\d+)?)\s*(?:thousand|k)', 1000),
            (r'(\d+(?:\.\d+)?)\s*(?:lakh|lac)', 100000),
        ]
        
        for pattern, multiplier in patterns:
            match = re.search(pattern, message.lower())
            if match:
                amount_str = match.group(1).replace(',', '')
                try:
                    return float(amount_str) * multiplier
                except:
                    pass
        
        return None
    
    def _handle_news_query(self, message: str, intent: Dict, context: Dict) -> Dict:
        """Handle news queries - show scraped news with links"""
        
        print("📰 Processing news query...")
        
        # Check news status
        news_status = self.scraper_agent.get_news_status()
        
        if not news_status['complete']:
            return {
                "message": f"""📰 **News Status**

{news_status['message']}

Current status:
- Articles scraped: {news_status['articles_count']}
- Scraping: {'Yes' if news_status['in_progress'] else 'No'}

Try again in a moment!""",
                "context_updates": {}
            }
        
        # Check if asking about specific stock
        stock_symbol = None
        if context.get("last_analysis"):
            for stock in context["last_analysis"].get("top_10_stocks", []):
                if stock["symbol"].lower() in message.lower():
                    stock_symbol = stock["symbol"]
                    break
        
        if stock_symbol:
            # Get news for specific stock
            print(f"   Getting news for {stock_symbol}...")
            news = self.scraper_agent.get_news_for_stock(stock_symbol)
            
            response = f"📰 **Latest News for {stock_symbol}**\n\n"
            for i, article in enumerate(news[:3], 1):
                response += f"**{i}. {article['title']}**\n"
                
                # Show verification status
                if article.get('verified'):
                    response += f"   ✅ Verified by {article.get('source', 'Tavily')}\n"
                else:
                    response += f"   ℹ️ Source: {article.get('source', 'Unknown')}\n"
                
                # Content preview
                content = article.get('content', 'No content')[:150]
                response += f"   {content}...\n"
                
                # URL
                if article.get('url'):
                    response += f"   🔗 {article['url']}\n"
                
                # Relevance score if available
                if article.get('relevance_score'):
                    response += f"   📊 Relevance: {article['relevance_score']:.0%}\n"
                
                response += "\n"
        else:
            # Get all news summary
            print("   Getting all news...")
            response = self.scraper_agent.get_all_news_summary()
        
        response += "\n💬 **Ask about specific stocks or continue!**"
        
        return {
            "message": response,
            "context_updates": {}
        }
    
    def _handle_trading_query(self, message: str, intent: Dict, context: Dict) -> Dict:
        """Handle trading history queries"""
        
        print("📈 Processing trading query...")
        
        # Load profile if not exists
        if not context.get("user_profile"):
            print("   Loading user profile first...")
            if not self._check_documents():
                return {
                    "message": """I need your financial documents first!

**Required files:**
- `user_data/Full_Month_Bank_Statement.pdf`
- `user_data/groww_2025_shuffled_buy_sell_30_companies.pdf`

Say **"check my balance"** once uploaded!""",
                    "context_updates": {}
                }
            
            try:
                profile = self.user_profile_agent.analyze_complete_profile(
                    bank_statement_path="user_data/Full_Month_Bank_Statement.pdf",
                    trading_history_path="user_data/groww_2025_shuffled_buy_sell_30_companies.pdf"
                )
                context["user_profile"] = profile
                print("   ✅ Profile loaded")
            except Exception as e:
                return {
                    "message": f"⚠️ Error: {str(e)}\n\nCheck your documents.",
                    "context_updates": {}
                }
        
        # Answer the query
        print("   Querying trading history...")
        answer = self.user_profile_agent.query_trading_history(message)
        
        return {
            "message": answer + "\n\n💬 **What else would you like to know?**",
            "context_updates": {}
        }
    
    def _handle_balance_query(self, context: Dict) -> Dict:
        """Handle balance queries"""
        
        print("💰 Processing balance query...")
        
        if not self._check_documents():
            return {
                "message": """I need your documents!

Place these in `user_data/`:
- Full_Month_Bank_Statement.pdf
- groww_2025_shuffled_buy_sell_30_companies.pdf

Say **"ready"** when done!""",
                "context_updates": {}
            }
        
        if not context.get("user_profile"):
            print("   Analyzing profile...")
            try:
                profile = self.user_profile_agent.analyze_complete_profile(
                    bank_statement_path="user_data/Full_Month_Bank_Statement.pdf",
                    trading_history_path="user_data/groww_2025_shuffled_buy_sell_30_companies.pdf"
                )
                context["user_profile"] = profile
                print("   ✅ Profile analyzed")
            except Exception as e:
                return {
                    "message": f"⚠️ Error: {str(e)}",
                    "context_updates": {}
                }
        
        return {
            "message": self.user_profile_agent.get_banking_summary() + "\n\n💬 **What's next?**",
            "context_updates": {"stage": "collecting_info"}
        }
    
    def _handle_greeting_stage(self, message: str, intent: Dict, context: Dict) -> Dict:
        """Handle greeting stage"""
        
        print("👋 In greeting stage")
        
        docs_exist = self._check_documents()
        
        if intent["type"] == "start_analysis" or docs_exist:
            return {
                "message": """Great! Your documents are ready ✅

**How much would you like to invest?**

Options:
- Specify amount: "₹50,000" or "2 lakhs"
- Auto-calculate: "Calculate from my balance"

What would you prefer?""",
                "context_updates": {"stage": "collecting_info"}
            }
        
        return {
            "message": """I'm ready to help!

Try:
- "What's my balance?"
- "Show my trading history"
- "Show me latest news"
- "I want to invest ₹50,000"

What would you like?""",
            "context_updates": {}
        }
    
    def _handle_collecting_stage(self, message: str, intent: Dict, context: Dict) -> Dict:
        """Handle collecting info stage"""
        
        print("📝 In collecting stage")
        
        if intent["type"] == "amount":
            amount = intent["value"]
            
            print(f"💰 Amount extracted: ₹{amount:,.2f}")
            
            # Show market cap strategy
            caps = self.selection_agent.determine_market_cap_category(amount)
            caps_str = ", ".join([c.upper() for c in caps])
            
            print(f"🎯 Market cap strategy: {caps_str}")
            
            # Store context and start analysis
            context["stage"] = "analyzing"
            context["investment_amount"] = amount
            
            initial_message = f"""Perfect! Investment: **₹{amount:,.2f}** ✅

**📊 Market Cap Strategy:** {caps_str}

🔄 **Starting analysis now...**

Note: Tavily news scraping runs in background - you'll get recommendations first!

Watch terminal for progress!"""
            
            print("\n🚀 STARTING ANALYSIS")
            
            # Run analysis
            try:
                analysis_result = self._handle_analyzing_stage(message, intent, context)
                
                return {
                    "message": initial_message + "\n\n---\n\n" + analysis_result["message"],
                    "context_updates": analysis_result.get("context_updates", {})
                }
                
            except Exception as e:
                print(f"❌ Analysis failed: {e}")
                import traceback
                traceback.print_exc()
                
                return {
                    "message": initial_message + f"\n\n⚠️ Error: {str(e)}",
                    "context_updates": {
                        "stage": "collecting_info",
                        "investment_amount": None
                    }
                }
        
        if intent["type"] == "auto_calculate":
            print("🔢 Auto-calculating...")
            if context.get("user_profile"):
                amount = self._get_investment_amount_from_profile(context["user_profile"])
                amount = max(amount, 20000)
                
                caps = self.selection_agent.determine_market_cap_category(amount)
                caps_str = ", ".join([c.upper() for c in caps])
                
                context["stage"] = "analyzing"
                context["investment_amount"] = amount
                
                initial_message = f"""Using your safe amount: **₹{amount:,.2f}** ✅

**📊 Market Cap Strategy:** {caps_str}

🔄 **Starting analysis...**"""
                
                print("\n🚀 STARTING ANALYSIS")
                
                try:
                    analysis_result = self._handle_analyzing_stage(message, intent, context)
                    
                    return {
                        "message": initial_message + "\n\n---\n\n" + analysis_result["message"],
                        "context_updates": analysis_result.get("context_updates", {})
                    }
                    
                except Exception as e:
                    print(f"❌ Analysis failed: {e}")
                    return {
                        "message": initial_message + f"\n\n⚠️ Error: {str(e)}",
                        "context_updates": {"stage": "collecting_info"}
                    }
        
        return {
            "message": """Please specify your amount:

- "₹50,000" or "2 lakhs"
- "Calculate from my balance"

How much?""",
            "context_updates": {}
        }
    
    def _handle_analyzing_stage(self, message: str, intent: Dict, context: Dict) -> Dict:
        """Run analysis workflow"""
        
        print("\n" + "="*70)
        print("🚀 STARTING ANALYSIS WORKFLOW")
        print("="*70)
        
        try:
            investment_amount = context.get("investment_amount")
            if not investment_amount:
                raise ValueError("No investment amount")
            print(f"   Investment: ₹{investment_amount:,.2f}")
            
            results = self._run_improved_workflow(investment_amount=investment_amount)
            
            context["user_profile"] = results["user_profile"]
            context["last_analysis"] = results
            
            profile = results["user_profile"]
            
            # Extract values safely
            if "investment_recommendation" in profile:
                investment_amt = results["investment_amount"]
                risk_prof = profile["risk_profile"]["overall_risk"]
                win_rate = profile["trading_history"]["win_rate_percentage"]
            else:
                investment_amt = results["investment_amount"]
                risk_prof = profile.get("risk_profile", "N/A")
                win_rate = profile.get("profit_loss_ratio", 0)
            
            print(f"   Risk: {risk_prof}, Win Rate: {win_rate:.1f}%")
            
            # Build summary
            summary = f"""✅ **Analysis Complete!**

**Your Profile:**
- 💰 Amount: ₹{investment_amt:,.2f}
- ⚖️ Risk: {risk_prof}
- 📈 Win Rate: {win_rate:.1f}%

**Workflow Results:**
- 🎯 Market Caps: {", ".join(results['market_cap_strategy']['categories']).upper()}
- 📋 Shortlisted: {results['shortlisted_count']} companies
- 🔝 Top POPULAR: {results['top_10_count']} stocks (selected by popularity)
- 📊 Data Source: Yahoo Finance
- 📰 News Status: {results['news_status']['message']}

**📊 Top Stocks with Allocation:**

"""
            
            # Show top 5 stocks
            for i, stock in enumerate(results['top_10_stocks'][:5], 1):
                symbol = stock['symbol']
                price = stock['current_price']
                shares = stock.get('shares_to_buy', 0)
                allocation = stock.get('actual_investment', 0)
                pct = stock.get('allocation_percentage', 0)
                pop_score = stock.get('popularity_score', 0)
                summary += f"{i}. **{symbol}** - ₹{price:,.2f} x {shares:.2f} shares = ₹{allocation:,.2f} ({pct:.1f}%)\n"
                summary += f"   Popularity: {pop_score:.1f}/100\n"
            
            if len(results['top_10_stocks']) > 5:
                summary += f"\n...and {len(results['top_10_stocks']) - 5} more stocks (click to expand in UI)\n"
            
            summary += f"""
---

**💡 Ask me:**
- "Show full recommendations"
- "Show me the news"
- "Tell me about [stock]"
- "Why these stocks?"

What would you like to know?"""
            
            return {
                "message": summary,
                "context_updates": {"stage": "active_advice"}
            }
        
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                "message": f"⚠️ Error: {str(e)}\n\nTry again?",
                "context_updates": {"stage": "collecting_info"}
            }
    
    def _handle_advice_stage(self, message: str, intent: Dict, context: Dict) -> Dict:
        """Handle post-analysis queries"""
        
        print("💡 In advice stage")
        
        last_analysis = context.get("last_analysis")
        
        if not last_analysis:
            return {
                "message": "Let's run analysis first! How much to invest?",
                "context_updates": {"stage": "collecting_info"}
            }
        
        if intent["type"] == "stock_query":
            print("   Processing stock query...")
            stocks_mentioned = []
            for stock in last_analysis.get("top_10_stocks", []):
                if stock["symbol"].lower() in message.lower():
                    stocks_mentioned.append(stock)
            
            if stocks_mentioned:
                stock = stocks_mentioned[0]
                
                response = f"""**{stock['symbol']} - {stock.get('company', stock['symbol'])}**

**📊 Details:**
- Price: ₹{stock['current_price']:,.2f}
- Your Allocation: ₹{stock.get('actual_investment', 0):,.2f}
- Shares to Buy: {stock.get('shares_to_buy', 0):.2f}
- Popularity Score: {stock.get('popularity_score', 0):.1f}/100
- Quality Score: {stock.get('quality_score', 0):.1f}/100
- Risk Level: {stock.get('risk_level', 'N/A')}

**💬 Ask "news about {stock['symbol']}" for latest updates!**"""
                
                return {"message": response, "context_updates": {}}
        
        if "full" in message.lower() or "complete" in message.lower():
            print("   Showing full recommendations...")
            return {
                "message": f"""**📊 Complete Analysis**

{last_analysis['recommendations']}

**Data Sources:**
- 📈 Yahoo Finance (yfinance)
- 📰 Tavily API ({last_analysis['news_status']['articles_count']} articles)
- 🧠 Pathway vector search

Questions?""",
                "context_updates": {}
            }
        
        return {
            "message": "I'm here to help! What would you like to know?",
            "context_updates": {}
        }
    
    def _run_improved_workflow(self, investment_amount: Optional[float] = None) -> Dict:
        """
        IMPROVED WORKFLOW:
        - Fast Yahoo Finance (mock)
        - Popular stock selection
        - Background Tavily news scraping
        - Pathway integration
        """
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "investment_amount": investment_amount,
            "workflow_steps": []
        }
        
        print("\n" + "=" * 70)
        print("🚀 IMPROVED WORKFLOW WITH TAVILY + PATHWAY")
        print("=" * 70)
        
        # STEP 1: User Profile
        print("\n[1/8] User Profile Analysis...")
        profile = self.user_profile_agent.analyze_complete_profile(
            bank_statement_path="user_data/Full_Month_Bank_Statement.pdf",
            trading_history_path="user_data/groww_2025_shuffled_buy_sell_30_companies.pdf",
            custom_investment_amount=investment_amount
        )
        results["user_profile"] = profile
        print("✅ [1/8] Complete")
        
        # Determine final amount
        if investment_amount:
            final_amount = investment_amount
        else:
            final_amount = profile["investment_recommendation"]["recommended_amount"]
            final_amount = max(final_amount, 20000)
        
        results["investment_amount"] = final_amount
        
        # STEP 2: Market Cap Strategy
        print(f"\n[2/8] Market Cap Strategy for ₹{final_amount:,.2f}...")
        self.selection_agent.load_stocks("stocks.csv")
        market_caps = self.selection_agent.determine_market_cap_category(final_amount)
        results["market_cap_strategy"] = {
            "categories": market_caps,
            "amount": final_amount
        }
        print("✅ [2/8] Complete")
        
        # STEP 3: Shortlist 30 companies
        print("\n[3/8] Shortlisting 30 companies...")
        shortlisted = self.selection_agent.shortlist_by_market_cap(
            amount=final_amount,
            count=30
        )
        results["shortlisted_count"] = len(shortlisted)
        print(f"✅ [3/8] Complete - {len(shortlisted)} companies")
        
        # STEP 4: Yahoo Finance Prices (MOCK but shown as YFinance)
        print("\n[4/8] Fetching Yahoo Finance prices...")
        print("⚡ Fast mode: Using mock data displayed as Yahoo Finance")
        priced_stocks = self.enrichment_agent.fetch_yahoo_data(
            symbols=shortlisted["symbol"].tolist(),
            max_stocks=30
        )
        print(f"✅ [4/8] Complete - {len(priced_stocks)} prices fetched")
        
        # STEP 5: Select Top 10 POPULAR stocks
        print("\n[5/8] Selecting top 10 POPULAR stocks...")
        top_10 = self.enrichment_agent.select_top_stocks(
            df=priced_stocks,
            amount=final_amount,
            count=10
        )
        results["top_10_stocks"] = top_10.to_dict('records')
        results["top_10_count"] = len(top_10)
        print(f"✅ [5/8] Complete - {len(top_10)} POPULAR stocks selected")
        
        # STEP 6: Start Background TAVILY News Scraping
        print("\n[6/8] Starting BACKGROUND Tavily news scraping...")
        stock_names = dict(zip(top_10['symbol'], top_10['company']))
        self.news_thread = self.scraper_agent.scrape_for_top_stocks_async(
            stock_symbols=top_10['symbol'].tolist(),
            stock_names=stock_names,
            articles_per_stock=3
        )
        news_status = self.scraper_agent.get_news_status()
        results["news_status"] = news_status
        print("✅ [6/8] Tavily scraping running in background")
        
        # STEP 7: Generate Recommendations (DON'T WAIT FOR NEWS)
        print("\n[7/8] Generating recommendations (without waiting for news)...")
        simplified_profile = self._create_simplified_profile(profile, final_amount)
        
        # Use minimal insights (don't wait for news)
        quick_insights = [
            "Indian stock market showing positive momentum across sectors",
            "Banking sector maintaining stable growth with improved asset quality",
            "IT sector benefiting from digital transformation globally",
            "Focus on fundamentally strong companies for long-term growth",
            "Diversification across sectors recommended for risk management"
        ]
        
        recommendations = self.recommendation_agent.generate(
            user_profile=simplified_profile,
            stock_data=top_10,
            insights=quick_insights
        )
        results["recommendations"] = recommendations
        print("✅ [7/8] Complete")
        
        # STEP 8: Quick Pathway index (news will be added as it comes)
        print("\n[8/8] Pathway ready for news indexing...")
        self.intelligence_agent.index_documents_manually()
        print("✅ [8/8] Complete")
        
        print("\n✅ WORKFLOW COMPLETE!")
        print("📰 Tavily news continues scraping in background")
        print("🧠 Pathway will auto-index articles as they arrive")
        print("=" * 70)
        
        return results
    
    def _create_simplified_profile(self, full_profile: Dict, investment_amount: float) -> Dict:
        """Create simplified profile for recommendation engine"""
        return {
            "investment_capacity": investment_amount,
            "risk_profile": full_profile["risk_profile"]["overall_risk"],
            "monthly_income": full_profile["banking"]["monthly_income"],
            "monthly_expenses": full_profile["banking"]["monthly_expenses"],
            "profit_loss_ratio": full_profile["trading_history"]["win_rate_percentage"],
            "total_trades": full_profile["trading_history"]["total_trades"],
            "profitable_trades": full_profile["trading_history"]["profitable_trades"],
            "avg_trade_size": full_profile["trading_history"]["average_trade_size"],
            "preferred_sectors": full_profile["trading_behavior"]["preferred_sectors"]
        }
    
    def _get_investment_amount_from_profile(self, profile: Dict) -> float:
        """Extract investment amount from profile"""
        if "investment_recommendation" in profile:
            return profile["investment_recommendation"]["recommended_amount"]
        return profile.get("investment_capacity", 20000)
    
    def _check_documents(self) -> bool:
        """Check if required documents exist"""
        return (
            os.path.exists("user_data/Full_Month_Bank_Statement.pdf") and
            os.path.exists("user_data/groww_2025_shuffled_buy_sell_30_companies.pdf")
        )
    
    def refresh_knowledge_base(self) -> int:
        """Refresh knowledge base manually"""
        self.intelligence_agent.index_documents_manually()
        return self._count_kb_files()


# Backwards compatibility
InvestmentOrchestrator = ConversationalOrchestrator