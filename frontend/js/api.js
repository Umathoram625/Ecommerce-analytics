class ApiClient {
    constructor(baseUrl = '/api/v1') {
        this.baseUrl = baseUrl;
    }

    buildQueryString(params = {}) {
        const query = new URLSearchParams();
        for (const key in params) {
            const val = params[key];
            if (val !== null && val !== undefined && val !== '' && val !== 'all') {
                query.append(key, val);
            }
        }
        const qs = query.toString();
        return qs ? `?${qs}` : '';
    }

    async get(endpoint, params = {}) {
        const url = `${this.baseUrl}${endpoint}${this.buildQueryString(params)}`;
        try {
            const response = await fetch(url, {
                headers: { 'Accept': 'application/json' }
            });
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `HTTP Error ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error(`API GET error on ${endpoint}:`, error);
            throw error;
        }
    }

    async post(endpoint, data, isFormData = false) {
        const url = `${this.baseUrl}${endpoint}`;
        try {
            const options = {
                method: 'POST'
            };
            if (isFormData) {
                options.body = data;
            } else {
                options.headers = {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                };
                options.body = JSON.stringify(data);
            }

            const response = await fetch(url, options);
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `HTTP Error ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error(`API POST error on ${endpoint}:`, error);
            throw error;
        }
    }

    async fetchKPIs(filters) { return this.get('/analytics/kpis', filters); }
    async fetchTrends(filters) { return this.get('/analytics/trends', filters); }
    async fetchCategories(filters) { return this.get('/analytics/categories', filters); }
    async fetchProducts(params) { return this.get('/analytics/products', params); }
    async fetchRegional(filters) { return this.get('/analytics/regional', filters); }
    async fetchStates(filters) { return this.get('/analytics/states', filters); }
    async fetchCustomers(filters) { return this.get('/analytics/customers', filters); }
    async fetchRFM(filters) { return this.get('/analytics/rfm', filters); }
    async fetchForecast(params) { return this.get('/forecast', params); }
    async fetchFilterOptions() { return this.get('/filters'); }
    async fetchHealth() { return this.get('/health'); }

    async uploadCSV(formData) { return this.post('/dataset/upload', formData, true); }
    async resetDataset() { return this.post('/dataset/reset', {}); }
    async fetchAuditLogs() { return this.get('/dataset/audit-logs'); }

    getExportUrl(filters) {
        return `${this.baseUrl}/dataset/export${this.buildQueryString(filters)}`;
    }
}

const api = new ApiClient();
