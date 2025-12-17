"""
Simple test runner for agent framework without pytest dependencies
"""

import sys
import os
import tempfile
import shutil
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

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


def test_base_agent():
    """Test BaseAgent functionality"""
    print("Testing BaseAgent...")
    
    # Test initialization
    agent = TestAgent()
    assert agent.agent_type == AgentType.SALES
    assert agent.status == AgentStatus.IDLE
    print("✓ Agent initialization works")
    
    # Test task creation
    input_data = {'data': 'test_data'}
    task = agent.create_task(TaskType.SALES, input_data)
    assert task.type == TaskType.SALES
    assert task.input == input_data
    print("✓ Task creation works")
    
    # Test successful task execution
    result = agent.execute_task(task)
    assert result['result'] == 'success'
    assert result['processed_data'] == 'test_data'
    assert agent.status == AgentStatus.COMPLETED
    print("✓ Task execution works")
    
    # Test context sharing
    context = ConversationContext(
        session_id="test_session",
        conversation_stage="initiation"
    )
    agent.set_context(context)
    agent.share_context_data('test_key', 'test_value')
    retrieved_value = agent.get_shared_data('test_key')
    assert retrieved_value == 'test_value'
    print("✓ Context sharing works")
    
    print("BaseAgent tests passed!\n")


def test_context_manager():
    """Test ContextManager functionality"""
    print("Testing ContextManager...")
    
    # Set up temporary directory
    temp_dir = tempfile.mkdtemp()
    
    try:
        context_manager = ContextManager(storage_path=temp_dir)
        
        # Test session creation
        context = context_manager.create_session(customer_id="test_customer")
        assert context.session_id is not None
        assert context.customer_id == "test_customer"
        print("✓ Session creation works")
        
        # Test context persistence and retrieval
        session_id = context.session_id
        context.add_collected_data('test_key', 'test_value')
        context_manager.update_context(context)
        
        retrieved_context = context_manager.get_context(session_id)
        assert retrieved_context is not None
        assert retrieved_context.session_id == session_id
        assert 'test_key' in retrieved_context.collected_data
        print("✓ Context persistence and retrieval works")
        
        # Test context sharing between agents
        data_to_share = {'loan_amount': 100000, 'tenure': 24}
        success = context_manager.share_context_between_agents(
            session_id, 'sales', 'verification', data_to_share
        )
        assert success is True
        
        shared_data = context_manager.get_shared_data(session_id, 'verification', 'sales')
        assert shared_data['loan_amount'] == 100000
        print("✓ Context sharing between agents works")
        
        print("ContextManager tests passed!\n")
        
    finally:
        # Clean up
        shutil.rmtree(temp_dir)


def test_session_manager():
    """Test SessionManager functionality"""
    print("Testing SessionManager...")
    
    # Set up temporary directory
    temp_dir = tempfile.mkdtemp()
    
    try:
        context_manager = ContextManager(storage_path=temp_dir)
        session_manager = SessionManager(context_manager)
        
        # Test session start and agent registration
        context = session_manager.start_session(customer_id="test_customer")
        session_id = context.session_id
        
        agent = TestAgent()
        success = session_manager.register_agent(session_id, agent)
        assert success is True
        
        retrieved_agent = session_manager.get_agent(session_id, AgentType.SALES)
        assert retrieved_agent is not None
        print("✓ Session start and agent registration works")
        
        # Test agent switching
        success = session_manager.switch_agent(session_id, AgentType.SALES, "sales_negotiation")
        assert success is True
        
        updated_context = session_manager.get_session_context(session_id)
        assert updated_context.current_agent == AgentType.SALES
        assert updated_context.conversation_stage == "sales_negotiation"
        print("✓ Agent switching works")
        
        # Test task execution through session manager
        input_data = {'data': 'session_test'}
        result = session_manager.execute_agent_task(
            session_id, AgentType.SALES, TaskType.SALES, input_data
        )
        assert result is not None
        assert result['result'] == 'success'
        print("✓ Task execution through session manager works")
        
        # Test data sharing between agents
        data_to_share = {'customer_verified': True, 'verification_score': 95}
        success = session_manager.share_data_between_agents(
            session_id, AgentType.VERIFICATION, AgentType.UNDERWRITING, data_to_share
        )
        assert success is True
        
        shared_data = session_manager.get_shared_data(
            session_id, AgentType.UNDERWRITING, AgentType.VERIFICATION
        )
        assert shared_data['customer_verified'] is True
        print("✓ Data sharing between agents works")
        
        # Test session end
        success = session_manager.end_session(session_id)
        assert success is True
        assert session_id not in session_manager.session_agents
        print("✓ Session end and cleanup works")
        
        print("SessionManager tests passed!\n")
        
    finally:
        # Clean up
        shutil.rmtree(temp_dir)


def main():
    """Run all tests"""
    print("Running Agent Framework Tests...\n")
    
    try:
        test_base_agent()
        test_context_manager()
        test_session_manager()
        
        print("🎉 All tests passed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)