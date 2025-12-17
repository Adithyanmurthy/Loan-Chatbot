const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');
const { v4: uuidv4 } = require('uuid');

const app = express();

// Middleware
app.use(cors());
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

// Security headers
app.use((req, res, next) => {
    res.header('X-Content-Type-Options', 'nosniff');
    res.header('X-Frame-Options', 'DENY');
    res.header('X-XSS-Protection', '1; mode=block');
    next();
});

// Health check
app.get('/health', (req, res) => {
    res.json({ status: 'healthy', service: 'mock-apis-server' });
});

// CRM API Mock (Port 3001)
const crmPort = process.env.CRM_PORT || 3001;
const crmApp = express();
crmApp.use(cors());
crmApp.use(bodyParser.json());

crmApp.get('/health', (req, res) => {
    res.json({ status: 'healthy', service: 'crm-api-mock' });
});

// Synthetic customer data for testing (10+ profiles)
const customerData = {
    'CUST001': {
        id: 'CUST001',
        name: 'Rajesh Kumar',
        age: 32,
        city: 'Mumbai',
        phone: '+91-9876543210',
        address: '123 Marine Drive, Mumbai, Maharashtra 400001',
        employmentType: 'Salaried',
        company: 'Tech Solutions Pvt Ltd',
        salary: 85000,
        kycStatus: 'verified',
        lastUpdated: '2024-01-15'
    },
    'CUST002': {
        id: 'CUST002',
        name: 'Priya Sharma',
        age: 28,
        city: 'Delhi',
        phone: '+91-9876543211',
        address: '456 Connaught Place, New Delhi, Delhi 110001',
        employmentType: 'Salaried',
        company: 'Financial Services Ltd',
        salary: 120000,
        kycStatus: 'verified',
        lastUpdated: '2024-01-20'
    },
    'CUST003': {
        id: 'CUST003',
        name: 'Amit Patel',
        age: 35,
        city: 'Bangalore',
        phone: '+91-9876543212',
        address: '789 MG Road, Bangalore, Karnataka 560001',
        employmentType: 'Self-Employed',
        company: 'Patel Enterprises',
        salary: 65000,
        kycStatus: 'pending',
        lastUpdated: '2024-01-10'
    },
    'CUST004': {
        id: 'CUST004',
        name: 'Sneha Reddy',
        age: 30,
        city: 'Hyderabad',
        phone: '+91-9876543213',
        address: '321 Banjara Hills, Hyderabad, Telangana 500034',
        employmentType: 'Salaried',
        company: 'IT Corporation',
        salary: 95000,
        kycStatus: 'verified',
        lastUpdated: '2024-01-25'
    },
    'CUST005': {
        id: 'CUST005',
        name: 'Vikram Singh',
        age: 40,
        city: 'Pune',
        phone: '+91-9876543214',
        address: '654 FC Road, Pune, Maharashtra 411005',
        employmentType: 'Salaried',
        company: 'Manufacturing Corp',
        salary: 75000,
        kycStatus: 'verified',
        lastUpdated: '2024-01-18'
    },
    'CUST006': {
        id: 'CUST006',
        name: 'Kavya Nair',
        age: 26,
        city: 'Chennai',
        phone: '+91-9876543215',
        address: '987 Anna Salai, Chennai, Tamil Nadu 600002',
        employmentType: 'Salaried',
        company: 'Software Solutions',
        salary: 55000,
        kycStatus: 'verified',
        lastUpdated: '2024-01-22'
    },
    'CUST007': {
        id: 'CUST007',
        name: 'Rohit Gupta',
        age: 33,
        city: 'Kolkata',
        phone: '+91-9876543216',
        address: '147 Park Street, Kolkata, West Bengal 700016',
        employmentType: 'Self-Employed',
        company: 'Gupta Trading Co',
        salary: 45000,
        kycStatus: 'incomplete',
        lastUpdated: '2024-01-12'
    },
    'CUST008': {
        id: 'CUST008',
        name: 'Anita Joshi',
        age: 29,
        city: 'Jaipur',
        phone: '+91-9876543217',
        address: '258 MI Road, Jaipur, Rajasthan 302001',
        employmentType: 'Salaried',
        company: 'Government Office',
        salary: 68000,
        kycStatus: 'verified',
        lastUpdated: '2024-01-28'
    },
    'CUST009': {
        id: 'CUST009',
        name: 'Suresh Iyer',
        age: 45,
        city: 'Kochi',
        phone: '+91-9876543218',
        address: '369 MG Road, Kochi, Kerala 682016',
        employmentType: 'Salaried',
        company: 'Marine Industries',
        salary: 110000,
        kycStatus: 'verified',
        lastUpdated: '2024-01-30'
    },
    'CUST010': {
        id: 'CUST010',
        name: 'Deepika Agarwal',
        age: 31,
        city: 'Ahmedabad',
        phone: '+91-9876543219',
        address: '741 CG Road, Ahmedabad, Gujarat 380009',
        employmentType: 'Self-Employed',
        company: 'Textile Business',
        salary: 80000,
        kycStatus: 'verified',
        lastUpdated: '2024-01-26'
    },
    'CUST011': {
        id: 'CUST011',
        name: 'Manoj Tiwari',
        age: 38,
        city: 'Lucknow',
        phone: '+91-9876543220',
        address: '852 Hazratganj, Lucknow, Uttar Pradesh 226001',
        employmentType: 'Salaried',
        company: 'Educational Institute',
        salary: 52000,
        kycStatus: 'pending',
        lastUpdated: '2024-01-14'
    },
    'CUST012': {
        id: 'CUST012',
        name: 'Ritu Malhotra',
        age: 27,
        city: 'Chandigarh',
        phone: '+91-9876543221',
        address: '963 Sector 17, Chandigarh 160017',
        employmentType: 'Salaried',
        company: 'Healthcare Services',
        salary: 72000,
        kycStatus: 'verified',
        lastUpdated: '2024-01-24'
    }
};

