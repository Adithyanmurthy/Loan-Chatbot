"""
Sanction Letter Generator Service
Implements PDF generation functionality for loan approval documents
Based on requirements: 5.1, 5.2, 5.3
"""

import os
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from fpdf import FPDF
from models.loan import LoanApplication
from models.customer import CustomerProfile


class SanctionLetterPDF(FPDF):
    """Custom PDF class for professional sanction letter generation"""
    
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=20)
        self.set_margins(20, 20, 20)
        
    def header(self):
        """Add professional header with company branding"""
        # Company logo and header
        self.set_font('Arial', 'B', 18)
        self.set_text_color(0, 51, 102)  # Dark blue
        self.cell(0, 12, 'TATA CAPITAL LIMITED', 0, 1, 'C')
        
        # Subtitle
        self.set_font('Arial', 'B', 10)
        self.set_text_color(102, 102, 102)
        self.cell(0, 6, 'Personal Loan Division', 0, 1, 'C')
        
        # Address
        self.set_font('Arial', '', 9)
        self.set_text_color(0, 0, 0)
        self.cell(0, 5, 'Registered Office: 11th Floor, Tower A, Peninsula Business Park,', 0, 1, 'C')
        self.cell(0, 5, 'Ganpatrao Kadam Marg, Lower Parel, Mumbai - 400013', 0, 1, 'C')
        self.cell(0, 5, 'CIN: L65191MH1991PLC059642 | www.tatacapital.com', 0, 1, 'C')
        
        # Horizontal line
        self.ln(8)
        self.set_draw_color(0, 51, 102)
        self.line(20, self.get_y(), 190, self.get_y())
        self.ln(10)
        
    def footer(self):
        """Add professional footer"""
        self.set_y(-25)
        
        # Horizontal line
        self.set_draw_color(0, 51, 102)
        self.line(20, self.get_y(), 190, self.get_y())
        self.ln(3)
        
        # Footer text
        self.set_font('Arial', 'I', 8)
        self.set_text_color(102, 102, 102)
        self.cell(0, 4, 'This is a system generated document and does not require signature.', 0, 1, 'C')
        self.cell(0, 4, f'Page {self.page_no()} | Customer Care: 1800-209-8800 | Email: customercare@tatacapital.com', 0, 0, 'C')
        
    def add_document_title(self, title: str):
        """Add main document title with styling"""
        self.set_font('Arial', 'B', 16)
        self.set_text_color(0, 51, 102)
        
        # Add border around title
        title_width = self.get_string_width(title) + 20
        x_pos = (210 - title_width) / 2
        
        self.set_x(x_pos)
        self.set_fill_color(240, 248, 255)
        self.cell(title_width, 12, title, 1, 1, 'C', True)
        self.ln(8)
        
    def add_section_header(self, header: str):
        """Add section header with background"""
        self.set_font('Arial', 'B', 11)
        self.set_text_color(255, 255, 255)
        self.set_fill_color(0, 51, 102)
        self.cell(0, 8, f'  {header}', 0, 1, 'L', True)
        self.ln(3)
        
    def add_field_row(self, label: str, value: str, label_width: int = 60):
        """Add a field with proper alignment"""
        if not value or value.strip() == '' or value.lower() in ['none', 'not provided', 'unknown']:
            return  # Skip empty or default values
            
        self.set_font('Arial', 'B', 10)
        self.set_text_color(0, 0, 0)
        self.cell(label_width, 7, f'{label}:', 0, 0, 'L')
        
        self.set_font('Arial', '', 10)
        self.set_text_color(51, 51, 51)
        self.cell(0, 7, str(value), 0, 1, 'L')
        
    def add_two_column_fields(self, field1_label: str, field1_value: str, 
                             field2_label: str, field2_value: str):
        """Add two fields side by side"""
        # Only add if at least one field has valid data
        if ((not field1_value or field1_value.strip() == '' or field1_value.lower() in ['none', 'not provided', 'unknown']) and
            (not field2_value or field2_value.strip() == '' or field2_value.lower() in ['none', 'not provided', 'unknown'])):
            return
            
        y_pos = self.get_y()
        
        # Left column
        if field1_value and field1_value.strip() != '' and field1_value.lower() not in ['none', 'not provided', 'unknown']:
            self.set_font('Arial', 'B', 10)
            self.cell(40, 7, f'{field1_label}:', 0, 0, 'L')
            self.set_font('Arial', '', 10)
            self.cell(55, 7, str(field1_value), 0, 0, 'L')
        
        # Right column
        if field2_value and field2_value.strip() != '' and field2_value.lower() not in ['none', 'not provided', 'unknown']:
            self.set_x(105)
            self.set_font('Arial', 'B', 10)
            self.cell(35, 7, f'{field2_label}:', 0, 0, 'L')
            self.set_font('Arial', '', 10)
            self.cell(0, 7, str(field2_value), 0, 0, 'L')
        
        self.ln(7)
        
    def add_formatted_paragraph(self, text: str, indent: bool = False):
        """Add a well-formatted paragraph"""
        self.set_font('Arial', '', 10)
        self.set_text_color(51, 51, 51)
        
        if indent:
            self.set_x(30)
            width = 160
        else:
            width = 0
            
        self.multi_cell(width, 6, text.strip())
        self.ln(2)
        
    def add_amount_highlight(self, label: str, amount: float, currency: str = "Rs."):
        """Add highlighted amount display"""
        self.set_font('Arial', 'B', 12)
        self.set_text_color(0, 102, 51)
        self.set_fill_color(240, 255, 240)
        
        amount_text = f'{label}: {currency} {amount:,.0f}'
        self.cell(0, 10, amount_text, 1, 1, 'C', True)
        self.ln(3)


