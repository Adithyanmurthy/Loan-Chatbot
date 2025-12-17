/**
 * AI Loan Chatbot - Combined Server
 * Runs everything in ONE service: Mock APIs + Backend Proxy + Frontend
 */

const express = require('express');
const cors = require('cors');
const path = require('path');
const { spawn } = require('child_process');

const app = express();
const PORT = process.env.PORT || 10000;

// Middleware
app.use(cors());
app.use(express.json());

// ============== MOCK APIs ==============

const customerData = {
    'CUST001': { id: 'CUST001', name: 'Rajesh Kumar', age: 32, city: 'Mumbai', phone: '+91-9876543210', salary: 85000, kycStatus: 'verified' },
    'CUST002': { id: 'CUST002', name: 'Priya Sharma', age: 28, city: 'Delhi', phone: '+91-9876543211', salary: 120000, kycStatus: 'verified' },
};

const creditScoreData = {
    'CUST001': { userId: 'CUST001', creditScore: 785, scoreRange: 'Excellent' },
    'CUST002': { userId: 'CUST002', creditScore: 820, scoreRange: 'Excellent' },
};

const offerData = {
    'CUST001': { userId: 'CUST001', preApprovedLimit: 500000, interestRate: 12.5 },
    'CUST002': { userId: 'CUST002', preApprovedLimit: 800000, interestRate: 11.2 },
};

// Health check
app.get('/health', (req, res) => {
    res.json({ status: 'healthy', service: 'ai-loan-chatbot' });
});

// Root
app.get('/', (req, res) => {
    res.json({
        status: 'running',
        service: 'AI Loan Chatbot - All-in-One Server',
        message: 'Backend is running. Frontend should be deployed separately as static site.',
        endpoints: { health: '/health', crm: '/crm/:userId', creditScore: '/credit-score/:userId', offers: '/offers/:userId' }
    });
});

// CRM API
app.get('/crm/:userId', (req, res) => {
    const customer = customerData[req.params.userId];
    res.json({ success: true, data: customer || { id: req.params.userId, name: 'Guest', kycStatus: 'pending' } });
});

// Credit Score API
app.get('/credit-score/:userId', (req, res) => {
    const data = creditScoreData[req.params.userId];
    const score = data?.creditScore || Math.floor(Math.random() * 150) + 700;
    res.json({ success: true, creditScore: score, data: data || { userId: req.params.userId, creditScore: score } });
});

// Offers API
app.get('/offers/:userId', (req, res) => {
    const data = offerData[req.params.userId];
    res.json({ success: true, preApprovedLimit: data?.preApprovedLimit || 500000, interestRate: data?.interestRate || 12.5, data: data || { preApprovedLimit: 500000, interestRate: 12.5 } });
});

// Start server
app.listen(PORT, '0.0.0.0', () => {
    console.log(`AI Loan Chatbot Server running on port ${PORT}`);
});
