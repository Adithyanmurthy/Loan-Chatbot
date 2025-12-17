# Implementation Plan

- [x] 1. Set up project structure and development environment




  - Create directory structure for frontend (React), backend (Python/Flask), and mock APIs (Node.js)
  - Initialize package.json, requirements.txt, and configuration files
  - Set up development dependencies and build tools
  - Configure CORS and basic security settings
  - _Requirements: All system requirements_

- [x] 2. Implement core data models and interfaces




  - [x] 2.1 Create TypeScript interfaces for frontend data models


    - Define CustomerProfile, LoanApplication, ConversationContext, and AgentTask interfaces
    - Implement data validation functions for all models
    - _Requirements: 1.4, 2.1, 3.1, 4.1_

  - [ ]* 2.2 Write property test for data model validation
    - **Property 3: Customer Information Collection**
    - **Validates: Requirements 1.4**

  - [x] 2.3 Create Python data classes for backend models


    - Implement Pydantic models for type safety and validation
    - Add serialization/deserialization methods
    - _Requirements: 1.4, 2.1, 3.1, 4.1_

  - [ ]* 2.4 Write unit tests for data model validation
    - Test model creation, validation, and serialization
    - Test edge cases with invalid data
    - _Requirements: 1.4, 2.1, 3.1, 4.1_

- [x] 3. Build mock external APIs (Node.js)





  - [x] 3.1 Implement CRM API server


    - Create `/crm/:userId` endpoint returning customer KYC data
    - Add synthetic customer data for 10+ test profiles
    - Implement error simulation for testing
    - _Requirements: 8.1_

  - [x] 3.2 Implement Credit Bureau API server


    - Create `/credit-score/:userId` endpoint returning credit scores (0-900)
    - Add realistic credit score distribution in test data
    - Implement timeout and failure simulation
    - _Requirements: 8.2_


  - [x] 3.3 Implement Offer Mart API server

    - Create `/offers/:userId` endpoint returning pre-approved limits
    - Add varied pre-approved amounts and interest rates
    - Implement service unavailability simulation
    - _Requirements: 8.3_

  - [ ]* 3.4 Write property test for external API integration
    - **Property 30: External API Integration**
    - **Validates: Requirements 8.1, 8.2, 8.3**

  - [ ]* 3.5 Write property test for API failure resilience
    - **Property 31: API Failure Resilience**
    - **Validates: Requirements 8.4**

- [x] 4. Implement base agent framework (Python/Flask)




  - [x] 4.1 Create base Agent class and common interfaces


    - Implement task execution interface and status reporting
    - Add error handling and logging mechanisms
    - Create context sharing functionality between agents
    - _Requirements: 6.1, 6.2, 6.3_

  - [x] 4.2 Implement conversation context management


    - Create ConversationContext class with state persistence
    - Add session management and context recovery
    - Implement context sharing between Master and Worker agents
    - _Requirements: 1.4, 6.1, 6.2_

  - [ ]* 4.3 Write property test for agent coordination
    - **Property 21: Task Coordination**
    - **Validates: Requirements 6.2**

- [x] 5. Implement Master Agent orchestration logic




  - [x] 5.1 Create Master Agent controller class


    - Implement conversation flow management
    - Add Worker Agent selection logic based on context
    - Create task delegation and coordination mechanisms
    - _Requirements: 6.1, 6.2, 6.4_

  - [x] 5.2 Implement conversation initiation and management


    - Add personalized greeting and conversation startup
    - Implement conversation state tracking and transitions
    - Create conversation closure and summary functionality
    - _Requirements: 1.1, 1.4, 6.4_

  - [ ]* 5.3 Write property test for Master Agent conversation initiation
    - **Property 1: Master Agent Conversation Initiation**
    - **Validates: Requirements 1.1**

  - [ ]* 5.4 Write property test for agent selection logic
    - **Property 20: Agent Selection Logic**
    - **Validates: Requirements 6.1**

  - [ ]* 5.5 Write property test for process completion summary
    - **Property 23: Process Completion Summary**
    - **Validates: Requirements 6.4**

