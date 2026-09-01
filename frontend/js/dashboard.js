class DashboardController {
    constructor() {
        this.activeTab = 'overview';
        this.filters = {
            start_date: null,
            end_date: null,
            region: 'all',
            state: 'all',
            category: 'all',
            sub_category: 'all',
            segment: 'all',
            ship_mode: 'all'
        };
        this.pendingUploadFile = null;
    }

    async init() {
        console.log('Initializing E-Commerce Analytics Dashboard...');
        this.setupEventListeners();
        this.setupTheme();
        await this.loadFilterOptions();
        await this.loadDashboardData();
        await this.checkSystemHealth();
    }

    setupEventListeners() {
        document.querySelectorAll('.sidebar-nav .nav-item').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const tabId = link.getAttribute('data-tab');
                this.switchTab(tabId);
            });
        });

        const debouncedRefresh = Utils.debounce(() => this.loadDashboardData(), 300);
        ['filterStartDate', 'filterEndDate', 'filterRegion', 'filterState', 
         'filterCategory', 'filterSubCategory', 'filterSegment', 'filterShipMode'].forEach(id => {
            const el = document.getElementById(id);
            if (el) {
                el.addEventListener('change', () => {
                    this.readFiltersFromUI();
                    debouncedRefresh();
                });
            }
        });

        document.getElementById('btnResetFilters')?.addEventListener('click', () => this.resetFilters());
        document.getElementById('themeToggle')?.addEventListener('click', () => this.toggleTheme());
        document.getElementById('sidebarToggle')?.addEventListener('click', () => {
            document.getElementById('sidebar')?.classList.toggle('open');
        });
        document.getElementById('btnExportCSV')?.addEventListener('click', () => this.exportCSV());

        document.getElementById('btnOpenUploadModal')?.addEventListener('click', () => this.openUploadModal());
        document.getElementById('btnCloseUploadModal')?.addEventListener('click', () => this.closeUploadModal());
        document.getElementById('btnCancelModal')?.addEventListener('click', () => this.closeUploadModal());
        document.getElementById('btnSubmitModalUpload')?.addEventListener('click', () => this.submitModalUpload());

        this.setupDropzone('datasetDropzone', 'csvFileInput');
        this.setupDropzone('modalDropzone', 'modalCsvFileInput');

        document.getElementById('btnResetDataset')?.addEventListener('click', () => this.resetDatabase());
        document.getElementById('btnRunForecast')?.addEventListener('click', () => this.loadForecastingData());
    }

    setupTheme() {
        const savedTheme = localStorage.getItem('apex_theme') || 'dark';
        document.documentElement.setAttribute('data-theme', savedTheme);
        this.updateThemeIcon(savedTheme);
    }

    toggleTheme() {
        const current = document.documentElement.getAttribute('data-theme');
        const next = current === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', next);
        localStorage.setItem('apex_theme', next);
        this.updateThemeIcon(next);
    }

    updateThemeIcon(theme) {
        const icon = document.querySelector('#themeToggle i');
        if (icon) {
            icon.className = theme === 'dark' ? 'fa-solid fa-sun' : 'fa-solid fa-moon';
        }
    }

    switchTab(tabId) {
        this.activeTab = tabId;
        document.querySelectorAll('.sidebar-nav .nav-item').forEach(el => {
            el.classList.toggle('active', el.getAttribute('data-tab') === tabId);
        });

        document.querySelectorAll('.tab-pane').forEach(el => {
            el.classList.toggle('active', el.id === `pane-${tabId}`);
        });

        const headings = {
            overview: ['Executive Overview', 'Real-time commercial performance metrics & dynamic financial intelligence'],
            trends: ['Sales & Financial Trends', 'Longitudinal revenue trajectories, profit margins, and month-over-month growth'],
            categories: ['Categories & Products Performance', 'Catalog profitability, sub-category distribution, and margin analysis'],
            geography: ['Regional & State Analytics', 'Geographical territory sales, state rankings, and logistics performance'],
            customers: ['Customer Intelligence & RFM', 'Behavioral segmentation, repeat cohorts, and customer lifetime value'],
            forecasting: ['Predictive Sales Forecasting', 'Statistical time-series projections with confidence bounds'],
            dataset: ['Dataset & Pipeline Manager', 'CSV ingestion pipeline, schema normalization, and validation audit logs']
        };

        if (headings[tabId]) {
            document.getElementById('pageHeading').textContent = headings[tabId][0];
            document.getElementById('pageSubheading').textContent = headings[tabId][1];
        }

        this.loadTabData(tabId);
    }

    readFiltersFromUI() {
        this.filters.start_date = document.getElementById('filterStartDate')?.value || null;
        this.filters.end_date = document.getElementById('filterEndDate')?.value || null;
        this.filters.region = document.getElementById('filterRegion')?.value || 'all';
        this.filters.state = document.getElementById('filterState')?.value || 'all';
        this.filters.category = document.getElementById('filterCategory')?.value || 'all';
        this.filters.sub_category = document.getElementById('filterSubCategory')?.value || 'all';
        this.filters.segment = document.getElementById('filterSegment')?.value || 'all';
        this.filters.ship_mode = document.getElementById('filterShipMode')?.value || 'all';
    }

    resetFilters() {
        ['filterRegion', 'filterState', 'filterCategory', 'filterSubCategory', 'filterSegment', 'filterShipMode'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.value = 'all';
        });
        this.readFiltersFromUI();
        this.loadDashboardData();
        Utils.showToast('Filters reset to default view.', 'info');
    }

    async loadFilterOptions() {
        try {
            const options = await api.fetchFilterOptions();
            if (options.date_range) {
                const sEl = document.getElementById('filterStartDate');
                const eEl = document.getElementById('filterEndDate');
                if (sEl && !sEl.value) sEl.value = options.date_range.min_date;
                if (eEl && !eEl.value) eEl.value = options.date_range.max_date;
                document.getElementById('datasetDateRange').textContent = `${options.date_range.min_date} to ${options.date_range.max_date}`;
            }
            this.populateSelect('filterRegion', options.regions);
            this.populateSelect('filterState', options.states);
            this.populateSelect('filterCategory', options.categories);
            this.populateSelect('filterSubCategory', options.sub_categories);
            this.populateSelect('filterSegment', options.segments);
            this.populateSelect('filterShipMode', options.ship_modes);
            this.readFiltersFromUI();
        } catch (error) {
            console.error('Failed to load filter options:', error);
        }
    }

    populateSelect(elementId, items) {
        const el = document.getElementById(elementId);
        if (!el || !items) return;
        const currentVal = el.value;
        const defaultLabel = el.options[0]?.text || 'All';
        el.innerHTML = `<option value="all">${defaultLabel}</option>`;
        items.forEach(item => {
            const opt = document.createElement('option');
            opt.value = item;
            opt.textContent = item;
            el.appendChild(opt);
        });
        if (currentVal && items.includes(currentVal)) {
            el.value = currentVal;
        }
    }

    async loadDashboardData() {
        try {
            await this.loadKPIs();
            await this.loadTabData(this.activeTab);
        } catch (err) {
            console.error('Error loading dashboard data:', err);
            Utils.showToast('Failed to update dashboard data.', 'error');
        }
    }

    async loadKPIs() {
        const kpis = await api.fetchKPIs(this.filters);
        document.getElementById('kpiTotalSales').textContent = Utils.formatCurrency(kpis.total_sales);
        document.getElementById('kpiTotalProfit').textContent = Utils.formatCurrency(kpis.total_profit);
        document.getElementById('kpiTotalOrders').textContent = Utils.formatNumber(kpis.total_orders);
        document.getElementById('kpiTotalCustomers').textContent = Utils.formatNumber(kpis.total_customers);
        document.getElementById('kpiAOV').textContent = Utils.formatCurrency(kpis.avg_order_value);
        document.getElementById('kpiProfitMargin').textContent = Utils.formatPercent(kpis.profit_margin);
        document.getElementById('kpiTotalUnits').textContent = `${Utils.formatNumber(kpis.total_quantity)} units sold`;
        document.getElementById('kpiProfitMarginTag').textContent = `Margin: ${Utils.formatPercent(kpis.profit_margin)}`;
        document.getElementById('kpiAvgDiscount').textContent = `Avg Discount: ${Utils.formatPercent(kpis.avg_discount)}`;
    }

    async loadTabData(tabId) {
        switch (tabId) {
            case 'overview':
                await this.loadOverviewData();
                break;
            case 'trends':
                await this.loadTrendsData();
                break;
            case 'categories':
                await this.loadCategoriesData();
                break;
            case 'geography':
                await this.loadGeographyData();
                break;
            case 'customers':
                await this.loadCustomersData();
                break;
            case 'forecasting':
                await this.loadForecastingData();
                break;
            case 'dataset':
                await this.loadDatasetManagerData();
                break;
        }
    }

    async loadOverviewData() {
        const [trends, categories, topProducts, regional] = await Promise.all([
            api.fetchTrends(this.filters),
            api.fetchCategories(this.filters),
            api.fetchProducts({ ...this.filters, sort_by: 'sales', limit: 5 }),
            api.fetchRegional(this.filters)
        ]);

        charts.renderOverviewTrendChart('overviewTrendChart', trends);
        charts.renderCategoryDoughnut('overviewCategoryChart', categories);
        charts.renderRegionalBarChart('overviewRegionalChart', regional);

        const tbody = document.getElementById('overviewTopProductsBody');
        if (tbody) {
            tbody.innerHTML = topProducts.map(p => `
                <tr>
                    <td><strong>${p.product_name}</strong></td>
                    <td><span class="badge badge-info">${p.category}</span></td>
                    <td>${Utils.formatCurrency(p.sales)}</td>
                    <td style="color: ${p.profit >= 0 ? 'var(--color-success)' : 'var(--color-danger)'}">${Utils.formatCurrency(p.profit)}</td>
                    <td>${Utils.formatPercent(p.profit_margin)}</td>
                </tr>
            `).join('');
        }
    }

    async loadTrendsData() {
        const trends = await api.fetchTrends(this.filters);
        charts.renderOverviewTrendChart('detailedTrendChart', trends);

        const tbody = document.getElementById('monthlyLedgerBody');
        if (tbody) {
            tbody.innerHTML = trends.map(t => `
                <tr>
                    <td><strong>${t.year_month}</strong></td>
                    <td>${t.month_name}</td>
                    <td>${Utils.formatCurrency(t.sales)}</td>
                    <td style="color: ${t.profit >= 0 ? 'var(--color-success)' : 'var(--color-danger)'}">${Utils.formatCurrency(t.profit)}</td>
                    <td>${Utils.formatNumber(t.orders)}</td>
                    <td>${Utils.formatPercent(t.profit_margin)}</td>
                    <td>
                        ${t.sales_mom_growth !== null ? `
                            <span class="badge ${t.sales_mom_growth >= 0 ? 'badge-success' : 'badge-danger'}">
                                ${t.sales_mom_growth >= 0 ? '+' : ''}${t.sales_mom_growth}%
                            </span>
                        ` : '-'}
                    </td>
                </tr>
            `).join('');
        }
    }

    async loadCategoriesData() {
        const [categories, bottomProducts, topProducts] = await Promise.all([
            api.fetchCategories(this.filters),
            api.fetchProducts({ ...this.filters, sort_by: 'profit', ascending: true, limit: 5 }),
            api.fetchProducts({ ...this.filters, sort_by: 'sales', limit: 20 })
        ]);

        charts.renderSubCategoryBarChart('subCategoryChart', categories);

        const bBody = document.getElementById('bottomProductsBody');
        if (bBody) {
            bBody.innerHTML = bottomProducts.map(p => `
                <tr>
                    <td><strong>${p.product_name}</strong></td>
                    <td><span class="badge badge-warning">${p.category}</span></td>
                    <td>${Utils.formatCurrency(p.sales)}</td>
                    <td style="color: var(--color-danger); font-weight: 700;">${Utils.formatCurrency(p.profit)}</td>
                    <td><span class="badge badge-danger">${Utils.formatPercent(p.profit_margin)}</span></td>
                </tr>
            `).join('');
        }

        const aBody = document.getElementById('allProductsBody');
        if (aBody) {
            aBody.innerHTML = topProducts.map(p => `
                <tr>
                    <td><code>${p.product_id}</code></td>
                    <td>${p.product_name}</td>
                    <td>${p.category}</td>
                    <td>${p.sub_category}</td>
                    <td>${Utils.formatNumber(p.quantity)}</td>
                    <td><strong>${Utils.formatCurrency(p.sales)}</strong></td>
                    <td style="color: ${p.profit >= 0 ? 'var(--color-success)' : 'var(--color-danger)'}">${Utils.formatCurrency(p.profit)}</td>
                    <td>${Utils.formatPercent(p.profit_margin)}</td>
                </tr>
            `).join('');
        }
    }

    async loadGeographyData() {
        const [regional, states] = await Promise.all([
            api.fetchRegional(this.filters),
            api.fetchStates(this.filters)
        ]);

        charts.renderRegionalBarChart('detailedRegionalChart', regional);

        const topStates = states.slice(0, 10);
        charts.renderRegionalBarChart('topStatesChart', topStates.map(s => ({
            region: s.state,
            sales: s.sales,
            profit: s.profit
        })));

        const tbody = document.getElementById('stateRankingBody');
        if (tbody) {
            tbody.innerHTML = states.map(s => `
                <tr>
                    <td><strong>${s.state}</strong></td>
                    <td>${s.region}</td>
                    <td>${Utils.formatCurrency(s.sales)}</td>
                    <td style="color: ${s.profit >= 0 ? 'var(--color-success)' : 'var(--color-danger)'}">${Utils.formatCurrency(s.profit)}</td>
                    <td>${Utils.formatNumber(s.orders)}</td>
                    <td>${Utils.formatPercent(s.profit_margin)}</td>
                    <td>
                        <span class="badge ${s.profit >= 0 ? 'badge-success' : 'badge-danger'}">
                            ${s.profit >= 0 ? 'Profitable' : 'Loss-Making'}
                        </span>
                    </td>
                </tr>
            `).join('');
        }
    }

    async loadCustomersData() {
        const [custData, rfmData] = await Promise.all([
            api.fetchCustomers(this.filters),
            api.fetchRFM(this.filters)
        ]);

        charts.renderCustomerSegmentChart('customerSegmentChart', custData.segments || []);
        charts.renderRFMCohortChart('rfmCohortChart', rfmData || []);

        const tbody = document.getElementById('topCustomerLeaderboardBody');
        if (tbody && custData.top_customers) {
            tbody.innerHTML = custData.top_customers.map(c => `
                <tr>
                    <td><code>${c.customer_id}</code></td>
                    <td><strong>${c.customer_name}</strong></td>
                    <td><span class="badge badge-info">${c.segment}</span></td>
                    <td>${Utils.formatCurrency(c.total_spend)}</td>
                    <td style="color: ${c.total_profit >= 0 ? 'var(--color-success)' : 'var(--color-danger)'}">${Utils.formatCurrency(c.total_profit)}</td>
                    <td>${Utils.formatNumber(c.order_count)}</td>
                    <td>${Utils.formatCurrency(c.avg_order_value)}</td>
                </tr>
            `).join('');
        }
    }

    async loadForecastingData() {
        const metric = document.getElementById('forecastMetric')?.value || 'sales';
        const horizon = parseInt(document.getElementById('forecastHorizon')?.value || '6');

        try {
            const res = await api.fetchForecast({ ...this.filters, metric, horizon });
            document.getElementById('forecastChartHeading').textContent = 
                `${metric === 'sales' ? 'Sales Revenue' : 'Net Profit'} Forecast Trajectory (95% Confidence Band)`;
            document.getElementById('forecastMetricsBadge').innerHTML = 
                `<span>Model: ${res.model_name}</span> | <span>MAE: ${Utils.formatCurrency(res.mae)}</span> | <span>RMSE: ${Utils.formatCurrency(res.rmse)}</span>`;
            
            charts.renderForecastChart('forecastChart', res);
        } catch (err) {
            console.error('Forecasting error:', err);
            Utils.showToast('Could not calculate forecast.', 'error');
        }
    }

    async loadDatasetManagerData() {
        try {
            const logs = await api.fetchAuditLogs();
            const tbody = document.getElementById('auditLogsBody');
            if (tbody && logs) {
                tbody.innerHTML = logs.map(l => `
                    <tr>
                        <td>${new Date(l.uploaded_at).toLocaleString()}</td>
                        <td><strong>${l.filename}</strong></td>
                        <td>${(l.file_size_bytes / 1024).toFixed(1)} KB</td>
                        <td>${Utils.formatNumber(l.total_rows)}</td>
                        <td><span class="badge badge-success">${Utils.formatNumber(l.valid_rows)}</span></td>
                        <td><span class="badge ${l.status === 'SUCCESS' ? 'badge-success' : 'badge-danger'}">${l.status}</span></td>
                    </tr>
                `).join('');
            }
        } catch (e) {
            console.error('Failed to load audit logs:', e);
        }
    }

    async checkSystemHealth() {
        try {
            const health = await api.fetchHealth();
            document.getElementById('dbStatus').textContent = `DB: ${health.database} (${health.environment})`;
            document.getElementById('sidebarTotalRecords').textContent = Utils.formatNumber(health.total_records);
            document.getElementById('datasetTotalRows').textContent = `${Utils.formatNumber(health.total_records)} records`;
            document.getElementById('datasetDbEngine').textContent = health.database === 'connected' ? 'Connected (Ready)' : health.database;
        } catch (e) {
            document.getElementById('dbStatus').textContent = 'API Offline';
        }
    }

    exportCSV() {
        const url = api.getExportUrl(this.filters);
        window.open(url, '_blank');
        Utils.showToast('Downloading filtered dataset CSV...', 'success');
    }

    setupDropzone(dropzoneId, inputId) {
        const dropzone = document.getElementById(dropzoneId);
        const input = document.getElementById(inputId);
        if (!dropzone || !input) return;

        dropzone.addEventListener('click', () => input.click());
        input.addEventListener('change', (e) => {
            if (e.target.files.length) {
                this.handleFileSelected(e.target.files[0]);
            }
        });

        dropzone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropzone.classList.add('dragover');
        });

        dropzone.addEventListener('dragleave', () => dropzone.classList.remove('dragover'));
        dropzone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropzone.classList.remove('dragover');
            if (e.dataTransfer.files.length) {
                this.handleFileSelected(e.dataTransfer.files[0]);
            }
        });
    }

    handleFileSelected(file) {
        if (!file.name.toLowerCase().endsWith('.csv')) {
            Utils.showToast('Please select a valid .csv file.', 'error');
            return;
        }
        this.pendingUploadFile = file;
        
        if (this.activeTab === 'dataset') {
            this.executeUpload(file);
        } else {
            const statusBox = document.getElementById('modalUploadStatus');
            if (statusBox) {
                statusBox.classList.remove('hidden');
                statusBox.innerHTML = `<strong>Selected file:</strong> ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
            }
            document.getElementById('btnSubmitModalUpload')?.removeAttribute('disabled');
        }
    }

    openUploadModal() {
        this.pendingUploadFile = null;
        document.getElementById('uploadModal')?.classList.remove('hidden');
        document.getElementById('modalUploadStatus')?.classList.add('hidden');
        document.getElementById('btnSubmitModalUpload')?.setAttribute('disabled', 'true');
    }

    closeUploadModal() {
        document.getElementById('uploadModal')?.classList.add('hidden');
        this.pendingUploadFile = null;
    }

    async submitModalUpload() {
        if (!this.pendingUploadFile) return;
        await this.executeUpload(this.pendingUploadFile);
        this.closeUploadModal();
    }

    async executeUpload(file) {
        const formData = new FormData();
        formData.append('file', file);

        const progressContainer = document.getElementById('uploadProgressContainer');
        const progressBar = document.getElementById('uploadProgressBar');
        if (progressContainer) progressContainer.classList.remove('hidden');
        if (progressBar) progressBar.style.width = '40%';

        try {
            Utils.showToast(`Uploading and validating ${file.name}...`, 'info');
            const result = await api.uploadCSV(formData);
            if (progressBar) progressBar.style.width = '100%';
            Utils.showToast(result.message, 'success');
            
            await this.loadFilterOptions();
            await this.loadDashboardData();
            await this.checkSystemHealth();
        } catch (error) {
            Utils.showToast(error.message || 'CSV Ingestion Failed', 'error');
        } finally {
            setTimeout(() => {
                if (progressContainer) progressContainer.classList.add('hidden');
                if (progressBar) progressBar.style.width = '0%';
            }, 1000);
        }
    }

    async resetDatabase() {
        if (!confirm('Reset database back to default Sample Superstore dataset?')) return;
        try {
            Utils.showToast('Resetting database...', 'info');
            await api.resetDataset();
            Utils.showToast('Database reset successfully!', 'success');
            await this.loadFilterOptions();
            await this.loadDashboardData();
            await this.checkSystemHealth();
        } catch (e) {
            Utils.showToast(e.message || 'Failed to reset dataset.', 'error');
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new DashboardController();
    window.dashboard.init();
});