// Error simulation flags
let simulateErrors = {
    timeout: false,
    serverError: false,
    notFound: false
};

// Error simulation control endpoint
crmApp.post('/simulate-error', (req, res) => {
    const { errorType, enabled } = req.body;
    if (simulateErrors.hasOwnProperty(errorType)) {
        simulateErrors[errorType] = enabled;
        res.json({ message: `Error simulation ${errorType} ${enabled ? 'enabled' : 'disabled'}` });
    } else {
        res.status(400).json({ error: 'Invalid error type' });
    }
});

crmApp.get('/crm/:userId', (req, res) => {
    const { userId } = req.params;
    
    // Simulate timeout error
    if (simulateErrors.timeout) {
        return setTimeout(() => {
            res.status(408).json({ error: 'Request timeout' });
        }, 5000);
    }
    
    // Simulate server error
    if (simulateErrors.serverError) {
        return res.status(500).json({ error: 'Internal server error' });
    }
    
    // Simulate not found error
    if (simulateErrors.notFound) {
        return res.status(404).json({ error: 'Customer not found' });
    }
    
    // Return customer data if exists
    const customer = customerData[userId];
    if (customer) {
        res.json({
            success: true,
            data: customer,
            timestamp: new Date().toISOString()
        });
    } else {
        res.status(404).json({
            success: false,
            error: 'Customer not found',
            timestamp: new Date().toISOString()
        });
    }
});

// Credit Bureau API Mock (Port 3002)
const creditPort = process.env.CREDIT_PORT || 3002;
const creditApp = express();
creditApp.use(cors());
creditApp.use(bodyParser.json());

creditApp.get('/health', (req, res) => {
    res.json({ status: 'healthy', service: 'credit-bureau-api-mock' });
});

