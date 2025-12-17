/**
 * AI Loan Chatbot - Complete All-in-One Server
 * Everything runs here: Mock APIs + Full Backend Logic + Frontend
 */

const express = require('express');
const cors = require('cors');
const path = require('path');
const fs = require('fs');

const app = express();
const PORT = process.env.PORT || 10000;

// Middleware
app.use(cors());
app.use(express.json());

// Serve frontend static files
app.use(express.static(path.join(__dirname, 'frontend/build')));

// ============== DATA STORAGE ==============
let applications = [];
let sanctionLetters = [];
let sessionData = {};

// ============== MOCK APIs ==============
const customerData = {
    'CUST001': { id: 'CUST001', name: 'Rajesh Kumar', age: 32, city: 'Mumbai', phone: '9876543210', salary: 85000, kycStatus: 'verified' },
    'CUST002': { id: 'CUST002', name: 'Priya Sharma', age: 28, city: 'Delhi', phone: '9876543211', salary: 120000, kycStatus: 'verified' },
};

// Health check
app.get('/health', (req, res) => res.json({ status: 'healthy', service: 'ai-loan-chatbot' }));
app.get('/api/health', (req, res) => res.json({ status: 'healthy', service: 'ai-loan-chatbot' }));

// CRM API
app.get('/crm/:userId', (req, res) => {
    const customer = customerData[req.params.userId];
    res.json({ success: true, data: customer || { id: req.params.userId, name: 'Guest', kycStatus: 'pending' } });
});

// Credit Score API
app.get('/credit-score/:userId', (req, res) => {
    const score = Math.floor(Math.random() * 150) + 700;
    res.json({ success: true, creditScore: score, data: { userId: req.params.userId, creditScore: score, scoreRange: 'Good' } });
});

// Offers API
app.get('/offers/:userId', (req, res) => {
    res.json({ success: true, preApprovedLimit: 500000, interestRate: 12.5 });
});

