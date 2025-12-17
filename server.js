/**
 * Combined Server for Render Deployment
 * Runs Mock APIs + serves as a proxy info endpoint
 * This allows single-service deployment
 */

const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 5000;

// Middleware
app.use(cors());
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

// Serve static frontend files if they exist
app.use(express.static(path.join(__dirname, 'frontend/build')));

// ============== MOCK APIs ==============

// Customer Data
const customerData = {
    'CUST001': { id: 'CUST001', name: 'Rajesh Kumar', age: 32, city: 'Mumbai', phone: '+91-9876543210', salary: 85000, kycStatus: 'verified' },
    'CUST002': { id: 'CUST002', name: 'Priya Sharma', age: 28, city: 'Delhi', phone: '+91-9876543211', salary: 120000, kycStatus: 'verified' },
    'CUST003': { id: 'CUST003', name: 'Amit Patel', age: 35, city: 'Bangalore', phone: '+91-9876543212', salary: 65000, kycStatus: 'pending' },
};

// Credit Score Data
const creditScoreData = {
    'CUST001': { userId: 'CUST001', creditScore: 785, scoreRange: 'Excellent' },
    'CUST002': { userId: 'CUST002', creditScore: 820, scoreRange: 'Excellent' },
    'CUST003': { userId: 'CUST003', creditScore: 650, scoreRange: 'Fair' },
};

// Offer Data
const offerData = {
    'CUST001': { userId: 'CUST001', preApprovedLimit: 500000, interestRate: 12.5 },
    'CUST002': { userId: 'CUST002', preApprovedLimit: 800000, interestRate: 11.2 },
    'CUST003': { userId: 'CUST003', preApprovedLimit: 200000, interestRate: 15.8 },
};

// Root endpoint
app.get('/', (req, res) => {
    res.json({
        status: 'running',
        service: 'AI Loan Chatbot - Combined Server',
        endpoints: {
            health: '/health',
            crm: '/crm/:userId',
            creditScore: '/credit-score/:userId',
            offers: '/offers/:userId'
        }
    });
});

// Health check
app.get('/health', (req, res) => {
    res.json({ status: 'healthy', service: 'combined-server', timestamp: new Date().toISOString() });
});

// CRM API
app.get('/crm/:userId', (req, res) => {
    const { userId } = req.params;
    const customer = customerData[userId];
    if (customer) {
        res.json({ success: true, data: customer });
    } else {
        res.json({ success: true, data: { id: userId, name: 'Guest User', kycStatus: 'pending' } });
    }
});

// Credit Score API
app.get('/credit-score/:userId', (req, res) => {
    const { userId } = req.params;
    const creditData = creditScoreData[userId];
    if (creditData) {
        res.json({ success: true, creditScore: creditData.creditScore, data: creditData });
    } else {
        const randomScore = Math.floor(Math.random() * 150) + 700;
        res.json({ success: true, creditScore: randomScore, data: { userId, creditScore: randomScore, scoreRange: 'Good' } });
    }
});

// Offers API
app.get('/offers/:userId', (req, res) => {
    const { userId } = req.params;
    const offers = offerData[userId];
    if (offers) {
        res.json({ success: true, preApprovedLimit: offers.preApprovedLimit, interestRate: offers.interestRate, data: offers });
    } else {
        res.json({ success: true, preApprovedLimit: 500000, interestRate: 12.5, data: { userId, preApprovedLimit: 500000, interestRate: 12.5 } });
    }
});

// Catch-all for frontend routing (SPA)
app.get('*', (req, res) => {
    const indexPath = path.join(__dirname, 'frontend/build', 'index.html');
    res.sendFile(indexPath, (err) => {
        if (err) {
            res.json({ error: 'Frontend not built. This is the API server.', endpoints: { health: '/health', crm: '/crm/:userId' } });
        }
    });
});

// Start server
app.listen(PORT, '0.0.0.0', () => {
    console.log(`Combined Server running on port ${PORT}`);
    console.log(`Health check: http://localhost:${PORT}/health`);
});
