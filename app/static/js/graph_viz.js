/**
 * Graph Visualization JavaScript
 * Uses Cytoscape.js for interactive graph visualization
 */

let cy = null;
let deckData = null;

// Interaction type colors
const INTERACTION_COLORS = {
    'combos_with': '#FF6B6B',
    'enables': '#4ECDC4',
    'synergy': '#45B7D1',
    'protects': '#96CEB4',
    'buffs': '#FFEAA7',
    'tutors': '#DDA0DD',
    'mana_enables': '#F7DC6F',
    'draws_into': '#85C1E9',
    'tribal': '#F39C12',
    'type_matters': '#9B59B6',
    'sacrifice_fodder': '#E74C3C',
    'sacrifice_outlet': '#C0392B',
    'counter_synergy': '#2ECC71',
    'etb_chain': '#1ABC9C',
    'death_chain': '#34495E'
};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadDecks();
    initControls();
    initLegend();
});

// ============================================================================
// Load Decks
// ============================================================================

async function loadDecks() {
    const select = document.getElementById('deck-select');

    try {
        const data = await api('/decks');

        if (data.decks && data.decks.length > 0) {
            data.decks.forEach(deck => {
                const option = document.createElement('option');
                option.value = deck.id;
                option.textContent = `${deck.name} (${deck.card_count} cards)`;
                select.appendChild(option);
            });
        }

        select.addEventListener('change', async (e) => {
            if (e.target.value) {
                await loadDeckGraph(e.target.value);
            }
        });

        // Check if we have a deck ID in the URL
        const pathParts = window.location.pathname.split('/');
        const deckId = pathParts[pathParts.length - 1];
        if (deckId && deckId !== 'graph') {
            select.value = deckId;
            await loadDeckGraph(deckId);
        }
    } catch (error) {
        console.error('Failed to load decks:', error);
    }
}

async function loadDeckGraph(deckId) {
    try {
        const graphData = await api(`/decks/${deckId}/graph`);
        deckData = graphData;

        initGraph(graphData);
        updateStats(graphData.stats);
        updateFilters(graphData.edges);

        // Load analysis
        const analysis = await api(`/decks/${deckId}/analysis`);
        updateKeyCards(analysis.key_cards);

        // Hide placeholder
        document.querySelector('.graph-placeholder').style.display = 'none';
    } catch (error) {
        showToast(`Failed to load graph: ${error.message}`, 'error');
    }
}

// ============================================================================
// Graph Initialization
// ============================================================================

function initGraph(data) {
    const container = document.getElementById('graph-container');

    cy = cytoscape({
        container: container,
        elements: {
            nodes: data.nodes,
            edges: data.edges
        },
        style: [
            {
                selector: 'node',
                style: {
                    'background-color': 'data(color)',
                    'label': 'data(label)',
                    'width': 'data(size)',
                    'height': 'data(size)',
                    'font-size': '10px',
                    'text-valign': 'bottom',
                    'text-margin-y': 5,
                    'color': '#fff',
                    'text-outline-color': '#000',
                    'text-outline-width': 1
                }
            },
            {
                selector: 'node[?is_commander]',
                style: {
                    'border-width': 3,
                    'border-color': '#FFD700'
                }
            },
            {
                selector: 'edge',
                style: {
                    'width': 2,
                    'line-color': 'data(color)',
                    'curve-style': 'bezier',
                    'opacity': 0.7
                }
            },
            {
                selector: 'node:selected',
                style: {
                    'border-width': 3,
                    'border-color': '#8b5cf6'
                }
            },
            {
                selector: '.highlighted',
                style: {
                    'opacity': 1
                }
            },
            {
                selector: '.faded',
                style: {
                    'opacity': 0.2
                }
            }
        ],
        layout: {
            name: 'cose',
            animate: true,
            animationDuration: 500,
            nodeRepulsion: 8000,
            idealEdgeLength: 100
        }
    });

    // Event handlers
    cy.on('tap', 'node', function (evt) {
        const node = evt.target;
        showCardDetails(node.data());
        highlightConnected(node);
    });

    cy.on('tap', function (evt) {
        if (evt.target === cy) {
            clearHighlight();
            hideCardDetails();
        }
    });

    cy.on('mouseover', 'node', function (evt) {
        const node = evt.target;
        highlightConnected(node);
    });

    cy.on('mouseout', 'node', function () {
        clearHighlight();
    });
}

