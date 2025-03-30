/**
 * visualizations.js
 *
 * Handles fetching data and rendering charts on the visualizacao.html page.
 * Uses Chart.js for rendering.
 */

document.addEventListener('DOMContentLoaded', () => {
    console.log("Visualizations script loaded.");

    // --- DOM Element References ---
    const debateTypeFilter = document.getElementById('debateTypeFilter');
    const timeRangeFilter = document.getElementById('timeRangeFilter');
    const metricFilter = document.getElementById('metricFilter');
    const applyFiltersButton = document.getElementById('applyFiltersButton');

    // Chart canvas elements and spinners
    const chartContexts = {
        engagementChart: document.getElementById('engagementChart')?.getContext('2d'),
        sentimentChart: document.getElementById('sentimentChart')?.getContext('2d'),
        topicDistributionChart: document.getElementById('topicDistributionChart')?.getContext('2d'),
        modelQualityRadarChart: document.getElementById('modelQualityRadarChart')?.getContext('2d'),
        correlationChart: document.getElementById('correlationChart')?.getContext('2d'),
        demographicImpactChart: document.getElementById('demographicImpactChart')?.getContext('2d')
        // Add more contexts if more charts are added
    };

    const chartSpinners = {
        engagementChart: document.getElementById('engagementChartSpinner'),
        sentimentChart: document.getElementById('sentimentChartSpinner'),
        topicDistributionChart: document.getElementById('topicDistributionChartSpinner'),
        modelQualityRadarChart: document.getElementById('modelQualityRadarChartSpinner'),
        correlationChart: document.getElementById('correlationChartSpinner'),
        demographicImpactChart: document.getElementById('demographicImpactChartSpinner')
        // Add more spinners
    };

    // --- Chart Instances ---
    let chartInstances = {}; // To store Chart.js instances for updates

    // --- Helper Functions ---

    /**
     * Shows or hides the loading spinner for a specific chart.
     * @param {string} chartId - The ID of the chart canvas.
     * @param {boolean} show - True to show the spinner, false to hide.
     */
    const toggleSpinner = (chartId, show) => {
        const spinner = chartSpinners[chartId];
        if (spinner) {
            spinner.style.display = show ? 'block' : 'none';
        }
        const canvas = document.getElementById(chartId);
         if (canvas) {
             canvas.style.display = show ? 'none' : 'block'; // Hide canvas when spinner is shown
         }
    };

    /**
     * Fetches visualization data from the backend API based on filters.
     * @param {object} filters - An object containing filter values { debateType, timeRange, metric }.
     * @returns {Promise<object|null>} - A promise resolving to the fetched data or null on error.
     */
    const fetchVisualizationData = async (filters) => {
        // Construct query parameters
        const params = new URLSearchParams(filters).toString();
        const apiUrl = `/api/visualization_data?${params}`; // Adjust API endpoint as needed

        console.log(`Fetching data from: ${apiUrl}`);

        try {
            const response = await fetch(apiUrl);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            console.log("Visualization data received:", data);
            return data;
        } catch (error) {
            console.error("Error fetching visualization data:", error);
            if (typeof showNotification === 'function') {
                showNotification(`Erro ao buscar dados de visualização: ${error.message}`, 'error');
            }
            return null; // Return null to indicate failure
        }
    };

    /**
     * Renders or updates a chart using Chart.js.
     * @param {string} chartId - The ID of the canvas element.
     * @param {string} chartType - Type of chart ('line', 'bar', 'pie', 'radar', 'scatter', etc.).
     * @param {object} chartData - Data object for Chart.js ({ labels: [], datasets: [{ data: [], ... }] }).
     * @param {object} options - Chart.js options object.
     */
    const renderChart = (chartId, chartType, chartData, options = {}) => {
        const ctx = chartContexts[chartId];
        if (!ctx) {
            console.warn(`Canvas context not found for chart ID: ${chartId}`);
            return;
        }

        // Destroy previous instance if it exists
        if (chartInstances[chartId]) {
            chartInstances[chartId].destroy();
        }

        // Default options (can be customized further)
        const defaultOptions = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                     labels: {
                         color: document.body.classList.contains('dark-theme') ? 'rgba(255, 255, 255, 0.8)' : 'rgba(0, 0, 0, 0.8)'
                     }
                },
                title: {
                    display: false, // Title is usually in the card header (h4)
                    // text: options.title || '', // Set title if needed
                     color: document.body.classList.contains('dark-theme') ? 'rgba(255, 255, 255, 0.9)' : 'rgba(0, 0, 0, 0.9)'
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                },
            },
            scales: {
                x: {
                    display: chartType !== 'pie' && chartType !== 'doughnut' && chartType !== 'radar', // Hide x-axis for pie/radar
                    grid: {
                        color: document.body.classList.contains('dark-theme') ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)'
                    },
                    ticks: {
                         color: document.body.classList.contains('dark-theme') ? 'rgba(255, 255, 255, 0.7)' : 'rgba(0, 0, 0, 0.7)'
                    }
                },
                y: {
                    display: chartType !== 'pie' && chartType !== 'doughnut' && chartType !== 'radar', // Hide y-axis for pie/radar
                    beginAtZero: true,
                     grid: {
                        color: document.body.classList.contains('dark-theme') ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)'
                    },
                     ticks: {
                         color: document.body.classList.contains('dark-theme') ? 'rgba(255, 255, 255, 0.7)' : 'rgba(0, 0, 0, 0.7)'
                    }
                },
                 r: { // Specific options for radar charts
                    display: chartType === 'radar',
                     angleLines: {
                         color: document.body.classList.contains('dark-theme') ? 'rgba(255, 255, 255, 0.2)' : 'rgba(0, 0, 0, 0.2)'
                     },
                     grid: {
                         color: document.body.classList.contains('dark-theme') ? 'rgba(255, 255, 255, 0.2)' : 'rgba(0, 0, 0, 0.2)'
                     },
                     pointLabels: {
                         color: document.body.classList.contains('dark-theme') ? 'rgba(255, 255, 255, 0.8)' : 'rgba(0, 0, 0, 0.8)'
                     },
                     ticks: {
                         backdropColor: 'transparent',
                         color: document.body.classList.contains('dark-theme') ? 'rgba(255, 255, 255, 0.6)' : 'rgba(0, 0, 0, 0.6)'
                     }
                 }
            },
            // Merge custom options
            ...options
        };

        try {
            chartInstances[chartId] = new Chart(ctx, {
                type: chartType,
                data: chartData,
                options: defaultOptions
            });
            console.log(`Chart rendered: ${chartId}`);
        } catch (error) {
             console.error(`Error rendering chart ${chartId}:`, error);
             if (typeof showNotification === 'function') {
                showNotification(`Erro ao renderizar gráfico ${chartId}.`, 'error');
             }
        }
    };

    /**
     * Updates all charts based on current filter settings.
     */
    const updateAllCharts = async () => {
        // Show all spinners
        Object.keys(chartSpinners).forEach(id => toggleSpinner(id, true));

        const filters = {
            debateType: debateTypeFilter?.value || 'all',
            timeRange: timeRangeFilter?.value || '24h',
            metric: metricFilter?.value || 'engagement'
        };

        const data = await fetchVisualizationData(filters);

        // Hide all spinners
        Object.keys(chartSpinners).forEach(id => toggleSpinner(id, false));

        if (data) {
            // --- Render each chart with its specific data ---
            // Replace these with actual data structures from your API response

            // Example: Engagement Chart (Line)
            if (data.engagementData) {
                renderChart('engagementChart', 'line', {
                    labels: data.engagementData.labels || [], // e.g., ['Jan', 'Feb', 'Mar']
                    datasets: [{
                        label: 'Engajamento Médio',
                        data: data.engagementData.values || [], // e.g., [65, 59, 80]
                        borderColor: 'rgba(75, 192, 192, 1)', // Teal
                        backgroundColor: 'rgba(75, 192, 192, 0.2)',
                        tension: 0.1,
                        fill: true
                    }]
                });
            } else {
                 console.warn("No data found for engagementChart");
            }

            // Example: Sentiment Chart (Doughnut/Pie)
            if (data.sentimentData) {
                renderChart('sentimentChart', 'doughnut', {
                    labels: data.sentimentData.labels || ['Positivo', 'Negativo', 'Neutro'],
                    datasets: [{
                        label: 'Distribuição de Sentimento',
                        data: data.sentimentData.values || [], // e.g., [50, 30, 20]
                        backgroundColor: [
                            'rgba(40, 167, 69, 0.8)',  // Green
                            'rgba(220, 53, 69, 0.8)',  // Red
                            'rgba(0, 123, 255, 0.8)' // Blue
                        ],
                        hoverOffset: 4
                    }]
                });
            } else {
                 console.warn("No data found for sentimentChart");
            }

            // Example: Topic Distribution (Bar)
            if (data.topicData) {
                 renderChart('topicDistributionChart', 'bar', {
                    labels: data.topicData.labels || [], // e.g., ['Política', 'Economia', 'Tecnologia']
                    datasets: [{
                        label: 'Menções por Tópico',
                        data: data.topicData.values || [], // e.g., [120, 90, 150]
                        backgroundColor: 'rgba(255, 193, 7, 0.8)', // Yellow
                        borderColor: 'rgba(255, 193, 7, 1)',
                        borderWidth: 1
                    }]
                }, { scales: { y: { beginAtZero: true } } }); // Override options if needed
            } else {
                 console.warn("No data found for topicDistributionChart");
            }

             // Example: Model Quality (Radar)
             if (data.modelQualityData) {
                 renderChart('modelQualityRadarChart', 'radar', {
                    labels: data.modelQualityData.labels || ['Acurácia', 'Coerência', 'Relevância', 'Fluência', 'Segurança'],
                    datasets: (data.modelQualityData.datasets || []).map((ds, index) => ({ // Assuming datasets is an array of { label: 'Model A', values: [...] }
                        label: ds.label || `Modelo ${index + 1}`,
                        data: ds.values || [],
                        fill: true,
                        backgroundColor: `rgba(${(index * 60) % 255}, ${(index * 100 + 50) % 255}, ${(index * 150 + 100) % 255}, 0.2)`,
                        borderColor: `rgb(${(index * 60) % 255}, ${(index * 100 + 50) % 255}, ${(index * 150 + 100) % 255})`,
                        pointBackgroundColor: `rgb(${(index * 60) % 255}, ${(index * 100 + 50) % 255}, ${(index * 150 + 100) % 255})`,
                        pointBorderColor: '#fff',
                        pointHoverBackgroundColor: '#fff',
                        pointHoverBorderColor: `rgb(${(index * 60) % 255}, ${(index * 100 + 50) % 255}, ${(index * 150 + 100) % 255})`
                    }))
                }, { elements: { line: { borderWidth: 3 } } }); // Radar specific options
             } else {
                 console.warn("No data found for modelQualityRadarChart");
             }

             // Example: Correlation (Scatter or Bubble)
             if (data.correlationData) {
                 renderChart('correlationChart', 'scatter', {
                    datasets: [{
                        label: 'Correlação Engajamento x Sentimento',
                        data: data.correlationData.points || [], // e.g., [{x: 0.5, y: 0.8}, {x: -0.2, y: 0.3}]
                        backgroundColor: 'rgba(23, 162, 184, 0.6)' // Info color
                    }]
                }, { scales: { x: { type: 'linear', position: 'bottom' }, y: { beginAtZero: false } } });
             } else {
                 console.warn("No data found for correlationChart");
             }

             // Example: Demographic Impact (Could be Radar or Bar)
             if (data.demographicData) {
                 renderChart('demographicImpactChart', 'bar', {
                    labels: data.demographicData.labels || [], // e.g., ['Age 18-24', 'Age 25-34', ...]
                    datasets: [{
                        label: 'Impacto por Grupo',
                        data: data.demographicData.values || [],
                        backgroundColor: 'rgba(108, 117, 125, 0.8)' // Gray
                    }]
                 });
             } else {
                 console.warn("No data found for demographicImpactChart");
             }

        } else {
            // Clear charts if data fetching failed
            Object.keys(chartInstances).forEach(id => {
                if (chartInstances[id]) {
                    chartInstances[id].destroy();
                    chartInstances[id] = null;
                }
                 // Optionally display an error message on the canvas
                 const ctx = chartContexts[id];
                 if (ctx) {
                     ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
                     ctx.fillStyle = document.body.classList.contains('dark-theme') ? '#aaa' : '#555';
                     ctx.textAlign = 'center';
                     ctx.fillText('Erro ao carregar dados.', ctx.canvas.width / 2, ctx.canvas.height / 2);
                 }
            });
        }
    };

    // --- Event Listeners ---
    if (applyFiltersButton) {
        applyFiltersButton.addEventListener('click', updateAllCharts);
    } else {
        console.warn("Apply filters button not found.");
    }

    // Optional: Update charts when theme changes to adjust colors
    const themeToggleButton = document.getElementById('themeToggle');
     if (themeToggleButton) {
         // We need a way to detect theme change. Since interactivity.js handles the
         // class toggle, we can use a MutationObserver or a custom event.
         // Simpler approach: re-render on toggle click (might fetch data again).
         themeToggleButton.addEventListener('click', () => {
             // Small delay to allow theme class to be applied
             setTimeout(updateAllCharts, 100);
         });
     }

    // --- Initial Load ---
    updateAllCharts(); // Load charts with default filters

}); // End DOMContentLoaded
