import axios, { AxiosResponse } from 'axios';
import { ConversationContext, SanctionLetter } from '../types/models';

// API Configuration - Use relative URL when served from same server, or env variable
const API_BASE_URL = process.env.REACT_APP_API_URL || '';
const API_TIMEOUT = 30000; // 30 seconds

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request/Response interfaces
interface SendMessageRequest {
  message: string;
  sessionId?: string;
  messageId: string;
}

interface SendMessageResponse {
  message: string;
  messageType?: 'text' | 'system' | 'download_link';
  agentType?: 'master' | 'sales' | 'verification' | 'underwriting' | 'sanction';
  context: ConversationContext;
  sanctionLetter?: SanctionLetter;
  metadata?: Record<string, any>;
}

interface UploadFileRequest {
  file: File;
  sessionId: string;
}

interface UploadFileResponse {
  message: string;
  agentType?: 'master' | 'sales' | 'verification' | 'underwriting' | 'sanction';
  context: ConversationContext;
  followUpMessage?: string;
}

interface ConversationStatusResponse {
  context: ConversationContext;
  status: 'active' | 'completed' | 'error';
}

// Retry configuration
interface RetryConfig {
  maxRetries: number;
  baseDelay: number;
  maxDelay: number;
}

const DEFAULT_RETRY_CONFIG: RetryConfig = {
  maxRetries: 3,
  baseDelay: 1000, // 1 second
  maxDelay: 10000, // 10 seconds
};

// Exponential backoff retry utility
const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

const withRetry = async <T>(
  operation: () => Promise<T>,
  config: RetryConfig = DEFAULT_RETRY_CONFIG
): Promise<T> => {
  let lastError: Error;
  
  for (let attempt = 0; attempt <= config.maxRetries; attempt++) {
    try {
      return await operation();
    } catch (error) {
      lastError = error as Error;
      
      // Don't retry on client errors (4xx) except 408, 429
      if (axios.isAxiosError(error)) {
        const status = error.response?.status;
        if (status && status >= 400 && status < 500 && status !== 408 && status !== 429) {
          throw error;
        }
      }
      
      // Don't retry on the last attempt
      if (attempt === config.maxRetries) {
        break;
      }
      
      // Calculate delay with exponential backoff and jitter
      const delay = Math.min(
        config.baseDelay * Math.pow(2, attempt) + Math.random() * 1000,
        config.maxDelay
      );
      
      console.warn(`API call failed (attempt ${attempt + 1}/${config.maxRetries + 1}), retrying in ${delay}ms:`, error);
      await sleep(delay);
    }
  }
  
  throw lastError!;
};

// API Error handling
class ApiError extends Error {
  constructor(
    message: string,
    public status?: number,
    public code?: string
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const handleApiError = (error: any): never => {
  if (axios.isAxiosError(error)) {
    const status = error.response?.status;
    const message = error.response?.data?.message || error.message;
    const code = error.response?.data?.code || error.code;
    
    if (status === 429) {
      throw new ApiError('Too many requests. Please wait a moment and try again.', status, code);
    } else if (status === 503) {
      throw new ApiError('Service temporarily unavailable. Please try again later.', status, code);
    } else if (status && status >= 500) {
      throw new ApiError('Server error. Please try again later.', status, code);
    } else if (status === 400) {
      throw new ApiError(`Invalid request: ${message}`, status, code);
    } else if (error.code === 'ECONNABORTED') {
      throw new ApiError('Request timeout. Please check your connection and try again.', undefined, code);
    } else if (error.code === 'NETWORK_ERROR') {
      throw new ApiError('Network error. Please check your connection.', undefined, code);
    }
    
    throw new ApiError(message || 'An unexpected error occurred', status, code);
  }
  
  throw new ApiError(error?.message || 'An unexpected error occurred');
};

// API Methods
export const chatApi = {
  // Send a message to the chatbot
  sendMessage: async (request: SendMessageRequest): Promise<SendMessageResponse> => {
    try {
      return await withRetry(async () => {
        const response: AxiosResponse<SendMessageResponse> = await apiClient.post('/api/chat/message', request);
        return response.data;
      });
    } catch (error) {
      return handleApiError(error);
    }
  },

  // Upload a file (salary slip, documents)
  uploadFile: async (request: UploadFileRequest): Promise<UploadFileResponse> => {
    try {
      return await withRetry(async () => {
        const formData = new FormData();
        formData.append('file', request.file);
        formData.append('sessionId', request.sessionId);

        const response: AxiosResponse<UploadFileResponse> = await apiClient.post('/api/documents/upload/salary-slip', formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          timeout: 60000, // Longer timeout for file uploads
        });
        
        return response.data;
      }, { ...DEFAULT_RETRY_CONFIG, maxRetries: 2 }); // Fewer retries for file uploads
    } catch (error) {
      return handleApiError(error);
    }
  },

  // Get conversation status
  getConversationStatus: async (sessionId?: string): Promise<ConversationStatusResponse> => {
    try {
      return await withRetry(async () => {
        const url = sessionId ? `/api/chat/status?sessionId=${sessionId}` : '/api/chat/status';
        const response: AxiosResponse<ConversationStatusResponse> = await apiClient.get(url);
        return response.data;
      });
    } catch (error) {
      return handleApiError(error);
    }
  },

  // Reset conversation
  resetConversation: async (sessionId?: string): Promise<void> => {
    try {
      await withRetry(async () => {
        const data = sessionId ? { sessionId } : {};
        await apiClient.post('/api/chat/reset', data);
      });
    } catch (error) {
      return handleApiError(error);
    }
  },

  // Download sanction letter
  downloadSanctionLetter: async (letterId: string): Promise<Blob> => {
    try {
      return await withRetry(async () => {
        const response: AxiosResponse<Blob> = await apiClient.get(`/api/documents/download/sanction-letter/${letterId}`, {
          responseType: 'blob',
          timeout: 60000, // Longer timeout for downloads
        });
        return response.data;
      }, { ...DEFAULT_RETRY_CONFIG, maxRetries: 2 }); // Fewer retries for downloads
    } catch (error) {
      return handleApiError(error);
    }
  },

  // Health check
  healthCheck: async (): Promise<{ status: string; timestamp: string }> => {
    try {
      const response: AxiosResponse<{ status: string; timestamp: string }> = await apiClient.get('/health');
      return response.data;
    } catch (error) {
      return handleApiError(error);
    }
  }
};

// Request interceptor for logging
apiClient.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for logging and error handling
apiClient.interceptors.response.use(
  (response) => {
    console.log(`API Response: ${response.status} ${response.config.url}`);
    return response;
  },
  (error) => {
    console.error('API Response Error:', error.response?.status, error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export { ApiError };