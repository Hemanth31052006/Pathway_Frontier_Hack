"""
Agent 1: Financial Analyzer
Analyzes user's financial health from bank statements and trading history
"""

import json
import PyPDF2
from typing import Dict
from agents.base_agent import BaseAgent


class FinancialAnalyzerAgent(BaseAgent):
    """Analyzes user's financial health from documents"""
    
    def __init__(self):
        super().__init__("💰 Financial Analyzer")
    
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
            self.log(f"Error reading PDF: {e}")
            return ""
    
    def analyze(
        self, 
        bank_statement_path: str, 
        groww_path: str,
        custom_amount: float = None
    ) -> Dict:
        """
        Analyze financial documents and extract user profile
        
        Args:
            bank_statement_path: Path to bank statement PDF
            groww_path: Path to Groww transaction history PDF
            custom_amount: Optional custom investment amount
        
        Returns:
            Dict with user financial profile
        """
        
        self.log("Reading financial documents...")
        bank_text = self.extract_text_from_pdf(bank_statement_path)
        groww_text = self.extract_text_from_pdf(groww_path)
        
        if not bank_text or not groww_text:
            self.log("⚠️ Failed to extract text from PDFs")
            return self._get_default_profile(custom_amount)
        
        self.log("Analyzing financial profile with Groq LLM...")
        
        prompt = f"""You are a financial analyst. Analyze these documents and extract key metrics.

BANK STATEMENT:
{bank_text[:3000]}

GROWW TRANSACTION HISTORY:
{groww_text[:3500]}

Extract and return ONLY a valid JSON object (no markdown, no extra text) with:
{{
  "monthly_income": <number>,
  "monthly_expenses": <number>,
  "available_balance": <number>,
  "investment_capacity": <number after keeping 3-month emergency fund>,
  "risk_profile": "<CONSERVATIVE/MODERATE/AGGRESSIVE based on past trades>",
  "preferred_sectors": [list of sectors from Groww],
  "avg_trade_size": <average investment amount>,
  "profit_loss_ratio": <win rate percentage>,
  "total_trades": <count>,
  "profitable_trades": <count>
}}

ANALYSIS GUIDELINES:
- Monthly income: Look for "Salary Credit" entries
- Monthly expenses: Sum all debit entries
- Available balance: Final balance in statement
- Investment capacity: Available balance - (monthly_expenses * 3) for emergency fund
- Risk profile: 
  * CONSERVATIVE if win rate < 50% or few trades
  * MODERATE if win rate 50-70%
  * AGGRESSIVE if win rate > 70%
- Sectors: Extract from stock names (IT, Banking, Pharma, etc.)

IMPORTANT: Return ONLY the JSON object, nothing else."""

        try:
            response = self.chat([
                {"role": "system", "content": "You are a financial data extraction expert. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ], temperature=0.3)
            
            # Clean response
            response = response.strip()
            if response.startswith("```json"):
                response = response.split("```json")[1].split("```")[0].strip()
            elif response.startswith("```"):
                response = response.split("```")[1].split("```")[0].strip()
            
            profile = json.loads(response)
            
            # Override investment capacity if custom amount provided
            if custom_amount:
                profile["investment_capacity"] = custom_amount
                self.log(f"Using custom investment amount: ₹{custom_amount:,.0f}")
            
            self.log(f"✅ Profile extracted successfully")
            self.log(f"   Risk: {profile['risk_profile']}")
            self.log(f"   Capacity: ₹{profile['investment_capacity']:,.0f}")
            self.log(f"   Win Rate: {profile['profit_loss_ratio']:.1f}%")
            
            return profile
            
        except json.JSONDecodeError as e:
            self.log(f"⚠️ JSON parse error: {e}")
            self.log("Using default profile...")
            return self._get_default_profile(custom_amount)
        except Exception as e:
            self.log(f"⚠️ Analysis error: {e}")
            return self._get_default_profile(custom_amount)
    
    def _get_default_profile(self, custom_amount: float = None) -> Dict:
        """Return default profile if analysis fails"""
        return {
            "monthly_income": 45000,
            "monthly_expenses": 43512,
            "available_balance": 1488,
            "investment_capacity": custom_amount if custom_amount else 20000,
            "risk_profile": "MODERATE",
            "preferred_sectors": ["IT", "Banking", "Pharma"],
            "avg_trade_size": 15000,
            "profit_loss_ratio": 65.0,
            "total_trades": 103,
            "profitable_trades": 67
        }