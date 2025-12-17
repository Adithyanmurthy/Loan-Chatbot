import React, { useRef, useEffect } from 'react';
import { ChatMessage } from '../types/models';
import MessageBubble from './MessageBubble';
import TypingIndicator from './TypingIndicator';
import ChatInput from './ChatInput';
import AgentStatus from './AgentStatus';
import './ChatInterface.css';

interface ChatInterfaceProps {
  messages: ChatMessage[];
  isTyping: boolean;
  currentAgent: 'master' | 'sales' | 'verification' | 'underwriting' | 'sanction';
  onSendMessage: (message: string) => void;
  onFileUpload: (file: File) => void;
  onFormSubmit?: (data: Record<string, any>) => void;
  onLoanOptionSelect?: (option: any) => void;
  onProceedToVerification?: () => void;
  isLoading: boolean;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({
  messages,
  isTyping,
  currentAgent,
  onSendMessage,
  onFileUpload,
  onFormSubmit,
  onLoanOptionSelect,
  onProceedToVerification,
  isLoading
}) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  return (
    <div className="chat-interface">
      <div className="chat-header">
        <h2>AI Loan Assistant</h2>
        <AgentStatus currentAgent={currentAgent} />
      </div>
      
      <div className="chat-messages">
        {messages.map((message) => (
          <MessageBubble 
            key={message.id} 
            message={message} 
            onFormSubmit={onFormSubmit}
            onLoanOptionSelect={onLoanOptionSelect}
            onProceedToVerification={onProceedToVerification}
            onActionClick={onSendMessage}
          />
        ))}
        
        {isTyping && <TypingIndicator />}
        <div ref={messagesEndRef} />
      </div>
      
      <ChatInput
        onSendMessage={onSendMessage}
        onFileUpload={onFileUpload}
        disabled={isLoading}
      />
    </div>
  );
};

export default ChatInterface;
