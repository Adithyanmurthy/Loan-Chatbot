"""
Document upload and management routes
Based on requirements: 7.1, 7.2
"""

from flask import Blueprint, request, jsonify, send_file, current_app
from werkzeug.exceptions import RequestEntityTooLarge
import os
import logging
import re
from datetime import datetime

from services.document_service import DocumentService
from services.document_processor import DocumentProcessor
from models.documents import DocumentType, FileUploadStatus

logger = logging.getLogger(__name__)

# Create blueprint for document routes
document_bp = Blueprint('documents', __name__, url_prefix='/api/documents')


def get_document_service():
    """Get document service instance with app configuration"""
    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
    max_size = current_app.config.get('MAX_CONTENT_LENGTH', 10 * 1024 * 1024)
    return DocumentService(upload_folder=upload_folder, max_file_size=max_size)


def get_document_processor():
    """Get document processor instance"""
    return DocumentProcessor()


@document_bp.route('/upload', methods=['POST'])
def upload_document():
    """
    Upload a document file
    
    Expected form data:
    - file: The file to upload
    - document_type: Type of document (salary_slip, bank_statement, etc.)
    
    Returns:
    - JSON response with upload details or error
    """
    try:
        # Check if file is present in request
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file provided in request',
                'error_code': 'NO_FILE'
            }), 400
        
        file = request.files['file']
        
        # Check if file was selected
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected',
                'error_code': 'NO_FILE_SELECTED'
            }), 400
        
        # Get document type from form data
        document_type_str = request.form.get('document_type', 'other')
        try:
            document_type = DocumentType(document_type_str)
        except ValueError:
            return jsonify({
                'success': False,
                'error': f'Invalid document type: {document_type_str}',
                'error_code': 'INVALID_DOCUMENT_TYPE',
                'valid_types': [dt.value for dt in DocumentType]
            }), 400
        
        # Initialize document service
        doc_service = get_document_service()
        
        # Save the file
        file_upload = doc_service.save_file(file, document_type)
        
        # Save metadata for retrieval
        doc_service.save_upload_metadata(file_upload)
        
        # Return success response
        return jsonify({
            'success': True,
            'upload_id': file_upload.id,
            'filename': file_upload.filename,
            'file_size': file_upload.file_size,
            'document_type': file_upload.document_type.value,
            'upload_status': file_upload.upload_status.value,
            'uploaded_at': file_upload.uploaded_at.isoformat() if file_upload.uploaded_at else None,
            'message': 'File uploaded successfully'
        }), 201
        
    except ValueError as e:
        # File validation error
        logger.warning(f"File validation error: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'error_code': 'VALIDATION_ERROR'
        }), 400
        
    except RequestEntityTooLarge:
        # File too large
        logger.warning("File too large error")
        return jsonify({
            'success': False,
            'error': 'File size exceeds maximum limit',
            'error_code': 'FILE_TOO_LARGE'
        }), 413
        
    except IOError as e:
        # File save error
        logger.error(f"File save error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to save file',
            'error_code': 'SAVE_ERROR'
        }), 500
        
    except Exception as e:
        # Unexpected error
        logger.error(f"Unexpected error in file upload: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'error_code': 'INTERNAL_ERROR'
        }), 500