// ============== CHAT API ==============
app.post('/api/chat/message', (req, res) => {
    const { message, sessionId, form_data } = req.body;
    const session = sessionId || `session_${Date.now()}`;
    
    if (!sessionData[session]) {
        sessionData[session] = { stage: 'initiation', customerData: null, loanOption: null };
    }
    
    const state = sessionData[session];
    let response = { success: true, context: { sessionId: session, currentAgent: 'master' } };
    
    // Handle form submission
    if (form_data?.form_data) {
        const fd = form_data.form_data;
        state.customerData = {
            name: fd.full_name,
            phone: fd.phone,
            city: fd.city,
            age: parseInt(fd.age),
            salary: parseFloat(fd.monthly_salary),
            loanAmount: parseFloat(fd.loan_amount),
            employmentType: fd.employment_type
        };
        state.stage = 'sales';
        
        const amount = state.customerData.loanAmount;
        const options = [
            { index: 1, amount, tenure: 36, interest_rate: 12.0, emi: Math.round(amount * 0.0332) },
            { index: 2, amount, tenure: 48, interest_rate: 12.5, emi: Math.round(amount * 0.0266) },
            { index: 3, amount, tenure: 60, interest_rate: 13.0, emi: Math.round(amount * 0.0227) }
        ];
        
        response.message = `Thank you ${state.customerData.name}! Based on your profile, here are your loan options:`;
        response.messageType = 'loan_options';
        response.agentType = 'sales';
        response.metadata = { loan_options: options, customer_profile: state.customerData };
        return res.json(response);
    }
    
    const msgLower = (message || '').toLowerCase();
    
    // Initial greeting
    if (state.stage === 'initiation' && (msgLower.includes('loan') || msgLower.includes('apply') || msgLower.includes('need') || msgLower.includes('hi') || msgLower.includes('hello'))) {
        response.message = "I'd be happy to help you with a personal loan! Please fill out the form below:";
        response.messageType = 'form';
        response.agentType = 'sales';
        response.metadata = {
            form_data: {
                form_type: 'customer_info',
                title: 'Personal Loan Application',
                description: 'Please provide your details to get personalized loan options',
                submit_text: 'Get Loan Options',
                fields: [
                    { name: 'full_name', label: 'Full Name', type: 'text', required: true, placeholder: 'Enter your full name' },
                    { name: 'phone', label: 'Mobile Number', type: 'tel', required: true, placeholder: '10-digit mobile number' },
                    { name: 'city', label: 'City', type: 'text', required: true, placeholder: 'Your city' },
                    { name: 'age', label: 'Age', type: 'number', required: true, placeholder: 'Your age', min: 21, max: 65 },
                    { name: 'monthly_salary', label: 'Monthly Salary (₹)', type: 'number', required: true, placeholder: 'e.g. 50000', min: 15000 },
                    { name: 'loan_amount', label: 'Loan Amount Required (₹)', type: 'number', required: true, placeholder: 'e.g. 500000', min: 50000, max: 5000000 },
                    { name: 'employment_type', label: 'Employment Type', type: 'select', required: true, options: [
                        { value: 'salaried', label: 'Salaried' },
                        { value: 'self_employed', label: 'Self Employed' },
                        { value: 'business', label: 'Business Owner' }
                    ]}
                ]
            }
        };
        return res.json(response);
    }
    
    // After loan option selection - verification
    if (msgLower.includes('select') || msgLower.includes('option')) {
        state.stage = 'verification';
        response.message = `✅ **Option Selected!**\n\nNow let's verify your identity.\n\n[YES_PROCEED]`;
        response.agentType = 'verification';
        return res.json(response);
    }
    
    // Credit check
    if (msgLower.includes('verification complete') || msgLower.includes('credit check')) {
        state.stage = 'underwriting';
        const score = Math.floor(Math.random() * 100) + 750;
        response.message = `📊 **Credit Check Complete!**\n\n✅ Credit Score: ${score}/900 - Excellent\n✅ Risk Assessment: Low Risk\n\nYour loan is eligible for approval!\n\n[PROCEED_APPROVAL]`;
        response.agentType = 'underwriting';
        return res.json(response);
    }
    
    // Generate sanction letter - CHECK THIS FIRST (before approval check)
    if (state.stage === 'approved' && (msgLower.includes('sanction') || msgLower.includes('letter') || msgLower.includes('generate'))) {
        const amount = state.customerData?.loanAmount || 500000;
        const name = state.customerData?.name || 'Customer';
        const letterId = `SL_${Date.now()}`;
        const emi = Math.round(amount * 0.0222);
        
        sanctionLetters.push({
            id: letterId,
            customer_name: name,
            loan_amount: amount,
            tenure: 60,
            interest_rate: 12.0,
            emi: emi,
            filename: `sanction_letter_${letterId}.pdf`,
            download_url: `/api/download/sanction-letter/${letterId}`,
            generated_at: new Date().toISOString(),
            downloaded_count: 0
        });
        
        state.stage = 'completed';
        
        response.message = `📄 **Sanction Letter Generated Successfully!**\n\n**Loan Details:**\n• Customer: ${name}\n• Amount: ₹${amount.toLocaleString()}\n• Tenure: 60 months\n• Interest Rate: 12% p.a.\n• Monthly EMI: ₹${emi.toLocaleString()}\n\n✅ Your application has been saved to history.\n\nThank you for choosing us! 🎉`;
        response.messageType = 'download_link';
        response.agentType = 'sanction';
        response.metadata = {
            download_url: `/api/download/sanction-letter/${letterId}`,
            filename: `sanction_letter_${letterId}.pdf`,
            letter_id: letterId
        };
        return res.json(response);
    }
    
    // Loan approval
    if (state.stage !== 'approved' && (msgLower.includes('approval') || msgLower.includes('approve') || msgLower.includes('eligibility'))) {
        state.stage = 'approved';
        const amount = state.customerData?.loanAmount || 500000;
        
        // Save application
        const appId = `APP_${Date.now()}`;
        applications.push({
            id: appId,
            customer_name: state.customerData?.name || 'Customer',
            requested_amount: amount,
            approved_amount: amount,
            tenure: 60,
            interest_rate: 12.0,
            emi: Math.round(amount * 0.0222),
            status: 'approved',
            created_at: new Date().toISOString()
        });
        
        response.message = `🎉 **CONGRATULATIONS!**\n\n**Your loan of ₹${amount.toLocaleString()} has been APPROVED!**\n\nClick below to generate your sanction letter.\n\n[GENERATE_LETTER]`;
        response.agentType = 'underwriting';
        return res.json(response);
    }
    
    // Default response
    response.message = "Hello! I'm your AI Loan Assistant. Say 'I need a loan' to get started!";
    response.agentType = 'master';
    res.json(response);
});

