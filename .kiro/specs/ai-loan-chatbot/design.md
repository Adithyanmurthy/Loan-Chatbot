# AI Loan Chatbot Design Document

## Overview

The AI Loan Chatbot is a multi-agent conversational system designed to automate the personal loan sales process for an NBFC. The system employs a Master Agent that orchestrates multiple specialized Worker Agents to handle customer conversations, verification, underwriting, and document generation in a seamless, human-like interaction.

The solution addresses the critical business need for instant, frictionless loan services in India's competitive financial market, aiming to improve sales conversion rates while reducing operational costs through intelligent automation.

## Architecture

### System Architecture Pattern
The system follows a **3-Tier Architecture** with **Multi-Agent Orchestration**:

1. **Presentation Layer (Tier 1)**: React & TypeScript responsive web interface
2. **Logic Layer (Tier 2)**: Python/Flask backend with AI agent orchestration
3. **Service Layer (Tier 3)**: Node.js mock APIs for external integrations

### Agent Architecture Pattern
The system implements a **Master-Worker Agent Pattern** where:
- **Master Agent**: Central orchestrator managing conversation flow and task delegation
- **Worker Agents**: Specialized agents handling specific domain tasks (Sales, Verification, Underwriting, Document Generation)

### Communication Flow
```
Customer ↔ Web Interface ↔ Master Agent ↔ Worker Agents ↔ External APIs
```

## Components and Interfaces

### Frontend Components

#### Chat Interface Component
- **Technology**: React with TypeScript
- **Responsibilities**: 
  - Render conversational UI with message bubbles
  - Handle user input and file uploads
  - Display typing indicators and agent status
  - Provide download links for generated documents
- **Key Features**:
  - Responsive design for desktop and mobile
  - Real-time message streaming
  - File upload widget for salary slips
  - Progress indicators for background processing

#### Message Handler Component
- **Responsibilities**:
  - Format and validate user messages
  - Handle different message types (text, file, system notifications)
  - Manage conversation state and history
  - Implement retry logic for failed messages

### Backend Components

#### Master Agent Controller
- **Technology**: Python with Flask framework
- **Responsibilities**:
  - Orchestrate conversation flow
  - Determine which Worker Agent to activate
  - Maintain conversation context and state
  - Handle error scenarios and fallbacks
- **Key Interfaces**:
  - `POST /chat/message` - Process user messages
  - `GET /chat/status` - Get conversation status
  - `POST /chat/reset` - Reset conversation state

#### Worker Agent Framework
Base class providing common functionality for all Worker Agents:
- Task execution interface
- Status reporting mechanisms
- Error handling and logging
- Context sharing with Master Agent

#### Sales Agent
- **Responsibilities**:
  - Engage customers in loan discussions
  - Negotiate terms (amount, tenure, interest rates)
  - Present personalized loan offers
  - Handle objections and provide alternatives
- **Key Methods**:
  - `negotiate_terms(customer_profile, loan_request)`
  - `present_offers(pre_approved_limits)`
  - `handle_objections(customer_concerns)`

#### Verification Agent
- **Responsibilities**:
  - Validate KYC details against CRM
  - Confirm phone and address information
  - Request additional documentation when needed
- **Key Methods**:
  - `verify_kyc(customer_id, provided_details)`
  - `validate_phone(phone_number)`
  - `confirm_address(address_details)`

#### Underwriting Agent
- **Responsibilities**:
  - Fetch credit scores from bureau API
  - Apply business rules for loan approval
  - Calculate EMI and affordability ratios
  - Make instant approval/rejection decisions
- **Key Methods**:
  - `fetch_credit_score(customer_id)`
  - `evaluate_eligibility(loan_amount, credit_score, salary)`
  - `calculate_emi(principal, rate, tenure)`

#### Sanction Letter Generator
- **Responsibilities**:
  - Generate PDF sanction letters using FPDF library
  - Include all loan terms and conditions
  - Apply official branding and formatting
  - Provide secure download links
- **Key Methods**:
  - `generate_sanction_letter(loan_details)`
  - `format_pdf_document(content, branding)`
  - `create_download_link(pdf_file)`