- [x] 6. Implement Sales Agent functionality




  - [x] 6.1 Create Sales Agent class with negotiation logic


    - Implement loan term presentation and negotiation
    - Add customer objection handling with alternatives
    - Create financial capacity assessment logic
    - _Requirements: 2.1, 2.2, 2.3_

  - [x] 6.2 Implement term calculation and validation


    - Add EMI calculation functions
    - Implement affordability assessment logic
    - Create term adjustment algorithms within approved limits
    - _Requirements: 2.2, 2.3_

  - [ ]* 6.3 Write property test for intent recognition and response
    - **Property 2: Intent Recognition and Response**
    - **Validates: Requirements 1.2**

  - [ ]* 6.4 Write property test for sales agent term negotiation
    - **Property 4: Sales Agent Term Negotiation**
    - **Validates: Requirements 2.1**

  - [ ]* 6.5 Write property test for financial capacity alignment
    - **Property 5: Financial Capacity Alignment**
    - **Validates: Requirements 2.2**

  - [ ]* 6.6 Write property test for objection handling
    - **Property 6: Objection Handling with Alternatives**
    - **Validates: Requirements 2.3**

  - [ ]* 6.7 Write property test for agent handoff coordination
    - **Property 7: Agent Handoff Coordination**
    - **Validates: Requirements 2.5**

- [x] 7. Checkpoint - Ensure all tests pass





  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Implement Verification Agent functionality





  - [x] 8.1 Create Verification Agent class


    - Implement KYC validation against CRM server
    - Add phone and address verification logic
    - Create verification failure handling and documentation requests
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

  - [x] 8.2 Implement CRM integration and data validation


    - Add CRM API client with retry logic
    - Implement data comparison and validation algorithms
    - Create verification status tracking and reporting
    - _Requirements: 3.1, 3.5, 8.1_

  - [ ]* 8.3 Write property test for comprehensive KYC verification
    - **Property 8: Comprehensive KYC Verification**
    - **Validates: Requirements 3.1, 3.2, 3.3**

  - [ ]* 8.4 Write property test for verification failure handling
    - **Property 9: Verification Failure Handling**
    - **Validates: Requirements 3.4**

  - [ ]* 8.5 Write property test for verification success status
    - **Property 10: Verification Success Status**
    - **Validates: Requirements 3.5**

- [x] 9. Implement Underwriting Agent functionality




  - [x] 9.1 Create Underwriting Agent class with business rules







    - Implement credit score fetching from Credit Bureau API
    - Add loan approval/rejection logic based on business rules
    - Create EMI calculation and affordability assessment
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

  - [ ] 9.2 Implement underwriting decision engine





    - Add instant approval logic for amounts ≤ pre-approved limit
    - Implement conditional approval with salary verification
    - Create rejection logic for excess amounts and low credit scores
    - _Requirements: 4.2, 4.3, 4.4, 4.5_

  - [ ]* 9.3 Write property test for credit score retrieval
    - **Property 11: Credit Score Retrieval**
    - **Validates: Requirements 4.1**

  - [ ]* 9.4 Write property test for instant approval rule
    - **Property 12: Instant Approval Rule**
    - **Validates: Requirements 4.2**

  - [ ]* 9.5 Write property test for conditional approval with EMI check
    - **Property 13: Conditional Approval with EMI Check**
    - **Validates: Requirements 4.3**

  - [ ]* 9.6 Write property test for excess amount rejection
    - **Property 14: Excess Amount Rejection**
    - **Validates: Requirements 4.4**

  - [ ]* 9.7 Write property test for credit score rejection rule
    - **Property 15: Credit Score Rejection Rule**
    - **Validates: Requirements 4.5**

- [-] 10. Implement document handling and file upload system


  - [x] 10.1 Create file upload handling infrastructure


    - Implement secure file upload endpoints
    - Add file validation for format and size requirements
    - Create document storage and retrieval mechanisms
    - _Requirements: 7.1, 7.2_


  - [x] 10.2 Implement document processing logic





    - Add salary slip parsing and information extraction
    - Implement document validation and verification
    - Create workflow continuation after document processing
    - _Requirements: 7.3, 7.4_

  - [ ]* 10.3 Write property test for file upload interface provision
    - **Property 25: File Upload Interface Provision**
    - **Validates: Requirements 7.1**

  - [ ]* 10.4 Write property test for file validation
    - **Property 26: File Validation**
    - **Validates: Requirements 7.2**

  - [ ]* 10.5 Write property test for document information extraction
    - **Property 27: Document Information Extraction**
    - **Validates: Requirements 7.3**

  - [ ]* 10.6 Write property test for workflow continuation after processing
    - **Property 28: Workflow Continuation After Processing**
    - **Validates: Requirements 7.4**

  - [ ]* 10.7 Write property test for upload error handling
    - **Property 29: Upload Error Handling**
    - **Validates: Requirements 7.5**

