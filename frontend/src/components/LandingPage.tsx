import React, { useState, useEffect } from 'react';
import {
  Box, Button, Container, Typography, Card, CardContent, Paper,
  AppBar, Toolbar, IconButton, Drawer, List, ListItem, ListItemIcon,
  ListItemText, Divider, Chip, Avatar
} from '@mui/material';
import Grid from '@mui/material/Grid';
import AccountBalanceIcon from '@mui/icons-material/AccountBalance';
import SpeedIcon from '@mui/icons-material/Speed';
import SecurityIcon from '@mui/icons-material/Security';
import SupportAgentIcon from '@mui/icons-material/SupportAgent';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import MenuIcon from '@mui/icons-material/Menu';
import ChatIcon from '@mui/icons-material/Chat';
import HistoryIcon from '@mui/icons-material/History';
import CalculateIcon from '@mui/icons-material/Calculate';
import DescriptionIcon from '@mui/icons-material/Description';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import VerifiedUserIcon from '@mui/icons-material/VerifiedUser';
import CurrencyRupeeIcon from '@mui/icons-material/CurrencyRupee';
import CalendarMonthIcon from '@mui/icons-material/CalendarMonth';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import StarIcon from '@mui/icons-material/Star';
import GroupsIcon from '@mui/icons-material/Groups';
import EmojiEventsIcon from '@mui/icons-material/EmojiEvents';
import './LandingPage.css';

interface LandingPageProps {
  onGetStarted: () => void;
  onViewHistory: () => void;
}