@document_bp.route('/upload/<upload_id>', methods=['GET'])
def get_upload_status(upload_id):
    """
    Get upload status and metadata
    
    Args:
        upload_id: Upload identifier
        
    Returns:
        JSON response with upload details
    """
    try:
        doc_service = get_document_service()
        file_upload = doc_service.load_upload_metadata(upload_id)
        
        if not file_upload:
            return jsonify({
                'success': False,
                'error': 'Upload not found',
                'error_code': 'UPLOAD_NOT_FOUND'
            }), 404
        
        return jsonify({
            'success': True,
            'upload_id': file_upload.id,
            'filename': file_upload.filename,
            'file_size': file_upload.file_size,
            'file_type': file_upload.file_type,
            'document_type': file_upload.document_type.value,
            'upload_status': file_upload.upload_status.value,
            'uploaded_at': file_upload.uploaded_at.isoformat() if file_upload.uploaded_at else None,
            'error': file_upload.error,
            'extracted_data': file_upload.extracted_data
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting upload status for {upload_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'error_code': 'INTERNAL_ERROR'
        }), 500


@document_bp.route('/upload/<upload_id>/download', methods=['GET'])
def download_file(upload_id):
    """
    Download uploaded file
    
    Args:
        upload_id: Upload identifier
        
    Returns:
        File download or error response
    """
    try:
        doc_service = get_document_service()
        file_upload = doc_service.load_upload_metadata(upload_id)
        
        if not file_upload:
            return jsonify({
                'success': False,
                'error': 'Upload not found',
                'error_code': 'UPLOAD_NOT_FOUND'
            }), 404
        
        if file_upload.upload_status != FileUploadStatus.COMPLETED:
            return jsonify({
                'success': False,
                'error': 'File upload not completed',
                'error_code': 'UPLOAD_NOT_COMPLETED'
            }), 400
        
        # Get file path
        if not file_upload.extracted_data or 'file_path' not in file_upload.extracted_data:
            return jsonify({
                'success': False,
                'error': 'File path not found',
                'error_code': 'FILE_PATH_NOT_FOUND'
            }), 404
        
        file_path = file_upload.extracted_data['file_path']
        
        if not os.path.exists(file_path):
            return jsonify({
                'success': False,
                'error': 'File not found on disk',
                'error_code': 'FILE_NOT_FOUND'
            }), 404
        
        # Send file
        return send_file(
            file_path,
            as_attachment=True,
            download_name=file_upload.filename,
            mimetype=file_upload.file_type
        )
        
    except Exception as e:
        logger.error(f"Error downloading file {upload_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'error_code': 'INTERNAL_ERROR'
        }), 500


@document_bp.route('/upload/<upload_id>', methods=['DELETE'])
def delete_upload(upload_id):
    """
    Delete uploaded file and metadata
    
    Args:
        upload_id: Upload identifier
        
    Returns:
        JSON response confirming deletion
    """
    try:
        doc_service = get_document_service()
        
        # Check if upload exists
        file_upload = doc_service.load_upload_metadata(upload_id)
        if not file_upload:
            return jsonify({
                'success': False,
                'error': 'Upload not found',
                'error_code': 'UPLOAD_NOT_FOUND'
            }), 404
        
        # Delete the file
        success = doc_service.delete_file(upload_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'File deleted successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to delete file',
                'error_code': 'DELETE_ERROR'
            }), 500
            
    except Exception as e:
        logger.error(f"Error deleting upload {upload_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'error_code': 'INTERNAL_ERROR'
        }), 500


@document_bp.route('/uploads', methods=['GET'])
def list_uploads():
    """
    List all uploads, optionally filtered by document type
    
    Query parameters:
    - document_type: Filter by document type (optional)
    
    Returns:
        JSON response with list of uploads
    """
    try:
        # Get query parameters
        document_type_str = request.args.get('document_type')
        document_type = None
        
        if document_type_str:
            try:
                document_type = DocumentType(document_type_str)
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': f'Invalid document type: {document_type_str}',
                    'error_code': 'INVALID_DOCUMENT_TYPE',
                    'valid_types': [dt.value for dt in DocumentType]
                }), 400
        
        doc_service = get_document_service()
        uploads = doc_service.list_uploads(document_type)
        
        # Convert to response format
        upload_list = []
        for upload in uploads:
            upload_list.append({
                'upload_id': upload.id,
                'filename': upload.filename,
                'file_size': upload.file_size,
                'file_type': upload.file_type,
                'document_type': upload.document_type.value,
                'upload_status': upload.upload_status.value,
                'uploaded_at': upload.uploaded_at.isoformat() if upload.uploaded_at else None,
                'error': upload.error
            })
        
        return jsonify({
            'success': True,
            'uploads': upload_list,
            'count': len(upload_list)
        }), 200
        
    except Exception as e:
        logger.error(f"Error listing uploads: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'error_code': 'INTERNAL_ERROR'
        }), 500


