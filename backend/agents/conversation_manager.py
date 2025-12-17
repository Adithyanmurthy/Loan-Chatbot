"""
Conversation Initiation and Management System
Implements personalized greeting, conversation state tracking, and closure functionality
Based on requirements: 1.1, 1.4, 6.4
"""

import logging
import uuid
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

from models.conversation import (
    ConversationContext, ChatMessage, AgentType, ErrorSeverity
)
from models.customer import CustomerProfile
from models.loan import LoanApplication


class ConversationManager:
    """
    Manages conversation initiation, state tracking, transitions, and closure.
    Provides personalized greetings and professional conversation management.
    """
    
    def __init__(self):
        """Initialize conversation manager with state tracking capabilities."""
        
        # Conversation stage definitions and transitions
        self.conversation_stages = {
            'initiation': {
                'description': 'Initial greeting and conversation startup',
                'next_stages': ['information_collection', 'underwriting', 'error_handling'],
                'required_data': [],
                'timeout_minutes': 5
            },
            'information_collection': {
                'description': 'Collecting basic customer information',
                'next_stages': ['sales_negotiation', 'underwriting', 'error_handling'],
                'required_data': ['name', 'age', 'city', 'loan_amount'],
                'timeout_minutes': 10
            },
            'sales_negotiation': {
                'description': 'Negotiating loan terms and conditions',
                'next_stages': ['verification', 'underwriting', 'error_handling'],
                'required_data': ['agreed_amount', 'agreed_tenure', 'agreed_rate'],
                'timeout_minutes': 15
            },
            'verification': {
                'description': 'Verifying customer identity and details',
                'next_stages': ['underwriting', 'error_handling'],
                'required_data': ['kyc_verified', 'phone_verified', 'address_verified'],
                'timeout_minutes': 10
            },
            'underwriting': {
                'description': 'Credit assessment and loan approval decision',
                'next_stages': ['sanction_generation', 'document_upload', 'completion', 'error_handling'],
                'required_data': ['credit_score', 'eligibility_decision'],
                'timeout_minutes': 5
            },
            'document_upload': {
                'description': 'Customer document upload and processing',
                'next_stages': ['underwriting', 'error_handling'],
                'required_data': ['salary_slip_uploaded', 'document_processed'],
                'timeout_minutes': 20
            },
            'sanction_generation': {
                'description': 'Generating loan sanction letter',
                'next_stages': ['completion', 'error_handling'],
                'required_data': ['sanction_letter_generated'],
                'timeout_minutes': 5
            },
            'completion': {
                'description': 'Conversation completion and closure',
                'next_stages': [],
                'required_data': ['completion_summary'],
                'timeout_minutes': 0
            },
            'error_handling': {
                'description': 'Handling errors and recovery',
                'next_stages': ['initiation', 'completion'],
                'required_data': [],
                'timeout_minutes': 10
            }
        }
        
        # Greeting templates for personalization
        self.greeting_templates = {
            'new_customer': [
                "Hello! Welcome to our personal loan service. I'm your AI assistant, and I'm here to help you find the perfect loan solution tailored to your needs.",
                "Hi there! Thanks for visiting us today. I'm here to make your loan application process as smooth and quick as possible.",
                "Welcome! I'm your personal loan advisor. Let's work together to find you the best loan option that fits your requirements."
            ],
            'returning_customer': [
                "Hello {name}! Welcome back. I see you're interested in our loan services again. How can I help you today?",
                "Hi {name}! Great to see you again. I'm here to assist you with your loan needs.",
                "Welcome back, {name}! I'm ready to help you with another loan application."
            ],
            'referred_customer': [
                "Hello! I understand you were referred to us for a personal loan. Welcome! I'm here to make this process easy for you.",
                "Hi! Thanks for choosing us based on a referral. I'm excited to help you with your loan requirements."
            ]
        }
        
        # Conversation closure templates
        self.closure_templates = {
            'approved': {
                'message': "Congratulations, {name}! Your loan of ₹{amount} has been approved. Your sanction letter is ready for download. Thank you for choosing our services!",
                'follow_up': "You can download your sanction letter using the link provided. If you have any questions, feel free to contact our support team."
            },
            'rejected': {
                'message': "Thank you for your interest, {name}. Unfortunately, we're unable to approve your loan application at this time based on our current lending criteria.",
                'follow_up': "We appreciate your time and encourage you to apply again in the future when your financial profile may better align with our requirements."
            },
            'cancelled': {
                'message': "I understand you've decided not to proceed with the loan application at this time, {name}.",
                'follow_up': "Thank you for considering our services. Feel free to reach out whenever you need financial assistance in the future."
            },
            'error': {
                'message': "I apologize, {name}, but we encountered some technical difficulties during your application process.",
                'follow_up': "Our team will review your application and contact you shortly. Thank you for your patience."
            }
        }
        
        # Set up logging
        self.logger = logging.getLogger("conversation_manager")
        self.logger.setLevel(logging.INFO)
        
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        
        self.logger.info("ConversationManager initialized with stage tracking and personalization")

    def generate_personalized_greeting(self, customer_id: Optional[str] = None, 
                                     customer_profile: Optional[CustomerProfile] = None,
                                     referral_source: Optional[str] = None,
                                     initial_message: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate personalized greeting based on customer context.
        
        Args:
            customer_id: Optional customer identifier
            customer_profile: Optional customer profile data
            referral_source: Optional referral source information
            initial_message: Optional initial message from customer
            
        Returns:
            Greeting information with message and context
        """
        try:
            # Determine customer type
            if customer_profile and customer_profile.name:
                customer_type = 'returning_customer'
                customer_name = customer_profile.name
            elif referral_source:
                customer_type = 'referred_customer'
                customer_name = None
            else:
                customer_type = 'new_customer'
                customer_name = None
            
            # Select appropriate greeting template
            templates = self.greeting_templates[customer_type]
            import random
            selected_template = random.choice(templates)
            
            # Personalize greeting if customer name is available
            if customer_name and '{name}' in selected_template:
                greeting_message = selected_template.format(name=customer_name)
            else:
                greeting_message = selected_template
            
            # Add context-specific follow-up
            follow_up = self._generate_greeting_follow_up(initial_message, customer_type)
            
            # Create greeting response
            greeting_response = {
                'greeting_message': greeting_message,
                'follow_up_message': follow_up,
                'customer_type': customer_type,
                'personalized': customer_name is not None,
                'conversation_starter': self._get_conversation_starter(initial_message),
                'expected_response': 'customer_loan_interest_or_information'
            }
            
            self.logger.info(f"Generated {customer_type} greeting for customer: {customer_id or 'anonymous'}")
            
            return greeting_response
            
        except Exception as e:
            self.logger.error(f"Failed to generate personalized greeting: {str(e)}")
            # Fallback to basic greeting
            return {
                'greeting_message': "Hello! Welcome to our personal loan service. How can I help you today?",
                'follow_up_message': "I'm here to assist you with finding the right loan solution.",
                'customer_type': 'unknown',
                'personalized': False,
                'conversation_starter': 'general_inquiry',
                'expected_response': 'customer_response'
            }

    def track_conversation_state(self, context: ConversationContext, 
                               new_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Track conversation state and manage transitions.
        
        Args:
            context: Current conversation context
            new_data: New data to add to conversation state
            
        Returns:
            State tracking result with transition information
        """
        try:
            current_stage = context.conversation_stage
            stage_config = self.conversation_stages.get(current_stage, {})
            
            # Add new data to context
            for key, value in new_data.items():
                context.add_collected_data(key, value)
            
            # Check stage completion
            completion_status = self._check_stage_completion(context, stage_config)
            
            # Determine next stage if current stage is complete
            next_stage_info = None
            if completion_status['completed']:
                next_stage_info = self._determine_next_stage(context, current_stage)
            
            # Calculate progress
            progress_info = self._calculate_conversation_progress(context)
            
            tracking_result = {
                'current_stage': current_stage,
                'stage_completed': completion_status['completed'],
                'completion_percentage': completion_status['completion_percentage'],
                'missing_data': completion_status['missing_data'],
                'next_stage': next_stage_info,
                'overall_progress': progress_info,
                'data_updated': True
            }
            
            self.logger.info(f"Tracked conversation state for session {context.session_id}: {current_stage}")
            
            return tracking_result
            
        except Exception as e:
            self.logger.error(f"Failed to track conversation state: {str(e)}")
            return {
                'current_stage': context.conversation_stage,
                'stage_completed': False,
                'data_updated': False,
                'error': str(e)
            }

    def manage_stage_transition(self, context: ConversationContext, 
                              target_stage: str, 
                              transition_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Manage transition between conversation stages.
        
        Args:
            context: Current conversation context
            target_stage: Target stage to transition to
            transition_data: Optional data for the transition
            
        Returns:
            Transition result with success status and information
        """
        try:
            current_stage = context.conversation_stage
            
            # Validate transition
            validation_result = self._validate_stage_transition(current_stage, target_stage)
            if not validation_result['valid']:
                return {
                    'transition_successful': False,
                    'error': validation_result['error'],
                    'current_stage': current_stage
                }
            
            # Prepare transition
            preparation_result = self._prepare_stage_transition(context, target_stage, transition_data)
            
            # Execute transition
            context.switch_agent(self._get_agent_for_stage(target_stage), target_stage)
            
            # Add transition metadata
            context.add_collected_data('stage_transition', {
                'from_stage': current_stage,
                'to_stage': target_stage,
                'transition_time': datetime.now().isoformat(),
                'transition_data': transition_data or {},
                'preparation_result': preparation_result
            })
            
            # Generate transition message
            transition_message = self._generate_transition_message(current_stage, target_stage)
            
            transition_result = {
                'transition_successful': True,
                'from_stage': current_stage,
                'to_stage': target_stage,
                'transition_message': transition_message,
                'preparation_result': preparation_result,
                'next_expected_actions': self._get_stage_expected_actions(target_stage)
            }
            
            self.logger.info(f"Successfully transitioned from {current_stage} to {target_stage} in session {context.session_id}")
            
            return transition_result
            
        except Exception as e:
            self.logger.error(f"Failed to manage stage transition: {str(e)}")
            return {
                'transition_successful': False,
                'error': str(e),
                'current_stage': context.conversation_stage
            }

    def generate_conversation_summary(self, context: ConversationContext, 
                                    completion_type: str,
                                    outcome_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate comprehensive conversation summary for closure.
        
        Args:
            context: Conversation context
            completion_type: Type of completion (approved, rejected, cancelled, error)
            outcome_data: Data about the conversation outcome
            
        Returns:
            Conversation summary with closure message
        """
        try:
            # Extract key conversation data
            customer_name = self._extract_customer_name(context)
            loan_amount = self._extract_loan_amount(context)
            conversation_duration = self._calculate_conversation_duration(context)
            
            # Generate closure message
            closure_info = self.closure_templates.get(completion_type, self.closure_templates['error'])
            
            # Personalize closure message
            closure_message = closure_info['message'].format(
                name=customer_name or 'there',
                amount=loan_amount or 'requested amount'
            )
            
            follow_up_message = closure_info['follow_up']
            
            # Create comprehensive summary
            summary = {
                'completion_type': completion_type,
                'closure_message': closure_message,
                'follow_up_message': follow_up_message,
                'conversation_summary': {
                    'session_id': context.session_id,
                    'customer_name': customer_name,
                    'loan_amount': loan_amount,
                    'stages_completed': self._get_completed_stages(context),
                    'duration_minutes': conversation_duration,
                    'total_messages': len(context.collected_data),
                    'errors_encountered': len(context.errors),
                    'outcome_data': outcome_data
                },
                'professional_closure': True,
                'summary_generated_at': datetime.now().isoformat()
            }
            
            self.logger.info(f"Generated conversation summary for session {context.session_id}: {completion_type}")
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Failed to generate conversation summary: {str(e)}")
            return {
                'completion_type': completion_type,
                'closure_message': "Thank you for your time. We appreciate your interest in our services.",
                'follow_up_message': "Please feel free to contact us if you need any assistance.",
                'error': str(e)
            }

    def handle_conversation_timeout(self, context: ConversationContext) -> Dict[str, Any]:
        """
        Handle conversation timeout scenarios.
        
        Args:
            context: Conversation context
            
        Returns:
            Timeout handling result
        """
        try:
            current_stage = context.conversation_stage
            stage_config = self.conversation_stages.get(current_stage, {})
            timeout_minutes = stage_config.get('timeout_minutes', 10)
            
            # Generate timeout message
            timeout_message = self._generate_timeout_message(current_stage, timeout_minutes)
            
            # Add timeout error to context
            context.add_error(
                message=f"Conversation timeout in stage: {current_stage}",
                severity=ErrorSeverity.MEDIUM,
                context={
                    'stage': current_stage,
                    'timeout_minutes': timeout_minutes,
                    'session_id': context.session_id
                }
            )
            
            # Determine timeout recovery action
            recovery_action = self._determine_timeout_recovery(current_stage, context)
            
            timeout_result = {
                'timeout_handled': True,
                'timeout_message': timeout_message,
                'recovery_action': recovery_action,
                'stage_at_timeout': current_stage,
                'timeout_duration': timeout_minutes
            }
            
            self.logger.warning(f"Handled conversation timeout in session {context.session_id}: {current_stage}")
            
            return timeout_result
            
        except Exception as e:
            self.logger.error(f"Failed to handle conversation timeout: {str(e)}")
            return {
                'timeout_handled': False,
                'error': str(e)
            }

    # Private helper methods
    
    def _generate_greeting_follow_up(self, initial_message: Optional[str], 
                                   customer_type: str) -> str:
        """Generate appropriate follow-up message for greeting"""
        if initial_message and 'loan' in initial_message.lower():
            return "I see you're interested in a personal loan. I'll be happy to help you find the best option for your needs."
        elif customer_type == 'returning_customer':
            return "What can I help you with today?"
        else:
            return "Whether you're looking for a personal loan or just exploring your options, I'm here to guide you through the process."

    def _get_conversation_starter(self, initial_message: Optional[str]) -> str:
        """Determine conversation starter type"""
        if not initial_message:
            return 'greeting_only'
        
        message_lower = initial_message.lower()
        if any(word in message_lower for word in ['loan', 'borrow', 'money', 'credit']):
            return 'loan_interest'
        elif any(word in message_lower for word in ['help', 'information', 'tell me']):
            return 'information_request'
        else:
            return 'general_inquiry'

    def _check_stage_completion(self, context: ConversationContext, 
                              stage_config: Dict[str, Any]) -> Dict[str, Any]:
        """Check if current stage requirements are completed"""
        required_data = stage_config.get('required_data', [])
        
        if not required_data:
            return {'completed': True, 'completion_percentage': 100, 'missing_data': []}
        
        collected_keys = set(context.collected_data.keys())
        required_keys = set(required_data)
        
        missing_data = list(required_keys - collected_keys)
        completed_count = len(required_keys - set(missing_data))
        completion_percentage = (completed_count / len(required_keys)) * 100 if required_keys else 100
        
        return {
            'completed': len(missing_data) == 0,
            'completion_percentage': completion_percentage,
            'missing_data': missing_data
        }

    def _determine_next_stage(self, context: ConversationContext, 
                            current_stage: str) -> Optional[Dict[str, Any]]:
        """Determine next stage based on context and current stage"""
        stage_config = self.conversation_stages.get(current_stage, {})
        possible_next_stages = stage_config.get('next_stages', [])
        
        if not possible_next_stages:
            return None
        
        # Logic to select appropriate next stage
        # This is simplified - in a real implementation, you'd have more complex logic
        if len(possible_next_stages) == 1:
            next_stage = possible_next_stages[0]
        else:
            # Default to first non-error stage
            next_stage = next(
                (stage for stage in possible_next_stages if stage != 'error_handling'),
                possible_next_stages[0]
            )
        
        return {
            'stage': next_stage,
            'reason': 'stage_completion',
            'possible_stages': possible_next_stages
        }

    def _calculate_conversation_progress(self, context: ConversationContext) -> Dict[str, Any]:
        """Calculate overall conversation progress"""
        all_stages = ['initiation', 'information_collection', 'sales_negotiation', 
                     'verification', 'underwriting', 'sanction_generation', 'completion']
        
        current_stage = context.conversation_stage
        
        if current_stage in all_stages:
            current_index = all_stages.index(current_stage)
            progress_percentage = (current_index / (len(all_stages) - 1)) * 100
        else:
            progress_percentage = 0
        
        return {
            'progress_percentage': progress_percentage,
            'current_stage_index': all_stages.index(current_stage) if current_stage in all_stages else -1,
            'total_stages': len(all_stages),
            'stages_remaining': len(all_stages) - all_stages.index(current_stage) - 1 if current_stage in all_stages else len(all_stages)
        }

    def _validate_stage_transition(self, current_stage: str, target_stage: str) -> Dict[str, Any]:
        """Validate if stage transition is allowed"""
        stage_config = self.conversation_stages.get(current_stage, {})
        allowed_next_stages = stage_config.get('next_stages', [])
        
        if target_stage in allowed_next_stages:
            return {'valid': True}
        else:
            return {
                'valid': False,
                'error': f"Invalid transition from {current_stage} to {target_stage}. Allowed: {allowed_next_stages}"
            }

    def _prepare_stage_transition(self, context: ConversationContext, 
                                target_stage: str, 
                                transition_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Prepare for stage transition"""
        return {
            'preparation_completed': True,
            'target_stage_config': self.conversation_stages.get(target_stage, {}),
            'transition_data_processed': transition_data is not None
        }

    def _get_agent_for_stage(self, stage: str) -> AgentType:
        """Get appropriate agent type for conversation stage"""
        agent_map = {
            'initiation': AgentType.MASTER,
            'information_collection': AgentType.MASTER,
            'sales_negotiation': AgentType.SALES,
            'verification': AgentType.VERIFICATION,
            'underwriting': AgentType.UNDERWRITING,
            'document_upload': AgentType.VERIFICATION,
            'sanction_generation': AgentType.SANCTION,
            'completion': AgentType.MASTER,
            'error_handling': AgentType.MASTER
        }
        return agent_map.get(stage, AgentType.MASTER)

    def _generate_transition_message(self, from_stage: str, to_stage: str) -> str:
        """Generate message for stage transition"""
        transition_messages = {
            ('initiation', 'information_collection'): "Great! Let me collect some basic information to get started.",
            ('information_collection', 'sales_negotiation'): "Perfect! Now let me present you with some attractive loan options.",
            ('sales_negotiation', 'verification'): "Excellent! Let me verify your details to proceed with the application.",
            ('verification', 'underwriting'): "Great! Now I'll assess your loan eligibility.",
            ('underwriting', 'sanction_generation'): "Congratulations! Your loan has been approved. Let me generate your sanction letter.",
            ('underwriting', 'document_upload'): "I need some additional documentation to complete your application.",
            ('document_upload', 'underwriting'): "Thank you for the documents. Let me complete the assessment.",
            ('sanction_generation', 'completion'): "Your sanction letter is ready! Let me provide you with the details."
        }
        
        key = (from_stage, to_stage)
        return transition_messages.get(key, f"Moving to the next step of your application process.")

    def _get_stage_expected_actions(self, stage: str) -> List[str]:
        """Get expected actions for a conversation stage"""
        actions_map = {
            'initiation': ['provide_greeting', 'wait_for_response'],
            'information_collection': ['collect_name', 'collect_age', 'collect_city', 'collect_loan_amount'],
            'sales_negotiation': ['present_offers', 'negotiate_terms', 'handle_objections'],
            'verification': ['verify_kyc', 'verify_phone', 'verify_address'],
            'underwriting': ['fetch_credit_score', 'assess_eligibility', 'make_decision'],
            'document_upload': ['request_documents', 'process_documents', 'validate_documents'],
            'sanction_generation': ['generate_pdf', 'provide_download_link'],
            'completion': ['provide_summary', 'close_conversation'],
            'error_handling': ['diagnose_error', 'provide_recovery', 'communicate_with_customer']
        }
        return actions_map.get(stage, [])

    def _extract_customer_name(self, context: ConversationContext) -> Optional[str]:
        """Extract customer name from conversation context"""
        name_data = context.collected_data.get('name') or context.collected_data.get('customer_name')
        return name_data['value'] if name_data else None

    def _extract_loan_amount(self, context: ConversationContext) -> Optional[str]:
        """Extract loan amount from conversation context"""
        amount_data = context.collected_data.get('loan_amount') or context.collected_data.get('requested_amount')
        if amount_data:
            amount = amount_data['value']
            return f"₹{amount:,}" if isinstance(amount, (int, float)) else str(amount)
        return None

    def _calculate_conversation_duration(self, context: ConversationContext) -> int:
        """Calculate conversation duration in minutes"""
        # Simplified calculation - in real implementation, you'd track start time
        return 10  # Default duration

    def _get_completed_stages(self, context: ConversationContext) -> List[str]:
        """Get list of completed conversation stages"""
        # Simplified - in real implementation, you'd track stage completion
        current_stage = context.conversation_stage
        all_stages = ['initiation', 'information_collection', 'sales_negotiation', 
                     'verification', 'underwriting', 'sanction_generation', 'completion']
        
        if current_stage in all_stages:
            current_index = all_stages.index(current_stage)
            return all_stages[:current_index + 1]
        
        return [current_stage]

    def _generate_timeout_message(self, stage: str, timeout_minutes: int) -> str:
        """Generate timeout message for stage"""
        return f"I notice we haven't heard from you in a while. Are you still there? I'm here to help you continue with your loan application."

    def _determine_timeout_recovery(self, stage: str, context: ConversationContext) -> str:
        """Determine recovery action for timeout"""
        if stage in ['initiation', 'information_collection']:
            return 'restart_conversation'
        elif stage in ['completion']:
            return 'close_conversation'
        else:
            return 'resume_from_current_stage'