const LandingPage: React.FC<LandingPageProps> = ({ onGetStarted, onViewHistory }) => {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [loanAmount, setLoanAmount] = useState(500000);
  const [tenure, setTenure] = useState(36);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 50);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const calculateEMI = (principal: number, months: number, rate: number = 12) => {
    const r = rate / 12 / 100;
    const emi = (principal * r * Math.pow(1 + r, months)) / (Math.pow(1 + r, months) - 1);
    return Math.round(emi);
  };

  const emi = calculateEMI(loanAmount, tenure);
  const totalPayable = emi * tenure;
  const totalInterest = totalPayable - loanAmount;

  const features = [
    { icon: <SpeedIcon />, title: 'Instant Approval', desc: 'Get loan approved in under 5 minutes with AI-powered processing', color: '#6366f1' },
    { icon: <SupportAgentIcon />, title: 'AI Assistant', desc: '24/7 intelligent chatbot guides you through the entire journey', color: '#8b5cf6' },
    { icon: <SecurityIcon />, title: 'Bank-Grade Security', desc: 'Your data is protected with enterprise-level encryption', color: '#06b6d4' },
    { icon: <VerifiedUserIcon />, title: 'Quick KYC', desc: 'Automated verification process - no manual paperwork needed', color: '#10b981' },
    { icon: <DescriptionIcon />, title: 'Digital Documents', desc: 'Sanction letters generated instantly as downloadable PDFs', color: '#f59e0b' },
    { icon: <TrendingUpIcon />, title: 'Best Rates', desc: 'Competitive interest rates starting from just 10.5% p.a.', color: '#ef4444' },
  ];

  const steps = [
    { num: '01', title: 'Start Conversation', desc: 'Chat with our AI assistant and share your loan requirements' },
    { num: '02', title: 'Quick Verification', desc: 'Automated KYC verification of your identity and documents' },
    { num: '03', title: 'Instant Decision', desc: 'AI-powered underwriting gives you immediate approval' },
    { num: '04', title: 'Get Your Letter', desc: 'Download your sanction letter and complete the process' },
  ];

  const stats = [
    { value: '50K+', label: 'Happy Customers', icon: <GroupsIcon /> },
    { value: '₹500Cr+', label: 'Loans Disbursed', icon: <CurrencyRupeeIcon /> },
    { value: '4.8★', label: 'Customer Rating', icon: <StarIcon /> },
    { value: '99%', label: 'Approval Rate', icon: <EmojiEventsIcon /> },
  ];

  const testimonials = [
    { name: 'Rahul Sharma', role: 'Business Owner', text: 'Got my loan approved in just 3 minutes! The AI chatbot made the entire process so smooth.', avatar: 'RS' },
    { name: 'Priya Patel', role: 'IT Professional', text: 'Best loan experience ever. No paperwork, no branch visits. Everything done from my phone!', avatar: 'PP' },
    { name: 'Amit Kumar', role: 'Doctor', text: 'The instant sanction letter feature is amazing. I could download it immediately after approval.', avatar: 'AK' },
  ];

  return (
    <div className="landing-page-v2">
      {/* Navigation */}
      <AppBar position="fixed" className={`navbar ${scrolled ? 'scrolled' : ''}`} elevation={scrolled ? 4 : 0}>
        <Toolbar>
          <Box className="logo" onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}>
            <AccountBalanceIcon className="logo-icon" />
            <Typography variant="h6" className="logo-text">Tata Capital</Typography>
          </Box>
          <Box className="nav-links">
            <Button color="inherit" onClick={() => document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' })}>Features</Button>
            <Button color="inherit" onClick={() => document.getElementById('calculator')?.scrollIntoView({ behavior: 'smooth' })}>Calculator</Button>
            <Button color="inherit" onClick={() => document.getElementById('how-it-works')?.scrollIntoView({ behavior: 'smooth' })}>How It Works</Button>
            <Button color="inherit" startIcon={<HistoryIcon />} onClick={onViewHistory}>History</Button>
            <Button variant="contained" className="nav-cta" startIcon={<ChatIcon />} onClick={onGetStarted}>Apply Now</Button>
          </Box>
          <IconButton className="menu-btn" onClick={() => setDrawerOpen(true)}><MenuIcon /></IconButton>
        </Toolbar>
      </AppBar>

      {/* Mobile Drawer */}
      <Drawer anchor="right" open={drawerOpen} onClose={() => setDrawerOpen(false)}>
        <Box className="drawer-content">
          <Box className="drawer-header">
            <AccountBalanceIcon /> <Typography variant="h6">Tata Capital</Typography>
          </Box>
          <Divider />
          <List>
            <ListItem component="div" onClick={() => { onGetStarted(); setDrawerOpen(false); }} sx={{ cursor: 'pointer', '&:hover': { bgcolor: 'action.hover' } }}>
              <ListItemIcon><ChatIcon /></ListItemIcon>
              <ListItemText primary="Apply for Loan" secondary="Start AI-assisted application" />
            </ListItem>
            <ListItem component="div" onClick={() => { onViewHistory(); setDrawerOpen(false); }} sx={{ cursor: 'pointer', '&:hover': { bgcolor: 'action.hover' } }}>
              <ListItemIcon><HistoryIcon /></ListItemIcon>
              <ListItemText primary="Application History" secondary="View past applications" />
            </ListItem>
            <Divider />
            <ListItem component="div" onClick={() => { document.getElementById('calculator')?.scrollIntoView({ behavior: 'smooth' }); setDrawerOpen(false); }} sx={{ cursor: 'pointer', '&:hover': { bgcolor: 'action.hover' } }}>
              <ListItemIcon><CalculateIcon /></ListItemIcon>
              <ListItemText primary="EMI Calculator" />
            </ListItem>
            <ListItem component="div" onClick={() => { document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' }); setDrawerOpen(false); }} sx={{ cursor: 'pointer', '&:hover': { bgcolor: 'action.hover' } }}>
              <ListItemIcon><StarIcon /></ListItemIcon>
              <ListItemText primary="Features" />
            </ListItem>
          </List>
        </Box>
      </Drawer>

      {/* Hero Section */}
      <Box className="hero-section-v2">
        <div className="hero-bg-shapes">
          <div className="shape shape-1"></div>
          <div className="shape shape-2"></div>
          <div className="shape shape-3"></div>
        </div>
        <Container maxWidth="lg">
          <Grid container spacing={6} alignItems="center">
            <Grid size={{ xs: 12, md: 6 }}>
              <Chip label="🎉 Instant Digital Loans" className="hero-chip" />
              <Typography variant="h1" className="hero-title-v2">
                Get Personal Loans <span className="gradient-text">Instantly</span> with AI
              </Typography>
              <Typography variant="h6" className="hero-subtitle-v2">
                Experience the future of lending. Our AI-powered chatbot processes your loan application in minutes, not days. No paperwork, no branch visits.
              </Typography>
              <Box className="hero-cta-group">
                <Button variant="contained" size="large" className="hero-btn-primary" startIcon={<PlayArrowIcon />} onClick={onGetStarted}>
                  Start Application
                </Button>
                <Button variant="outlined" size="large" className="hero-btn-secondary" startIcon={<CalculateIcon />} onClick={() => document.getElementById('calculator')?.scrollIntoView({ behavior: 'smooth' })}>
                  Calculate EMI
                </Button>
              </Box>
              <Box className="hero-trust-badges">
                <div className="trust-item"><CheckCircleIcon /> No Hidden Charges</div>
                <div className="trust-item"><CheckCircleIcon /> 100% Digital Process</div>
                <div className="trust-item"><CheckCircleIcon /> Secure & Private</div>
              </Box>
            </Grid>
            <Grid size={{ xs: 12, md: 6 }}>
              <Box className="hero-visual">
                <Paper className="chat-demo-card" elevation={8}>
                  <div className="chat-demo-header">
                    <Avatar className="bot-avatar"><SupportAgentIcon /></Avatar>
                    <div>
                      <Typography variant="subtitle1">AI Loan Assistant</Typography>
                      <Typography variant="caption" className="online-status">● Online</Typography>
                    </div>
                  </div>
                  <div className="chat-demo-body">
                    <div className="demo-message bot">
                      <Typography>Hello! 👋 I'm your AI loan assistant. I can help you get a personal loan approved in just 5 minutes!</Typography>
                    </div>
                    <div className="demo-message user">
                      <Typography>I need a loan of ₹5 lakhs</Typography>
                    </div>
                    <div className="demo-message bot">
                      <Typography>Great choice! Let me check your eligibility... ✨</Typography>
                      <Box className="typing-indicator">
                        <span></span><span></span><span></span>
                      </Box>
                    </div>
                  </div>
                  <Button fullWidth variant="contained" className="chat-demo-btn" onClick={onGetStarted}>
                    Try It Now <ArrowForwardIcon />
                  </Button>
                </Paper>
                <div className="floating-card card-1">
                  <CheckCircleIcon className="float-icon success" />
                  <Typography variant="body2">Loan Approved!</Typography>
                </div>
                <div className="floating-card card-2">
                  <CurrencyRupeeIcon className="float-icon" />
                  <Typography variant="body2">₹5,00,000</Typography>
                </div>
              </Box>
            </Grid>
          </Grid>
        </Container>
      </Box>

      {/* Stats Section */}
      <Box className="stats-section">
        <Container maxWidth="lg">
          <Grid container spacing={3}>
            {stats.map((stat, i) => (
              <Grid size={{ xs: 6, md: 3 }} key={i}>
                <Box className="stat-card-v2">
                  <div className="stat-icon">{stat.icon}</div>
                  <Typography variant="h3" className="stat-value">{stat.value}</Typography>
                  <Typography variant="body2" className="stat-label">{stat.label}</Typography>
                </Box>
              </Grid>
            ))}
          </Grid>
        </Container>
      </Box>

      {/* Features Section */}
      <Box className="features-section-v2" id="features">
        <Container maxWidth="lg">
          <Box className="section-header">
            <Chip label="Why Choose Us" className="section-chip" />
            <Typography variant="h2" className="section-title-v2">Powerful Features for Modern Banking</Typography>
            <Typography variant="body1" className="section-subtitle">Everything you need for a seamless loan experience</Typography>
          </Box>
          <Grid container spacing={4}>
            {features.map((feature, i) => (
              <Grid size={{ xs: 12, sm: 6, md: 4 }} key={i}>
                <Card className="feature-card-v2" elevation={0}>
                  <CardContent>
                    <Box className="feature-icon-v2" style={{ background: `${feature.color}15`, color: feature.color }}>
                      {feature.icon}
                    </Box>
                    <Typography variant="h6" className="feature-title-v2">{feature.title}</Typography>
                    <Typography variant="body2" className="feature-desc-v2">{feature.desc}</Typography>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Container>
      </Box>

      {/* EMI Calculator Section */}
      <Box className="calculator-section" id="calculator">
        <Container maxWidth="lg">
          <Grid container spacing={6} alignItems="center">
            <Grid size={{ xs: 12, md: 5 }}>
              <Chip label="EMI Calculator" className="section-chip" />
              <Typography variant="h2" className="section-title-v2">Plan Your Loan Smartly</Typography>
              <Typography variant="body1" className="section-subtitle">Use our calculator to estimate your monthly payments and plan your finances better.</Typography>
            </Grid>
            <Grid size={{ xs: 12, md: 7 }}>
              <Paper className="calculator-card" elevation={4}>
                <Box className="calc-input-group">
                  <Box className="calc-label">
                    <CurrencyRupeeIcon /> Loan Amount
                    <Typography variant="h5" className="calc-value">₹{loanAmount.toLocaleString()}</Typography>
                  </Box>
                  <input type="range" min="50000" max="5000000" step="10000" value={loanAmount} onChange={(e) => setLoanAmount(Number(e.target.value))} className="calc-slider" />
                  <Box className="calc-range"><span>₹50K</span><span>₹50L</span></Box>
                </Box>
                <Box className="calc-input-group">
                  <Box className="calc-label">
                    <CalendarMonthIcon /> Tenure (Months)
                    <Typography variant="h5" className="calc-value">{tenure} months</Typography>
                  </Box>
                  <input type="range" min="6" max="84" step="6" value={tenure} onChange={(e) => setTenure(Number(e.target.value))} className="calc-slider" />
                  <Box className="calc-range"><span>6 months</span><span>84 months</span></Box>
                </Box>
                <Divider className="calc-divider" />
                <Grid container spacing={2} className="calc-results">
                  <Grid size={{ xs: 4 }}>
                    <Typography variant="caption">Monthly EMI</Typography>
                    <Typography variant="h5" className="emi-value">₹{emi.toLocaleString()}</Typography>
                  </Grid>
                  <Grid size={{ xs: 4 }}>
                    <Typography variant="caption">Total Interest</Typography>
                    <Typography variant="h6">₹{totalInterest.toLocaleString()}</Typography>
                  </Grid>
                  <Grid size={{ xs: 4 }}>
                    <Typography variant="caption">Total Payable</Typography>
                    <Typography variant="h6">₹{totalPayable.toLocaleString()}</Typography>
                  </Grid>
                </Grid>
                <Button fullWidth variant="contained" size="large" className="calc-apply-btn" onClick={onGetStarted}>
                  Apply for ₹{loanAmount.toLocaleString()} <ArrowForwardIcon />
                </Button>
              </Paper>
            </Grid>
          </Grid>
        </Container>
      </Box>

      {/* How It Works */}
      <Box className="how-it-works-v2" id="how-it-works">
        <Container maxWidth="lg">
          <Box className="section-header">
            <Chip label="Simple Process" className="section-chip" />
            <Typography variant="h2" className="section-title-v2">Get Your Loan in 4 Easy Steps</Typography>
          </Box>
          <Box className="steps-container">
            {steps.map((step, i) => (
              <Box className="step-card-v2" key={i}>
                <div className="step-number-v2">{step.num}</div>
                <Typography variant="h6" className="step-title-v2">{step.title}</Typography>
                <Typography variant="body2" className="step-desc-v2">{step.desc}</Typography>
                {i < steps.length - 1 && <div className="step-connector"></div>}
              </Box>
            ))}
          </Box>
        </Container>
      </Box>

      {/* Testimonials */}
      <Box className="testimonials-section">
        <Container maxWidth="lg">
          <Box className="section-header">
            <Chip label="Testimonials" className="section-chip" />
            <Typography variant="h2" className="section-title-v2">What Our Customers Say</Typography>
          </Box>
          <Grid container spacing={4}>
            {testimonials.map((t, i) => (
              <Grid size={{ xs: 12, md: 4 }} key={i}>
                <Card className="testimonial-card" elevation={2}>
                  <CardContent>
                    <Box className="testimonial-stars">{'★'.repeat(5)}</Box>
                    <Typography variant="body1" className="testimonial-text">"{t.text}"</Typography>
                    <Box className="testimonial-author">
                      <Avatar className="testimonial-avatar">{t.avatar}</Avatar>
                      <Box>
                        <Typography variant="subtitle2">{t.name}</Typography>
                        <Typography variant="caption">{t.role}</Typography>
                      </Box>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Container>
      </Box>

      {/* CTA Section */}
      <Box className="cta-section-v2">
        <Container maxWidth="md">
          <Typography variant="h3" className="cta-title">Ready to Get Your Loan?</Typography>
          <Typography variant="body1" className="cta-subtitle">Join thousands of happy customers who got their loans approved instantly</Typography>
          <Box className="cta-buttons">
            <Button variant="contained" size="large" className="cta-btn-primary" startIcon={<ChatIcon />} onClick={onGetStarted}>
              Start Application Now
            </Button>
            <Button variant="outlined" size="large" className="cta-btn-secondary" startIcon={<HistoryIcon />} onClick={onViewHistory}>
              View My Applications
            </Button>
          </Box>
        </Container>
      </Box>

      {/* Footer */}
      <Box className="footer-v2">
        <Container maxWidth="lg">
          <Grid container spacing={4}>
            <Grid size={{ xs: 12, md: 4 }}>
              <Box className="footer-brand">
                <AccountBalanceIcon /> <Typography variant="h6">Tata Capital</Typography>
              </Box>
              <Typography variant="body2" className="footer-desc">
                India's leading NBFC providing instant personal loans through AI-powered digital platform.
              </Typography>
            </Grid>
            <Grid size={{ xs: 6, md: 2 }}>
              <Typography variant="subtitle2" className="footer-heading">Quick Links</Typography>
              <Typography variant="body2" className="footer-link" onClick={onGetStarted}>Apply for Loan</Typography>
              <Typography variant="body2" className="footer-link" onClick={onViewHistory}>My Applications</Typography>
              <Typography variant="body2" className="footer-link">EMI Calculator</Typography>
            </Grid>
            <Grid size={{ xs: 6, md: 2 }}>
              <Typography variant="subtitle2" className="footer-heading">Support</Typography>
              <Typography variant="body2" className="footer-link">Help Center</Typography>
              <Typography variant="body2" className="footer-link">FAQs</Typography>
              <Typography variant="body2" className="footer-link">Contact Us</Typography>
            </Grid>
            <Grid size={{ xs: 12, md: 4 }}>
              <Typography variant="subtitle2" className="footer-heading">Contact</Typography>
              <Typography variant="body2">📞 1800-209-8800 (Toll Free)</Typography>
              <Typography variant="body2">✉️ support@tatacapital.com</Typography>
              <Typography variant="body2">🏢 Mumbai, Maharashtra, India</Typography>
            </Grid>
          </Grid>
          <Divider className="footer-divider" />
          <Typography variant="body2" className="copyright-v2">
            © 2024 Tata Capital Limited. All rights reserved. | This is a demo application.
          </Typography>
        </Container>
      </Box>
    </div>
  );
};

export default LandingPage;
