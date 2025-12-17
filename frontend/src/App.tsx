import React, { useState } from 'react';
import ChatContainer from './components/ChatContainer';
import LandingPage from './components/LandingPage';
import HistoryPage from './components/HistoryPage';
import VerificationPage from './components/VerificationPage';
import ErrorBoundary from './components/ErrorBoundary';
import './App.css';

type PageType = 'landing' | 'chat' | 'history' | 'verification';

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

function App() {
  const [currentPage, setCurrentPage] = useState<PageType>('landing');
  const [verificationData, setVerificationData] = useState<VerificationData | null>(null);
  const [verificationResult, setVerificationResult] = useState<any>(null);
  const [chatMounted, setChatMounted] = useState(false);

  const handleStartVerification = (data: VerificationData) => {
    setVerificationData(data);
    setCurrentPage('verification');
  };

  const handleVerificationComplete = (result: any) => {
    setVerificationResult(result);
    setCurrentPage('chat');
  };

  const handleGoToChat = () => {
    setChatMounted(true);
    setCurrentPage('chat');
  };

  const handleBackToLanding = () => {
    setCurrentPage('landing');
    // Don't unmount chat to preserve state
  };

  return (
    <div className="App">
      <ErrorBoundary>
        {/* Landing Page */}
        {currentPage === 'landing' && (
          <LandingPage 
            onGetStarted={handleGoToChat}
            onViewHistory={() => setCurrentPage('history')}
          />
        )}

        {/* History Page */}
        {currentPage === 'history' && (
          <HistoryPage onBack={() => setCurrentPage('landing')} />
        )}

        {/* Chat Container - Keep mounted once started to preserve state */}
        {chatMounted && (
          <div style={{ display: currentPage === 'chat' ? 'block' : 'none', height: '100%' }}>
            <ChatContainer 
              onBack={handleBackToLanding}
              onStartVerification={handleStartVerification}
              verificationResult={verificationResult}
            />
          </div>
        )}

        {/* Verification Page */}
        {currentPage === 'verification' && verificationData && (
          <VerificationPage
            customerData={verificationData.customerData}
            onVerificationComplete={handleVerificationComplete}
            onBack={() => setCurrentPage('chat')}
          />
        )}
      </ErrorBoundary>
    </div>
  );
}

export default App;
