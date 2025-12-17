#!/usr/bin/env python3
"""
Simple test script to verify error handling implementation
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.error_handler import (
    ComprehensiveErrorHandler, ErrorCategory, ErrorContext, 
    CustomerCommunicationManager, ErrorLogger, ErrorRecoveryManager
)
from agents.base_agent import BaseAgent
from models.conversation import AgentType, ConversationContext


def test_error_handler():
    """Test comprehensive error handler"""
    print("Testing Comprehensive Error Handler...")
    
    # Initialize error handler
    error_handler = ComprehensiveErrorHandler()
    
    # Test error handling
    test_error = Exception("Test API failure")
    error_context = ErrorContext(
        session_id="test_session_123",
        agent_type=AgentType.SALES,
        additional_data={'test': True}
    )
    
    result = error_handler.handle_error(
        error=test_error,
        error_category=ErrorCategory.API_FAILURE,
        error_context=error_context
    )
    
    print(f"✓ Error handled: {result.handled}")
    print(f"✓ Customer message: {result.customer_message}")
    print(f"✓ Recovery actions: {result.recovery_actions}")
    print(f"✓ Escalation required: {result.escalation_required}")
    
    return result.handled


def test_customer_communication():
    """Test customer communication manager"""
    print("\nTesting Customer Communication Manager...")
    
    comm_manager = CustomerCommunicationManager()
    
    # Test different error categories
    categories = [
        ErrorCategory.AGENT_FAILURE,
        ErrorCategory.API_FAILURE,
        ErrorCategory.VALIDATION_ERROR,
        ErrorCategory.NETWORK_ERROR
    ]
    
    for category in categories:
        message = comm_manager.get_customer_message(category)
        print(f"✓ {category.value}: {message[:50]}...")
    
    return True


def test_error_logger():
    """Test error logger"""
    print("\nTesting Error Logger...")
    
    logger = ErrorLogger()
    
    error_id = logger.log_error(
        error_category=ErrorCategory.SYSTEM_ERROR,
        error_message="Test system error",
        exception=Exception("Test exception")
    )
    
    print(f"✓ Error logged with ID: {error_id}")
    
    return error_id is not None


def test_recovery_manager():
    """Test error recovery manager"""
    print("\nTesting Error Recovery Manager...")
    
    recovery_manager = ErrorRecoveryManager()
    
    error_context = ErrorContext(
        session_id="test_session",
        agent_type=AgentType.VERIFICATION
    )
    
    recovery_result = recovery_manager.execute_recovery(
        ErrorCategory.AGENT_FAILURE,
        error_context
    )
    
    print(f"✓ Recovery type: {recovery_result['recovery_type']}")
    print(f"✓ Recovery actions: {recovery_result['actions']}")
    print(f"✓ Retry possible: {recovery_result['retry_possible']}")
    
    return recovery_result['recovery_type'] is not None


def test_base_agent_error_handling():
    """Test base agent error handling integration"""
    print("\nTesting Base Agent Error Handling...")
    
    try:
        # Create a test agent (we'll use a mock implementation)
        class TestAgent(BaseAgent):
            def _execute_task_logic(self, task):
                # Simulate a task that fails
                raise Exception("Test task failure")
            
            def can_execute_task(self, task_type):
                return True
        
        agent = TestAgent(AgentType.SALES)
        
        # Test error handling
        test_error = Exception("Test agent error")
        error_result = agent.handle_error(test_error)
        
        print(f"✓ Agent error handled: {error_result.handled}")
        print(f"✓ Agent error count: {agent.error_count}")
        print(f"✓ Agent is healthy: {agent.is_healthy()}")
        
        return error_result.handled
        
    except Exception as e:
        print(f"✗ Base agent test failed: {str(e)}")
        return False


def main():
    """Run all error handling tests"""
    print("=" * 60)
    print("ERROR HANDLING IMPLEMENTATION TESTS")
    print("=" * 60)
    
    tests = [
        ("Comprehensive Error Handler", test_error_handler),
        ("Customer Communication", test_customer_communication),
        ("Error Logger", test_error_logger),
        ("Recovery Manager", test_recovery_manager),
        ("Base Agent Integration", test_base_agent_error_handling)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
            status = "PASS" if result else "FAIL"
            print(f"\n{status}: {test_name}")
        except Exception as e:
            results.append((test_name, False))
            print(f"\nFAIL: {test_name} - {str(e)}")
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All error handling tests passed!")
        return 0
    else:
        print("❌ Some tests failed. Check implementation.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)