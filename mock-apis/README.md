# Mock External APIs for AI Loan Chatbot

This directory contains mock implementations of external APIs required by the AI Loan Chatbot system.

## APIs Included

### 1. CRM API (Port 3001)
- **Endpoint**: `GET /crm/:userId`
- **Purpose**: Returns customer KYC data
- **Test Data**: 12 synthetic customer profiles (CUST001-CUST012)

### 2. Credit Bureau API (Port 3002)
- **Endpoint**: `GET /credit-score/:userId`
- **Purpose**: Returns credit scores (0-900 scale)
- **Features**: Realistic credit score distribution with detailed factors

### 3. Offer Mart API (Port 3003)
- **Endpoint**: `GET /offers/:userId`
- **Purpose**: Returns pre-approved loan limits and offers
- **Features**: Varied pre-approved amounts and interest rates

## Running the APIs

```bash
# Install dependencies
npm install

# Start all three API servers
npm start

# Run tests
npm test

# Development mode with auto-restart
npm run dev
```

## API Endpoints

### CRM API Examples
```bash
# Get customer data
curl http://localhost:3001/crm/CUST001

# Simulate server error
curl -X POST http://localhost:3001/simulate-error \
  -H "Content-Type: application/json" \
  -d '{"errorType": "serverError", "enabled": true}'
```

### Credit Bureau API Examples
```bash
# Get credit score
curl http://localhost:3002/credit-score/CUST001

# Simulate timeout
curl -X POST http://localhost:3002/simulate-error \
  -H "Content-Type: application/json" \
  -d '{"errorType": "timeout", "enabled": true}'
```

### Offer Mart API Examples
```bash
# Get offers
curl http://localhost:3003/offers/CUST001

# Simulate service unavailable
curl -X POST http://localhost:3003/simulate-error \
  -H "Content-Type: application/json" \
  -d '{"errorType": "serviceUnavailable", "enabled": true}'
```

## Error Simulation

Each API supports error simulation for testing resilience:

- `timeout`: Simulates request timeouts
- `serverError`: Returns 500 internal server error
- `notFound`: Returns 404 not found
- `serviceUnavailable`: Returns 503 service unavailable (Credit Bureau & Offer Mart)
- `maintenanceMode`: Returns 503 maintenance mode (Offer Mart only)

## Test Data

### Customer Profiles (CUST001-CUST012)
- Diverse demographics across major Indian cities
- Varied employment types (Salaried, Self-Employed, Government, etc.)
- Different salary ranges (₹25K - ₹2L monthly)
- Mixed KYC statuses for testing verification flows

### Credit Scores
- Range: 590-820 (realistic distribution)
- Categories: Poor (590-649), Fair (650-699), Good (700-749), Excellent (750+)
- Detailed factors: Payment history, credit utilization, credit age, etc.

### Loan Offers
- Pre-approved limits: ₹1.5L - ₹8L
- Interest rates: 10.9% - 18.2%
- Various offer types: Basic, Standard, Premium, Premium Plus
- Special offers for specific customer segments

## Health Checks

All APIs include health check endpoints:
- CRM: `GET http://localhost:3001/health`
- Credit Bureau: `GET http://localhost:3002/health`
- Offer Mart: `GET http://localhost:3003/health`