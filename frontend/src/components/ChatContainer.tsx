import React, { useEffect, useState } from 'react';
import ChatInterface from './ChatInterface';
import { useChat } from '../hooks/useChat';
import './ChatContainer.css';

interface VerificationData {
  customerData: {
    name: string;
    phone: string;
    address?: string;
    city?: string;
  };
  loanData?: any;
  sessionId?: string;
}

interface ChatContainerProps {
  onBack?: () => void;
  onStartVerification?: (data: VerificationData) => void;
  verificationResult?: any;
}

const ChatContainer: React.FC<ChatContainerProps> = ({ onBack, onStartVerification, verificationResult }) => {
  const {
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
  } = useChat();

  const [pendingVerification, setPendingVerification] = useState<any>(null);
  const [selectedLoanOption, setSelectedLoanOption] = useState<any>(null);
  const [verificationProcessed, setVerificationProcessed] = useState(false);

  // Handle verification result when returning from verification page
  useEffect(() => {
    if (verificationResult && pendingVerification && !verificationProcessed) {
      setVerificationProcessed(true);
      setPendingVerification(null);
      
      // Show detailed verification complete message with Continue button
      addMessage({
        content: `✅ **KYC Verification Complete!**

**Verified Details:**
• Name: ${customerData?.name || 'Customer'} ✓
• Phone: ${customerData?.phone || 'Verified'} ✓
• Aadhaar: XXXX XXXX ${verificationResult.aadhaarLast4 || '1234'} ✓
• Address: ${verificationResult.verifiedAddress || customerData?.city || 'Verified'} ✓

**Verification Score:** ${verificationResult.verificationScore}%

🎉 **Your identity has been successfully verified!**

Now let's check your credit score and eligibility for the loan.

[CONTINUE_CREDIT_CHECK]`,
        sender: 'agent',
        timestamp: new Date(),
        messageType: 'text',
        agentType: 'verification'
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [verificationResult, pendingVerification, verificationProcessed]);

  const handleSendMessage = async (message: string) => {
    // Handle special button actions
    if (message === 'Continue with credit check') {
      // Send message to backend to trigger credit check/underwriting
      await sendMessage('Verification complete. Please check my credit score and eligibility for the loan.');
      return;
    }
    
    if (message === 'Proceed with loan approval' || message === 'Check my eligibility') {
      // Trigger loan approval - use keywords that trigger underwriting
      await sendMessage('Yes, I agree. Please proceed with loan approval and check my eligibility.');
      return;
    }
    
    if (message === 'Generate my sanction letter' || 
        message === 'Please approve my loan and generate the sanction letter' ||
        message.includes('sanction letter')) {
      // Trigger sanction letter generation
      await sendMessage('Yes, please approve my loan and generate my sanction letter now.');
      return;
    }
    
    if (message === 'view_history') {
      // Navigate to history page - go back to landing then to history
      if (onBack) {
        onBack();
      }
      return;
    }
    
    await sendMessage(message);
  };

  const handleFileUpload = async (file: File) => {
    await uploadFile(file);
  };

  const handleFormSubmit = async (formData: Record<string, any>) => {
    await submitForm(formData);
  };

  const handleLoanOptionSelect = async (option: any) => {
    setSelectedLoanOption(option);
    await selectLoanOption(option);
  };

  const handleProceedToVerification = () => {
    if (onStartVerification && customerData) {
      setPendingVerification(true);
      onStartVerification({
        customerData: {
          name: customerData.name,
          phone: customerData.phone,
          address: `${customerData.city}`,
          city: customerData.city
        },
        loanData: selectedLoanOption,
        sessionId: conversationContext?.sessionId
      });
    }
  };

  return (
    <div className="chat-container">
      {onBack && (
        <div className="chat-nav-header">
          <button className="back-button" onClick={onBack}>
            ← Back to Home
          </button>
          <span className="nav-title">AI Loan Assistant</span>
        </div>
      )}
      
      {error && (
        <div className="error-banner">
          <span className="error-message">{error}</span>
          <button 
            className="error-dismiss"
            onClick={() => window.location.reload()}
          >
            Retry
          </button>
        </div>
      )}
      
      <ChatInterface
        messages={messages}
        isTyping={isTyping}
        currentAgent={currentAgent}
        onSendMessage={handleSendMessage}
        onFileUpload={handleFileUpload}
        onFormSubmit={handleFormSubmit}
        onLoanOptionSelect={handleLoanOptionSelect}
        onProceedToVerification={handleProceedToVerification}
        isLoading={isLoading}
      />
      
      {conversationContext && (
        <div className="conversation-info">
          <div className="session-info">
            Session: {conversationContext.sessionId.slice(-8)}
          </div>
          <button 
            className="reset-button"
            onClick={resetConversation}
            disabled={isLoading}
          >
            New Conversation
          </button>
        </div>
      )}
    </div>
  );
};

export default ChatContainer;
