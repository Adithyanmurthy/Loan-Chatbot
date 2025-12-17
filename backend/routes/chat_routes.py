"""
Chat API Routes
Implements REST API endpoints for chat functionality
Based on requirements: 1.1, 6.1, 6.4
"""

from flask import Blueprint, request, jsonify, current_app
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from agents.master_agent import MasterAgent
from agents.session_manager import SessionManager
from models.conversation import ConversationContext, AgentType
from services.error_handler import ComprehensiveErrorHandler

logger = logging.getLogger(__name__)

# Create blueprint for chat routes
chat_bp = Blueprint('chat', __name__, url_prefix='/api/chat')

# Global instances (in production, these would be managed differently)
session_manager = SessionManager()
master_agent = MasterAgent(session_manager)
error_handler = ComprehensiveErrorHandler()


def get_session_manager():
    """Get session manager instance"""
    return session_manager


def get_master_agent():
    """Get master agent instance"""
    return master_agent


@chat_bp.route('/message', methods=['POST'])
def process_message():
    """
    Process incoming chat message from user
    
    Expected JSON body:
    {
        "message": "User message text",
        "session_id": "optional_session_id",
        "customer_id": "optional_customer_id",
        "message_type": "text" (optional, defaults to "text")
    }
    
    Returns:
        JSON response with agent response and session information
    """
    try:
        # Validate request
        if not request.is_json:
            return jsonify({
                'success': False,
                'error': 'Request must be JSON',
                'error_code': 'INVALID_CONTENT_TYPE'
            }), 400
        
        data = request.get_json()
        
        # Validate required fields
        if 'message' not in data:
            return jsonify({
                'success': False,
                'error': 'Message is required',
                'error_code': 'MISSING_MESSAGE'
            }), 400
        
        message = data['message'].strip()
        if not message and 'form_data' not in data:
            return jsonify({
                'success': False,
                'error': 'Message or form data is required',
                'error_code': 'EMPTY_MESSAGE'
            }), 400
        
        session_id = data.get('session_id') or data.get('sessionId')  # Support both formats
        customer_id = data.get('customer_id') or data.get('customerId')
        message_type = data.get('message_type', 'text')
        form_data = data.get('form_data')  # Handle form submissions
        
        # Get master agent and session manager
        master = get_master_agent()
        session_mgr = get_session_manager()
        
        # Handle new conversation or existing session
        if not session_id:
            # Start new conversation
            logger.info(f"Starting new conversation for customer: {customer_id}")
            
            initiation_result = master.initiate_conversation(
                customer_id=customer_id,
                initial_message=message
            )
            
            session_id = initiation_result['session_id']
            
            # Process the initial message (handle form data if present)
            if form_data:
                # Store form data in session context
                session_mgr.add_session_data(session_id, 'form_data', form_data)
                message = f"Form submitted with customer details: {form_data.get('full_name', 'Customer')}"
                message_type = 'form_submission'
            
            processing_result = master.process_user_message(
                session_id=session_id,
                message=message,
                message_type=message_type
            )
            
            # Get conversation context for response
            context = session_mgr.get_session_context(session_id)
            
            # For new conversations, send the greeting first, then the response to the user's message
            # If the user's first message is just "Hello", send greeting. Otherwise, send the response.
            if message.lower().strip() in ['hello', 'hi', 'hey']:
                agent_message = initiation_result['greeting']
            else:
                agent_message = processing_result.get('response', initiation_result['greeting'])
            
            # Determine message type based on processing result for new conversations
            message_type_response = 'text'
            metadata = {
                'conversation_started': True,
                'next_expected_input': initiation_result.get('next_expected_input'),
                'action_taken': processing_result.get('action_taken'),
                'upload_required': processing_result.get('upload_required', False),
                'tracking_info': processing_result.get('tracking_info', {}),
                'timestamp': datetime.now().isoformat()
            }
            
            # Check if we need to show a form
            if processing_result.get('show_form') and processing_result.get('form_data'):
                message_type_response = 'form'
                metadata['form_data'] = processing_result['form_data']
            
            # Check if we have loan options to display
            elif processing_result.get('show_loan_options') and processing_result.get('loan_options'):
                message_type_response = 'loan_options'
                metadata['loan_options'] = processing_result['loan_options']
                metadata['customer_profile'] = processing_result.get('customer_profile')
            
            # Check if we have a download link to provide
            elif processing_result.get('message_type') == 'download_link' or processing_result.get('download_url'):
                message_type_response = 'download_link'
                metadata['download_url'] = processing_result.get('download_url')
                metadata['filename'] = processing_result.get('filename', 'Sanction Letter.pdf')
            
            # Combine initiation and processing results in frontend-expected format
            response_data = {
                'success': True,
                'message': agent_message,
                'messageType': message_type_response,
                'agentType': 'master',
                'context': {
                    'sessionId': session_id,
                    'currentAgent': 'master',
                    'conversationStage': initiation_result['conversation_stage'],
                    'customerId': customer_id
                },
                'metadata': metadata
            }
            
        else:
            # Continue existing conversation
            logger.info(f"Processing message for existing session: {session_id}")
            
            # Verify session exists
            context = session_mgr.get_session_context(session_id)
            if not context:
                return jsonify({
                    'success': False,
                    'error': 'Session not found or expired',
                    'error_code': 'SESSION_NOT_FOUND'
                }), 404
            
            # Handle form data if present
            if form_data:
                # Store form data in session context
                session_mgr.add_session_data(session_id, 'form_data', form_data)
                message = f"Form submitted with customer details: {form_data.get('full_name', 'Customer')}"
                message_type = 'form_submission'
            
            # Process the message
            processing_result = master.process_user_message(
                session_id=session_id,
                message=message,
                message_type=message_type
            )
            
            # Determine message type based on processing result
            message_type_response = 'text'
            metadata = {
                'conversation_started': False,
                'action_taken': processing_result.get('action_taken'),
                'upload_required': processing_result.get('upload_required', False),
                'delegation_result': processing_result.get('delegation_result'),
                'tracking_info': processing_result.get('tracking_info', {}),
                'timestamp': datetime.now().isoformat()
            }
            
            # Check if we need to show a form
            if processing_result.get('show_form') and processing_result.get('form_data'):
                message_type_response = 'form'
                metadata['form_data'] = processing_result['form_data']
            
            # Check if we have loan options to display
            elif processing_result.get('show_loan_options') and processing_result.get('loan_options'):
                message_type_response = 'loan_options'
                metadata['loan_options'] = processing_result['loan_options']
                metadata['customer_profile'] = processing_result.get('customer_profile')
            
            # Check if we have a download link to provide
            elif processing_result.get('message_type') == 'download_link' or processing_result.get('download_url'):
                message_type_response = 'download_link'
                metadata['download_url'] = processing_result.get('download_url')
                metadata['filename'] = processing_result.get('filename', 'Sanction Letter.pdf')
            
            # Format response for frontend
            response_data = {
                'success': True,
                'message': processing_result.get('response', ''),
                'messageType': message_type_response,
                'agentType': context.current_agent.value if context.current_agent else 'master',
                'context': {
                    'sessionId': session_id,
                    'currentAgent': context.current_agent.value if context.current_agent else 'master',
                    'conversationStage': context.conversation_stage,
                    'customerId': context.customer_id
                },
                'metadata': metadata
            }
        
        logger.info(f"Successfully processed message for session {session_id}")
        return jsonify(response_data), 200
        
    except ValueError as e:
        logger.warning(f"Validation error in message processing: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'error_code': 'VALIDATION_ERROR'
        }), 400
        
    except Exception as e:
        logger.error(f"Unexpected error in message processing: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'error_code': 'INTERNAL_ERROR'
        }), 500


