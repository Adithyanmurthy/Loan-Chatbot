"""
History API Routes
Provides endpoints for loan application history and sanction letters
"""

from flask import Blueprint, request, jsonify
import logging
from datetime import datetime

from services.history_service import get_history_service

logger = logging.getLogger(__name__)

history_bp = Blueprint('history', __name__, url_prefix='/api/history')


@history_bp.route('/applications', methods=['GET'])
def get_applications():
    """Get all loan applications with optional filtering"""
    try:
        limit = int(request.args.get('limit', 50))
        status = request.args.get('status')
        
        history_service = get_history_service()
        applications = history_service.get_all_applications(limit=limit, status=status)
        
        return jsonify({
            'success': True,
            'applications': [app.to_dict() for app in applications],
            'count': len(applications),
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching applications: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@history_bp.route('/applications/<app_id>', methods=['GET'])
def get_application(app_id):
    """Get a specific application by ID"""
    try:
        history_service = get_history_service()
        application = history_service.get_application(app_id)
        
        if not application:
            return jsonify({'success': False, 'error': 'Application not found'}), 404
        
        return jsonify({
            'success': True,
            'application': application.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching application {app_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@history_bp.route('/sanction-letters', methods=['GET'])
def get_sanction_letters():
    """Get all sanction letters"""
    try:
        limit = int(request.args.get('limit', 50))
        
        history_service = get_history_service()
        letters = history_service.get_all_sanction_letters(limit=limit)
        
        return jsonify({
            'success': True,
            'sanction_letters': [letter.to_dict() for letter in letters],
            'count': len(letters),
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching sanction letters: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@history_bp.route('/sanction-letters/<letter_id>', methods=['GET'])
def get_sanction_letter(letter_id):
    """Get a specific sanction letter by ID"""
    try:
        history_service = get_history_service()
        letter = history_service.get_sanction_letter(letter_id)
        
        if not letter:
            return jsonify({'success': False, 'error': 'Sanction letter not found'}), 404
        
        return jsonify({
            'success': True,
            'sanction_letter': letter.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching sanction letter {letter_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@history_bp.route('/statistics', methods=['GET'])
def get_statistics():
    """Get overall statistics"""
    try:
        history_service = get_history_service()
        stats = history_service.get_statistics()
        
        return jsonify({
            'success': True,
            'statistics': stats,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching statistics: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
