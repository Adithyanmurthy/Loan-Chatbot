"""
Services package for business logic
Includes CRM integration, verification tracking, and other business services
"""

from .crm_client import CRMClient, CRMResponse, CRMErrorType, CRMDataValidator
from .verification_tracker import (
    VerificationTracker, VerificationRecord, VerificationStatusType, 
    VerificationMethod, get_verification_tracker
)

__all__ = [
    'CRMClient',
    'CRMResponse', 
    'CRMErrorType',
    'CRMDataValidator',
    'VerificationTracker',
    'VerificationRecord',
    'VerificationStatusType',
    'VerificationMethod',
    'get_verification_tracker',
]