@chat_bp.route('/status', methods=['GET'])
def get_conversation_status():
    """
    Get current conversation status for a session
    
    Query parameters:
    - session_id: Session identifier (required)
    
    Returns:
        JSON response with conversation status information
    """
    try:
        session_id = request.args.get('session_id')
        
        if not session_id:
            return jsonify({
                'success': False,
                'error': 'Session ID is required',
                'error_code': 'MISSING_SESSION_ID'
            }), 400
        
        # Get session context
        session_mgr = get_session_manager()
        context = session_mgr.get_session_context(session_id)
        
        if not context:
            return jsonify({
                'success': False,
                'error': 'Session not found',
                'error_code': 'SESSION_NOT_FOUND'
            }), 404
        
        # Get master agent for additional status information
        master = get_master_agent()
        
        # Get worker agent health status
        agent_health = master.get_worker_agent_health_status()
        
        # Build status response
        status_data = {
            'success': True,
            'session_id': session_id,
            'customer_id': context.customer_id,
            'conversation_stage': context.conversation_stage,
            'current_agent': context.current_agent.value if context.current_agent else None,
            'session_created': context.created_at.isoformat() if context.created_at else None,
            'last_updated': context.updated_at.isoformat() if context.updated_at else None,
            'pending_tasks': [task.id for task in context.pending_tasks],
            'completed_tasks': [task.id for task in context.completed_tasks],
            'collected_data_keys': list(context.collected_data.keys()) if context.collected_data else [],
            'error_count': len(context.errors) if context.errors else 0,
            'agent_health': agent_health,
            'session_active': True,
            'timestamp': datetime.now().isoformat()
        }
        
        # Add any recent errors (last 5)
        if context.errors:
            recent_errors = context.errors[-5:]  # Last 5 errors
            status_data['recent_errors'] = [
                {
                    'message': error.message,
                    'severity': error.severity.value,
                    'timestamp': error.timestamp.isoformat() if error.timestamp else None
                }
                for error in recent_errors
            ]
        
        logger.info(f"Retrieved status for session {session_id}")
        return jsonify(status_data), 200
        
    except Exception as e:
        logger.error(f"Error retrieving conversation status: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'error_code': 'INTERNAL_ERROR'
        }), 500


