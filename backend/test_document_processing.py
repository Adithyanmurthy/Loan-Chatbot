#!/usr/bin/env python3
"""
Test script for document processing functionality
"""

import os
import tempfile
import json
from services.document_processor import DocumentProcessor
from services.document_service import DocumentService
from services.workflow_manager import WorkflowManager
from models.documents import FileUpload, DocumentType, DocumentProcessingResult


def test_document_processor():
    """Test document processor functionality"""
    print("Testing DocumentProcessor...")
    
    processor = DocumentProcessor()
    
    # Test salary slip parsing
    test_text = """
    SALARY SLIP
    Employee Name: John Doe
    Employee ID: EMP001
    Company: ABC Technologies Pvt Ltd
    Pay Period: March 2024
    
    Basic Salary: Rs. 50,000.00
    HRA: Rs. 20,000.00
    Special Allowance: Rs. 10,000.00
    Gross Salary: Rs. 80,000.00
    
    PF Deduction: Rs. 6,000.00
    Tax Deduction: Rs. 8,000.00
    Total Deductions: Rs. 14,000.00
    
    Net Salary: Rs. 66,000.00
    """
    
    parsed_data = processor.parse_salary_slip(test_text)
    
    assert 'monthly_income' in parsed_data['extracted_fields']
    assert parsed_data['extracted_fields']['monthly_income'] == 66000.0
    assert 'basic_salary' in parsed_data['extracted_fields']
    assert parsed_data['extracted_fields']['basic_salary'] == 50000.0
    
    print("✓ Salary slip parsing works")
    
    # Test validation
    validation_errors = processor.validate_extracted_data(parsed_data['extracted_fields'])
    print(f"✓ Validation completed with {len(validation_errors)} issues")
    
    # Test authenticity verification
    auth_result = processor.verify_document_authenticity(test_text)
    assert auth_result['is_authentic'] == True
    assert auth_result['confidence_score'] > 0.5
    
    print("✓ Document authenticity verification works")
    
    return True


def test_document_service():
    """Test document service functionality"""
    print("Testing DocumentService...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        doc_service = DocumentService(upload_folder=temp_dir)
        
        # Test file validation (mock)
        class MockFile:
            def __init__(self, filename, mimetype, size=1024):
                self.filename = filename
                self.mimetype = mimetype
                self.content_length = size
        
        mock_file = MockFile("test_salary.pdf", "application/pdf")
        is_valid, error_msg = doc_service.validate_file(mock_file)
        
        assert is_valid == True
        assert error_msg is None
        
        print("✓ File validation works")
        
        # Test invalid file
        invalid_file = MockFile("test.exe", "application/exe")
        is_valid, error_msg = doc_service.validate_file(invalid_file)
        
        assert is_valid == False
        assert error_msg is not None
        
        print("✓ Invalid file rejection works")
    
    return True


def test_workflow_manager():
    """Test workflow manager functionality"""
    print("Testing WorkflowManager...")
    
    workflow_manager = WorkflowManager()
    
    # Test document type detection
    doc_type = workflow_manager._get_document_type_from_upload('test_upload')
    assert doc_type == DocumentType.SALARY_SLIP
    
    print("✓ Document type detection works")
    
    # Test continuation handler selection
    handler = workflow_manager._get_continuation_handler(DocumentType.SALARY_SLIP, 'success')
    assert handler is not None
    
    print("✓ Continuation handler selection works")
    
    return True


def test_integration():
    """Test integration between components"""
    print("Testing Integration...")
    
    processor = DocumentProcessor()
    workflow_manager = WorkflowManager()
    
    # Create test processing result
    processing_result = DocumentProcessingResult(
        upload_id='test_upload_123',
        processing_status='success'
    )
    
    processing_result.extracted_fields = {
        'monthly_income': 75000.0,
        'employee_name': 'Jane Smith',
        'company_name': 'XYZ Corp'
    }
    
    processing_result.confidence_scores = {
        'monthly_income': 0.95,
        'employee_name': 0.85,
        'company_name': 0.80
    }
    
    # Test that processing result is properly structured
    assert processing_result.processing_status == 'success'
    assert 'monthly_income' in processing_result.extracted_fields
    assert processing_result.extracted_fields['monthly_income'] == 75000.0
    
    print("✓ Processing result structure works")
    
    # Test workflow status
    status = workflow_manager.get_workflow_status('non_existent_session')
    assert status['status_available'] == False
    
    print("✓ Workflow status handling works")
    
    return True


def main():
    """Run all tests"""
    print("Running Document Processing Tests...\n")
    
    try:
        test_document_processor()
        print("DocumentProcessor tests passed!\n")
        
        test_document_service()
        print("DocumentService tests passed!\n")
        
        test_workflow_manager()
        print("WorkflowManager tests passed!\n")
        
        test_integration()
        print("Integration tests passed!\n")
        
        print("🎉 All document processing tests passed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)