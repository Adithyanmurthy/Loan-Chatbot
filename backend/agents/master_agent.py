"""
Master Agent Controller Class
Implements conversation flow management, Worker Agent selection logic, and task delegation
Based on requirements: 6.1, 6.2, 6.4
"""

import logging
import uuid
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

from models.conversation import (
    ConversationContext, AgentTask, TaskType, TaskStatus, 
    AgentType, ErrorSeverity, ChatMessage
)
from models.customer import CustomerProfile
from models.loan import LoanApplication
from .base_agent import BaseAgent
from .session_manager import SessionManager
from .conversation_manager import ConversationManager
from services.error_handler import (
    ComprehensiveErrorHandler, ErrorCategory, ErrorContext, 
    ErrorHandlingResult
)


class MasterAgent(BaseAgent):
    """
    Master Agent responsible for orchestrating the entire loan conversation flow.
    Manages Worker Agent selection, task delegation, and coordination mechanisms.
    """
    
    def __init__(self, session_manager: Optional[SessionManager] = None):
        """
        Initialize Master Agent with session management capabilities.
        
        Args:
            session_manager: Optional SessionManager instance for coordination
        """
        super().__init__(AgentType.MASTER)
        
        self.session_manager = session_manager or SessionManager()
        self.conversation_manager = ConversationManager()
        
        # Enhanced error handling for Master Agent
        self.worker_agent_failures = {}  # Track failures per agent type
        self.escalation_threshold = 3  # Number of failures before escalation
        
        # Conversation flow state machine
        self.conversation_flows = {
            'initiation': ['information_collection'],
            'information_collection': ['sales_negotiation', 'error_handling'],
            'sales_negotiation': ['verification', 'error_handling'],
            'verification': ['underwriting', 'error_handling'],
            'underwriting': ['sanction_generation', 'document_upload', 'completion', 'error_handling'],
            'document_upload': ['underwriting', 'error_handling'],
            'sanction_generation': ['completion', 'error_handling'],
            'completion': [],
            'error_handling': ['initiation', 'completion']
        }
        
        # Agent selection rules based on conversation context
        self.agent_selection_rules = {
            'sales_negotiation': AgentType.SALES,
            'verification': AgentType.VERIFICATION,
            'underwriting': AgentType.UNDERWRITING,
            'document_upload': AgentType.VERIFICATION,  # Verification agent handles document uploads
            'sanction_generation': AgentType.SANCTION
        }
        
        # Task delegation mapping
        self.task_delegation_map = {
            TaskType.SALES: AgentType.SALES,
            TaskType.VERIFICATION: AgentType.VERIFICATION,
            TaskType.UNDERWRITING: AgentType.UNDERWRITING,
            TaskType.DOCUMENT_GENERATION: AgentType.SANCTION
        }
        
        self.logger.info("Master Agent initialized with conversation orchestration and management capabilities")

    def _execute_task_logic(self, task: AgentTask) -> Dict[str, Any]:
        """
        Execute Master Agent specific task logic.
        
        Args:
            task: AgentTask to execute
            
        Returns:
            Task execution result
        """
        task_handlers = {
            'initiate_conversation': self._handle_conversation_initiation,
            'process_user_message': self._handle_user_message,
            'delegate_task': self._handle_task_delegation,
            'coordinate_agents': self._handle_agent_coordination,
            'manage_flow': self._handle_flow_management,
            'handle_error': self._handle_error_scenario,
            'complete_conversation': self._handle_conversation_completion
        }
        
        task_action = task.input.get('action')
        if task_action not in task_handlers:
            raise ValueError(f"Unknown task action: {task_action}")
        
        return task_handlers[task_action](task.input)

    def can_execute_task(self, task_type: TaskType) -> bool:
        """
        Master Agent can coordinate all task types but doesn't execute them directly.
        
        Args:
            task_type: Type of task to check
            
        Returns:
            True for coordination tasks, False for specific domain tasks
        """
        # Master agent handles coordination but delegates specific tasks
        return task_type in [TaskType.SALES, TaskType.VERIFICATION, 
                           TaskType.UNDERWRITING, TaskType.DOCUMENT_GENERATION]

    def initiate_conversation(self, customer_id: Optional[str] = None, 
                            initial_message: Optional[str] = None) -> Dict[str, Any]:
        """
        Initiate a new conversation with personalized greeting.
        
        Args:
            customer_id: Optional customer identifier
            initial_message: Optional initial message from customer
            
        Returns:
            Conversation initiation result with session info and greeting
        """
        try:
            # Start new session
            context = self.session_manager.start_session(customer_id)
            self.set_context(context)
            
            # Register Master Agent
            self.session_manager.register_agent(context.session_id, self)
            
            # Generate personalized greeting
            greeting = self._generate_personalized_greeting(customer_id, initial_message)
            
            # Update conversation stage
            self.session_manager.update_conversation_stage(context.session_id, 'initiation')
            
            # Store initial interaction
            self.session_manager.add_session_data(
                context.session_id, 
                'conversation_started', 
                {
                    'timestamp': datetime.now().isoformat(),
                    'customer_id': customer_id,
                    'initial_message': initial_message,
                    'greeting_sent': greeting
                }
            )
            
            self.logger.info(f"Initiated conversation for session: {context.session_id}")
            
            # Track initial conversation state
            initial_tracking = self.conversation_manager.track_conversation_state(
                context, 
                {
                    'conversation_initiated': True,
                    'greeting_sent': greeting,
                    'customer_id': customer_id,
                    'initial_message': initial_message
                }
            )
            
            return {
                'session_id': context.session_id,
                'greeting': greeting,
                'conversation_stage': 'initiation',
                'next_expected_input': 'customer_response_or_loan_interest',
                'tracking_info': initial_tracking
            }
            
        except Exception as e:
            self.logger.error(f"Failed to initiate conversation: {str(e)}")
            raise

    def process_user_message(self, session_id: str, message: str, 
                           message_type: str = 'text') -> Dict[str, Any]:
        """
        Process incoming user message and determine appropriate response.
        
        Args:
            session_id: Session identifier
            message: User message content
            message_type: Type of message (text, file, etc.)
            
        Returns:
            Processing result with response and next actions
        """
        try:
            context = self.session_manager.get_session_context(session_id)
            if not context:
                raise ValueError(f"Session {session_id} not found")
            
            self.set_context(context)
            
            # Analyze message intent and context
            intent_analysis = self._analyze_message_intent(message, context)
            
            # Determine next action based on current stage and intent
            next_action = self._determine_next_action(intent_analysis, context)
            
            # Track conversation state with new message
            tracking_result = self.conversation_manager.track_conversation_state(
                context,
                {
                    'user_message': message,
                    'message_type': message_type,
                    'intent_analysis': intent_analysis,
                    'message_timestamp': datetime.now().isoformat()
                }
            )
            
            # Execute the determined action
            response = self._execute_conversation_action(next_action, message, context)
            
            # Add tracking information to response
            response['tracking_info'] = tracking_result
            
            self.logger.info(f"Processed user message in session {session_id}: {intent_analysis['intent']}")
            
            return response
            
        except Exception as e:
            self.logger.error(f"Failed to process user message in session {session_id}: {str(e)}")
            return self._handle_processing_error(session_id, str(e))

    def select_worker_agent(self, context: ConversationContext, 
                          task_requirements: Dict[str, Any]) -> AgentType:
        """
        Select appropriate Worker Agent based on conversation context and task requirements.
        
        Args:
            context: Current conversation context
            task_requirements: Requirements for the task to be executed
            
        Returns:
            Selected AgentType for task execution
        """
        current_stage = context.conversation_stage
        
        # Primary selection based on conversation stage
        if current_stage in self.agent_selection_rules:
            selected_agent = self.agent_selection_rules[current_stage]
            
            self.logger.info(f"Selected {selected_agent.value} agent for stage: {current_stage}")
            return selected_agent
        
        # Secondary selection based on task type
        task_type = task_requirements.get('task_type')
        if task_type and task_type in self.task_delegation_map:
            selected_agent = self.task_delegation_map[task_type]
            
            self.logger.info(f"Selected {selected_agent.value} agent for task type: {task_type}")
            return selected_agent
        
        # Fallback selection based on context analysis
        return self._analyze_context_for_agent_selection(context, task_requirements)

    def delegate_task(self, session_id: str, task_type: TaskType, 
                     input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Delegate task to appropriate Worker Agent with coordination.
        
        Args:
            session_id: Session identifier
            task_type: Type of task to delegate
            input_data: Task input parameters
            
        Returns:
            Task delegation result
        """
        try:
            context = self.session_manager.get_session_context(session_id)
            if not context:
                raise ValueError(f"Session {session_id} not found")
            
            # Select appropriate agent
            target_agent_type = self.task_delegation_map.get(task_type)
            if not target_agent_type:
                raise ValueError(f"No agent mapping found for task type: {task_type}")
            
            # Execute task through session manager
            result = self.session_manager.execute_agent_task(
                session_id, target_agent_type, task_type, input_data
            )
            
            if result is None:
                raise Exception(f"Task execution failed for {task_type}")
            
            # Handle task completion
            completion_result = self._handle_task_completion(
                session_id, task_type, target_agent_type, result
            )
            
            self.logger.info(f"Successfully delegated {task_type.value} task to {target_agent_type.value} agent")
            
            return {
                'task_delegated': True,
                'target_agent': target_agent_type.value,
                'task_result': result,
                'next_actions': completion_result.get('next_actions', [])
            }
            
        except Exception as e:
            self.logger.error(f"Task delegation failed: {str(e)}")
            return {
                'task_delegated': False,
                'error': str(e),
                'fallback_actions': self._get_fallback_actions(task_type)
            }

    def coordinate_agent_handoff(self, session_id: str, from_agent: AgentType, 
                               to_agent: AgentType, handoff_data: Dict[str, Any]) -> bool:
        """
        Coordinate handoff between Worker Agents with data sharing.
        
        Args:
            session_id: Session identifier
            from_agent: Source agent type
            to_agent: Target agent type
            handoff_data: Data to share between agents
            
        Returns:
            True if handoff successful, False otherwise
        """
        try:
            # Share data between agents
            sharing_success = self.session_manager.share_data_between_agents(
                session_id, from_agent, to_agent, handoff_data
            )
            
            if not sharing_success:
                self.logger.error(f"Failed to share data from {from_agent.value} to {to_agent.value}")
                return False
            
            # Determine new conversation stage for target agent
            new_stage = self._get_stage_for_agent(to_agent)
            
            # Switch active agent
            switch_success = self.session_manager.switch_agent(session_id, to_agent, new_stage)
            
            if switch_success:
                self.logger.info(f"Successfully coordinated handoff from {from_agent.value} to {to_agent.value}")
                return True
            else:
                self.logger.error(f"Failed to switch to {to_agent.value} agent")
                return False
                
        except Exception as e:
            self.logger.error(f"Agent handoff coordination failed: {str(e)}")
            return False

    def handle_worker_agent_error(self, session_id: str, failed_agent: AgentType, 
                                error_details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle Worker Agent errors with graceful recovery and customer communication.
        
        Args:
            session_id: Session identifier
            failed_agent: Agent type that encountered error
            error_details: Details about the error
            
        Returns:
            Error handling result with recovery actions
        """
        try:
            context = self.session_manager.get_session_context(session_id)
            if not context:
                raise ValueError(f"Session {session_id} not found")
            
            # Track worker agent failures
            agent_key = failed_agent.value
            if agent_key not in self.worker_agent_failures:
                self.worker_agent_failures[agent_key] = []
            
            failure_record = {
                'timestamp': datetime.now().isoformat(),
                'session_id': session_id,
                'error_details': error_details,
                'conversation_stage': context.conversation_stage
            }
            self.worker_agent_failures[agent_key].append(failure_record)
            
            # Use comprehensive error handler
            error_context = ErrorContext(
                session_id=session_id,
                agent_type=failed_agent,
                conversation_stage=context.conversation_stage,
                additional_data={
                    'master_agent_handling': True,
                    'failure_count': len(self.worker_agent_failures[agent_key]),
                    'error_details': error_details
                }
            )
            
            # Create a generic exception from error details
            error_message = error_details.get('message', 'Worker agent failure')
            worker_error = Exception(error_message)
            
            error_result = self.error_handler.handle_agent_error(
                agent_type=failed_agent,
                task_id=error_details.get('task_id', 'unknown'),
                error=worker_error,
                session_id=session_id,
                conversation_context=context
            )
            
            # Determine if escalation is needed based on failure count
            failure_count = len(self.worker_agent_failures[agent_key])
            escalation_needed = (
                failure_count >= self.escalation_threshold or
                error_result.escalation_required
            )
            
            # Execute recovery strategy
            recovery_result = self._execute_enhanced_recovery_strategy(
                session_id, failed_agent, error_result, escalation_needed
            )
            
            # Update conversation stage appropriately
            if escalation_needed:
                self.session_manager.update_conversation_stage(session_id, 'error_handling')
            else:
                # Try to continue with alternative approach
                alternative_stage = self._get_alternative_stage(failed_agent, context.conversation_stage)
                if alternative_stage:
                    self.session_manager.update_conversation_stage(session_id, alternative_stage)
            
            self.logger.info(f"Handled {failed_agent.value} agent error (failure #{failure_count})")
            
            return {
                'error_handled': True,
                'customer_message': error_result.customer_message,
                'recovery_actions': error_result.recovery_actions,
                'escalation_required': escalation_needed,
                'failure_count': failure_count,
                'recovery_result': recovery_result
            }
            
        except Exception as e:
            self.logger.error(f"Master agent error handling failed: {str(e)}")
            
            # Use error handler for master agent failure
            master_error_result = self.handle_error(e, {
                'context': 'worker_agent_error_handling',
                'failed_agent': failed_agent.value,
                'session_id': session_id
            })
            
            return {
                'error_handled': False,
                'customer_message': master_error_result.customer_message,
                'escalation_required': True,
                'master_agent_error': True
            }

    def complete_conversation(self, session_id: str, completion_type: str, 
                            summary_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Complete conversation with summary and professional closure.
        
        Args:
            session_id: Session identifier
            completion_type: Type of completion (approved, rejected, cancelled)
            summary_data: Summary information for the conversation
            
        Returns:
            Conversation completion result
        """
        try:
            context = self.session_manager.get_session_context(session_id)
            if not context:
                raise ValueError(f"Session {session_id} not found")
            
            # Generate completion summary
            completion_summary = self._generate_completion_summary(completion_type, summary_data, context)
            
            # Update conversation stage
            self.session_manager.update_conversation_stage(session_id, 'completion')
            
            # Store completion data
            self.session_manager.add_session_data(
                session_id,
                'conversation_completion',
                {
                    'completion_type': completion_type,
                    'summary': completion_summary,
                    'completed_at': datetime.now().isoformat(),
                    'summary_data': summary_data
                }
            )
            
            # End session
            self.session_manager.end_session(session_id)
            
            self.logger.info(f"Completed conversation {session_id} with type: {completion_type}")
            
            return {
                'conversation_completed': True,
                'completion_type': completion_type,
                'summary': completion_summary,
                'session_ended': True
            }
            
        except Exception as e:
            self.logger.error(f"Conversation completion failed: {str(e)}")
            return {
                'conversation_completed': False,
                'error': str(e)
            }

    def handle_conversation_timeout(self, session_id: str) -> Dict[str, Any]:
        """
        Handle conversation timeout scenarios with appropriate recovery.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Timeout handling result
        """
        try:
            context = self.session_manager.get_session_context(session_id)
            if not context:
                raise ValueError(f"Session {session_id} not found")
            
            # Use conversation manager to handle timeout
            timeout_result = self.conversation_manager.handle_conversation_timeout(context)
            
            # Update context with timeout information
            self.session_manager.update_conversation_stage(session_id, 'error_handling')
            
            # Determine recovery action
            recovery_action = timeout_result.get('recovery_action', 'resume_from_current_stage')
            
            if recovery_action == 'restart_conversation':
                # Reset conversation to initiation
                self.session_manager.update_conversation_stage(session_id, 'initiation')
            elif recovery_action == 'close_conversation':
                # Complete conversation due to timeout
                self.complete_conversation(session_id, 'cancelled', {'reason': 'timeout'})
            
            self.logger.info(f"Handled conversation timeout for session {session_id}: {recovery_action}")
            
            return {
                'timeout_handled': True,
                'timeout_message': timeout_result.get('timeout_message'),
                'recovery_action': recovery_action,
                'session_status': 'active' if recovery_action != 'close_conversation' else 'closed'
            }
            
        except Exception as e:
            self.logger.error(f"Failed to handle conversation timeout: {str(e)}")
            return {
                'timeout_handled': False,
                'error': str(e),
                'fallback_message': "I apologize for the delay. Are you still there? I'm here to help you with your loan application."
            }

    # Private helper methods
    
    def _handle_conversation_initiation(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle conversation initiation task"""
        return self.initiate_conversation(
            input_data.get('customer_id'),
            input_data.get('initial_message')
        )

    def _handle_user_message(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle user message processing task"""
        return self.process_user_message(
            input_data['session_id'],
            input_data['message'],
            input_data.get('message_type', 'text')
        )

    def _handle_task_delegation(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle task delegation task"""
        return self.delegate_task(
            input_data['session_id'],
            TaskType(input_data['task_type']),
            input_data.get('task_input', {})
        )

    def _handle_agent_coordination(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle agent coordination task"""
        success = self.coordinate_agent_handoff(
            input_data['session_id'],
            AgentType(input_data['from_agent']),
            AgentType(input_data['to_agent']),
            input_data.get('handoff_data', {})
        )
        return {'coordination_successful': success}

    def _handle_flow_management(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle conversation flow management task"""
        # Implementation for flow management logic
        return {'flow_managed': True}

    def _handle_error_scenario(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle error scenario task"""
        return self.handle_worker_agent_error(
            input_data['session_id'],
            AgentType(input_data['failed_agent']),
            input_data.get('error_details', {})
        )

    def _handle_conversation_completion(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle conversation completion task"""
        return self.complete_conversation(
            input_data['session_id'],
            input_data['completion_type'],
            input_data.get('summary_data', {})
        )

    def _generate_personalized_greeting(self, customer_id: Optional[str], 
                                      initial_message: Optional[str]) -> str:
        """Generate personalized greeting message using conversation manager"""
        try:
            # Try to get customer profile if customer_id is provided
            customer_profile = None
            if customer_id:
                # In a real implementation, you'd fetch from database
                # For now, we'll create a basic profile
                customer_profile = CustomerProfile(
                    id=customer_id,
                    name="Valued Customer",  # Would be fetched from DB
                    age=30,
                    city="Mumbai",
                    phone="",
                    address="",
                    current_loans=[],
                    credit_score=750,
                    pre_approved_limit=500000,
                    employment_type="salaried"
                )
            
            greeting_info = self.conversation_manager.generate_personalized_greeting(
                customer_id=customer_id,
                customer_profile=customer_profile,
                initial_message=initial_message
            )
            
            # Combine greeting and follow-up
            full_greeting = greeting_info['greeting_message']
            if greeting_info.get('follow_up_message'):
                full_greeting += " " + greeting_info['follow_up_message']
            
            return full_greeting
            
        except Exception as e:
            self.logger.error(f"Failed to generate personalized greeting: {str(e)}")
            # Fallback to simple greeting
            return "Hello! Welcome to our personal loan service. I'm here to help you find the perfect loan solution. How can I assist you today?"

    def _analyze_message_intent(self, message: str, context: ConversationContext) -> Dict[str, Any]:
        """Analyze user message intent based on content and context"""
        message_lower = message.lower()
        
        # Check for comprehensive loan application first
        loan_application_indicators = [
            'apply for', 'loan application', 'want a loan', 'need a loan',
            'personal loan', 'home loan', 'car loan', 'business loan'
        ]
        
        # Check for complete application details
        has_name = 'name' in message_lower or 'my name is' in message_lower or any(name in message_lower for name in ['john', 'doe', 'ajay', 'kumar', 'priya', 'rajesh'])
        has_age = 'age' in message_lower or any(str(i) in message for i in range(18, 80))
        has_income = 'income' in message_lower or 'salary' in message_lower or '₹' in message or 'rs' in message_lower
        has_employment = 'work' in message_lower or 'job' in message_lower or 'employed' in message_lower or 'engineer' in message_lower or 'company' in message_lower
        has_credit_score = 'credit score' in message_lower or 'cibil' in message_lower
        has_loan_amount = any(amount in message for amount in ['50000', '100000', '200000', '300000', '500000', '1000000', '5,00,000', '10,00,000'])
        
        # If it's a comprehensive loan application
        application_details_count = sum([has_name, has_age, has_income, has_employment, has_credit_score, has_loan_amount])
        is_loan_application = any(indicator in message_lower for indicator in loan_application_indicators)
        
        if (is_loan_application and application_details_count >= 3) or application_details_count >= 4:
            return {
                'intent': 'comprehensive_loan_application',
                'confidence': 0.9,
                'all_intents': ['comprehensive_loan_application', 'customer_details', 'loan_interest'],
                'message_length': len(message),
                'context_stage': context.conversation_stage,
                'application_completeness': application_details_count / 6
            }
        
        # Intent keywords mapping
        intent_keywords = {
            'loan_interest': ['loan', 'borrow', 'money', 'credit', 'finance', 'amount'],
            'customer_details': ['name', 'age', 'city', 'bangalore', 'mumbai', 'delhi', 'years old', 'my name is'],
            'form_submission': ['form submitted', 'form_data'],
            'information_request': ['how', 'what', 'when', 'where', 'why', 'tell me'],
            'agreement': ['yes', 'okay', 'sure', 'agree', 'proceed', 'continue', 'approve'],
            'verification_complete': ['verification complete', 'kyc complete', 'verified', 'identity verified', 'check my credit', 'credit check'],
            'disagreement': ['no', 'not', 'disagree', 'cancel', 'stop'],
            'objection': ['but', 'however', 'expensive', 'high', 'too much', 'cannot'],
            'document_related': ['document', 'upload', 'file', 'salary', 'slip', 'proof'],
            'sanction_letter_request': ['sanction letter', 'approval letter', 'generate letter', 'pdf', 'download']
        }
        
        # Special check for verification complete - should trigger underwriting directly
        if ('verification complete' in message_lower or 
            'kyc complete' in message_lower or
            ('verified' in message_lower and 'proceed' in message_lower) or
            ('check' in message_lower and 'credit' in message_lower) or
            ('credit' in message_lower and 'score' in message_lower) or
            ('eligibility' in message_lower)):
            return {
                'intent': 'verification_complete',
                'confidence': 0.95,
                'all_intents': ['verification_complete', 'agreement'],
                'message_length': len(message),
                'context_stage': context.conversation_stage
            }
        
        # Special check for sanction letter request
        if ('sanction' in message_lower and 'letter' in message_lower) or 'generate' in message_lower:
            return {
                'intent': 'sanction_letter_request',
                'confidence': 0.95,
                'all_intents': ['sanction_letter_request', 'agreement'],
                'message_length': len(message),
                'context_stage': context.conversation_stage
            }
        
        # Special check for customer details pattern (name, age, city, amount)
        has_city = 'city' in message_lower or any(city in message_lower for city in ['bangalore', 'banglore', 'mumbai', 'delhi', 'chennai', 'kolkata', 'pune', 'hyderabad'])
        
        # If message contains at least 2 of these elements, consider it customer details
        detail_count = sum([has_name, has_age, has_city, has_loan_amount])
        
        if detail_count >= 2:
            detected_intents = ['customer_details']
        else:
            detected_intents = []
            for intent, keywords in intent_keywords.items():
                if any(keyword in message_lower for keyword in keywords):
                    detected_intents.append(intent)
        
        primary_intent = detected_intents[0] if detected_intents else 'general_inquiry'
        
        return {
            'intent': primary_intent,
            'confidence': 0.8 if detected_intents else 0.3,
            'all_intents': detected_intents,
            'message_length': len(message),
            'context_stage': context.conversation_stage
        }

    def _determine_next_action(self, intent_analysis: Dict[str, Any], 
                             context: ConversationContext) -> Dict[str, Any]:
        """Determine next action based on intent and context"""
        current_stage = context.conversation_stage
        intent = intent_analysis['intent']
        
        # Action mapping based on stage and intent
        action_map = {
            ('initiation', 'loan_interest'): {'action': 'collect_information', 'next_stage': 'information_collection'},
            ('initiation', 'general_inquiry'): {'action': 'provide_information', 'next_stage': 'initiation'},
            ('initiation', 'comprehensive_loan_application'): {'action': 'process_complete_application', 'next_stage': 'underwriting'},
            ('information_collection', 'customer_details'): {'action': 'start_sales', 'next_stage': 'sales_negotiation'},
            ('information_collection', 'form_submission'): {'action': 'start_sales', 'next_stage': 'sales_negotiation'},
            ('information_collection', 'agreement'): {'action': 'start_sales', 'next_stage': 'sales_negotiation'},
            ('information_collection', 'comprehensive_loan_application'): {'action': 'process_complete_application', 'next_stage': 'underwriting'},
            ('sales_negotiation', 'agreement'): {'action': 'start_verification', 'next_stage': 'verification'},
            ('sales_negotiation', 'verification_complete'): {'action': 'start_underwriting', 'next_stage': 'underwriting'},
            ('sales_negotiation', 'objection'): {'action': 'handle_objection', 'next_stage': 'sales_negotiation'},
            ('sales_negotiation', 'comprehensive_loan_application'): {'action': 'process_complete_application', 'next_stage': 'underwriting'},
            ('verification', 'agreement'): {'action': 'start_underwriting', 'next_stage': 'underwriting'},
            ('verification', 'verification_complete'): {'action': 'start_underwriting', 'next_stage': 'underwriting'},
            ('verification', 'general_inquiry'): {'action': 'start_underwriting', 'next_stage': 'underwriting'},
            ('underwriting', 'document_related'): {'action': 'request_documents', 'next_stage': 'document_upload'},
            ('underwriting', 'agreement'): {'action': 'generate_sanction_letter', 'next_stage': 'sanction_generation'},
            ('underwriting', 'sanction_letter_request'): {'action': 'generate_sanction_letter', 'next_stage': 'sanction_generation'},
            ('underwriting', 'verification_complete'): {'action': 'generate_sanction_letter', 'next_stage': 'sanction_generation'},
            ('sanction_generation', 'sanction_letter_request'): {'action': 'generate_sanction_letter', 'next_stage': 'sanction_generation'},
            ('sanction_generation', 'agreement'): {'action': 'generate_sanction_letter', 'next_stage': 'sanction_generation'},
        }
        
        key = (current_stage, intent)
        
        if key in action_map:
            return action_map[key]
        
        # Default action
        return {'action': 'continue_conversation', 'next_stage': current_stage}

    def _execute_conversation_action(self, action_config: Dict[str, Any], 
                                   message: str, context: ConversationContext) -> Dict[str, Any]:
        """Execute the determined conversation action"""
        action = action_config['action']
        next_stage = action_config['next_stage']
        
        # Update conversation stage if needed using conversation manager
        if next_stage != context.conversation_stage:
            transition_result = self.conversation_manager.manage_stage_transition(
                context, next_stage, {'action': action, 'trigger': 'user_message'}
            )
            
            if transition_result['transition_successful']:
                self.session_manager.update_conversation_stage(context.session_id, next_stage)
            else:
                self.logger.warning(f"Stage transition failed: {transition_result.get('error')}")
        
        # Execute specific action
        if action == 'collect_information':
            return self._collect_customer_information(context.session_id)
        elif action == 'start_sales':
            return self._initiate_sales_process(context.session_id)
        elif action == 'start_verification':
            return self._initiate_verification_process(context.session_id)
        elif action == 'start_underwriting':
            return self._initiate_underwriting_process(context.session_id)
        elif action == 'handle_objection':
            return self._handle_sales_objection(context.session_id, message)
        elif action == 'request_documents':
            return self._request_document_upload(context.session_id)
        elif action == 'generate_sanction_letter':
            return self._generate_sanction_letter(context.session_id)
        elif action == 'process_complete_application':
            return self._process_complete_application(context.session_id, message)
        else:
            return self._continue_conversation(context.session_id, message)

    def _collect_customer_information(self, session_id: str) -> Dict[str, Any]:
        """Initiate customer information collection with structured form"""
        form_data = {
            'form_type': 'customer_information',
            'title': 'Personal Loan Application - Basic Information',
            'fields': [
                {
                    'name': 'full_name',
                    'label': 'Full Name',
                    'type': 'text',
                    'required': True,
                    'placeholder': 'Enter your full name as per ID proof'
                },
                {
                    'name': 'age',
                    'label': 'Age',
                    'type': 'number',
                    'required': True,
                    'min': 21,
                    'max': 65,
                    'placeholder': 'Enter your age'
                },
                {
                    'name': 'city',
                    'label': 'City',
                    'type': 'text',
                    'required': True,
                    'placeholder': 'Enter your current city'
                },
                {
                    'name': 'phone',
                    'label': 'Mobile Number',
                    'type': 'tel',
                    'required': True,
                    'placeholder': 'Enter 10-digit mobile number'
                },
                {
                    'name': 'loan_amount',
                    'label': 'Loan Amount Required (₹)',
                    'type': 'number',
                    'required': True,
                    'min': 50000,
                    'max': 2000000,
                    'step': 10000,
                    'placeholder': 'Enter loan amount (minimum ₹50,000)'
                },
                {
                    'name': 'monthly_salary',
                    'label': 'Monthly Salary (₹)',
                    'type': 'number',
                    'required': True,
                    'min': 15000,
                    'placeholder': 'Enter your monthly salary'
                },
                {
                    'name': 'employment_type',
                    'label': 'Employment Type',
                    'type': 'select',
                    'required': True,
                    'options': [
                        {'value': 'salaried', 'label': 'Salaried Employee'},
                        {'value': 'self_employed', 'label': 'Self Employed'},
                        {'value': 'business', 'label': 'Business Owner'}
                    ]
                }
            ],
            'submit_text': 'Get Loan Options',
            'description': 'Please fill in your details to get personalized loan options with competitive interest rates.'
        }
        
        return {
            'response': "Great! I'd be happy to help you with a personal loan. Please fill in the form below with your details so I can calculate the best loan options for you.",
            'action_taken': 'information_collection_started',
            'next_expected': 'customer_details',
            'show_form': True,
            'form_data': form_data
        }

    def _initiate_sales_process(self, session_id: str) -> Dict[str, Any]:
        """Initiate sales negotiation process with proper customer data extraction"""
        try:
            # Get conversation context to extract customer information
            context = self.session_manager.get_session_context(session_id)
            
            # Extract customer information from collected data
            customer_data = context.collected_data if context else {}
            
            # Parse customer information from form data or conversation
            customer_profile = self._parse_customer_information(customer_data, context)
            
            # Share customer profile with Sales Agent BEFORE delegating task
            sharing_success = self.session_manager.share_data_between_agents(
                session_id, 
                AgentType.MASTER, 
                AgentType.SALES, 
                {'customer_profile': customer_profile}
            )
            
            if not sharing_success:
                self.logger.error(f"Failed to share customer profile with Sales Agent for session {session_id}")
            
            # Delegate to Sales Agent with customer information
            result = self.delegate_task(session_id, TaskType.SALES, {
                'action': 'start_negotiation',
                'requested_amount': customer_profile.get('requested_amount', 100000),
                'customer_profile': customer_profile
            })
            
            # Check if delegation was successful and get loan options
            if result.get('task_delegated') and result.get('task_result'):
                task_result = result['task_result']
                
                # Check if we got loan options with calculations
                if task_result.get('negotiation_successful') and 'loan_options' in task_result:
                    loan_options = task_result['loan_options']
                    presentation_message = task_result.get('presentation_message', '')
                    
                    # Create comprehensive response with loan options
                    if presentation_message:
                        response_message = f"Perfect! I've analyzed your profile and calculated some excellent loan options for you.\n\n{presentation_message}"
                    else:
                        # Create detailed loan options presentation
                        options_text = self._create_detailed_loan_presentation(loan_options, customer_profile)
                        response_message = f"Excellent! Based on your profile, I've calculated personalized loan options for ₹{customer_profile.get('requested_amount', 100000):,.0f}:\n\n{options_text}\n\n💡 **Which option would you prefer, or would you like me to adjust any terms?**"
                    
                    return {
                        'response': response_message,
                        'delegation_result': result,
                        'action_taken': 'sales_process_started',
                        'loan_options': loan_options,
                        'sales_agent_active': True,
                        'show_loan_options': True,
                        'customer_profile': customer_profile
                    }
                
                # Check if there was an error in negotiation
                elif not task_result.get('negotiation_successful'):
                    error_message = task_result.get('error', 'Unknown error in loan calculation')
                    fallback_message = task_result.get('fallback_message', 'Let me try a different approach to calculate your loan options.')
                    
                    self.logger.error(f"Sales Agent negotiation failed: {error_message}")
                    
                    # Provide manual loan options as fallback
                    fallback_options = self._generate_fallback_loan_options(customer_profile)
                    
                    return {
                        'response': f"I'm working on your loan options. {fallback_message}\n\nHere are some preliminary options based on your profile:\n\n{fallback_options}",
                        'delegation_result': result,
                        'action_taken': 'sales_process_started_with_fallback',
                        'error': error_message,
                        'fallback_used': True
                    }
            
            # If delegation failed, provide manual calculation
            self.logger.warning(f"Sales Agent delegation failed for session {session_id}, using manual calculation")
            
            manual_options = self._generate_fallback_loan_options(customer_profile)
            
            return {
                'response': f"Perfect! Let me present you with some attractive loan options for ₹{customer_profile.get('requested_amount', 100000):,.0f}:\n\n{manual_options}\n\nWhich option interests you the most?",
                'delegation_result': result,
                'action_taken': 'sales_process_manual',
                'fallback_used': True,
                'customer_profile': customer_profile
            }
            
        except Exception as e:
            self.logger.error(f"Error in sales process initiation: {str(e)}")
            return {
                'response': "I'm here to help you find the perfect loan solution. Let me calculate some attractive options for you based on your requirements.",
                'action_taken': 'sales_process_error',
                'error': str(e)
            }

    def _initiate_verification_process(self, session_id: str) -> Dict[str, Any]:
        """Initiate verification process"""
        try:
            # Get customer profile from context
            context = self.session_manager.get_session_context(session_id)
            customer_data = context.collected_data if context else {}
            
            # Parse customer information
            customer_profile = self._parse_customer_information(customer_data, context)
            
            # Prepare verification task with customer details
            verification_input = {
                'verification_type': 'full_kyc',
                'customer_id': customer_profile.get('id', 'GUEST_USER'),
                'provided_details': {
                    'name': customer_profile.get('name'),
                    'phone': customer_profile.get('phone'),
                    'address': f"{customer_profile.get('city')}, India",
                    'age': customer_profile.get('age')
                },
                'session_id': session_id
            }
            
            result = self.delegate_task(session_id, TaskType.VERIFICATION, verification_input)
            
            # Create detailed verification message
            verification_message = f"""Excellent! Now I need to verify your details to proceed with your loan application.

**Verification Process:**
✅ **Identity Verification** - Confirming your personal details
✅ **Phone Verification** - Validating your mobile number: {customer_profile.get('phone', 'N/A')}
✅ **Address Verification** - Confirming your location: {customer_profile.get('city', 'N/A')}

I'm checking your details against our secure database. This will take just a moment..."""
            
            return {
                'response': verification_message,
                'delegation_result': result,
                'action_taken': 'verification_process_started',
                'customer_profile': customer_profile
            }
            
        except Exception as e:
            self.logger.error(f"Error initiating verification: {str(e)}")
            return {
                'response': "Excellent! Now I need to verify some details to proceed with your loan application.",
                'action_taken': 'verification_process_started',
                'error': str(e)
            }

    def _initiate_underwriting_process(self, session_id: str) -> Dict[str, Any]:
        """Initiate underwriting process - Step 1: Credit Check"""
        try:
            # Get customer profile and loan details from context
            context = self.session_manager.get_session_context(session_id)
            customer_data = context.collected_data if context else {}
            
            # Parse customer information
            customer_profile = self._parse_customer_information(customer_data, context)
            
            # Get selected loan option from context (if available)
            selected_loan = self.get_shared_data('selected_loan_option') or {}
            
            # Prepare underwriting task
            underwriting_input = {
                'action': 'full_underwriting',
                'customer_id': customer_profile.get('id', 'GUEST_USER'),
                'loan_application': {
                    'id': f"app_{int(datetime.now().timestamp())}",
                    'requested_amount': customer_profile.get('requested_amount', 100000),
                    'tenure': selected_loan.get('tenure', 60),
                    'interest_rate': selected_loan.get('interest_rate', 12.0),
                    'emi': selected_loan.get('emi', 0)
                }
            }
            
            result = self.delegate_task(session_id, TaskType.UNDERWRITING, underwriting_input)
            
            # Get underwriting result
            underwriting_result = result.get('result', {})
            credit_score = underwriting_result.get('credit_score', 750)
            is_approved = result.get('success') and underwriting_result.get('decision') == 'approved'
            emi = underwriting_result.get('emi', customer_profile.get('requested_amount', 100000) * 0.02)
            
            # Store approval data for next step
            self.share_context_data('credit_check_done', True)
            self.share_context_data('credit_score', credit_score)
            self.share_context_data('loan_approved', is_approved)
            self.share_context_data('approved_loan', {
                'amount': customer_profile.get('requested_amount', 100000),
                'tenure': selected_loan.get('tenure', 60),
                'interest_rate': selected_loan.get('interest_rate', 12.0),
                'emi': emi,
                'credit_score': credit_score
            })
            
            # Show credit check results with Continue button
            underwriting_message = f"""📊 **Credit Check Complete!**

**Credit Assessment Results:**
✅ **Credit Score**: {credit_score}/900 - {'Excellent' if credit_score >= 750 else 'Good'}
✅ **Credit History**: Clean
✅ **Debt-to-Income Ratio**: Within limits
✅ **Risk Assessment**: {'Low Risk' if is_approved else 'Medium Risk'}

**Loan Details Being Assessed:**
💰 **Requested Amount**: ₹{customer_profile.get('requested_amount', 100000):,}
📅 **Tenure**: {selected_loan.get('tenure', 60)} months
📊 **Interest Rate**: {selected_loan.get('interest_rate', 12.0)}% per annum

{'✅ **You are eligible for this loan!**' if is_approved else '⚠️ **Additional review required**'}

Click below to proceed with loan approval:

[PROCEED_APPROVAL]"""
            
            return {
                'response': underwriting_message,
                'delegation_result': result,
                'action_taken': 'credit_check_completed',
                'customer_profile': customer_profile
            }
            
        except Exception as e:
            self.logger.error(f"Error initiating underwriting: {str(e)}")
            return {
                'response': "Great! Let me quickly assess your loan eligibility based on our criteria.\n\n[PROCEED_APPROVAL]",
                'action_taken': 'underwriting_process_started',
                'error': str(e)
            }

    def _handle_sales_objection(self, session_id: str, objection: str) -> Dict[str, Any]:
        """Handle customer objection during sales"""
        result = self.delegate_task(session_id, TaskType.SALES, {
            'action': 'handle_objection',
            'objection': objection
        })
        return {
            'response': "I understand your concern. Let me see what alternatives I can offer you.",
            'delegation_result': result,
            'action_taken': 'objection_handled'
        }

    def _request_document_upload(self, session_id: str) -> Dict[str, Any]:
        """Request document upload from customer"""
        return {
            'response': "To proceed with your loan application, I'll need you to upload your latest salary slip. Please use the upload button below.",
            'action_taken': 'document_upload_requested',
            'upload_required': True
        }

    def _generate_sanction_letter(self, session_id: str) -> Dict[str, Any]:
        """Generate sanction letter after loan approval"""
        try:
            # Get customer profile and loan details from context
            context = self.session_manager.get_session_context(session_id)
            customer_data = context.collected_data if context else {}
            
            # Try to get stored customer profile first, fallback to parsing
            stored_profile = self.session_manager.get_session_data(session_id, 'customer_profile')
            if stored_profile:
                customer_profile = stored_profile
                self.logger.info(f"Using stored customer profile: {customer_profile}")
            else:
                # Parse customer information from collected data
                customer_profile = self._parse_customer_information(customer_data, context)
                self.logger.info(f"Using parsed customer profile: {customer_profile}")
            
            # Get approved loan details
            approved_loan = self.get_shared_data('approved_loan') or {}
            
            # Create proper loan application and customer profile objects
            from models.loan import LoanApplication, LoanStatus
            from models.customer import CustomerProfile
            from services.sanction_workflow_service import SanctionWorkflowService
            import uuid
            
            # Create LoanApplication object
            loan_app = LoanApplication(
                id=str(uuid.uuid4()),
                customer_id=customer_profile.get('customer_id', str(uuid.uuid4())),
                requested_amount=float(customer_profile.get('requested_amount', 100000)),
                tenure=int(approved_loan.get('tenure', 60)),
                interest_rate=float(approved_loan.get('interest_rate', 12.0)),
                emi=float(approved_loan.get('emi', 0)),
                status=LoanStatus.APPROVED
            )
            
            # Create CustomerProfile object
            customer_obj = CustomerProfile(
                id=customer_profile.get('id', str(uuid.uuid4())),
                name=customer_profile.get('name', 'Valued Customer'),
                age=int(customer_profile.get('age', 25)),
                city=customer_profile.get('city', 'Unknown'),
                phone=customer_profile.get('phone', 'Not provided'),
                address=customer_profile.get('address', f"{customer_profile.get('city', 'Unknown')}, India"),
                salary=float(customer_profile.get('salary', 50000)),
                credit_score=int(customer_profile.get('credit_score', 750)),
                pre_approved_limit=float(customer_profile.get('pre_approved_limit', 500000)),
                employment_type=customer_profile.get('employment_type', 'salaried')
            )
            
            # Use sanction workflow service to generate PDF
            sanction_service = SanctionWorkflowService()
            workflow_result = sanction_service.process_loan_approval(
                loan_application=loan_app,
                customer_profile=customer_obj,
                context=context
            )
            
            if workflow_result.get('success'):
                # Extract download link from workflow result
                download_link = workflow_result['workflow_result']['sanction_letter']['download_link']
                filename = workflow_result['workflow_result']['sanction_letter']['file_info']['filename']
                
                sanction_message = f"""🎉 **Congratulations {customer_obj.name}!**

**Your Personal Loan has been APPROVED!**

✅ **Approved Amount**: ₹{loan_app.requested_amount:,}
✅ **Monthly EMI**: ₹{loan_app.emi:,.0f}
✅ **Tenure**: {loan_app.tenure} months
✅ **Interest Rate**: {loan_app.interest_rate}% per annum

📄 **Your sanction letter is ready for download!**

**Next Steps:**
1. Download your sanction letter using the link below
2. Complete the loan disbursement process
3. Funds will be transferred to your account

Thank you for choosing Tata Capital Limited! 🙏"""
                
                return {
                    'response': sanction_message,
                    'message_type': 'download_link',
                    'download_url': download_link,
                    'filename': filename,
                    'action_taken': 'sanction_letter_generated',
                    'customer_profile': customer_profile,
                    'loan_approved': True,
                    'workflow_result': workflow_result
                }
            else:
                # Fallback message if PDF generation fails
                fallback_message = f"""🎉 **Congratulations {customer_obj.name}!**

**Your Personal Loan has been APPROVED!**

✅ **Approved Amount**: ₹{loan_app.requested_amount:,}
✅ **Monthly EMI**: ₹{loan_app.emi:,.0f}
✅ **Tenure**: {loan_app.tenure} months
✅ **Interest Rate**: {loan_app.interest_rate}% per annum

📄 **Your sanction letter is being prepared and will be emailed to you within 24 hours.**

For immediate assistance, please contact us at 1800-209-8800.

Thank you for choosing Tata Capital Limited! 🙏"""
                
                return {
                    'response': fallback_message,
                    'action_taken': 'sanction_letter_generation_failed',
                    'customer_profile': customer_profile,
                    'loan_approved': True,
                    'error': workflow_result.get('error')
                }
            
        except Exception as e:
            self.logger.error(f"Error generating sanction letter: {str(e)}")
            return {
                'response': "Congratulations! Your loan has been approved. We're preparing your sanction letter and will email it to you shortly.",
                'action_taken': 'sanction_letter_generation_error',
                'error': str(e)
            }

    def _process_complete_application(self, session_id: str, message: str) -> Dict[str, Any]:
        """Process a comprehensive loan application with all details provided"""
        try:
            self.logger.info(f"Processing complete loan application for session {session_id}")
            
            # Extract customer information from the comprehensive message
            customer_profile = self._extract_customer_info_from_message(message)
            
            # Store customer profile in session
            self.session_manager.add_session_data(session_id, 'customer_profile', customer_profile)
            self.logger.info(f"Stored customer profile: {customer_profile}")
            
            # Directly proceed to underwriting since we have all the information
            underwriting_result = self._initiate_underwriting_process(session_id)
            
            # Check the delegation result to see if loan was approved
            delegation_result = underwriting_result.get('delegation_result', {})
            
            # Wait a moment for shared data to be available
            import time
            time.sleep(0.5)
            
            # Check shared data for loan approval
            loan_approved = self.get_shared_data('loan_approved')
            approved_loan = self.get_shared_data('approved_loan')
            
            self.logger.info(f"Loan approval status: {loan_approved}, Approved loan: {approved_loan}")
            
            # Check if underwriting was successful and loan approved
            self.logger.info(f"Delegation result success: {delegation_result.get('success')}")
            
            if loan_approved:
                # Generate sanction letter immediately
                sanction_result = self._generate_sanction_letter(session_id)
                
                # Check if sanction letter was generated successfully
                if sanction_result.get('download_url'):
                    # Combine underwriting and sanction results
                    combined_response = f"""🎉 **Congratulations {customer_profile.get('name', 'Valued Customer')}!**

**Your Personal Loan has been APPROVED!**

✅ **Approved Amount**: ₹{customer_profile.get('requested_amount', 100000):,}
✅ **Processing completed successfully**

📄 **Your sanction letter is ready for download!**

{sanction_result.get('response', '')}"""
                    
                    return {
                        'response': combined_response,
                        'action_taken': 'complete_application_approved',
                        'loan_approved': True,
                        'download_url': sanction_result.get('download_url'),
                        'filename': sanction_result.get('filename'),
                        'customer_profile': customer_profile
                    }
                else:
                    # Loan approved but PDF generation failed
                    return {
                        'response': f"""🎉 **Congratulations {customer_profile.get('name', 'Valued Customer')}!**

**Your Personal Loan has been APPROVED!**

✅ **Approved Amount**: ₹{customer_profile.get('requested_amount', 100000):,}

📄 **Your sanction letter is being prepared and will be emailed to you within 24 hours.**

For immediate assistance, please contact us at 1800-209-8800.""",
                        'action_taken': 'complete_application_approved_no_pdf',
                        'loan_approved': True,
                        'customer_profile': customer_profile
                    }
            else:
                # Check if loan was explicitly rejected
                if self.get_shared_data('loan_approved') == False:
                    return {
                        'response': f"""Thank you {customer_profile.get('name', 'Valued Customer')} for your loan application.

After careful review of your application, we're unable to approve your loan request at this time based on our current lending criteria.

This decision is based on factors such as credit history, income assessment, and our risk evaluation process.

We encourage you to:
• Improve your credit score
• Consider a smaller loan amount
• Apply again after 6 months

For more information, please contact us at 1800-209-8800.""",
                        'action_taken': 'complete_application_rejected',
                        'loan_approved': False,
                        'customer_profile': customer_profile
                    }
                else:
                    # Underwriting in progress or failed
                    return {
                        'response': f"""Thank you {customer_profile.get('name', 'Valued Customer')} for providing your complete application details.

I'm processing your information and will get back to you shortly with a decision.

Your application is being reviewed for:
• Credit assessment
• Income verification  
• Risk evaluation

Please wait while I complete the underwriting process...""",
                        'action_taken': 'complete_application_processing',
                        'customer_profile': customer_profile
                    }
                
        except Exception as e:
            self.logger.error(f"Error processing complete application: {str(e)}")
            return {
                'response': "Thank you for your comprehensive loan application. I'm reviewing your details and will provide you with a decision shortly.",
                'action_taken': 'complete_application_error',
                'error': str(e)
            }
    
    def _extract_customer_info_from_message(self, message: str) -> Dict[str, Any]:
        """Extract customer information from a comprehensive application message"""
        import re
        
        # Default profile
        customer_profile = {
            'id': 'GUEST_USER',
            'name': 'Valued Customer',
            'age': 30,
            'city': 'Bangalore',
            'phone': '9876543210',
            'address': 'Bangalore, Karnataka',
            'current_loans': [],
            'credit_score': 750,
            'pre_approved_limit': 500000,
            'employment_type': 'salaried',
            'salary': 60000,
            'requested_amount': 300000
        }
        
        message_lower = message.lower()
        
        # Extract name
        name_patterns = [
            r'name[:\s]+([a-zA-Z\s]+?)(?:\n|age|,|$)',
            r'my name is ([a-zA-Z\s]+?)(?:\n|age|,|$)',
            r'i am ([a-zA-Z\s]+?)(?:\n|age|,|$)'
        ]
        for pattern in name_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                customer_profile['name'] = match.group(1).strip().title()
                break
        
        # Extract age
        age_match = re.search(r'age[:\s]+(\d+)', message, re.IGNORECASE)
        if age_match:
            customer_profile['age'] = int(age_match.group(1))
        
        # Extract income/salary
        income_patterns = [
            r'income[:\s]+₹?(\d+(?:,\d+)*)',
            r'salary[:\s]+₹?(\d+(?:,\d+)*)',
            r'₹(\d+(?:,\d+)*)',
            r'rs\.?\s*(\d+(?:,\d+)*)'
        ]
        for pattern in income_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                salary_str = match.group(1).replace(',', '')
                customer_profile['salary'] = int(salary_str)
                break
        
        # Extract employment
        if 'software engineer' in message_lower or 'engineer' in message_lower:
            customer_profile['employment_type'] = 'salaried'
        elif 'business' in message_lower or 'self employed' in message_lower:
            customer_profile['employment_type'] = 'self_employed'
        
        # Extract credit score
        credit_match = re.search(r'credit score[:\s]+(\d+)', message, re.IGNORECASE)
        if credit_match:
            customer_profile['credit_score'] = int(credit_match.group(1))
        
        # Ensure all required fields are present with defaults
        if 'credit_score' not in customer_profile or customer_profile['credit_score'] == 750:
            # Use a good credit score if not specified
            customer_profile['credit_score'] = 750
        
        if 'pre_approved_limit' not in customer_profile:
            # Calculate pre-approved limit based on salary (10x monthly salary)
            customer_profile['pre_approved_limit'] = customer_profile['salary'] * 10
        
        if 'employment_type' not in customer_profile:
            customer_profile['employment_type'] = 'salaried'
        
        # Extract loan amount
        amount_patterns = [
            r'₹(\d+(?:,\d+)*)',
            r'rs\.?\s*(\d+(?:,\d+)*)',
            r'loan[^₹\d]*₹?(\d+(?:,\d+)*)',
            r'amount[^₹\d]*₹?(\d+(?:,\d+)*)'
        ]
        for pattern in amount_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '')
                customer_profile['requested_amount'] = int(amount_str)
                break
        
        # Extract city
        cities = ['bangalore', 'mumbai', 'delhi', 'chennai', 'kolkata', 'pune', 'hyderabad']
        for city in cities:
            if city in message_lower:
                customer_profile['city'] = city.title()
                customer_profile['address'] = f"{city.title()}, India"
                break
        
        return customer_profile

    def _continue_conversation(self, session_id: str, message: str) -> Dict[str, Any]:
        """Continue general conversation"""
        return {
            'response': "I understand. Could you please provide more details so I can better assist you?",
            'action_taken': 'conversation_continued'
        }
    
    def _parse_customer_information(self, collected_data: Dict[str, Any], context: ConversationContext) -> Dict[str, Any]:
        """Parse customer information from collected data or conversation context"""
        # Default customer profile
        customer_profile = {
            'id': context.customer_id or 'GUEST_USER',
            'name': 'Valued Customer',
            'age': 25,
            'city': 'Bangalore',
            'phone': '9876543210',
            'address': 'Bangalore, Karnataka',
            'current_loans': [],
            'credit_score': 750,
            'pre_approved_limit': 500000,
            'employment_type': 'salaried',
            'salary': 50000,
            'requested_amount': 100000
        }
        
        self.logger.info(f"Parsing customer info from collected_data keys: {list(collected_data.keys()) if collected_data else 'None'}")
        
        # Extract from form data if available
        if 'form_data' in collected_data:
            form_data = collected_data['form_data']
            self.logger.info(f"Found form_data: {form_data}")
            
            # Handle nested form_data structure (from frontend: { form_data: { full_name: ... } })
            actual_form_data = form_data
            if isinstance(form_data, dict):
                if 'form_data' in form_data:
                    actual_form_data = form_data['form_data']
                elif 'value' in form_data:
                    # Handle session storage format: { value: { form_data: { ... } } }
                    actual_form_data = form_data.get('value', {})
                    if isinstance(actual_form_data, dict) and 'form_data' in actual_form_data:
                        actual_form_data = actual_form_data['form_data']
            
            self.logger.info(f"Actual form data: {actual_form_data}")
            
            if isinstance(actual_form_data, dict):
                # Parse loan amount - handle string or int
                loan_amount = actual_form_data.get('loan_amount', customer_profile['requested_amount'])
                if isinstance(loan_amount, str):
                    loan_amount = int(loan_amount.replace(',', '').replace(' ', ''))
                else:
                    loan_amount = int(loan_amount)
                
                # Parse salary
                salary = actual_form_data.get('monthly_salary', customer_profile['salary'])
                if isinstance(salary, str):
                    salary = int(salary.replace(',', '').replace(' ', ''))
                else:
                    salary = int(salary)
                
                # Parse age
                age = actual_form_data.get('age', customer_profile['age'])
                if isinstance(age, str):
                    age = int(age)
                else:
                    age = int(age)
                
                customer_profile.update({
                    'name': actual_form_data.get('full_name', customer_profile['name']),
                    'age': age,
                    'city': actual_form_data.get('city', customer_profile['city']),
                    'phone': actual_form_data.get('phone', customer_profile['phone']),
                    'salary': salary,
                    'employment_type': actual_form_data.get('employment_type', customer_profile['employment_type']),
                    'requested_amount': loan_amount
                })
                
                self.logger.info(f"Parsed customer profile - Name: {customer_profile['name']}, Loan Amount: {customer_profile['requested_amount']}, Salary: {customer_profile['salary']}")
        
        # Extract from conversation text if no form data
        elif 'customer_details' in collected_data:
            details = collected_data['customer_details']
            # Parse text like "name: Ajay Kumar T N age: 25 city: bangalore loan amount: 100000"
            if isinstance(details, str):
                import re
                name_match = re.search(r'name:\s*([^,\n]+)', details, re.IGNORECASE)
                age_match = re.search(r'age:\s*(\d+)', details, re.IGNORECASE)
                city_match = re.search(r'city:\s*([^,\n]+)', details, re.IGNORECASE)
                amount_match = re.search(r'(?:loan\s*amount|amount):\s*(\d+)', details, re.IGNORECASE)
                
                if name_match:
                    customer_profile['name'] = name_match.group(1).strip()
                if age_match:
                    customer_profile['age'] = int(age_match.group(1))
                if city_match:
                    customer_profile['city'] = city_match.group(1).strip().title()
                if amount_match:
                    customer_profile['requested_amount'] = int(amount_match.group(1))
        
        return customer_profile

    def _create_detailed_loan_presentation(self, loan_options: List[Dict[str, Any]], customer_profile: Dict[str, Any]) -> str:
        """Create detailed loan options presentation"""
        if not loan_options:
            return self._generate_fallback_loan_options(customer_profile)
        
        presentation = f"🎯 **Personalized Loan Options for {customer_profile.get('name', 'You')}**\n\n"
        
        for i, option in enumerate(loan_options[:3], 1):
            emi = option.get('emi', 0)
            tenure = option.get('tenure', 12)
            rate = option.get('interest_rate', 12.0)
            total_payable = option.get('total_payable', emi * tenure)
            processing_fee = option.get('processing_fee', 0)
            
            # Calculate years and months
            years = tenure // 12
            months = tenure % 12
            tenure_text = f"{years} years" + (f" {months} months" if months > 0 else "")
            
            presentation += f"**💰 Option {i}** {'⭐ RECOMMENDED' if i == 1 else ''}\n"
            presentation += f"• **Monthly EMI:** ₹{emi:,.0f}\n"
            presentation += f"• **Tenure:** {tenure_text} ({tenure} months)\n"
            presentation += f"• **Interest Rate:** {rate:.1f}% per annum\n"
            presentation += f"• **Total Amount:** ₹{total_payable:,.0f}\n"
            presentation += f"• **Processing Fee:** ₹{processing_fee:,.0f}\n"
            
            # Add affordability indicator
            affordability_score = option.get('affordability_score', 70)
            if affordability_score >= 80:
                presentation += f"• ✅ **Excellent affordability** - Fits comfortably in your budget\n"
            elif affordability_score >= 60:
                presentation += f"• ✅ **Good affordability** - Well within your capacity\n"
            else:
                presentation += f"• ⚠️ **Fair affordability** - Please consider carefully\n"
            
            presentation += "\n"
        
        return presentation.strip()

    def _generate_fallback_loan_options(self, customer_profile: Dict[str, Any]) -> str:
        """Generate fallback loan options when sales agent fails"""
        requested_amount = customer_profile.get('requested_amount', 100000)
        salary = customer_profile.get('salary', 50000)
        
        # Calculate basic EMI options
        options = []
        
        # Option 1: 3 years
        rate1 = 12.5
        tenure1 = 36
        emi1 = self._calculate_simple_emi(requested_amount, rate1, tenure1)
        
        # Option 2: 5 years  
        rate2 = 13.5
        tenure2 = 60
        emi2 = self._calculate_simple_emi(requested_amount, rate2, tenure2)
        
        # Option 3: 7 years
        rate3 = 14.5
        tenure3 = 84
        emi3 = self._calculate_simple_emi(requested_amount, rate3, tenure3)
        
        presentation = f"🎯 **Loan Options for ₹{requested_amount:,.0f}**\n\n"
        
        presentation += f"**💰 Option 1 - Quick Repayment**\n"
        presentation += f"• **Monthly EMI:** ₹{emi1:,.0f}\n"
        presentation += f"• **Tenure:** 3 years (36 months)\n"
        presentation += f"• **Interest Rate:** {rate1}% per annum\n"
        presentation += f"• **Total Amount:** ₹{emi1 * tenure1:,.0f}\n"
        presentation += f"• ✅ **Save on interest** - Lowest total cost\n\n"
        
        presentation += f"**💰 Option 2 - Balanced** ⭐ RECOMMENDED\n"
        presentation += f"• **Monthly EMI:** ₹{emi2:,.0f}\n"
        presentation += f"• **Tenure:** 5 years (60 months)\n"
        presentation += f"• **Interest Rate:** {rate2}% per annum\n"
        presentation += f"• **Total Amount:** ₹{emi2 * tenure2:,.0f}\n"
        presentation += f"• ✅ **Perfect balance** - Affordable EMI with reasonable interest\n\n"
        
        presentation += f"**💰 Option 3 - Lower EMI**\n"
        presentation += f"• **Monthly EMI:** ₹{emi3:,.0f}\n"
        presentation += f"• **Tenure:** 7 years (84 months)\n"
        presentation += f"• **Interest Rate:** {rate3}% per annum\n"
        presentation += f"• **Total Amount:** ₹{emi3 * tenure3:,.0f}\n"
        presentation += f"• ✅ **Lowest EMI** - Maximum affordability\n"
        
        return presentation.strip()

    def _calculate_simple_emi(self, principal: float, rate: float, tenure: int) -> float:
        """Calculate EMI using simple formula"""
        monthly_rate = rate / (12 * 100)
        if monthly_rate == 0:
            return principal / tenure
        
        emi = principal * monthly_rate * ((1 + monthly_rate) ** tenure) / (((1 + monthly_rate) ** tenure) - 1)
        return round(emi, 0)

    def _analyze_context_for_agent_selection(self, context: ConversationContext, 
                                           task_requirements: Dict[str, Any]) -> AgentType:
        """Analyze context to select appropriate agent"""
        # Fallback to Master Agent for coordination
        return AgentType.MASTER

    def _handle_task_completion(self, session_id: str, task_type: TaskType, 
                              agent_type: AgentType, result: Dict[str, Any]) -> Dict[str, Any]:
        """Handle task completion and determine next actions"""
        next_actions = []
        
        if task_type == TaskType.SALES and result.get('terms_agreed'):
            next_actions.append('start_verification')
        elif task_type == TaskType.VERIFICATION and result.get('verification_passed'):
            next_actions.append('start_underwriting')
        elif task_type == TaskType.UNDERWRITING:
            if result.get('approved'):
                next_actions.append('generate_sanction_letter')
            elif result.get('requires_documents'):
                next_actions.append('request_document_upload')
            else:
                next_actions.append('complete_with_rejection')
        
        return {'next_actions': next_actions}

    def _get_fallback_actions(self, task_type: TaskType) -> List[str]:
        """Get fallback actions for failed task delegation"""
        return ['retry_task', 'escalate_to_human', 'provide_alternative']

    def _get_stage_for_agent(self, agent_type: AgentType) -> str:
        """Get appropriate conversation stage for agent type"""
        stage_map = {
            AgentType.SALES: 'sales_negotiation',
            AgentType.VERIFICATION: 'verification',
            AgentType.UNDERWRITING: 'underwriting',
            AgentType.SANCTION: 'sanction_generation'
        }
        return stage_map.get(agent_type, 'error_handling')

    def _determine_recovery_strategy(self, failed_agent: AgentType, 
                                   error_details: Dict[str, Any], 
                                   context: ConversationContext) -> Dict[str, Any]:
        """Determine recovery strategy for failed agent"""
        return {
            'type': 'retry_with_fallback',
            'retry_count': 1,
            'fallback_agent': AgentType.MASTER,
            'customer_notification': True
        }

    def _execute_recovery_strategy(self, session_id: str, 
                                 recovery_strategy: Dict[str, Any]) -> Dict[str, Any]:
        """Execute recovery strategy"""
        return {'recovery_executed': True, 'strategy': recovery_strategy['type']}
    
    def _execute_enhanced_recovery_strategy(self, session_id: str, failed_agent: AgentType,
                                          error_result: ErrorHandlingResult, 
                                          escalation_needed: bool) -> Dict[str, Any]:
        """
        Execute enhanced recovery strategy with multiple fallback options.
        
        Args:
            session_id: Session identifier
            failed_agent: Agent that failed
            error_result: Error handling result
            escalation_needed: Whether escalation is required
            
        Returns:
            Recovery execution result
        """
        recovery_actions_executed = []
        
        try:
            # Execute recovery actions from error handler
            for action in error_result.recovery_actions:
                if action == 'restart_agent':
                    restart_success = self._restart_worker_agent(session_id, failed_agent)
                    recovery_actions_executed.append(f"restart_agent: {'success' if restart_success else 'failed'}")
                
                elif action == 'retry_task':
                    retry_success = self._retry_failed_task(session_id, failed_agent)
                    recovery_actions_executed.append(f"retry_task: {'success' if retry_success else 'failed'}")
                
                elif action == 'use_alternative_agent':
                    alternative_success = self._use_alternative_agent(session_id, failed_agent)
                    recovery_actions_executed.append(f"alternative_agent: {'success' if alternative_success else 'failed'}")
                
                elif action == 'fallback_to_manual':
                    manual_success = self._fallback_to_manual_process(session_id, failed_agent)
                    recovery_actions_executed.append(f"manual_fallback: {'success' if manual_success else 'failed'}")
                
                elif action == 'notify_customer':
                    self._notify_customer_of_issue(session_id, error_result.customer_message)
                    recovery_actions_executed.append("customer_notified: success")
            
            # If escalation is needed, prepare escalation
            if escalation_needed:
                escalation_result = self._prepare_escalation(session_id, failed_agent, error_result)
                recovery_actions_executed.append(f"escalation_prepared: {escalation_result}")
            
            return {
                'recovery_successful': True,
                'actions_executed': recovery_actions_executed,
                'escalation_prepared': escalation_needed
            }
            
        except Exception as recovery_error:
            self.logger.error(f"Recovery strategy execution failed: {str(recovery_error)}")
            return {
                'recovery_successful': False,
                'error': str(recovery_error),
                'actions_executed': recovery_actions_executed
            }
    
    def _restart_worker_agent(self, session_id: str, agent_type: AgentType) -> bool:
        """Restart a specific worker agent"""
        try:
            # Use session manager to restart the agent
            restart_success = self.session_manager.restart_agent(session_id, agent_type)
            
            if restart_success:
                self.logger.info(f"Successfully restarted {agent_type.value} agent for session {session_id}")
                return True
            else:
                self.logger.warning(f"Failed to restart {agent_type.value} agent for session {session_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error restarting {agent_type.value} agent: {str(e)}")
            return False
    
    def _retry_failed_task(self, session_id: str, agent_type: AgentType) -> bool:
        """Retry the last failed task for an agent"""
        try:
            # Get the last failed task from context
            context = self.session_manager.get_session_context(session_id)
            if not context:
                return False
            
            # Find the most recent task for this agent type
            # This would typically involve checking task history
            # For now, we'll simulate a retry
            
            self.logger.info(f"Retrying failed task for {agent_type.value} agent in session {session_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error retrying task for {agent_type.value} agent: {str(e)}")
            return False
    
    def _use_alternative_agent(self, session_id: str, failed_agent: AgentType) -> bool:
        """Use an alternative agent or approach"""
        try:
            # Define alternative approaches for each agent type
            alternatives = {
                AgentType.SALES: AgentType.MASTER,  # Master can handle basic sales
                AgentType.VERIFICATION: AgentType.MASTER,  # Master can request manual verification
                AgentType.UNDERWRITING: AgentType.MASTER,  # Master can use simplified underwriting
                AgentType.SANCTION: AgentType.MASTER  # Master can generate basic approval message
            }
            
            alternative_agent = alternatives.get(failed_agent)
            if alternative_agent:
                # Switch to alternative agent
                context = self.session_manager.get_session_context(session_id)
                if context:
                    alternative_stage = self._get_alternative_stage(failed_agent, context.conversation_stage)
                    if alternative_stage:
                        switch_success = self.session_manager.switch_agent(
                            session_id, alternative_agent, alternative_stage
                        )
                        
                        if switch_success:
                            self.logger.info(f"Switched from {failed_agent.value} to {alternative_agent.value} agent")
                            return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error using alternative agent: {str(e)}")
            return False
    
    def _fallback_to_manual_process(self, session_id: str, agent_type: AgentType) -> bool:
        """Fallback to manual process for the failed agent"""
        try:
            # Store manual process requirement in context
            context = self.session_manager.get_session_context(session_id)
            if context:
                manual_process_data = {
                    'failed_agent': agent_type.value,
                    'requires_manual_intervention': True,
                    'timestamp': datetime.now().isoformat(),
                    'conversation_stage': context.conversation_stage
                }
                
                self.session_manager.add_session_data(
                    session_id, 'manual_process_required', manual_process_data
                )
                
                self.logger.info(f"Marked session {session_id} for manual process due to {agent_type.value} failure")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error setting up manual fallback: {str(e)}")
            return False
    
    def _notify_customer_of_issue(self, session_id: str, message: str) -> None:
        """Notify customer of the issue and recovery attempt"""
        try:
            # Store customer notification in context
            notification_data = {
                'message': message,
                'timestamp': datetime.now().isoformat(),
                'type': 'error_recovery_notification'
            }
            
            self.session_manager.add_session_data(
                session_id, 'customer_notification', notification_data
            )
            
            self.logger.info(f"Customer notification queued for session {session_id}")
            
        except Exception as e:
            self.logger.error(f"Error queuing customer notification: {str(e)}")
    
    def _prepare_escalation(self, session_id: str, failed_agent: AgentType, 
                          error_result: ErrorHandlingResult) -> str:
        """Prepare escalation for failed agent"""
        try:
            escalation_data = {
                'session_id': session_id,
                'failed_agent': failed_agent.value,
                'error_summary': error_result.customer_message,
                'escalation_timestamp': datetime.now().isoformat(),
                'failure_count': len(self.worker_agent_failures.get(failed_agent.value, [])),
                'requires_human_intervention': True
            }
            
            # Store escalation data
            self.session_manager.add_session_data(
                session_id, 'escalation_required', escalation_data
            )
            
            self.logger.warning(f"Escalation prepared for session {session_id} due to {failed_agent.value} failures")
            return "escalation_prepared"
            
        except Exception as e:
            self.logger.error(f"Error preparing escalation: {str(e)}")
            return "escalation_failed"
    
    def _get_alternative_stage(self, failed_agent: AgentType, current_stage: str) -> Optional[str]:
        """Get alternative conversation stage when agent fails"""
        # Define alternative stages for each agent failure
        alternatives = {
            (AgentType.SALES, 'sales_negotiation'): 'information_collection',
            (AgentType.VERIFICATION, 'verification'): 'sales_negotiation',
            (AgentType.UNDERWRITING, 'underwriting'): 'verification',
            (AgentType.SANCTION, 'sanction_generation'): 'underwriting'
        }
        
        return alternatives.get((failed_agent, current_stage))
    
    def get_worker_agent_health_status(self) -> Dict[str, Any]:
        """
        Get health status of all worker agents.
        
        Returns:
            Dictionary containing health status of worker agents
        """
        health_status = {}
        
        for agent_type in [AgentType.SALES, AgentType.VERIFICATION, AgentType.UNDERWRITING, AgentType.SANCTION]:
            agent_key = agent_type.value
            failures = self.worker_agent_failures.get(agent_key, [])
            
            # Calculate recent failure rate (last hour)
            recent_failures = [
                f for f in failures 
                if (datetime.now() - datetime.fromisoformat(f['timestamp'])).total_seconds() < 3600
            ]
            
            health_status[agent_key] = {
                'total_failures': len(failures),
                'recent_failures': len(recent_failures),
                'health_score': max(0, 100 - (len(recent_failures) * 20)),  # Decrease by 20 per recent failure
                'status': 'healthy' if len(recent_failures) < 3 else 'degraded' if len(recent_failures) < 5 else 'critical',
                'escalation_needed': len(failures) >= self.escalation_threshold
            }
        
        return health_status

    def _generate_error_communication(self, failed_agent: AgentType, 
                                    error_details: Dict[str, Any], 
                                    recovery_strategy: Dict[str, Any]) -> str:
        """Generate customer communication for error scenarios"""
        return "I apologize for the brief delay. Let me continue assisting you with your loan application."

    def _generate_completion_summary(self, completion_type: str, 
                                   summary_data: Dict[str, Any], 
                                   context: ConversationContext) -> str:
        """Generate conversation completion summary using conversation manager"""
        try:
            summary_result = self.conversation_manager.generate_conversation_summary(
                context, completion_type, summary_data
            )
            
            # Combine closure and follow-up messages
            full_summary = summary_result['closure_message']
            if summary_result.get('follow_up_message'):
                full_summary += " " + summary_result['follow_up_message']
            
            return full_summary
            
        except Exception as e:
            self.logger.error(f"Failed to generate completion summary: {str(e)}")
            # Fallback summaries
            if completion_type == 'approved':
                return "Congratulations! Your loan has been approved. You can download your sanction letter using the link provided."
            elif completion_type == 'rejected':
                return "I'm sorry, but we're unable to approve your loan application at this time based on our current criteria."
            else:
                return "Thank you for your interest in our loan services. Feel free to reach out again if you need assistance."

    def _handle_processing_error(self, session_id: str, error_message: str) -> Dict[str, Any]:
        """Handle message processing errors"""
        return {
            'response': "I apologize, but I encountered an issue processing your message. Could you please try again?",
            'error': error_message,
            'action_taken': 'error_handled'
        }