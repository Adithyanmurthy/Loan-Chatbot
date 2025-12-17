/**
 * Data validation functions for frontend models
 * Based on requirements: 1.4, 2.1, 3.1, 4.1
 */

import { CustomerProfile, LoanApplication, ConversationContext, AgentTask, ChatMessage, FileUpload } from './models';

// Validation result type
export interface ValidationResult {
  isValid: boolean;
  errors: string[];
}

// Customer Profile Validation
export function validateCustomerProfile(profile: Partial<CustomerProfile>): ValidationResult {
  const errors: string[] = [];

  if (!profile.id || profile.id.trim() === '') {
    errors.push('Customer ID is required');
  }

  if (!profile.name || profile.name.trim() === '') {
    errors.push('Customer name is required');
  }

  if (!profile.age || profile.age < 18 || profile.age > 100) {
    errors.push('Customer age must be between 18 and 100');
  }

  if (!profile.city || profile.city.trim() === '') {
    errors.push('City is required');
  }

  if (!profile.phone || !isValidPhoneNumber(profile.phone)) {
    errors.push('Valid phone number is required');
  }

  if (!profile.address || profile.address.trim() === '') {
    errors.push('Address is required');
  }

  if (profile.creditScore !== undefined && (profile.creditScore < 300 || profile.creditScore > 900)) {
    errors.push('Credit score must be between 300 and 900');
  }

  if (profile.preApprovedLimit !== undefined && profile.preApprovedLimit < 0) {
    errors.push('Pre-approved limit cannot be negative');
  }

  if (profile.salary !== undefined && profile.salary < 0) {
    errors.push('Salary cannot be negative');
  }

  if (!profile.employmentType || profile.employmentType.trim() === '') {
    errors.push('Employment type is required');
  }

  return {
    isValid: errors.length === 0,
    errors
  };
}

// Loan Application Validation
export function validateLoanApplication(application: Partial<LoanApplication>): ValidationResult {
  const errors: string[] = [];

  if (!application.id || application.id.trim() === '') {
    errors.push('Application ID is required');
  }

  if (!application.customerId || application.customerId.trim() === '') {
    errors.push('Customer ID is required');
  }

  if (!application.requestedAmount || application.requestedAmount <= 0) {
    errors.push('Requested amount must be greater than 0');
  }

  if (!application.tenure || application.tenure <= 0 || application.tenure > 360) {
    errors.push('Tenure must be between 1 and 360 months');
  }

  if (application.interestRate !== undefined && (application.interestRate < 0 || application.interestRate > 50)) {
    errors.push('Interest rate must be between 0 and 50 percent');
  }

  if (application.emi !== undefined && application.emi < 0) {
    errors.push('EMI cannot be negative');
  }

  const validStatuses = ['pending', 'approved', 'rejected', 'requires_documents'];
  if (application.status && !validStatuses.includes(application.status)) {
    errors.push('Invalid application status');
  }

  if (!application.createdAt) {
    errors.push('Creation date is required');
  }

  return {
    isValid: errors.length === 0,
    errors
  };
}

// Conversation Context Validation
export function validateConversationContext(context: Partial<ConversationContext>): ValidationResult {
  const errors: string[] = [];

  if (!context.sessionId || context.sessionId.trim() === '') {
    errors.push('Session ID is required');
  }

  const validAgents = ['master', 'sales', 'verification', 'underwriting', 'sanction'];
  if (context.currentAgent && !validAgents.includes(context.currentAgent)) {
    errors.push('Invalid current agent type');
  }

  if (!context.conversationStage || context.conversationStage.trim() === '') {
    errors.push('Conversation stage is required');
  }

  if (!context.collectedData) {
    errors.push('Collected data object is required');
  }

  if (!Array.isArray(context.pendingTasks)) {
    errors.push('Pending tasks must be an array');
  }

  if (!Array.isArray(context.completedTasks)) {
    errors.push('Completed tasks must be an array');
  }

  if (!Array.isArray(context.errors)) {
    errors.push('Errors must be an array');
  }

  return {
    isValid: errors.length === 0,
    errors
  };
}

