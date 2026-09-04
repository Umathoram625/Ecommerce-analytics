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
            const options = { method: 'POST' };
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

    // Dynamic Analytics Endpoints
    getSummary(params) { return this.get('/analytics/summary', params); }
    getSalesTrend(params) { return this.get('/analytics/sales-trend', params); }
    getProfitTrend(params) { return this.get('/analytics/profit-trend', params); }
    getCategoryPerformance(params) { return this.get('/analytics/category-performance', params); }
    getSubCategoryPerformance(params) { return this.get('/analytics/subcategory-performance', params); }
    getTopProducts(params) { return this.get('/analytics/top-products', params); }
    getLossMakingProducts(params) { return this.get('/analytics/loss-making-products', params); }
    getCustomerPerformance(params) { return this.get('/analytics/customer-performance', params); }
    getTopCustomers(params) { return this.get('/analytics/top-customers', params); }
    getCustomerSegments(params) { return this.get('/analytics/customer-segments', params); }
    getRFM(params) { return this.get('/analytics/rfm', params); }
    getGeography(params) { return this.get('/analytics/geography', params); }
    getShipping(params) { return this.get('/analytics/shipping', params); }
    getDiscountImpact(params) { return this.get('/analytics/discount-impact', params); }
    getOrders(params) { return this.get('/analytics/orders', params); }
    getReturns(params) { return this.get('/analytics/returns', params); }
    getInsights(params) { return this.get('/analytics/insights', params); }

    // Dynamic Filters & Health
    getFilters() { return this.get('/filters'); }
    getHealth() { return this.get('/health'); }

    // Forecasting
    getForecast(metric = 'sales', horizon = 6) {
        return this.get('/forecast', { metric, horizon });
    }

    // Dataset Management
    uploadDataset(formData, replace = true) {
        return this.post(`/dataset/upload?replace_existing=${replace}`, formData, true);
    }
    resetDataset() { return this.post('/dataset/reset', {}); }
    getAuditLogs() { return this.get('/dataset/audit-logs'); }
    getExportUrl(params) {
        return `${this.baseUrl}/dataset/export${this.buildQueryString(params)}`;
    }
}

window.api = new ApiClient();
