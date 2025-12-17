"""
Agent framework for the AI Loan Chatbot backend
Based on requirements: 6.1, 6.2, 6.3
"""

from .base_agent import BaseAgent, AgentStatus
from .context_manager import ContextManager
from .session_manager import SessionManager
from .verification_agent import VerificationAgent

__all__ = [
    'BaseAgent',
    'AgentStatus',
    'ContextManager',
    'SessionManager',
    'VerificationAgent',
]