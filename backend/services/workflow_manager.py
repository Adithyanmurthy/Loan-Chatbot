"""
Workflow Manager for Document Processing Integration
Handles workflow continuation after document processing completion
Based on requirements: 7.4
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from models.documents import DocumentProcessingResult, DocumentType
from models.conversation import ConversationContext, AgentType, TaskType
from models.customer import CustomerProfile
from models.loan import LoanApplication
from agents.session_manager import SessionManager

logger = logging.getLogger(__name__)


class WorkflowManager:
    """
    Service for managing workflow continuation after document processing.
    Coordinates between document processing results and agent workflow.
    """
    
    def __init__(self, session_manager: Optional[SessionManager] = None):
        """
        Initialize workflow manager
        
        Args:
            session_manager: Optional SessionManager instance for agent coordination
        """
        self.session_manager = session_manager or SessionManager()
        
        # Workflow continuation rules based on document type and processing results
        self.continuation_rules = {
            DocumentType.SALARY_SLIP: {
                'success': self._continue_salary_slip_workflow,
                'partial_success': self._handle_partial_salary_processing,
                'failed': self._handle_failed_salary_processing
            },
            DocumentType.BANK_STATEMENT: {
                'success': self._continue_bank_statement_workflow,
                'partial_success': self._handle_partial_bank_processing,
                'failed': self._handle_failed_bank_processing
            },
            DocumentType.ID_PROOF: {
                'success': self._continue_id_proof_workflow,
                'partial_success': self._handle_partial_id_processing,
                'failed': self._handle_failed_id_processing
            }
        }
        
        logger.info("Workflow Manager initialized with document processing continuation rules")
    
    def continue_workflow_after_processing(self, session_id: str, upload_id: str, 
                                         processing_result: DocumentProcessingResult) -> Dict[str, Any]:
        """
        Continue workflow after document processing completion
        
        Args:
            session_id: Session identifier for the conversation
            upload_id: Upload identifier for the processed document
            processing_result: Results from document processing
            
        Returns:
            Workflow continuation result with next actions
        """
        try:
            # Get session context
            context = self.session_manager.get_session_context(session_id)
            if not context:
                raise ValueError(f"Session {session_id} not found")
            
            # Get document type from upload metadata
            document_type = self._get_document_type_from_upload(upload_id)
            if not document_type:
                raise ValueError(f"Could not determine document type for upload {upload_id}")
            
            # Get continuation handler for document type and processing status
            continuation_handler = self._get_continuation_handler(document_type, processing_result.processing_status)
            
            if not continuation_handler:
                raise ValueError(f"No continuation handler found for {document_type.value} with status {processing_result.processing_status}")
            
            # Execute continuation logic
            continuation_result = continuation_handler(session_id, upload_id, processing_result, context)
            
            # Update session with continuation results
            self.session_manager.add_session_data(
                session_id,
                'document_processing_continuation',
                {
                    'upload_id': upload_id,
                    'document_type': document_type.value,
                    'processing_status': processing_result.processing_status,
                    'continuation_result': continuation_result,
                    'continued_at': datetime.now().isoformat()
                }
            )
            
            logger.info(f"Successfully continued workflow for session {session_id} after processing {document_type.value}")
            
            return {
                'workflow_continued': True,
                'session_id': session_id,
                'upload_id': upload_id,
                'document_type': document_type.value,
                'processing_status': processing_result.processing_status,
                'continuation_result': continuation_result,
                'next_actions': continuation_result.get('next_actions', [])
            }
            
        except Exception as e:
            logger.error(f"Failed to continue workflow for session {session_id}: {str(e)}")
            return {
                'workflow_continued': False,
                'error': str(e),
                'fallback_actions': ['notify_customer_of_processing_issue']
            }
    
    def _get_document_type_from_upload(self, upload_id: str) -> Optional[DocumentType]:
        """
        Get document type from upload metadata
        
        Args:
            upload_id: Upload identifier
            
        Returns:
            DocumentType if found, None otherwise
        """
        try:
            # In a real implementation, this would query the database
            # For now, we'll assume salary slip based on the task requirements
            return DocumentType.SALARY_SLIP
        except Exception as e:
            logger.error(f"Error getting document type for upload {upload_id}: {e}")
            return None
    
    def _get_continuation_handler(self, document_type: DocumentType, processing_status: str):
        """
        Get appropriate continuation handler for document type and status
        
        Args:
            document_type: Type of processed document
            processing_status: Processing result status
            
        Returns:
            Continuation handler function or None
        """
        if document_type in self.continuation_rules:
            return self.continuation_rules[document_type].get(processing_status)
        return None
    
    def _continue_salary_slip_workflow(self, session_id: str, upload_id: str, 
                                     processing_result: DocumentProcessingResult, 
                                     context: ConversationContext) -> Dict[str, Any]:
        """
        Continue workflow after successful salary slip processing
        
        Args:
            session_id: Session identifier
            upload_id: Upload identifier
            processing_result: Processing results
            context: Conversation context
            
        Returns:
            Continuation result for salary slip processing
        """
        try:
            # Extract salary information from processing results
            extracted_fields = processing_result.extracted_fields
            
            if 'monthly_income' not in extracted_fields:
                return self._handle_missing_salary_data(session_id, upload_id, processing_result)
            
            monthly_income = extracted_fields['monthly_income']
            
            # Update customer profile with salary information
            customer_data = self.session_manager.get_session_data(session_id, 'customer_profile')
            if customer_data:
                customer_profile = CustomerProfile.from_dict(customer_data['value'])
                customer_profile.salary = monthly_income
                
                # Update session with new customer profile
                self.session_manager.add_session_data(
                    session_id, 
                    'customer_profile', 
                    customer_profile.to_dict()
                )
            
            # Get loan application data
            loan_data = self.session_manager.get_session_data(session_id, 'loan_application')
            if not loan_data:
                return {
                    'success': False,
                    'error': 'Loan application data not found in session',
                    'next_actions': ['restart_loan_application']
                }
            
            # Trigger underwriting agent with updated salary information
            underwriting_result = self.session_manager.execute_agent_task(
                session_id,
                AgentType.UNDERWRITING,
                TaskType.UNDERWRITING,
                {
                    'action': 'full_underwriting',
                    'customer_id': customer_profile.id if customer_data else None,
                    'loan_application': loan_data['value'],
                    'salary_verified': True,
                    'salary_source': 'document_upload',
                    'document_upload_id': upload_id
                }
            )
            
            if underwriting_result:
                # Determine next action based on underwriting decision
                decision = underwriting_result.get('decision', 'error')
                
                if decision == 'approved':
                    return {
                        'success': True,
                        'workflow_stage': 'loan_approved',
                        'underwriting_decision': decision,
                        'message': 'Great news! Based on your salary verification, your loan has been approved.',
                        'next_actions': ['generate_sanction_letter', 'notify_customer_approval']
                    }
                elif decision == 'rejected':
                    return {
                        'success': True,
                        'workflow_stage': 'loan_rejected',
                        'underwriting_decision': decision,
                        'message': underwriting_result.get('message', 'Unfortunately, we cannot approve your loan application at this time.'),
                        'next_actions': ['notify_customer_rejection', 'offer_alternatives']
                    }
                else:
                    return {
                        'success': False,
                        'error': f'Unexpected underwriting decision: {decision}',
                        'next_actions': ['manual_review_required']
                    }
            else:
                return {
                    'success': False,
                    'error': 'Underwriting process failed after salary verification',
                    'next_actions': ['retry_underwriting', 'escalate_to_human']
                }
                
        except Exception as e:
            logger.error(f"Error continuing salary slip workflow: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'next_actions': ['notify_customer_processing_error']
            }
    
    def _handle_partial_salary_processing(self, session_id: str, upload_id: str, 
                                        processing_result: DocumentProcessingResult, 
                                        context: ConversationContext) -> Dict[str, Any]:
        """
        Handle partial success in salary slip processing
        
        Args:
            session_id: Session identifier
            upload_id: Upload identifier
            processing_result: Processing results
            context: Conversation context
            
        Returns:
            Handling result for partial processing
        """
        extracted_fields = processing_result.extracted_fields
        processing_errors = processing_result.processing_errors
        
        # Check if we have minimum required information
        if 'monthly_income' in extracted_fields:
            # We have salary info, continue with warnings
            logger.warning(f"Partial salary processing for session {session_id}: {processing_errors}")
            
            # Continue workflow but notify about data quality issues
            continuation_result = self._continue_salary_slip_workflow(
                session_id, upload_id, processing_result, context
            )
            
            # Add warning about data quality
            continuation_result['data_quality_warning'] = True
            continuation_result['processing_warnings'] = processing_errors
            
            return continuation_result
        else:
            # Missing critical information, request re-upload
            return {
                'success': False,
                'workflow_stage': 'document_reupload_required',
                'error': 'Could not extract salary information from document',
                'processing_errors': processing_errors,
                'message': 'We had trouble reading your salary slip. Please ensure the document is clear and try uploading again.',
                'next_actions': ['request_document_reupload', 'offer_manual_entry']
            }
    
    def _handle_failed_salary_processing(self, session_id: str, upload_id: str, 
                                       processing_result: DocumentProcessingResult, 
                                       context: ConversationContext) -> Dict[str, Any]:
        """
        Handle failed salary slip processing
        
        Args:
            session_id: Session identifier
            upload_id: Upload identifier
            processing_result: Processing results
            context: Conversation context
            
        Returns:
            Handling result for failed processing
        """
        processing_errors = processing_result.processing_errors
        
        return {
            'success': False,
            'workflow_stage': 'document_processing_failed',
            'error': 'Document processing failed',
            'processing_errors': processing_errors,
            'message': 'We were unable to process your salary slip. Please try uploading a clearer document or contact our support team.',
            'next_actions': ['request_document_reupload', 'offer_manual_entry', 'escalate_to_human']
        }
    
    def _handle_missing_salary_data(self, session_id: str, upload_id: str, 
                                  processing_result: DocumentProcessingResult) -> Dict[str, Any]:
        """
        Handle case where salary data could not be extracted
        
        Args:
            session_id: Session identifier
            upload_id: Upload identifier
            processing_result: Processing results
            
        Returns:
            Handling result for missing salary data
        """
        return {
            'success': False,
            'workflow_stage': 'salary_data_missing',
            'error': 'Salary information not found in document',
            'message': 'We could not find salary information in your document. Please ensure you have uploaded a valid salary slip with clear salary details.',
            'next_actions': ['request_document_reupload', 'offer_manual_salary_entry']
        }
    
    # Placeholder methods for other document types
    def _continue_bank_statement_workflow(self, session_id: str, upload_id: str, 
                                        processing_result: DocumentProcessingResult, 
                                        context: ConversationContext) -> Dict[str, Any]:
        """Continue workflow after bank statement processing"""
        return {
            'success': True,
            'workflow_stage': 'bank_statement_processed',
            'message': 'Bank statement processed successfully',
            'next_actions': ['continue_verification']
        }
    
    def _handle_partial_bank_processing(self, session_id: str, upload_id: str, 
                                      processing_result: DocumentProcessingResult, 
                                      context: ConversationContext) -> Dict[str, Any]:
        """Handle partial bank statement processing"""
        return {
            'success': False,
            'workflow_stage': 'bank_statement_partial',
            'message': 'Bank statement processing incomplete',
            'next_actions': ['request_document_reupload']
        }
    
    def _handle_failed_bank_processing(self, session_id: str, upload_id: str, 
                                     processing_result: DocumentProcessingResult, 
                                     context: ConversationContext) -> Dict[str, Any]:
        """Handle failed bank statement processing"""
        return {
            'success': False,
            'workflow_stage': 'bank_statement_failed',
            'message': 'Bank statement processing failed',
            'next_actions': ['request_document_reupload', 'escalate_to_human']
        }
    
    def _continue_id_proof_workflow(self, session_id: str, upload_id: str, 
                                  processing_result: DocumentProcessingResult, 
                                  context: ConversationContext) -> Dict[str, Any]:
        """Continue workflow after ID proof processing"""
        return {
            'success': True,
            'workflow_stage': 'id_proof_processed',
            'message': 'ID proof processed successfully',
            'next_actions': ['continue_verification']
        }
    
    def _handle_partial_id_processing(self, session_id: str, upload_id: str, 
                                    processing_result: DocumentProcessingResult, 
                                    context: ConversationContext) -> Dict[str, Any]:
        """Handle partial ID proof processing"""
        return {
            'success': False,
            'workflow_stage': 'id_proof_partial',
            'message': 'ID proof processing incomplete',
            'next_actions': ['request_document_reupload']
        }
    
    def _handle_failed_id_processing(self, session_id: str, upload_id: str, 
                                   processing_result: DocumentProcessingResult, 
                                   context: ConversationContext) -> Dict[str, Any]:
        """Handle failed ID proof processing"""
        return {
            'success': False,
            'workflow_stage': 'id_proof_failed',
            'message': 'ID proof processing failed',
            'next_actions': ['request_document_reupload', 'escalate_to_human']
        }
    
    def get_workflow_status(self, session_id: str) -> Dict[str, Any]:
        """
        Get current workflow status for a session
        
        Args:
            session_id: Session identifier
            
        Returns:
            Current workflow status information
        """
        try:
            context = self.session_manager.get_session_context(session_id)
            if not context:
                return {
                    'status_available': False,
                    'error': 'Session not found'
                }
            
            # Get document processing history
            processing_data = self.session_manager.get_session_data(session_id, 'document_processing_continuation')
            
            return {
                'status_available': True,
                'session_id': session_id,
                'conversation_stage': context.conversation_stage,
                'document_processing_history': processing_data['value'] if processing_data else None,
                'pending_tasks': context.pending_tasks,
                'completed_tasks': context.completed_tasks
            }
            
        except Exception as e:
            logger.error(f"Error getting workflow status for session {session_id}: {e}")
            return {
                'status_available': False,
                'error': str(e)
            }