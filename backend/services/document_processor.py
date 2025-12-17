"""
Document processing service for extracting information from uploaded documents
Based on requirements: 7.3, 7.4
"""

import os
import re
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import json

from models.documents import DocumentProcessingResult, DocumentType, FileUpload

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Service for processing and extracting information from documents"""
    
    def __init__(self):
        """Initialize document processor"""
        # Salary patterns for extraction
        self.salary_patterns = {
            'basic_salary': [
                r'basic\s*salary\s*[:\-]?\s*(?:rs\.?|₹)?\s*([0-9,]+(?:\.[0-9]{2})?)',
                r'basic\s*pay\s*[:\-]?\s*(?:rs\.?|₹)?\s*([0-9,]+(?:\.[0-9]{2})?)',
                r'basic\s*[:\-]?\s*(?:rs\.?|₹)?\s*([0-9,]+(?:\.[0-9]{2})?)'
            ],
            'gross_salary': [
                r'gross\s*salary\s*[:\-]?\s*(?:rs\.?|₹)?\s*([0-9,]+(?:\.[0-9]{2})?)',
                r'gross\s*pay\s*[:\-]?\s*(?:rs\.?|₹)?\s*([0-9,]+(?:\.[0-9]{2})?)',
                r'total\s*gross\s*[:\-]?\s*(?:rs\.?|₹)?\s*([0-9,]+(?:\.[0-9]{2})?)'
            ],
            'net_salary': [
                r'net\s*salary\s*[:\-]?\s*(?:rs\.?|₹)?\s*([0-9,]+(?:\.[0-9]{2})?)',
                r'net\s*pay\s*[:\-]?\s*(?:rs\.?|₹)?\s*([0-9,]+(?:\.[0-9]{2})?)',
                r'take\s*home\s*[:\-]?\s*(?:rs\.?|₹)?\s*([0-9,]+(?:\.[0-9]{2})?)'
            ],
            'employee_name': [
                r'employee\s*name\s*[:\-]?\s*([a-zA-Z\s]+)',
                r'name\s*[:\-]?\s*([a-zA-Z\s]+)',
                r'emp\s*name\s*[:\-]?\s*([a-zA-Z\s]+)'
            ],
            'employee_id': [
                r'employee\s*id\s*[:\-]?\s*([a-zA-Z0-9]+)',
                r'emp\s*id\s*[:\-]?\s*([a-zA-Z0-9]+)',
                r'id\s*[:\-]?\s*([a-zA-Z0-9]+)'
            ],
            'pay_period': [
                r'pay\s*period\s*[:\-]?\s*([a-zA-Z0-9\s/\-]+)',
                r'salary\s*for\s*[:\-]?\s*([a-zA-Z0-9\s/\-]+)',
                r'month\s*[:\-]?\s*([a-zA-Z0-9\s/\-]+)'
            ]
        }
        
        # Company patterns
        self.company_patterns = [
            r'company\s*[:\-]?\s*([a-zA-Z\s&\.\(\)]+)',
            r'organization\s*[:\-]?\s*([a-zA-Z\s&\.\(\)]+)',
            r'employer\s*[:\-]?\s*([a-zA-Z\s&\.\(\)]+)',
            r'company\s*name\s*[:\-]?\s*([a-zA-Z\s&\.\(\)]+)',
            r'org\s*[:\-]?\s*([a-zA-Z\s&\.\(\)]+)'
        ]
        
        # Document authenticity indicators
        self.authenticity_indicators = [
            'salary slip', 'pay slip', 'payslip', 'salary statement',
            'pay statement', 'monthly salary', 'salary certificate',
            'employee pay', 'compensation statement'
        ]
        
        # Suspicious patterns that might indicate fake documents
        self.suspicious_patterns = [
            r'sample', r'template', r'example', r'test', r'dummy',
            r'lorem ipsum', r'placeholder', r'xxx', r'000000'
        ]
    
    def extract_text_from_file(self, file_path: str, file_type: str) -> str:
        """
        Extract text content from uploaded file
        
        Args:
            file_path: Path to the uploaded file
            file_type: MIME type of the file
            
        Returns:
            Extracted text content
        """
        try:
            if file_type == 'application/pdf':
                return self._extract_text_from_pdf(file_path)
            elif file_type.startswith('image/'):
                return self._extract_text_from_image(file_path)
            else:
                logger.warning(f"Unsupported file type for text extraction: {file_type}")
                return ""
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {e}")
            return ""
    
    def _extract_text_from_pdf(self, file_path: str) -> str:
        """
        Extract text from PDF file
        
        Note: This is a simplified implementation. In production, you would use
        libraries like PyPDF2, pdfplumber, or OCR tools like Tesseract
        """
        try:
            # For now, return a placeholder implementation
            # In production, you would use:
            # import PyPDF2 or pdfplumber
            logger.info(f"PDF text extraction not fully implemented for {file_path}")
            
            # Simulate extracted text for testing
            return """
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
        except Exception as e:
            logger.error(f"Error extracting text from PDF {file_path}: {e}")
            return ""
    
    def _extract_text_from_image(self, file_path: str) -> str:
        """
        Extract text from image file using OCR
        
        Note: This is a placeholder implementation. In production, you would use
        OCR libraries like Tesseract (pytesseract)
        """
        try:
            # For now, return a placeholder implementation
            # In production, you would use:
            # import pytesseract
            # from PIL import Image
            logger.info(f"Image OCR not fully implemented for {file_path}")
            
            # Simulate extracted text for testing
            return """
            MONTHLY SALARY STATEMENT
            Name: Jane Smith
            Emp ID: EMP002
            Organization: XYZ Corp Ltd
            Month: April 2024
            
            Basic Pay: 45000
            Allowances: 15000
            Gross Pay: 60000
            
            Deductions: 9000
            Net Pay: 51000
            """
        except Exception as e:
            logger.error(f"Error extracting text from image {file_path}: {e}")
            return ""
    
    def parse_salary_slip(self, text_content: str) -> Dict[str, Any]:
        """
        Parse salary slip text and extract structured information
        
        Args:
            text_content: Raw text extracted from document
            
        Returns:
            Dictionary with extracted salary information
        """
        extracted_data = {}
        confidence_scores = {}
        
        # Normalize text for better matching
        normalized_text = text_content.lower().strip()
        
        # Extract salary information using patterns
        for field_name, patterns in self.salary_patterns.items():
            value, confidence = self._extract_field_with_patterns(normalized_text, patterns)
            if value:
                if field_name in ['basic_salary', 'gross_salary', 'net_salary']:
                    # Convert to numeric value
                    numeric_value = self._parse_currency_value(value)
                    if numeric_value is not None:
                        extracted_data[field_name] = numeric_value
                        confidence_scores[field_name] = confidence
                else:
                    extracted_data[field_name] = value.strip()
                    confidence_scores[field_name] = confidence
        
        # Extract company information
        company_value, company_confidence = self._extract_field_with_patterns(
            normalized_text, self.company_patterns
        )
        if company_value:
            extracted_data['company_name'] = company_value.strip()
            confidence_scores['company_name'] = company_confidence
        
        # Calculate derived fields
        if 'net_salary' in extracted_data:
            # Estimate monthly income for underwriting
            extracted_data['monthly_income'] = extracted_data['net_salary']
            confidence_scores['monthly_income'] = confidence_scores.get('net_salary', 0.8)
        elif 'gross_salary' in extracted_data:
            # Estimate net as 80% of gross if net not found
            estimated_net = extracted_data['gross_salary'] * 0.8
            extracted_data['monthly_income'] = estimated_net
            confidence_scores['monthly_income'] = 0.6  # Lower confidence for estimation
        
        return {
            'extracted_fields': extracted_data,
            'confidence_scores': confidence_scores,
            'raw_text': text_content[:500]  # Store first 500 chars for debugging
        }
    
    def _extract_field_with_patterns(self, text: str, patterns: List[str]) -> Tuple[Optional[str], float]:
        """
        Extract field value using multiple regex patterns
        
        Args:
            text: Text to search in
            patterns: List of regex patterns to try
            
        Returns:
            Tuple of (extracted_value, confidence_score)
        """
        for i, pattern in enumerate(patterns):
            try:
                match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if match:
                    value = match.group(1).strip()
                    if value:
                        # Higher confidence for earlier patterns (more specific)
                        confidence = 1.0 - (i * 0.1)
                        return value, max(confidence, 0.5)
            except Exception as e:
                logger.warning(f"Error in pattern matching: {e}")
                continue
        
        return None, 0.0
    
    def _parse_currency_value(self, value_str: str) -> Optional[float]:
        """
        Parse currency string to numeric value
        
        Args:
            value_str: String containing currency value
            
        Returns:
            Numeric value or None if parsing fails
        """
        try:
            # Remove currency symbols and commas
            cleaned = re.sub(r'[₹,\s]', '', value_str)
            cleaned = re.sub(r'rs\.?', '', cleaned, flags=re.IGNORECASE)
            
            # Convert to float
            return float(cleaned)
        except (ValueError, TypeError):
            logger.warning(f"Could not parse currency value: {value_str}")
            return None
    
    def validate_extracted_data(self, extracted_data: Dict[str, Any]) -> List[str]:
        """
        Validate extracted data for completeness and reasonableness
        
        Args:
            extracted_data: Dictionary with extracted fields
            
        Returns:
            List of validation errors
        """
        errors = []
        warnings = []
        
        # Check for required fields
        required_fields = ['monthly_income']
        for field in required_fields:
            if field not in extracted_data:
                errors.append(f"Required field '{field}' not found")
        
        # Validate salary ranges (reasonable values for Indian market)
        if 'monthly_income' in extracted_data:
            income = extracted_data['monthly_income']
            if income < 5000:  # Very low salary
                errors.append(f"Monthly income ₹{income:,.0f} seems unreasonably low")
            elif income < 15000:  # Low but possible salary
                warnings.append(f"Monthly income ₹{income:,.0f} is quite low")
            elif income > 2000000:  # Very high salary
                errors.append(f"Monthly income ₹{income:,.0f} seems unreasonably high")
            elif income > 500000:  # High but possible salary
                warnings.append(f"Monthly income ₹{income:,.0f} is quite high")
        
        # Check for consistency between salary fields
        if 'basic_salary' in extracted_data and 'gross_salary' in extracted_data:
            basic = extracted_data['basic_salary']
            gross = extracted_data['gross_salary']
            if basic > gross:
                errors.append("Basic salary cannot be higher than gross salary")
            elif basic < gross * 0.3:  # Basic should be at least 30% of gross
                warnings.append("Basic salary seems unusually low compared to gross salary")
        
        if 'gross_salary' in extracted_data and 'net_salary' in extracted_data:
            gross = extracted_data['gross_salary']
            net = extracted_data['net_salary']
            if net > gross:
                errors.append("Net salary cannot be higher than gross salary")
            elif net < gross * 0.6:  # Net should be at least 60% of gross
                warnings.append("Net salary seems low compared to gross (high deductions)")
            elif net > gross * 0.95:  # Net should not be more than 95% of gross
                warnings.append("Net salary seems too close to gross (very low deductions)")
        
        # Validate employee information
        if 'employee_name' in extracted_data:
            name = extracted_data['employee_name'].strip()
            if len(name) < 2:
                errors.append("Employee name seems too short")
            elif not name.replace(' ', '').isalpha():
                warnings.append("Employee name contains non-alphabetic characters")
        
        if 'employee_id' in extracted_data:
            emp_id = str(extracted_data['employee_id']).strip()
            if len(emp_id) < 3:
                warnings.append("Employee ID seems unusually short")
        
        # Validate company information
        if 'company_name' in extracted_data:
            company = extracted_data['company_name'].strip()
            if len(company) < 3:
                warnings.append("Company name seems too short")
        
        # Validate pay period
        if 'pay_period' in extracted_data:
            pay_period = extracted_data['pay_period'].strip()
            if len(pay_period) < 3:
                warnings.append("Pay period information seems incomplete")
        
        # Add warnings to errors list for now (they will be treated as validation issues)
        # In a more sophisticated system, warnings could be handled separately
        errors.extend([f"Warning: {w}" for w in warnings])
        
        return errors
    
    def process_document(self, file_upload: FileUpload) -> DocumentProcessingResult:
        """
        Process uploaded document and extract information
        
        Args:
            file_upload: FileUpload instance with document details
            
        Returns:
            DocumentProcessingResult with extracted information
        """
        processing_result = DocumentProcessingResult(
            upload_id=file_upload.id,
            processing_status='failed'
        )
        
        try:
            # Get file path
            if not file_upload.extracted_data or 'file_path' not in file_upload.extracted_data:
                processing_result.add_processing_error("File path not found in upload metadata")
                return processing_result
            
            file_path = file_upload.extracted_data['file_path']
            
            if not os.path.exists(file_path):
                processing_result.add_processing_error("File not found on disk")
                return processing_result
            
            # Extract text from document
            text_content = self.extract_text_from_file(file_path, file_upload.file_type)
            
            if not text_content.strip():
                processing_result.add_processing_error("No text content could be extracted from document")
                return processing_result
            
            # Process based on document type
            if file_upload.document_type == DocumentType.SALARY_SLIP:
                parsed_data = self.parse_salary_slip(text_content)
                
                # Store extracted data first
                processing_result.extracted_fields = parsed_data['extracted_fields']
                processing_result.confidence_scores = parsed_data['confidence_scores']
                processing_result.extracted_fields['raw_text_preview'] = parsed_data['raw_text']
                
                # Perform comprehensive validation
                comprehensive_validation = self.perform_comprehensive_validation(file_upload, processing_result)
                
                # Store validation results
                processing_result.extracted_fields['validation_result'] = comprehensive_validation
                
                # Determine processing status based on validation
                if not comprehensive_validation['overall_valid']:
                    processing_result.processing_status = 'failed'
                    processing_result.add_processing_error("Document failed comprehensive validation")
                    for recommendation in comprehensive_validation.get('recommendations', []):
                        processing_result.add_processing_error(f"Validation issue: {recommendation}")
                elif comprehensive_validation['validation_score'] < 0.8:
                    processing_result.processing_status = 'partial_success'
                    processing_result.add_processing_error("Document validation score is below optimal threshold")
                else:
                    processing_result.processing_status = 'success'
                
                # Add any data validation errors
                data_validation = comprehensive_validation.get('data_quality_validation', {})
                for error in data_validation.get('data_errors', []):
                    processing_result.add_processing_error(error)
                
            else:
                # For other document types, implement specific processing logic
                processing_result.add_processing_error(f"Processing not implemented for document type: {file_upload.document_type}")
                processing_result.processing_status = 'failed'
            
            return processing_result
            
        except Exception as e:
            logger.error(f"Error processing document {file_upload.id}: {e}")
            processing_result.add_processing_error(f"Processing failed: {str(e)}")
            processing_result.processing_status = 'failed'
            return processing_result
    
    def get_processing_summary(self, processing_result: DocumentProcessingResult) -> Dict[str, Any]:
        """
        Generate a summary of document processing results
        
        Args:
            processing_result: Processing result to summarize
            
        Returns:
            Summary dictionary for API responses
        """
        summary = {
            'upload_id': processing_result.upload_id,
            'status': processing_result.processing_status,
            'processed_at': processing_result.processed_at.isoformat(),
            'fields_extracted': len(processing_result.extracted_fields),
            'has_errors': len(processing_result.processing_errors) > 0,
            'error_count': len(processing_result.processing_errors)
        }
        
        # Add key extracted fields for quick reference
        if 'monthly_income' in processing_result.extracted_fields:
            summary['monthly_income'] = processing_result.extracted_fields['monthly_income']
        
        if 'employee_name' in processing_result.extracted_fields:
            summary['employee_name'] = processing_result.extracted_fields['employee_name']
        
        # Add confidence information
        if processing_result.confidence_scores:
            avg_confidence = sum(processing_result.confidence_scores.values()) / len(processing_result.confidence_scores)
            summary['average_confidence'] = round(avg_confidence, 2)
        
        return summary
    
    def verify_document_authenticity(self, text_content: str) -> Dict[str, Any]:
        """
        Verify document authenticity based on content analysis
        
        Args:
            text_content: Raw text extracted from document
            
        Returns:
            Dictionary with authenticity verification results
        """
        verification_result = {
            'is_authentic': True,
            'confidence_score': 1.0,
            'authenticity_indicators': [],
            'suspicious_indicators': [],
            'verification_notes': []
        }
        
        normalized_text = text_content.lower().strip()
        
        # Check for authenticity indicators
        authenticity_count = 0
        for indicator in self.authenticity_indicators:
            if indicator in normalized_text:
                authenticity_count += 1
                verification_result['authenticity_indicators'].append(indicator)
        
        # Check for suspicious patterns
        suspicious_count = 0
        for pattern in self.suspicious_patterns:
            matches = re.findall(pattern, normalized_text, re.IGNORECASE)
            if matches:
                suspicious_count += len(matches)
                verification_result['suspicious_indicators'].append({
                    'pattern': pattern,
                    'matches': matches
                })
        
        # Calculate confidence score
        if authenticity_count > 0:
            verification_result['confidence_score'] += 0.2 * authenticity_count
        
        if suspicious_count > 0:
            verification_result['confidence_score'] -= 0.3 * suspicious_count
            verification_result['is_authentic'] = False
            verification_result['verification_notes'].append(f"Found {suspicious_count} suspicious patterns")
        
        # Check document structure
        structure_score = self._analyze_document_structure(normalized_text)
        verification_result['confidence_score'] += structure_score
        
        # Normalize confidence score
        verification_result['confidence_score'] = max(0.0, min(1.0, verification_result['confidence_score']))
        
        # Final authenticity determination
        if verification_result['confidence_score'] < 0.5:
            verification_result['is_authentic'] = False
            verification_result['verification_notes'].append("Low confidence score indicates potential document issues")
        
        return verification_result
    
    def _analyze_document_structure(self, text_content: str) -> float:
        """
        Analyze document structure for authenticity indicators
        
        Args:
            text_content: Normalized text content
            
        Returns:
            Structure score (0.0 to 0.3)
        """
        structure_score = 0.0
        
        # Check for typical salary slip sections
        sections = [
            'employee', 'salary', 'deduction', 'allowance', 'gross', 'net',
            'basic', 'hra', 'pf', 'tax', 'total'
        ]
        
        section_count = 0
        for section in sections:
            if section in text_content:
                section_count += 1
        
        # Score based on section coverage
        if section_count >= 6:
            structure_score = 0.3
        elif section_count >= 4:
            structure_score = 0.2
        elif section_count >= 2:
            structure_score = 0.1
        
        return structure_score
    
    def perform_comprehensive_validation(self, file_upload: FileUpload, 
                                       processing_result: DocumentProcessingResult) -> Dict[str, Any]:
        """
        Perform comprehensive validation including authenticity and data quality checks
        
        Args:
            file_upload: Original file upload information
            processing_result: Document processing results
            
        Returns:
            Comprehensive validation results
        """
        validation_result = {
            'overall_valid': True,
            'validation_score': 1.0,
            'file_validation': {},
            'content_validation': {},
            'authenticity_validation': {},
            'data_quality_validation': {},
            'recommendations': []
        }
        
        try:
            # File-level validation
            validation_result['file_validation'] = {
                'file_size_ok': file_upload.file_size > 0 and file_upload.file_size < 10 * 1024 * 1024,
                'file_type_ok': file_upload.file_type in ['application/pdf', 'image/jpeg', 'image/png'],
                'filename_ok': len(file_upload.filename) > 0
            }
            
            # Content validation
            if processing_result.extracted_fields.get('raw_text_preview'):
                raw_text = processing_result.extracted_fields['raw_text_preview']
                
                # Authenticity check
                authenticity_result = self.verify_document_authenticity(raw_text)
                validation_result['authenticity_validation'] = authenticity_result
                
                if not authenticity_result['is_authentic']:
                    validation_result['overall_valid'] = False
                    validation_result['recommendations'].append("Document authenticity is questionable")
                
                # Content quality check
                validation_result['content_validation'] = {
                    'text_length_ok': len(raw_text.strip()) > 50,
                    'has_salary_info': 'monthly_income' in processing_result.extracted_fields,
                    'has_employee_info': 'employee_name' in processing_result.extracted_fields,
                    'processing_errors': len(processing_result.processing_errors)
                }
            
            # Data quality validation
            if processing_result.extracted_fields:
                data_errors = self.validate_extracted_data(processing_result.extracted_fields)
                validation_result['data_quality_validation'] = {
                    'data_errors_count': len(data_errors),
                    'data_errors': data_errors,
                    'has_required_fields': 'monthly_income' in processing_result.extracted_fields
                }
                
                if len(data_errors) > 3:  # Too many data quality issues
                    validation_result['overall_valid'] = False
                    validation_result['recommendations'].append("Multiple data quality issues detected")
            
            # Calculate overall validation score
            scores = []
            
            if validation_result['file_validation']['file_size_ok']:
                scores.append(0.2)
            if validation_result['file_validation']['file_type_ok']:
                scores.append(0.2)
            if validation_result['authenticity_validation'].get('confidence_score', 0) > 0.7:
                scores.append(0.3)
            if validation_result['content_validation'].get('has_salary_info', False):
                scores.append(0.3)
            
            validation_result['validation_score'] = sum(scores)
            
            # Final validation decision
            if validation_result['validation_score'] < 0.6:
                validation_result['overall_valid'] = False
                validation_result['recommendations'].append("Overall validation score too low")
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error in comprehensive validation: {e}")
            return {
                'overall_valid': False,
                'validation_score': 0.0,
                'error': str(e),
                'recommendations': ['Validation process failed - manual review required']
            }