@chat_bp.route('/reset', methods=['POST'])
def reset_conversation():
    """
    Reset conversation state for a session
    
    Expected JSON body:
    {
        "session_id": "session_identifier",
        "reset_type": "soft" | "hard" (optional, defaults to "soft")
    }
    
    Returns:
        JSON response confirming reset and new conversation state
    """
    try:
        # Validate request
        if not request.is_json:
            return jsonify({
                'success': False,
                'error': 'Request must be JSON',
                'error_code': 'INVALID_CONTENT_TYPE'
            }), 400
        
        data = request.get_json()
        
        # Validate required fields
        if 'session_id' not in data:
            return jsonify({
                'success': False,
                'error': 'Session ID is required',
                'error_code': 'MISSING_SESSION_ID'
            }), 400
        
        session_id = data['session_id']
        reset_type = data.get('reset_type', 'soft')
        
        if reset_type not in ['soft', 'hard']:
            return jsonify({
                'success': False,
                'error': 'Reset type must be "soft" or "hard"',
                'error_code': 'INVALID_RESET_TYPE'
            }), 400
        
        # Get session manager and master agent
        session_mgr = get_session_manager()
        master = get_master_agent()
        
        # Verify session exists
        context = session_mgr.get_session_context(session_id)
        if not context:
            return jsonify({
                'success': False,
                'error': 'Session not found',
                'error_code': 'SESSION_NOT_FOUND'
            }), 404
        
        # Perform reset based on type
        if reset_type == 'hard':
            # Hard reset: End current session and start new one
            logger.info(f"Performing hard reset for session {session_id}")
            
            # End current session
            session_mgr.end_session(session_id)
            
            # Start new session with same customer
            customer_id = context.customer_id
            new_context = session_mgr.start_session(customer_id)
            
            # Register master agent with new session
            session_mgr.register_agent(new_context.session_id, master)
            
            response_data = {
                'success': True,
                'reset_type': 'hard',
                'old_session_id': session_id,
                'new_session_id': new_context.session_id,
                'conversation_stage': new_context.conversation_stage,
                'message': 'Conversation has been completely reset. Starting fresh.',
                'timestamp': datetime.now().isoformat()
            }
            
        else:
            # Soft reset: Reset conversation stage but keep session
            logger.info(f"Performing soft reset for session {session_id}")
            
            # Reset conversation stage to initiation
            session_mgr.update_conversation_stage(session_id, 'initiation')
            
            # Clear pending tasks and errors (but keep collected data)
            context.pending_tasks = []
            context.errors = []
            
            # Update context
            session_mgr.update_context(context)
            
            response_data = {
                'success': True,
                'reset_type': 'soft',
                'session_id': session_id,
                'conversation_stage': 'initiation',
                'message': 'Conversation has been reset to the beginning. Your information is preserved.',
                'timestamp': datetime.now().isoformat()
            }
        
        logger.info(f"Successfully performed {reset_type} reset for session {session_id}")
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Error resetting conversation: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'error_code': 'INTERNAL_ERROR'
        }), 500


