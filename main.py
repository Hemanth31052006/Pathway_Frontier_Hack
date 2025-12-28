"""
Streamlit UI with TAVILY News Integration
- Shows verified Tavily articles
- Pathway semantic search demo
- Real content with working links
- Clear verification badges
"""

import streamlit as st
import os
from datetime import datetime
from orchestrator.orchestrator import ConversationalOrchestrator

# Page config
st.set_page_config(
    page_title="AI Investment Advisor",
    page_icon="💰",
    layout="wide"
)

# Helper functions
def get_investment_amount(profile):
    if not profile:
        return 0
    if "investment_recommendation" in profile:
        return profile["investment_recommendation"]["recommended_amount"]
    return profile.get("investment_capacity", 0)

def get_risk_profile(profile):
    if not profile:
        return "N/A"
    if "risk_profile" in profile and isinstance(profile["risk_profile"], dict):
        return profile["risk_profile"]["overall_risk"]
    return profile.get("risk_profile", "N/A")

def get_win_rate(profile):
    if not profile:
        return 0
    if "trading_history" in profile:
        return profile["trading_history"]["win_rate_percentage"]
    return profile.get("profit_loss_ratio", 0)

def display_stock_card(stock, index):
    """Display stock with investment details"""
    
    has_shares = stock.get('shares_to_buy', 0) > 0
    
    if has_shares:
        title = f"✅ {index}. **{stock['symbol']}** - ₹{stock.get('actual_investment', 0):,.2f} ({stock.get('allocation_percentage', 0):.1f}%)"
    else:
        title = f"⚠️ {index}. **{stock['symbol']}** - Not invested"
    
    with st.expander(title, expanded=(index <= 3 and has_shares)):
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Company:** {stock.get('company', stock['symbol'])}")
            st.write(f"**Price:** ₹{stock.get('current_price', 0):,.2f}")
            st.write(f"**Shares:** {stock.get('shares_to_buy', 0):.2f}")
            st.write(f"**Investment:** ₹{stock.get('actual_investment', 0):,.2f}")
            st.write(f"**Allocation:** {stock.get('allocation_percentage', 0):.1f}%")
        
        with col2:
            st.write(f"**Sector:** {stock.get('sector', 'N/A')}")
            st.write(f"**Risk Level:** {stock.get('risk_level', 'N/A')}")
            st.write(f"**Quality Score:** {stock.get('quality_score', 0):.1f}/100")
            st.write(f"**Popularity:** {stock.get('popularity_score', 0):.1f}/100")
        
        # News button for this stock
        if st.button(f"📰 News about {stock['symbol']}", key=f"news_{stock['symbol']}"):
            st.session_state.show_news = True
            st.session_state.news_stock = stock['symbol']
            st.rerun()
        
        if not has_shares:
            st.warning("⚠️ **Not in portfolio** - Price too high for current amount")

def display_news_article(article, index):
    """Display a single news article with Tavily verification"""
    
    verified = article.get('verified', False)
    source = article.get('source', 'Unknown')
    
    # Title with verification badge
    if verified:
        st.markdown(f"### ✅ {index}. {article.get('title', 'No title')}")
        st.success(f"**Verified by {source}**")
    else:
        st.markdown(f"### {index}. {article.get('title', 'No title')}")
        st.info(f"**Source:** {source}")
    
    # Relevance score if available
    if 'relevance_score' in article:
        score = article['relevance_score']
        st.progress(score, text=f"Relevance: {score:.0%}")
    
    # Content
    content = article.get('content', 'No content available')
    if content and len(content) > 200:
        with st.expander("📄 Read full article"):
            st.write(content)
    else:
        st.write(content)
    
    # URL
    url = article.get('url', '')
    if url:
        st.markdown(f"🔗 [Read on original site]({url})")
    
    # Stock info
    symbol = article.get('stock_symbol', '')
    company = article.get('company_name', '')
    if symbol:
        st.caption(f"📊 Related to: **{symbol}** ({company})")
    
    st.markdown("---")

