/**
 * ApexSales E-Commerce Sales Analytics - Enterprise Dashboard Controller
 * 100% Dynamic data fetching, filter synchronization, and chart rendering.
 */

class DashboardController {
    constructor() {
        this.activeFilters = {};
        this.ledgerPage = 1;
        this.ledgerPageSize = 20;
        this.ledgerSearchTerm = '';
        this.debounceTimer = null;

        document.addEventListener('DOMContentLoaded', () => this.init());
    }

    async init() {
        this.initTheme();
        this.initNavigation();
        this.initEventListeners();
        await this.loadFilterOptions();
        await this.refreshAllData();
    }

    // ==========================================
    // THEME CONTROLLER
    // ==========================================
    initTheme() {
        const savedTheme = localStorage.getItem('apex_theme') || 'dark';
        document.documentElement.setAttribute('data-theme', savedTheme);
        this.updateThemeIcon(savedTheme);

        const themeBtn = document.getElementById('themeToggleBtn');
        if (themeBtn) {
            themeBtn.addEventListener('click', () => {
                const current = document.documentElement.getAttribute('data-theme');
                const nextTheme = current === 'dark' ? 'light' : 'dark';
                document.documentElement.setAttribute('data-theme', nextTheme);
                localStorage.setItem('apex_theme', nextTheme);
                this.updateThemeIcon(nextTheme);
            });
        }
    }

    updateThemeIcon(theme) {
        const icon = document.getElementById('themeIcon');
        if (icon) {
            icon.className = theme === 'dark' ? 'fa-solid fa-moon' : 'fa-solid fa-sun';
        }
    }

