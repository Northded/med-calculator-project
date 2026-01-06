import { CONFIG } from './config.js';

export class ApiService {
    constructor(baseURL) {
        this.baseURL = baseURL;
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;

        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        try {
            const response = await fetch(url, config);

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `HTTP ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }

    async get(endpoint, params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const url = queryString ? `${endpoint}?${queryString}` : endpoint;

        return this.request(url, {
            method: 'GET'
        });
    }

    async post(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async delete(endpoint) {
        return this.request(endpoint, {
            method: 'DELETE'
        });
    }
}

export class CalculationsApi extends ApiService {
    constructor() {
        super(CONFIG.API_URL);
    }

    async checkHealth() {
        return this.get('/health');
    }

    async calculateIMT(data) {
        return this.post('/calculations/imt', data);
    }

    async calculateCalories(data) {
        return this.post('/calculations/calories', data);
    }

    async calculateBloodPressure(data) {
        return this.post('/calculations/blood-pressure', data);
    }

    async getHistory(userId, limit = 10, offset = 0) {
        return this.get('/calculations/history', {
            user_id: userId,
            limit,
            offset
        });
    }

    async deleteCalculation(calcId, userId) {
        return this.delete(`/calculations/${calcId}?user_id=${userId}`);
    }

    async getStats(userId) {
        return this.get('/calculations/stats', {
            user_id: userId
        });
    }
}

export const api = new CalculationsApi();