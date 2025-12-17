"""
Sanction Workflow Service
Handles automatic PDF generation upon loan approval and customer notification
Based on requirements: 5.1, 5.3, 5.5
"""

import logging
from typing import Dict, Any, Optional
from models.loan import LoanApplication, LoanStatus
from models.customer import CustomerProfile
from models.conversation import ConversationContext, AgentType
from agents.sanction_letter_agent import SanctionLetterAgent
from services.sanction_letter_generator import SanctionLetterGenerator


class SanctionWorkflowService:
    """
    Service for managing the complete sanction letter workflow.
    Handles automatic generation, error handling, and customer notification.
    """
    
    def __init__(self):
        """Initialize the sanction workflow service"""
        self.logger = logging.getLogger(__name__)
        self.sanction_agent = SanctionLetterAgent()
        self.generator = SanctionLetterGenerator()
        
    def process_loan_approval(
        self, 
        loan_application: LoanApplication,
        customer_profile: CustomerProfile,
        context: Optional[ConversationContext] = None,
        additional_terms: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process loan approval and generate sanction letter automatically
        
        Args:
            loan_application: Approved loan application
            customer_profile: Customer information
            context: Optional conversation context
            additional_terms: Optional additional terms and conditions
            
        Returns:
            Complete workflow result including PDF generation and notification
        """
        try:
            # Validate that loan is approved
            if loan_application.status != LoanStatus.APPROVED:
                raise ValueError(f"Cannot process sanction letter for loan with status: {loan_application.status}")
            
            self.logger.info(f"Processing loan approval for application {loan_application.id}")
            
            # Set context for the agent if provided
            if context:
                self.sanction_agent.set_context(context)
                # Update conversation stage
                context.switch_agent(AgentType.SANCTION_LETTER, 'sanction_letter_generation')
            
            # Execute complete workflow using the sanction letter agent
            workflow_result = self.sanction_agent.generate_and_notify(
                loan_application=loan_application,
                customer_profile=customer_profile,
                additional_terms=additional_terms
            )
            
            # Log successful completion
            self.logger.info(f"Sanction letter workflow completed successfully for loan {loan_application.id}")
            
            # Update context with completion status
            if context:
                context.switch_agent(AgentType.MASTER, 'completion')
                context.add_collected_data('sanction_letter_completed', True)
                context.add_collected_data('final_download_link', workflow_result['sanction_letter']['download_link'])
            
            return {
                'success': True,
                'loan_id': loan_application.id,
                'customer_id': customer_profile.id,
                'workflow_result': workflow_result,
                'message': 'Loan approval processed and sanction letter generated successfully'
            }
            
        except Exception as e:
            self.logger.error(f"Failed to process loan approval for {loan_application.id}: {str(e)}")
            
            # Handle error with fallback
            error_result = self.sanction_agent.handle_generation_error(e, loan_application.id)
            
            # Update context with error status
            if context:
                context.switch_agent(AgentType.MASTER, 'error_handling')
                context.add_error(
                    message=f"Sanction letter generation failed: {str(e)}",
                    context={'loan_id': loan_application.id, 'customer_id': customer_profile.id}
                )
            
            return {
                'success': False,
                'loan_id': loan_application.id,
                'customer_id': customer_profile.id,
                'error': str(e),
                'error_result': error_result,
                'message': 'Failed to process loan approval'
            }
    
    def regenerate_sanction_letter(
        self,
        loan_application: LoanApplication,
        customer_profile: CustomerProfile,
        additional_terms: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Regenerate sanction letter for an existing approved loan
        
        Args:
            loan_application: Approved loan application
            customer_profile: Customer information
            additional_terms: Optional additional terms and conditions
            
        Returns:
            Regeneration result
        """
        try:
            self.logger.info(f"Regenerating sanction letter for loan {loan_application.id}")
            
            # Generate new PDF
            filepath = self.generator.generate_sanction_letter(
                loan_application=loan_application,
                customer_profile=customer_profile,
                additional_terms=additional_terms
            )
            
            # Create download link
            download_link = self.generator.create_download_link(filepath)
            
            # Get file information
            file_info = self.generator.get_file_info(filepath)
            
            return {
                'success': True,
                'loan_id': loan_application.id,
                'filepath': filepath,
                'download_link': download_link,
                'file_info': file_info,
                'message': 'Sanction letter regenerated successfully'
            }
            
        except Exception as e:
            self.logger.error(f"Failed to regenerate sanction letter for {loan_application.id}: {str(e)}")
            return {
                'success': False,
                'loan_id': loan_application.id,
                'error': str(e),
                'message': 'Failed to regenerate sanction letter'
            }
    
    def get_sanction_letter_status(self, loan_id: str) -> Dict[str, Any]:
        """
        Get status of sanction letter for a loan
        
        Args:
            loan_id: Loan application ID
            
        Returns:
            Status information about sanction letter
        """
        try:
            import os
            import glob
            
            # Look for sanction letter files for this loan
            pattern = os.path.join(self.generator.output_directory, f"sanction_letter_{loan_id}_*.pdf")
            matching_files = glob.glob(pattern)
            
            if not matching_files:
                return {
                    'success': True,
                    'loan_id': loan_id,
                    'sanction_letter_exists': False,
                    'message': 'No sanction letter found for this loan'
                }
            
            # Get the most recent file
            latest_file = max(matching_files, key=os.path.getctime)
            
            # Get file information
            file_info = self.generator.get_file_info(latest_file)
            download_link = self.generator.create_download_link(latest_file)
            
            return {
                'success': True,
                'loan_id': loan_id,
                'sanction_letter_exists': True,
                'filepath': latest_file,
                'download_link': download_link,
                'file_info': file_info,
                'message': 'Sanction letter found'
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get sanction letter status for {loan_id}: {str(e)}")
            return {
                'success': False,
                'loan_id': loan_id,
                'error': str(e),
                'message': 'Failed to get sanction letter status'
            }
    
    def cleanup_old_sanction_letters(self, days_old: int = 30) -> Dict[str, Any]:
        """
        Clean up old sanction letter files
        
        Args:
            days_old: Remove files older than this many days
            
        Returns:
            Cleanup result
        """
        try:
            self.logger.info(f"Cleaning up sanction letters older than {days_old} days")
            
            # Use generator's cleanup method
            self.generator.cleanup_old_files(days_old)
            
            return {
                'success': True,
                'days_old': days_old,
                'message': f'Cleanup completed for files older than {days_old} days'
            }
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup old sanction letters: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to cleanup old sanction letters'
            }
    
    def validate_loan_for_sanction(self, loan_application: LoanApplication) -> Dict[str, Any]:
        """
        Validate that a loan is ready for sanction letter generation
        
        Args:
            loan_application: Loan application to validate
            
        Returns:
            Validation result
        """
        validation_errors = []
        
        # Check loan status
        if loan_application.status != LoanStatus.APPROVED:
            validation_errors.append(f"Loan status must be 'approved', current status: {loan_application.status}")
        
        # Check required fields
        if not loan_application.requested_amount or loan_application.requested_amount <= 0:
            validation_errors.append("Invalid loan amount")
        
        if not loan_application.tenure or loan_application.tenure <= 0:
            validation_errors.append("Invalid loan tenure")
        
        if not loan_application.interest_rate or loan_application.interest_rate <= 0:
            validation_errors.append("Invalid interest rate")
        
        if not loan_application.emi or loan_application.emi <= 0:
            validation_errors.append("Invalid EMI amount")
        
        # Check approval timestamp
        if not loan_application.approved_at:
            validation_errors.append("Missing approval timestamp")
        
        is_valid = len(validation_errors) == 0
        
        return {
            'valid': is_valid,
            'errors': validation_errors,
            'message': 'Loan validation passed' if is_valid else 'Loan validation failed'
        }
    
    def get_workflow_summary(self, loan_id: str) -> Dict[str, Any]:
        """
        Get summary of the complete sanction workflow for a loan
        
        Args:
            loan_id: Loan application ID
            
        Returns:
            Workflow summary
        """
        try:
            # Get sanction letter status
            letter_status = self.get_sanction_letter_status(loan_id)
            
            # Get agent task history if available
            task_history = self.sanction_agent.get_task_history()
            
            # Filter tasks for this loan
            loan_tasks = [
                task for task in task_history 
                if task.get('input', {}).get('loan_application', {}).get('id') == loan_id
            ]
            
            return {
                'success': True,
                'loan_id': loan_id,
                'sanction_letter_status': letter_status,
                'task_history': loan_tasks,
                'agent_status': self.sanction_agent.get_status(),
                'message': 'Workflow summary retrieved successfully'
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get workflow summary for {loan_id}: {str(e)}")
            return {
                'success': False,
                'loan_id': loan_id,
                'error': str(e),
                'message': 'Failed to get workflow summary'
            }