// ============== DOWNLOAD API ==============
app.get('/api/download/sanction-letter/:letterId', (req, res) => {
    const letter = sanctionLetters.find(l => l.id === req.params.letterId);
    if (!letter) {
        return res.status(404).json({ error: 'Sanction letter not found' });
    }
    
    // Generate a simple text-based sanction letter (in production, use PDF library)
    const content = `
================================================================================
                           TATA CAPITAL LIMITED
                         LOAN SANCTION LETTER
================================================================================

Date: ${new Date().toLocaleDateString('en-IN')}
Reference No: ${letter.id}

Dear ${letter.customer_name},

We are pleased to inform you that your Personal Loan application has been 
APPROVED with the following terms and conditions:

--------------------------------------------------------------------------------
                              LOAN DETAILS
--------------------------------------------------------------------------------

Loan Amount Sanctioned    : ₹ ${letter.loan_amount.toLocaleString('en-IN')}
Loan Tenure               : ${letter.tenure} months
Rate of Interest          : ${letter.interest_rate}% per annum
Monthly EMI               : ₹ ${letter.emi.toLocaleString('en-IN')}
Processing Fee            : ₹ ${Math.round(letter.loan_amount * 0.01).toLocaleString('en-IN')}

--------------------------------------------------------------------------------
                           TERMS & CONDITIONS
--------------------------------------------------------------------------------

1. This sanction is valid for 30 days from the date of issue.
2. The loan is subject to completion of all documentation.
3. EMI will be debited from your registered bank account.
4. Prepayment charges may apply as per bank policy.

--------------------------------------------------------------------------------

For any queries, please contact our customer support:
📞 1800-209-8800 (Toll Free)
📧 support@tatacapital.com

Thank you for choosing Tata Capital!

================================================================================
                    This is a system generated document
================================================================================
`;

    // Increment download count
    letter.downloaded_count++;
    
    res.setHeader('Content-Type', 'text/plain');
    res.setHeader('Content-Disposition', `attachment; filename="sanction_letter_${letter.id}.txt"`);
    res.send(content);
});

// ============== HISTORY API ==============
app.get('/api/history/applications', (req, res) => {
    res.json({ success: true, applications, count: applications.length });
});

app.get('/api/history/sanction-letters', (req, res) => {
    res.json({ success: true, sanction_letters: sanctionLetters, count: sanctionLetters.length });
});

app.get('/api/history/statistics', (req, res) => {
    res.json({
        success: true,
        statistics: {
            total_applications: applications.length,
            approved: applications.filter(a => a.status === 'approved').length,
            rejected: 0,
            pending: 0,
            approval_rate: 100,
            total_sanction_letters: sanctionLetters.length
        }
    });
});

// ============== SERVE FRONTEND ==============
app.get('*', (req, res) => {
    const indexPath = path.join(__dirname, 'frontend/build', 'index.html');
    if (fs.existsSync(indexPath)) {
        res.sendFile(indexPath);
    } else {
        res.json({
            status: 'running',
            message: 'AI Loan Chatbot API Server',
            note: 'Frontend not built. Run: cd frontend && npm install && npm run build',
            endpoints: ['/health', '/api/chat/message', '/api/history/applications']
        });
    }
});

app.listen(PORT, '0.0.0.0', () => {
    console.log(`🚀 AI Loan Chatbot running on port ${PORT}`);
    console.log(`   Health: http://localhost:${PORT}/health`);
});
