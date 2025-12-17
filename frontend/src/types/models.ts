/**
 * Core data models for the AI Loan Chatbot frontend
 * Based on requirements: 1.4, 2.1, 3.1, 4.1
 */

export interface CustomerProfile {
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

export interface LoanDetails {
  id: string;
  amount: number;
  tenure: number;
  interestRate: number;
  emi: number;
  status: string;
  startDate: Date;
}

export interface LoanApplication {
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

export interface ConversationContext {
  sessionId: string;
  customerId?: string;
  currentAgent: 'master' | 'sales' | 'verification' | 'underwriting' | 'sanction';
  conversationStage: string;
  collectedData: Record<string, any>;
  pendingTasks: string[];
  completedTasks: string[];
  errors: ErrorLog[];
}

export interface ErrorLog {
  id: string;
  timestamp: Date;
  message: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  context?: Record<string, any>;
}

export interface AgentTask {
  id: string;
  type: 'sales' | 'verification' | 'underwriting' | 'document_generation';
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  input: Record<string, any>;
  output?: Record<string, any>;
  error?: string;
  createdAt: Date;
  completedAt?: Date;
}

// Additional interfaces for chat functionality
export interface ChatMessage {
  id: string;
  content: string;
  sender: 'user' | 'agent';
  timestamp: Date;
  messageType: 'text' | 'file' | 'system' | 'download_link' | 'form' | 'loan_options';
  agentType?: 'master' | 'sales' | 'verification' | 'underwriting' | 'sanction';
  metadata?: Record<string, any>;
}

export interface FileUpload {
  id: string;
  filename: string;
  fileType: string;
  fileSize: number;
  uploadStatus: 'pending' | 'uploading' | 'completed' | 'failed';
  uploadedAt?: Date;
  error?: string;
}

export interface SanctionLetter {
  id: string;
  loanApplicationId: string;
  filename: string;
  downloadUrl: string;
  generatedAt: Date;
  expiresAt: Date;
}