@document_bp.route('/process/<upload_id>', methods=['POST'])
def process_document(upload_id):
    """
    Process an uploaded document to extract information
    
    Args:
        upload_id: Upload identifier
        
    Returns:
        JSON response with processing results
    """
    try:
        doc_service = get_document_service()
        doc_processor = get_document_processor()
        
        # Load upload metadata
        file_upload = doc_service.load_upload_metadata(upload_id)
        
        if not file_upload:
            return jsonify({
                'success': False,
                'error': 'Upload not found',
                'error_code': 'UPLOAD_NOT_FOUND'
            }), 404
        
        if file_upload.upload_status != FileUploadStatus.COMPLETED:
            return jsonify({
                'success': False,
                'error': 'File upload not completed',
                'error_code': 'UPLOAD_NOT_COMPLETED'
            }), 400
        
        # Process the document
        processing_result = doc_processor.process_document(file_upload)
        
        # Generate processing summary
        summary = doc_processor.get_processing_summary(processing_result)
        
        # Update file upload with processing results
        file_upload.extracted_data = file_upload.extracted_data or {}
        file_upload.extracted_data['processing_result'] = processing_result.to_dict()
        file_upload.extracted_data['processing_summary'] = summary
        
        # Save updated metadata
        doc_service.save_upload_metadata(file_upload)
        
        return jsonify({
            'success': True,
            'upload_id': upload_id,
            'processing_status': processing_result.processing_status,
            'extracted_fields': processing_result.extracted_fields,
            'confidence_scores': processing_result.confidence_scores,
            'processing_errors': processing_result.processing_errors,
            'summary': summary,
            'processed_at': processing_result.processed_at.isoformat(),
            'message': 'Document processed successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error processing document {upload_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'error_code': 'INTERNAL_ERROR'
        }), 500


@document_bp.route('/process-and-continue/<upload_id>', methods=['POST'])
def process_document_and_continue_workflow(upload_id):
    """
    Process an uploaded document and continue the workflow
    
    Expected JSON body:
    - session_id: Session identifier for workflow continuation
    
    Args:
        upload_id: Upload identifier
        
    Returns:
        JSON response with processing results and workflow continuation
    """
    try:
        from services.workflow_manager import WorkflowManager
        
        # Get session_id from request body
        request_data = request.get_json() or {}
        session_id = request_data.get('session_id')
        
        if not session_id:
            return jsonify({
                'success': False,
                'error': 'Session ID is required for workflow continuation',
                'error_code': 'MISSING_SESSION_ID'
            }), 400
        
        doc_service = get_document_service()
        doc_processor = get_document_processor()
        workflow_manager = WorkflowManager()
        
        # Load upload metadata
        file_upload = doc_service.load_upload_metadata(upload_id)
        
        if not file_upload:
            return jsonify({
                'success': False,
                'error': 'Upload not found',
                'error_code': 'UPLOAD_NOT_FOUND'
            }), 404
        
        if file_upload.upload_status != FileUploadStatus.COMPLETED:
            return jsonify({
                'success': False,
                'error': 'File upload not completed',
                'error_code': 'UPLOAD_NOT_COMPLETED'
            }), 400
        
        # Process the document
        processing_result = doc_processor.process_document(file_upload)
        
        # Generate processing summary
        summary = doc_processor.get_processing_summary(processing_result)
        
        # Update file upload with processing results
        file_upload.extracted_data = file_upload.extracted_data or {}
        file_upload.extracted_data['processing_result'] = processing_result.to_dict()
        file_upload.extracted_data['processing_summary'] = summary
        
        # Save updated metadata
        doc_service.save_upload_metadata(file_upload)
        
        # Continue workflow based on processing results
        workflow_result = workflow_manager.continue_workflow_after_processing(
            session_id, upload_id, processing_result
        )
        
        return jsonify({
            'success': True,
            'upload_id': upload_id,
            'session_id': session_id,
            'processing_status': processing_result.processing_status,
            'extracted_fields': processing_result.extracted_fields,
            'confidence_scores': processing_result.confidence_scores,
            'processing_errors': processing_result.processing_errors,
            'summary': summary,
            'processed_at': processing_result.processed_at.isoformat(),
            'workflow_continuation': workflow_result,
            'message': 'Document processed and workflow continued successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error processing document and continuing workflow {upload_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'error_code': 'INTERNAL_ERROR'
        }), 500