// Credit score data with realistic distribution (0-900 scale)
const creditScoreData = {
    'CUST001': {
        userId: 'CUST001',
        creditScore: 785,
        scoreRange: 'Excellent',
        reportDate: '2024-01-15',
        bureau: 'CIBIL',
        factors: {
            paymentHistory: 'Good',
            creditUtilization: '25%',
            creditAge: '8 years',
            creditMix: 'Good',
            newCredit: 'Low'
        }
    },
    'CUST002': {
        userId: 'CUST002',
        creditScore: 820,
        scoreRange: 'Excellent',
        reportDate: '2024-01-20',
        bureau: 'CIBIL',
        factors: {
            paymentHistory: 'Excellent',
            creditUtilization: '15%',
            creditAge: '10 years',
            creditMix: 'Excellent',
            newCredit: 'Low'
        }
    },
    'CUST003': {
        userId: 'CUST003',
        creditScore: 650,
        scoreRange: 'Fair',
        reportDate: '2024-01-10',
        bureau: 'CIBIL',
        factors: {
            paymentHistory: 'Fair',
            creditUtilization: '45%',
            creditAge: '5 years',
            creditMix: 'Fair',
            newCredit: 'Medium'
        }
    },
    'CUST004': {
        userId: 'CUST004',
        creditScore: 750,
        scoreRange: 'Good',
        reportDate: '2024-01-25',
        bureau: 'CIBIL',
        factors: {
            paymentHistory: 'Good',
            creditUtilization: '30%',
            creditAge: '7 years',
            creditMix: 'Good',
            newCredit: 'Low'
        }
    },
    'CUST005': {
        userId: 'CUST005',
        creditScore: 720,
        scoreRange: 'Good',
        reportDate: '2024-01-18',
        bureau: 'CIBIL',
        factors: {
            paymentHistory: 'Good',
            creditUtilization: '35%',
            creditAge: '12 years',
            creditMix: 'Good',
            newCredit: 'Low'
        }
    },
    'CUST006': {
        userId: 'CUST006',
        creditScore: 680,
        scoreRange: 'Fair',
        reportDate: '2024-01-22',
        bureau: 'CIBIL',
        factors: {
            paymentHistory: 'Fair',
            creditUtilization: '40%',
            creditAge: '4 years',
            creditMix: 'Fair',
            newCredit: 'Medium'
        }
    },
    'CUST007': {
        userId: 'CUST007',
        creditScore: 590,
        scoreRange: 'Poor',
        reportDate: '2024-01-12',
        bureau: 'CIBIL',
        factors: {
            paymentHistory: 'Poor',
            creditUtilization: '65%',
            creditAge: '3 years',
            creditMix: 'Poor',
            newCredit: 'High'
        }
    },
    'CUST008': {
        userId: 'CUST008',
        creditScore: 710,
        scoreRange: 'Good',
        reportDate: '2024-01-28',
        bureau: 'CIBIL',
        factors: {
            paymentHistory: 'Good',
            creditUtilization: '28%',
            creditAge: '6 years',
            creditMix: 'Good',
            newCredit: 'Low'
        }
    },
    'CUST009': {
        userId: 'CUST009',
        creditScore: 800,
        scoreRange: 'Excellent',
        reportDate: '2024-01-30',
        bureau: 'CIBIL',
        factors: {
            paymentHistory: 'Excellent',
            creditUtilization: '18%',
            creditAge: '15 years',
            creditMix: 'Excellent',
            newCredit: 'Low'
        }
    },
    'CUST010': {
        userId: 'CUST010',
        creditScore: 730,
        scoreRange: 'Good',
        reportDate: '2024-01-26',
        bureau: 'CIBIL',
        factors: {
            paymentHistory: 'Good',
            creditUtilization: '32%',
            creditAge: '9 years',
            creditMix: 'Good',
            newCredit: 'Low'
        }
    },
    'CUST011': {
        userId: 'CUST011',
        creditScore: 620,
        scoreRange: 'Fair',
        reportDate: '2024-01-14',
        bureau: 'CIBIL',
        factors: {
            paymentHistory: 'Fair',
            creditUtilization: '50%',
            creditAge: '4 years',
            creditMix: 'Fair',
            newCredit: 'Medium'
        }
    },
    'CUST012': {
        userId: 'CUST012',
        creditScore: 760,
        scoreRange: 'Good',
        reportDate: '2024-01-24',
        bureau: 'CIBIL',
        factors: {
            paymentHistory: 'Good',
            creditUtilization: '22%',
            creditAge: '5 years',
            creditMix: 'Good',
            newCredit: 'Low'
        }
    }
};

