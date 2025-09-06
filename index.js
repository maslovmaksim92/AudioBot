// Simple frontend to display logs and dashboard
// This will be served as static file by FastAPI

document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 VasDom AI Assistant Dashboard loaded');
    
    // Auto-refresh dashboard every 30 seconds
    setInterval(loadDashboard, 30000);
    loadDashboard();
});

async function loadDashboard() {
    try {
        const response = await fetch('/dashboard');
        const data = await response.json();
        
        updateDashboard(data);
    } catch (error) {
        console.error('Error loading dashboard:', error);
    }
}

function updateDashboard(data) {
    const container = document.getElementById('dashboard-container');
    if (!container) return;
    
    container.innerHTML = `
        <div class="dashboard">
            <h1>🤖 AI-Ассистент ВасДом - Дашборд</h1>
            <div class="status">
                <h2>📊 Статус системы</h2>
                <p>Всего запросов: ${data.system_status?.total_requests || 0}</p>
                <p>Telegram updates: ${data.system_status?.telegram_updates || 0}</p>
                <p>Ошибки: ${data.system_status?.errors || 0}</p>
            </div>
            <div class="logs">
                <h2>📋 Последние логи</h2>
                ${data.recent_logs?.map(log => `
                    <div class="log-entry ${log.level}">
                        <span class="timestamp">${log.timestamp}</span>
                        <span class="message">${log.message}</span>
                    </div>
                `).join('') || 'Нет логов'}
            </div>
        </div>
    `;
}