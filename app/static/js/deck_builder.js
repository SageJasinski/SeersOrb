/**
 * Deck Builder JavaScript
 * Handles card search, deck management, and stats visualization
 */

// State
let currentDeck = {
    id: null,
    name: 'New Deck',
    format: 'commander',
    cards: {}
};

let searchTimeout = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initSearch();
    initDeckActions();
    initViewToggle();
    updateStats();
    loadDeckIfEditing();
});

// ============================================================================
// Search
// ============================================================================

function initSearch() {
    const searchInput = document.getElementById('card-search-input');

    searchInput.addEventListener('input', (e) => {
        const query = e.target.value.trim();

        clearTimeout(searchTimeout);

        if (query.length < 2) {
            showSearchPlaceholder();
            return;
        }

        searchTimeout = setTimeout(() => {
            searchCards(query);
        }, 300);
    });
}

async function searchCards(query) {
    const resultsContainer = document.getElementById('search-results');
    resultsContainer.innerHTML = '<div class="loading-spinner"></div>';

    try {
        const data = await api(`/cards/search?q=${encodeURIComponent(query)}`);
        displaySearchResults(data.cards);
    } catch (error) {
        resultsContainer.innerHTML = `<p class="text-muted">Error: ${error.message}</p>`;
    }
}

function displaySearchResults(cards) {
    const resultsContainer = document.getElementById('search-results');

    if (!cards || cards.length === 0) {
        resultsContainer.innerHTML = '<p class="text-muted text-center">No cards found</p>';
        return;
    }

    resultsContainer.innerHTML = cards.map(card => {
        // Escape JSON for safe HTML attribute embedding
        const cardJson = JSON.stringify(card).replace(/'/g, '&#39;').replace(/"/g, '&quot;');
        return `
        <div class="search-result-item" data-card="${cardJson}">
            <img src="${card.image_uri || '/static/img/card-back.png'}" 
                 alt="${(card.name || '').replace(/"/g, '&quot;')}" 
                 class="search-result-image"
                 loading="lazy">
            <div class="search-result-info">
                <div class="search-result-name">${card.name}</div>
                <div class="search-result-type">${card.type_line}</div>
            </div>
            <button class="btn btn-sm btn-primary add-card-btn">+</button>
        </div>
    `}).join('');

    // Add click handlers
    resultsContainer.querySelectorAll('.search-result-item').forEach(item => {
        const addBtn = item.querySelector('.add-card-btn');
        addBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            const card = JSON.parse(item.dataset.card);
            addCardToDeck(card);
        });

        item.addEventListener('click', () => {
            const card = JSON.parse(item.dataset.card);
            addCardToDeck(card);
        });
    });
}

function showSearchPlaceholder() {
    document.getElementById('search-results').innerHTML =
        '<p class="text-muted text-center">Type to search for cards</p>';
}

// ============================================================================
// Deck Management
// ============================================================================

function addCardToDeck(card, quantity = 1) {
    if (currentDeck.cards[card.id]) {
        currentDeck.cards[card.id].quantity += quantity;
    } else {
        currentDeck.cards[card.id] = {
            card: card,
            quantity: quantity,
            category: ''
        };
    }

    renderDeck();
    updateStats();
    showToast(`Added ${card.name}`, 'success');
}

function removeCardFromDeck(cardId) {
    if (currentDeck.cards[cardId]) {
        currentDeck.cards[cardId].quantity--;
        if (currentDeck.cards[cardId].quantity <= 0) {
            delete currentDeck.cards[cardId];
        }
        renderDeck();
        updateStats();
    }
}

function renderDeck() {
    const container = document.getElementById('deck-cards');
    const cards = Object.values(currentDeck.cards);

    if (cards.length === 0) {
        container.innerHTML = `
            <div class="empty-deck">
                <span class="empty-icon">🃏</span>
                <p>Your deck is empty</p>
                <p class="text-muted">Search for cards on the left to add them</p>
            </div>
        `;
        return;
    }

    container.innerHTML = `
        <div class="card-grid">
            ${cards.map(entry => `
                <div class="mtg-card" data-card-id="${entry.card.id}">
                    <img src="${entry.card.image_uri || '/static/img/card-back.png'}" 
                         alt="${entry.card.name}">
                    ${entry.quantity > 1 ?
            `<span class="mtg-card-quantity">${entry.quantity}x</span>` :
            ''}
                    <div class="mtg-card-overlay">
                        <div>${entry.card.name}</div>
                        <div class="mtg-card-actions">
                            <button class="btn btn-sm btn-secondary" onclick="addCardToDeck(currentDeck.cards['${entry.card.id}'].card)">+</button>
                            <button class="btn btn-sm btn-danger" onclick="removeCardFromDeck('${entry.card.id}')">−</button>
                        </div>
                    </div>
                </div>
            `).join('')}
        </div>
    `;
}

// ============================================================================
// Statistics
// ============================================================================

function updateStats() {
    const cards = Object.values(currentDeck.cards);

    // Total cards
    const totalCards = cards.reduce((sum, entry) => sum + entry.quantity, 0);
    document.getElementById('total-cards').textContent = totalCards;

    // Land count
    const landCount = cards
        .filter(e => e.card.type_line && e.card.type_line.includes('Land'))
        .reduce((sum, e) => sum + e.quantity, 0);
    document.getElementById('land-count').textContent = landCount;

    // Average CMC
    let totalCmc = 0;
    let nonLandCount = 0;
    cards.forEach(entry => {
        if (!entry.card.type_line || !entry.card.type_line.includes('Land')) {
            totalCmc += (entry.card.cmc || 0) * entry.quantity;
            nonLandCount += entry.quantity;
        }
    });
    const avgCmc = nonLandCount > 0 ? (totalCmc / nonLandCount).toFixed(2) : '0.00';
    document.getElementById('avg-cmc').textContent = avgCmc;

    // Mana curve
    renderManaCurve(cards);

    // Color distribution
    renderColorDistribution(cards);

    // Type distribution
    renderTypeDistribution(cards);
}

