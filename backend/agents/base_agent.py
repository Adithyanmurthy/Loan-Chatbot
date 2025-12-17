"""
Base Agent Framework for AI Loan Chatbot
Implements task execution interface, status reporting, error handling, and context sharing
Based on requirements: 6.1, 6.2, 6.3
"""

import logging
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum

from models.conversation import (
    ConversationContext, AgentTask, TaskType, TaskStatus, 
    AgentType, ErrorLog, ErrorSeverity
)
from services.error_handler import (
    ComprehensiveErrorHandler, ErrorCategory, ErrorContext, 
    ErrorHandlingResult
)


class AgentStatus(str, Enum):
    """Enumeration for agent status"""
    IDLE = "idle"
    PROCESSING = "processing"
    WAITING = "waiting"
    ERROR = "error"
    COMPLETED = "completed"


class BaseAgent(ABC):
    """
    Base class for all AI agents in the loan processing system.
    Provides common functionality for task execution, status reporting,
    error handling, and context sharing.
    """
    
    def __init__(self, agent_type: AgentType, agent_id: Optional[str] = None):
        """
        Initialize base agent with type and unique identifier.
        
        Args:
            agent_type: Type of agent (master, sales, verification, etc.)
            agent_id: Optional unique identifier, generated if not provided
        """
        self.agent_type = agent_type
        self.agent_id = agent_id or f"{agent_type.value}_{uuid.uuid4().hex[:8]}"
        self.status = AgentStatus.IDLE
        self.current_task: Optional[AgentTask] = None
        self.context: Optional[ConversationContext] = None
        
        # Set up logging
        self.logger = self._setup_logging()
        
        # Task execution history
        self.task_history: List[AgentTask] = []
        
        # Error handling
        self.error_count = 0
        self.max_retries = 3
        self.error_handler = ComprehensiveErrorHandler()
        
        # Recovery state
        self.recovery_attempts = 0
        self.max_recovery_attempts = 2
        self.last_error_time = None
        
        self.logger.info(f"Initialized {self.agent_type.value} agent with ID: {self.agent_id}")

    def _setup_logging(self) -> logging.Logger:
        """Set up logging for the agent"""
        logger = logging.getLogger(f"agent.{self.agent_type.value}.{self.agent_id}")
        logger.setLevel(logging.INFO)
        
        # Create handler if not exists
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger

    def set_context(self, context: ConversationContext) -> None:
        """
        Set the conversation context for this agent.
        
        Args:
            context: ConversationContext object containing session state
        """
        self.context = context
        self.logger.info(f"Context set for session: {context.session_id}")

    def get_status(self) -> Dict[str, Any]:
        """
        Get current agent status and information.
        
        Returns:
            Dictionary containing agent status information
        """
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type.value,
            "status": self.status.value,
            "current_task_id": self.current_task.id if self.current_task else None,
            "error_count": self.error_count,
            "task_history_count": len(self.task_history),
            "context_session_id": self.context.session_id if self.context else None
        }

    def create_task(self, task_type: TaskType, input_data: Dict[str, Any]) -> AgentTask:
        """
        Create a new task for execution.
        
        Args:
            task_type: Type of task to create
            input_data: Input parameters for the task
            
        Returns:
            Created AgentTask object
        """
        task = AgentTask(
            id=f"task_{uuid.uuid4().hex[:8]}",
            type=task_type,
            input=input_data
        )
        
        self.logger.info(f"Created task {task.id} of type {task_type.value}")
        return task

    def execute_task(self, task: AgentTask) -> Dict[str, Any]:
        """
        Execute a task with error handling and status reporting.
        
        Args:
            task: AgentTask to execute
            
        Returns:
            Task execution result
            
        Raises:
            Exception: If task execution fails after max retries
        """
        self.current_task = task
        self.status = AgentStatus.PROCESSING
        task.start_task()
        
        self.logger.info(f"Starting execution of task {task.id}")
        
        retry_count = 0
        while retry_count <= self.max_retries:
            try:
                # Execute the specific task logic
                result = self._execute_task_logic(task)
                
                # Mark task as completed
                task.complete_task(result)
                self.status = AgentStatus.COMPLETED
                self.task_history.append(task)
                
                # Update context if available
                if self.context:
                    self.context.complete_task(task.id)
                
                self.logger.info(f"Successfully completed task {task.id}")
                return result
                
            except Exception as e:
                retry_count += 1
                self.error_count += 1
                self.last_error_time = datetime.now()
                
                # Use comprehensive error handler
                error_context = ErrorContext(
                    session_id=self.context.session_id if self.context else None,
                    agent_type=self.agent_type,
                    task_id=task.id,
                    conversation_stage=self.context.conversation_stage if self.context else None,
                    additional_data={
                        'retry_count': retry_count,
                        'max_retries': self.max_retries,
                        'task_type': task.type.value
                    }
                )
                
                error_result = self.error_handler.handle_agent_error(
                    agent_type=self.agent_type,
                    task_id=task.id,
                    error=e,
                    session_id=self.context.session_id if self.context else None,
                    conversation_context=self.context
                )
                
                self.logger.error(f"Task execution failed (attempt {retry_count}): {str(e)}")
                
                if retry_count > self.max_retries:
                    # Final failure - use error handler result
                    task.fail_task(f"Task failed after {self.max_retries} retries: {error_result.customer_message}")
                    self.status = AgentStatus.ERROR
                    self.task_history.append(task)
                    
                    # Attempt recovery if possible
                    if error_result.retry_possible and self.recovery_attempts < self.max_recovery_attempts:
                        recovery_success = self._attempt_recovery(task, error_result)
                        if recovery_success:
                            continue  # Retry the task
                    
                    # If escalation is required, log it
                    if error_result.escalation_required:
                        self.logger.critical(f"Task {task.id} requires escalation: {str(e)}")
                    
                    raise Exception(f"Task {task.id} failed after {self.max_retries} retries: {error_result.customer_message}")
                
                # Wait before retry (exponential backoff)
                import time
                backoff_time = min(2 ** (retry_count - 1), 30)  # Cap at 30 seconds
                time.sleep(backoff_time)
        
        # This should never be reached, but included for completeness
        raise Exception(f"Unexpected error in task execution for {task.id}")

    @abstractmethod
    def _execute_task_logic(self, task: AgentTask) -> Dict[str, Any]:
        """
        Abstract method for specific task execution logic.
        Must be implemented by concrete agent classes.
        
        Args:
            task: AgentTask to execute
            
        Returns:
            Task execution result
        """
        pass

    def handle_error(self, error: Exception, context: Optional[Dict[str, Any]] = None,
                    error_category: ErrorCategory = ErrorCategory.AGENT_FAILURE) -> ErrorHandlingResult:
        """
        Handle errors with comprehensive error handling and recovery.
        
        Args:
            error: Exception that occurred
            context: Optional additional context information
            error_category: Category of the error
            
        Returns:
            Error handling result
        """
        self.error_count += 1
        self.status = AgentStatus.ERROR
        self.last_error_time = datetime.now()
        
        # Create error context
        error_context = ErrorContext(
            session_id=self.context.session_id if self.context else None,
            agent_type=self.agent_type,
            conversation_stage=self.context.conversation_stage if self.context else None,
            additional_data={
                "agent_id": self.agent_id,
                "error_count": self.error_count,
                "additional_context": context or {}
            }
        )
        
        # Use comprehensive error handler
        error_result = self.error_handler.handle_error(
            error=error,
            error_category=error_category,
            error_context=error_context,
            conversation_context=self.context
        )
        
        self.logger.error(f"Agent {self.agent_id} encountered error: {str(error)}")
        
        # Attempt recovery if possible
        if error_result.retry_possible and self.recovery_attempts < self.max_recovery_attempts:
            self._attempt_recovery(None, error_result)
        
        return error_result

    def reset_agent(self) -> None:
        """Reset agent to initial state"""
        self.status = AgentStatus.IDLE
        self.current_task = None
        self.error_count = 0
        self.task_history.clear()
        
        self.logger.info(f"Agent {self.agent_id} reset to initial state")

    def get_task_history(self) -> List[Dict[str, Any]]:
        """
        Get history of executed tasks.
        
        Returns:
            List of task dictionaries
        """
        return [task.to_dict() for task in self.task_history]

    def can_execute_task(self, task_type: TaskType) -> bool:
        """
        Check if this agent can execute a specific task type.
        Default implementation returns False - should be overridden by concrete agents.
        
        Args:
            task_type: Type of task to check
            
        Returns:
            True if agent can execute the task, False otherwise
        """
        return False

    def share_context_data(self, key: str, value: Any) -> None:
        """
        Share data with other agents through conversation context.
        
        Args:
            key: Data key
            value: Data value to share
        """
        if self.context:
            self.context.add_collected_data(key, value)
            self.logger.info(f"Shared context data: {key}")
        else:
            self.logger.warning("No context available for data sharing")

    def get_shared_data(self, key: str) -> Optional[Any]:
        """
        Get shared data from conversation context.
        
        Args:
            key: Data key to retrieve
            
        Returns:
            Shared data value or None if not found
        """
        if self.context and key in self.context.collected_data:
            return self.context.collected_data[key]['value']
        return None

    def __str__(self) -> str:
        """String representation of the agent"""
        return f"{self.agent_type.value.title()}Agent(id={self.agent_id}, status={self.status.value})"

    def _attempt_recovery(self, failed_task: Optional[AgentTask] = None, 
                        error_result: Optional[ErrorHandlingResult] = None) -> bool:
        """
        Attempt to recover from error using recovery actions.
        
        Args:
            failed_task: Task that failed (if any)
            error_result: Error handling result with recovery actions
            
        Returns:
            True if recovery was successful, False otherwise
        """
        if not error_result or not error_result.recovery_actions:
            return False
        
        self.recovery_attempts += 1
        
        try:
            for action in error_result.recovery_actions:
                if action == 'restart_agent':
                    self._restart_agent()
                elif action == 'reset_task':
                    if failed_task:
                        failed_task.status = TaskStatus.PENDING
                        failed_task.error = None
                elif action == 'clear_context':
                    self._clear_error_context()
                elif action == 'retry_operation':
                    # This will be handled by the calling method
                    pass
                elif action == 'notify_customer':
                    self._notify_customer_of_recovery(error_result.customer_message)
            
            self.logger.info(f"Recovery attempt {self.recovery_attempts} completed for agent {self.agent_id}")
            return True
            
        except Exception as recovery_error:
            self.logger.error(f"Recovery attempt failed: {str(recovery_error)}")
            return False
    
    def _restart_agent(self) -> None:
        """Restart agent to clean state"""
        self.status = AgentStatus.IDLE
        self.current_task = None
        # Don't reset error_count to maintain statistics
        self.logger.info(f"Agent {self.agent_id} restarted")
    
    def _clear_error_context(self) -> None:
        """Clear error-related context data"""
        if self.context:
            # Remove recent errors from context (keep last 3 for debugging)
            if len(self.context.errors) > 3:
                self.context.errors = self.context.errors[-3:]
        
        self.logger.info(f"Error context cleared for agent {self.agent_id}")
    
    def _notify_customer_of_recovery(self, message: str) -> None:
        """Notify customer of recovery attempt"""
        if self.context:
            self.share_context_data('recovery_message', {
                'message': message,
                'timestamp': datetime.now().isoformat(),
                'agent_id': self.agent_id
            })
        
        self.logger.info(f"Customer notified of recovery: {message}")
    
    def get_error_summary(self) -> Dict[str, Any]:
        """
        Get summary of agent errors and recovery attempts.
        
        Returns:
            Dictionary containing error summary
        """
        return {
            'agent_id': self.agent_id,
            'agent_type': self.agent_type.value,
            'total_errors': self.error_count,
            'recovery_attempts': self.recovery_attempts,
            'last_error_time': self.last_error_time.isoformat() if self.last_error_time else None,
            'current_status': self.status.value,
            'context_errors': len(self.context.errors) if self.context else 0
        }
    
    def is_healthy(self) -> bool:
        """
        Check if agent is in a healthy state.
        
        Returns:
            True if agent is healthy, False otherwise
        """
        # Agent is unhealthy if:
        # 1. Too many errors in short time
        # 2. Status is ERROR for too long
        # 3. Recovery attempts exceeded
        
        if self.error_count > 10:  # Too many total errors
            return False
        
        if self.recovery_attempts >= self.max_recovery_attempts:
            return False
        
        if self.status == AgentStatus.ERROR:
            # Check if error state is too long
            if self.last_error_time:
                time_since_error = datetime.now() - self.last_error_time
                if time_since_error.total_seconds() > 300:  # 5 minutes
                    return False
        
        return True

    def __repr__(self) -> str:
        """Detailed string representation of the agent"""
        return (f"{self.__class__.__name__}(agent_type={self.agent_type.value}, "
                f"agent_id={self.agent_id}, status={self.status.value}, "
                f"error_count={self.error_count}, recovery_attempts={self.recovery_attempts})")