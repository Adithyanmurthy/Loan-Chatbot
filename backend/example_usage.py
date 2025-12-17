"""
Example usage of the Agent Framework
Demonstrates how to use the base agent framework for the AI Loan Chatbot
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents import BaseAgent, AgentStatus, ContextManager, SessionManager
from models.conversation import AgentType, TaskType, AgentTask


class ExampleSalesAgent(BaseAgent):
    """Example Sales Agent implementation"""
    
    def __init__(self):
        super().__init__(AgentType.SALES)
    
    def _execute_task_logic(self, task: AgentTask):
        """Execute sales-specific task logic"""
        task_input = task.input
        
        if task.type == TaskType.SALES:
            # Simulate sales negotiation
            customer_request = task_input.get('loan_request', {})
            amount = customer_request.get('amount', 0)
            
            # Simple negotiation logic
            if amount <= 100000:
                return {
                    'status': 'approved',
                    'negotiated_amount': amount,
                    'interest_rate': 12.5,
                    'tenure': 24,
                    'message': f'Great! We can offer you ₹{amount} at 12.5% for 24 months.'
                }
            else:
                return {
                    'status': 'counter_offer',
                    'negotiated_amount': 100000,
                    'interest_rate': 13.0,
                    'tenure': 36,
                    'message': 'How about ₹1,00,000 at 13% for 36 months?'
                }
        
        return {'status': 'unknown_task'}
    
    def can_execute_task(self, task_type: TaskType) -> bool:
        return task_type == TaskType.SALES


def main():
    """Demonstrate the agent framework usage"""
    print("🤖 AI Loan Chatbot Agent Framework Demo\n")
    
    # Initialize the framework
    print("1. Initializing framework...")
    session_manager = SessionManager()
    
    # Start a new conversation session
    print("2. Starting new conversation session...")
    context = session_manager.start_session(customer_id="CUST_12345")
    session_id = context.session_id
    print(f"   Session ID: {session_id}")
    
    # Create and register a sales agent
    print("3. Creating and registering Sales Agent...")
    sales_agent = ExampleSalesAgent()
    session_manager.register_agent(session_id, sales_agent)
    
    # Add some customer data to the session
    print("4. Adding customer data to session...")
    session_manager.add_session_data(session_id, 'customer_name', 'Rajesh Kumar')
    session_manager.add_session_data(session_id, 'customer_phone', '+91-9876543210')
    session_manager.add_session_data(session_id, 'customer_city', 'Mumbai')
    
    # Switch to sales agent and execute a task
    print("5. Switching to Sales Agent and executing negotiation...")
    session_manager.switch_agent(session_id, AgentType.SALES, "sales_negotiation")
    
    # Execute a sales task
    loan_request = {
        'amount': 150000,
        'purpose': 'home_renovation',
        'tenure_preference': 24
    }
    
    result = session_manager.execute_agent_task(
        session_id, 
        AgentType.SALES, 
        TaskType.SALES, 
        {'loan_request': loan_request}
    )
    
    print(f"   Sales Agent Response: {result['message']}")
    print(f"   Status: {result['status']}")
    print(f"   Negotiated Amount: ₹{result['negotiated_amount']}")
    
    # Share data between agents (simulating handoff to verification)
    print("6. Sharing negotiation results with Verification Agent...")
    negotiation_data = {
        'agreed_amount': result['negotiated_amount'],
        'agreed_rate': result['interest_rate'],
        'agreed_tenure': result['tenure']
    }
    
    session_manager.share_data_between_agents(
        session_id, 
        AgentType.SALES, 
        AgentType.VERIFICATION, 
        negotiation_data
    )
    
    # Retrieve shared data (as verification agent would)
    shared_data = session_manager.get_shared_data(
        session_id, 
        AgentType.VERIFICATION, 
        AgentType.SALES
    )
    
    print(f"   Verification Agent received: {shared_data}")
    
    # Get session statistics
    print("7. Session statistics:")
    stats = session_manager.get_session_statistics()
    print(f"   Active sessions: {stats['active_sessions']}")
    print(f"   Sessions by stage: {stats['sessions_by_stage']}")
    
    # End the session
    print("8. Ending conversation session...")
    session_manager.end_session(session_id)
    
    print("\n✅ Demo completed successfully!")
    print("\nKey Features Demonstrated:")
    print("- Session management with unique IDs")
    print("- Agent registration and task execution")
    print("- Context sharing between agents")
    print("- Conversation stage management")
    print("- Data persistence and recovery")
    print("- Error handling and logging")


if __name__ == "__main__":
    main()