// Credit Bureau error simulation flags
let creditSimulateErrors = {
    timeout: false,
    serverError: false,
    notFound: false,
    serviceUnavailable: false
};

// Error simulation control endpoint for Credit Bureau
creditApp.post('/simulate-error', (req, res) => {
    const { errorType, enabled } = req.body;
    if (creditSimulateErrors.hasOwnProperty(errorType)) {
        creditSimulateErrors[errorType] = enabled;
        res.json({ message: `Credit Bureau error simulation ${errorType} ${enabled ? 'enabled' : 'disabled'}` });
    } else {
        res.status(400).json({ error: 'Invalid error type' });
    }
});

creditApp.get('/credit-score/:userId', (req, res) => {
    const { userId } = req.params;
    
    // Simulate timeout error (longer delay)
    if (creditSimulateErrors.timeout) {
        return setTimeout(() => {
            res.status(408).json({ error: 'Credit bureau request timeout' });
        }, 8000);
    }
    
    // Simulate service unavailable
    if (creditSimulateErrors.serviceUnavailable) {
        return res.status(503).json({ error: 'Credit bureau service temporarily unavailable' });
    }
    
    // Simulate server error
    if (creditSimulateErrors.serverError) {
        return res.status(500).json({ error: 'Credit bureau internal server error' });
    }
    
    // Simulate not found error
    if (creditSimulateErrors.notFound) {
        return res.status(404).json({ error: 'Credit record not found' });
    }
    
    // Return credit score data if exists
    const creditData = creditScoreData[userId];
    if (creditData) {
        res.json({
            success: true,
            data: creditData,
            timestamp: new Date().toISOString(),
            processingTime: Math.floor(Math.random() * 3000) + 1000 // 1-4 seconds
        });
    } else {
        res.status(404).json({
            success: false,
            error: 'Credit record not found for user',
            timestamp: new Date().toISOString()
        });
    }
});

// Offer Mart API Mock (Port 3003)
const offerPort = process.env.OFFER_PORT || 3003;
const offerApp = express();
offerApp.use(cors());
offerApp.use(bodyParser.json());

offerApp.get('/health', (req, res) => {
    res.json({ status: 'healthy', service: 'offer-mart-api-mock' });
});

