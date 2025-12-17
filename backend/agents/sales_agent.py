"""
Sales Agent Implementation
Implements loan term presentation, negotiation, customer objection handling, and financial capacity assessment
Based on requirements: 2.1, 2.2, 2.3
"""

import logging
import uuid
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

from models.conversation import ConversationContext, AgentTask, TaskType, AgentType
from models.customer import CustomerProfile
from models.loan import LoanApplication, LoanStatus
from .base_agent import BaseAgent
from services.loan_calculator import LoanCalculator, LoanTerms


class SalesAgent(BaseAgent):
    """
    Sales Agent responsible for loan term negotiation and customer engagement.
    Handles loan presentation, objection handling, and financial capacity assessment.
    """
    
    def __init__(self, agent_id: Optional[str] = None):
        """
        Initialize Sales Agent with negotiation capabilities.
        
        Args:
            agent_id: Optional unique identifier for the agent
        """
        super().__init__(AgentType.SALES, agent_id)
        
        # Initialize loan calculator service
        self.loan_calculator = LoanCalculator()
        
        # Interest rate ranges based on credit score and loan amount
        self.interest_rate_matrix = {
            'excellent': {'min': 10.5, 'max': 12.0},  # Credit score 800+
            'good': {'min': 12.0, 'max': 14.5},       # Credit score 750-799
            'fair': {'min': 14.5, 'max': 17.0},       # Credit score 700-749
            'poor': {'min': 17.0, 'max': 20.0}        # Credit score 650-699
        }
        
        # Tenure options (in months)
        self.tenure_options = [6, 12, 18, 24, 36, 48, 60, 72, 84, 96, 120]
        
        # Processing fee structure
        self.processing_fee_rates = {
            'standard': 0.02,  # 2% of loan amount
            'premium': 0.015,  # 1.5% for high-value customers
            'promotional': 0.01  # 1% for special offers
        }
        
        # Objection handling strategies
        self.objection_strategies = {
            'high_interest': self._handle_interest_rate_objection,
            'high_emi': self._handle_emi_objection,
            'long_tenure': self._handle_tenure_objection,
            'processing_fee': self._handle_processing_fee_objection,
            'general_concern': self._handle_general_objection
        }
        
        self.logger.info("Sales Agent initialized with negotiation and objection handling capabilities")

    def _execute_task_logic(self, task: AgentTask) -> Dict[str, Any]:
        """
        Execute Sales Agent specific task logic.
        
        Args:
            task: AgentTask to execute
            
        Returns:
            Task execution result
        """
        task_handlers = {
            'start_negotiation': self._handle_negotiation_start,
            'present_terms': self._handle_term_presentation,
            'handle_objection': self._handle_objection_processing,
            'finalize_terms': self._handle_term_finalization,
            'assess_capacity': self._handle_capacity_assessment,
            'provide_alternatives': self._handle_alternative_options
        }
        
        task_action = task.input.get('action')
        if task_action not in task_handlers:
            raise ValueError(f"Unknown Sales Agent task action: {task_action}")
        
        return task_handlers[task_action](task.input)

    def can_execute_task(self, task_type: TaskType) -> bool:
        """
        Sales Agent can execute sales-related tasks.
        
        Args:
            task_type: Type of task to check
            
        Returns:
            True if agent can execute sales tasks
        """
        return task_type == TaskType.SALES

    def negotiate_loan_terms(self, customer_profile: CustomerProfile, 
                           requested_amount: float, preferred_tenure: Optional[int] = None) -> Dict[str, Any]:
        """
        Negotiate loan terms based on customer profile and preferences.
        
        Args:
            customer_profile: Customer profile information
            requested_amount: Requested loan amount
            preferred_tenure: Customer's preferred tenure (optional)
            
        Returns:
            Negotiated loan terms and presentation
        """
        try:
            # Assess financial capacity
            capacity_assessment = self._assess_financial_capacity(customer_profile, requested_amount)
            
            # Determine appropriate interest rate
            interest_rate = self._calculate_interest_rate(customer_profile, requested_amount)
            
            # Generate tenure options
            tenure_options = self._generate_tenure_options(
                requested_amount, interest_rate, customer_profile, preferred_tenure
            )
            
            # Create loan options using loan calculator
            loan_options = []
            for tenure in tenure_options[:3]:  # Present top 3 options
                loan_terms = self.loan_calculator.calculate_loan_terms(
                    requested_amount, interest_rate, tenure
                )
                
                # Assess affordability
                affordability = self.loan_calculator.assess_affordability(customer_profile, loan_terms)
                
                loan_option = {
                    'amount': loan_terms.amount,
                    'tenure': loan_terms.tenure,
                    'interest_rate': loan_terms.interest_rate,
                    'emi': loan_terms.emi,
                    'total_payable': loan_terms.total_payable,
                    'processing_fee': loan_terms.processing_fee,
                    'affordability_score': self._convert_affordability_to_score(affordability),
                    'is_affordable': affordability.is_affordable,
                    'risk_level': affordability.risk_level
                }
                loan_options.append(loan_option)
            
            # Generate presentation message
            presentation = self._generate_loan_presentation(loan_options, capacity_assessment)
            
            # Store negotiation data in context
            if self.context:
                self.share_context_data('loan_options', loan_options)
                self.share_context_data('capacity_assessment', capacity_assessment)
                self.share_context_data('negotiation_stage', 'terms_presented')
            
            self.logger.info(f"Generated loan terms for customer {customer_profile.id}: {len(loan_options)} options")
            
            return {
                'negotiation_successful': True,
                'loan_options': loan_options,
                'presentation_message': presentation,
                'capacity_assessment': capacity_assessment,
                'recommended_option': loan_options[0] if loan_options else None
            }
            
        except Exception as e:
            self.logger.error(f"Loan term negotiation failed: {str(e)}")
            return {
                'negotiation_successful': False,
                'error': str(e),
                'fallback_message': "I apologize, but I'm having trouble calculating your loan options. Let me try a different approach."
            }

    def handle_customer_objection(self, objection_text: str, current_terms: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle customer objections with appropriate alternatives.
        
        Args:
            objection_text: Customer's objection or concern
            current_terms: Currently proposed loan terms
            
        Returns:
            Objection handling result with alternatives
        """
        try:
            # Analyze objection type
            objection_type = self._analyze_objection_type(objection_text)
            
            # Get appropriate strategy
            strategy_handler = self.objection_strategies.get(
                objection_type, self.objection_strategies['general_concern']
            )
            
            # Execute objection handling strategy
            handling_result = strategy_handler(objection_text, current_terms)
            
            # Update context with objection handling
            if self.context:
                objection_data = {
                    'objection_text': objection_text,
                    'objection_type': objection_type,
                    'handling_result': handling_result,
                    'timestamp': datetime.now().isoformat()
                }
                self.share_context_data('objections_handled', objection_data)
            
            self.logger.info(f"Handled customer objection of type: {objection_type}")
            
            return {
                'objection_handled': True,
                'objection_type': objection_type,
                'response_message': handling_result['response'],
                'alternative_options': handling_result.get('alternatives', []),
                'next_action': handling_result.get('next_action', 'continue_negotiation')
            }
            
        except Exception as e:
            self.logger.error(f"Objection handling failed: {str(e)}")
            return {
                'objection_handled': False,
                'error': str(e),
                'fallback_response': "I understand your concern. Let me see what other options I can offer you."
            }

    def assess_financial_capacity(self, customer_profile: CustomerProfile, 
                                requested_amount: float) -> Dict[str, Any]:
        """
        Assess customer's financial capacity for the requested loan amount.
        
        Args:
            customer_profile: Customer profile information
            requested_amount: Requested loan amount
            
        Returns:
            Financial capacity assessment result
        """
        try:
            assessment = self._assess_financial_capacity(customer_profile, requested_amount)
            
            # Store assessment in context
            if self.context:
                self.share_context_data('financial_assessment', assessment)
            
            self.logger.info(f"Completed financial capacity assessment for customer {customer_profile.id}")
            
            return {
                'assessment_completed': True,
                'capacity_result': assessment,
                'recommendation': self._generate_capacity_recommendation(assessment)
            }
            
        except Exception as e:
            self.logger.error(f"Financial capacity assessment failed: {str(e)}")
            return {
                'assessment_completed': False,
                'error': str(e)
            }

    # Private helper methods for task handlers
    
    def _handle_negotiation_start(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle negotiation start task"""
        try:
            # Try to get customer profile from shared data first
            customer_data = self.get_shared_data('customer_profile')
            
            # If not available in shared data, try from input_data
            if not customer_data:
                customer_data = input_data.get('customer_profile')
            
            if not customer_data:
                self.logger.error("Customer profile not available in shared data or input")
                return {
                    'negotiation_successful': False,
                    'error': 'Customer profile not available',
                    'fallback_message': 'I need some basic information to calculate your loan options. Could you please provide your details?'
                }
            
            # Create CustomerProfile object
            if isinstance(customer_data, dict):
                # Convert dict to CustomerProfile
                customer_profile = CustomerProfile(
                    id=customer_data.get('id', 'GUEST_USER'),
                    name=customer_data.get('name', 'Valued Customer'),
                    age=customer_data.get('age', 25),
                    city=customer_data.get('city', 'Bangalore'),
                    phone=customer_data.get('phone', '9876543210'),
                    address=customer_data.get('address', 'Bangalore, Karnataka'),
                    current_loans=customer_data.get('current_loans', []),
                    credit_score=customer_data.get('credit_score', 750),
                    pre_approved_limit=customer_data.get('pre_approved_limit', 500000),
                    employment_type=customer_data.get('employment_type', 'salaried'),
                    salary=customer_data.get('salary', 50000)
                )
            else:
                customer_profile = customer_data
            
            # Get requested amount - prioritize from customer data
            requested_amount = customer_data.get('requested_amount') or input_data.get('requested_amount', customer_profile.pre_approved_limit)
            
            self.logger.info(f"Starting loan negotiation for customer {customer_profile.name}, amount: ₹{requested_amount:,.0f}")
            
            # Call the main negotiation method
            negotiation_result = self.negotiate_loan_terms(customer_profile, requested_amount)
            
            # Ensure we have a proper presentation message
            if negotiation_result.get('negotiation_successful') and negotiation_result.get('loan_options'):
                if not negotiation_result.get('presentation_message'):
                    # Generate presentation if missing
                    loan_options = negotiation_result['loan_options']
                    presentation = self._generate_enhanced_loan_presentation(loan_options, customer_profile, requested_amount)
                    negotiation_result['presentation_message'] = presentation
            
            return negotiation_result
            
        except Exception as e:
            self.logger.error(f"Error in negotiation start: {str(e)}")
            return {
                'negotiation_successful': False,
                'error': str(e),
                'fallback_message': 'I apologize for the technical issue. Let me try to calculate your loan options manually.'
            }

    def _handle_term_presentation(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle term presentation task"""
        loan_options = input_data.get('loan_options', [])
        if not loan_options:
            loan_options = self.get_shared_data('loan_options') or []
        
        presentation = self._generate_loan_presentation(loan_options, {})
        return {
            'presentation_generated': True,
            'presentation_message': presentation,
            'options_count': len(loan_options)
        }

    def _handle_objection_processing(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle objection processing task"""
        objection = input_data.get('objection', '')
        current_terms = input_data.get('current_terms', {})
        
        if not current_terms:
            current_terms = self.get_shared_data('loan_options', [{}])[0]
        
        return self.handle_customer_objection(objection, current_terms)

    def _handle_term_finalization(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle term finalization task"""
        selected_option = input_data.get('selected_option', {})
        
        if self.context:
            self.share_context_data('finalized_terms', selected_option)
            self.share_context_data('negotiation_stage', 'terms_agreed')
        
        return {
            'terms_finalized': True,
            'final_terms': selected_option,
            'next_stage': 'verification'
        }

    def _handle_capacity_assessment(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle capacity assessment task"""
        customer_data = self.get_shared_data('customer_profile')
        if not customer_data:
            return {'error': 'Customer profile not available'}
        
        customer_profile = CustomerProfile.from_dict(customer_data)
        requested_amount = input_data.get('requested_amount', 0)
        
        return self.assess_financial_capacity(customer_profile, requested_amount)

    def _handle_alternative_options(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle alternative options generation task"""
        customer_data = self.get_shared_data('customer_profile')
        if not customer_data:
            return {'error': 'Customer profile not available'}
        
        customer_profile = CustomerProfile.from_dict(customer_data)
        constraints = input_data.get('constraints', {})
        
        alternatives = self._generate_alternative_options(customer_profile, constraints)
        
        return {
            'alternatives_generated': True,
            'alternative_options': alternatives,
            'options_count': len(alternatives)
        }

    # Private calculation and assessment methods
    
    def _assess_financial_capacity(self, customer_profile: CustomerProfile, 
                                 requested_amount: float) -> Dict[str, Any]:
        """Assess customer's financial capacity"""
        assessment = {
            'customer_id': customer_profile.id,
            'requested_amount': requested_amount,
            'pre_approved_limit': customer_profile.pre_approved_limit,
            'credit_score': customer_profile.credit_score,
            'current_debt_ratio': customer_profile.calculate_debt_to_income_ratio(),
            'available_income': customer_profile.get_available_income(),
            'assessment_timestamp': datetime.now().isoformat()
        }
        
        # Calculate capacity metrics
        assessment['amount_to_limit_ratio'] = requested_amount / customer_profile.pre_approved_limit if customer_profile.pre_approved_limit > 0 else float('inf')
        assessment['within_pre_approved'] = requested_amount <= customer_profile.pre_approved_limit
        assessment['within_2x_limit'] = requested_amount <= (customer_profile.pre_approved_limit * 2)
        
        # Determine capacity level
        if assessment['within_pre_approved']:
            assessment['capacity_level'] = 'excellent'
        elif assessment['within_2x_limit']:
            assessment['capacity_level'] = 'good'
        else:
            assessment['capacity_level'] = 'limited'
        
        # Calculate recommended amount
        if customer_profile.salary:
            max_emi_capacity = customer_profile.salary * 0.5  # 50% of salary
            current_emi_burden = sum(loan.emi for loan in customer_profile.current_loans)
            available_emi_capacity = max_emi_capacity - current_emi_burden
            
            # Estimate maximum loan amount based on available EMI capacity
            estimated_rate = self._calculate_interest_rate(customer_profile, requested_amount)
            estimated_tenure = 60  # 5 years default
            
            if available_emi_capacity > 0:
                # Calculate maximum amount for available EMI capacity
                monthly_rate = estimated_rate / (12 * 100)
                if monthly_rate > 0:
                    max_amount = available_emi_capacity * ((1 + monthly_rate) ** estimated_tenure - 1) / (monthly_rate * (1 + monthly_rate) ** estimated_tenure)
                else:
                    max_amount = available_emi_capacity * estimated_tenure
                
                assessment['recommended_amount'] = min(max_amount, customer_profile.pre_approved_limit * 2)
            else:
                assessment['recommended_amount'] = 0
            
            assessment['available_emi_capacity'] = available_emi_capacity
        else:
            assessment['recommended_amount'] = customer_profile.pre_approved_limit
            assessment['available_emi_capacity'] = None
        
        return assessment

    def _calculate_interest_rate(self, customer_profile: CustomerProfile, 
                               loan_amount: float) -> float:
        """Calculate appropriate interest rate based on customer profile"""
        credit_score = customer_profile.credit_score
        
        # Determine credit category
        if credit_score >= 800:
            category = 'excellent'
        elif credit_score >= 750:
            category = 'good'
        elif credit_score >= 700:
            category = 'fair'
        else:
            category = 'poor'
        
        rate_range = self.interest_rate_matrix[category]
        
        # Adjust rate based on loan amount relative to pre-approved limit
        amount_ratio = loan_amount / customer_profile.pre_approved_limit if customer_profile.pre_approved_limit > 0 else 2
        
        if amount_ratio <= 0.5:
            # Lower amount, better rate
            rate = rate_range['min']
        elif amount_ratio <= 1.0:
            # Within pre-approved, standard rate
            rate = rate_range['min'] + (rate_range['max'] - rate_range['min']) * 0.3
        elif amount_ratio <= 2.0:
            # Up to 2x limit, higher rate
            rate = rate_range['min'] + (rate_range['max'] - rate_range['min']) * 0.7
        else:
            # Above 2x limit, maximum rate
            rate = rate_range['max']
        
        return round(rate, 2)

    def _generate_tenure_options(self, amount: float, interest_rate: float, 
                               customer_profile: CustomerProfile, 
                               preferred_tenure: Optional[int] = None) -> List[int]:
        """Generate appropriate tenure options"""
        suitable_tenures = []
        
        for tenure in self.tenure_options:
            loan_terms = self.loan_calculator.calculate_loan_terms(amount, interest_rate, tenure)
            
            # Check affordability using loan calculator
            affordability = self.loan_calculator.assess_affordability(customer_profile, loan_terms)
            
            if affordability.is_affordable or not customer_profile.salary:
                suitable_tenures.append(tenure)
        
        # Sort by preference: preferred tenure first, then by EMI affordability
        if preferred_tenure and preferred_tenure in suitable_tenures:
            suitable_tenures.remove(preferred_tenure)
            suitable_tenures.insert(0, preferred_tenure)
        
        return suitable_tenures[:5]  # Return top 5 options

    def _convert_affordability_to_score(self, affordability) -> float:
        """Convert affordability assessment to score (0-100)"""
        if affordability.risk_level == 'low':
            return 100.0
        elif affordability.risk_level == 'medium':
            return 70.0
        else:
            return 40.0

    def _get_processing_fee_type(self, amount: float, customer_profile: CustomerProfile) -> str:
        """Determine processing fee type based on customer profile"""
        if customer_profile.credit_score >= 800 and amount >= 500000:
            return 'premium'
        elif amount <= 100000:
            return 'promotional'
        else:
            return 'standard'

    def _generate_loan_presentation(self, loan_options: List[Dict[str, Any]], 
                                  capacity_assessment: Dict[str, Any]) -> str:
        """Generate loan presentation message"""
        if not loan_options:
            return "I apologize, but I'm unable to generate suitable loan options at this time. Let me review your requirements again."
        
        presentation = "Based on your profile, I have some excellent loan options for you:\n\n"
        
        for i, option in enumerate(loan_options, 1):
            presentation += f"**Option {i}:**\n"
            presentation += f"• Loan Amount: ₹{option['amount']:,.0f}\n"
            presentation += f"• Tenure: {option['tenure']} months ({option['tenure']//12} years {option['tenure']%12} months)\n"
            presentation += f"• Interest Rate: {option['interest_rate']}% per annum\n"
            presentation += f"• Monthly EMI: ₹{option['emi']:,.0f}\n"
            presentation += f"• Total Amount Payable: ₹{option['total_payable']:,.0f}\n"
            presentation += f"• Processing Fee: ₹{option['processing_fee']:,.0f}\n"
            
            if option['affordability_score'] >= 80:
                presentation += "• Affordability: Excellent ✅\n\n"
            elif option['affordability_score'] >= 60:
                presentation += "• Affordability: Good ✅\n\n"
            else:
                presentation += "• Affordability: Fair ⚠️\n\n"
        
        presentation += "Which option would you prefer, or would you like me to adjust any terms?"
        
        return presentation

    def _generate_enhanced_loan_presentation(self, loan_options: List[Dict[str, Any]], 
                                           customer_profile: CustomerProfile, 
                                           requested_amount: float) -> str:
        """Generate enhanced loan presentation with better formatting"""
        if not loan_options:
            return f"I'm working on calculating the best loan options for ₹{requested_amount:,.0f}. Let me present some preliminary options."
        
        customer_name = customer_profile.name if hasattr(customer_profile, 'name') else customer_profile.get('name', 'Valued Customer')
        
        presentation = f"🎯 **Excellent News {customer_name}!**\n\n"
        presentation += f"I've calculated personalized loan options for ₹{requested_amount:,.0f} based on your profile:\n\n"
        
        for i, option in enumerate(loan_options[:3], 1):  # Show top 3 options
            emi = option.get('emi', 0)
            tenure = option.get('tenure', 12)
            rate = option.get('interest_rate', 12.0)
            total_payable = option.get('total_payable', emi * tenure)
            processing_fee = option.get('processing_fee', 0)
            
            # Calculate years and months
            years = tenure // 12
            months = tenure % 12
            tenure_text = f"{years} years" + (f" {months} months" if months > 0 else "")
            
            # Add recommendation badge for best option
            badge = " ⭐ **RECOMMENDED**" if i == 1 else ""
            
            presentation += f"**💰 Option {i}{badge}**\n"
            presentation += f"• **Monthly EMI:** ₹{emi:,.0f}\n"
            presentation += f"• **Tenure:** {tenure_text} ({tenure} months)\n"
            presentation += f"• **Interest Rate:** {rate:.1f}% per annum\n"
            presentation += f"• **Total Amount:** ₹{total_payable:,.0f}\n"
            presentation += f"• **Processing Fee:** ₹{processing_fee:,.0f}\n"
            
            # Add affordability indicator with better descriptions
            affordability_score = option.get('affordability_score', 70)
            if affordability_score >= 80:
                presentation += f"• ✅ **Excellent Fit** - Comfortably within your budget\n"
            elif affordability_score >= 60:
                presentation += f"• ✅ **Good Option** - Well-suited for your income\n"
            else:
                presentation += f"• ⚠️ **Consider Carefully** - Higher EMI relative to income\n"
            
            presentation += "\n"
        
        presentation += "💡 **Which option interests you most, or would you like me to adjust any terms?**\n"
        presentation += "I can modify the loan amount, tenure, or show you more options!"
        
        return presentation

    # Objection handling methods
    
    def _analyze_objection_type(self, objection_text: str) -> str:
        """Analyze customer objection to determine type"""
        objection_lower = objection_text.lower()
        
        if any(word in objection_lower for word in ['interest', 'rate', 'expensive', 'high rate']):
            return 'high_interest'
        elif any(word in objection_lower for word in ['emi', 'monthly', 'payment', 'installment']):
            return 'high_emi'
        elif any(word in objection_lower for word in ['tenure', 'duration', 'long', 'years']):
            return 'long_tenure'
        elif any(word in objection_lower for word in ['fee', 'charges', 'processing']):
            return 'processing_fee'
        else:
            return 'general_concern'

    def _handle_interest_rate_objection(self, objection: str, current_terms: Dict[str, Any]) -> Dict[str, Any]:
        """Handle interest rate objection"""
        # Try to offer slightly better rate or explain value proposition
        current_rate = current_terms.get('interest_rate', 15.0)
        
        if current_rate > 12.0:
            # Offer a small reduction if possible
            better_rate = max(10.5, current_rate - 0.5)
            alternative_terms = self.loan_calculator.calculate_loan_terms(
                current_terms['amount'], better_rate, current_terms['tenure']
            )
            alternative_emi = alternative_terms.emi
            
            response = f"I understand your concern about the interest rate. Let me see if I can offer you a better rate of {better_rate}% which would bring your EMI down to ₹{alternative_emi:,.0f}. This is a competitive rate given your profile."
            
            alternatives = [{
                **current_terms,
                'interest_rate': better_rate,
                'emi': alternative_emi,
                'total_payable': alternative_emi * current_terms['tenure']
            }]
        else:
            response = f"I understand your concern. The rate of {current_rate}% is actually quite competitive in the current market. However, let me show you how choosing a longer tenure can reduce your monthly EMI."
            
            # Offer longer tenure option
            longer_tenure = min(120, current_terms['tenure'] + 24)
            longer_terms = self.loan_calculator.calculate_loan_terms(
                current_terms['amount'], current_rate, longer_tenure
            )
            longer_emi = longer_terms.emi
            
            alternatives = [{
                **current_terms,
                'tenure': longer_tenure,
                'emi': longer_emi,
                'total_payable': longer_emi * longer_tenure
            }]
        
        return {
            'response': response,
            'alternatives': alternatives,
            'next_action': 'present_alternatives'
        }

    def _handle_emi_objection(self, objection: str, current_terms: Dict[str, Any]) -> Dict[str, Any]:
        """Handle EMI objection"""
        current_emi = current_terms.get('emi', 0)
        current_amount = current_terms.get('amount', 0)
        current_rate = current_terms.get('interest_rate', 15.0)
        
        # Offer longer tenure to reduce EMI
        longer_tenure = min(120, current_terms.get('tenure', 60) + 24)
        longer_terms = self.loan_calculator.calculate_loan_terms(current_amount, current_rate, longer_tenure)
        reduced_emi = longer_terms.emi
        
        # Also offer reduced amount option
        reduced_amount = current_amount * 0.8
        reduced_terms = self.loan_calculator.calculate_loan_terms(reduced_amount, current_rate, current_terms.get('tenure', 60))
        reduced_amount_emi = reduced_terms.emi
        
        response = f"I understand the EMI of ₹{current_emi:,.0f} might be a stretch. I have two solutions: Option 1 - Extend the tenure to {longer_tenure} months, reducing your EMI to ₹{reduced_emi:,.0f}. Option 2 - Reduce the loan amount to ₹{reduced_amount:,.0f} with an EMI of ₹{reduced_amount_emi:,.0f}."
        
        alternatives = [
            {
                **current_terms,
                'tenure': longer_tenure,
                'emi': reduced_emi,
                'total_payable': reduced_emi * longer_tenure
            },
            {
                **current_terms,
                'amount': reduced_amount,
                'emi': reduced_amount_emi,
                'total_payable': reduced_amount_emi * current_terms.get('tenure', 60)
            }
        ]
        
        return {
            'response': response,
            'alternatives': alternatives,
            'next_action': 'present_alternatives'
        }

    def _handle_tenure_objection(self, objection: str, current_terms: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tenure objection"""
        current_tenure = current_terms.get('tenure', 60)
        current_amount = current_terms.get('amount', 0)
        current_rate = current_terms.get('interest_rate', 15.0)
        
        # Offer shorter tenure options
        shorter_tenure = max(12, current_tenure - 24)
        shorter_terms = self.loan_calculator.calculate_loan_terms(current_amount, current_rate, shorter_tenure)
        shorter_emi = shorter_terms.emi
        
        response = f"I understand you'd prefer a shorter repayment period. With a {shorter_tenure}-month tenure, your EMI would be ₹{shorter_emi:,.0f}, but you'll save significantly on total interest."
        
        total_savings = (current_terms.get('emi', 0) * current_tenure) - (shorter_emi * shorter_tenure)
        
        if total_savings > 0:
            response += f" You'll save ₹{total_savings:,.0f} in total interest payments."
        
        alternatives = [{
            **current_terms,
            'tenure': shorter_tenure,
            'emi': shorter_emi,
            'total_payable': shorter_emi * shorter_tenure
        }]
        
        return {
            'response': response,
            'alternatives': alternatives,
            'next_action': 'present_alternatives'
        }

    def _handle_processing_fee_objection(self, objection: str, current_terms: Dict[str, Any]) -> Dict[str, Any]:
        """Handle processing fee objection"""
        current_fee = current_terms.get('processing_fee', 0)
        
        # Offer to waive or reduce processing fee
        reduced_fee = current_fee * 0.5
        
        response = f"I understand your concern about the processing fee. As a special offer, I can reduce it from ₹{current_fee:,.0f} to ₹{reduced_fee:,.0f}. This covers our administrative costs while giving you a better deal."
        
        alternatives = [{
            **current_terms,
            'processing_fee': reduced_fee
        }]
        
        return {
            'response': response,
            'alternatives': alternatives,
            'next_action': 'present_alternatives'
        }

    def _handle_general_objection(self, objection: str, current_terms: Dict[str, Any]) -> Dict[str, Any]:
        """Handle general objections"""
        response = "I understand your concerns. Let me address them and see how we can make this work better for you. Could you tell me specifically what aspect you'd like me to adjust - the EMI amount, tenure, or loan amount?"
        
        return {
            'response': response,
            'alternatives': [],
            'next_action': 'clarify_objection'
        }

    def _generate_alternative_options(self, customer_profile: CustomerProfile, 
                                    constraints: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate alternative loan options based on constraints"""
        alternatives = []
        
        base_amount = constraints.get('max_amount', customer_profile.pre_approved_limit)
        max_emi = constraints.get('max_emi')
        max_tenure = constraints.get('max_tenure', 120)
        
        # Generate 3 alternative options
        amounts = [base_amount * 0.7, base_amount * 0.85, base_amount]
        
        for amount in amounts:
            rate = self._calculate_interest_rate(customer_profile, amount)
            
            # Find suitable tenure
            for tenure in self.tenure_options:
                if tenure > max_tenure:
                    continue
                
                loan_terms = self.loan_calculator.calculate_loan_terms(amount, rate, tenure)
                
                if max_emi and loan_terms.emi > max_emi:
                    continue
                
                # Assess affordability
                affordability = self.loan_calculator.assess_affordability(customer_profile, loan_terms)
                
                alternative = {
                    'amount': loan_terms.amount,
                    'tenure': loan_terms.tenure,
                    'interest_rate': loan_terms.interest_rate,
                    'emi': loan_terms.emi,
                    'total_payable': loan_terms.total_payable,
                    'processing_fee': loan_terms.processing_fee,
                    'affordability_score': self._convert_affordability_to_score(affordability)
                }
                
                alternatives.append(alternative)
                break
        
        return alternatives

    def generate_adjusted_terms(self, customer_profile: CustomerProfile, 
                              desired_amount: float, interest_rate: float) -> List[Dict[str, Any]]:
        """
        Generate adjusted loan terms using the loan calculator's affordability engine.
        
        Args:
            customer_profile: Customer's financial profile
            desired_amount: Desired loan amount
            interest_rate: Interest rate to use
            
        Returns:
            List of adjusted loan options
        """
        try:
            # Use loan calculator to generate adjusted terms
            adjusted_terms_list = self.loan_calculator.adjust_terms_for_affordability(
                customer_profile, desired_amount, interest_rate
            )
            
            # Convert LoanTerms objects to dictionaries with affordability scores
            adjusted_options = []
            for terms in adjusted_terms_list:
                affordability = self.loan_calculator.assess_affordability(customer_profile, terms)
                
                option = {
                    'amount': terms.amount,
                    'tenure': terms.tenure,
                    'interest_rate': terms.interest_rate,
                    'emi': terms.emi,
                    'total_payable': terms.total_payable,
                    'processing_fee': terms.processing_fee,
                    'affordability_score': self._convert_affordability_to_score(affordability),
                    'is_affordable': affordability.is_affordable,
                    'risk_level': affordability.risk_level
                }
                adjusted_options.append(option)
            
            return adjusted_options
            
        except Exception as e:
            self.logger.error(f"Failed to generate adjusted terms: {str(e)}")
            return []

    def validate_loan_terms(self, loan_terms: Dict[str, Any], 
                          customer_profile: CustomerProfile) -> Dict[str, Any]:
        """
        Validate loan terms using the loan calculator's validation engine.
        
        Args:
            loan_terms: Loan terms to validate
            customer_profile: Customer profile for validation
            
        Returns:
            Validation result
        """
        try:
            # Convert dict to LoanTerms object
            terms = LoanTerms(
                amount=loan_terms['amount'],
                tenure=loan_terms['tenure'],
                interest_rate=loan_terms['interest_rate'],
                emi=loan_terms['emi'],
                total_payable=loan_terms.get('total_payable', 0),
                total_interest=loan_terms.get('total_interest', 0),
                processing_fee=loan_terms.get('processing_fee', 0)
            )
            
            # Use loan calculator for validation
            validation_result = self.loan_calculator.validate_loan_terms(terms, customer_profile)
            
            return validation_result
            
        except Exception as e:
            self.logger.error(f"Failed to validate loan terms: {str(e)}")
            return {
                'is_valid': False,
                'errors': [f"Validation error: {str(e)}"],
                'warnings': [],
                'recommendations': []
            }

    def _generate_capacity_recommendation(self, assessment: Dict[str, Any]) -> str:
        """Generate capacity-based recommendation"""
        capacity_level = assessment.get('capacity_level', 'limited')
        requested_amount = assessment.get('requested_amount', 0)
        recommended_amount = assessment.get('recommended_amount', 0)
        
        if capacity_level == 'excellent':
            return f"Excellent! You're well within your financial capacity. The requested amount of ₹{requested_amount:,.0f} is easily manageable."
        elif capacity_level == 'good':
            return f"Good news! While ₹{requested_amount:,.0f} is above your pre-approved limit, it's still within a manageable range. We can proceed with additional verification."
        else:
            return f"Based on your current financial profile, I'd recommend considering ₹{recommended_amount:,.0f} instead of ₹{requested_amount:,.0f} for better affordability."