function renderManaCurve(cards) {
    const curve = {};
    cards.forEach(entry => {
        if (!entry.card.type_line || !entry.card.type_line.includes('Land')) {
            const cmc = Math.min(Math.floor(entry.card.cmc || 0), 7);
            curve[cmc] = (curve[cmc] || 0) + entry.quantity;
        }
    });

    const maxCount = Math.max(...Object.values(curve), 1);

    const container = document.getElementById('mana-curve');
    container.innerHTML = '';

    for (let i = 0; i <= 7; i++) {
        const count = curve[i] || 0;
        const height = (count / maxCount) * 100;

        container.innerHTML += `
            <div class="mana-curve-bar" style="height: ${height}%">
                <span class="mana-curve-count">${count || ''}</span>
                <span class="mana-curve-label">${i === 7 ? '7+' : i}</span>
            </div>
        `;
    }
}

function renderColorDistribution(cards) {
    const colors = { W: 0, U: 0, B: 0, R: 0, G: 0, C: 0 };

    cards.forEach(entry => {
        const cardColors = entry.card.colors || [];
        if (cardColors.length === 0) {
            colors.C += entry.quantity;
        } else {
            cardColors.forEach(c => {
                if (colors.hasOwnProperty(c)) {
                    colors[c] += entry.quantity;
                }
            });
        }
    });

    const container = document.getElementById('color-distribution');
    container.innerHTML = Object.entries(colors)
        .filter(([_, count]) => count > 0)
        .map(([color, count]) => `
            <div class="color-pip ${color}" title="${count} ${color} cards">
                ${count}
            </div>
        `).join('');
}

function renderTypeDistribution(cards) {
    const types = {};
    cards.forEach(entry => {
        const typeLine = entry.card.type_line || '';
        ['Creature', 'Instant', 'Sorcery', 'Artifact', 'Enchantment', 'Planeswalker', 'Land'].forEach(type => {
            if (typeLine.includes(type)) {
                types[type] = (types[type] || 0) + entry.quantity;
            }
        });
    });

    const total = Object.values(types).reduce((a, b) => a + b, 0) || 1;

    const container = document.getElementById('type-distribution');
    container.innerHTML = Object.entries(types)
        .sort((a, b) => b[1] - a[1])
        .map(([type, count]) => `
            <div class="type-row">
                <span style="width: 80px">${type}</span>
                <div class="type-bar">
                    <div class="type-bar-fill" style="width: ${(count / total) * 100}%"></div>
                </div>
                <span style="width: 30px; text-align: right">${count}</span>
            </div>
        `).join('');
}

// ============================================================================
// Deck Actions
// ============================================================================

function initDeckActions() {
    document.getElementById('deck-name').addEventListener('change', (e) => {
        currentDeck.name = e.target.value;
    });

    document.getElementById('deck-format').addEventListener('change', (e) => {
        currentDeck.format = e.target.value;
    });

    document.getElementById('save-deck-btn').addEventListener('click', saveDeck);
    document.getElementById('export-deck-btn').addEventListener('click', exportDeck);

    // Analysis links
    document.getElementById('view-graph-link').addEventListener('click', (e) => {
        e.preventDefault();
        if (currentDeck.id) {
            window.location.href = `/deck/graph/${currentDeck.id}`;
        } else {
            showToast('Save the deck first to view the graph', 'warning');
        }
    });
}

async function saveDeck() {
    try {
        const deckData = {
            name: currentDeck.name,
            format: currentDeck.format,
            cards: currentDeck.cards
        };

        let response;
        if (currentDeck.id) {
            response = await api(`/decks/${currentDeck.id}`, {
                method: 'PUT',
                body: deckData
            });
        } else {
            response = await api('/decks', {
                method: 'POST',
                body: deckData
            });
            currentDeck.id = response.id;
        }

        showToast('Deck saved!', 'success');
    } catch (error) {
        showToast(`Failed to save: ${error.message}`, 'error');
    }
}

function exportDeck() {
    const cards = Object.values(currentDeck.cards);
    let text = `// ${currentDeck.name}\n// Format: ${currentDeck.format}\n\n`;

    cards.forEach(entry => {
        text += `${entry.quantity} ${entry.card.name}\n`;
    });

    // Create download
    const blob = new Blob([text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${currentDeck.name.replace(/[^a-z0-9]/gi, '_')}.txt`;
    a.click();
    URL.revokeObjectURL(url);

    showToast('Deck exported!', 'success');
}

// ============================================================================
// View Toggle
// ============================================================================

function initViewToggle() {
    document.querySelectorAll('.view-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.view-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            // TODO: Implement different view modes
        });
    });
}

// ============================================================================
// Load Existing Deck
// ============================================================================

async function loadDeckIfEditing() {
    const urlParams = new URLSearchParams(window.location.search);
    const deckId = urlParams.get('id') || window.location.pathname.split('/').pop();

    if (deckId && deckId !== 'builder') {
        try {
            const deck = await api(`/decks/${deckId}`);
            currentDeck = {
                id: deck.id,
                name: deck.name,
                format: deck.format,
                cards: deck.cards || {}
            };

            document.getElementById('deck-name').value = deck.name;
            document.getElementById('deck-format').value = deck.format;

            renderDeck();
            updateStats();
        } catch (error) {
            console.error('Failed to load deck:', error);
        }
    }
}
