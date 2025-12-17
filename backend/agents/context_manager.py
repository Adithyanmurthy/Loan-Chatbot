"""
Conversation Context Management System
Implements state persistence, session management, and context recovery
Based on requirements: 1.4, 6.1, 6.2
"""

import json
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from pathlib import Path
import logging

from models.conversation import ConversationContext, AgentType, ErrorSeverity


class ContextManager:
    """
    Manages conversation contexts with persistence, session management,
    and context recovery capabilities.
    """
    
    def __init__(self, storage_path: str = "data/contexts"):
        """
        Initialize context manager with storage configuration.
        
        Args:
            storage_path: Directory path for storing context files
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # In-memory context cache for active sessions
        self.active_contexts: Dict[str, ConversationContext] = {}
        
        # Session timeout (in minutes)
        self.session_timeout = 30
        
        # Set up logging
        self.logger = logging.getLogger("context_manager")
        self.logger.setLevel(logging.INFO)
        
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        
        self.logger.info(f"ContextManager initialized with storage: {self.storage_path}")

    def create_session(self, customer_id: Optional[str] = None) -> ConversationContext:
        """
        Create a new conversation session with unique session ID.
        
        Args:
            customer_id: Optional customer identifier
            
        Returns:
            New ConversationContext object
        """
        session_id = f"session_{uuid.uuid4().hex[:12]}"
        
        context = ConversationContext(
            session_id=session_id,
            customer_id=customer_id,
            current_agent=AgentType.MASTER,
            conversation_stage="initiation",
            collected_data={},
            pending_tasks=[],
            completed_tasks=[],
            errors=[]
        )
        
        # Store in active contexts cache
        self.active_contexts[session_id] = context
        
        # Persist to storage
        self._persist_context(context)
        
        self.logger.info(f"Created new session: {session_id} for customer: {customer_id}")
        return context

    def get_context(self, session_id: str) -> Optional[ConversationContext]:
        """
        Retrieve conversation context by session ID.
        First checks active cache, then attempts to load from storage.
        
        Args:
            session_id: Session identifier
            
        Returns:
            ConversationContext if found, None otherwise
        """
        # Check active contexts first
        if session_id in self.active_contexts:
            context = self.active_contexts[session_id]
            
            # Check if session has expired
            if self._is_session_expired(context):
                self.logger.warning(f"Session {session_id} has expired")
                self._cleanup_session(session_id)
                return None
            
            return context
        
        # Try to load from storage
        context = self._load_context_from_storage(session_id)
        if context:
            # Check if session has expired
            if self._is_session_expired(context):
                self.logger.warning(f"Loaded session {session_id} has expired")
                self._cleanup_session(session_id)
                return None
            
            # Add to active contexts
            self.active_contexts[session_id] = context
            self.logger.info(f"Loaded context from storage for session: {session_id}")
            return context
        
        self.logger.warning(f"Context not found for session: {session_id}")
        return None

    def update_context(self, context: ConversationContext) -> None:
        """
        Update conversation context in both cache and persistent storage.
        
        Args:
            context: Updated ConversationContext object
        """
        session_id = context.session_id
        
        # Update active cache
        self.active_contexts[session_id] = context
        
        # Persist to storage
        self._persist_context(context)
        
        self.logger.debug(f"Updated context for session: {session_id}")

    def share_context_between_agents(self, session_id: str, source_agent: str, 
                                   target_agent: str, data: Dict[str, Any]) -> bool:
        """
        Share context data between agents within the same session.
        
        Args:
            session_id: Session identifier
            source_agent: Agent sharing the data
            target_agent: Agent receiving the data
            data: Data to share
            
        Returns:
            True if sharing successful, False otherwise
        """
        context = self.get_context(session_id)
        if not context:
            self.logger.error(f"Cannot share context - session {session_id} not found")
            return False
        
        # Add shared data with metadata
        for key, value in data.items():
            shared_key = f"shared_{source_agent}_to_{target_agent}_{key}"
            context.add_collected_data(shared_key, {
                'value': value,
                'source_agent': source_agent,
                'target_agent': target_agent,
                'shared_at': datetime.now().isoformat()
            })
        
        # Update context
        self.update_context(context)
        
        self.logger.info(f"Shared context data from {source_agent} to {target_agent} in session {session_id}")
        return True

    def get_shared_data(self, session_id: str, target_agent: str, 
                       source_agent: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieve shared data for a specific agent.
        
        Args:
            session_id: Session identifier
            target_agent: Agent requesting the data
            source_agent: Optional specific source agent filter
            
        Returns:
            Dictionary of shared data
        """
        context = self.get_context(session_id)
        if not context:
            return {}
        
        shared_data = {}
        
        for key, data_entry in context.collected_data.items():
            if key.startswith("shared_") and target_agent in key:
                # Extract the original key name
                parts = key.split("_")
                if len(parts) >= 4:
                    original_key = "_".join(parts[4:])  # Remove "shared_source_to_target_" prefix
                    
                    # Filter by source agent if specified
                    if source_agent is None or source_agent in key:
                        # Extract the actual value from the nested structure
                        if isinstance(data_entry['value'], dict) and 'value' in data_entry['value']:
                            shared_data[original_key] = data_entry['value']['value']
                        else:
                            shared_data[original_key] = data_entry['value']
        
        return shared_data

    def recover_context(self, session_id: str) -> Optional[ConversationContext]:
        """
        Attempt to recover context from storage after system restart or failure.
        
        Args:
            session_id: Session identifier to recover
            
        Returns:
            Recovered ConversationContext or None if recovery fails
        """
        self.logger.info(f"Attempting to recover context for session: {session_id}")
        
        context = self._load_context_from_storage(session_id)
        if context:
            # Check if context is recoverable (not too old)
            if self._is_context_recoverable(context):
                # Add to active contexts
                self.active_contexts[session_id] = context
                
                # Add recovery note to context
                context.add_collected_data("recovery_info", {
                    'recovered_at': datetime.now().isoformat(),
                    'recovery_reason': 'system_restart_or_failure'
                })
                
                self.update_context(context)
                
                self.logger.info(f"Successfully recovered context for session: {session_id}")
                return context
            else:
                self.logger.warning(f"Context for session {session_id} is too old to recover")
                self._cleanup_session(session_id)
        
        return None

    def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions from both cache and storage.
        
        Returns:
            Number of sessions cleaned up
        """
        cleaned_count = 0
        
        # Clean up active contexts
        expired_sessions = []
        for session_id, context in self.active_contexts.items():
            if self._is_session_expired(context):
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            self._cleanup_session(session_id)
            cleaned_count += 1
        
        # Clean up storage files
        storage_cleaned = self._cleanup_storage_files()
        cleaned_count += storage_cleaned
        
        if cleaned_count > 0:
            self.logger.info(f"Cleaned up {cleaned_count} expired sessions")
        
        return cleaned_count

    def get_active_sessions(self) -> List[str]:
        """
        Get list of currently active session IDs.
        
        Returns:
            List of active session IDs
        """
        return list(self.active_contexts.keys())

    def get_session_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about current sessions.
        
        Returns:
            Dictionary containing session statistics
        """
        active_count = len(self.active_contexts)
        
        # Count sessions by stage
        stage_counts = {}
        agent_counts = {}
        
        for context in self.active_contexts.values():
            stage = context.conversation_stage
            agent = context.current_agent.value
            
            stage_counts[stage] = stage_counts.get(stage, 0) + 1
            agent_counts[agent] = agent_counts.get(agent, 0) + 1
        
        return {
            'active_sessions': active_count,
            'sessions_by_stage': stage_counts,
            'sessions_by_agent': agent_counts,
            'storage_path': str(self.storage_path),
            'session_timeout_minutes': self.session_timeout
        }

    def get_all_active_contexts(self) -> List[ConversationContext]:
        """
        Get all active conversation contexts.
        
        Returns:
            List of all active ConversationContext objects
        """
        return list(self.active_contexts.values())

    def _persist_context(self, context: ConversationContext) -> None:
        """Persist context to storage file"""
        file_path = self.storage_path / f"{context.session_id}.json"
        
        try:
            context_data = context.to_dict()
            context_data['last_updated'] = datetime.now().isoformat()
            
            with open(file_path, 'w') as f:
                json.dump(context_data, f, indent=2, default=str)
                
        except Exception as e:
            self.logger.error(f"Failed to persist context {context.session_id}: {str(e)}")

    def _load_context_from_storage(self, session_id: str) -> Optional[ConversationContext]:
        """Load context from storage file"""
        file_path = self.storage_path / f"{session_id}.json"
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r') as f:
                context_data = json.load(f)
            
            # Remove metadata fields that aren't part of the model
            context_data.pop('last_updated', None)
            
            return ConversationContext.from_dict(context_data)
            
        except Exception as e:
            self.logger.error(f"Failed to load context {session_id}: {str(e)}")
            return None

    def _is_session_expired(self, context: ConversationContext) -> bool:
        """Check if session has expired based on timeout"""
        # For now, we'll use a simple timeout check
        # In a real implementation, you might want to track last activity time
        return False  # Simplified - sessions don't expire for now

    def _is_context_recoverable(self, context: ConversationContext) -> bool:
        """Check if context is recoverable (not too old)"""
        # Allow recovery within 24 hours
        recovery_window = timedelta(hours=24)
        
        # Since we don't have creation time in the model, we'll allow all recoveries for now
        return True

    def _cleanup_session(self, session_id: str) -> None:
        """Clean up session from cache and storage"""
        # Remove from active contexts
        self.active_contexts.pop(session_id, None)
        
        # Remove storage file
        file_path = self.storage_path / f"{session_id}.json"
        if file_path.exists():
            try:
                file_path.unlink()
            except Exception as e:
                self.logger.error(f"Failed to delete context file {session_id}: {str(e)}")

    def _cleanup_storage_files(self) -> int:
        """Clean up old storage files"""
        cleaned_count = 0
        
        try:
            for file_path in self.storage_path.glob("*.json"):
                # Check file age
                file_age = datetime.now() - datetime.fromtimestamp(file_path.stat().st_mtime)
                
                # Remove files older than 24 hours
                if file_age > timedelta(hours=24):
                    file_path.unlink()
                    cleaned_count += 1
                    
        except Exception as e:
            self.logger.error(f"Error during storage cleanup: {str(e)}")
        
        return cleaned_count