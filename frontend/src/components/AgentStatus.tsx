import React from 'react';
import './AgentStatus.css';

interface AgentStatusProps {
  currentAgent: 'master' | 'sales' | 'verification' | 'underwriting' | 'sanction';
}

const AgentStatus: React.FC<AgentStatusProps> = ({ currentAgent }) => {
  const getAgentInfo = (agent: string) => {
    switch (agent) {
      case 'master':
        return {
          name: 'Loan Assistant',
          description: 'Guiding your loan application',
          color: '#4CAF50'
        };
      case 'sales':
        return {
          name: 'Sales Specialist',
          description: 'Discussing loan options',
          color: '#2196F3'
        };
      case 'verification':
        return {
          name: 'Verification Team',
          description: 'Verifying your details',
          color: '#FF9800'
        };
      case 'underwriting':
        return {
          name: 'Underwriting Team',
          description: 'Evaluating your application',
          color: '#9C27B0'
        };
      case 'sanction':
        return {
          name: 'Document Team',
          description: 'Preparing your documents',
          color: '#607D8B'
        };
      default:
        return {
          name: 'Assistant',
          description: 'Ready to help',
          color: '#4CAF50'
        };
    }
  };

  const agentInfo = getAgentInfo(currentAgent);

  return (
    <div className="agent-status">
      <div 
        className="agent-indicator"
        style={{ backgroundColor: agentInfo.color }}
      />
      <div className="agent-info">
        <div className="agent-name">{agentInfo.name}</div>
        <div className="agent-description">{agentInfo.description}</div>
      </div>
    </div>
  );
};

export default AgentStatus;