import React from 'react';
import { ChatMessage } from '../types/models';
import CustomerInfoForm from './CustomerInfoForm';
import LoanOptionsDisplay from './LoanOptionsDisplay';
import './MessageBubble.css';

interface MessageBubbleProps {
  message: ChatMessage;
  onFormSubmit?: (data: Record<string, any>) => void;
  onLoanOptionSelect?: (option: any) => void;
  onProceedToVerification?: () => void;
  onActionClick?: (action: string) => void;
}

const MessageBubble: React.FC<MessageBubbleProps> = ({ 
  message, 
  onFormSubmit, 
  onLoanOptionSelect,
  onProceedToVerification,
  onActionClick 
}) => {
  const formatTime = (timestamp: Date) => {
    return new Date(timestamp).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const handleDownload = async (downloadUrl: string, filename?: string) => {
    try {
      const baseUrl = process.env.REACT_APP_API_URL || 'http://localhost:5001';
      const fullUrl = downloadUrl.startsWith('http') 
        ? downloadUrl 
        : `${baseUrl}${downloadUrl}`;
      
      const response = await fetch(fullUrl, {
        method: 'GET',
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error(`Download failed: ${response.status} ${response.statusText}`);
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename || 'sanction_letter.pdf';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
    } catch (error) {
      console.error('Download failed:', error);
      alert('Failed to download the file. Please try again or contact support.');
    }
  };

  const getAgentDisplayName = (agentType?: string) => {
    switch (agentType) {
      case 'master': return 'Loan Assistant';
      case 'sales': return 'Sales Specialist';
      case 'verification': return 'Verification Team';
      case 'underwriting': return 'Underwriting Team';
      case 'sanction': return 'Document Team';
      default: return 'Assistant';
    }
  };

  // Parse action buttons from message content
  const parseActionButtons = (content: string) => {
    const buttonPatterns = [
      { pattern: /\[YES_PROCEED\]/g, label: '✅ Yes, Proceed to Verification', action: 'start_verification', isVerification: true },
      { pattern: /\[START_VERIFICATION\]/g, label: '🔐 Start KYC Verification', action: 'start_verification', isVerification: true },
      { pattern: /\[VIEW_DETAILS\]/g, label: '📋 View Details', action: 'Show me the details', isVerification: false },
      { pattern: /\[APPROVE_LOAN\]/g, label: '✅ Approve & Generate Sanction Letter', action: 'Please approve my loan and generate the sanction letter', isVerification: false },
      { pattern: /\[CHECK_ELIGIBILITY\]/g, label: '📊 Check Eligibility', action: 'Check my eligibility', isVerification: false },
      { pattern: /\[CONTINUE_CREDIT_CHECK\]/g, label: '📊 Continue to Credit Check', action: 'Continue with credit check', isVerification: false },
      { pattern: /\[PROCEED_APPROVAL\]/g, label: '✅ Proceed to Loan Approval', action: 'Proceed with loan approval', isVerification: false },
      { pattern: /\[GENERATE_LETTER\]/g, label: '📄 Generate Sanction Letter', action: 'Generate my sanction letter', isVerification: false },
      { pattern: /\[VIEW_HISTORY\]/g, label: '📋 View My Applications', action: 'view_history', isVerification: false },
    ];
    
    let cleanContent = content;
    const buttons: { label: string; action: string; isVerification: boolean }[] = [];
    
    buttonPatterns.forEach(({ pattern, label, action, isVerification }) => {
      if (pattern.test(content)) {
        buttons.push({ label, action, isVerification });
        cleanContent = cleanContent.replace(pattern, '');
      }
    });
    
    return { cleanContent: cleanContent.trim(), buttons };
  };

  const renderMessageContent = () => {
    const { cleanContent, buttons } = parseActionButtons(message.content);
    
    switch (message.messageType) {
      case 'download_link':
        return (
          <div className="download-message">
            <div className="text-message" dangerouslySetInnerHTML={{ __html: formatMessage(cleanContent) }} />
            {(message.metadata?.downloadUrl || message.metadata?.download_url) && (
              <div className="download-section">
                <div className="download-container">
                  <button
                    onClick={() => handleDownload(message.metadata?.downloadUrl || message.metadata?.download_url, message.metadata?.filename)}
                    className="download-button"
                  >
                    📄 Download {message.metadata?.filename || 'Sanction Letter'}
                  </button>
                  <p className="download-note">Click the button above to download your sanction letter PDF</p>
                </div>
              </div>
            )}
          </div>
        );
        
      case 'system':
        return <div className="system-message">{cleanContent}</div>;
        
      case 'file':
        return (
          <div className="file-message">
            <span className="file-icon">📎</span>
            <span>{cleanContent}</span>
          </div>
        );
        
      case 'form':
        return (
          <div className="form-message">
            <div className="text-message" dangerouslySetInnerHTML={{ __html: formatMessage(cleanContent) }} />
            {message.metadata?.form_data && onFormSubmit && (
              <CustomerInfoForm
                formData={message.metadata.form_data}
                onSubmit={onFormSubmit}
                isLoading={false}
              />
            )}
          </div>
        );
        
      case 'loan_options':
        return (
          <div className="loan-options-message">
            <div className="text-message" dangerouslySetInnerHTML={{ __html: formatMessage(cleanContent) }} />
            {message.metadata?.loan_options && onLoanOptionSelect && (
              <LoanOptionsDisplay
                options={message.metadata.loan_options}
                onSelect={onLoanOptionSelect}
                customerProfile={message.metadata.customer_profile}
              />
            )}
          </div>
        );
        
      default:
        return (
          <div>
            <div className="text-message" dangerouslySetInnerHTML={{ __html: formatMessage(cleanContent) }} />
            {buttons.length > 0 && (
              <div className="action-buttons">
                {buttons.map((btn, idx) => (
                  <button
                    key={idx}
                    className={`action-btn ${btn.isVerification ? 'verification-btn' : ''}`}
                    onClick={() => {
                      if (btn.isVerification && onProceedToVerification) {
                        onProceedToVerification();
                      } else if (onActionClick) {
                        onActionClick(btn.action);
                      }
                    }}
                  >
                    {btn.label}
                  </button>
                ))}
              </div>
            )}
          </div>
        );
    }
  };

  // Format message with markdown-like syntax
  const formatMessage = (text: string) => {
    if (!text) return '';
    
    return text
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\n/g, '<br/>')
      .replace(/•/g, '&bull;')
      .replace(/✅/g, '<span class="emoji-check">✅</span>')
      .replace(/❌/g, '<span class="emoji-cross">❌</span>')
      .replace(/⚠️/g, '<span class="emoji-warn">⚠️</span>')
      .replace(/🎉/g, '<span class="emoji">🎉</span>')
      .replace(/💰/g, '<span class="emoji">💰</span>')
      .replace(/📊/g, '<span class="emoji">📊</span>')
      .replace(/📋/g, '<span class="emoji">📋</span>');
  };

  return (
    <div className={`message-bubble ${message.sender}`}>
      <div className="message-header">
        {message.sender === 'agent' && (
          <span className="agent-name">
            {getAgentDisplayName(message.agentType)}
          </span>
        )}
        <span className="message-time">{formatTime(message.timestamp)}</span>
      </div>
      <div className="message-content">
        {renderMessageContent()}
      </div>
    </div>
  );
};

export default MessageBubble;