function highlightConnected(node) {
    cy.elements().addClass('faded');
    node.addClass('highlighted').removeClass('faded');
    node.neighborhood().addClass('highlighted').removeClass('faded');
}

function clearHighlight() {
    cy.elements().removeClass('faded highlighted');
}

// ============================================================================
// Controls
// ============================================================================

function initControls() {
    document.getElementById('btn-fit').addEventListener('click', () => {
        cy.fit();
    });

    document.getElementById('btn-center').addEventListener('click', () => {
        cy.center();
    });

    document.getElementById('btn-layout').addEventListener('click', () => {
        const layoutName = document.getElementById('layout-algorithm').value;
        runLayout(layoutName);
    });

    document.getElementById('layout-algorithm').addEventListener('change', (e) => {
        runLayout(e.target.value);
    });

    document.getElementById('close-details').addEventListener('click', hideCardDetails);
}

function runLayout(name) {
    const layouts = {
        cose: {
            name: 'cose',
            nodeRepulsion: 8000,
            idealEdgeLength: 100
        },
        circle: {
            name: 'circle'
        },
        grid: {
            name: 'grid'
        },
        concentric: {
            name: 'concentric',
            concentric: function (node) {
                return node.degree();
            },
            levelWidth: function () {
                return 2;
            }
        }
    };

    const layout = cy.layout(layouts[name] || layouts.cose);
    layout.run();
}

// ============================================================================
// Stats & UI Updates
// ============================================================================

function updateStats(stats) {
    document.getElementById('stat-nodes').textContent = stats.total_nodes;
    document.getElementById('stat-edges').textContent = stats.total_edges;
    document.getElementById('stat-density').textContent = (stats.density * 100).toFixed(1) + '%';
    document.getElementById('stat-components').textContent = stats.connected_components;
}

function updateFilters(edges) {
    const types = new Set();
    edges.forEach(edge => {
        edge.data.interaction_types.forEach(t => types.add(t));
    });

    const container = document.getElementById('interaction-filters');
    container.innerHTML = Array.from(types).map(type => `
        <label class="filter-item">
            <input type="checkbox" checked data-type="${type}">
            <span class="legend-color" style="background: ${INTERACTION_COLORS[type] || '#888'}"></span>
            ${type.replace(/_/g, ' ')}
        </label>
    `).join('');

    container.querySelectorAll('input').forEach(input => {
        input.addEventListener('change', filterEdges);
    });
}

function filterEdges() {
    const checked = Array.from(document.querySelectorAll('#interaction-filters input:checked'))
        .map(i => i.dataset.type);

    cy.edges().forEach(edge => {
        const types = edge.data('interaction_types');
        const visible = types.some(t => checked.includes(t));
        edge.style('display', visible ? 'element' : 'none');
    });
}

function updateKeyCards(keyCards) {
    const container = document.getElementById('key-cards-list');

    if (!keyCards || keyCards.length === 0) {
        container.innerHTML = '<p class="text-muted">No key cards found</p>';
        return;
    }

    container.innerHTML = keyCards.slice(0, 10).map(card => `
        <div class="key-card-item">
            <span>${card.name}</span>
            <span class="text-accent">${(card.metrics.composite * 100).toFixed(1)}</span>
        </div>
    `).join('');
}

function initLegend() {
    const container = document.getElementById('legend-items');
    container.innerHTML = Object.entries(INTERACTION_COLORS).map(([type, color]) => `
        <div class="legend-item">
            <span class="legend-color" style="background: ${color}"></span>
            <span>${type.replace(/_/g, ' ')}</span>
        </div>
    `).join('');
}

// ============================================================================
// Card Details
// ============================================================================

function showCardDetails(data) {
    const panel = document.getElementById('card-details');
    panel.classList.remove('hidden');

    document.getElementById('detail-card-name').textContent = data.label;
    document.getElementById('detail-card-image').src = data.image || '';

    // Get connections
    const node = cy.getElementById(data.id);
    const neighbors = node.neighborhood('node');

    const connectionsList = document.getElementById('detail-connections');
    connectionsList.innerHTML = neighbors.map(n => `
        <li>${n.data('label')}</li>
    `).join('');

    // TODO: Get metrics from analysis
}

function hideCardDetails() {
    document.getElementById('card-details').classList.add('hidden');
}