def display_analysis_results(context):
    """Display analysis results"""
    
    last_analysis = context.get("last_analysis")
    if not last_analysis:
        return
    
    st.markdown("---")
    st.subheader("📊 Analysis Results")
    
    # Quick stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Investment", 
            f"₹{last_analysis.get('investment_amount', 0):,.0f}"
        )
    
    with col2:
        stocks = last_analysis.get('top_10_stocks', [])
        invested_stocks = [s for s in stocks if s.get('shares_to_buy', 0) > 0]
        st.metric("Stocks Selected", f"{len(invested_stocks)}/{len(stocks)}")
    
    with col3:
        total_invested = sum(s.get('actual_investment', 0) for s in stocks)
        utilization = (total_invested / last_analysis.get('investment_amount', 1)) * 100
        st.metric("Utilization", f"{utilization:.1f}%")
    
    with col4:
        news_status = last_analysis.get('news_status', {})
        st.metric("Tavily Articles", news_status.get('articles_count', 0))
    
    # Stock list
    st.markdown("---")
    st.subheader("🎯 Your Portfolio Stocks")
    
    stocks = last_analysis.get('top_10_stocks', [])
    if stocks:
        invested_stocks = [s for s in stocks if s.get('shares_to_buy', 0) > 0]
        if invested_stocks:
            total_invested = sum(s.get('actual_investment', 0) for s in invested_stocks)
            st.success(f"✅ {len(invested_stocks)} stocks - Total: ₹{total_invested:,.2f}")
        
        for i, stock in enumerate(stocks, 1):
            display_stock_card(stock, i)
    else:
        st.info("No stocks selected yet")
    
    # News section
    st.markdown("---")
    st.subheader("📰 Tavily Market News")
    
    news_status = last_analysis.get('news_status', {})
    
    col1, col2 = st.columns([3, 1])
    with col1:
        if news_status.get('complete'):
            st.success(f"✅ {news_status.get('articles_count', 0)} verified articles from Tavily!")
        elif news_status.get('in_progress'):
            st.info("🔄 Scraping real news with Tavily API...")
        else:
            st.warning("⏸️ News not available yet")
    
    with col2:
        if news_status.get('complete'):
            if st.button("📰 View All News", use_container_width=True):
                st.session_state.show_news = True
                st.session_state.news_stock = None
                st.rerun()

def display_pathway_demo(orchestrator):
    """Display Pathway semantic search demo"""
    
    st.markdown("---")
    st.subheader("🧠 Pathway Semantic Search Demo")
    
    st.info("""
    **Pathway Integration**: All Tavily articles are saved to `knowledge_base/` folder.
    Pathway monitors this folder in real-time and creates vector embeddings for semantic search.
    """)
    
    query = st.text_input("🔍 Ask about the news:", placeholder="e.g., 'What's happening with IT stocks?'")
    
    if query:
        with st.spinner("Searching with Pathway..."):
            # Use market intelligence agent for semantic search
            insights = orchestrator.intelligence_agent.query_insights(query, top_k=5)
            
            st.success(f"Found {len(insights)} relevant insights:")
            
            for i, insight in enumerate(insights, 1):
                with st.expander(f"Result {i}"):
                    st.write(insight)

# Initialize session state
if "orchestrator" not in st.session_state:
    st.session_state.orchestrator = ConversationalOrchestrator()
    st.session_state.messages = []
    st.session_state.context = {
        "stage": "greeting",
        "user_profile": None,
        "last_analysis": None
    }
    st.session_state.show_news = False
    st.session_state.news_stock = None
    
    greeting = st.session_state.orchestrator.get_greeting()
    st.session_state.messages.append({
        "role": "assistant",
        "content": greeting,
        "timestamp": datetime.now()
    })

