/**
 * Monte Carlo Simulation JavaScript
 * Handles simulation configuration and results visualization
 */

let turnDistChart = null;
let mulliganChart = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadDecks();
    initSimulation();
});

// ============================================================================
// Load Decks
// ============================================================================

async function loadDecks() {
    const select = document.getElementById('sim-deck-select');

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

        select.addEventListener('change', (e) => {
            const btn = document.getElementById('run-sim-btn');
            btn.disabled = !e.target.value;

            if (e.target.value) {
                const deck = data.decks.find(d => d.id === e.target.value);
                if (deck) {
                    document.getElementById('deck-info').classList.remove('hidden');
                    document.getElementById('deck-card-count').textContent = deck.card_count;
                }
            } else {
                document.getElementById('deck-info').classList.add('hidden');
            }
        });

        // Check URL for deck ID
        const pathParts = window.location.pathname.split('/');
        const deckId = pathParts[pathParts.length - 1];
        if (deckId && deckId !== 'simulation' && deckId !== '') {
            select.value = deckId;
            select.dispatchEvent(new Event('change'));
        }
    } catch (error) {
        console.error('Failed to load decks:', error);
    }
}

// ============================================================================
// Simulation
// ============================================================================

function initSimulation() {
    document.getElementById('run-sim-btn').addEventListener('click', runSimulation);
}

async function runSimulation() {
    const deckId = document.getElementById('sim-deck-select').value;
    const iterations = parseInt(document.getElementById('sim-iterations').value);
    const maxTurn = parseInt(document.getElementById('sim-max-turn').value);

    // Build criteria
    const criteria = {
        min_lands: parseInt(document.getElementById('crit-min-lands').value),
        max_lands: parseInt(document.getElementById('crit-max-lands').value)
    };

    // Required cards
    const cardsText = document.getElementById('crit-cards').value.trim();
    if (cardsText) {
        criteria.any_of = cardsText.split('\n').map(c => c.trim()).filter(c => c);
    }

    // Show loading
    document.getElementById('sim-placeholder').classList.add('hidden');
    document.getElementById('sim-results-panel').classList.add('hidden');
    document.getElementById('sim-loading').classList.remove('hidden');
    document.getElementById('loading-progress').textContent = `Running ${iterations.toLocaleString()} iterations...`;

    try {
        const results = await api('/simulation/run', {
            method: 'POST',
            body: {
                deck_id: deckId,
                iterations: iterations,
                max_turn: maxTurn,
                criteria: criteria,
                use_mulligan: document.getElementById('use-mulligan').checked
            }
        });

        displayResults(results);
    } catch (error) {
        showToast(`Simulation failed: ${error.message}`, 'error');
        document.getElementById('sim-loading').classList.add('hidden');
        document.getElementById('sim-placeholder').classList.remove('hidden');
    }
}

function displayResults(results) {
    document.getElementById('sim-loading').classList.add('hidden');
    document.getElementById('sim-results-panel').classList.remove('hidden');

    // Stats
    document.getElementById('res-success-rate').textContent = results.success_percentage + '%';
    document.getElementById('res-avg-turn').textContent = results.average_turn || '-';
    document.getElementById('res-iterations').textContent = results.iterations.toLocaleString();

    const ci = results.confidence_interval;
    const margin = ((ci.upper - ci.lower) / 2 * 100).toFixed(1);
    document.getElementById('res-confidence').textContent = `± ${margin}%`;

    // Turn distribution chart
    renderTurnDistChart(results.turn_distribution);

    // Card frequency
    renderCardFrequency(results.card_frequency_in_wins);

    // Mulligan chart
    renderMulliganChart(results.mulligan_stats);
}

function renderTurnDistChart(distribution) {
    const ctx = document.getElementById('turn-dist-chart').getContext('2d');

    if (turnDistChart) {
        turnDistChart.destroy();
    }

    const labels = Object.keys(distribution).map(t => t === '0' ? 'Opening' : 'Turn ' + t);
    const values = Object.values(distribution);

    turnDistChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Successes',
                data: values,
                backgroundColor: 'rgba(34, 197, 94, 0.7)',
                borderColor: 'rgba(34, 197, 94, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                title: {
                    display: true,
                    text: 'When criteria was achieved'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Count'
                    }
                }
            }
        }
    });
}

function renderCardFrequency(frequency) {
    const container = document.getElementById('card-freq-list');

    if (!frequency || Object.keys(frequency).length === 0) {
        container.innerHTML = '<p class="text-muted">No data available</p>';
        return;
    }

    const maxFreq = Math.max(...Object.values(frequency));

    container.innerHTML = Object.entries(frequency)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 15)
        .map(([name, freq]) => `
            <div class="card-freq-item">
                <span class="name">${name}</span>
                <div class="bar">
                    <div class="bar-fill" style="width: ${(freq / maxFreq) * 100}%"></div>
                </div>
                <span class="pct">${(freq * 100).toFixed(0)}%</span>
            </div>
        `).join('');
}

function renderMulliganChart(stats) {
    const ctx = document.getElementById('mulligan-chart').getContext('2d');

    if (mulliganChart) {
        mulliganChart.destroy();
    }

    const labels = Object.keys(stats).map(m => m === '0' ? 'Keep 7' : m + ' mulligan(s)');
    const values = Object.values(stats);

    mulliganChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: [
                    'rgba(34, 197, 94, 0.7)',
                    'rgba(245, 158, 11, 0.7)',
                    'rgba(239, 68, 68, 0.7)',
                    'rgba(139, 92, 246, 0.7)'
                ],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right'
                }
            }
        }
    });
}
