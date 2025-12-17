import React, { useState } from 'react';
import {
  Box, Container, Typography, Paper, TextField, Button, Stepper, Step, StepLabel,
  CircularProgress, Alert, Chip, Avatar, InputAdornment
} from '@mui/material';
import VerifiedUserIcon from '@mui/icons-material/VerifiedUser';
import PhoneAndroidIcon from '@mui/icons-material/PhoneAndroid';
import HomeIcon from '@mui/icons-material/Home';
import BadgeIcon from '@mui/icons-material/Badge';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import './VerificationPage.css';

interface VerificationPageProps {
  customerData: {
    name: string;
    phone: string;
    address?: string;
    city?: string;
  };
  onVerificationComplete: (verificationResult: any) => void;
  onBack: () => void;
}

const VerificationPage: React.FC<VerificationPageProps> = ({
  customerData,
  onVerificationComplete,
  onBack
}) => {
  const [activeStep, setActiveStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Form states
  const [aadhaarNumber, setAadhaarNumber] = useState('');
  const [phoneOtp, setPhoneOtp] = useState('');
  const [otpSent, setOtpSent] = useState(false);
  const [address, setAddress] = useState(customerData.address || '');
  const [pincode, setPincode] = useState('');
  
  // Verification states
  const [aadhaarVerified, setAadhaarVerified] = useState(false);
  const [phoneVerified, setPhoneVerified] = useState(false);
  const [addressVerified, setAddressVerified] = useState(false);

  const steps = [
    { label: 'Aadhaar Verification', icon: <BadgeIcon /> },
    { label: 'Phone OTP', icon: <PhoneAndroidIcon /> },
    { label: 'Address Verification', icon: <HomeIcon /> },
  ];

  const formatAadhaar = (value: string) => {
    const digits = value.replace(/\D/g, '').slice(0, 12);
    const parts = digits.match(/.{1,4}/g) || [];
    return parts.join(' ');
  };

  const handleAadhaarChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setAadhaarNumber(formatAadhaar(e.target.value));
  };

  const verifyAadhaar = async () => {
    const cleanAadhaar = aadhaarNumber.replace(/\s/g, '');
    if (cleanAadhaar.length !== 12) {
      setError('Please enter a valid 12-digit Aadhaar number');
      return;
    }
    
    setLoading(true);
    setError(null);
    
    // Simulate Aadhaar verification (Demo)
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // Demo: Accept any 12-digit number
    setAadhaarVerified(true);
    setLoading(false);
    setActiveStep(1);
  };

  const sendOtp = async () => {
    setLoading(true);
    setError(null);
    
    // Simulate OTP sending (Demo)
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    setOtpSent(true);
    setLoading(false);
  };

  const verifyOtp = async () => {
    if (phoneOtp.length !== 6) {
      setError('Please enter a valid 6-digit OTP');
      return;
    }
    
    setLoading(true);
    setError(null);
    
    // Simulate OTP verification (Demo - accept any 6 digits)
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    setPhoneVerified(true);
    setLoading(false);
    setActiveStep(2);
  };

  const verifyAddress = async () => {
    if (!address || pincode.length !== 6) {
      setError('Please enter complete address with valid 6-digit pincode');
      return;
    }
    
    setLoading(true);
    setError(null);
    
    // Simulate address verification (Demo)
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    setAddressVerified(true);
    setLoading(false);
    
    // All verifications complete
    setTimeout(() => {
      onVerificationComplete({
        aadhaarVerified: true,
        phoneVerified: true,
        addressVerified: true,
        aadhaarLast4: aadhaarNumber.replace(/\s/g, '').slice(-4),
        verifiedPhone: customerData.phone,
        verifiedAddress: `${address}, ${pincode}`,
        verificationScore: 95,
        verifiedAt: new Date().toISOString()
      });
    }, 1000);
  };

  const renderStepContent = () => {
    switch (activeStep) {
      case 0:
        return (
          <Box className="verification-step-content">
            <Avatar className="step-avatar aadhaar">
              <BadgeIcon />
            </Avatar>
            <Typography variant="h5" className="step-title">Aadhaar Verification</Typography>
            <Typography variant="body2" className="step-desc">
              Enter your 12-digit Aadhaar number for identity verification
            </Typography>
            
            <TextField
              fullWidth
              label="Aadhaar Number"
              value={aadhaarNumber}
              onChange={handleAadhaarChange}
              placeholder="XXXX XXXX XXXX"
              variant="outlined"
              className="verification-input"
              inputProps={{ maxLength: 14 }}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <BadgeIcon color="primary" />
                  </InputAdornment>
                ),
              }}
            />
            
            <Alert severity="info" className="demo-alert">
              <strong>Demo Mode:</strong> Enter any 12-digit number (e.g., 1234 5678 9012)
            </Alert>
            
            <Button
              variant="contained"
              size="large"
              fullWidth
              onClick={verifyAadhaar}
              disabled={loading || aadhaarNumber.replace(/\s/g, '').length !== 12}
              className="verify-btn"
            >
              {loading ? <CircularProgress size={24} /> : 'Verify Aadhaar'}
            </Button>
          </Box>
        );
        
      case 1:
        return (
          <Box className="verification-step-content">
            <Avatar className="step-avatar phone">
              <PhoneAndroidIcon />
            </Avatar>
            <Typography variant="h5" className="step-title">Phone Verification</Typography>
            <Typography variant="body2" className="step-desc">
              Verify your phone number: <strong>{customerData.phone}</strong>
            </Typography>
            
            {!otpSent ? (
              <>
                <Alert severity="info" className="demo-alert">
                  <strong>Demo Mode:</strong> Click to simulate OTP sending
                </Alert>
                <Button
                  variant="contained"
                  size="large"
                  fullWidth
                  onClick={sendOtp}
                  disabled={loading}
                  className="verify-btn"
                >
                  {loading ? <CircularProgress size={24} /> : 'Send OTP'}
                </Button>
              </>
            ) : (
              <>
                <TextField
                  fullWidth
                  label="Enter OTP"
                  value={phoneOtp}
                  onChange={(e) => setPhoneOtp(e.target.value.replace(/\D/g, '').slice(0, 6))}
                  placeholder="Enter 6-digit OTP"
                  variant="outlined"
                  className="verification-input"
                  inputProps={{ maxLength: 6 }}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <PhoneAndroidIcon color="primary" />
                      </InputAdornment>
                    ),
                  }}
                />
                
                <Alert severity="info" className="demo-alert">
                  <strong>Demo Mode:</strong> Enter any 6-digit number (e.g., 123456)
                </Alert>
                
                <Button
                  variant="contained"
                  size="large"
                  fullWidth
                  onClick={verifyOtp}
                  disabled={loading || phoneOtp.length !== 6}
                  className="verify-btn"
                >
                  {loading ? <CircularProgress size={24} /> : 'Verify OTP'}
                </Button>
                
                <Button variant="text" onClick={sendOtp} disabled={loading} className="resend-btn">
                  Resend OTP
                </Button>
              </>
            )}
          </Box>
        );
        
      case 2:
        return (
          <Box className="verification-step-content">
            <Avatar className="step-avatar address">
              <HomeIcon />
            </Avatar>
            <Typography variant="h5" className="step-title">Address Verification</Typography>
            <Typography variant="body2" className="step-desc">
              Confirm your residential address for loan processing
            </Typography>
            
            <TextField
              fullWidth
              label="Full Address"
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              placeholder="Enter your complete address"
              variant="outlined"
              multiline
              rows={3}
              className="verification-input"
            />
            
            <TextField
              fullWidth
              label="Pincode"
              value={pincode}
              onChange={(e) => setPincode(e.target.value.replace(/\D/g, '').slice(0, 6))}
              placeholder="6-digit pincode"
              variant="outlined"
              className="verification-input"
              inputProps={{ maxLength: 6 }}
            />
            
            <Alert severity="info" className="demo-alert">
              <strong>Demo Mode:</strong> Enter any address and 6-digit pincode
            </Alert>
            
            <Button
              variant="contained"
              size="large"
              fullWidth
              onClick={verifyAddress}
              disabled={loading || !address || pincode.length !== 6}
              className="verify-btn"
            >
              {loading ? <CircularProgress size={24} /> : 'Verify Address'}
            </Button>
          </Box>
        );
        
      default:
        return null;
    }
  };

  return (
    <div className="verification-page">
      <Box className="verification-header">
        <Container maxWidth="md">
          <Box display="flex" alignItems="center" gap={2}>
            <Button startIcon={<ArrowBackIcon />} onClick={onBack} className="back-btn">
              Back
            </Button>
            <VerifiedUserIcon className="header-icon" />
            <Typography variant="h5">KYC Verification</Typography>
          </Box>
        </Container>
      </Box>

      <Container maxWidth="sm" className="verification-content">
        <Paper className="verification-card" elevation={3}>
          {/* Customer Info */}
          <Box className="customer-info-bar">
            <Typography variant="body2">
              Verifying for: <strong>{customerData.name}</strong>
            </Typography>
            <Chip label="Secure Process" size="small" color="success" icon={<VerifiedUserIcon />} />
          </Box>

          {/* Stepper */}
          <Stepper activeStep={activeStep} alternativeLabel className="verification-stepper">
            {steps.map((step, index) => (
              <Step key={step.label} completed={
                (index === 0 && aadhaarVerified) ||
                (index === 1 && phoneVerified) ||
                (index === 2 && addressVerified)
              }>
                <StepLabel
                  StepIconComponent={() => (
                    <Avatar className={`stepper-icon ${activeStep === index ? 'active' : ''} ${
                      (index === 0 && aadhaarVerified) ||
                      (index === 1 && phoneVerified) ||
                      (index === 2 && addressVerified) ? 'completed' : ''
                    }`}>
                      {((index === 0 && aadhaarVerified) ||
                        (index === 1 && phoneVerified) ||
                        (index === 2 && addressVerified)) ? (
                        <CheckCircleIcon />
                      ) : (
                        step.icon
                      )}
                    </Avatar>
                  )}
                >
                  {step.label}
                </StepLabel>
              </Step>
            ))}
          </Stepper>

          {/* Error Alert */}
          {error && (
            <Alert severity="error" onClose={() => setError(null)} className="error-alert">
              {error}
            </Alert>
          )}

          {/* Step Content */}
          {renderStepContent()}

          {/* All Verified */}
          {aadhaarVerified && phoneVerified && addressVerified && (
            <Box className="all-verified">
              <CheckCircleIcon className="success-icon" />
              <Typography variant="h6">All Verifications Complete!</Typography>
              <Typography variant="body2">Redirecting to loan approval...</Typography>
              <CircularProgress size={24} className="redirect-loader" />
            </Box>
          )}
        </Paper>
      </Container>
    </div>
  );
};

export default VerificationPage;
