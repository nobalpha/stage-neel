/**
 * European Grid Simulator - Frontend Application
 * Interactive visualization and control for the electric grid simulation
 */

// ========================================
// Configuration & State
// ========================================
const API_BASE = "";

const state = {
    map: null,
    nodeLayer: null,
    edgeLayer: null,
    buses: [],
    lines: [],
    graphData: null,
    simulationData: null,
    charts: {
        kappa: null,
        beta: null,
        resistance: null,
        psi: null,
    },
    selects: {
        busIn: null,
        busOut: null,
        removeLine: null,
        removeNode: null,
    },
};

// Viridis color scale (matching Python's viridis)
const viridisColors = [
    "#440154",
    "#482878",
    "#3e4989",
    "#31688e",
    "#26838f",
    "#1f9e89",
    "#35b779",
    "#6ece58",
    "#b5de2b",
    "#fde725",
];

function getViridisColor(value) {
    // value should be between 0 and 1
    const clampedValue = Math.max(0, Math.min(1, value));
    const index = Math.floor(clampedValue * (viridisColors.length - 1));
    return viridisColors[index];
}

// ========================================
// Initialization
// ========================================
document.addEventListener("DOMContentLoaded", () => {
    initMap();
    initCharts();
    initSelects();
    initEventListeners();
    loadInitialData();
});

function initMap() {
    // Create map centered on Europe
    state.map = L.map("map", {
        center: [50, 10],
        zoom: 4,
        zoomControl: true,
    });

    // Add dark tile layer
    L.tileLayer(
        "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        {
            attribution:
                '&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a> &copy; <a href="https://carto.com/attributions">CARTO</a>',
            subdomains: "abcd",
            maxZoom: 19,
        },
    ).addTo(state.map);

    // Initialize layers
    state.edgeLayer = L.layerGroup().addTo(state.map);
    state.nodeLayer = L.layerGroup().addTo(state.map);
}

function initCharts() {
    const chartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { display: false },
        },
        scales: {
            x: {
                grid: { color: "rgba(255,255,255,0.1)" },
                ticks: { color: "#a0a0a0", font: { size: 9 } },
            },
            y: {
                grid: { color: "rgba(255,255,255,0.1)" },
                ticks: { color: "#a0a0a0", font: { size: 9 } },
            },
        },
    };

    // Kappa Chart
    state.charts.kappa = new Chart(document.getElementById("kappaChart"), {
        type: "line",
        data: {
            labels: [],
            datasets: [
                {
                    label: "κ²",
                    data: [],
                    borderColor: "#3498db",
                    borderWith: 1,
                    backgroundColor: "rgba(52, 152, 219, 0.2)",
                    fill: true,
                    pointStyle: false,
                    tension: 0.3,
                },
                {
                    label: "Σκ²",
                    data: [],
                    borderWith: 1,
                    borderColor: "#e74c3c",
                    pointStyle: false,
                    backgroundColor: "transparent",
                    borderDash: [5, 5],
                    tension: 0.3,
                },
            ],
        },
        options: {
            ...chartOptions,
            plugins: {
                ...chartOptions.plugins,
                legend: {
                    display: true,
                    labels: { color: "#a0a0a0", font: { size: 9 } },
                },
            },
        },
    });

    // Beta Chart
    state.charts.beta = new Chart(document.getElementById("betaChart"), {
        type: "line",
        data: {
            labels: [],
            datasets: [
                {
                    label: "β",
                    data: [],
                    pointStyle: false,
                    borderColor: "#27ae60",
                    backgroundColor: "rgba(39, 174, 96, 0.2)",
                    fill: true,
                    tension: 0.1,
                },
            ],
        },
        options: chartOptions,
    });

    // Resistance Chart
    state.charts.resistance = new Chart(
        document.getElementById("resistanceChart"),
        {
            type: "line",
            data: {
                labels: [],
                datasets: [
                    {
                        label: "R_eff",
                        data: [],
                        pointStyle: false,
                        borderColor: "#f39c12",
                        backgroundColor: "rgba(243, 156, 18, 0.2)",
                        fill: true,
                        tension: 0.3,
                    },
                ],
            },
            options: chartOptions,
        },
    );

    // Psi Chart
    state.charts.psi = new Chart(document.getElementById("psiChart"), {
        type: "line",
        data: {
            labels: [],
            datasets: [
                {
                    label: "ψ²",
                    data: [],
                    pointStyle: false,
                    borderColor: "#9b59b6",
                    backgroundColor: "rgba(155, 89, 182, 0.2)",
                    fill: true,
                    tension: 0.3,
                },
            ],
        },
        options: chartOptions,
    });
}

