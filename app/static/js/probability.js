/**
 * Probability Analysis JavaScript
 * Handles calculations for hypergeometric and multivariate distributions
 */

let hyperChart = null;
let turnChart = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initHypergeometric();
    initMultivariate();
    initByTurn();
    initOptimal();
});

// ============================================================================
// Single Card (Hypergeometric)
// ============================================================================

function initHypergeometric() {
    document.getElementById('calc-hyper-btn').addEventListener('click', calculateHypergeometric);
}

async function calculateHypergeometric() {
    const deckSize = parseInt(document.getElementById('hyper-deck-size').value);
    const copies = parseInt(document.getElementById('hyper-copies').value);
    const drawn = parseInt(document.getElementById('hyper-drawn').value);
    const successes = parseInt(document.getElementById('hyper-successes').value);

    try {
        const data = await api('/probability/hypergeometric', {
            method: 'POST',
            body: {
                deck_size: deckSize,
                copies: copies,
                cards_drawn: drawn,
                successes: successes
            }
        });

        displayHyperResults(data);
    } catch (error) {
        showToast(`Calculation failed: ${error.message}`, 'error');
    }
}

function displayHyperResults(data) {
    const resultsPanel = document.getElementById('hyper-results');
    resultsPanel.classList.remove('hidden');

    document.getElementById('result-exactly').textContent = (data.exactly * 100).toFixed(2) + '%';
    document.getElementById('result-at-least').textContent = (data.at_least * 100).toFixed(2) + '%';
    document.getElementById('result-at-most').textContent = (data.at_most * 100).toFixed(2) + '%';

    // Chart
    const dist = data.distribution;
    const labels = Object.keys(dist).map(k => `${k} card${k !== '1' ? 's' : ''}`);
    const values = Object.values(dist).map(v => v * 100);

    const ctx = document.getElementById('hyper-chart').getContext('2d');

    if (hyperChart) {
        hyperChart.destroy();
    }

    hyperChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Probability (%)',
                data: values,
                backgroundColor: 'rgba(139, 92, 246, 0.7)',
                borderColor: 'rgba(139, 92, 246, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Probability (%)'
                    }
                }
            }
        }
    });
}

// ============================================================================
// Multi-Card Combo
// ============================================================================

function initMultivariate() {
    document.getElementById('add-piece-btn').addEventListener('click', addComboPiece);
    document.getElementById('calc-multi-btn').addEventListener('click', calculateMultivariate);
}

function addComboPiece() {
    const container = document.getElementById('combo-pieces');
    const piece = document.createElement('div');
    piece.className = 'combo-piece';
    piece.innerHTML = `
        <input type="text" placeholder="Card name" class="form-input piece-name">
        <input type="number" value="1" min="1" max="4" class="form-input piece-copies" placeholder="Copies">
        <input type="number" value="1" min="1" max="4" class="form-input piece-need" placeholder="Need">
    `;
    container.appendChild(piece);
}

async function calculateMultivariate() {
    const deckSize = parseInt(document.getElementById('multi-deck-size').value);
    const drawn = parseInt(document.getElementById('multi-drawn').value);

    const pieces = [];
    const pieceElements = document.querySelectorAll('.combo-piece');
    const cardCounts = [];
    const successes = [];

    pieceElements.forEach(piece => {
        const copies = parseInt(piece.querySelector('.piece-copies').value) || 1;
        const need = parseInt(piece.querySelector('.piece-need').value) || 1;
        cardCounts.push(copies);
        successes.push(need);
    });

    try {
        const data = await api('/probability/multivariate', {
            method: 'POST',
            body: {
                deck_size: deckSize,
                card_counts: cardCounts,
                cards_drawn: drawn,
                successes: successes
            }
        });

        displayMultiResults(data);
    } catch (error) {
        showToast(`Calculation failed: ${error.message}`, 'error');
    }
}

