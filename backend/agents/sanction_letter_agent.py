"""
Sanction Letter Agent for AI Loan Chatbot
Handles automatic PDF generation upon loan approval and customer notification
Based on requirements: 5.1, 5.3, 5.5
"""

import os
from typing import Dict, Any, Optional
from agents.base_agent import BaseAgent
from models.conversation import AgentType, TaskType, AgentTask
from models.loan import LoanApplication
from models.customer import CustomerProfile
from services.sanction_letter_generator import SanctionLetterGenerator
from services.history_service import get_history_service


class SanctionLetterAgent(BaseAgent):
    """
    Agent responsible for generating sanction letters and managing document workflow.
    Automatically creates PDF documents upon loan approval and handles download availability.
    """
    
    def __init__(self, agent_id: Optional[str] = None):
        """Initialize Sanction Letter Agent"""
        super().__init__(AgentType.SANCTION_LETTER, agent_id)
        self.generator = SanctionLetterGenerator()
        self.supported_tasks = {
            TaskType.GENERATE_SANCTION_LETTER,
            TaskType.DOCUMENT_GENERATION,
            TaskType.CREATE_DOWNLOAD_LINK,
            TaskType.NOTIFY_CUSTOMER
        }
        
    def can_execute_task(self, task_type: TaskType) -> bool:
        """Check if this agent can execute the specified task type"""
        return task_type in self.supported_tasks or task_type == TaskType.DOCUMENT_GENERATION
    
    def _execute_task_logic(self, task: AgentTask) -> Dict[str, Any]:
        """Execute specific task logic based on task type"""
        if task.type == TaskType.GENERATE_SANCTION_LETTER or task.type == TaskType.DOCUMENT_GENERATION:
            return self._generate_sanction_letter(task)
        elif task.type == TaskType.CREATE_DOWNLOAD_LINK:
            return self._create_download_link(task)
        elif task.type == TaskType.NOTIFY_CUSTOMER:
            return self._notify_customer(task)
        else:
            raise ValueError(f"Unsupported task type: {task.type}")
    
    def _generate_sanction_letter(self, task: AgentTask) -> Dict[str, Any]:
        """
        Generate PDF sanction letter for approved loan
        
        Expected input:
        - loan_application: LoanApplication object
        - customer_profile: CustomerProfile object
        - additional_terms: Optional additional terms
        
        Returns:
        - filepath: Path to generated PDF
        - download_link: Download URL
        - file_info: File metadata
        """
        try:
            # Extract input data
            loan_data = task.input.get('loan_application')
            customer_data = task.input.get('customer_profile')
            additional_terms = task.input.get('additional_terms')
            
            if not loan_data or not customer_data:
                raise ValueError("Missing required loan application or customer profile data")
            
            # Convert dictionaries to model objects if needed
            if isinstance(loan_data, dict):
                loan_application = LoanApplication.from_dict(loan_data)
            else:
                loan_application = loan_data
                
            if isinstance(customer_data, dict):
                customer_profile = CustomerProfile.from_dict(customer_data)
            else:
                customer_profile = customer_data
            
            self.logger.info(f"Generating sanction letter for loan {loan_application.id}")
            
            # Generate PDF
            filepath = self.generator.generate_sanction_letter(
                loan_application=loan_application,
                customer_profile=customer_profile,
                additional_terms=additional_terms
            )
            
            # Create download link
            download_link = self.generator.create_download_link(filepath)
            
            # Get file information
            file_info = self.generator.get_file_info(filepath)
            
            # Share data with other agents
            self.share_context_data('sanction_letter_path', filepath)
            self.share_context_data('sanction_letter_download_link', download_link)
            self.share_context_data('sanction_letter_generated', True)
            
            # Record sanction letter in history
            try:
                history_service = get_history_service()
                history_service.create_sanction_letter_record(
                    application_id=loan_application.id,
                    customer_name=customer_profile.name,
                    loan_amount=loan_application.requested_amount,
                    tenure=loan_application.tenure,
                    interest_rate=loan_application.interest_rate,
                    emi=loan_application.emi,
                    filename=os.path.basename(filepath),
                    download_url=download_link,
                    file_path=filepath
                )
                self.logger.info(f"Recorded sanction letter in history for loan {loan_application.id}")
            except Exception as hist_error:
                self.logger.warning(f"Failed to record sanction letter history: {hist_error}")
            
            result = {
                'success': True,
                'filepath': filepath,
                'download_link': download_link,
                'file_info': file_info,
                'message': 'Sanction letter generated successfully'
            }
            
            self.logger.info(f"Successfully generated sanction letter: {filepath}")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to generate sanction letter: {str(e)}")
            raise Exception(f"Sanction letter generation failed: {str(e)}")
    
    def _create_download_link(self, task: AgentTask) -> Dict[str, Any]:
        """
        Create download link for existing sanction letter
        
        Expected input:
        - filepath: Path to existing PDF file
        
        Returns:
        - download_link: Download URL
        - file_info: File metadata
        """
        try:
            filepath = task.input.get('filepath')
            if not filepath:
                raise ValueError("Missing filepath for download link creation")
            
            if not os.path.exists(filepath):
                raise FileNotFoundError(f"Sanction letter file not found: {filepath}")
            
            # Create download link
            download_link = self.generator.create_download_link(filepath)
            
            # Get file information
            file_info = self.generator.get_file_info(filepath)
            
            result = {
                'success': True,
                'download_link': download_link,
                'file_info': file_info,
                'message': 'Download link created successfully'
            }
            
            self.logger.info(f"Created download link for: {filepath}")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to create download link: {str(e)}")
            raise Exception(f"Download link creation failed: {str(e)}")
    
    def _notify_customer(self, task: AgentTask) -> Dict[str, Any]:
        """
        Prepare customer notification about sanction letter availability
        
        Expected input:
        - customer_name: Customer name
        - download_link: Download URL
        - loan_amount: Approved loan amount
        
        Returns:
        - notification_message: Message to send to customer
        - notification_type: Type of notification
        """
        try:
            customer_name = task.input.get('customer_name')
            download_link = task.input.get('download_link')
            loan_amount = task.input.get('loan_amount')
            
            if not all([customer_name, download_link, loan_amount]):
                raise ValueError("Missing required notification data")
            
            # Format loan amount
            formatted_amount = f"Rs. {float(loan_amount):,.2f}"
            
            # Create notification message
            notification_message = f"""
🎉 Congratulations {customer_name}!

Your personal loan application has been APPROVED!

✅ Approved Amount: {formatted_amount}
📄 Your official sanction letter is ready for download.

Click here to download your sanction letter: {download_link}

Please save this document for your records. You can now proceed with the loan disbursement process.

For any queries, contact our customer service at 1800-209-8800.

Thank you for choosing Tata Capital Limited!
            """.strip()
            
            # Share notification data
            self.share_context_data('customer_notification_message', notification_message)
            self.share_context_data('notification_sent', True)
            
            result = {
                'success': True,
                'notification_message': notification_message,
                'notification_type': 'approval_with_download',
                'message': 'Customer notification prepared successfully'
            }
            
            self.logger.info(f"Prepared notification for customer: {customer_name}")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to prepare customer notification: {str(e)}")
            raise Exception(f"Customer notification preparation failed: {str(e)}")
    
    def generate_and_notify(
        self, 
        loan_application: LoanApplication, 
        customer_profile: CustomerProfile,
        additional_terms: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Complete workflow: Generate sanction letter and prepare customer notification
        
        Args:
            loan_application: Approved loan application
            customer_profile: Customer information
            additional_terms: Optional additional terms
            
        Returns:
            Complete workflow result with PDF path and notification message
        """
        try:
            # Step 1: Generate sanction letter
            generation_task = self.create_task(
                TaskType.GENERATE_SANCTION_LETTER,
                {
                    'loan_application': loan_application.to_dict(),
                    'customer_profile': customer_profile.to_dict(),
                    'additional_terms': additional_terms
                }
            )
            
            generation_result = self.execute_task(generation_task)
            
            # Step 2: Prepare customer notification
            notification_task = self.create_task(
                TaskType.NOTIFY_CUSTOMER,
                {
                    'customer_name': customer_profile.name,
                    'download_link': generation_result['download_link'],
                    'loan_amount': loan_application.requested_amount
                }
            )
            
            notification_result = self.execute_task(notification_task)
            
            # Combine results
            complete_result = {
                'success': True,
                'sanction_letter': {
                    'filepath': generation_result['filepath'],
                    'download_link': generation_result['download_link'],
                    'file_info': generation_result['file_info']
                },
                'notification': {
                    'message': notification_result['notification_message'],
                    'type': notification_result['notification_type']
                },
                'workflow_completed': True
            }
            
            self.logger.info(f"Complete sanction letter workflow completed for loan {loan_application.id}")
            return complete_result
            
        except Exception as e:
            self.logger.error(f"Sanction letter workflow failed: {str(e)}")
            raise Exception(f"Complete workflow failed: {str(e)}")
    
    def handle_generation_error(self, error: Exception, loan_id: str) -> Dict[str, Any]:
        """
        Handle PDF generation errors with appropriate fallback
        
        Args:
            error: Exception that occurred
            loan_id: Loan application ID
            
        Returns:
            Error handling result with fallback options
        """
        self.handle_error(error, {'loan_id': loan_id})
        
        # Prepare fallback notification
        fallback_message = f"""
We apologize for the technical difficulty. Your loan application (ID: {loan_id}) has been approved, 
but we're experiencing issues generating your sanction letter.

Our team has been notified and will email your sanction letter within 24 hours.

For immediate assistance, please contact us at 1800-209-8800.

Thank you for your patience.
        """.strip()
        
        return {
            'success': False,
            'error': str(error),
            'fallback_message': fallback_message,
            'requires_manual_intervention': True
        }