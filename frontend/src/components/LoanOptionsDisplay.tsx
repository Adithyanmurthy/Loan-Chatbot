import React, { useState } from 'react';
import './LoanOptionsDisplay.css';

interface LoanOption {
  amount: number;
  tenure: number;
  interest_rate: number;
  emi: number;
  total_payable: number;
  processing_fee: number;
  affordability_score: number;
  is_affordable?: boolean;
  risk_level?: string;
}

interface LoanOptionsDisplayProps {
  options: LoanOption[];
  onSelect: (option: LoanOption & { index: number }) => void;
  customerProfile?: any;
}

const LoanOptionsDisplay: React.FC<LoanOptionsDisplayProps> = ({
  options,
  onSelect,
  customerProfile,
}) => {
  const [selectedOption, setSelectedOption] = useState<number | null>(null);

  const formatCurrency = (amount: number) => {
    return `₹${amount?.toLocaleString('en-IN') || 0}`;
  };

  const formatTenure = (months: number) => {
    const years = Math.floor(months / 12);
    const remainingMonths = months % 12;
    if (years === 0) return `${months} months`;
    if (remainingMonths === 0) return `${years} year${years > 1 ? 's' : ''}`;
    return `${years}y ${remainingMonths}m`;
  };

  const handleSelect = (option: LoanOption, index: number) => {
    setSelectedOption(index);
    onSelect({ ...option, index: index + 1 });
  };

  if (!options || options.length === 0) {
    return <div className="no-options">No loan options available</div>;
  }

  return (
    <div className="loan-options-simple">
      <div className="options-header">
        <span className="options-icon">💰</span>
        <span>Select Your Preferred Option</span>
      </div>
      
      <div className="options-list">
        {options.slice(0, 3).map((option, index) => {
          const isSelected = selectedOption === index;
          const isRecommended = index === 0;
          
          return (
            <div
              key={index}
              className={`option-card ${isSelected ? 'selected' : ''} ${isRecommended ? 'recommended' : ''}`}
              onClick={() => handleSelect(option, index)}
            >
              {isRecommended && <div className="recommended-badge">⭐ Recommended</div>}
              {isSelected && <div className="selected-badge">✅ Selected</div>}
              
              <div className="option-header">
                <span className="option-number">Option {index + 1}</span>
              </div>
              
              <div className="option-emi">
                <span className="emi-label">Monthly EMI</span>
                <span className="emi-value">{formatCurrency(option.emi)}</span>
              </div>
              
              <div className="option-details">
                <div className="detail-row">
                  <span>Amount</span>
                  <span>{formatCurrency(option.amount)}</span>
                </div>
                <div className="detail-row">
                  <span>Tenure</span>
                  <span>{formatTenure(option.tenure)}</span>
                </div>
                <div className="detail-row">
                  <span>Interest</span>
                  <span>{option.interest_rate}% p.a.</span>
                </div>
                <div className="detail-row">
                  <span>Total</span>
                  <span>{formatCurrency(option.total_payable)}</span>
                </div>
              </div>
              
              <button 
                className={`select-btn ${isSelected ? 'selected' : ''}`}
                onClick={(e) => { e.stopPropagation(); handleSelect(option, index); }}
              >
                {isSelected ? '✓ Selected' : 'Select This'}
              </button>
            </div>
          );
        })}
      </div>
      
      {selectedOption !== null && (
        <div className="selection-note">
          ✅ Option {selectedOption + 1} selected. Processing your choice...
        </div>
      )}
    </div>
  );
};

export default LoanOptionsDisplay;