// Agent Task Validation
export function validateAgentTask(task: Partial<AgentTask>): ValidationResult {
  const errors: string[] = [];

  if (!task.id || task.id.trim() === '') {
    errors.push('Task ID is required');
  }

  const validTypes = ['sales', 'verification', 'underwriting', 'document_generation'];
  if (!task.type || !validTypes.includes(task.type)) {
    errors.push('Valid task type is required');
  }

  const validStatuses = ['pending', 'in_progress', 'completed', 'failed'];
  if (!task.status || !validStatuses.includes(task.status)) {
    errors.push('Valid task status is required');
  }

  if (!task.input) {
    errors.push('Task input is required');
  }

  if (!task.createdAt) {
    errors.push('Creation date is required');
  }

  return {
    isValid: errors.length === 0,
    errors
  };
}

// Chat Message Validation
export function validateChatMessage(message: Partial<ChatMessage>): ValidationResult {
  const errors: string[] = [];

  if (!message.id || message.id.trim() === '') {
    errors.push('Message ID is required');
  }

  if (!message.content || message.content.trim() === '') {
    errors.push('Message content is required');
  }

  const validSenders = ['user', 'agent'];
  if (!message.sender || !validSenders.includes(message.sender)) {
    errors.push('Valid sender type is required');
  }

  if (!message.timestamp) {
    errors.push('Timestamp is required');
  }

  const validMessageTypes = ['text', 'file', 'system', 'download_link'];
  if (!message.messageType || !validMessageTypes.includes(message.messageType)) {
    errors.push('Valid message type is required');
  }

  const validAgentTypes = ['master', 'sales', 'verification', 'underwriting', 'sanction'];
  if (message.agentType && !validAgentTypes.includes(message.agentType)) {
    errors.push('Invalid agent type');
  }

  return {
    isValid: errors.length === 0,
    errors
  };
}

// File Upload Validation
export function validateFileUpload(upload: Partial<FileUpload>): ValidationResult {
  const errors: string[] = [];

  if (!upload.id || upload.id.trim() === '') {
    errors.push('Upload ID is required');
  }

  if (!upload.filename || upload.filename.trim() === '') {
    errors.push('Filename is required');
  }

  if (!upload.fileType || upload.fileType.trim() === '') {
    errors.push('File type is required');
  }

  if (!upload.fileSize || upload.fileSize <= 0) {
    errors.push('File size must be greater than 0');
  }

  // File size limit: 10MB
  if (upload.fileSize && upload.fileSize > 10 * 1024 * 1024) {
    errors.push('File size cannot exceed 10MB');
  }

  const validStatuses = ['pending', 'uploading', 'completed', 'failed'];
  if (!upload.uploadStatus || !validStatuses.includes(upload.uploadStatus)) {
    errors.push('Valid upload status is required');
  }

  // Validate file type for salary slips (PDF, JPG, PNG)
  const allowedTypes = ['application/pdf', 'image/jpeg', 'image/png', 'image/jpg'];
  if (upload.fileType && !allowedTypes.includes(upload.fileType.toLowerCase())) {
    errors.push('File type must be PDF, JPG, or PNG');
  }

  return {
    isValid: errors.length === 0,
    errors
  };
}

// Helper function for phone number validation
function isValidPhoneNumber(phone: string): boolean {
  // Indian phone number validation (10 digits, optionally with +91)
  const phoneRegex = /^(\+91)?[6-9]\d{9}$/;
  return phoneRegex.test(phone.replace(/\s+/g, ''));
}

// Helper function to validate email format
export function isValidEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

// Helper function to validate amount format
export function isValidAmount(amount: number): boolean {
  return amount > 0 && amount <= 10000000; // Max 1 crore
}

// Helper function to validate tenure
export function isValidTenure(tenure: number): boolean {
  return tenure >= 6 && tenure <= 360; // 6 months to 30 years
}