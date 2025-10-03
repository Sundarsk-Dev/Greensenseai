// Chart.js instance
let emissionChart = null;

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    console.log('🌱 GreenPulse AI Dashboard Initialized');
    
    // Setup refresh button
    const refreshBtn = document.getElementById('refresh-btn');
    refreshBtn.addEventListener('click', fetchData);
    
    // Initial data load
    fetchData();
});

// Fetch emission data from backend
function fetchData() {
    showLoading();
    
    fetch('/api/refresh-data')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateCurrentScore(data.current);
                updatePrediction(data.prediction);
                updateChart(data.historical);
                updateTimestamp();
                checkAlerts(data.current.score);
                resetRefreshButton();
            } else {
                showError('Failed to fetch data');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showError('Network error. Please try again.');
        });
}

// Update current emission score
function updateCurrentScore(current) {
    const scoreElement = document.getElementById('current-score');
    const statusElement = document.getElementById('current-status');
    
    scoreElement.textContent = current.score.toFixed(2);
    scoreElement.className = `score-value ${current.color}`;
    
    statusElement.textContent = current.status;
    statusElement.className = `score-status ${current.color}`;
    
    document.getElementById('co-value').textContent = current.co.toFixed(2);
    document.getElementById('nox-value').textContent = current.nox.toFixed(1);
    document.getElementById('no2-value').textContent = current.no2.toFixed(1);
    document.getElementById('temp-value').textContent = current.temp.toFixed(1);
}

// Update prediction
function updatePrediction(prediction) {
    const scoreElement = document.getElementById('predicted-score');
    const statusElement = document.getElementById('predicted-status');
    
    scoreElement.textContent = prediction.score.toFixed(2);
    scoreElement.className = `predicted-value ${prediction.color}`;
    
    statusElement.textContent = prediction.status;
    statusElement.className = `predicted-status ${prediction.color}`;
}

// Update historical chart
function updateChart(historicalData) {
    const ctx = document.getElementById('emissionChart').getContext('2d');
    
    if (emissionChart) {
        emissionChart.destroy();
    }
    
    const labels = historicalData.map(d => d.time);
    const scores = historicalData.map(d => d.score);
    
    const gradient = ctx.createLinearGradient(0, 0, 0, 400);
    gradient.addColorStop(0, 'rgba(16, 185, 129, 0.5)');
    gradient.addColorStop(1, 'rgba(16, 185, 129, 0.0)');
    
    emissionChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Emission Score',
                data: scores,
                borderColor: '#10b981',
                backgroundColor: gradient,
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointRadius: 3,
                pointHoverRadius: 6,
                pointBackgroundColor: '#10b981',
                pointBorderColor: '#fff',
                pointBorderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: 'rgba(15, 23, 42, 0.9)',
                    titleColor: '#f1f5f9',
                    bodyColor: '#f1f5f9',
                    borderColor: '#334155',
                    borderWidth: 1,
                    padding: 12,
                    displayColors: false,
                    callbacks: {
                        label: function(context) {
                            return 'Score: ' + context.parsed.y.toFixed(2);
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        color: 'rgba(51, 65, 85, 0.3)',
                        drawBorder: false
                    },
                    ticks: {
                        color: '#94a3b8',
                        maxRotation: 45,
                        minRotation: 45
                    }
                },
                y: {
                    min: 0,
                    max: 10,
                    grid: {
                        color: 'rgba(51, 65, 85, 0.3)',
                        drawBorder: false
                    },
                    ticks: {
                        color: '#94a3b8',
                        callback: function(value) {
                            return value.toFixed(1);
                        }
                    }
                }
            },
            interaction: {
                intersect: false,
                mode: 'index'
            }
        }
    });
}

// Check for alerts
function checkAlerts(score) {
    const alertBanner = document.getElementById('alert-banner');
    const alertMessage = document.getElementById('alert-message');
    
    if (score < 4.0) {
        alertMessage.textContent = `⚠️ High emission levels detected! Current score: ${score.toFixed(2)}`;
        alertBanner.classList.remove('hidden');
    } else {
        alertBanner.classList.add('hidden');
    }
}

// Update timestamp
function updateTimestamp() {
    const now = new Date();
    const timeString = now.toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
    document.getElementById('last-update').textContent = timeString;
}

// Show loading state
function showLoading() {
    const refreshBtn = document.getElementById('refresh-btn');
    refreshBtn.disabled = true;
    refreshBtn.innerHTML = '<span class="refresh-icon">⏳</span> Loading...';
}

// Show error message
function showError(message) {
    alert('Error: ' + message);
    resetRefreshButton();
}

// Reset refresh button
function resetRefreshButton() {
    const refreshBtn = document.getElementById('refresh-btn');
    refreshBtn.disabled = false;
    refreshBtn.innerHTML = '<span class="refresh-icon">🔄</span> Refresh Data';
}