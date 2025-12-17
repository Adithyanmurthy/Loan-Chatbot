"""
Tests for the base agent framework
Tests task execution interface, status reporting, error handling, and context sharing
"""

import pytest
import tempfile
import shutil
from unittest.mock import Mock, patch
from datetime import datetime

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.base_agent import BaseAgent, AgentStatus
from agents.context_manager import ContextManager
from agents.session_manager import SessionManager
from models.conversation import ConversationContext, AgentType, TaskType, AgentTask


class TestAgent(BaseAgent):
    """Test implementation of BaseAgent for testing purposes"""
    
    def __init__(self):
        super().__init__(AgentType.SALES)
    
    def _execute_task_logic(self, task: AgentTask):
        """Simple test task execution"""
        if task.input.get('should_fail'):
            raise Exception("Test failure")
        
        return {
            'result': 'success',
            'processed_data': task.input.get('data', 'default')
        }
    
    def can_execute_task(self, task_type: TaskType) -> bool:
        """This test agent can execute sales tasks"""
        return task_type == TaskType.SALES


class TestBaseAgent:
    """Test cases for BaseAgent functionality"""
    
    def test_agent_initialization(self):
        """Test agent initialization"""
        agent = TestAgent()
        
        assert agent.agent_type == AgentType.SALES
        assert agent.status == AgentStatus.IDLE
        assert agent.current_task is None
        assert agent.error_count == 0
        assert len(agent.task_history) == 0

    def test_task_creation(self):
        """Test task creation"""
        agent = TestAgent()
        
        input_data = {'data': 'test_data'}
        task = agent.create_task(TaskType.SALES, input_data)
        
        assert task.type == TaskType.SALES
        assert task.input == input_data
        assert task.status.value == 'pending'

    def test_successful_task_execution(self):
        """Test successful task execution"""
        agent = TestAgent()
        
        input_data = {'data': 'test_data'}
        task = agent.create_task(TaskType.SALES, input_data)
        
        result = agent.execute_task(task)
        
        assert result['result'] == 'success'
        assert result['processed_data'] == 'test_data'
        assert task.status.value == 'completed'
        assert agent.status == AgentStatus.COMPLETED
        assert len(agent.task_history) == 1

    def test_task_execution_failure(self):
        """Test task execution failure and retry logic"""
        agent = TestAgent()
        
        input_data = {'should_fail': True}
        task = agent.create_task(TaskType.SALES, input_data)
        
        with pytest.raises(Exception):
            agent.execute_task(task)
        
        assert task.status.value == 'failed'
        assert agent.status == AgentStatus.ERROR
        assert agent.error_count > 0

    def test_context_sharing(self):
        """Test context sharing functionality"""
        agent = TestAgent()
        
        # Create a mock context
        context = ConversationContext(
            session_id="test_session",
            conversation_stage="test_stage"
        )
        
        agent.set_context(context)
        
        # Test sharing data
        agent.share_context_data('test_key', 'test_value')
        
        # Test retrieving shared data
        retrieved_value = agent.get_shared_data('test_key')
        assert retrieved_value == 'test_value'

    def test_agent_status_reporting(self):
        """Test agent status reporting"""
        agent = TestAgent()
        
        status = agent.get_status()
        
        assert status['agent_type'] == 'sales'
        assert status['status'] == 'idle'
        assert status['error_count'] == 0
        assert status['current_task_id'] is None


