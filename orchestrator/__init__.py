"""Orchestrator package - supports both old and new"""
from .orchestrator import ConversationalOrchestrator

# Backwards compatibility alias
InvestmentOrchestrator = ConversationalOrchestrator

__all__ = ['ConversationalOrchestrator', 'InvestmentOrchestrator']