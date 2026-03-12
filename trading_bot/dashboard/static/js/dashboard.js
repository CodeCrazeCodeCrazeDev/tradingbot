// Dashboard JavaScript

// WebSocket connection
let ws;
function connectWebSocket() {
    ws = new WebSocket('ws://' + window.location.host + '/ws/market_data');
    ws.onmessage = handleMarketData;
    ws.onclose = () => {
        console.log('WebSocket closed. Reconnecting...');
        setTimeout(connectWebSocket, 1000);
    };
}
connectWebSocket();

// Initialize GridJS tables
const positionsGrid = new gridjs.Grid({
    columns: ['Symbol', 'Direction', 'Size', 'Entry', 'Current', 'P/L', 'Actions'],
    sort: true,
    search: true,
    resizable: true
}).render(document.getElementById('positionsGrid'));

const marketDataGrid = new gridjs.Grid({
    columns: ['Symbol', 'Bid', 'Ask', 'Last', 'Volume'],
    sort: true,
    search: true,
    resizable: true
}).render(document.getElementById('marketDataGrid'));

// Initialize performance chart
const performanceChart = new Chart(
    document.getElementById('performanceChart'),
    {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Daily P/L',
                data: [],
                borderColor: 'rgb(75, 192, 192)',
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    }
);

// Health status indicators
const healthIndicators = {
    MT5_CONNECTION: createHealthIndicator('MT5 Connection'),
    DATA_PIPELINE: createHealthIndicator('Data Pipeline'),
    STRATEGY_ENGINE: createHealthIndicator('Strategy Engine'),
    RISK_MANAGER: createHealthIndicator('Risk Manager'),
    ORDER_EXECUTOR: createHealthIndicator('Order Executor')
};

function createHealthIndicator(name) {
    const container = document.createElement('div');
    container.className = 'health-indicator mb-2';
    container.innerHTML = `
        <span class="health-name">${name}</span>
        <span class="health-status badge bg-secondary">Unknown</span>
    `;
    document.getElementById('healthMetrics').appendChild(container);
    return container.querySelector('.health-status');
}

// Update functions
async function updateSystemStatus() {
    try {
        const response = await fetch('/api/system/status');
        const data = await response.json();
        
        // Update health indicators
        Object.entries(data.health).forEach(([component, status]) => {
            if (healthIndicators[component]) {
                const badge = healthIndicators[component];
                badge.className = 'health-status badge ' + getStatusClass(status);
                badge.textContent = status;
            }
        });
        
        // Update system status badge
        const systemBadge = document.getElementById('systemStatus');
        const overallHealth = determineOverallHealth(data.health);
        systemBadge.className = 'badge ' + getStatusClass(overallHealth);
        systemBadge.textContent = `System ${overallHealth}`;
        
    } catch (error) {
        console.error('Error updating system status:', error);
    }
}

async function updatePositions() {
    try {
        const response = await fetch('/api/trading/positions');
        const data = await response.json();
        
        const positions = Object.entries(data.positions).map(([symbol, pos]) => [
            symbol,
            pos.direction > 0 ? 'Long' : 'Short',
            pos.size.toFixed(2),
            pos.entry_price.toFixed(5),
            pos.current_price.toFixed(5),
            pos.pnl.toFixed(2),
            createPositionActions(symbol)
        ]);
        
        positionsGrid.updateConfig({
            data: positions
        }).forceRender();
        
    } catch (error) {
        console.error('Error updating positions:', error);
    }
}

async function updatePerformance() {
    try {
        const response = await fetch('/api/trading/performance');
        const data = await response.json();
        
        // Update performance chart
        performanceChart.data.labels = Object.keys(data.daily_pnl);
        performanceChart.data.datasets[0].data = Object.values(data.daily_pnl);
        performanceChart.update();
        
    } catch (error) {
        console.error('Error updating performance:', error);
    }
}

function handleMarketData(event) {
    const data = JSON.parse(event.data);
    
    // Update market data grid
    const marketData = Object.entries(data.market_data).map(([symbol, md]) => [
        symbol,
        md.bid.toFixed(5),
        md.ask.toFixed(5),
        md.last.toFixed(5),
        md.volume
    ]);
    
    marketDataGrid.updateConfig({
        data: marketData
    }).forceRender();
}

async function updateAlerts() {
    try {
        const response = await fetch('/api/alerts');
        const data = await response.json();
        
        const alertsContainer = document.getElementById('alertsContainer');
        alertsContainer.innerHTML = data.alerts.map(alert => `
            <div class="alert alert-${getAlertClass(alert.level)} alert-dismissible fade show">
                <strong>${alert.level}:</strong> ${alert.message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `).join('');
        
    } catch (error) {
        console.error('Error updating alerts:', error);
    }
}

// Helper functions
function getStatusClass(status) {
    switch (status) {
        case 'HEALTHY': return 'bg-success';
        case 'DEGRADED': return 'bg-warning';
        case 'CRITICAL': return 'bg-danger';
        default: return 'bg-secondary';
    }
}

function getAlertClass(level) {
    switch (level) {
        case 'CRITICAL': return 'danger';
        case 'WARNING': return 'warning';
        case 'INFO': return 'info';
        default: return 'secondary';
    }
}

function determineOverallHealth(healthMetrics) {
    if (Object.values(healthMetrics).includes('CRITICAL')) return 'CRITICAL';
    if (Object.values(healthMetrics).includes('DEGRADED')) return 'DEGRADED';
    return 'HEALTHY';
}

function createPositionActions(symbol) {
    return gridjs.html(`
        <div class="btn-group btn-group-sm">
            <button class="btn btn-danger" onclick="closePosition('${symbol}')">Close</button>
            <button class="btn btn-warning" onclick="modifyPosition('${symbol}')">Modify</button>
        </div>
    `);
}

// Action handlers
async function closePosition(symbol) {
    try {
        const response = await fetch(`/api/position/close/${symbol}`, {
            method: 'POST'
        });
        const data = await response.json();
        if (data.status === 'success') {
            showNotification('success', `Closing position for ${symbol}`);
        }
    } catch (error) {
        console.error('Error closing position:', error);
        showNotification('error', 'Failed to close position');
    }
}

async function closeAllPositions() {
    try {
        const response = await fetch('/api/position/close_all', {
            method: 'POST'
        });
        const data = await response.json();
        if (data.status === 'success') {
            showNotification('success', 'Closing all positions');
        }
    } catch (error) {
        console.error('Error closing all positions:', error);
        showNotification('error', 'Failed to close positions');
    }
}

async function setTradingMode(mode) {
    try {
        const response = await fetch(`/api/trading/mode/${mode}`, {
            method: 'POST'
        });
        const data = await response.json();
        if (data.status === 'success') {
            showNotification('success', `Trading mode set to ${mode}`);
        }
    } catch (error) {
        console.error('Error setting trading mode:', error);
        showNotification('error', 'Failed to set trading mode');
    }
}

function showNotification(type, message) {
    // Implement notification system (e.g., toast notifications)
    console.log(`${type}: ${message}`);
}

// Update intervals
setInterval(updateSystemStatus, 5000);
setInterval(updatePositions, 1000);
setInterval(updatePerformance, 60000);
setInterval(updateAlerts, 10000);

// Initial updates
updateSystemStatus();
updatePositions();
updatePerformance();
updateAlerts();
