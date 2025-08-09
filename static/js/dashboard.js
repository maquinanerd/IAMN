// static/js/dashboard.js
document.addEventListener('DOMContentLoaded', function() {
    const API_PREFIX = '/api';

    // Helper function to update text content of an element
    const updateText = (id, text) => {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = text;
        } else {
            console.warn(`Element with id "${id}" not found.`);
        }
    };

    // Helper function to update status indicators
    const updateStatusIndicator = (id, isOnline) => {
        const element = document.getElementById(id);
        if (element) {
            element.classList.remove('text-success', 'text-danger', 'text-warning');
            if (isOnline === true) {
                element.textContent = 'Online';
                element.classList.add('text-success');
            } else if (isOnline === false) {
                element.textContent = 'Offline';
                element.classList.add('text-danger');
            } else {
                element.textContent = 'Verificando...';
                element.classList.add('text-warning');
            }
        }
    };

    // Fetch and display system statistics
    function fetchStats() {
        fetch(`${API_PREFIX}/stats`)
            .then(response => response.json())
            .then(data => {
                if (data.error) throw new Error(data.error);
                updateText('stat-total', data.total_articles);
                updateText('stat-pending', data.pending_articles);
                updateText('stat-processing', data.processing_articles);
                updateText('stat-processed', data.processed_articles);
                updateText('stat-published', data.published_articles);
                updateText('stat-failed', data.failed_articles);
                updateText('stat-today-published', data.today_published);
            })
            .catch(error => console.error('Error fetching stats:', error));
    }

    // Fetch and display AI status
    function fetchAiStatus() {
        fetch(`${API_PREFIX}/ai-status`)
            .then(response => response.json())
            .then(data => {
                if (data.error) throw new Error(data.error);
                const container = document.getElementById('ai-status-container');
                if (!container) return;
                container.innerHTML = ''; // Clear previous content
                Object.entries(data).forEach(([key, value]) => {
                    const statusDiv = document.createElement('div');
                    statusDiv.className = 'd-flex justify-content-between align-items-center mb-1';
                    statusDiv.innerHTML = `
                        <span class="text-capitalize">${key} Keys:</span>
                        <span class="badge bg-primary rounded-pill">${value.available_keys}</span>
                    `;
                    container.appendChild(statusDiv);
                });
            })
            .catch(error => console.error('Error fetching AI status:', error));
    }

    // Fetch and display Scheduler status
    function fetchSchedulerStatus() {
        fetch(`${API_PREFIX}/scheduler-status`)
            .then(response => response.json())
            .then(data => {
                if (data.error) throw new Error(data.error);
                updateStatusIndicator('scheduler-status', data.running);
                const nextRunElement = document.getElementById('scheduler-next-run');
                if (nextRunElement && data.jobs.length > 0 && data.jobs[0].next_run) {
                    const nextRun = new Date(data.jobs[0].next_run).toLocaleString();
                    nextRunElement.textContent = `Próxima Execução: ${nextRun}`;
                }
            })
            .catch(error => console.error('Error fetching scheduler status:', error));
    }

    // Fetch and display WordPress status
    function fetchWordPressStatus() {
        updateStatusIndicator('wordpress-status', null); // Set to 'Verificando...'
        fetch(`${API_PREFIX}/wordpress-test`)
            .then(response => response.json())
            .then(data => {
                if (data.error) throw new Error(data.error);
                updateStatusIndicator('wordpress-status', data.connected);
            })
            .catch(error => {
                console.error('Error fetching WordPress status:', error);
                updateStatusIndicator('wordpress-status', false);
            });
    }

    // Fetch and display recent articles
    function fetchRecentArticles() {
        fetch(`${API_PREFIX}/recent-articles?limit=10`)
            .then(response => response.json())
            .then(data => {
                if (data.error) throw new Error(data.error);
                const tbody = document.getElementById('recent-articles-tbody');
                if (!tbody) return;
                tbody.innerHTML = ''; // Clear previous content
                data.forEach(article => {
                    const statusBadges = { 'pending': 'bg-secondary', 'processing': 'bg-info', 'processed': 'bg-primary', 'published': 'bg-success', 'failed': 'bg-danger' };
                    const statusClass = statusBadges[article.status] || 'bg-dark';
                    
                    // Display error message if it exists
                    let errorCell = '-';
                    if (article.status === 'failed' && article.error_message) {
                        // Show a snippet of the error and the full error on hover
                        const shortError = article.error_message.substring(0, 40) + (article.error_message.length > 40 ? '...' : '');
                        errorCell = `<small class="text-danger" title="${article.error_message}">${shortError}</small>`;
                    }
                    const row = `<tr><td>${article.id}</td><td title="${article.title}">${article.title.substring(0, 40)}...</td><td><span class="badge ${statusClass}">${article.status}</span></td><td>${article.feed_type}</td><td>${new Date(article.created_at).toLocaleString()}</td><td>${errorCell}</td></tr>`;
                    tbody.innerHTML += row;
                });
            })
            .catch(error => console.error('Error fetching recent articles:', error));
    }

    // Function to load frequently updated data
    function loadFrequentData() {
        fetchStats();
        fetchAiStatus();
        fetchSchedulerStatus();
        fetchRecentArticles();
    }

    // Function to load infrequently updated data
    function loadInfrequentData() {
        fetchWordPressStatus();
    }

});