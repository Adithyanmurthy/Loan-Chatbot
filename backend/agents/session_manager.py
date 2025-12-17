"""
Session Management System
Provides high-level session management functionality for agent coordination
Based on requirements: 1.4, 6.1, 6.2
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from models.conversation import ConversationContext, AgentType, AgentTask, TaskType
from .context_manager import ContextManager
from .base_agent import BaseAgent


class SessionManager:
    """
    High-level session management for coordinating agents and maintaining
    conversation state across the loan processing workflow.
    """
    
    def __init__(self, context_manager: Optional[ContextManager] = None):
        """
        Initialize session manager with context management.
        
        Args:
            context_manager: Optional ContextManager instance
        """
        self.context_manager = context_manager or ContextManager()
        
        # Registry of active agents by session
        self.session_agents: Dict[str, Dict[str, BaseAgent]] = {}
        
        # Set up logging
        self.logger = logging.getLogger("session_manager")
        self.logger.setLevel(logging.INFO)
        
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        
        self.logger.info("SessionManager initialized")

    def start_session(self, customer_id: Optional[str] = None) -> ConversationContext:
        """
        Start a new conversation session.
        
        Args:
            customer_id: Optional customer identifier
            
        Returns:
            New ConversationContext object
        """
        context = self.context_manager.create_session(customer_id)
        
        # Initialize agent registry for this session
        self.session_agents[context.session_id] = {}
        
        self.logger.info(f"Started new session: {context.session_id}")
        return context

    def get_session_context(self, session_id: str) -> Optional[ConversationContext]:
        """
        Get conversation context for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            ConversationContext if found, None otherwise
        """
        return self.context_manager.get_context(session_id)

    def register_agent(self, session_id: str, agent: BaseAgent) -> bool:
        """
        Register an agent for a specific session.
        
        Args:
            session_id: Session identifier
            agent: BaseAgent instance to register
            
        Returns:
            True if registration successful, False otherwise
        """
        context = self.get_session_context(session_id)
        if not context:
            self.logger.error(f"Cannot register agent - session {session_id} not found")
            return False
        
        # Set context for the agent
        agent.set_context(context)
        
        # Register agent
        if session_id not in self.session_agents:
            self.session_agents[session_id] = {}
        
        self.session_agents[session_id][agent.agent_type.value] = agent
        
        self.logger.info(f"Registered {agent.agent_type.value} agent for session {session_id}")
        return True

    def get_agent(self, session_id: str, agent_type: AgentType) -> Optional[BaseAgent]:
        """
        Get a specific agent for a session. Auto-creates if not found.
        
        Args:
            session_id: Session identifier
            agent_type: Type of agent to retrieve
            
        Returns:
            BaseAgent instance if found, None otherwise
        """
        if session_id not in self.session_agents:
            return None
        
        # Check if agent already exists
        existing_agent = self.session_agents[session_id].get(agent_type.value)
        if existing_agent:
            return existing_agent
        
        # Auto-create worker agents if they don't exist
        if agent_type != AgentType.MASTER:
            new_agent = self._create_worker_agent(agent_type)
            if new_agent:
                self.register_agent(session_id, new_agent)
                return new_agent
        
        return None
    
    def _create_worker_agent(self, agent_type: AgentType) -> Optional[BaseAgent]:
        """Create a worker agent instance based on type"""
        try:
            if agent_type == AgentType.SALES:
                from .sales_agent import SalesAgent
                return SalesAgent()
            elif agent_type == AgentType.VERIFICATION:
                from .verification_agent import VerificationAgent
                return VerificationAgent()
            elif agent_type == AgentType.UNDERWRITING:
                from .underwriting_agent import UnderwritingAgent
                return UnderwritingAgent()
            elif agent_type == AgentType.SANCTION:
                from .sanction_letter_agent import SanctionLetterAgent
                return SanctionLetterAgent()
            else:
                self.logger.error(f"Unknown agent type: {agent_type}")
                return None
        except Exception as e:
            self.logger.error(f"Failed to create {agent_type.value} agent: {e}")
            return None

    def switch_agent(self, session_id: str, new_agent_type: AgentType, 
                    new_stage: str) -> bool:
        """
        Switch the active agent for a session.
        
        Args:
            session_id: Session identifier
            new_agent_type: Type of agent to switch to
            new_stage: New conversation stage
            
        Returns:
            True if switch successful, False otherwise
        """
        context = self.get_session_context(session_id)
        if not context:
            self.logger.error(f"Cannot switch agent - session {session_id} not found")
            return False
        
        # Check if target agent is registered
        target_agent = self.get_agent(session_id, new_agent_type)
        if not target_agent:
            self.logger.error(f"Target agent {new_agent_type.value} not registered for session {session_id}")
            return False
        
        # Update context
        old_agent_type = context.current_agent
        context.switch_agent(new_agent_type, new_stage)
        
        # Update context in storage
        self.context_manager.update_context(context)
        
        # Update agent context
        target_agent.set_context(context)
        
        self.logger.info(f"Switched from {old_agent_type.value} to {new_agent_type.value} agent in session {session_id}")
        return True

    def execute_agent_task(self, session_id: str, agent_type: AgentType, 
                          task_type: TaskType, input_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Execute a task using a specific agent.
        
        Args:
            session_id: Session identifier
            agent_type: Type of agent to use
            task_type: Type of task to execute
            input_data: Task input parameters
            
        Returns:
            Task execution result or None if failed
        """
        context = self.get_session_context(session_id)
        if not context:
            self.logger.error(f"Cannot execute task - session {session_id} not found")
            return None
        
        agent = self.get_agent(session_id, agent_type)
        if not agent:
            self.logger.error(f"Agent {agent_type.value} not found for session {session_id}")
            return None
        
        try:
            # Create and execute task
            task = agent.create_task(task_type, input_data)
            
            # Add task to context
            context.add_pending_task(task.id)
            self.context_manager.update_context(context)
            
            # Execute task
            result = agent.execute_task(task)
            
            # Update context after successful execution
            updated_context = self.get_session_context(session_id)
            if updated_context:
                self.context_manager.update_context(updated_context)
            
            self.logger.info(f"Successfully executed {task_type.value} task in session {session_id}")
            return result
            
        except Exception as e:
            self.logger.error(f"Task execution failed in session {session_id}: {str(e)}")
            return None

    def share_data_between_agents(self, session_id: str, source_agent_type: AgentType,
                                 target_agent_type: AgentType, data: Dict[str, Any]) -> bool:
        """
        Share data between agents in a session.
        
        Args:
            session_id: Session identifier
            source_agent_type: Source agent type
            target_agent_type: Target agent type
            data: Data to share
            
        Returns:
            True if sharing successful, False otherwise
        """
        return self.context_manager.share_context_between_agents(
            session_id, 
            source_agent_type.value, 
            target_agent_type.value, 
            data
        )

    def get_shared_data(self, session_id: str, target_agent_type: AgentType,
                       source_agent_type: Optional[AgentType] = None) -> Dict[str, Any]:
        """
        Get shared data for an agent.
        
        Args:
            session_id: Session identifier
            target_agent_type: Agent requesting the data
            source_agent_type: Optional specific source agent
            
        Returns:
            Dictionary of shared data
        """
        source_agent_str = source_agent_type.value if source_agent_type else None
        return self.context_manager.get_shared_data(
            session_id, 
            target_agent_type.value, 
            source_agent_str
        )

    def update_conversation_stage(self, session_id: str, new_stage: str) -> bool:
        """
        Update the conversation stage for a session.
        
        Args:
            session_id: Session identifier
            new_stage: New conversation stage
            
        Returns:
            True if update successful, False otherwise
        """
        context = self.get_session_context(session_id)
        if not context:
            return False
        
        old_stage = context.conversation_stage
        context.conversation_stage = new_stage
        
        self.context_manager.update_context(context)
        
        self.logger.info(f"Updated conversation stage from '{old_stage}' to '{new_stage}' in session {session_id}")
        return True

    def add_session_data(self, session_id: str, key: str, value: Any) -> bool:
        """
        Add data to session context.
        
        Args:
            session_id: Session identifier
            key: Data key
            value: Data value
            
        Returns:
            True if successful, False otherwise
        """
        context = self.get_session_context(session_id)
        if not context:
            return False
        
        context.add_collected_data(key, value)
        self.context_manager.update_context(context)
        
        return True

    def get_session_data(self, session_id: str, key: str) -> Optional[Any]:
        """
        Get data from session context.
        
        Args:
            session_id: Session identifier
            key: Data key
            
        Returns:
            Data value or None if not found
        """
        context = self.get_session_context(session_id)
        if not context or key not in context.collected_data:
            return None
        
        return context.collected_data[key]['value']

    def end_session(self, session_id: str) -> bool:
        """
        End a conversation session and clean up resources.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if successful, False otherwise
        """
        context = self.get_session_context(session_id)
        if not context:
            return False
        
        # Update stage to completion
        context.conversation_stage = "completion"
        self.context_manager.update_context(context)
        
        # Clean up agent registry
        if session_id in self.session_agents:
            # Reset all agents
            for agent in self.session_agents[session_id].values():
                agent.reset_agent()
            
            del self.session_agents[session_id]
        
        self.logger.info(f"Ended session: {session_id}")
        return True

    def recover_session(self, session_id: str) -> Optional[ConversationContext]:
        """
        Recover a session after system restart or failure.
        
        Args:
            session_id: Session identifier to recover
            
        Returns:
            Recovered ConversationContext or None if recovery fails
        """
        context = self.context_manager.recover_context(session_id)
        if context:
            # Reinitialize agent registry
            self.session_agents[session_id] = {}
            self.logger.info(f"Recovered session: {session_id}")
        
        return context

    def get_session_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive session statistics.
        
        Returns:
            Dictionary containing session statistics
        """
        context_stats = self.context_manager.get_session_statistics()
        
        # Add agent registry statistics
        agent_registry_stats = {
            'sessions_with_agents': len(self.session_agents),
            'total_registered_agents': sum(len(agents) for agents in self.session_agents.values())
        }
        
        return {
            **context_stats,
            'agent_registry': agent_registry_stats
        }

    def list_active_sessions(self, customer_id: Optional[str] = None, 
                           limit: int = 50) -> List[ConversationContext]:
        """
        List active sessions, optionally filtered by customer ID.
        
        Args:
            customer_id: Optional customer ID filter
            limit: Maximum number of sessions to return
            
        Returns:
            List of active ConversationContext objects
        """
        try:
            # Get all active sessions from context manager
            all_sessions = self.context_manager.get_all_active_contexts()
            
            # Filter by customer_id if provided
            if customer_id:
                filtered_sessions = [
                    context for context in all_sessions 
                    if context.customer_id == customer_id
                ]
            else:
                filtered_sessions = all_sessions
            
            # Sort by creation time (newest first) and apply limit
            sorted_sessions = sorted(
                filtered_sessions,
                key=lambda x: x.created_at or datetime.min,
                reverse=True
            )
            
            return sorted_sessions[:limit]
            
        except Exception as e:
            self.logger.error(f"Error listing active sessions: {e}")
            return []

    def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions.
        
        Returns:
            Number of sessions cleaned up
        """
        # Clean up context manager
        cleaned_contexts = self.context_manager.cleanup_expired_sessions()
        
        # Clean up agent registry for non-existent sessions
        active_sessions = set(self.context_manager.get_active_sessions())
        registry_sessions = set(self.session_agents.keys())
        
        orphaned_sessions = registry_sessions - active_sessions
        for session_id in orphaned_sessions:
            del self.session_agents[session_id]
        
        total_cleaned = cleaned_contexts + len(orphaned_sessions)
        
        if total_cleaned > 0:
            self.logger.info(f"Cleaned up {total_cleaned} expired sessions")
        
        return total_cleaned