class SanctionLetterGenerator:
    """Service for generating loan sanction letters"""
    
    def __init__(self, output_directory: str = "uploads/sanction_letters"):
        """Initialize the generator with output directory"""
        self.output_directory = output_directory
        self._ensure_output_directory()
        
    def _ensure_output_directory(self):
        """Create output directory if it doesn't exist"""
        os.makedirs(self.output_directory, exist_ok=True)
        
    def generate_sanction_letter(
        self, 
        loan_application: LoanApplication, 
        customer_profile: CustomerProfile,
        additional_terms: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate a PDF sanction letter for approved loan
        
        Args:
            loan_application: Approved loan application details
            customer_profile: Customer information
            additional_terms: Additional terms and conditions
            
        Returns:
            str: File path of generated PDF
            
        Raises:
            ValueError: If loan is not approved
            Exception: If PDF generation fails
        """
        if loan_application.status.value != "approved":
            raise ValueError("Cannot generate sanction letter for non-approved loan")
            
        try:
            # Generate professional ID numbers
            current_date = datetime.now()
            sanction_number = f"SL/{current_date.year}/{current_date.strftime('%m%d')}{uuid.uuid4().hex[:6].upper()}"
            application_id = f"APP/{current_date.year}/{current_date.strftime('%m%d')}{uuid.uuid4().hex[:8].upper()}"
            
            # Generate filename with proper format
            filename = f"sanction_letter_{sanction_number.replace('/', '_')}_{uuid.uuid4().hex[:8]}.pdf"
            filepath = os.path.join(self.output_directory, filename)
            
            # Create PDF document
            pdf = SanctionLetterPDF()
            pdf.add_page()
            
            # Add document title
            pdf.add_document_title("PERSONAL LOAN SANCTION LETTER")
            
            # Add reference details section
            pdf.add_section_header("Reference Information")
            pdf.add_two_column_fields("Sanction Letter No", sanction_number, "Date", current_date.strftime("%d %B, %Y"))
            pdf.add_field_row("Application ID", application_id)
            pdf.ln(5)
            
            # Add customer details - only show provided information
            pdf.add_section_header("Customer Information")
            
            # Only add fields that have actual customer data (not defaults)
            if customer_profile.name and customer_profile.name not in ['Valued Customer', 'GUEST_USER', 'Customer']:
                pdf.add_field_row("Name", customer_profile.name)
            
            if hasattr(customer_profile, 'age') and customer_profile.age and customer_profile.age != 25:
                age_text = f"{customer_profile.age} years"
                if customer_profile.city and customer_profile.city not in ['Unknown', 'Bangalore']:
                    pdf.add_two_column_fields("Age", age_text, "City", customer_profile.city)
                else:
                    pdf.add_field_row("Age", age_text)
            elif customer_profile.city and customer_profile.city not in ['Unknown', 'Bangalore']:
                pdf.add_field_row("City", customer_profile.city)
            
            if customer_profile.phone and customer_profile.phone not in ['Not provided', '9876543210']:
                pdf.add_field_row("Phone", customer_profile.phone)
            
            if customer_profile.address and customer_profile.address not in ['Bangalore, Karnataka', f"{customer_profile.city}, India"]:
                pdf.add_field_row("Address", customer_profile.address)
            
            # Add employment info if available
            if hasattr(customer_profile, 'employment_type') and customer_profile.employment_type:
                employment_display = customer_profile.employment_type.replace('_', ' ').title()
                if hasattr(customer_profile, 'salary') and customer_profile.salary and customer_profile.salary != 50000:
                    salary_display = f"Rs. {customer_profile.salary:,.0f} per month"
                    pdf.add_two_column_fields("Employment", employment_display, "Monthly Income", salary_display)
                else:
                    pdf.add_field_row("Employment Type", employment_display)
            elif hasattr(customer_profile, 'salary') and customer_profile.salary and customer_profile.salary != 50000:
                pdf.add_field_row("Monthly Income", f"Rs. {customer_profile.salary:,.0f}")
            
            pdf.ln(5)
            
            # Add loan details with highlighting
            pdf.add_section_header("Loan Sanction Details")
            
            # Highlight the sanctioned amount
            pdf.add_amount_highlight("SANCTIONED AMOUNT", loan_application.requested_amount)
            
            # Add other loan details
            pdf.add_two_column_fields("Interest Rate", f"{loan_application.interest_rate}% per annum", 
                                    "Loan Tenure", f"{loan_application.tenure} months")
            
            if loan_application.emi and loan_application.emi > 0:
                pdf.add_two_column_fields("Monthly EMI", f"Rs. {loan_application.emi:,.0f}", 
                                        "Processing Fee", "As per tariff")
            else:
                pdf.add_field_row("Processing Fee", "As per schedule of charges")
            
            # Calculate total amount payable
            total_amount = loan_application.emi * loan_application.tenure if loan_application.emi else 0
            if total_amount > 0:
                pdf.add_field_row("Total Amount Payable", f"Rs. {total_amount:,.0f}")
            
            pdf.ln(8)
            
            # Add congratulatory message
            customer_name = customer_profile.name if customer_profile.name not in ['Valued Customer', 'GUEST_USER'] else "Dear Customer"
            
            congratulations_text = f"""Dear {customer_name},

Congratulations! We are delighted to inform you that your Personal Loan application has been APPROVED.

Your loan will be processed and disbursed upon completion of documentation and verification formalities. Our relationship manager will contact you within 2 business days to guide you through the next steps.

NEXT STEPS:
- Complete KYC documentation
- Submit income and address proof
- Sign loan agreement
- Provide bank account details for disbursement

The loan amount will be credited directly to your registered bank account within 3-5 business days after documentation completion."""
            
            pdf.add_formatted_paragraph(congratulations_text)
            pdf.ln(5)
            
            # Add terms and conditions
            pdf.add_section_header("Important Terms & Conditions")
            
            terms_list = [
                "This sanction is valid for 30 days from the date of this letter.",
                "Loan disbursement is subject to satisfactory documentation and verification.",
                "Interest rate is as per company policy and may vary based on RBI guidelines.",
                "EMI will be auto-debited from your registered bank account monthly.",
                "Processing fee and other charges as per current tariff will be applicable.",
                "Prepayment is allowed with applicable charges as per loan agreement.",
                "All terms and conditions of the loan agreement will apply.",
                "This offer is subject to credit and risk assessment policies of the company."
            ]
            
            for i, term in enumerate(terms_list, 1):
                pdf.add_formatted_paragraph(f"{i}. {term}", indent=True)
            
            pdf.ln(8)
            
            # Add contact information
            pdf.add_section_header("Contact Information")
            contact_text = """For any queries or assistance:
            
Customer Care: 1800-209-8800 (Toll Free)
Email: customercare@tatacapital.com
Website: www.tatacapital.com

Thank you for choosing Tata Capital Limited. We look forward to serving you!

Warm Regards,
Loan Processing Team
Tata Capital Limited"""
            
            pdf.add_formatted_paragraph(contact_text)
            
            # Save PDF
            pdf.output(filepath)
            
            return filepath
            
        except Exception as e:
            raise Exception(f"Failed to generate sanction letter: {str(e)}")
    
    def create_download_link(self, filepath: str) -> str:
        """
        Create a download link for the generated PDF
        
        Args:
            filepath: Path to the PDF file
            
        Returns:
            str: Download URL/endpoint
        """
        filename = os.path.basename(filepath)
        # Return the correct API endpoint for downloading sanction letters
        return f"/api/documents/download/sanction-letter/{filename}"
    
    def get_file_info(self, filepath: str) -> Dict[str, Any]:
        """
        Get information about the generated PDF file
        
        Args:
            filepath: Path to the PDF file
            
        Returns:
            dict: File information including size, creation time, etc.
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")
            
        stat = os.stat(filepath)
        return {
            "filename": os.path.basename(filepath),
            "size_bytes": stat.st_size,
            "size_mb": round(stat.st_size / (1024 * 1024), 2),
            "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
        }
    
    def cleanup_old_files(self, days_old: int = 30):
        """
        Clean up old sanction letter files
        
        Args:
            days_old: Remove files older than this many days
        """
        import time
        
        current_time = time.time()
        cutoff_time = current_time - (days_old * 24 * 60 * 60)
        
        for filename in os.listdir(self.output_directory):
            filepath = os.path.join(self.output_directory, filename)
            if os.path.isfile(filepath) and filename.endswith('.pdf'):
                file_time = os.path.getctime(filepath)
                if file_time < cutoff_time:
                    try:
                        os.remove(filepath)
                    except OSError:
                        pass  # Ignore errors during cleanup