### External Service Interfaces

#### CRM API Interface
- **Endpoint**: `/crm/:userId`
- **Purpose**: Retrieve customer KYC data
- **Response Format**: JSON with customer details, phone, address
- **Error Handling**: Retry logic with exponential backoff

#### Credit Bureau API Interface
- **Endpoint**: `/credit-score/:userId`
- **Purpose**: Fetch customer credit scores (0-900 scale)
- **Response Format**: JSON with credit score and report date
- **Error Handling**: Fallback to default scoring if API unavailable

#### Offer Mart API Interface
- **Endpoint**: `/offers/:userId`
- **Purpose**: Get pre-approved loan limits
- **Response Format**: JSON with approved amounts and interest rates
- **Error Handling**: Use conservative defaults if service unavailable

## Data Models

### Customer Profile Model
```typescript
interface CustomerProfile {
  id: string;
  name: string;
  age: number;
  city: string;
  phone: string;
  address: string;
  currentLoans: LoanDetails[];
  creditScore: number;
  preApprovedLimit: number;
  salary?: number;
  employmentType: string;
}
```

### Loan Application Model
```typescript
interface LoanApplication {
  id: string;
  customerId: string;
  requestedAmount: number;
  tenure: number;
  interestRate: number;
  emi: number;
  status: 'pending' | 'approved' | 'rejected' | 'requires_documents';
  createdAt: Date;
  approvedAt?: Date;
  rejectionReason?: string;
}
```

### Conversation Context Model
```typescript
interface ConversationContext {
  sessionId: string;
  customerId?: string;
  currentAgent: 'master' | 'sales' | 'verification' | 'underwriting' | 'sanction';
  conversationStage: string;
  collectedData: Record<string, any>;
  pendingTasks: string[];
  completedTasks: string[];
  errors: ErrorLog[];
}
```