@chat_bp.route('/sessions', methods=['GET'])
def list_active_sessions():
    """
    List all active sessions (for debugging/monitoring)
    
    Query parameters:
    - customer_id: Filter by customer ID (optional)
    - limit: Maximum number of sessions to return (optional, default 50)
    
    Returns:
        JSON response with list of active sessions
    """
    try:
        customer_id = request.args.get('customer_id')
        limit = int(request.args.get('limit', 50))
        
        # Get session manager
        session_mgr = get_session_manager()
        
        # Get all active sessions
        active_sessions = session_mgr.list_active_sessions(
            customer_id=customer_id,
            limit=limit
        )
        
        # Format session data
        sessions_data = []
        for context in active_sessions:
            session_info = {
                'session_id': context.session_id,
                'customer_id': context.customer_id,
                'conversation_stage': context.conversation_stage,
                'current_agent': context.current_agent.value if context.current_agent else None,
                'created_at': context.created_at.isoformat() if context.created_at else None,
                'last_updated': context.updated_at.isoformat() if context.updated_at else None,
                'pending_tasks_count': len(context.pending_tasks),
                'completed_tasks_count': len(context.completed_tasks),
                'error_count': len(context.errors) if context.errors else 0
            }
            sessions_data.append(session_info)
        
        return jsonify({
            'success': True,
            'sessions': sessions_data,
            'count': len(sessions_data),
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': f'Invalid parameter: {str(e)}',
            'error_code': 'INVALID_PARAMETER'
        }), 400
        
    except Exception as e:
        logger.error(f"Error listing active sessions: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'error_code': 'INTERNAL_ERROR'
        }), 500


# Error handlers for the blueprint
@chat_bp.errorhandler(400)
def bad_request(error):
    """Handle bad request error"""
    return jsonify({
        'success': False,
        'error': 'Bad request',
        'error_code': 'BAD_REQUEST'
    }), 400


@chat_bp.errorhandler(404)
def not_found(error):
    """Handle not found error"""
    return jsonify({
        'success': False,
        'error': 'Resource not found',
        'error_code': 'NOT_FOUND'
    }), 404


@chat_bp.errorhandler(500)
def internal_error(error):
    """Handle internal server error"""
    logger.error(f"Internal server error: {error}")
    return jsonify({
        'success': False,
        'error': 'Internal server error',
        'error_code': 'INTERNAL_ERROR'
    }), 500