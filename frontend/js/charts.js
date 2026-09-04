class ChartManager {
    constructor() {
        this.instances = {};
        this.setupDefaults();
    }

    setupDefaults() {
        if (typeof Chart === 'undefined') return;
        Chart.defaults.font.family = "'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif";
        Chart.defaults.color = '#94a3b8';
        Chart.defaults.borderColor = 'rgba(255, 255, 255, 0.08)';
        Chart.defaults.plugins.legend.labels.usePointStyle = true;
        Chart.defaults.plugins.tooltip.padding = 12;
        Chart.defaults.plugins.tooltip.cornerRadius = 8;
    }

    destroyChart(chartKey) {
        if (this.instances[chartKey]) {
            this.instances[chartKey].destroy();
            delete this.instances[chartKey];
        }
    }

    formatCurrency(val) {
        if (val === null || val === undefined) return '$0';
        if (Math.abs(val) >= 1e6) return `$${(val / 1e6).toFixed(2)}M`;
        if (Math.abs(val) >= 1e3) return `$${(val / 1e3).toFixed(1)}K`;
        return `$${val.toFixed(2)}`;
    }

    renderSalesProfitTrend(canvasId, trendData) {
        this.destroyChart(canvasId);
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;
        const ctx = canvas.getContext('2d');

        const labels = trendData.map(d => d.period || d.year_month);
        const revenues = trendData.map(d => d.revenue || d.sales || 0);
        const profits = trendData.map(d => d.profit || 0);
        const rolling = trendData.map(d => d.rolling_3m_revenue || null);

        const revGradient = ctx.createLinearGradient(0, 0, 0, 320);
        revGradient.addColorStop(0, 'rgba(99, 102, 241, 0.35)');
        revGradient.addColorStop(1, 'rgba(99, 102, 241, 0.0)');

        this.instances[canvasId] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [
                    {
                        type: 'line',
                        label: 'Gross Revenue',
                        data: revenues,
                        borderColor: '#6366f1',
                        backgroundColor: revGradient,
                        fill: true,
                        tension: 0.35,
                        pointRadius: 3,
                        pointHoverRadius: 6,
                        yAxisID: 'y'
                    },
                    {
                        type: 'line',
                        label: 'Rolling 3M Avg',
                        data: rolling,
                        borderColor: '#f59e0b',
                        borderDash: [5, 5],
                        fill: false,
                        tension: 0.35,
                        pointRadius: 0,
                        pointHoverRadius: 4,
                        yAxisID: 'y'
                    },
                    {
                        type: 'bar',
                        label: 'Net Profit',
                        data: profits,
                        backgroundColor: profits.map(p => p >= 0 ? 'rgba(16, 185, 129, 0.75)' : 'rgba(239, 68, 68, 0.75)'),
                        borderRadius: 4,
                        yAxisID: 'y1'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: { mode: 'index', intersect: false },
                scales: {
                    x: { grid: { display: false } },
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: { display: true, text: 'Gross Revenue ($)' },
                        ticks: { callback: (v) => this.formatCurrency(v) }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: { display: true, text: 'Net Profit ($)' },
                        grid: { drawOnChartArea: false },
                        ticks: { callback: (v) => this.formatCurrency(v) }
                    }
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: (ctx) => `${ctx.dataset.label}: ${this.formatCurrency(ctx.parsed.y)}`
                        }
                    }
                }
            }
        });
    }

    renderCategoryDoughnut(canvasId, catData) {
        this.destroyChart(canvasId);
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;
        const ctx = canvas.getContext('2d');

        const labels = catData.map(c => c.category);
        const values = catData.map(c => c.revenue || c.sales || 0);
        const margins = catData.map(c => c.profit_margin || 0);

        const colors = ['#6366f1', '#06b6d4', '#10b981', '#f59e0b', '#ec4899'];

        this.instances[canvasId] = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: values,
                    backgroundColor: colors.slice(0, labels.length),
                    borderWidth: 2,
                    borderColor: 'rgba(15, 23, 42, 0.8)',
                    hoverOffset: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '72%',
                plugins: {
                    legend: { position: 'bottom' },
                    tooltip: {
                        callbacks: {
                            label: (ctx) => {
                                const idx = ctx.dataIndex;
                                return ` Revenue: ${this.formatCurrency(values[idx])} (Margin: ${margins[idx]}%)`;
                            }
                        }
                    }
                }
            }
        });
    }

    renderSubcategoryBar(canvasId, subcatData) {
        this.destroyChart(canvasId);
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;
        const ctx = canvas.getContext('2d');

        const sorted = [...subcatData].sort((a, b) => (b.revenue || 0) - (a.revenue || 0));
        const labels = sorted.map(s => s.sub_category);
        const revenues = sorted.map(s => s.revenue || s.sales || 0);
        const profits = sorted.map(s => s.profit || 0);

        this.instances[canvasId] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Revenue',
                        data: revenues,
                        backgroundColor: 'rgba(99, 102, 241, 0.75)',
                        borderRadius: 4
                    },
                    {
                        label: 'Profit',
                        data: profits,
                        backgroundColor: profits.map(p => p >= 0 ? 'rgba(16, 185, 129, 0.8)' : 'rgba(239, 68, 68, 0.8)'),
                        borderRadius: 4
                    }
                ]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: { ticks: { callback: (v) => this.formatCurrency(v) } },
                    y: { grid: { display: false } }
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: (ctx) => `${ctx.dataset.label}: ${this.formatCurrency(ctx.parsed.x)}`
                        }
                    }
                }
            }
        });
    }

    renderProfitLossDistribution(canvasId, kpiData) {
        this.destroyChart(canvasId);
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;
        const ctx = canvas.getContext('2d');

        const profitable = kpiData.profitable_orders || 0;
        const loss = kpiData.loss_orders || 0;

        this.instances[canvasId] = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Profitable Orders', 'Loss-Making Orders'],
                datasets: [{
                    data: [profitable, loss],
                    backgroundColor: ['#10b981', '#ef4444'],
                    borderColor: 'rgba(15, 23, 42, 0.8)',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '70%',
                plugins: {
                    legend: { position: 'bottom' },
                    tooltip: {
                        callbacks: {
                            label: (ctx) => {
                                const val = ctx.parsed;
                                const tot = profitable + loss;
                                const pct = tot > 0 ? ((val / tot) * 100).toFixed(1) : '0';
                                return ` ${ctx.label}: ${val.toLocaleString()} (${pct}%)`;
                            }
                        }
                    }
                }
            }
        });
    }

    renderRFMPolar(canvasId, rfmData) {
        this.destroyChart(canvasId);
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;
        const ctx = canvas.getContext('2d');

        const labels = rfmData.map(r => r.segment);
        const customers = rfmData.map(r => r.customer_count);
        const colors = [
            'rgba(16, 185, 129, 0.7)',
            'rgba(99, 102, 241, 0.7)',
            'rgba(6, 182, 212, 0.7)',
            'rgba(245, 158, 11, 0.7)',
            'rgba(239, 68, 68, 0.7)',
            'rgba(148, 163, 184, 0.7)'
        ];

        this.instances[canvasId] = new Chart(ctx, {
            type: 'polarArea',
            data: {
                labels: labels,
                datasets: [{
                    data: customers,
                    backgroundColor: colors.slice(0, labels.length)
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'bottom' },
                    tooltip: {
                        callbacks: {
                            label: (ctx) => {
                                const idx = ctx.dataIndex;
                                const item = rfmData[idx];
                                return ` ${item.segment}: ${item.customer_count} accounts (${this.formatCurrency(item.total_revenue)})`;
                            }
                        }
                    }
                }
            }
        });
    }

    renderDiscountImpactChart(canvasId, discountData) {
        this.destroyChart(canvasId);
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;
        const ctx = canvas.getContext('2d');

        const labels = discountData.map(d => d.discount_band);
        const revenues = discountData.map(d => d.revenue || 0);
        const margins = discountData.map(d => d.profit_margin || 0);

        this.instances[canvasId] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [
                    {
                        type: 'bar',
                        label: 'Revenue',
                        data: revenues,
                        backgroundColor: 'rgba(99, 102, 241, 0.7)',
                        borderRadius: 4,
                        yAxisID: 'y'
                    },
                    {
                        type: 'line',
                        label: 'Profit Margin (%)',
                        data: margins,
                        borderColor: '#ef4444',
                        backgroundColor: 'transparent',
                        pointBackgroundColor: '#ef4444',
                        pointRadius: 4,
                        tension: 0.3,
                        yAxisID: 'y1'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: { mode: 'index', intersect: false },
                scales: {
                    x: { grid: { display: false } },
                    y: {
                        type: 'linear',
                        position: 'left',
                        ticks: { callback: (v) => this.formatCurrency(v) }
                    },
                    y1: {
                        type: 'linear',
                        position: 'right',
                        grid: { drawOnChartArea: false },
                        ticks: { callback: (v) => `${v}%` }
                    }
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: (ctx) => {
                                if (ctx.dataset.yAxisID === 'y1') return `Margin: ${ctx.parsed.y}%`;
                                return `Revenue: ${this.formatCurrency(ctx.parsed.y)}`;
                            }
                        }
                    }
                }
            }
        });
    }

    renderGeographyBar(canvasId, geoData) {
        this.destroyChart(canvasId);
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;
        const ctx = canvas.getContext('2d');

        const top10 = geoData.slice(0, 10);
        const labels = top10.map(g => g.country);
        const revenues = top10.map(g => g.revenue || g.sales || 0);
        const profits = top10.map(g => g.profit || 0);

        this.instances[canvasId] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Revenue',
                        data: revenues,
                        backgroundColor: 'rgba(6, 182, 212, 0.75)',
                        borderRadius: 4
                    },
                    {
                        label: 'Profit',
                        data: profits,
                        backgroundColor: 'rgba(16, 185, 129, 0.8)',
                        borderRadius: 4
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: { grid: { display: false } },
                    y: { ticks: { callback: (v) => this.formatCurrency(v) } }
                }
            }
        });
    }

    renderForecastChart(canvasId, forecastData) {
        this.destroyChart(canvasId);
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;
        const ctx = canvas.getContext('2d');

        const points = forecastData.data || [];
        const labels = points.map(p => p.period);
        const actuals = points.map(p => p.actual);
        const forecasts = points.map(p => p.forecast);
        const lowers = points.map(p => p.lower_bound);
        const uppers = points.map(p => p.upper_bound);

        this.instances[canvasId] = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Actual Historical',
                        data: actuals,
                        borderColor: '#6366f1',
                        backgroundColor: 'rgba(99, 102, 241, 0.1)',
                        fill: false,
                        pointRadius: 2.5,
                        tension: 0.3
                    },
                    {
                        label: 'Projected Forecast',
                        data: forecasts,
                        borderColor: '#10b981',
                        borderDash: [5, 5],
                        backgroundColor: 'transparent',
                        pointRadius: 4,
                        tension: 0.3
                    },
                    {
                        label: 'Upper 95% Confidence',
                        data: uppers,
                        borderColor: 'transparent',
                        backgroundColor: 'rgba(16, 185, 129, 0.12)',
                        fill: '+1',
                        pointRadius: 0
                    },
                    {
                        label: 'Lower 95% Confidence',
                        data: lowers,
                        borderColor: 'transparent',
                        backgroundColor: 'transparent',
                        fill: false,
                        pointRadius: 0
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: { ticks: { callback: (v) => this.formatCurrency(v) } }
                }
            }
        });
    }
}

window.chartManager = new ChartManager();
