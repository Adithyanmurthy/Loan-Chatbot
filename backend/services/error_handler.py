"""
Comprehensive Error Handling Service for AI Loan Chatbot
Implements graceful error handling, customer communication, and error logging infrastructure
Based on requirements: 6.3, 6.5
"""

import logging
import traceback
import uuid
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field

from models.conversation import ConversationContext, AgentType, ErrorSeverity


class ErrorCategory(str, Enum):
    """Categories of errors in the system"""
    AGENT_FAILURE = "agent_failure"
    API_FAILURE = "api_failure"
    VALIDATION_ERROR = "validation_error"
    PROCESSING_ERROR = "processing_error"
    NETWORK_ERROR = "network_error"
    TIMEOUT_ERROR = "timeout_error"
    AUTHENTICATION_ERROR = "authentication_error"
    BUSINESS_RULE_ERROR = "business_rule_error"
    DATA_ERROR = "data_error"
    SYSTEM_ERROR = "system_error"


class ErrorSeverityLevel(str, Enum):
    """Error severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class ErrorContext:
    """Context information for error handling"""
    session_id: Optional[str] = None
    agent_type: Optional[AgentType] = None
    task_id: Optional[str] = None
    customer_id: Optional[str] = None
    conversation_stage: Optional[str] = None
    additional_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ErrorHandlingResult:
    """Result of error handling operation"""
    handled: bool
    customer_message: str
    recovery_actions: List[str]
    escalation_required: bool = False
    retry_possible: bool = False
    error_logged: bool = False
    context_updated: bool = False


class CustomerCommunicationManager:
    """Manages customer-facing error communications"""
    
    def __init__(self):
        # Customer-friendly error messages by category
        self.error_messages = {
            ErrorCategory.AGENT_FAILURE: {
                'default': "I apologize, but I'm experiencing a temporary issue. Let me try to help you in a different way.",
                'sales': "I'm having trouble with the loan calculation. Let me get you connected with our loan specialist.",
                'verification': "There's a temporary issue with verification. Let me try an alternative approach.",
                'underwriting': "I'm experiencing difficulty with the approval process. Please give me a moment to resolve this.",
                'sanction': "There's a temporary issue generating your documents. I'll have this resolved shortly."
            },
            ErrorCategory.API_FAILURE: {
                'default': "I'm having trouble accessing some information right now. Let me try again in a moment.",
                'crm': "I'm unable to access your customer information at the moment. Could you please provide your details manually?",
                'credit_bureau': "I'm having difficulty checking your credit score. We can proceed with alternative verification methods.",
                'offer_mart': "I'm unable to access your pre-approved offers right now. Let me calculate options based on standard criteria."
            },
            ErrorCategory.VALIDATION_ERROR: {
                'default': "There seems to be an issue with the information provided. Could you please check and try again?",
                'amount': "The loan amount you've entered seems unusual. Could you please confirm the amount?",
                'tenure': "The tenure you've selected isn't available. Let me show you the available options.",
                'documents': "There's an issue with the document you've uploaded. Please check the format and try again."
            },
            ErrorCategory.PROCESSING_ERROR: {
                'default': "I'm having trouble processing your request. Let me try a different approach.",
                'calculation': "There's an issue with the loan calculations. Let me recalculate this for you.",
                'document_generation': "I'm having trouble generating your documents. I'll resolve this shortly."
            },
            ErrorCategory.NETWORK_ERROR: {
                'default': "I'm experiencing connectivity issues. Please bear with me while I resolve this.",
                'timeout': "The request is taking longer than expected. Let me try again with a different approach."
            },
            ErrorCategory.TIMEOUT_ERROR: {
                'default': "The operation is taking longer than expected. Let me try again.",
                'api_timeout': "I'm having trouble getting a response from our systems. Let me try an alternative method."
            },
            ErrorCategory.BUSINESS_RULE_ERROR: {
                'default': "There's an issue with the loan criteria. Let me explain the available options.",
                'eligibility': "Based on our current criteria, there are some eligibility concerns. Let me explain the alternatives.",
                'limits': "The requested amount exceeds our current limits. Let me show you what's available."
            },
            ErrorCategory.DATA_ERROR: {
                'default': "There seems to be an issue with the data. Could you please verify the information?",
                'missing_data': "Some required information is missing. Could you please provide the additional details?",
                'invalid_data': "Some of the information doesn't seem correct. Could you please check and update it?"
            },
            ErrorCategory.SYSTEM_ERROR: {
                'default': "I'm experiencing a technical issue. Let me try to resolve this for you.",
                'database': "There's a temporary issue with our systems. I'm working to resolve this.",
                'service_unavailable': "Some of our services are temporarily unavailable. Let me try alternative methods."
            }
        }
        
        # Recovery suggestions by category
        self.recovery_suggestions = {
            ErrorCategory.AGENT_FAILURE: [
                "Let me try a different approach to help you",
                "I'll connect you with an alternative solution",
                "Let me restart this process for you"
            ],
            ErrorCategory.API_FAILURE: [
                "I'll try accessing the information through a different method",
                "Let me use alternative data sources",
                "We can proceed with manual verification if needed"
            ],
            ErrorCategory.VALIDATION_ERROR: [
                "Please double-check the information and try again",
                "Let me guide you through the correct format",
                "I'll help you provide the information in the right way"
            ],
            ErrorCategory.PROCESSING_ERROR: [
                "Let me recalculate this for you",
                "I'll try processing this differently",
                "Let me break this down into smaller steps"
            ],
            ErrorCategory.NETWORK_ERROR: [
                "I'll retry the connection",
                "Let me try a different server",
                "We can continue once the connection is restored"
            ],
            ErrorCategory.BUSINESS_RULE_ERROR: [
                "Let me explain the available alternatives",
                "I'll show you options that meet our criteria",
                "Let me find a solution that works within our guidelines"
            ]
        }
    
    def get_customer_message(self, error_category: ErrorCategory, 
                           error_context: Optional[ErrorContext] = None,
                           specific_type: Optional[str] = None) -> str:
        """
        Get customer-friendly error message.
        
        Args:
            error_category: Category of the error
            error_context: Additional context about the error
            specific_type: Specific type within the category
            
        Returns:
            Customer-friendly error message
        """
        messages = self.error_messages.get(error_category, {})
        
        # Try to get specific message first
        if specific_type and specific_type in messages:
            return messages[specific_type]
        
        # Fall back to default message for category
        if 'default' in messages:
            return messages['default']
        
        # Ultimate fallback
        return "I apologize, but I'm experiencing a technical issue. Let me try to help you in a different way."
    
    def get_recovery_suggestions(self, error_category: ErrorCategory) -> List[str]:
        """
        Get recovery suggestions for error category.
        
        Args:
            error_category: Category of the error
            
        Returns:
            List of recovery suggestions
        """
        return self.recovery_suggestions.get(error_category, [
            "Let me try to resolve this issue",
            "I'll attempt a different approach",
            "Please bear with me while I fix this"
        ])


class ErrorLogger:
    """Centralized error logging system"""
    
    def __init__(self, log_level: int = logging.INFO):
        """
        Initialize error logger.
        
        Args:
            log_level: Logging level
        """
        self.logger = logging.getLogger("ai_loan_chatbot.error_handler")
        self.logger.setLevel(log_level)
        
        # Create handler if not exists
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def log_error(self, error_category: ErrorCategory, error_message: str,
                  error_context: Optional[ErrorContext] = None,
                  exception: Optional[Exception] = None,
                  severity: ErrorSeverityLevel = ErrorSeverityLevel.MEDIUM) -> str:
        """
        Log error with context and return error ID.
        
        Args:
            error_category: Category of the error
            error_message: Error message
            error_context: Additional context
            exception: Original exception if available
            severity: Error severity level
            
        Returns:
            Unique error ID
        """
        error_id = f"err_{uuid.uuid4().hex[:8]}_{int(datetime.now().timestamp())}"
        
        log_data = {
            'error_id': error_id,
            'category': error_category.value,
            'message': error_message,
            'severity': severity.value,
            'timestamp': datetime.now().isoformat()
        }
        
        if error_context:
            log_data['context'] = {
                'session_id': error_context.session_id,
                'agent_type': error_context.agent_type.value if error_context.agent_type else None,
                'task_id': error_context.task_id,
                'customer_id': error_context.customer_id,
                'conversation_stage': error_context.conversation_stage,
                'additional_data': error_context.additional_data
            }
        
        if exception:
            log_data['exception'] = {
                'type': type(exception).__name__,
                'message': str(exception),
                'traceback': traceback.format_exc()
            }
        
        # Log based on severity
        if severity == ErrorSeverityLevel.CRITICAL:
            self.logger.critical(f"CRITICAL ERROR: {log_data}")
        elif severity == ErrorSeverityLevel.HIGH:
            self.logger.error(f"HIGH SEVERITY ERROR: {log_data}")
        elif severity == ErrorSeverityLevel.MEDIUM:
            self.logger.warning(f"MEDIUM SEVERITY ERROR: {log_data}")
        elif severity == ErrorSeverityLevel.LOW:
            self.logger.info(f"LOW SEVERITY ERROR: {log_data}")
        else:
            self.logger.info(f"INFO: {log_data}")
        
        return error_id


class ErrorRecoveryManager:
    """Manages error recovery strategies and execution"""
    
    def __init__(self):
        """Initialize error recovery manager"""
        self.recovery_strategies = {
            ErrorCategory.AGENT_FAILURE: self._handle_agent_failure,
            ErrorCategory.API_FAILURE: self._handle_api_failure,
            ErrorCategory.VALIDATION_ERROR: self._handle_validation_error,
            ErrorCategory.PROCESSING_ERROR: self._handle_processing_error,
            ErrorCategory.NETWORK_ERROR: self._handle_network_error,
            ErrorCategory.TIMEOUT_ERROR: self._handle_timeout_error,
            ErrorCategory.BUSINESS_RULE_ERROR: self._handle_business_rule_error,
            ErrorCategory.DATA_ERROR: self._handle_data_error,
            ErrorCategory.SYSTEM_ERROR: self._handle_system_error
        }
    
    def execute_recovery(self, error_category: ErrorCategory,
                        error_context: ErrorContext,
                        recovery_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Execute recovery strategy for error.
        
        Args:
            error_category: Category of the error
            error_context: Error context information
            recovery_callback: Optional callback for custom recovery
            
        Returns:
            Recovery execution result
        """
        strategy_handler = self.recovery_strategies.get(error_category)
        
        if strategy_handler:
            return strategy_handler(error_context, recovery_callback)
        else:
            return self._default_recovery(error_context, recovery_callback)
    
    def _handle_agent_failure(self, context: ErrorContext, callback: Optional[Callable] = None) -> Dict[str, Any]:
        """Handle agent failure recovery"""
        return {
            'recovery_type': 'agent_restart',
            'actions': ['restart_agent', 'reset_task', 'notify_customer'],
            'retry_possible': True,
            'escalation_required': False,
            'estimated_recovery_time': 30  # seconds
        }
    
    def _handle_api_failure(self, context: ErrorContext, callback: Optional[Callable] = None) -> Dict[str, Any]:
        """Handle API failure recovery"""
        return {
            'recovery_type': 'api_retry_with_fallback',
            'actions': ['retry_api_call', 'use_fallback_data', 'continue_with_manual'],
            'retry_possible': True,
            'escalation_required': False,
            'estimated_recovery_time': 60  # seconds
        }
    
    def _handle_validation_error(self, context: ErrorContext, callback: Optional[Callable] = None) -> Dict[str, Any]:
        """Handle validation error recovery"""
        return {
            'recovery_type': 'request_correction',
            'actions': ['request_data_correction', 'provide_format_guidance', 'offer_assistance'],
            'retry_possible': True,
            'escalation_required': False,
            'estimated_recovery_time': 0  # immediate
        }
    
    def _handle_processing_error(self, context: ErrorContext, callback: Optional[Callable] = None) -> Dict[str, Any]:
        """Handle processing error recovery"""
        return {
            'recovery_type': 'reprocess_with_alternative',
            'actions': ['retry_processing', 'use_alternative_method', 'simplify_process'],
            'retry_possible': True,
            'escalation_required': False,
            'estimated_recovery_time': 45  # seconds
        }
    
    def _handle_network_error(self, context: ErrorContext, callback: Optional[Callable] = None) -> Dict[str, Any]:
        """Handle network error recovery"""
        return {
            'recovery_type': 'network_retry',
            'actions': ['retry_connection', 'use_cached_data', 'wait_and_retry'],
            'retry_possible': True,
            'escalation_required': False,
            'estimated_recovery_time': 90  # seconds
        }
    
    def _handle_timeout_error(self, context: ErrorContext, callback: Optional[Callable] = None) -> Dict[str, Any]:
        """Handle timeout error recovery"""
        return {
            'recovery_type': 'timeout_retry',
            'actions': ['increase_timeout', 'retry_operation', 'use_async_processing'],
            'retry_possible': True,
            'escalation_required': False,
            'estimated_recovery_time': 120  # seconds
        }
    
    def _handle_business_rule_error(self, context: ErrorContext, callback: Optional[Callable] = None) -> Dict[str, Any]:
        """Handle business rule error recovery"""
        return {
            'recovery_type': 'provide_alternatives',
            'actions': ['explain_rules', 'offer_alternatives', 'suggest_modifications'],
            'retry_possible': True,
            'escalation_required': False,
            'estimated_recovery_time': 0  # immediate
        }
    
    def _handle_data_error(self, context: ErrorContext, callback: Optional[Callable] = None) -> Dict[str, Any]:
        """Handle data error recovery"""
        return {
            'recovery_type': 'data_correction',
            'actions': ['request_data_verification', 'use_default_values', 'manual_data_entry'],
            'retry_possible': True,
            'escalation_required': False,
            'estimated_recovery_time': 30  # seconds
        }
    
    def _handle_system_error(self, context: ErrorContext, callback: Optional[Callable] = None) -> Dict[str, Any]:
        """Handle system error recovery"""
        return {
            'recovery_type': 'system_recovery',
            'actions': ['restart_service', 'use_backup_system', 'escalate_to_admin'],
            'retry_possible': True,
            'escalation_required': True,
            'estimated_recovery_time': 300  # seconds
        }
    
    def _default_recovery(self, context: ErrorContext, callback: Optional[Callable] = None) -> Dict[str, Any]:
        """Default recovery strategy"""
        return {
            'recovery_type': 'generic_recovery',
            'actions': ['log_error', 'notify_customer', 'continue_conversation'],
            'retry_possible': False,
            'escalation_required': True,
            'estimated_recovery_time': 60  # seconds
        }