@document_bp.route('/upload/salary-slip', methods=['POST'])
def upload_salary_slip():
    """
    Upload salary slip document specifically for loan processing
    
    Expected form data:
    - file: The salary slip file to upload
    - session_id: Session identifier for workflow continuation (optional)
    
    Returns:
        JSON response with upload details and processing continuation
    """
    try:
        # Check if file is present in request
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file provided in request',
                'error_code': 'NO_FILE'
            }), 400
        
        file = request.files['file']
        
        # Check if file was selected
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected',
                'error_code': 'NO_FILE_SELECTED'
            }), 400
        
        # Get session_id from form data
        session_id = request.form.get('session_id')
        
        # Initialize document service
        doc_service = get_document_service()
        
        # Save the file with salary_slip document type
        file_upload = doc_service.save_file(file, DocumentType.SALARY_SLIP)
        
        # Save metadata for retrieval
        doc_service.save_upload_metadata(file_upload)
        
        # If session_id is provided, continue workflow automatically
        workflow_result = None
        if session_id:
            try:
                from services.workflow_manager import WorkflowManager
                workflow_manager = WorkflowManager()
                
                # Process document and continue workflow
                doc_processor = get_document_processor()
                processing_result = doc_processor.process_document(file_upload)
                
                # Update file upload with processing results
                file_upload.extracted_data = file_upload.extracted_data or {}
                file_upload.extracted_data['processing_result'] = processing_result.to_dict()
                
                # Save updated metadata
                doc_service.save_upload_metadata(file_upload)
                
                # Continue workflow
                workflow_result = workflow_manager.continue_workflow_after_processing(
                    session_id, file_upload.id, processing_result
                )
                
            except Exception as workflow_error:
                logger.warning(f"Workflow continuation failed: {workflow_error}")
                # Don't fail the upload, just log the workflow error
                workflow_result = {'error': str(workflow_error)}
        
        # Return success response
        response_data = {
            'success': True,
            'upload_id': file_upload.id,
            'filename': file_upload.filename,
            'file_size': file_upload.file_size,
            'document_type': file_upload.document_type.value,
            'upload_status': file_upload.upload_status.value,
            'uploaded_at': file_upload.uploaded_at.isoformat() if file_upload.uploaded_at else None,
            'message': 'Salary slip uploaded successfully'
        }
        
        # Add workflow result if available
        if workflow_result:
            response_data['workflow_continuation'] = workflow_result
            if session_id:
                response_data['session_id'] = session_id
        
        return jsonify(response_data), 201
        
    except ValueError as e:
        # File validation error
        logger.warning(f"Salary slip validation error: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'error_code': 'VALIDATION_ERROR'
        }), 400
        
    except RequestEntityTooLarge:
        # File too large
        logger.warning("Salary slip file too large error")
        return jsonify({
            'success': False,
            'error': 'File size exceeds maximum limit',
            'error_code': 'FILE_TOO_LARGE'
        }), 413
        
    except IOError as e:
        # File save error
        logger.error(f"Salary slip file save error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to save file',
            'error_code': 'SAVE_ERROR'
        }), 500
        
    except Exception as e:
        # Unexpected error
        logger.error(f"Unexpected error in salary slip upload: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'error_code': 'INTERNAL_ERROR'
        }), 500


@document_bp.route('/download/sanction-letter/by-id/<letter_id>', methods=['GET'])
def download_sanction_letter_by_id(letter_id):
    """
    Download sanction letter PDF by letter ID
    
    Args:
        letter_id: Unique identifier for the sanction letter
        
    Returns:
        PDF file download or error response
    """
    try:
        # Validate letter_id format (should be alphanumeric with possible hyphens/underscores)
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', letter_id):
            return jsonify({
                'success': False,
                'error': 'Invalid letter ID format',
                'error_code': 'INVALID_LETTER_ID'
            }), 400
        
        # Construct filename from letter_id
        filename = f"sanction_letter_{letter_id}.pdf"
        
        # Construct file path
        sanction_letters_dir = os.path.join(current_app.root_path, 'uploads', 'sanction_letters')
        file_path = os.path.join(sanction_letters_dir, filename)
        
        # Check if file exists
        if not os.path.exists(file_path):
            # Try alternative naming patterns
            alternative_patterns = [
                f"{letter_id}.pdf",
                f"sanction_{letter_id}.pdf",
                f"letter_{letter_id}.pdf"
            ]
            
            for pattern in alternative_patterns:
                alt_path = os.path.join(sanction_letters_dir, pattern)
                if os.path.exists(alt_path):
                    file_path = alt_path
                    filename = pattern
                    break
            else:
                return jsonify({
                    'success': False,
                    'error': 'Sanction letter not found',
                    'error_code': 'LETTER_NOT_FOUND'
                }), 404
        
        # Send file
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        logger.error(f"Error downloading sanction letter {letter_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'error_code': 'INTERNAL_ERROR'
        }), 500