### Agent Task Model
```typescript
interface AgentTask {
  id: string;
  type: 'sales' | 'verification' | 'underwriting' | 'document_generation';
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  input: Record<string, any>;
  output?: Record<string, any>;
  error?: string;
  createdAt: Date;
  completedAt?: Date;
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property Reflection

After analyzing all acceptance criteria, several properties can be consolidated to eliminate redundancy:

- **Agent Orchestration Properties**: Properties 6.1, 6.2, 6.3, 6.4, and 6.5 can be combined into comprehensive orchestration properties
- **API Integration Properties**: Properties 8.1, 8.2, and 8.3 can be consolidated into a single external API integration property
- **Verification Properties**: Properties 3.1, 3.2, and 3.3 can be combined into a comprehensive verification property
- **Underwriting Business Rules**: Properties 4.2, 4.3, 4.4, and 4.5 represent the complete underwriting decision matrix and should remain separate for clarity

### Core Properties

**Property 1: Master Agent Conversation Initiation**
*For any* customer landing on the chatbot, the Master Agent should respond with an initial personalized message within the conversation interface
**Validates: Requirements 1.1**

**Property 2: Intent Recognition and Response**
*For any* customer expression of loan interest, the Master Agent should understand the intent and present relevant loan options
**Validates: Requirements 1.2**

**Property 3: Customer Information Collection**
*For any* conversation flow, the Master Agent should collect all required customer information fields before proceeding to verification
**Validates: Requirements 1.4**

**Property 4: Sales Agent Term Negotiation**
*For any* customer showing interest, the Sales Agent should present loan terms including amount, tenure, and interest rates
**Validates: Requirements 2.1**

**Property 5: Financial Capacity Alignment**
*For any* customer profile with defined financial capacity, the Sales Agent should present terms that align with their affordability
**Validates: Requirements 2.2**

**Property 6: Objection Handling with Alternatives**
*For any* customer objection to proposed terms, the Sales Agent should provide alternative options within approved limits
**Validates: Requirements 2.3**

**Property 7: Agent Handoff Coordination**
*For any* agreed terms between Sales Agent and customer, control should pass back to the Master Agent for next workflow steps
**Validates: Requirements 2.5**

**Property 8: Comprehensive KYC Verification**
*For any* customer details provided, the Verification Agent should confirm all KYC details against the CRM server
**Validates: Requirements 3.1, 3.2, 3.3**

**Property 9: Verification Failure Handling**
*For any* failed verification attempt, the Verification Agent should request additional documentation or clarification
**Validates: Requirements 3.4**

**Property 10: Verification Success Status**
*For any* successful verification completion, the customer should be marked as verified for loan processing
**Validates: Requirements 3.5**

**Property 11: Credit Score Retrieval**
*For any* credit assessment requirement, the Underwriting Agent should fetch the customer's credit score from the credit bureau API
**Validates: Requirements 4.1**

**Property 12: Instant Approval Rule**
*For any* loan amount less than or equal to the pre-approved limit, the Underwriting Agent should approve the loan instantly
**Validates: Requirements 4.2**

**Property 13: Conditional Approval with EMI Check**
*For any* loan amount less than or equal to 2× the pre-approved limit, the Underwriting Agent should request salary slip and approve only if EMI ≤ 50% of salary
**Validates: Requirements 4.3**

**Property 14: Excess Amount Rejection**
*For any* loan amount exceeding 2× the pre-approved limit, the Underwriting Agent should reject the application
**Validates: Requirements 4.4**

**Property 15: Credit Score Rejection Rule**
*For any* credit score below 700, the Underwriting Agent should reject the application regardless of other factors
**Validates: Requirements 4.5**

**Property 16: Automatic PDF Generation**
*For any* approved loan meeting all conditions, the Sanction Letter Generator should create a PDF sanction letter automatically
**Validates: Requirements 5.1**

**Property 17: Complete Document Content**
*For any* generated sanction letter, the PDF should include all relevant loan details, terms, and conditions
**Validates: Requirements 5.2**

**Property 18: Download Availability**
*For any* ready sanction letter, the system should make it available for immediate download
**Validates: Requirements 5.3**

**Property 19: Completion Notification**
*For any* completed loan process, the Master Agent should notify the customer and provide download instructions
**Validates: Requirements 5.5**

**Property 20: Agent Selection Logic**
*For any* task delegation requirement, the Master Agent should determine the correct Worker Agent based on conversation context
**Validates: Requirements 6.1**

**Property 21: Task Coordination**
*For any* Worker Agent task completion, the Master Agent should receive status updates and coordinate appropriate next steps
**Validates: Requirements 6.2**

**Property 22: Error Handling and Communication**
*For any* Worker Agent error, the Master Agent should handle exceptions gracefully and inform the customer appropriately
**Validates: Requirements 6.3**

**Property 23: Process Completion Summary**
*For any* completed loan process, the Master Agent should summarize the outcome and close the conversation professionally
**Validates: Requirements 6.4**

**Property 24: Edge Case Management**
*For any* edge case scenario (rejections, additional documentation), the Master Agent should manage flow and customer communication appropriately
**Validates: Requirements 6.5**

**Property 25: File Upload Interface Provision**
*For any* salary slip verification requirement, the system should provide a secure file upload interface within the chat
**Validates: Requirements 7.1**

**Property 26: File Validation**
*For any* uploaded document, the system should validate file format and size requirements
**Validates: Requirements 7.2**

**Property 27: Document Information Extraction**
*For any* processed uploaded document, the system should extract relevant information for underwriting decisions
**Validates: Requirements 7.3**

**Property 28: Workflow Continuation After Processing**
*For any* completed document processing, the system should continue with the loan approval workflow
**Validates: Requirements 7.4**

**Property 29: Upload Error Handling**
*For any* failed document upload, the system should provide clear error messages and retry options
**Validates: Requirements 7.5**

**Property 30: External API Integration**
*For any* data requirement (customer, credit, offers), the system should fetch information from the appropriate external API (CRM, Credit Bureau, Offer Mart)
**Validates: Requirements 8.1, 8.2, 8.3**

**Property 31: API Failure Resilience**
*For any* external API failure, the system should implement retry logic and graceful error handling
**Validates: Requirements 8.4**

**Property 32: Data Validation and Sanitization**
*For any* retrieved external data, the system should validate and sanitize all information before processing
**Validates: Requirements 8.5**

## Error Handling

### Error Categories and Strategies

#### 1. External API Failures
- **CRM Server Unavailable**: Implement exponential backoff retry (3 attempts), fallback to manual verification request
- **Credit Bureau Timeout**: Retry with increased timeout, fallback to conservative credit assessment
- **Offer Mart Service Down**: Use cached pre-approved limits, default to conservative offers

#### 2. Agent Processing Errors
- **Sales Agent Negotiation Failure**: Escalate to Master Agent with simplified offer presentation
- **Verification Agent KYC Mismatch**: Request manual document upload and human verification
- **Underwriting Agent Calculation Error**: Log error, request manual underwriting review

#### 3. Document Processing Errors
- **File Upload Failure**: Provide clear error message, offer alternative upload methods
- **PDF Generation Error**: Retry generation, fallback to email delivery of approval details
- **Document Parsing Error**: Request re-upload with format guidelines

#### 4. Conversation Flow Errors
- **Context Loss**: Implement conversation state recovery from database
- **Agent Handoff Failure**: Master Agent maintains conversation, logs handoff error
- **Customer Input Parsing Error**: Request clarification with suggested formats

### Error Recovery Mechanisms

#### Graceful Degradation
- If advanced AI features fail, fallback to rule-based responses
- If real-time processing fails, queue requests for batch processing
- If personalization fails, use generic but functional responses

#### User Communication Strategy
- Always inform users of delays or issues in conversational language
- Provide alternative paths when primary flows fail
- Offer human agent escalation for complex error scenarios

#### Logging and Monitoring
- Comprehensive error logging with conversation context
- Real-time monitoring of agent performance and API health
- Automated alerts for critical system failures

## Testing Strategy

### Dual Testing Approach

The system will employ both unit testing and property-based testing to ensure comprehensive coverage and correctness validation.

#### Unit Testing Approach
- **Framework**: pytest for Python backend, Jest for React frontend
- **Coverage**: Specific examples, integration points, error conditions
- **Focus Areas**:
  - Agent initialization and configuration
  - API integration endpoints with mock responses
  - File upload and validation logic
  - PDF generation with sample data
  - Conversation state management

#### Property-Based Testing Approach
- **Framework**: Hypothesis for Python (backend agents and logic)
- **Configuration**: Minimum 100 iterations per property test
- **Test Tagging**: Each property-based test tagged with format: `**Feature: ai-loan-chatbot, Property {number}: {property_text}**`
- **Coverage**: Universal properties across all valid inputs
- **Focus Areas**:
  - Agent orchestration logic with varied conversation contexts
  - Underwriting business rules with diverse customer profiles
  - API integration resilience with simulated failures
  - Document processing with various file types and contents

#### Test Data Strategy
- **Synthetic Customer Data**: 10+ diverse customer profiles with varying:
  - Credit scores (300-900 range)
  - Pre-approved limits (₹50K - ₹10L range)
  - Salary ranges (₹25K - ₹2L monthly)
  - Employment types and cities
- **Mock API Responses**: Comprehensive test data for all external services
- **Edge Case Scenarios**: Boundary conditions, error states, timeout scenarios

#### Integration Testing
- **End-to-End Conversation Flows**: Complete customer journeys from initiation to sanction letter
- **Cross-Agent Communication**: Verify proper handoffs and data sharing between agents
- **External API Integration**: Test with mock services simulating real-world conditions

#### Performance Testing
- **Concurrent User Simulation**: Test system behavior with multiple simultaneous conversations
- **Response Time Validation**: Ensure sub-5-minute processing for standard loan applications
- **Resource Usage Monitoring**: Verify system stability under load

### Success Metrics
- **Conversion Rate**: (Sanction letters generated / Conversations initiated)
- **Process Cycle Time**: Average time from conversation start to final decision
- **Error Rate**: Percentage of conversations experiencing technical failures
- **Customer Satisfaction**: Post-conversation feedback scores

The testing strategy ensures that both specific functionality (unit tests) and general system behavior (property tests) are thoroughly validated, providing confidence in the system's correctness and reliability.