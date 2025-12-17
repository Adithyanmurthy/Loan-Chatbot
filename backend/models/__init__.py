"""
Data models for the AI Loan Chatbot backend
Based on requirements: 1.4, 2.1, 3.1, 4.1
"""

# Customer models
from .customer import CustomerProfile, LoanDetails

# Loan models
from .loan import LoanApplication, LoanStatus, UnderwritingDecision

# Conversation models
from .conversation import (
    ConversationContext, AgentTask, ChatMessage, ErrorLog,
    AgentType, TaskType, TaskStatus, ErrorSeverity
)

# Document models
from .documents import (
    FileUpload, SanctionLetter, DocumentProcessingResult,
    FileUploadStatus, DocumentType
)

__all__ = [
    # Customer models
    'CustomerProfile',
    'LoanDetails',
    
    # Loan models
    'LoanApplication',
    'LoanStatus',
    'UnderwritingDecision',
    
    # Conversation models
    'ConversationContext',
    'AgentTask',
    'ChatMessage',
    'ErrorLog',
    'AgentType',
    'TaskType',
    'TaskStatus',
    'ErrorSeverity',
    
    # Document models
    'FileUpload',
    'SanctionLetter',
    'DocumentProcessingResult',
    'FileUploadStatus',
    'DocumentType',
]