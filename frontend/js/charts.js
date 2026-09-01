class ChartManager {
    constructor() {
        this.instances = {};
        this.setupDefaults();
    }

    setupDefaults() {
        Chart.defaults.font.family = "'Plus Jakarta Sans', sans-serif";
        Chart.defaults.color = '#94a3b8';
        Chart.defaults.borderColor = 'rgba(255, 255, 255, 0.08)';
        Chart.defaults.plugins.legend.labels.usePointStyle = true;
    }

    destroyChart(chartKey) {
        if (this.instances[chartKey]) {
            this.instances[chartKey].destroy();
            delete this.instances[chartKey];
        }
    }

    renderOverviewTrendChart(canvasId, trendData) {
        this.destroyChart(canvasId);
        const ctx = document.getElementById(canvasId)?.getContext('2d');
        if (!ctx) return;

        const labels = trendData.map(d => d.year_month);
        const sales = trendData.map(d => d.sales);
        const profit = trendData.map(d => d.profit);

        const salesGradient = ctx.createLinearGradient(0, 0, 0, 300);
        salesGradient.addColorStop(0, 'rgba(99, 102, 241, 0.4)');
        salesGradient.addColorStop(1, 'rgba(99, 102, 241, 0.0)');

        this.instances[canvasId] = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Sales Revenue',
                        data: sales,
                        borderColor: '#6366f1',
                        backgroundColor: salesGradient,
                        fill: true,
                        tension: 0.35,
                        pointRadius: 3,
                        pointHoverRadius: 6,
                        yAxisID: 'y'
                    },
                    {
                        label: 'Net Profit',
                        data: profit,
                        borderColor: '#10b981',
                        backgroundColor: 'transparent',
                        borderDash: [4, 4],
                        tension: 0.35,
                        pointRadius: 3,
                        pointHoverRadius: 6,
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
                        ticks: { callback: v => Utils.formatCompactCurrency(v) }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        grid: { drawOnChartArea: false },
                        ticks: { callback: v => Utils.formatCompactCurrency(v) }
                    }
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: ctx => `${ctx.dataset.label}: ${Utils.formatCurrency(ctx.parsed.y)}`
                        }
                    }
                }
            }
        });
    }

    renderCategoryDoughnut(canvasId, categoryData) {
        this.destroyChart(canvasId);
        const ctx = document.getElementById(canvasId)?.getContext('2d');
        if (!ctx) return;

        const labels = categoryData.map(c => c.category);
        const sales = categoryData.map(c => c.sales);
        const colors = ['#6366f1', '#10b981', '#f59e0b', '#06b6d4', '#ec4899'];

        this.instances[canvasId] = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: sales,
                    backgroundColor: colors.slice(0, labels.length),
                    borderWidth: 2,
                    borderColor: 'rgba(15, 23, 42, 0.6)'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'bottom' },
                    tooltip: {
                        callbacks: {
                            label: ctx => ` ${ctx.label}: ${Utils.formatCurrency(ctx.parsed)}`
                        }
                    }
                },
                cutout: '70%'
            }
        });
    }

    renderSubCategoryBarChart(canvasId, categoryData) {
        this.destroyChart(canvasId);
        const ctx = document.getElementById(canvasId)?.getContext('2d');
        if (!ctx) return;

        let subCats = [];
        categoryData.forEach(c => {
            if (c.sub_categories) subCats.push(...c.sub_categories);
        });
        subCats = subCats.sort((a, b) => b.sales - a.sales);

        const labels = subCats.map(sc => sc.sub_category);
        const sales = subCats.map(sc => sc.sales);
        const profits = subCats.map(sc => sc.profit);

        this.instances[canvasId] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Sales ($)',
                        data: sales,
                        backgroundColor: 'rgba(99, 102, 241, 0.85)',
                        borderRadius: 4
                    },
                    {
                        label: 'Profit ($)',
                        data: profits,
                        backgroundColor: profits.map(p => p >= 0 ? 'rgba(16, 185, 129, 0.85)' : 'rgba(239, 68, 68, 0.85)'),
                        borderRadius: 4
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                scales: {
                    x: { ticks: { callback: v => Utils.formatCompactCurrency(v) } }
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: ctx => ` ${ctx.dataset.label}: ${Utils.formatCurrency(ctx.parsed.x)}`
                        }
                    }
                }
            }
        });
    }

    renderRegionalBarChart(canvasId, regionalData) {
        this.destroyChart(canvasId);
        const ctx = document.getElementById(canvasId)?.getContext('2d');
        if (!ctx) return;

        const labels = regionalData.map(r => r.region);
        const sales = regionalData.map(r => r.sales);
        const profit = regionalData.map(r => r.profit);

        this.instances[canvasId] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Revenue',
                        data: sales,
                        backgroundColor: '#6366f1',
                        borderRadius: 6
                    },
                    {
                        label: 'Profit',
                        data: profit,
                        backgroundColor: '#10b981',
                        borderRadius: 6
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: { ticks: { callback: v => Utils.formatCompactCurrency(v) } }
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: ctx => ` ${ctx.dataset.label}: ${Utils.formatCurrency(ctx.parsed.y)}`
                        }
                    }
                }
            }
        });
    }

    renderCustomerSegmentChart(canvasId, segments) {
        this.destroyChart(canvasId);
        const ctx = document.getElementById(canvasId)?.getContext('2d');
        if (!ctx) return;

        const labels = segments.map(s => s.segment);
        const sales = segments.map(s => s.sales);

        this.instances[canvasId] = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: sales,
                    backgroundColor: ['#6366f1', '#10b981', '#06b6d4', '#f59e0b'],
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'bottom' },
                    tooltip: {
                        callbacks: {
                            label: ctx => ` ${ctx.label}: ${Utils.formatCurrency(ctx.parsed)}`
                        }
                    }
                }
            }
        });
    }

    renderRFMCohortChart(canvasId, rfmData) {
        this.destroyChart(canvasId);
        const ctx = document.getElementById(canvasId)?.getContext('2d');
        if (!ctx) return;

        const labels = rfmData.map(r => r.segment);
        const counts = rfmData.map(r => r.customer_count);

        this.instances[canvasId] = new Chart(ctx, {
            type: 'polarArea',
            data: {
                labels: labels,
                datasets: [{
                    data: counts,
                    backgroundColor: [
                        'rgba(16, 185, 129, 0.7)',
                        'rgba(99, 102, 241, 0.7)',
                        'rgba(245, 158, 11, 0.7)',
                        'rgba(239, 68, 68, 0.7)'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'bottom' }
                }
            }
        });
    }

    renderForecastChart(canvasId, forecastResponse) {
        this.destroyChart(canvasId);
        const ctx = document.getElementById(canvasId)?.getContext('2d');
        if (!ctx) return;

        const points = forecastResponse.data || [];
        const labels = points.map(p => p.period);
        const actuals = points.map(p => p.actual);
        const forecasts = points.map(p => p.forecast);
        const upper = points.map(p => p.upper_bound);
        const lower = points.map(p => p.lower_bound);

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
                        tension: 0.3,
                        pointRadius: 4
                    },
                    {
                        label: 'Forecast Trajectory',
                        data: forecasts,
                        borderColor: '#8b5cf6',
                        borderDash: [5, 5],
                        backgroundColor: 'transparent',
                        tension: 0.3,
                        pointRadius: 4
                    },
                    {
                        label: 'Upper 95% Bound',
                        data: upper,
                        borderColor: 'transparent',
                        backgroundColor: 'rgba(139, 92, 246, 0.15)',
                        fill: '+1',
                        pointRadius: 0
                    },
                    {
                        label: 'Lower 95% Bound',
                        data: lower,
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
                    y: { ticks: { callback: v => Utils.formatCompactCurrency(v) } }
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: ctx => ` ${ctx.dataset.label}: ${Utils.formatCurrency(ctx.parsed.y)}`
                        }
                    }
                }
            }
        });
    }
}

const charts = new ChartManager();
