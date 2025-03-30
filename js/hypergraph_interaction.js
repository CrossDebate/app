/**
 * hypergraph_interaction.js
 *
 * Handles the visualization and interaction with the Hypergraph of Thoughts (HoT)
 * on the analise.html page.
 * - Fetches HoT data from the backend.
 * - Renders the hypergraph using D3.js (example implementation).
 * - Handles user selection of nodes/hyperedges.
 * - Allows users to adjust parameters via controls.
 * - Sends adjustments back to the backend API.
 * - Updates visualization based on backend data.
 */

document.addEventListener('DOMContentLoaded', () => {
    console.log("Hypergraph interaction script loaded.");

    // --- DOM Element References ---
    const visualizationContainer = document.getElementById('hypergraph-visualization');
    const loadingSpinner = visualizationContainer ? visualizationContainer.querySelector('.loading-spinner') : null;
    const selectedElementInfo = document.getElementById('selectedElementInfo');
    const edgeWeightSlider = document.getElementById('edgeWeightSlider');
    const edgeWeightValue = document.getElementById('edgeWeightValue');
    const nodeRelevanceSlider = document.getElementById('nodeRelevanceSlider');
    const nodeRelevanceValue = document.getElementById('nodeRelevanceValue');
    const layoutForceSlider = document.getElementById('layoutForceSlider');
    const layoutForceValue = document.getElementById('layoutForceValue');
    const applyChangesButton = document.getElementById('applyHoTChanges');
    const resetButton = document.getElementById('resetHoTView');
    const metricsContainer = document.getElementById('hot-metrics');
    const insightsContainer = document.getElementById('hot-insights');

    // --- State Variables ---
    let currentHotData = null; // Stores the latest HoT data from backend
    let selectedElement = null; // { type: 'node'/'edge', id: '...' }
    let simulation = null; // D3 force simulation instance
    let svg = null; // D3 SVG element
    let linkElements = null, nodeElements = null, textElements = null; // D3 selections

    // --- D3 Setup (Basic Example) ---
    const width = visualizationContainer ? visualizationContainer.clientWidth : 800;
    const height = visualizationContainer ? visualizationContainer.clientHeight : 500;

    const setupD3 = () => {
        if (!visualizationContainer) return;
        visualizationContainer.innerHTML = ''; // Clear previous content/spinner

        svg = d3.select(visualizationContainer)
            .append("svg")
            .attr("width", width)
            .attr("height", height)
            .attr("viewBox", [-width / 2, -height / 2, width, height])
            .call(d3.zoom().on("zoom", (event) => {
                svg.attr("transform", event.transform);
            }))
            .append("g");

        // Define arrow markers for directed edges (if needed)
        svg.append('defs').append('marker')
            .attr('id', 'arrowhead')
            .attr('viewBox', '-0 -5 10 10')
            .attr('refX', 15) // Adjust based on node size
            .attr('refY', 0)
            .attr('orient', 'auto')
            .attr('markerWidth', 6)
            .attr('markerHeight', 6)
            .attr('xoverflow', 'visible')
            .append('svg:path')
            .attr('d', 'M 0,-5 L 10 ,0 L 0,5')
            .attr('fill', '#999')
            .style('stroke', 'none');

        // Create selections for links, nodes, text
        linkElements = svg.append("g")
            .attr("class", "links")
            .selectAll("line");

        nodeElements = svg.append("g")
            .attr("class", "nodes")
            .selectAll("circle");

        textElements = svg.append("g")
            .attr("class", "texts")
            .selectAll("text");

        // Initialize force simulation
        simulation = d3.forceSimulation()
            .force("link", d3.forceLink().id(d => d.id).distance(100).strength(0.5)) // Initial strength
            .force("charge", d3.forceManyBody().strength(-150))
            .force("center", d3.forceCenter(0, 0))
            .force("x", d3.forceX())
            .force("y", d3.forceY())
            .on("tick", ticked);
    };

    // --- D3 Update Functions ---
    const ticked = () => {
        linkElements
            .attr("x1", d => d.source.x)
            .attr("y1", d => d.source.y)
            .attr("x2", d => d.target.x)
            .attr("y2", d => d.target.y);

        nodeElements
            .attr("cx", d => d.x)
            .attr("cy", d => d.y);

        textElements
            .attr("x", d => d.x + 12) // Offset text slightly
            .attr("y", d => d.y + 4);
    };

    const updateVisualization = (hotData) => {
        if (!svg || !simulation) {
            console.error("D3 setup not complete.");
            return;
        }
        if (!hotData || !hotData.nodes || !hotData.edges) {
            console.warn("Invalid or empty HoT data received for update.");
            // Optionally clear the visualization
             svg.selectAll("*").remove();
            return;
        }

        currentHotData = hotData; // Store the latest data

        // --- Data Transformation for D3 Force Layout ---
        // D3 force layout works best with nodes and simple source-target links.
        // Representing hyperedges directly is complex. This is a *simplification*
        // where we might represent hyperedges by connecting all nodes within them,
        // or by creating 'dummy' nodes for hyperedges.
        // **This part needs significant refinement based on the desired hypergraph visualization.**
        // For now, let's assume a simplified graph structure derived from HoT.

        const nodes = hotData.nodes.map(n => ({ id: n.id, label: n.label || n.id, ...n })); // Use node ID and add other attributes
        const links = [];
        hotData.edges.forEach(edge => {
            // Simple pairwise links for demonstration
            const edgeNodes = edge.nodes;
            if (edgeNodes.length >= 2) {
                for (let i = 0; i < edgeNodes.length; i++) {
                    for (let j = i + 1; j < edgeNodes.length; j++) {
                        links.push({ source: edgeNodes[i], target: edgeNodes[j], weight: edge.weight || 0.5, id: edge.id });
                    }
                }
            }
            // Alternative: Create a dummy node for the hyperedge and link nodes to it.
        });

        // --- Update D3 Selections ---
        // Update Nodes
        nodeElements = nodeElements.data(nodes, d => d.id);
        nodeElements.exit().remove();
        nodeElements = nodeElements.enter().append("circle")
            .attr("class", "node")
            .attr("r", 8) // Base size
            .attr("fill", "var(--secondary-color)")
            .attr("stroke", "#fff")
            .attr("stroke-width", 1.5)
            .call(drag(simulation)) // Add drag behavior
            .on("click", nodeClicked)
            .merge(nodeElements);

        // Update Text Labels
        textElements = textElements.data(nodes, d => d.id);
        textElements.exit().remove();
        textElements = textElements.enter().append("text")
             .attr("class", "node-label")
             .text(d => d.label)
             .attr("font-size", "10px")
             .attr("fill", "var(--text-color)")
             .attr("dx", 12)
             .attr("dy", ".35em")
             .merge(textElements);

        // Update Links
        linkElements = linkElements.data(links, d => `${d.source.id}-${d.target.id}`); // Use source-target as key
        linkElements.exit().remove();
        linkElements = linkElements.enter().append("line")
            .attr("class", "link")
            .attr("stroke", "var(--border-color)")
            .attr("stroke-opacity", 0.6)
            .attr("stroke-width", d => Math.sqrt(d.weight || 0.5) * 2) // Example: width based on weight
            // .attr('marker-end', 'url(#arrowhead)') // Add arrows if directed
            .on("click", linkClicked)
            .merge(linkElements);

        // Update simulation
        simulation.nodes(nodes);
        simulation.force("link").links(links);
        simulation.alpha(1).restart(); // Restart simulation with new data

        console.log("Hypergraph visualization updated.");
        if (loadingSpinner) loadingSpinner.style.display = 'none';
    };

    // --- D3 Drag Handling ---
    const drag = (simulationInstance) => {
        function dragstarted(event, d) {
            if (!event.active) simulationInstance.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
        }
        function dragged(event, d) {
            d.fx = event.x;
            d.fy = event.y;
        }
        function dragended(event, d) {
            if (!event.active) simulationInstance.alphaTarget(0);
            d.fx = null;
            d.fy = null;
        }
        return d3.drag()
            .on("start", dragstarted)
            .on("drag", dragged)
            .on("end", dragended);
    };

    // --- Event Handlers ---
    const nodeClicked = (event, d) => {
        event.stopPropagation(); // Prevent triggering background click
        console.log("Node clicked:", d);
        selectElement('node', d.id, d);
    };

    const linkClicked = (event, d) => {
         event.stopPropagation();
         // For simplicity, we treat link clicks as selecting the associated hyperedge (if applicable)
         // This needs refinement based on how hyperedges are represented.
         // If links represent pairwise connections within a hyperedge, find the hyperedge ID.
         const edgeId = d.id; // Assuming the link data has the original hyperedge ID
         if (edgeId) {
            console.log("Link clicked (Hyperedge):", edgeId, d);
            const edgeData = currentHotData.edges.find(e => e.id === edgeId);
            selectElement('edge', edgeId, edgeData);
         }
    };

    const backgroundClicked = () => {
        console.log("Background clicked");
        deselectElement();
    };

    // Add background click listener to SVG
    if (svg) {
        svg.on("click", backgroundClicked);
    }

    const selectElement = (type, id, data) => {
        selectedElement = { type, id, data };
        if (selectedElementInfo) selectedElementInfo.textContent = `${type}: ${id}`;

        // Reset styles
        nodeElements.classed("selected", false);
        linkElements.classed("selected", false);

        // Highlight selected
        if (type === 'node') {
            d3.select(event.target).classed("selected", true); // Highlight the clicked circle
            if (nodeRelevanceSlider) {
                nodeRelevanceSlider.disabled = false;
                nodeRelevanceSlider.value = data.relevance || 0.5; // Use actual relevance if available
                if (nodeRelevanceValue) nodeRelevanceValue.textContent = nodeRelevanceSlider.value;
            }
            if (edgeWeightSlider) edgeWeightSlider.disabled = true;
        } else if (type === 'edge') {
             // Highlight all links belonging to this hyperedge (needs better mapping)
             linkElements.filter(l => l.id === id).classed("selected", true);
            if (edgeWeightSlider) {
                edgeWeightSlider.disabled = false;
                edgeWeightSlider.value = data.weight || 0.5; // Use actual weight
                if (edgeWeightValue) edgeWeightValue.textContent = edgeWeightSlider.value;
            }
            if (nodeRelevanceSlider) nodeRelevanceSlider.disabled = true;
        }

        if (applyChangesButton) applyChangesButton.disabled = false;
    };

    const deselectElement = () => {
        selectedElement = null;
        if (selectedElementInfo) selectedElementInfo.textContent = 'Nenhum';
        if (edgeWeightSlider) edgeWeightSlider.disabled = true;
        if (nodeRelevanceSlider) nodeRelevanceSlider.disabled = true;
        if (applyChangesButton) applyChangesButton.disabled = true;

        // Remove highlight
        nodeElements.classed("selected", false);
        linkElements.classed("selected", false);
    };

    // --- Control Listeners ---
    if (edgeWeightSlider && edgeWeightValue) {
        edgeWeightSlider.addEventListener('input', () => {
            edgeWeightValue.textContent = edgeWeightSlider.value;
        });
    }
    if (nodeRelevanceSlider && nodeRelevanceValue) {
        nodeRelevanceSlider.addEventListener('input', () => {
            nodeRelevanceValue.textContent = nodeRelevanceSlider.value;
        });
    }
     if (layoutForceSlider && layoutForceValue && simulation) {
        layoutForceSlider.addEventListener('input', () => {
            const forceValue = parseFloat(layoutForceSlider.value);
            layoutForceValue.textContent = forceValue.toFixed(1);
            // Adjust simulation forces (example: charge strength)
            simulation.force("charge", d3.forceManyBody().strength(forceValue * -300));
            simulation.alpha(0.3).restart(); // Reheat simulation
        });
    }

    if (applyChangesButton) {
        applyChangesButton.addEventListener('click', async () => {
            if (!selectedElement) return;

            const adjustmentData = {
                element_id: selectedElement.id,
                element_type: selectedElement.type,
            };

            if (selectedElement.type === 'edge' && edgeWeightSlider) {
                adjustmentData.new_weight = parseFloat(edgeWeightSlider.value);
            } else if (selectedElement.type === 'node' && nodeRelevanceSlider) {
                adjustmentData.new_relevance = parseFloat(nodeRelevanceSlider.value);
            } else {
                return; // No relevant value to adjust
            }

            console.log("Applying HoT changes:", adjustmentData);
            applyChangesButton.disabled = true; // Disable while processing
            applyChangesButton.textContent = "Aplicando...";

            try {
                const response = await fetch('/api/hot/adjust', { // Backend endpoint
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(adjustmentData)
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
                }

                const result = await response.json();
                console.log("HoT adjustment result:", result);
                if (typeof showNotification === 'function') {
                    showNotification('Ajustes do Hipergrafo aplicados com sucesso!', 'success');
                }
                // Optionally, fetch updated HoT data and re-render
                // await fetchHotData();
                deselectElement(); // Deselect after applying

            } catch (error) {
                console.error("Erro ao aplicar ajustes do HoT:", error);
                 if (typeof showNotification === 'function') {
                    showNotification(`Erro ao aplicar ajustes: ${error.message}`, 'error');
                 }
            } finally {
                 applyChangesButton.textContent = "Aplicar Ajustes";
                 // Re-enable button only if an element is still selected? Or always re-enable?
                 if (selectedElement) applyChangesButton.disabled = false;
            }
        });
    }

    if (resetButton) {
        resetButton.addEventListener('click', () => {
            console.log("Resetting HoT view...");
            // Option 1: Reset D3 simulation forces/zoom
            if (simulation) {
                 simulation.alpha(1).restart();
            }
             if (svg) {
                 svg.transition().duration(750).call(
                     d3.zoom().transform,
                     d3.zoomIdentity // Reset zoom
                 );
             }
            // Option 2: Re-fetch data and re-render
            // fetchHotData();
            deselectElement();
        });
    }

    // --- Data Fetching ---
    const fetchHotData = async () => {
        console.log("Fetching HoT data...");
        if (loadingSpinner) loadingSpinner.style.display = 'block';
        try {
            const response = await fetch('/api/hot/current'); // Backend endpoint
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const data = await response.json();
            console.log("HoT data received:", data);
            if (data && data.nodes && data.edges) {
                 updateVisualization(data); // Update D3 visualization
            } else {
                 console.warn("Received invalid HoT data structure from backend.");
                 if (loadingSpinner) loadingSpinner.style.display = 'none';
                 if (typeof showNotification === 'function') {
                    showNotification("Não foi possível carregar os dados do hipergrafo.", 'warning');
                 }
            }
        } catch (error) {
            console.error("Erro ao buscar dados do HoT:", error);
            if (loadingSpinner) loadingSpinner.style.display = 'none';
            if (typeof showNotification === 'function') {
                showNotification(`Erro ao carregar hipergrafo: ${error.message}`, 'error');
            }
             // Display error message in the visualization area
             if(visualizationContainer) visualizationContainer.innerHTML = `<p style='color: var(--danger-color); padding: 20px;'>Erro ao carregar visualização.</p>`;
        }
    };

    const fetchMetricsAndInsights = async () => {
         console.log("Fetching HoT metrics and insights...");
         if (metricsContainer) metricsContainer.innerHTML = '<p>Carregando...</p>';
         if (insightsContainer) insightsContainer.innerHTML = '<p>Carregando...</p>';
         try {
            const metricsResponse = await fetch('/api/hot/metrics');
            const insightsResponse = await fetch('/api/hot/insights');

            if (!metricsResponse.ok || !insightsResponse.ok) {
                throw new Error("Failed to fetch metrics or insights");
            }

            const metricsData = await metricsResponse.json();
            const insightsData = await insightsResponse.json();

            // Display Metrics (Example)
            if (metricsContainer) {
                metricsContainer.innerHTML = `
                    <p><strong>Nós:</strong> ${metricsData.node_count || 'N/A'}</p>
                    <p><strong>Hiperarestas:</strong> ${metricsData.edge_count || 'N/A'}</p>
                    <p><strong>Densidade:</strong> ${metricsData.density?.toFixed(3) || 'N/A'}</p>
                    <p><strong>Centralidade Média:</strong> ${metricsData.avg_centrality?.toFixed(3) || 'N/A'}</p>
                `;
            }

             // Display Insights (Example)
            if (insightsContainer) {
                insightsContainer.innerHTML = insightsData.insights?.map(insight => `<p>- ${insight}</p>`).join('') || '<p>Nenhum insight gerado.</p>';
            }

         } catch (error) {
             console.error("Erro ao buscar métricas/insights:", error);
             if (metricsContainer) metricsContainer.innerHTML = '<p style="color: var(--danger-color);">Erro ao carregar métricas.</p>';
             if (insightsContainer) insightsContainer.innerHTML = '<p style="color: var(--danger-color);">Erro ao carregar insights.</p>';
         }
    };

    // --- Global Function for Updates ---
    // Make updateHypergraph globally accessible so chat.js can call it
    window.updateHypergraph = (newData) => {
        console.log("Global updateHypergraph called with new data.");
        updateVisualization(newData);
        // Optionally fetch new metrics/insights after update
        fetchMetricsAndInsights();
    };

    // --- Initial Load ---
    setupD3(); // Setup SVG and simulation
    fetchHotData(); // Fetch initial data and render
    fetchMetricsAndInsights(); // Fetch initial metrics/insights

}); // End DOMContentLoaded