# Sidebar
with st.sidebar:
    st.title("💰 AI Investment Advisor")
    st.markdown("---")
    
    # Current stage
    stage = st.session_state.context["stage"]
    stage_emoji = {
        "greeting": "👋",
        "collecting_info": "📝",
        "analyzing": "🔄",
        "active_advice": "💡"
    }
    
    st.subheader(f"{stage_emoji.get(stage, '🤖')} Stage")
    st.info(stage.replace("_", " ").title())
    
    # Document status
    st.markdown("---")
    st.subheader("📁 Documents")
    
    bank_exists = os.path.exists("user_data/Full_Month_Bank_Statement.pdf")
    groww_exists = os.path.exists("user_data/groww_2025_shuffled_buy_sell_30_companies.pdf")
    
    st.write("Bank:", "✅" if bank_exists else "❌")
    st.write("Trading:", "✅" if groww_exists else "❌")
    
    # Knowledge base + Pathway status
    st.markdown("---")
    st.subheader("🧠 Knowledge Base")
    
    kb_files = len([f for f in os.listdir("knowledge_base") 
                    if f.endswith(('.txt', '.pdf'))]) if os.path.exists("knowledge_base") else 0
    
    st.metric("Pathway Files", kb_files)
    
    tavily_key = os.getenv("TAVILY_API_KEY")
    st.write("Tavily API:", "✅" if tavily_key else "❌")
    
    if st.button("🔄 Refresh KB"):
        count = st.session_state.orchestrator.refresh_knowledge_base()
        st.success(f"✅ {count} files indexed")
    
    # User profile
    if st.session_state.context.get("user_profile"):
        st.markdown("---")
        st.subheader("👤 Profile")
        profile = st.session_state.context["user_profile"]
        
        investment_amt = get_investment_amount(profile)
        risk_prof = get_risk_profile(profile)
        win_rate = get_win_rate(profile)
        
        st.write(f"💰 ₹{investment_amt:,.0f}")
        st.write(f"⚖️ {risk_prof}")
        st.write(f"📈 {win_rate:.1f}%")
    
    # Clear chat
    st.markdown("---")
    if st.button("🗑️ Clear"):
        st.session_state.messages = []
        st.session_state.context = {
            "stage": "greeting",
            "user_profile": None,
            "last_analysis": None
        }
        st.session_state.show_news = False
        st.session_state.news_stock = None
        greeting = st.session_state.orchestrator.get_greeting()
        st.session_state.messages.append({
            "role": "assistant",
            "content": greeting,
            "timestamp": datetime.now()
        })
        st.rerun()

# Main content
if st.session_state.get("show_news", False):
    # News display mode
    st.title("📰 Tavily Market News")
    
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("⬅️ Back"):
            st.session_state.show_news = False
            st.session_state.news_stock = None
            st.rerun()
    
    news_cache = st.session_state.orchestrator.scraper_agent.news_cache
    
    if not news_cache:
        st.info("🔄 News is being scraped with Tavily API. Check back soon!")
    else:
        # Filter by stock if specified
        stock_filter = st.session_state.get('news_stock')
        
        if stock_filter:
            st.subheader(f"News for {stock_filter}")
            filtered_news = [a for a in news_cache if a.get('stock_symbol') == stock_filter]
        else:
            st.subheader("All News")
            filtered_news = news_cache
        
        if not filtered_news:
            st.warning("No news articles found")
        else:
            st.success(f"✅ {len(filtered_news)} verified articles from Tavily")
            
            # Display articles
            for i, article in enumerate(filtered_news, 1):
                display_news_article(article, i)
        
        # Pathway semantic search demo
        display_pathway_demo(st.session_state.orchestrator)

else:
    # Chat mode
    st.title("💬 Investment Advisor Chat")
    
    # Display analysis results
    if st.session_state.context.get("last_analysis"):
        display_analysis_results(st.session_state.context)
        st.markdown("---")
    
    # Chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Type your message..."):
        # Add user message
        st.session_state.messages.append({
            "role": "user",
            "content": prompt,
            "timestamp": datetime.now()
        })
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Process
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response = st.session_state.orchestrator.process_message(
                        user_message=prompt,
                        context=st.session_state.context
                    )
                    
                    if "context_updates" in response:
                        st.session_state.context.update(response["context_updates"])
                    
                    assistant_message = response["message"]
                    st.markdown(assistant_message)
                    
                    if "system_message" in response:
                        st.info(response["system_message"])
                    
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": assistant_message,
                        "timestamp": datetime.now()
                    })
                    
                except Exception as e:
                    import traceback
                    error_details = traceback.format_exc()
                    error_msg = f"❌ Error: {str(e)}"
                    st.error(error_msg)
                    
                    print("="*60)
                    print("ERROR:")
                    print(error_details)
                    print("="*60)

# Footer
st.markdown("---")
st.caption("🔥 **Powered by Tavily API + Pathway** | Real news with semantic search")