// Pre-approved loan offers with varied amounts and interest rates
const offerData = {
    'CUST001': {
        userId: 'CUST001',
        preApprovedLimit: 500000,
        interestRate: 12.5,
        tenure: [12, 24, 36, 48, 60],
        offerType: 'Premium',
        validUntil: '2024-06-30',
        specialOffers: [
            {
                amount: 300000,
                rate: 11.8,
                processingFee: 0,
                description: 'Special rate for existing customers'
            }
        ]
    },
    'CUST002': {
        userId: 'CUST002',
        preApprovedLimit: 800000,
        interestRate: 11.2,
        tenure: [12, 24, 36, 48, 60, 72],
        offerType: 'Premium Plus',
        validUntil: '2024-07-15',
        specialOffers: [
            {
                amount: 600000,
                rate: 10.9,
                processingFee: 0,
                description: 'Exclusive rate for high-value customers'
            }
        ]
    },
    'CUST003': {
        userId: 'CUST003',
        preApprovedLimit: 200000,
        interestRate: 15.8,
        tenure: [12, 24, 36],
        offerType: 'Standard',
        validUntil: '2024-05-20',
        specialOffers: []
    },
    'CUST004': {
        userId: 'CUST004',
        preApprovedLimit: 600000,
        interestRate: 13.2,
        tenure: [12, 24, 36, 48, 60],
        offerType: 'Premium',
        validUntil: '2024-06-25',
        specialOffers: [
            {
                amount: 400000,
                rate: 12.8,
                processingFee: 2500,
                description: 'Reduced processing fee offer'
            }
        ]
    },
    'CUST005': {
        userId: 'CUST005',
        preApprovedLimit: 400000,
        interestRate: 14.1,
        tenure: [12, 24, 36, 48],
        offerType: 'Standard Plus',
        validUntil: '2024-06-10',
        specialOffers: []
    },
    'CUST006': {
        userId: 'CUST006',
        preApprovedLimit: 250000,
        interestRate: 16.5,
        tenure: [12, 24, 36],
        offerType: 'Standard',
        validUntil: '2024-05-30',
        specialOffers: []
    },
    'CUST007': {
        userId: 'CUST007',
        preApprovedLimit: 150000,
        interestRate: 18.2,
        tenure: [12, 24],
        offerType: 'Basic',
        validUntil: '2024-04-15',
        specialOffers: []
    },
    'CUST008': {
        userId: 'CUST008',
        preApprovedLimit: 350000,
        interestRate: 13.8,
        tenure: [12, 24, 36, 48],
        offerType: 'Government Employee',
        validUntil: '2024-07-31',
        specialOffers: [
            {
                amount: 300000,
                rate: 13.2,
                processingFee: 1000,
                description: 'Government employee special rate'
            }
        ]
    },
    'CUST009': {
        userId: 'CUST009',
        preApprovedLimit: 750000,
        interestRate: 11.8,
        tenure: [12, 24, 36, 48, 60, 72],
        offerType: 'Premium Plus',
        validUntil: '2024-08-15',
        specialOffers: [
            {
                amount: 500000,
                rate: 11.2,
                processingFee: 0,
                description: 'Long-term customer loyalty rate'
            }
        ]
    },
    'CUST010': {
        userId: 'CUST010',
        preApprovedLimit: 450000,
        interestRate: 14.5,
        tenure: [12, 24, 36, 48],
        offerType: 'Business Owner',
        validUntil: '2024-06-20',
        specialOffers: [
            {
                amount: 350000,
                rate: 14.0,
                processingFee: 3000,
                description: 'Business expansion loan'
            }
        ]
    },
    'CUST011': {
        userId: 'CUST011',
        preApprovedLimit: 180000,
        interestRate: 17.2,
        tenure: [12, 24, 36],
        offerType: 'Standard',
        validUntil: '2024-05-10',
        specialOffers: []
    },
    'CUST012': {
        userId: 'CUST012',
        preApprovedLimit: 380000,
        interestRate: 13.5,
        tenure: [12, 24, 36, 48],
        offerType: 'Healthcare Professional',
        validUntil: '2024-07-05',
        specialOffers: [
            {
                amount: 300000,
                rate: 12.9,
                processingFee: 1500,
                description: 'Healthcare professional discount'
            }
        ]
    }
};

// Offer Mart error simulation flags
let offerSimulateErrors = {
    timeout: false,
    serverError: false,
    notFound: false,
    serviceUnavailable: false,
    maintenanceMode: false
};

// Error simulation control endpoint for Offer Mart
offerApp.post('/simulate-error', (req, res) => {
    const { errorType, enabled } = req.body;
    if (offerSimulateErrors.hasOwnProperty(errorType)) {
        offerSimulateErrors[errorType] = enabled;
        res.json({ message: `Offer Mart error simulation ${errorType} ${enabled ? 'enabled' : 'disabled'}` });
    } else {
        res.status(400).json({ error: 'Invalid error type' });
    }
});

offerApp.get('/offers/:userId', (req, res) => {
    const { userId } = req.params;
    
    // Simulate maintenance mode
    if (offerSimulateErrors.maintenanceMode) {
        return res.status(503).json({ 
            error: 'Offer Mart is under maintenance',
            retryAfter: '2024-02-01T10:00:00Z'
        });
    }
    
    // Simulate timeout error
    if (offerSimulateErrors.timeout) {
        return setTimeout(() => {
            res.status(408).json({ error: 'Offer Mart request timeout' });
        }, 6000);
    }
    
    // Simulate service unavailable
    if (offerSimulateErrors.serviceUnavailable) {
        return res.status(503).json({ 
            error: 'Offer Mart service temporarily unavailable',
            estimatedRecovery: '15 minutes'
        });
    }
    
    // Simulate server error
    if (offerSimulateErrors.serverError) {
        return res.status(500).json({ error: 'Offer Mart internal server error' });
    }
    
    // Simulate not found error
    if (offerSimulateErrors.notFound) {
        return res.status(404).json({ error: 'No offers found for user' });
    }
    
    // Return offer data if exists
    const offers = offerData[userId];
    if (offers) {
        res.json({
            success: true,
            data: offers,
            timestamp: new Date().toISOString(),
            processingTime: Math.floor(Math.random() * 2000) + 500 // 0.5-2.5 seconds
        });
    } else {
        res.status(404).json({
            success: false,
            error: 'No pre-approved offers found for user',
            timestamp: new Date().toISOString()
        });
    }
});