class ComprehensiveErrorHandler:
    """Main error handling orchestrator"""
    
    def __init__(self):
        """Initialize comprehensive error handler"""
        self.communication_manager = CustomerCommunicationManager()
        self.error_logger = ErrorLogger()
        self.recovery_manager = ErrorRecoveryManager()
        
        # Error handling statistics
        self.error_stats = {
            'total_errors': 0,
            'errors_by_category': {},
            'recovery_success_rate': 0.0,
            'escalation_rate': 0.0
        }
    
    def handle_error(self, error: Exception, error_category: ErrorCategory,
                    error_context: Optional[ErrorContext] = None,
                    conversation_context: Optional[ConversationContext] = None,
                    specific_type: Optional[str] = None) -> ErrorHandlingResult:
        """
        Comprehensive error handling with logging, recovery, and customer communication.
        
        Args:
            error: The exception that occurred
            error_category: Category of the error
            error_context: Context information about the error
            conversation_context: Current conversation context
            specific_type: Specific error type within category
            
        Returns:
            Error handling result
        """
        try:
            # Update statistics
            self.error_stats['total_errors'] += 1
            category_count = self.error_stats['errors_by_category'].get(error_category.value, 0)
            self.error_stats['errors_by_category'][error_category.value] = category_count + 1
            
            # Log the error
            error_id = self.error_logger.log_error(
                error_category=error_category,
                error_message=str(error),
                error_context=error_context,
                exception=error,
                severity=self._determine_severity(error_category, error)
            )
            
            # Get customer-friendly message
            customer_message = self.communication_manager.get_customer_message(
                error_category, error_context, specific_type
            )
            
            # Execute recovery strategy
            recovery_result = self.recovery_manager.execute_recovery(
                error_category, error_context or ErrorContext()
            )
            
            # Update conversation context if provided
            context_updated = False
            if conversation_context:
                conversation_context.add_error(
                    message=f"Error ID {error_id}: {str(error)}",
                    severity=self._map_to_conversation_severity(error_category),
                    context={
                        'error_id': error_id,
                        'error_category': error_category.value,
                        'recovery_strategy': recovery_result['recovery_type']
                    }
                )
                context_updated = True
            
            # Determine if escalation is required
            escalation_required = (
                recovery_result.get('escalation_required', False) or
                self._should_escalate(error_category, error)
            )
            
            return ErrorHandlingResult(
                handled=True,
                customer_message=customer_message,
                recovery_actions=recovery_result.get('actions', []),
                escalation_required=escalation_required,
                retry_possible=recovery_result.get('retry_possible', False),
                error_logged=True,
                context_updated=context_updated
            )
            
        except Exception as handler_error:
            # Error in error handler - use minimal fallback
            self.error_logger.log_error(
                ErrorCategory.SYSTEM_ERROR,
                f"Error handler failure: {str(handler_error)}",
                severity=ErrorSeverityLevel.CRITICAL
            )
            
            return ErrorHandlingResult(
                handled=False,
                customer_message="I apologize, but I'm experiencing technical difficulties. Please try again in a moment.",
                recovery_actions=['restart_conversation'],
                escalation_required=True,
                retry_possible=True,
                error_logged=True,
                context_updated=False
            )
    
    def handle_agent_error(self, agent_type: AgentType, task_id: str, error: Exception,
                          session_id: Optional[str] = None,
                          conversation_context: Optional[ConversationContext] = None) -> ErrorHandlingResult:
        """
        Handle agent-specific errors with appropriate recovery.
        
        Args:
            agent_type: Type of agent that failed
            task_id: ID of the task that failed
            error: The exception that occurred
            session_id: Session ID if available
            conversation_context: Current conversation context
            
        Returns:
            Error handling result
        """
        error_context = ErrorContext(
            session_id=session_id,
            agent_type=agent_type,
            task_id=task_id,
            conversation_stage=conversation_context.conversation_stage if conversation_context else None,
            additional_data={'agent_error': True}
        )
        
        return self.handle_error(
            error=error,
            error_category=ErrorCategory.AGENT_FAILURE,
            error_context=error_context,
            conversation_context=conversation_context,
            specific_type=agent_type.value
        )
    
    def handle_api_error(self, api_name: str, error: Exception,
                        session_id: Optional[str] = None,
                        conversation_context: Optional[ConversationContext] = None) -> ErrorHandlingResult:
        """
        Handle API-specific errors with appropriate recovery.
        
        Args:
            api_name: Name of the API that failed
            error: The exception that occurred
            session_id: Session ID if available
            conversation_context: Current conversation context
            
        Returns:
            Error handling result
        """
        error_context = ErrorContext(
            session_id=session_id,
            additional_data={'api_name': api_name, 'api_error': True}
        )
        
        return self.handle_error(
            error=error,
            error_category=ErrorCategory.API_FAILURE,
            error_context=error_context,
            conversation_context=conversation_context,
            specific_type=api_name.lower()
        )
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """
        Get error handling statistics.
        
        Returns:
            Dictionary containing error statistics
        """
        return self.error_stats.copy()
    
    def _determine_severity(self, error_category: ErrorCategory, error: Exception) -> ErrorSeverityLevel:
        """Determine error severity based on category and exception type"""
        # Critical errors
        if error_category in [ErrorCategory.SYSTEM_ERROR]:
            return ErrorSeverityLevel.CRITICAL
        
        # High severity errors
        if error_category in [ErrorCategory.AGENT_FAILURE, ErrorCategory.API_FAILURE]:
            return ErrorSeverityLevel.HIGH
        
        # Medium severity errors
        if error_category in [ErrorCategory.PROCESSING_ERROR, ErrorCategory.NETWORK_ERROR, ErrorCategory.TIMEOUT_ERROR]:
            return ErrorSeverityLevel.MEDIUM
        
        # Low severity errors
        if error_category in [ErrorCategory.VALIDATION_ERROR, ErrorCategory.BUSINESS_RULE_ERROR]:
            return ErrorSeverityLevel.LOW
        
        # Default to medium
        return ErrorSeverityLevel.MEDIUM
    
    def _map_to_conversation_severity(self, error_category: ErrorCategory) -> ErrorSeverity:
        """Map error category to conversation context severity"""
        severity_map = {
            ErrorCategory.SYSTEM_ERROR: ErrorSeverity.CRITICAL,
            ErrorCategory.AGENT_FAILURE: ErrorSeverity.HIGH,
            ErrorCategory.API_FAILURE: ErrorSeverity.HIGH,
            ErrorCategory.PROCESSING_ERROR: ErrorSeverity.MEDIUM,
            ErrorCategory.NETWORK_ERROR: ErrorSeverity.MEDIUM,
            ErrorCategory.TIMEOUT_ERROR: ErrorSeverity.MEDIUM,
            ErrorCategory.VALIDATION_ERROR: ErrorSeverity.LOW,
            ErrorCategory.BUSINESS_RULE_ERROR: ErrorSeverity.LOW,
            ErrorCategory.DATA_ERROR: ErrorSeverity.MEDIUM
        }
        return severity_map.get(error_category, ErrorSeverity.MEDIUM)
    
    def _should_escalate(self, error_category: ErrorCategory, error: Exception) -> bool:
        """Determine if error should be escalated"""
        # Always escalate system errors
        if error_category == ErrorCategory.SYSTEM_ERROR:
            return True
        
        # Escalate if error count for category is high
        category_count = self.error_stats['errors_by_category'].get(error_category.value, 0)
        if category_count > 10:  # Threshold for escalation
            return True
        
        return False


# Global error handler instance
error_handler = ComprehensiveErrorHandler()