@document_bp.route('/validate', methods=['POST'])
def validate_file():
    """
    Validate a file without uploading it
    
    Expected form data:
    - file: The file to validate
    
    Returns:
        JSON response with validation result
    """
    try:
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file provided in request',
                'error_code': 'NO_FILE'
            }), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected',
                'error_code': 'NO_FILE_SELECTED'
            }), 400
        
        doc_service = get_document_service()
        is_valid, error_msg = doc_service.validate_file(file)
        
        if is_valid:
            return jsonify({
                'success': True,
                'valid': True,
                'filename': file.filename,
                'file_type': file.mimetype,
                'message': 'File validation passed'
            }), 200
        else:
            return jsonify({
                'success': True,
                'valid': False,
                'error': error_msg,
                'filename': file.filename,
                'file_type': file.mimetype
            }), 200
            
    except Exception as e:
        logger.error(f"Error validating file: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'error_code': 'INTERNAL_ERROR'
        }), 500


# Error handlers for the blueprint
@document_bp.errorhandler(413)
def file_too_large(error):
    """Handle file too large error"""
    return jsonify({
        'success': False,
        'error': 'File size exceeds maximum limit',
        'error_code': 'FILE_TOO_LARGE'
    }), 413


@document_bp.route('/download/sanction-letter/<filename>', methods=['GET'])
def download_sanction_letter(filename):
    """
    Download sanction letter PDF
    
    Args:
        filename: Name of the PDF file to download
        
    Returns:
        PDF file download or error response
    """
    try:
        # Validate filename to prevent directory traversal
        if '..' in filename or '/' in filename or '\\' in filename:
            return jsonify({
                'success': False,
                'error': 'Invalid filename',
                'error_code': 'INVALID_FILENAME'
            }), 400
        
        # Ensure filename ends with .pdf
        if not filename.endswith('.pdf'):
            return jsonify({
                'success': False,
                'error': 'File must be a PDF',
                'error_code': 'INVALID_FILE_TYPE'
            }), 400
        
        # Construct file path
        sanction_letters_dir = os.path.join(current_app.root_path, 'uploads', 'sanction_letters')
        file_path = os.path.join(sanction_letters_dir, filename)
        
        # Check if file exists
        if not os.path.exists(file_path):
            return jsonify({
                'success': False,
                'error': 'Sanction letter not found',
                'error_code': 'FILE_NOT_FOUND'
            }), 404
        
        # Send file
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        logger.error(f"Error downloading sanction letter {filename}: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'error_code': 'INTERNAL_ERROR'
        }), 500


@document_bp.route('/sanction-letters', methods=['GET'])
def list_sanction_letters():
    """
    List available sanction letters
    
    Returns:
        JSON response with list of available sanction letters
    """
    try:
        sanction_letters_dir = os.path.join(current_app.root_path, 'uploads', 'sanction_letters')
        
        if not os.path.exists(sanction_letters_dir):
            return jsonify({
                'success': True,
                'sanction_letters': [],
                'count': 0
            }), 200
        
        # List PDF files in the directory
        sanction_letters = []
        for filename in os.listdir(sanction_letters_dir):
            if filename.endswith('.pdf'):
                file_path = os.path.join(sanction_letters_dir, filename)
                stat = os.stat(file_path)
                
                sanction_letters.append({
                    'filename': filename,
                    'size_bytes': stat.st_size,
                    'size_mb': round(stat.st_size / (1024 * 1024), 2),
                    'created_at': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    'download_link': f'/api/documents/download/sanction-letter/{filename}'
                })
        
        # Sort by creation time (newest first)
        sanction_letters.sort(key=lambda x: x['created_at'], reverse=True)
        
        return jsonify({
            'success': True,
            'sanction_letters': sanction_letters,
            'count': len(sanction_letters)
        }), 200
        
    except Exception as e:
        logger.error(f"Error listing sanction letters: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'error_code': 'INTERNAL_ERROR'
        }), 500


@document_bp.errorhandler(400)
def bad_request(error):
    """Handle bad request error"""
    return jsonify({
        'success': False,
        'error': 'Bad request',
        'error_code': 'BAD_REQUEST'
    }), 400