function displayMultiResults(data) {
    const resultsPanel = document.getElementById('multi-results');
    resultsPanel.classList.remove('hidden');

    document.getElementById('combo-probability').textContent = (data.probability * 100).toFixed(2);
}

// ============================================================================
// Probability by Turn
// ============================================================================

function initByTurn() {
    document.getElementById('calc-turn-btn').addEventListener('click', calculateByTurn);
}

async function calculateByTurn() {
    const deckSize = parseInt(document.getElementById('turn-deck-size').value);
    const copies = parseInt(document.getElementById('turn-copies').value);
    const onPlay = document.getElementById('turn-play-draw').value === 'play';

    // Calculate locally for each turn
    const results = [];
    for (let turn = 0; turn <= 10; turn++) {
        let cardsSeen;
        if (turn === 0) {
            cardsSeen = 7;
        } else if (onPlay) {
            cardsSeen = 7 + turn;
        } else {
            cardsSeen = 7 + turn + 1;
        }

        cardsSeen = Math.min(cardsSeen, deckSize);

        // Use API for calculation
        const data = await api('/probability/hypergeometric', {
            method: 'POST',
            body: {
                deck_size: deckSize,
                copies: copies,
                cards_drawn: cardsSeen,
                successes: 1
            }
        });

        results.push({
            turn: turn,
            cardsSeen: cardsSeen,
            probability: data.at_least
        });
    }

    displayTurnResults(results);
}

function displayTurnResults(results) {
    const resultsPanel = document.getElementById('turn-results');
    resultsPanel.classList.remove('hidden');

    // Table
    const tbody = document.getElementById('turn-table-body');
    tbody.innerHTML = results.map(r => `
        <tr>
            <td>${r.turn === 0 ? 'Opening' : 'Turn ' + r.turn}</td>
            <td>${r.cardsSeen}</td>
            <td style="color: var(--color-accent); font-weight: 500">
                ${(r.probability * 100).toFixed(1)}%
            </td>
        </tr>
    `).join('');

    // Chart
    const ctx = document.getElementById('turn-chart').getContext('2d');

    if (turnChart) {
        turnChart.destroy();
    }

    turnChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: results.map(r => r.turn === 0 ? 'Open' : 'T' + r.turn),
            datasets: [{
                label: 'Probability (%)',
                data: results.map(r => r.probability * 100),
                borderColor: 'rgba(139, 92, 246, 1)',
                backgroundColor: 'rgba(139, 92, 246, 0.1)',
                fill: true,
                tension: 0.3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    title: {
                        display: true,
                        text: 'Probability (%)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Turn'
                    }
                }
            }
        }
    });
}

// ============================================================================
// Optimal Copies
// ============================================================================

function initOptimal() {
    document.getElementById('calc-opt-btn').addEventListener('click', calculateOptimal);
}

async function calculateOptimal() {
    const deckSize = parseInt(document.getElementById('opt-deck-size').value);
    const targetPct = parseInt(document.getElementById('opt-target').value) / 100;
    const drawn = parseInt(document.getElementById('opt-drawn').value);

    // Binary search for optimal copies
    let optimalCopies = 1;
    let actualProb = 0;

    for (let copies = 1; copies <= deckSize; copies++) {
        const data = await api('/probability/hypergeometric', {
            method: 'POST',
            body: {
                deck_size: deckSize,
                copies: copies,
                cards_drawn: drawn,
                successes: 1
            }
        });

        if (data.at_least >= targetPct) {
            optimalCopies = copies;
            actualProb = data.at_least;
            break;
        }

        actualProb = data.at_least;
        optimalCopies = copies;
    }

    displayOptimalResults(optimalCopies, actualProb);
}

function displayOptimalResults(copies, probability) {
    const resultsPanel = document.getElementById('opt-results');
    resultsPanel.classList.remove('hidden');

    document.getElementById('opt-copies').textContent = copies;
    document.getElementById('opt-actual').textContent =
        `Actual probability: ${(probability * 100).toFixed(1)}%`;
}
