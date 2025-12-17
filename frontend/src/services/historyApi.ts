import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' }
});

export const historyApi = {
  getApplications: async (limit: number = 50, status?: string) => {
    try {
      const params = new URLSearchParams({ limit: limit.toString() });
      if (status) params.append('status', status);
      const response = await apiClient.get(`/api/history/applications?${params}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching applications:', error);
      return { success: false, applications: [], error: 'Failed to fetch applications' };
    }
  },

  getApplication: async (appId: string) => {
    try {
      const response = await apiClient.get(`/api/history/applications/${appId}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching application:', error);
      return { success: false, error: 'Failed to fetch application' };
    }
  },

  getSanctionLetters: async (limit: number = 50) => {
    try {
      const response = await apiClient.get(`/api/history/sanction-letters?limit=${limit}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching sanction letters:', error);
      return { success: false, sanction_letters: [], error: 'Failed to fetch sanction letters' };
    }
  },

  getStatistics: async () => {
    try {
      const response = await apiClient.get('/api/history/statistics');
      return response.data;
    } catch (error) {
      console.error('Error fetching statistics:', error);
      return { success: false, statistics: null, error: 'Failed to fetch statistics' };
    }
  }
};
