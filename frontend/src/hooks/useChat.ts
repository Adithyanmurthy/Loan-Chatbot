import { useState, useCallback, useRef } from 'react';
import { ChatMessage, ConversationContext } from '../types/models';
import { chatApi } from '../services/chatApi';

interface UseChatReturn {
  messages: ChatMessage[];
  isTyping: boolean;
  isLoading: boolean;
  currentAgent: 'master' | 'sales' | 'verification' | 'underwriting' | 'sanction';
  conversationContext: ConversationContext | null;
  sendMessage: (content: string) => Promise<void>;
  submitForm: (formData: Record<string, any>) => Promise<void>;
  selectLoanOption: (option: any) => Promise<void>;
  uploadFile: (file: File) => Promise<void>;
  resetConversation: () => Promise<void>;
  error: string | null;
  addMessage: (message: Omit<ChatMessage, 'id'>) => ChatMessage;
}

interface CustomerData {
  name: string;
  phone: string;
  city: string;
  age: number;
  loanAmount: number;
  salary: number;
  employmentType: string;
}

export const useChat = (): UseChatReturn & { customerData: CustomerData | null } => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome_msg',
      content: 'Hello! I\'m your AI Loan Assistant. I\'m here to help you with your personal loan application. How can I assist you today?',
      sender: 'agent',
      timestamp: new Date(),
      messageType: 'text',
      agentType: 'master'
    }
  ]);
  const [isTyping, setIsTyping] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [currentAgent, setCurrentAgent] = useState<'master' | 'sales' | 'verification' | 'underwriting' | 'sanction'>('master');
  const [conversationContext, setConversationContext] = useState<ConversationContext | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [customerData, setCustomerData] = useState<CustomerData | null>(null);
  
  const messageIdCounter = useRef(0);

  const generateMessageId = () => {
    messageIdCounter.current += 1;
    return `msg_${Date.now()}_${messageIdCounter.current}`;
  };

  const addMessage = useCallback((message: Omit<ChatMessage, 'id'>) => {
    const newMessage: ChatMessage = {
      ...message,
      id: generateMessageId(),
    };
    setMessages(prev => [...prev, newMessage]);
    return newMessage;
  }, []);

  const sendMessage = useCallback(async (content: string, formData?: Record<string, any>) => {
    if ((!content.trim() && !formData) || isLoading) return;

    setError(null);
    setIsLoading(true);

    // Add user message immediately
    const userMessage = addMessage({
      content: formData ? `Submitted form: ${formData.form_data?.full_name || 'Customer Information'}` : content,
      sender: 'user',
      timestamp: new Date(),
      messageType: formData ? 'form' : 'text'
    });

    try {
      setIsTyping(true);
      
      // Send message to backend
      const requestData: any = {
        message: content,
        sessionId: conversationContext?.sessionId,
        messageId: userMessage.id
      };
      
      if (formData) {
        requestData.form_data = formData;
        requestData.message_type = 'form_submission';
      }
      
      const response = await chatApi.sendMessage(requestData);

      setIsTyping(false);

      // Update conversation context
      if (response.context) {
        setConversationContext(response.context);
        setCurrentAgent(response.context.currentAgent);
      }

      // Add agent response
      if (response.message) {
        addMessage({
          content: response.message,
          sender: 'agent',
          timestamp: new Date(),
          messageType: response.messageType || 'text',
          agentType: response.agentType || currentAgent,
          metadata: response.metadata
        });
      }

      // Handle download links for sanction letters
      if (response.sanctionLetter) {
        addMessage({
          content: 'Your sanction letter is ready for download!',
          sender: 'agent',
          timestamp: new Date(),
          messageType: 'download_link',
          agentType: 'sanction',
          metadata: {
            downloadUrl: response.sanctionLetter.downloadUrl,
            filename: response.sanctionLetter.filename
          }
        });
      }
      
      // Also handle download_url in metadata (alternative format)
      if (response.metadata?.download_url && response.messageType === 'download_link') {
        // The message already has the download link in metadata, no need to add another message
        // Just ensure the metadata is properly formatted
      }

    } catch (err) {
      setIsTyping(false);
      const errorMessage = err instanceof Error ? err.message : 'Failed to send message';
      setError(errorMessage);
      
      // Add error message to chat
      addMessage({
        content: `Sorry, I encountered an error: ${errorMessage}. Please try again.`,
        sender: 'agent',
        timestamp: new Date(),
        messageType: 'system',
        agentType: currentAgent
      });
    } finally {
      setIsLoading(false);
    }
  }, [isLoading, conversationContext, currentAgent, addMessage]);

  const submitForm = useCallback(async (formData: Record<string, any>) => {
    // Store customer data from form
    if (formData.form_data) {
      const fd = formData.form_data;
      setCustomerData({
        name: fd.full_name || '',
        phone: fd.phone || '',
        city: fd.city || '',
        age: parseInt(fd.age) || 0,
        loanAmount: parseFloat(fd.loan_amount) || 0,
        salary: parseFloat(fd.monthly_salary) || 0,
        employmentType: fd.employment_type || 'salaried'
      });
    }
    await sendMessage('Form submitted with customer information', formData);
  }, [sendMessage]);

  const selectLoanOption = useCallback(async (option: any) => {
    const optionText = `I select Option ${option.index || 1} with ₹${option.emi?.toLocaleString()} EMI for ${option.tenure} months.`;
    
    // Add user selection message
    addMessage({
      content: optionText,
      sender: 'user',
      timestamp: new Date(),
      messageType: 'text'
    });
    
    // Add confirmation message with customer details
    const customerName = customerData?.name || 'Valued Customer';
    const customerPhone = customerData?.phone || 'N/A';
    const customerCity = customerData?.city || 'N/A';
    
    addMessage({
      content: `✅ **Option ${option.index || 1} Selected!**\n\n**Your Loan Details:**\n• Amount: ₹${option.amount?.toLocaleString()}\n• EMI: ₹${option.emi?.toLocaleString()}/month\n• Tenure: ${option.tenure} months\n• Interest: ${option.interest_rate}% p.a.\n\n**Applicant Details:**\n• Name: ${customerName}\n• Phone: ${customerPhone}\n• City: ${customerCity}\n\nNow let's verify your identity to proceed with the loan approval.\n\n[YES_PROCEED]`,
      sender: 'agent',
      timestamp: new Date(),
      messageType: 'text',
      agentType: 'verification',
      metadata: { selectedOption: option, customerData }
    });
  }, [addMessage, customerData]);

  const uploadFile = useCallback(async (file: File) => {
    if (isLoading) return;

    setError(null);
    setIsLoading(true);

    // Add file upload message
    addMessage({
      content: `Uploading ${file.name}...`,
      sender: 'user',
      timestamp: new Date(),
      messageType: 'file'
    });

    try {
      setIsTyping(true);

      const response = await chatApi.uploadFile({
        file,
        sessionId: conversationContext?.sessionId || ''
      });

      setIsTyping(false);

      // Update conversation context
      if (response.context) {
        setConversationContext(response.context);
        setCurrentAgent(response.context.currentAgent);
      }

      // Add success message
      addMessage({
        content: response.message || 'File uploaded successfully!',
        sender: 'agent',
        timestamp: new Date(),
        messageType: 'text',
        agentType: response.agentType || currentAgent
      });

      // Continue with workflow if there's a follow-up message
      if (response.followUpMessage) {
        setTimeout(() => {
          addMessage({
            content: response.followUpMessage!,
            sender: 'agent',
            timestamp: new Date(),
            messageType: 'text',
            agentType: response.agentType || currentAgent
          });
        }, 1000);
      }

    } catch (err) {
      setIsTyping(false);
      const errorMessage = err instanceof Error ? err.message : 'Failed to upload file';
      setError(errorMessage);
      
      addMessage({
        content: `File upload failed: ${errorMessage}. Please try again.`,
        sender: 'agent',
        timestamp: new Date(),
        messageType: 'system',
        agentType: currentAgent
      });
    } finally {
      setIsLoading(false);
    }
  }, [isLoading, conversationContext, currentAgent, addMessage]);

  const resetConversation = useCallback(async () => {
    try {
      setIsLoading(true);
      await chatApi.resetConversation(conversationContext?.sessionId);
      
      // Clear state and reset to initial welcome message
      setMessages([{
        id: 'welcome_msg',
        content: 'Hello! I\'m your AI Loan Assistant. I\'m here to help you with your personal loan application. How can I assist you today?',
        sender: 'agent',
        timestamp: new Date(),
        messageType: 'text',
        agentType: 'master'
      }]);
      setConversationContext(null);
      setCurrentAgent('master');
      setError(null);
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to reset conversation';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, [conversationContext]);

  return {
    messages,
    isTyping,
    isLoading,
    currentAgent,
    conversationContext,
    sendMessage,
    submitForm,
    selectLoanOption,
    uploadFile,
    resetConversation,
    error,
    customerData,
    addMessage
  };
};