class TestContextManager:
    """Test cases for ContextManager functionality"""
    
    def setup_method(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.context_manager = ContextManager(storage_path=self.temp_dir)
    
    def teardown_method(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir)

    def test_session_creation(self):
        """Test session creation"""
        context = self.context_manager.create_session(customer_id="test_customer")
        
        assert context.session_id is not None
        assert context.customer_id == "test_customer"
        assert context.current_agent == AgentType.MASTER
        assert context.conversation_stage == "initiation"

    def test_context_persistence_and_retrieval(self):
        """Test context persistence and retrieval"""
        # Create context
        context = self.context_manager.create_session(customer_id="test_customer")
        session_id = context.session_id
        
        # Add some data
        context.add_collected_data('test_key', 'test_value')
        self.context_manager.update_context(context)
        
        # Retrieve context
        retrieved_context = self.context_manager.get_context(session_id)
        
        assert retrieved_context is not None
        assert retrieved_context.session_id == session_id
        assert retrieved_context.customer_id == "test_customer"
        assert 'test_key' in retrieved_context.collected_data

    def test_context_sharing_between_agents(self):
        """Test context sharing between agents"""
        context = self.context_manager.create_session()
        session_id = context.session_id
        
        # Share data from sales to verification agent
        data_to_share = {'loan_amount': 100000, 'tenure': 24}
        success = self.context_manager.share_context_between_agents(
            session_id, 'sales', 'verification', data_to_share
        )
        
        assert success is True
        
        # Retrieve shared data
        shared_data = self.context_manager.get_shared_data(session_id, 'verification', 'sales')
        
        assert shared_data['loan_amount'] == 100000
        assert shared_data['tenure'] == 24

    def test_context_recovery(self):
        """Test context recovery functionality"""
        # Create and persist context
        context = self.context_manager.create_session(customer_id="recovery_test")
        session_id = context.session_id
        
        # Clear active contexts to simulate system restart
        self.context_manager.active_contexts.clear()
        
        # Attempt recovery
        recovered_context = self.context_manager.recover_context(session_id)
        
        assert recovered_context is not None
        assert recovered_context.session_id == session_id
        assert recovered_context.customer_id == "recovery_test"


class TestSessionManager:
    """Test cases for SessionManager functionality"""
    
    def setup_method(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        context_manager = ContextManager(storage_path=self.temp_dir)
        self.session_manager = SessionManager(context_manager)
    
    def teardown_method(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir)

    def test_session_start_and_agent_registration(self):
        """Test session start and agent registration"""
        # Start session
        context = self.session_manager.start_session(customer_id="test_customer")
        session_id = context.session_id
        
        # Create and register agent
        agent = TestAgent()
        success = self.session_manager.register_agent(session_id, agent)
        
        assert success is True
        
        # Retrieve agent
        retrieved_agent = self.session_manager.get_agent(session_id, AgentType.SALES)
        assert retrieved_agent is not None
        assert retrieved_agent.agent_type == AgentType.SALES

    def test_agent_switching(self):
        """Test agent switching functionality"""
        # Start session and register agents
        context = self.session_manager.start_session()
        session_id = context.session_id
        
        sales_agent = TestAgent()
        self.session_manager.register_agent(session_id, sales_agent)
        
        # Switch to sales agent
        success = self.session_manager.switch_agent(session_id, AgentType.SALES, "sales_negotiation")
        
        assert success is True
        
        # Verify context update
        updated_context = self.session_manager.get_session_context(session_id)
        assert updated_context.current_agent == AgentType.SALES
        assert updated_context.conversation_stage == "sales_negotiation"

    def test_task_execution_through_session_manager(self):
        """Test task execution through session manager"""
        # Start session and register agent
        context = self.session_manager.start_session()
        session_id = context.session_id
        
        agent = TestAgent()
        self.session_manager.register_agent(session_id, agent)
        
        # Execute task
        input_data = {'data': 'session_test'}
        result = self.session_manager.execute_agent_task(
            session_id, AgentType.SALES, TaskType.SALES, input_data
        )
        
        assert result is not None
        assert result['result'] == 'success'
        assert result['processed_data'] == 'session_test'

    def test_data_sharing_between_agents(self):
        """Test data sharing between agents through session manager"""
        # Start session
        context = self.session_manager.start_session()
        session_id = context.session_id
        
        # Share data
        data_to_share = {'customer_verified': True, 'verification_score': 95}
        success = self.session_manager.share_data_between_agents(
            session_id, AgentType.VERIFICATION, AgentType.UNDERWRITING, data_to_share
        )
        
        assert success is True
        
        # Retrieve shared data
        shared_data = self.session_manager.get_shared_data(
            session_id, AgentType.UNDERWRITING, AgentType.VERIFICATION
        )
        
        assert shared_data['customer_verified'] is True
        assert shared_data['verification_score'] == 95

    def test_session_end_and_cleanup(self):
        """Test session end and cleanup"""
        # Start session and register agent
        context = self.session_manager.start_session()
        session_id = context.session_id
        
        agent = TestAgent()
        self.session_manager.register_agent(session_id, agent)
        
        # End session
        success = self.session_manager.end_session(session_id)
        
        assert success is True
        
        # Verify cleanup
        assert session_id not in self.session_manager.session_agents
        
        # Verify context is marked as completed
        final_context = self.session_manager.get_session_context(session_id)
        assert final_context.conversation_stage == "completion"


if __name__ == "__main__":
    # Run tests without pytest to avoid Flask compatibility issues
    import unittest
    unittest.main()