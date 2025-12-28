"""
Base Agent Class
All agents inherit from this class
"""

import os
from typing import Dict, List
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class BaseAgent:
    """Base class for all agents"""
    
    def __init__(self, name: str):
        self.name = name
        
        # Initialize Groq client with API key from .env
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError(
                "GROQ_API_KEY not found! Please create a .env file with:\n"
                "GROQ_API_KEY=your_api_key_here"
            )
        
        # Remove quotes if present in the API key
        api_key = api_key.strip('"').strip("'")
        
        try:
            # Initialize Groq client with just the API key
            self.groq_client = Groq(api_key=api_key)
            self.model = "llama-3.3-70b-versatile"
        except Exception as e:
            raise ValueError(
                f"Failed to initialize Groq client: {e}\n"
                f"Please check your GROQ_API_KEY in .env file"
            )
    
    def chat(
        self, 
        messages: List[Dict], 
        temperature: float = 0.7, 
        max_tokens: int = 2000
    ) -> str:
        """Call Groq LLM"""
        try:
            response = self.groq_client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            self.log(f"Error calling Groq API: {e}")
            raise
    
    def log(self, message: str):
        """Agent logging"""
        print(f"[{self.name}] {message}")
    
    def get_status(self) -> Dict:
        """Return agent status"""
        return {
            "name": self.name,
            "model": self.model,
            "status": "active"
        }