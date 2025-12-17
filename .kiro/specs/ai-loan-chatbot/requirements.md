# Requirements Document

## Introduction

This document outlines the requirements for an AI-driven conversational loan processing system for a Non-Banking Financial Company (NBFC). The system aims to increase revenue from existing customers and prospects by selling personal loans through a web-based chatbot interface that simulates a human-like sales process.

## Glossary

- **Master Agent**: The main orchestrator AI that manages conversation flow with customers and coordinates Worker Agents
- **Worker Agent**: Specialized AI agents that handle specific tasks (Sales, Verification, Underwriting, Sanction Letter Generation)
- **NBFC**: Non-Banking Financial Company - the financial institution offering loans
- **KYC**: Know Your Customer - identity verification process
- **EMI**: Equated Monthly Installment - monthly loan payment amount
- **Sanction Letter**: Official loan approval document
- **CRM Server**: Customer Relationship Management system containing customer data
- **Credit Bureau API**: External service providing credit scores
- **Offer Mart Server**: System hosting pre-approved loan offers

## Requirements

### Requirement 1

**User Story:** As a prospective customer, I want to interact with an AI chatbot that understands my loan needs, so that I can quickly explore personal loan options without human intervention.

#### Acceptance Criteria

1. WHEN a customer lands on the web chatbot via digital ads or marketing emails, THE Master Agent SHALL initiate a personalized conversation
2. WHEN the customer expresses interest in loans, THE Master Agent SHALL understand their needs and present relevant loan options
3. WHEN engaging with customers, THE Master Agent SHALL use persuasive and conversational language similar to a human sales executive
4. WHEN the conversation begins, THE Master Agent SHALL collect basic customer information for processing
5. WHEN the customer shows hesitation, THE Master Agent SHALL provide compelling reasons to proceed with the loan application

### Requirement 2

**User Story:** As a sales manager, I want the AI system to negotiate loan terms effectively, so that we can maximize conversion rates while meeting customer needs.

#### Acceptance Criteria

1. WHEN a customer shows interest, THE Sales Agent SHALL negotiate loan terms including amount, tenure, and interest rates
2. WHEN discussing loan options, THE Sales Agent SHALL present terms that align with customer's financial capacity
3. WHEN customer objects to terms, THE Sales Agent SHALL provide alternative options within approved limits
4. WHEN finalizing terms, THE Sales Agent SHALL ensure customer understanding and agreement
5. WHEN terms are agreed upon, THE Sales Agent SHALL pass control back to the Master Agent for next steps

### Requirement 3

**User Story:** As a compliance officer, I want the system to verify customer identity and details, so that we maintain regulatory compliance and prevent fraud.

#### Acceptance Criteria

1. WHEN customer details are provided, THE Verification Agent SHALL confirm KYC details against the CRM server
2. WHEN phone verification is required, THE Verification Agent SHALL validate phone numbers through the CRM system
3. WHEN address verification is needed, THE Verification Agent SHALL cross-check addresses with stored customer data
4. WHEN verification fails, THE Verification Agent SHALL request additional documentation or clarification
5. WHEN all verifications pass, THE Verification Agent SHALL mark the customer as verified for loan processing

### Requirement 4

**User Story:** As a risk manager, I want automated credit evaluation and eligibility assessment, so that we can make instant loan decisions while managing risk effectively.

#### Acceptance Criteria

1. WHEN credit assessment is required, THE Underwriting Agent SHALL fetch the customer's credit score from the credit bureau API
2. WHEN the loan amount is less than or equal to the pre-approved limit, THE Underwriting Agent SHALL approve the loan instantly
3. WHEN the loan amount is less than or equal to 2× the pre-approved limit, THE Underwriting Agent SHALL request salary slip upload and approve only if expected EMI is ≤ 50% of salary
4. WHEN the loan amount exceeds 2× the pre-approved limit, THE Underwriting Agent SHALL reject the application
5. WHEN the credit score is below 700, THE Underwriting Agent SHALL reject the application regardless of other factors

### Requirement 5

**User Story:** As a customer, I want to receive an official loan approval document immediately upon approval, so that I have proof of my loan sanction for my records.

#### Acceptance Criteria

1. WHEN all loan conditions are met and approved, THE Sanction Letter Generator SHALL create a PDF sanction letter automatically
2. WHEN generating the sanction letter, THE Sanction Letter Generator SHALL include all relevant loan details, terms, and conditions
3. WHEN the sanction letter is ready, THE Sanction Letter Generator SHALL make it available for immediate download
4. WHEN the letter is generated, THE Sanction Letter Generator SHALL ensure proper formatting and official branding
5. WHEN the process completes, THE Master Agent SHALL notify the customer and provide download instructions

### Requirement 6

**User Story:** As a system administrator, I want the Master Agent to orchestrate all worker agents seamlessly, so that the customer experiences a smooth, unified interaction.

#### Acceptance Criteria

1. WHEN tasks need delegation, THE Master Agent SHALL determine which Worker Agent to trigger based on conversation context
2. WHEN Worker Agents complete tasks, THE Master Agent SHALL receive status updates and coordinate next steps
3. WHEN errors occur in any Worker Agent, THE Master Agent SHALL handle exceptions gracefully and inform the customer appropriately
4. WHEN the loan process is complete, THE Master Agent SHALL summarize the outcome and close the conversation professionally
5. WHEN edge cases arise (rejections, additional documentation needed), THE Master Agent SHALL manage the flow and customer communication

### Requirement 7

**User Story:** As a customer, I want the system to handle document uploads when required, so that I can complete additional verification steps without leaving the chat interface.

#### Acceptance Criteria

1. WHEN salary slip verification is required, THE System SHALL provide a secure file upload interface within the chat
2. WHEN documents are uploaded, THE System SHALL validate file format and size requirements
3. WHEN processing uploaded documents, THE System SHALL extract relevant information for underwriting decisions
4. WHEN document processing is complete, THE System SHALL continue with the loan approval workflow
5. WHEN document upload fails, THE System SHALL provide clear error messages and retry options

### Requirement 8

**User Story:** As a business analyst, I want the system to integrate with existing backend services, so that we can leverage current infrastructure and data sources.

#### Acceptance Criteria

1. WHEN customer data is needed, THE System SHALL fetch information from the CRM server via API calls
2. WHEN credit scores are required, THE System SHALL retrieve data from the credit bureau API
3. WHEN pre-approved limits are needed, THE System SHALL query the Offer Mart server
4. WHEN API calls fail, THE System SHALL implement retry logic and graceful error handling
5. WHEN data is retrieved, THE System SHALL validate and sanitize all external data before processing