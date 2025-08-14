/**
 * Advanced Charts JavaScript Library
 * Enhanced visualization components with real-time updates and interactivity
 */

class AdvancedChartManager {
    constructor() {
        this.charts = new Map();
        this.websocket = null;
        this.autoRefreshEnabled = false;
        this.refreshIntervals = new Map();
        this.chartConfigs = new Map();
        
        this.initializeWebSocket();
        this.setupGlobalEventHandlers();
        
        console.log('AdvancedChartManager initialized');
    }
    
    initializeWebSocket() {
        try {
            this.websocket = io({
                transports: ['websocket', 'polling']
            });
            
            this.websocket.on('connect', () => {
                console.log('WebSocket connected for chart updates');
                this.emit('websocket_connected');
            });
            
            this.websocket.on('disconnect', () => {
                console.log('WebSocket disconnected');
                this.emit('websocket_disconnected');
            });
            
            // Handle visualization updates
            this.websocket.on('analytics_update', (data) => {
                if (data.visualization_update && data.chart_type) {
                    this.updateChart(data.chart_type, data.chart_data);
                }
            });
            
        } catch (error) {
            console.error('Failed to initialize WebSocket:', error);
        }
    }
    
    setupGlobalEventHandlers() {
        // Handle window resize
        window.addEventListener('resize', () => {
            this.resizeAllCharts();
        });
        
        // Handle page visibility changes
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.pauseAutoRefresh();
            } else {
                this.resumeAutoRefresh();
            }
        });
    }
    
    /**
     * Create a new chart with advanced configuration
     */
    createChart(containerId, chartType, data, options = {}) {
        try {
            const container = document.getElementById(containerId);
            if (!container) {
                throw new Error(`Container ${containerId} not found`);
            }
            
            // Find or create canvas
            let canvas = container.querySelector('canvas');
            if (!canvas) {
                canvas = document.createElement('canvas');
                container.appendChild(canvas);
            }
            
            const ctx = canvas.getContext('2d');
            
            // Destroy existing chart if it exists
            if (this.charts.has(containerId)) {
                this.charts.get(containerId).destroy();
            }
            
            // Prepare chart configuration
            const config = this.prepareChartConfig(chartType, data, options);
            
            // Create new chart
            const chart = new Chart(ctx, config);
            this.charts.set(containerId, chart);
            this.chartConfigs.set(containerId, { type: chartType, data, options });
            
            // Add interactive features
            this.addChartInteractivity(containerId, chart);
            
            // Emit creation event
            this.emit('chart_created', { containerId, chartType });
            
            return chart;
            
        } catch (error) {
            console.error(`Error creating chart ${containerId}:`, error);
            this.showChartError(containerId, error.message);
            return null;
        }
    }
    
    prepareChartConfig(chartType, data, options) {
        const baseConfig = {
            type: chartType,
            data: data,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    intersect: false,
                    mode: 'index'
                },
                plugins: {
                    legend: {
                        display: options.showLegend !== false,
                        position: options.legendPosition || 'top'
                    },
                    tooltip: {
                        enabled: true,
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#ffffff',
                        bodyColor: '#ffffff',
                        cornerRadius: 6,
                        displayColors: true
                    }
                },
                animation: {
                    duration: options.animation !== false ? 750 : 0,
                    easing: 'easeInOutQuart'
                }
            }
        };
        
        // Add specific configurations based on chart type
        switch (chartType) {
            case 'line':
                this.configureLineChart(baseConfig, options);
                break;
            case 'bar':
                this.configureBarChart(baseConfig, options);
                break;
            case 'pie':
            case 'doughnut':
                this.configurePieChart(baseConfig, options);
                break;
            case 'radar':
                this.configureRadarChart(baseConfig, options);
                break;
            case 'scatter':
                this.configureScatterChart(baseConfig, options);
                break;
            case 'bubble':
                this.configureBubbleChart(baseConfig, options);
                break;
        }
        
        return baseConfig;
    }
    
    configureLineChart(config, options) {
        config.options.scales = {
            x: {
                title: {
                    display: options.xAxisLabel ? true : false,
                    text: options.xAxisLabel || ''
                },
                grid: {
                    color: 'rgba(0, 0, 0, 0.1)'
                }
            },
            y: {
                title: {
                    display: options.yAxisLabel ? true : false,
                    text: options.yAxisLabel || ''
                },
                grid: {
                    color: 'rgba(0, 0, 0, 0.1)'
                }
            }
        };
        
        // Add zoom and pan plugins if available
        if (typeof Chart.Zoom !== 'undefined') {
            config.options.plugins.zoom = {
                pan: {
                    enabled: true,
                    mode: 'x'
                },
                zoom: {
                    enabled: true,
                    mode: 'x'
                }
            };
        }
    }
    
    configureBarChart(config, options) {
        config.options.scales = {
            x: {
                title: {
                    display: options.xAxisLabel ? true : false,
                    text: options.xAxisLabel || ''
                }
            },
            y: {
                title: {
                    display: options.yAxisLabel ? true : false,
                    text: options.yAxisLabel || ''
                },
                beginAtZero: true
            }
        };
        
        if (options.horizontal) {
            config.options.indexAxis = 'y';
        }
    }
    
    configurePieChart(config, options) {
        config.options.plugins.legend.position = 'right';
        config.options.plugins.datalabels = {
            display: options.showDataLabels || false,
            color: '#ffffff',
            font: {
                weight: 'bold'
            },
            formatter: (value, context) => {
                const total = context.chart.data.datasets[0].data.reduce((a, b) => a + b, 0);
                const percentage = ((value / total) * 100).toFixed(1);
                return `${percentage}%`;
            }
        };
    }
    
    configureRadarChart(config, options) {
        config.options.scales = {
            r: {
                beginAtZero: true,
                grid: {
                    color: 'rgba(0, 0, 0, 0.1)'
                }
            }
        };
    }
    
    configureScatterChart(config, options) {
        config.options.scales = {
            x: {
                type: 'linear',
                position: 'bottom',
                title: {
                    display: options.xAxisLabel ? true : false,
                    text: options.xAxisLabel || ''
                }
            },
            y: {
                title: {
                    display: options.yAxisLabel ? true : false,
                    text: options.yAxisLabel || ''
                }
            }
        };
    }
    
    configureBubbleChart(config, options) {
        this.configureScatterChart(config, options);
        config.options.plugins.tooltip.callbacks = {
            label: (context) => {
                const point = context.raw;
                return `${context.dataset.label}: (${point.x}, ${point.y}), Size: ${point.r}`;
            }
        };
    }
    
    addChartInteractivity(containerId, chart) {
        const canvas = chart.canvas;
        
        // Add click handlers
        canvas.addEventListener('click', (event) => {
            const elements = chart.getElementsAtEventForMode(event, 'nearest', { intersect: true }, false);
            if (elements.length > 0) {
                const element = elements[0];
                this.emit('chart_click', {
                    containerId,
                    datasetIndex: element.datasetIndex,
                    index: element.index,
                    value: chart.data.datasets[element.datasetIndex].data[element.index]
                });
            }
        });
        
        // Add hover effects
        canvas.addEventListener('mousemove', (event) => {
            const elements = chart.getElementsAtEventForMode(event, 'nearest', { intersect: false }, false);
            canvas.style.cursor = elements.length > 0 ? 'pointer' : 'default';
        });
    }
    
    /**
     * Update existing chart with new data
     */
    updateChart(containerId, newData) {
        const chart = this.charts.get(containerId);
        if (!chart) {
            console.warn(`Chart ${containerId} not found for update`);
            return false;
        }
        
        try {
            // Update data
            if (newData.labels) {
                chart.data.labels = newData.labels;
            }
            
            if (newData.datasets) {
                chart.data.datasets = newData.datasets;
            }
            
            // Animate update
            chart.update('active');
            
            // Update metadata
            this.updateChartMetadata(containerId);
            
            this.emit('chart_updated', { containerId, newData });
            
            return true;
            
        } catch (error) {
            console.error(`Error updating chart ${containerId}:`, error);
            return false;
        }
    }
    
    /**
     * Refresh chart data from server
     */
    async refreshChart(containerId, chartType) {
        try {
            this.showChartLoading(containerId);
            
            const response = await fetch(`/viz/api/chart/${chartType}`);
            const result = await response.json();
            
            if (result.success) {
                const chart = this.charts.get(containerId);
                if (chart) {
                    chart.data.labels = result.data.labels;
                    chart.data.datasets = result.data.datasets;
                    chart.update();
                    
                    this.updateChartMetadata(containerId, result.data.metadata);
                    this.emit('chart_refreshed', { containerId, chartType });
                }
            } else {
                throw new Error(result.error || 'Failed to refresh chart');
            }
            
        } catch (error) {
            console.error(`Error refreshing chart ${containerId}:`, error);
            this.showChartError(containerId, error.message);
        } finally {
            this.hideChartLoading(containerId);
        }
    }
    
    /**
     * Create gauge chart
     */
    createGaugeChart(containerId, value, maxValue, options = {}) {
        const data = {
            datasets: [{
                data: [value, maxValue - value],
                backgroundColor: [
                    options.color || '#4F46E5',
                    '#E5E7EB'
                ],
                borderWidth: 0,
                cutout: options.cutout || '80%'
            }]
        };
        
        const gaugeOptions = {
            ...options,
            showLegend: false,
            plugins: {
                tooltip: { enabled: false },
                legend: { display: false }
            }
        };
        
        const chart = this.createChart(containerId, 'doughnut', data, gaugeOptions);
        
        // Add center text for gauge value
        if (chart) {
            this.addGaugeCenterText(containerId, value, options.unit || '%');
        }
        
        return chart;
    }
    
    addGaugeCenterText(containerId, value, unit) {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        let centerText = container.querySelector('.gauge-center-text');
        if (!centerText) {
            centerText = document.createElement('div');
            centerText.className = 'gauge-center-text';
            centerText.style.cssText = `
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                text-align: center;
                font-weight: bold;
                pointer-events: none;
            `;
            container.style.position = 'relative';
            container.appendChild(centerText);
        }
        
        centerText.innerHTML = `
            <div style="font-size: 24px; color: #374151;">${value.toFixed(1)}</div>
            <div style="font-size: 14px; color: #6B7280;">${unit}</div>
        `;
    }
    
    /**
     * Auto-refresh functionality
     */
    enableAutoRefresh(containerId, chartType, intervalSeconds) {
        if (this.refreshIntervals.has(containerId)) {
            clearInterval(this.refreshIntervals.get(containerId));
        }
        
        const intervalId = setInterval(() => {
            if (this.autoRefreshEnabled && !document.hidden) {
                this.refreshChart(containerId, chartType);
            }
        }, intervalSeconds * 1000);
        
        this.refreshIntervals.set(containerId, intervalId);
    }
    
    disableAutoRefresh(containerId) {
        if (this.refreshIntervals.has(containerId)) {
            clearInterval(this.refreshIntervals.get(containerId));
            this.refreshIntervals.delete(containerId);
        }
    }
    
    pauseAutoRefresh() {
        this.autoRefreshEnabled = false;
    }
    
    resumeAutoRefresh() {
        this.autoRefreshEnabled = true;
    }
    
    /**
     * Chart utilities
     */
    resizeAllCharts() {
        this.charts.forEach((chart, containerId) => {
            try {
                chart.resize();
            } catch (error) {
                console.warn(`Error resizing chart ${containerId}:`, error);
            }
        });
    }
    
    destroyChart(containerId) {
        const chart = this.charts.get(containerId);
        if (chart) {
            chart.destroy();
            this.charts.delete(containerId);
            this.chartConfigs.delete(containerId);
            this.disableAutoRefresh(containerId);
        }
    }
    
    destroyAllCharts() {
        this.charts.forEach((chart, containerId) => {
            this.destroyChart(containerId);
        });
    }
    
    /**
     * UI helpers
     */
    showChartLoading(containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        let overlay = container.querySelector('.chart-loading-overlay');
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.className = 'chart-loading-overlay';
            overlay.style.cssText = `
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(255, 255, 255, 0.8);
                display: flex;
                justify-content: center;
                align-items: center;
                z-index: 10;
            `;
            overlay.innerHTML = '<div class="spinner-border text-primary" role="status"></div>';
            container.style.position = 'relative';
            container.appendChild(overlay);
        }
        
        overlay.style.display = 'flex';
    }
    
    hideChartLoading(containerId) {
        const container = document.getElementById(containerId);
        if (container) {
            const overlay = container.querySelector('.chart-loading-overlay');
            if (overlay) {
                overlay.style.display = 'none';
            }
        }
    }
    
    showChartError(containerId, message) {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        let errorDiv = container.querySelector('.chart-error-message');
        if (!errorDiv) {
            errorDiv = document.createElement('div');
            errorDiv.className = 'chart-error-message';
            errorDiv.style.cssText = `
                text-align: center;
                padding: 40px 20px;
                color: #6B7280;
                background: #F9FAFB;
                border-radius: 8px;
                margin: 20px;
            `;
            container.appendChild(errorDiv);
        }
        
        errorDiv.innerHTML = `
            <i class="bi bi-exclamation-triangle" style="font-size: 2rem; color: #EF4444; margin-bottom: 10px;"></i>
            <h6>Chart Error</h6>
            <p class="mb-0 small">${message}</p>
        `;
    }
    
    updateChartMetadata(containerId, metadata = null) {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        let metadataEl = container.querySelector('.chart-metadata');
        if (!metadataEl) {
            metadataEl = document.createElement('div');
            metadataEl.className = 'chart-metadata';
            metadataEl.style.cssText = `
                position: absolute;
                bottom: 8px;
                right: 8px;
                font-size: 11px;
                color: #9CA3AF;
                background: rgba(255, 255, 255, 0.8);
                padding: 2px 6px;
                border-radius: 4px;
            `;
            container.style.position = 'relative';
            container.appendChild(metadataEl);
        }
        
        const timestamp = metadata?.generated_at || new Date().toISOString();
        metadataEl.textContent = `Updated: ${new Date(timestamp).toLocaleTimeString()}`;
    }
    
    /**
     * Event system
     */
    emit(eventName, data = {}) {
        const event = new CustomEvent(`chart_${eventName}`, { detail: data });
        document.dispatchEvent(event);
    }
    
    on(eventName, callback) {
        document.addEventListener(`chart_${eventName}`, (event) => {
            callback(event.detail);
        });
    }
    
    /**
     * Export functionality
     */
    exportChart(containerId, format = 'png') {
        const chart = this.charts.get(containerId);
        if (!chart) return null;
        
        const canvas = chart.canvas;
        const link = document.createElement('a');
        
        switch (format.toLowerCase()) {
            case 'png':
                link.download = `chart-${containerId}-${Date.now()}.png`;
                link.href = canvas.toDataURL('image/png');
                break;
            case 'jpg':
                link.download = `chart-${containerId}-${Date.now()}.jpg`;
                link.href = canvas.toDataURL('image/jpeg', 0.9);
                break;
            case 'svg':
                // SVG export would require additional library
                console.warn('SVG export not supported yet');
                return null;
            default:
                console.warn(`Unsupported export format: ${format}`);
                return null;
        }
        
        link.click();
        return link.href;
    }
    
    exportAllCharts(format = 'png') {
        this.charts.forEach((chart, containerId) => {
            this.exportChart(containerId, format);
        });
    }
}

// Global instance
window.chartManager = new AdvancedChartManager();

// Helper functions for backward compatibility
window.createAdvancedChart = (containerId, chartType, data, options) => {
    return window.chartManager.createChart(containerId, chartType, data, options);
};

window.updateAdvancedChart = (containerId, newData) => {
    return window.chartManager.updateChart(containerId, newData);
};

window.refreshAdvancedChart = (containerId, chartType) => {
    return window.chartManager.refreshChart(containerId, chartType);
};

console.log('Advanced Charts library loaded successfully');