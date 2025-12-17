const request = require('supertest');
const { crmApp, creditApp, offerApp } = require('../server');

describe('Mock APIs', () => {
    describe('CRM API', () => {
        test('should return customer data for valid user', async () => {
            const response = await request(crmApp)
                .get('/crm/CUST001')
                .expect(200);
            
            expect(response.body.success).toBe(true);
            expect(response.body.data.id).toBe('CUST001');
            expect(response.body.data.name).toBe('Rajesh Kumar');
        });

        test('should return 404 for invalid user', async () => {
            const response = await request(crmApp)
                .get('/crm/INVALID')
                .expect(404);
            
            expect(response.body.success).toBe(false);
        });

        test('should simulate server error when enabled', async () => {
            await request(crmApp)
                .post('/simulate-error')
                .send({ errorType: 'serverError', enabled: true })
                .expect(200);

            await request(crmApp)
                .get('/crm/CUST001')
                .expect(500);

            // Reset error simulation
            await request(crmApp)
                .post('/simulate-error')
                .send({ errorType: 'serverError', enabled: false });
        });
    });

    describe('Credit Bureau API', () => {
        test('should return credit score for valid user', async () => {
            const response = await request(creditApp)
                .get('/credit-score/CUST001')
                .expect(200);
            
            expect(response.body.success).toBe(true);
            expect(response.body.data.userId).toBe('CUST001');
            expect(response.body.data.creditScore).toBe(785);
        });

        test('should return 404 for invalid user', async () => {
            const response = await request(creditApp)
                .get('/credit-score/INVALID')
                .expect(404);
            
            expect(response.body.success).toBe(false);
        });
    });

    describe('Offer Mart API', () => {
        test('should return offers for valid user', async () => {
            const response = await request(offerApp)
                .get('/offers/CUST001')
                .expect(200);
            
            expect(response.body.success).toBe(true);
            expect(response.body.data.userId).toBe('CUST001');
            expect(response.body.data.preApprovedLimit).toBe(500000);
        });

        test('should return 404 for invalid user', async () => {
            const response = await request(offerApp)
                .get('/offers/INVALID')
                .expect(404);
            
            expect(response.body.success).toBe(false);
        });
    });
});