- [ ] 11. Implement Sanction Letter Generator





  - [x] 11.1 Create PDF generation functionality using FPDF

    - Implement sanction letter template and formatting
    - Add loan details, terms, and conditions to PDF
    - Create download link generation and file serving
    - _Requirements: 5.1, 5.2, 5.3_

  - [x] 11.2 Implement document generation workflow


    - Add automatic PDF creation upon loan approval
    - Implement download availability and customer notification
    - Create error handling for PDF generation failures
    - _Requirements: 5.1, 5.3, 5.5_

  - [ ]* 11.3 Write property test for automatic PDF generation
    - **Property 16: Automatic PDF Generation**
    - **Validates: Requirements 5.1**

  - [ ]* 11.4 Write property test for complete document content
    - **Property 17: Complete Document Content**
    - **Validates: Requirements 5.2**

  - [ ]* 11.5 Write property test for download availability
    - **Property 18: Download Availability**
    - **Validates: Requirements 5.3**

  - [ ]* 11.6 Write property test for completion notification
    - **Property 19: Completion Notification**
    - **Validates: Requirements 5.5**

- [x] 12. Implement error handling and resilience features



  - [x] 12.1 Add comprehensive error handling across all agents


    - Implement graceful error handling for Worker Agent failures
    - Add customer communication for error scenarios
    - Create error logging and monitoring infrastructure

    - _Requirements: 6.3, 6.5_

  - [x] 12.2 Implement API resilience and retry logic


    - Add exponential backoff retry for external API calls
    - Implement fallback mechanisms for service unavailability
    - Create data validation and sanitization for external data
    - _Requirements: 8.4, 8.5_

  - [ ]* 12.3 Write property test for error handling and communication
    - **Property 22: Error Handling and Communication**
    - **Validates: Requirements 6.3**

  - [ ]* 12.4 Write property test for edge case management
    - **Property 24: Edge Case Management**
    - **Validates: Requirements 6.5**

  - [ ]* 12.5 Write property test for data validation and sanitization
    - **Property 32: Data Validation and Sanitization**
    - **Validates: Requirements 8.5**

- [x] 13. Build React frontend chat interface



  - [x] 13.1 Create responsive chat UI components


    - Implement message bubble components for conversation display
    - Add typing indicators and agent status displays
    - Create input field with send button and file upload widget
    - _Requirements: 1.1, 7.1_

  - [x] 13.2 Implement chat functionality and state management


    - Add real-time message handling and conversation flow
    - Implement file upload interface integration
    - Create download link display for generated documents
    - _Requirements: 1.1, 5.3, 7.1_

  - [x] 13.3 Add frontend API integration


    - Implement HTTP client for backend communication
    - Add error handling and retry logic for API calls
    - Create loading states and user feedback mechanisms
    - _Requirements: 1.1, 6.3_

  - [ ]* 13.4 Write unit tests for React components
    - Test chat interface rendering and user interactions
    - Test file upload component functionality
    - Test API integration and error handling
    - _Requirements: 1.1, 5.3, 7.1_

- [x] 14. Implement Flask API endpoints and routing




  - [x] 14.1 Create REST API endpoints for chat functionality


    - Implement `/chat/message` endpoint for message processing
    - Add `/chat/status` endpoint for conversation status
    - Create `/chat/reset` endpoint for conversation reset
    - _Requirements: 1.1, 6.1, 6.4_

  - [x] 14.2 Add file upload and document endpoints


    - Implement `/upload/salary-slip` endpoint for document upload
    - Add `/download/sanction-letter/:id` endpoint for PDF download
    - Create proper error handling and validation for all endpoints
    - _Requirements: 7.1, 5.3_

  - [ ]* 14.3 Write integration tests for API endpoints
    - Test complete conversation flows through API
    - Test file upload and download functionality
    - Test error scenarios and edge cases
    - _Requirements: 1.1, 5.3, 7.1_

- [x] 15. Final integration and end-to-end testing





  - [x] 15.1 Integrate all components and test complete workflows


    - Connect frontend, backend, and mock APIs
    - Test complete customer journeys from initiation to sanction letter
    - Verify all agent handoffs and coordination work correctly
    - _Requirements: All requirements_


  - [ ] 15.2 Performance testing and optimization
    - Test system behavior with multiple concurrent conversations
    - Verify response times meet sub-5-minute target for standard applications
    - Optimize any performance bottlenecks identified
    - _Requirements: All requirements_

  - [ ]* 15.3 Write end-to-end property tests
    - Test complete conversation flows with property-based inputs
    - Verify system behavior across diverse customer profiles
    - Test edge cases and error recovery scenarios
    - _Requirements: All requirements_

- [ ] 16. Final Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.