// Combined server for Render deployment (single port)
const combinedApp = express();
combinedApp.use(cors());
combinedApp.use(bodyParser.json());

// Health check for combined server
combinedApp.get('/health', (req, res) => {
    res.json({ status: 'healthy', service: 'combined-mock-apis' });
});

// Mount CRM routes under /crm
combinedApp.use('/crm', (req, res, next) => {
    // Rewrite the URL for the CRM app
    req.url = '/crm' + req.url;
    crmApp(req, res, next);
});

// Mount Credit Bureau routes under /credit
combinedApp.get('/credit-score/:userId', (req, res) => {
    const { userId } = req.params;
    
    if (creditSimulateErrors.timeout) {
        return setTimeout(() => {
            res.status(408).json({ error: 'Credit bureau request timeout' });
        }, 8000);
    }
    
    if (creditSimulateErrors.serviceUnavailable) {
        return res.status(503).json({ error: 'Credit bureau service temporarily unavailable' });
    }
    
    if (creditSimulateErrors.serverError) {
        return res.status(500).json({ error: 'Credit bureau internal server error' });
    }
    
    const creditData = creditScoreData[userId];
    if (creditData) {
        res.json({
            success: true,
            creditScore: creditData.creditScore,
            data: creditData,
            timestamp: new Date().toISOString()
        });
    } else {
        // For unknown users, generate a random good credit score
        res.json({
            success: true,
            creditScore: Math.floor(Math.random() * 150) + 700,
            data: {
                userId: userId,
                creditScore: Math.floor(Math.random() * 150) + 700,
                scoreRange: 'Good',
                reportDate: new Date().toISOString().split('T')[0],
                bureau: 'CIBIL'
            },
            timestamp: new Date().toISOString()
        });
    }
});

// Mount Offer Mart routes under /offers
combinedApp.get('/offers/:userId', (req, res) => {
    const { userId } = req.params;
    
    if (offerSimulateErrors.maintenanceMode) {
        return res.status(503).json({ error: 'Offer Mart is under maintenance' });
    }
    
    if (offerSimulateErrors.timeout) {
        return setTimeout(() => {
            res.status(408).json({ error: 'Offer Mart request timeout' });
        }, 6000);
    }
    
    const offers = offerData[userId];
    if (offers) {
        res.json({
            success: true,
            preApprovedLimit: offers.preApprovedLimit,
            interestRate: offers.interestRate,
            data: offers,
            timestamp: new Date().toISOString()
        });
    } else {
        // For unknown users, generate default offer
        res.json({
            success: true,
            preApprovedLimit: 500000,
            interestRate: 12.5,
            data: {
                userId: userId,
                preApprovedLimit: 500000,
                interestRate: 12.5,
                tenure: [12, 24, 36, 48, 60],
                offerType: 'Standard'
            },
            timestamp: new Date().toISOString()
        });
    }
});

// Start servers
const PORT = process.env.PORT || 3001;

if (require.main === module) {
    // If PORT env is set (Render/production) OR NODE_ENV is production - use single combined server
    if (process.env.PORT || process.env.NODE_ENV === 'production') {
        combinedApp.listen(PORT, '0.0.0.0', () => {
            console.log(`Combined Mock APIs running on port ${PORT}`);
        });
    } else {
        // Development mode - run separate servers
        crmApp.listen(crmPort, () => {
            console.log(`CRM API Mock running on port ${crmPort}`);
        });
        
        creditApp.listen(creditPort, () => {
            console.log(`Credit Bureau API Mock running on port ${creditPort}`);
        });
        
        offerApp.listen(offerPort, () => {
            console.log(`Offer Mart API Mock running on port ${offerPort}`);
        });
    }
}

module.exports = { crmApp, creditApp, offerApp, combinedApp };