function initSelects() {
    // Bus In Select
    state.selects.busIn = new TomSelect("#busInSelect", {
        valueField: "id",
        labelField: "label",
        searchField: ["id", "country"],
        options: [],
        placeholder: "Select input bus...",
        render: {
            option: (data, escape) =>
                `<div><strong>${escape(data.id)}</strong> <span style="color:#888">(${escape(data.country)})</span></div>`,
        },
    });

    // Bus Out Select
    state.selects.busOut = new TomSelect("#busOutSelect", {
        valueField: "id",
        labelField: "label",
        searchField: ["id", "country"],
        options: [],
        placeholder: "Select output bus...",
        render: {
            option: (data, escape) =>
                `<div><strong>${escape(data.id)}</strong> <span style="color:#888">(${escape(data.country)})</span></div>`,
        },
    });

    // Remove Line Select
    state.selects.removeLine = new TomSelect("#removeLineSelect", {
        valueField: "id",
        labelField: "label",
        searchField: ["id"],
        options: [],
        placeholder: "Select line to remove...",
    });

    // Remove Node Select
    state.selects.removeNode = new TomSelect("#removeNodeSelect", {
        valueField: "id",
        labelField: "label",
        searchField: ["id", "country"],
        options: [],
        placeholder: "Select node to remove...",
    });
}

function initEventListeners() {
    document
        .getElementById("simulateBtn")
        .addEventListener("click", runSimulation);
    document.getElementById("resetBtn").addEventListener("click", resetGrid);
    document
        .getElementById("applyEndpointsBtn")
        .addEventListener("click", applyEndpoints);
    document
        .getElementById("removeLineBtn")
        .addEventListener("click", removeLine);
    document
        .getElementById("removeNodeBtn")
        .addEventListener("click", removeNode);
}

// ========================================
// API Calls
// ========================================
async function apiCall(endpoint, method = "GET", data = null) {
    const options = {
        method,
        headers: { "Content-Type": "application/json" },
    };

    if (data) {
        options.body = JSON.stringify(data);
    }

    const response = await fetch(`${API_BASE}${endpoint}`, options);
    return response.json();
}

async function loadInitialData() {
    showLoading(true);

    try {
        // Load buses list
        const busesResponse = await apiCall("/api/get_buses");
        if (busesResponse.success) {
            state.buses = busesResponse.buses;
            updateBusSelects();
        }

        // Initialize grid and run simulation
        const initResponse = await apiCall("/api/init", "POST", {});
        if (initResponse.success) {
            updateVisualization(initResponse);
            updateLineSelect();
        } else {
            console.error("Init failed:", initResponse.error);
        }
    } catch (error) {
        console.error("Error loading initial data:", error);
    }

    showLoading(false);
}

async function runSimulation() {
    showLoading(true);

    try {
        const response = await apiCall("/api/simulate", "POST");
        if (response.success) {
            updateVisualization(response);
        } else {
            alert("Simulation failed: " + response.error);
        }
    } catch (error) {
        console.error("Simulation error:", error);
        alert("Simulation error: " + error.message);
    }

    showLoading(false);
}

async function resetGrid() {
    showLoading(true);

    try {
        const response = await apiCall("/api/reset", "POST");
        if (response.success) {
            updateVisualization(response);
            updateRemovedList([]);
        }
    } catch (error) {
        console.error("Reset error:", error);
    }

    showLoading(false);
}

async function applyEndpoints() {
    const busIn = state.selects.busIn.getValue();
    const busOut = state.selects.busOut.getValue();

    if (!busIn || !busOut) {
        alert("Please select both input and output buses");
        return;
    }

    if (busIn === busOut) {
        alert("Input and output buses must be different");
        return;
    }

    showLoading(true);

    try {
        const response = await apiCall("/api/set_endpoints", "POST", {
            bus_in: busIn,
            bus_out: busOut,
        });

        if (response.success) {
            updateVisualization(response);
        } else {
            alert("Failed to apply endpoints: " + response.error);
        }
    } catch (error) {
        console.error("Error applying endpoints:", error);
    }

    showLoading(false);
}