    // ==========================================
    // NAVIGATION CONTROLLER
    // ==========================================
    initNavigation() {
        const navLinks = document.querySelectorAll('.nav-link');
        navLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const targetId = link.getAttribute('data-tab');
                if (!targetId) return;

                // Update active link
                navLinks.forEach(l => l.classList.remove('active'));
                link.classList.add('active');

                // Switch visible pane
                document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
                const targetPane = document.getElementById(targetId);
                if (targetPane) targetPane.classList.add('active');

                // Update title
                const titleElem = document.getElementById('pageTitle');
                const textElem = link.querySelector('span');
                if (titleElem && textElem) titleElem.textContent = textElem.textContent;

                // Close mobile sidebar if open
                document.getElementById('sidebar')?.classList.remove('open');
            });
        });

        // Mobile sidebar toggles
        document.getElementById('sidebarToggleBtn')?.addEventListener('click', () => {
            document.getElementById('sidebar')?.classList.add('open');
        });
        document.getElementById('sidebarCloseBtn')?.addEventListener('click', () => {
            document.getElementById('sidebar')?.classList.remove('open');
        });
    }

    // ==========================================
    // EVENT LISTENERS & FILTER BINDINGS
    // ==========================================
    initEventListeners() {
        // Filter elements
        const filterIds = [
            'filterYear', 'filterQuarter', 'filterMonth', 'filterCountry',
            'filterMarket', 'filterRegion', 'filterCategory', 'filterSubCategory',
            'filterSegment', 'filterShipMode', 'filterOrderStatus'
        ];

        filterIds.forEach(id => {
            const el = document.getElementById(id);
            if (el) {
                el.addEventListener('change', () => this.handleFilterChange());
            }
        });

        // Reset filters button
        document.getElementById('btnResetFilters')?.addEventListener('click', () => {
            filterIds.forEach(id => {
                const el = document.getElementById(id);
                if (el) el.value = 'all';
            });
            this.handleFilterChange();
        });

        // Ledger Search
        const searchInput = document.getElementById('ledgerSearchInput');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                clearTimeout(this.debounceTimer);
                this.debounceTimer = setTimeout(() => {
                    this.ledgerSearchTerm = e.target.value.trim();
                    this.ledgerPage = 1;
                    this.loadOrdersLedger();
                }, 350);
            });
        }

        // Ledger Pagination
        document.getElementById('btnPrevPage')?.addEventListener('click', () => {
            if (this.ledgerPage > 1) {
                this.ledgerPage--;
                this.loadOrdersLedger();
            }
        });

        document.getElementById('btnNextPage')?.addEventListener('click', () => {
            this.ledgerPage++;
            this.loadOrdersLedger();
        });

        // Ledger Export CSV
        document.getElementById('btnExportCSV')?.addEventListener('click', () => {
            window.location.href = window.api.getExportUrl(this.getFilterParams());
        });

        // Forecast Run
        document.getElementById('btnRunForecast')?.addEventListener('click', () => {
            this.loadForecast();
        });

        // Upload Modal
        this.initUploadModal();

        // Dataset Reset
        document.getElementById('btnResetDataset')?.addEventListener('click', async () => {
            if (confirm('Are you sure you want to reset the database to the default Global Superstore dataset?')) {
                try {
                    await window.api.resetDataset();
                    window.utils.showToast('Database reset to default dataset.', 'success');
                    await this.loadFilterOptions();
                    await this.refreshAllData();
                } catch (err) {
                    window.utils.showToast('Failed to reset dataset: ' + err.message, 'error');
                }
            }
        });
    }

    initUploadModal() {
        const modal = document.getElementById('uploadModal');
        const openBtn = document.getElementById('openUploadModalBtn');
        const closeBtn = document.getElementById('closeUploadModalBtn');
        const cancelBtn = document.getElementById('cancelUploadBtn');
        const dropzone = document.getElementById('modalDropzone');
        const fileInput = document.getElementById('modalFileInput');
        const startBtn = document.getElementById('startUploadBtn');
        let selectedFile = null;

        if (openBtn) openBtn.addEventListener('click', () => modal.classList.remove('hidden'));
        const closeModal = () => {
            modal.classList.add('hidden');
            selectedFile = null;
            if (fileInput) fileInput.value = '';
            document.getElementById('modalSelectedFile')?.classList.add('hidden');
            startBtn.disabled = true;
        };

        if (closeBtn) closeBtn.addEventListener('click', closeModal);
        if (cancelBtn) cancelBtn.addEventListener('click', closeModal);

        if (dropzone && fileInput) {
            dropzone.addEventListener('click', () => fileInput.click());
            dropzone.addEventListener('dragover', (e) => { e.preventDefault(); dropzone.classList.add('dragover'); });
            dropzone.addEventListener('dragleave', () => dropzone.classList.remove('dragover'));
            dropzone.addEventListener('drop', (e) => {
                e.preventDefault();
                dropzone.classList.remove('dragover');
                if (e.dataTransfer.files.length) {
                    handleFile(e.dataTransfer.files[0]);
                }
            });

            fileInput.addEventListener('change', (e) => {
                if (e.target.files.length) handleFile(e.target.files[0]);
            });
        }

        const handleFile = (file) => {
            selectedFile = file;
            const badge = document.getElementById('modalSelectedFile');
            if (badge) {
                badge.textContent = `${file.name} (${(file.size / 1024 / 1024).toFixed(2)} MB)`;
                badge.classList.remove('hidden');
            }
            startBtn.disabled = false;
        };

        if (startBtn) {
            startBtn.addEventListener('click', async () => {
                if (!selectedFile) return;
                startBtn.disabled = true;
                startBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Ingesting...';

                try {
                    const formData = new FormData();
                    formData.append('file', selectedFile);
                    const res = await window.api.uploadDataset(formData, true);

                    window.utils.showToast(res.message, 'success');
                    closeModal();
                    await this.loadFilterOptions();
                    await this.refreshAllData();
                } catch (err) {
                    window.utils.showToast('Upload failed: ' + err.message, 'error');
                } finally {
                    startBtn.disabled = false;
                    startBtn.innerHTML = '<i class="fa-solid fa-upload"></i> Process & Ingest';
                }
            });
        }
    }

    // ==========================================
    // FILTER POPULATION & PARAMS
    // ==========================================
    async loadFilterOptions() {
        try {
            const data = await window.api.getFilters();

            // Populate Years dynamically from actual dataset
            const yearSelect = document.getElementById('filterYear');
            if (yearSelect) {
                const currentVal = yearSelect.value;
                yearSelect.innerHTML = '<option value="all">All Years</option>';
                data.years.forEach(y => {
                    const opt = document.createElement('option');
                    opt.value = y;
                    opt.textContent = y;
                    yearSelect.appendChild(opt);
                });
                if (data.years.includes(parseInt(currentVal))) yearSelect.value = currentVal;
            }

            // Populate Months
            const monthSelect = document.getElementById('filterMonth');
            if (monthSelect) {
                monthSelect.innerHTML = '<option value="all">All Months</option>';
                data.months.forEach(m => {
                    const opt = document.createElement('option');
                    opt.value = m.number;
                    opt.textContent = m.name;
                    monthSelect.appendChild(opt);
                });
            }

            // Helper to populate select
            const populate = (elemId, list, defaultLabel) => {
                const sel = document.getElementById(elemId);
                if (!sel) return;
                sel.innerHTML = `<option value="all">${defaultLabel}</option>`;
                list.forEach(item => {
                    const opt = document.createElement('option');
                    opt.value = item;
                    opt.textContent = item;
                    sel.appendChild(opt);
                });
            };

            populate('filterCountry', data.countries, 'All Countries');
            populate('filterMarket', data.markets, 'All Markets');
            populate('filterRegion', data.regions, 'All Regions');
            populate('filterCategory', data.categories, 'All Categories');
            populate('filterSubCategory', data.sub_categories, 'All Subcategories');
            populate('filterSegment', data.segments, 'All Segments');
            populate('filterShipMode', data.ship_modes, 'All Modes');

            // Update Dataset Pill
            const pillLabel = document.getElementById('activeDatasetLabel');
            if (pillLabel && data.years.length > 0) {
                const minYear = Math.min(...data.years);
                const maxYear = Math.max(...data.years);
                pillLabel.textContent = `Active: ${minYear}–${maxYear} Dataset (${data.countries.length} countries)`;
            }
        } catch (err) {
            console.error('Failed to load filter options:', err);
        }
    }

    getFilterParams() {
        const getVal = (id) => {
            const el = document.getElementById(id);
            return el && el.value !== 'all' ? el.value : null;
        };

        const params = {};
        const y = getVal('filterYear');
        if (y) params.year = parseInt(y);

        const q = getVal('filterQuarter');
        if (q) params.quarter = q;

        const m = getVal('filterMonth');
        if (m) params.month = parseInt(m);

        const country = getVal('filterCountry');
        if (country) params.country = country;

        const market = getVal('filterMarket');
        if (market) params.market = market;

        const region = getVal('filterRegion');
        if (region) params.region = region;

        const category = getVal('filterCategory');
        if (category) params.category = category;

        const subCategory = getVal('filterSubCategory');
        if (subCategory) params.sub_category = subCategory;

        const segment = getVal('filterSegment');
        if (segment) params.segment = segment;

        const shipMode = getVal('filterShipMode');
        if (shipMode) params.ship_mode = shipMode;

        const status = getVal('filterOrderStatus');
        if (status) params.order_status = status;

        return params;
    }

    handleFilterChange() {
        this.ledgerPage = 1;
        this.refreshAllData();
    }

    // ==========================================
    // REFRESH ALL DATA ACROSS 8 SECTIONS
    // ==========================================
    async refreshAllData() {
        const params = this.getFilterParams();

        try {
            await Promise.all([
                this.loadKPIs(params),
                this.loadTrends(params),
                this.loadCategoriesAndProducts(params),
                this.loadProfitability(params),
                this.loadCustomersAndRFM(params),
                this.loadGeographyAndShipping(params),
                this.loadReturns(params),
                this.loadOrdersLedger(params),
                this.loadInsights(params),
                this.loadForecast()
            ]);
        } catch (err) {
            console.error('Error refreshing dashboard data:', err);
            window.utils.showToast('Failed to load some analytics: ' + err.message, 'error');
        }
    }

    // 1. KPI CARDS
    async loadKPIs(params) {
        const kpi = await window.api.getSummary(params);

        document.getElementById('kpiRevenue').textContent = window.chartManager.formatCurrency(kpi.total_revenue);
        document.getElementById('kpiProfit').textContent = window.chartManager.formatCurrency(kpi.total_profit);
        document.getElementById('kpiMargin').textContent = `${kpi.profit_margin.toFixed(2)}%`;
        document.getElementById('kpiOrders').textContent = kpi.total_orders.toLocaleString();
        document.getElementById('kpiUnits').textContent = `${kpi.units_sold.toLocaleString()} units sold`;
        document.getElementById('kpiCustomers').textContent = kpi.total_customers.toLocaleString();
        document.getElementById('kpiAOV').textContent = window.chartManager.formatCurrency(kpi.avg_order_value);
        document.getElementById('kpiReturns').textContent = `${kpi.total_returned_orders.toLocaleString()} orders`;
        document.getElementById('kpiReturnRate').textContent = `Return Rate: ${kpi.return_rate.toFixed(2)}%`;
        document.getElementById('kpiShippingCost').textContent = window.chartManager.formatCurrency(kpi.avg_shipping_cost);
        document.getElementById('kpiAvgDiscount').textContent = `Avg Discount: ${kpi.avg_discount.toFixed(1)}%`;
        document.getElementById('kpiProfitSub').textContent = `Profitable: ${kpi.profitable_orders.toLocaleString()} orders`;

        // Also update returns tab KPI cards
        document.getElementById('returnsTabCount').textContent = kpi.total_returned_orders.toLocaleString();
        document.getElementById('returnsTabRate').textContent = `${kpi.return_rate.toFixed(2)}%`;
        document.getElementById('returnsTabRevenue').textContent = window.chartManager.formatCurrency(kpi.returned_revenue);

        // Render profit distribution doughnut
        window.chartManager.renderProfitLossDistribution('profitDistributionChart', kpi);
    }

    // 2. TRENDS (OVERVIEW & DETAILED)
    async loadTrends(params) {
        const trends = await window.api.getSalesTrend(params);
        window.chartManager.renderSalesProfitTrend('overviewTrendChart', trends);
        window.chartManager.renderSalesProfitTrend('detailedTrendChart', trends);

        // Populate Monthly Financials Ledger Table
        const tbody = document.querySelector('#tableMonthlyFinancials tbody');
        if (tbody) {
            tbody.innerHTML = '';
            trends.forEach(t => {
                const tr = document.createElement('tr');
                const yoyClass = t.yoy_growth !== null ? (t.yoy_growth >= 0 ? 'text-success' : 'text-danger') : 'text-muted';
                const yoyText = t.yoy_growth !== null ? `${t.yoy_growth > 0 ? '+' : ''}${t.yoy_growth}%` : '—';
                tr.innerHTML = `
                    <td><strong>${t.period}</strong></td>
                    <td>${t.year}</td>
                    <td>${t.month_name}</td>
                    <td>${t.quarter}</td>
                    <td><strong>${window.chartManager.formatCurrency(t.revenue)}</strong></td>
                    <td>${t.orders.toLocaleString()}</td>
                    <td>${t.units.toLocaleString()}</td>
                    <td class="${yoyClass}">${yoyText}</td>
                    <td>${t.rolling_3m_revenue ? window.chartManager.formatCurrency(t.rolling_3m_revenue) : '—'}</td>
                    <td>${t.running_total_revenue ? window.chartManager.formatCurrency(t.running_total_revenue) : '—'}</td>
                `;
                tbody.appendChild(tr);
            });
        }
    }

    // 3. CATEGORIES & PRODUCTS
    async loadCategoriesAndProducts(params) {
        const [cats, subcats, topProducts] = await Promise.all([
            window.api.getCategoryPerformance(params),
            window.api.getSubCategoryPerformance(params),
            window.api.getTopProducts(params)
        ]);

        window.chartManager.renderCategoryDoughnut('overviewCategoryChart', cats);
        window.chartManager.renderSubcategoryBar('subcategoryPerformanceChart', subcats);

        // Overview Top Products Table
        const tbOverview = document.querySelector('#tableTopProductsOverview tbody');
        if (tbOverview) {
            tbOverview.innerHTML = '';
            topProducts.slice(0, 5).forEach(p => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td><strong>${p.product_name.substring(0, 30)}...</strong></td>
                    <td>${p.category}</td>
                    <td>${window.chartManager.formatCurrency(p.revenue)}</td>
                    <td class="${p.profit >= 0 ? 'text-success' : 'text-danger'}">${window.chartManager.formatCurrency(p.profit)}</td>
                    <td>${p.profit_margin.toFixed(1)}%</td>
                `;
                tbOverview.appendChild(tr);
            });
        }

        // Full Top 10 Products Table
        const tbTop10 = document.querySelector('#tableTop10Products tbody');
        if (tbTop10) {
            tbTop10.innerHTML = '';
            topProducts.forEach(p => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td><code>${p.product_id}</code></td>
                    <td><strong>${p.product_name}</strong></td>
                    <td><span class="badge badge-primary">${p.category}</span></td>
                    <td>${p.sub_category}</td>
                    <td>${p.quantity.toLocaleString()}</td>
                    <td><strong>${window.chartManager.formatCurrency(p.revenue)}</strong></td>
                    <td class="${p.profit >= 0 ? 'text-success' : 'text-danger'}">${window.chartManager.formatCurrency(p.profit)}</td>
                    <td>${p.profit_margin.toFixed(1)}%</td>
                    <td>${p.avg_discount.toFixed(1)}%</td>
                `;
                tbTop10.appendChild(tr);
            });
        }
    }

    // 4. PROFITABILITY & LOSS
    async loadProfitability(params) {
        const [losses, discount] = await Promise.all([
            window.api.getLossMakingProducts(params),
            window.api.getDiscountImpact(params)
        ]);

        window.chartManager.renderDiscountImpactChart('discountImpactChart', discount);

        const tbLoss = document.querySelector('#tableLossMakingProducts tbody');
        if (tbLoss) {
            tbLoss.innerHTML = '';
            losses.forEach(p => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td><strong>${p.product_name}</strong></td>
                    <td><span class="badge badge-warning">${p.category}</span></td>
                    <td>${p.quantity.toLocaleString()}</td>
                    <td>${window.chartManager.formatCurrency(p.revenue)}</td>
                    <td class="text-danger font-bold">${window.chartManager.formatCurrency(p.profit)}</td>
                    <td class="text-danger">${p.profit_margin.toFixed(1)}%</td>
                    <td>${p.avg_discount.toFixed(1)}%</td>
                `;
                tbLoss.appendChild(tr);
            });
        }
    }

    // 5. CUSTOMERS & RFM
    async loadCustomersAndRFM(params) {
        const [rfm, custPerf] = await Promise.all([
            window.api.getRFM(params),
            window.api.getCustomerPerformance(params)
        ]);

        window.chartManager.renderRFMPolar('rfmPolarChart', rfm);

        // Top Customers Leaderboard
        const tbTopCust = document.querySelector('#tableTopCustomers tbody');
        if (tbTopCust) {
            tbTopCust.innerHTML = '';
            (custPerf.top_customers || []).forEach(c => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td><strong>${c.customer_name}</strong></td>
                    <td><span class="badge badge-info">${c.segment}</span></td>
                    <td>${c.country}</td>
                    <td>${c.order_count}</td>
                    <td><strong>${window.chartManager.formatCurrency(c.total_spend)}</strong></td>
                    <td class="${c.total_profit >= 0 ? 'text-success' : 'text-danger'}">${window.chartManager.formatCurrency(c.total_profit)}</td>
                    <td>${window.chartManager.formatCurrency(c.avg_order_value)}</td>
                `;
                tbTopCust.appendChild(tr);
            });
        }

        // RFM Segment Table
        const tbRFM = document.querySelector('#tableRFMSegments tbody');
        if (tbRFM) {
            tbRFM.innerHTML = '';
            rfm.forEach(r => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td><strong>${r.segment}</strong></td>
                    <td>${r.customer_count.toLocaleString()}</td>
                    <td>${r.share_of_customers.toFixed(1)}%</td>
                    <td>${window.chartManager.formatCurrency(r.total_revenue)}</td>
                    <td class="${r.total_profit >= 0 ? 'text-success' : 'text-danger'}">${window.chartManager.formatCurrency(r.total_profit)}</td>
                    <td>${r.avg_recency_days} days</td>
                    <td>${r.avg_frequency} orders</td>
                    <td>${window.chartManager.formatCurrency(r.avg_monetary)}</td>
                `;
                tbRFM.appendChild(tr);
            });
        }
    }

    // 6. GEOGRAPHY & SHIPPING
    async loadGeographyAndShipping(params) {
        const [geo, shipping] = await Promise.all([
            window.api.getGeography(params),
            window.api.getShipping(params)
        ]);

        window.chartManager.renderGeographyBar('geographyBarChart', geo);

        // Overview top geography
        const tbGeoOverview = document.querySelector('#tableTopGeographyOverview tbody');
        if (tbGeoOverview) {
            tbGeoOverview.innerHTML = '';
            geo.slice(0, 5).forEach(g => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td><strong>${g.country}</strong></td>
                    <td>${g.market}</td>
                    <td>${window.chartManager.formatCurrency(g.revenue)}</td>
                    <td class="${g.profit >= 0 ? 'text-success' : 'text-danger'}">${window.chartManager.formatCurrency(g.profit)}</td>
                    <td>${g.orders.toLocaleString()}</td>
                `;
                tbGeoOverview.appendChild(tr);
            });
        }

        // Detailed Geography Table
        const tbGeoDet = document.querySelector('#tableGeographyDetailed tbody');
        if (tbGeoDet) {
            tbGeoDet.innerHTML = '';
            geo.forEach(g => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td><strong>${g.country}</strong></td>
                    <td>${g.market}</td>
                    <td>${g.region}</td>
                    <td>${g.orders.toLocaleString()}</td>
                    <td>${window.chartManager.formatCurrency(g.revenue)}</td>
                    <td class="${g.profit >= 0 ? 'text-success' : 'text-danger'}">${window.chartManager.formatCurrency(g.profit)}</td>
                    <td>${g.profit_margin.toFixed(1)}%</td>
                `;
                tbGeoDet.appendChild(tr);
            });
        }

        // Shipping Table
        const tbShip = document.querySelector('#tableShippingModes tbody');
        if (tbShip) {
            tbShip.innerHTML = '';
            shipping.forEach(s => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td><strong>${s.ship_mode}</strong></td>
                    <td>${s.order_count.toLocaleString()}</td>
                    <td>${window.chartManager.formatCurrency(s.total_revenue)}</td>
                    <td class="${s.total_profit >= 0 ? 'text-success' : 'text-danger'}">${window.chartManager.formatCurrency(s.total_profit)}</td>
                    <td>${window.chartManager.formatCurrency(s.avg_shipping_cost)}</td>
                    <td>${s.avg_shipping_days.toFixed(1)} days</td>
                `;
                tbShip.appendChild(tr);
            });
        }
    }

    // 7. RETURNS TAB
    async loadReturns(params) {
        const retData = await window.api.getReturns(params);

        // Top returned products
        const tbRetProds = document.querySelector('#tableTopReturnedProducts tbody');
        if (tbRetProds) {
            tbRetProds.innerHTML = '';
            retData.top_returned_products.forEach(p => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td><strong>${p.product_name}</strong></td>
                    <td><span class="badge badge-warning">${p.category}</span></td>
                    <td class="text-danger font-bold">${p.return_count}</td>
                    <td>${window.chartManager.formatCurrency(p.returned_revenue)}</td>
                `;
                tbRetProds.appendChild(tr);
            });
        }

        // Top returned customers
        const tbRetCusts = document.querySelector('#tableTopReturnedCustomers tbody');
        if (tbRetCusts) {
            tbRetCusts.innerHTML = '';
            retData.top_returned_customers.forEach(c => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td><strong>${c.customer_name}</strong></td>
                    <td>${c.country}</td>
                    <td class="text-danger font-bold">${c.return_count}</td>
                    <td>${window.chartManager.formatCurrency(c.returned_revenue)}</td>
                `;
                tbRetCusts.appendChild(tr);
            });
        }
    }

    // 8. TRANSACTION LEDGER (PAGINATED & SEARCHABLE)
    async loadOrdersLedger() {
        const params = {
            ...this.getFilterParams(),
            page: this.ledgerPage,
            page_size: this.ledgerPageSize,
            search: this.ledgerSearchTerm || undefined
        };

        const res = await window.api.getOrders(params);

        const tbody = document.getElementById('ledgerTableBody');
        if (tbody) {
            tbody.innerHTML = '';
            if (res.data.length === 0) {
                tbody.innerHTML = '<tr><td colspan="12" class="text-center py-4 text-muted">No transactions found matching criteria.</td></tr>';
            } else {
                res.data.forEach(row => {
                    const tr = document.createElement('tr');
                    const statusBadge = row.order_status === 'Returned' ? 
                        '<span class="badge badge-danger">Returned</span>' : 
                        '<span class="badge badge-success">Completed</span>';
                    tr.innerHTML = `
                        <td><code>${row.order_id}</code></td>
                        <td>${row.order_date}</td>
                        <td><strong>${row.customer_name}</strong></td>
                        <td>${row.country}</td>
                        <td>${row.product_name.substring(0, 30)}...</td>
                        <td>${row.category}</td>
                        <td>${row.quantity}</td>
                        <td>$${row.unit_price.toFixed(2)}</td>
                        <td><strong>${window.chartManager.formatCurrency(row.sales)}</strong></td>
                        <td>${(row.discount * 100).toFixed(0)}%</td>
                        <td class="${row.profit >= 0 ? 'text-success' : 'text-danger'} font-bold">${window.chartManager.formatCurrency(row.profit)}</td>
                        <td>${statusBadge}</td>
                    `;
                    tbody.appendChild(tr);
                });
            }
        }

        // Update pagination
        const start = res.total_records > 0 ? (res.page - 1) * res.page_size + 1 : 0;
        const end = Math.min(res.page * res.page_size, res.total_records);
        document.getElementById('paginationInfo').textContent = `Showing ${start} to ${end} of ${res.total_records.toLocaleString()} records`;
        document.getElementById('currentPageBadge').textContent = `Page ${res.page} of ${res.total_pages}`;
        document.getElementById('btnPrevPage').disabled = res.page <= 1;
        document.getElementById('btnNextPage').disabled = res.page >= res.total_pages;
    }

    // 9. DYNAMIC BUSINESS INSIGHTS
    async loadInsights(params) {
        const container = document.getElementById('insightsContainer');
        if (!container) return;

        const data = await window.api.getInsights(params);
        container.innerHTML = '';

        data.insights.forEach(ins => {
            const card = document.createElement('div');
            card.className = `insight-card ${ins.status}`;
            let icon = 'fa-lightbulb';
            if (ins.status === 'negative') icon = 'fa-triangle-exclamation';
            if (ins.status === 'positive') icon = 'fa-circle-check';
            if (ins.category === 'geography') icon = 'fa-earth-americas';

            card.innerHTML = `
                <div class="insight-header">
                    <i class="fa-solid ${icon}"></i>
                    <h4>${ins.title}</h4>
                </div>
                <p class="insight-desc">${ins.description}</p>
            `;
            container.appendChild(card);
        });
    }

    // 10. TIME-SERIES FORECASTING
    async loadForecast() {
        const metricEl = document.getElementById('forecastMetric');
        const horizonEl = document.getElementById('forecastHorizon');
        const metric = metricEl ? metricEl.value : 'sales';
        const horizon = horizonEl ? parseInt(horizonEl.value) : 6;

        try {
            const res = await window.api.getForecast(metric, horizon);
            window.chartManager.renderForecastChart('forecastChart', res);
            document.getElementById('forecastMetricsBadge').innerHTML = 
                `<span>MAE: $${res.mae.toLocaleString()}</span> | <span>RMSE: $${res.rmse.toLocaleString()}</span>`;
            document.getElementById('forecastChartHeading').textContent = 
                `${metric === 'sales' ? 'Sales Revenue' : 'Net Profit'} Forecast Trajectory (95% Confidence Band)`;
        } catch (err) {
            console.error('Forecast error:', err);
        }
    }
}

window.dashboardController = new DashboardController();