async function removeLine() {
    const lineId = state.selects.removeLine.getValue();
    if (!lineId) {
        alert("Please select a line to remove");
        return;
    }

    showLoading(true);

    try {
        const response = await apiCall("/api/remove_line", "POST", {
            line_id: lineId,
        });

        if (response.success) {
            updateVisualization(response);
            state.selects.removeLine.clear();
            updateLineSelect();
            fetchAndUpdateStats();
        } else {
            alert("Failed to remove line: " + response.error);
        }
    } catch (error) {
        console.error("Error removing line:", error);
    }

    showLoading(false);
}

async function removeNode() {
    const nodeId = state.selects.removeNode.getValue();
    if (!nodeId) {
        alert("Please select a node to remove");
        return;
    }

    showLoading(true);

    try {
        const response = await apiCall("/api/remove_node", "POST", {
            node_id: nodeId,
        });

        if (response.success) {
            updateVisualization(response);
            state.selects.removeNode.clear();
            updateNodeSelect();
            fetchAndUpdateStats();
        } else {
            alert("Failed to remove node: " + response.error);
        }
    } catch (error) {
        console.error("Error removing node:", error);
    }

    showLoading(false);
}

async function fetchAndUpdateStats() {
    try {
        const response = await apiCall("/api/simulation_stats");
        if (response.success) {
            updateStats(response.stats);
            updateRemovedList([
                ...response.stats.removed_lines.map((l) => ({
                    id: l,
                    type: "line",
                })),
                ...response.stats.removed_nodes.map((n) => ({
                    id: n,
                    type: "node",
                })),
            ]);
        }
    } catch (error) {
        console.error("Error fetching stats:", error);
    }
}

// ========================================
// Visualization Updates
// ========================================
function updateVisualization(response) {
    state.graphData = response.graph;
    state.simulationData = response.simulation;

    updateMap();
    updateCharts();
    updateStats({
        num_nodes: response.graph.nodes.filter((n) => n.type === "node").length,
        num_lines: response.graph.nodes.filter((n) => n.type === "line").length,
        avg_beta: response.simulation?.betas
            ? response.simulation.betas.reduce((a, b) => a + b, 0) /
              response.simulation.betas.length
            : 0,
        avg_resistance: response.simulation?.effective_resistances
            ? response.simulation.effective_resistances.reduce(
                  (a, b) => a + b,
                  0,
              ) / response.simulation.effective_resistances.length
            : 0,
    });
    updateNodeSelect();
    updateLineSelect();
}

function updateMap() {
    const { nodes, edges, max_weight } = state.graphData;

    // Clear existing layers
    state.edgeLayer.clearLayers();
    state.nodeLayer.clearLayers();

    // Create node lookup for edges
    const nodeMap = {};
    nodes.forEach((node) => {
        nodeMap[node.id] = node;
    });

    // Draw edges
    edges.forEach((edge) => {
        const source = nodeMap[edge.source];
        const target = nodeMap[edge.target];

        if (source && target) {
            const polyline = L.polyline(
                [
                    [source.lat, source.lon],
                    [target.lat, target.lon],
                ],
                {
                    color: "#555",
                    weight: 1,
                    opacity: 0.5,
                },
            );
            state.edgeLayer.addLayer(polyline);
        }
    });

    // Draw nodes
    nodes.forEach((node) => {
        const isInput = node.is_input;
        const isOutput = node.is_output;
        const isLine = node.type === "line";

        // Determine color and size
        let color, radius;

        if (isInput) {
            color = "#00ff00";
            radius = 12;
        } else if (isOutput) {
            color = "#ff0000";
            radius = 12;
        } else if (isLine) {
            color = getViridisColor(node.normalized_weight);
            radius = 4;
        } else {
            color = getViridisColor(node.normalized_weight);
            radius = 6;
        }

        const marker = L.circleMarker([node.lat, node.lon], {
            radius: radius,
            fillColor: color,
            fillOpacity: 0.9,
            color: isInput || isOutput ? "#fff" : color,
            weight: isInput || isOutput ? 2 : 1,
        });

        // Add popup
        const popupContent = `
            <div class="node-popup">
                <h4>${node.id}</h4>
                <p><strong>Type:</strong> ${node.type}</p>
                <p><strong>Weight:</strong> <span class="weight-value">${node.weight.toFixed(6)}</span></p>
                ${node.country !== "N/A" ? `<p><strong>Country:</strong> ${node.country}</p>` : ""}
                ${
                    !isInput && !isOutput
                        ? `
                    <button class="btn btn-danger btn-sm" onclick="removeElementFromPopup('${node.id}', '${node.type}')">
                        Remove
                    </button>
                `
                        : ""
                }
            </div>
        `;

        marker.bindPopup(popupContent);
        state.nodeLayer.addLayer(marker);
    });
}

function updateCharts() {
    if (!state.simulationData) return;

    const { kappas, betas, psi_squared, effective_resistances } =
        state.simulationData;

    // Update Kappa Chart
    if (kappas && kappas.length > 0) {
        const kappaSq = kappas.map((k) => k * k);
        const kappaSum = kappaSq.reduce((acc, val, i) => {
            acc.push((acc[i - 1] || 0) + val);
            return acc;
        }, []);

        state.charts.kappa.data.labels = kappas.map((_, i) => i + 1);
        state.charts.kappa.data.datasets[0].data = kappaSq;
        state.charts.kappa.data.datasets[1].data = kappaSum;
        state.charts.kappa.update();
    }

    // Update Beta Chart
    if (betas && betas.length > 0) {
        state.charts.beta.data.labels = betas.map((_, i) => i + 1);
        state.charts.beta.data.datasets[0].data = betas;
        state.charts.beta.update();
    }

    // Update Resistance Chart
    if (effective_resistances && effective_resistances.length > 0) {
        state.charts.resistance.data.labels = effective_resistances.map(
            (_, i) => i + 1,
        );
        state.charts.resistance.data.datasets[0].data = effective_resistances;
        state.charts.resistance.update();
    }

    // Update Psi Chart
    if (psi_squared && psi_squared.length > 0) {
        state.charts.psi.data.labels = psi_squared.map((_, i) => i + 1);
        state.charts.psi.data.datasets[0].data = psi_squared;
        state.charts.psi.update();
    }
}

function updateStats(stats) {
    document.getElementById("statNodes").textContent = stats.num_nodes || "-";
    document.getElementById("statLines").textContent = stats.num_lines || "-";
    document.getElementById("statBeta").textContent = stats.avg_beta
        ? stats.avg_beta.toFixed(4)
        : "-";
    document.getElementById("statResistance").textContent = stats.avg_resistance
        ? stats.avg_resistance.toFixed(4)
        : "-";
}

function updateBusSelects() {
    const busOptions = state.buses.map((bus) => ({
        id: bus.id,
        label: `${bus.id} (${bus.country})`,
        country: bus.country,
    }));

    state.selects.busIn.clearOptions();
    state.selects.busIn.addOptions(busOptions);

    state.selects.busOut.clearOptions();
    state.selects.busOut.addOptions(busOptions);
}

function updateLineSelect() {
    if (!state.graphData) return;

    const lineOptions = state.graphData.nodes
        .filter((n) => n.type === "line")
        .map((line) => ({
            id: line.id,
            label: `${line.id} (w: ${line.weight.toFixed(4)})`,
        }));

    state.selects.removeLine.clearOptions();
    state.selects.removeLine.addOptions(lineOptions);
}

function updateNodeSelect() {
    if (!state.graphData) return;

    const nodeOptions = state.graphData.nodes
        .filter((n) => n.type === "node" && !n.is_input && !n.is_output)
        .map((node) => ({
            id: node.id,
            label: `${node.id} (${node.country})`,
            country: node.country,
        }));

    state.selects.removeNode.clearOptions();
    state.selects.removeNode.addOptions(nodeOptions);
}

function updateRemovedList(items) {
    const container = document.getElementById("removedList");

    if (items.length === 0) {
        container.innerHTML =
            '<p class="empty-message">No elements removed</p>';
        return;
    }

    container.innerHTML = items
        .map(
            (item) => `
        <div class="removed-item">
            <span>${item.id}</span>
            <span class="type-badge ${item.type}">${item.type}</span>
        </div>
    `,
        )
        .join("");
}

// ========================================
// Utility Functions
// ========================================
function showLoading(show) {
    const overlay = document.getElementById("loadingOverlay");
    if (show) {
        overlay.classList.add("active");
    } else {
        overlay.classList.remove("active");
    }
}

// Global function for popup button
window.removeElementFromPopup = async function (id, type) {
    showLoading(true);
    state.map.closePopup();

    try {
        const endpoint =
            type === "line" ? "/api/remove_line" : "/api/remove_node";
        const payload = type === "line" ? { line_id: id } : { node_id: id };

        const response = await apiCall(endpoint, "POST", payload);

        if (response.success) {
            updateVisualization(response);
            fetchAndUpdateStats();
        } else {
            alert("Failed to remove element: " + response.error);
        }
    } catch (error) {
        console.error("Error removing element:", error);
    }

    showLoading(false);
};
