/* === LEXIS — App Logic === */

// ── State ──────────────────────────────────────────────
let state = {
  cards: [],
  stats: null,
  reviewQueue: [],
  reviewIndex: 0,
  editingCardId: null,
  currentDeck: null,
};

// ── Init ───────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  setGreeting();
  loadDashboard();
  setupNav();
});

function setGreeting() {
  const h = new Date().getHours();
  const el = document.getElementById('timeGreeting');
  if (el) el.textContent = h < 12 ? 'morning' : h < 17 ? 'afternoon' : 'evening';
}

// ── Navigation ─────────────────────────────────────────
function setupNav() {
  document.querySelectorAll('.nav-btn').forEach(btn => {
    btn.addEventListener('click', () => switchView(btn.dataset.view));
  });
}

function switchView(viewId) {
  document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
  document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
  const view = document.getElementById('view-' + viewId);
  const btn = document.querySelector(`.nav-btn[data-view="${viewId}"]`);
  if (view) view.classList.add('active');
  if (btn) btn.classList.add('active');

  if (viewId === 'dashboard') loadDashboard();
  if (viewId === 'review') loadReview();
  if (viewId === 'cards') loadCards();
  if (viewId === 'stats') loadStats();
}

// ── API helpers ────────────────────────────────────────
async function api(path, opts = {}) {
  const res = await fetch(path, {
    headers: { 'Content-Type': 'application/json' },
    ...opts,
  });
  return res.json();
}

// ── Dashboard ──────────────────────────────────────────
async function loadDashboard() {
  const [stats, decks] = await Promise.all([
    api('/api/stats'),
    api('/api/decks'),
  ]);
  state.stats = stats;

  document.getElementById('statDue').textContent = stats.due;
  document.getElementById('statTotal').textContent = stats.total;
  document.getElementById('statMastered').textContent = stats.mastered;
  document.getElementById('statLearning').textContent = stats.learning;
  renderStreak(stats);
  renderDeckList(decks);
  renderActivityChart(stats.daily);
}

function renderStreak(stats) {
  // Simple streak: count consecutive days with activity
  const daily = stats.daily || [];
  let streak = 0;
  for (let i = daily.length - 1; i >= 0; i--) {
    if (daily[i].count > 0) streak++;
    else break;
  }
  document.getElementById('streakCount').textContent = streak;
}

function renderDeckList(decks) {
  const el = document.getElementById('deckList');
  if (!decks.length) {
    el.innerHTML = `<div class="empty-state"><div class="empty-state-icon">🌱</div>No decks yet. Add some cards to get started.</div>`;
    return;
  }
  el.innerHTML = decks.map(d => `
    <div class="deck-item" onclick="filterByDeck('${d.id}')">
      <div>
        <div class="deck-name">${escHtml(d.name)}</div>
        <div class="deck-meta">${d.total} cards</div>
      </div>
      <div class="deck-due-badge">${d.due} due</div>
    </div>
  `).join('');
}

function filterByDeck(deckId) {
  switchView('review');
  state.currentDeck = deckId;
  loadReview(deckId);
}

function renderActivityChart(daily) {
  const el = document.getElementById('activityChart');
  if (!daily || !daily.length) { el.innerHTML = ''; return; }
  const max = Math.max(...daily.map(d => d.count), 1);
  el.innerHTML = daily.map(d => {
    const h = Math.max(3, Math.round((d.count / max) * 55));
    const dayLabel = new Date(d.date + 'T12:00:00').toLocaleDateString('en', { weekday: 'short' });
    return `
      <div class="activity-bar-wrap">
        <div class="activity-bar ${d.count > 0 ? 'has-reviews' : ''}" style="height:${h}px" title="${d.count} reviews"></div>
        <div class="activity-day">${dayLabel}</div>
      </div>`;
  }).join('');
}

// ── Review ─────────────────────────────────────────────
async function loadReview(deckId = null) {
  const arena = document.getElementById('reviewArena');
  arena.innerHTML = `<div class="loading-dots"><span></span><span></span><span></span></div>`;

  const url = '/api/review' + (deckId ? `?deck_id=${deckId}` : '');
  const queue = await api(url);
  state.reviewQueue = queue;
  state.reviewIndex = 0;

  const info = document.getElementById('reviewQueueInfo');
  info.textContent = `${queue.length} card${queue.length !== 1 ? 's' : ''} due`;

  if (!queue.length) {
    arena.innerHTML = `
      <div class="review-empty">
        <span class="review-empty-icon">🎉</span>
        <h2>All caught up!</h2>
        <p>No cards due for review right now. Come back later or add new cards.</p>
      </div>`;
    return;
  }
  showReviewCard();
}

function showReviewCard() {
  const arena = document.getElementById('reviewArena');
  const queue = state.reviewQueue;
  const idx = state.reviewIndex;

  if (idx >= queue.length) {
    arena.innerHTML = `
      <div class="review-empty">
        <span class="review-empty-icon">✨</span>
        <h2>Session complete!</h2>
        <p>You reviewed ${queue.length} card${queue.length !== 1 ? 's' : ''}. Great work!</p>
      </div>`;
    loadDashboard();
    return;
  }

  const card = queue[idx];
  const pct = Math.round((idx / queue.length) * 100);

  arena.innerHTML = `
    <div class="progress-bar-wrap">
      <div class="progress-track"><div class="progress-fill" style="width:${pct}%"></div></div>
      <div class="progress-label">${idx} / ${queue.length}</div>
    </div>
    <div class="flashcard" id="flashcard" onclick="flipCard()">
      <div class="card-inner">
        <div class="card-face card-face--front">
          <div class="card-badge">front</div>
          <div class="card-text">${escHtml(card.front)}</div>
          <div class="card-hint">click to reveal</div>
        </div>
        <div class="card-face card-face--back">
          <div class="card-badge">back</div>
          <div class="card-text">${escHtml(card.back)}</div>
        </div>
      </div>
    </div>
    <div class="rating-row" id="ratingRow" style="display:none">
      <button class="rating-btn again" onclick="submitReview(1)">
        <span class="rating-emoji">😵</span>
        <span class="rating-label">Again</span>
      </button>
      <button class="rating-btn hard" onclick="submitReview(2)">
        <span class="rating-emoji">😓</span>
        <span class="rating-label">Hard</span>
      </button>
      <button class="rating-btn good" onclick="submitReview(4)">
        <span class="rating-emoji">😊</span>
        <span class="rating-label">Good</span>
      </button>
      <button class="rating-btn easy" onclick="submitReview(5)">
        <span class="rating-emoji">😎</span>
        <span class="rating-label">Easy</span>
      </button>
    </div>`;
}

function flipCard() {
  const fc = document.getElementById('flashcard');
  if (!fc) return;
  fc.classList.toggle('flipped');
  if (fc.classList.contains('flipped')) {
    const rr = document.getElementById('ratingRow');
    if (rr) rr.style.display = 'flex';
  }
}

async function submitReview(quality) {
  const card = state.reviewQueue[state.reviewIndex];
  await api(`/api/review/${card.id}`, {
    method: 'POST',
    body: JSON.stringify({ quality }),
  });
  state.reviewIndex++;
  showReviewCard();
}

// ── Cards ──────────────────────────────────────────────
let allCards = [];

async function loadCards() {
  const grid = document.getElementById('cardsGrid');
  grid.innerHTML = `<div class="loading-dots"><span></span><span></span><span></span></div>`;

  const [cards, decks] = await Promise.all([api('/api/cards'), api('/api/decks')]);
  allCards = cards;

  // Populate deck filter
  const filter = document.getElementById('deckFilter');
  filter.innerHTML = '<option value="">All Decks</option>' +
    decks.map(d => `<option value="${d.id}">${escHtml(d.name)}</option>`).join('');

  renderCardsGrid(cards);
}

function renderCardsGrid(cards) {
  const grid = document.getElementById('cardsGrid');
  if (!cards.length) {
    grid.innerHTML = `<div class="empty-state"><div class="empty-state-icon">🃏</div>No cards found.</div>`;
    return;
  }
  grid.innerHTML = cards.map(c => {
    const nextDate = c.next_review ? new Date(c.next_review).toLocaleDateString() : '—';
    return `
      <div class="card-item" onclick="openEditModal('${c.id}')">
        <div class="card-item-front">${escHtml(c.front)}</div>
        <div class="card-item-back">${escHtml(c.back)}</div>
        <div class="card-item-meta">
          <span class="card-item-interval">+${c.interval}d</span>
          <span>${nextDate}</span>
          ${c.tags && c.tags.length ? c.tags.map(t => `<span class="tag">${escHtml(t)}</span>`).join('') : ''}
        </div>
      </div>`;
  }).join('');
}

function filterCards() {
  const q = document.getElementById('cardSearch').value.toLowerCase();
  const deck = document.getElementById('deckFilter').value;
  let filtered = allCards;
  if (deck) filtered = filtered.filter(c => c.deck_id === deck);
  if (q) filtered = filtered.filter(c =>
    c.front.toLowerCase().includes(q) || c.back.toLowerCase().includes(q)
  );
  renderCardsGrid(filtered);
}

// ── Edit Modal ─────────────────────────────────────────
function openEditModal(cardId) {
  const card = allCards.find(c => c.id === cardId);
  if (!card) return;
  state.editingCardId = cardId;
  document.getElementById('editFront').value = card.front;
  document.getElementById('editBack').value = card.back;
  document.getElementById('editTags').value = (card.tags || []).join(', ');
  document.getElementById('editModal').classList.add('open');
}

function closeEditModal(e) {
  if (e && e.target !== document.getElementById('editModal')) return;
  document.getElementById('editModal').classList.remove('open');
  state.editingCardId = null;
}

async function saveEdit() {
  const id = state.editingCardId;
  if (!id) return;
  const front = document.getElementById('editFront').value.trim();
  const back = document.getElementById('editBack').value.trim();
  const tags = document.getElementById('editTags').value.split(',').map(t => t.trim()).filter(Boolean);
  if (!front || !back) { showToast('Front and back are required'); return; }
  await api(`/api/cards/${id}`, { method: 'PUT', body: JSON.stringify({ front, back, tags }) });
  document.getElementById('editModal').classList.remove('open');
  showToast('Card updated');
  loadCards();
}

async function deleteCard() {
  const id = state.editingCardId;
  if (!id) return;
  if (!confirm('Delete this card?')) return;
  await api(`/api/cards/${id}`, { method: 'DELETE' });
  document.getElementById('editModal').classList.remove('open');
  showToast('Card deleted');
  loadCards();
}

// ── Add Cards ──────────────────────────────────────────
async function addSingleCard() {
  const front = document.getElementById('addFront').value.trim();
  const back = document.getElementById('addBack').value.trim();
  const deck_id = document.getElementById('addDeck').value.trim() || 'default';
  const tags = document.getElementById('addTags').value.split(',').map(t => t.trim()).filter(Boolean);
  const fb = document.getElementById('addFeedback');

  if (!front || !back) { fb.textContent = 'Front and back are required.'; fb.className = 'form-feedback err'; return; }

  await api('/api/cards', { method: 'POST', body: JSON.stringify({ front, back, deck_id, tags }) });
  document.getElementById('addFront').value = '';
  document.getElementById('addBack').value = '';
  document.getElementById('addTags').value = '';
  fb.textContent = '✓ Card added!';
  fb.className = 'form-feedback ok';
  setTimeout(() => { fb.textContent = ''; }, 2500);
  showToast('Card added to ' + deck_id);
}

async function bulkImport() {
  const text = document.getElementById('bulkText').value;
  const deck_id = document.getElementById('bulkDeck').value.trim() || 'imported';
  const fb = document.getElementById('bulkFeedback');

  const lines = text.split('\n').filter(l => l.includes('::'));
  if (!lines.length) { fb.textContent = 'No valid pairs found (use ::)'; fb.className = 'form-feedback err'; return; }

  const pairs = lines.map(l => {
    const [front, ...rest] = l.split('::');
    return { front: front.trim(), back: rest.join('::').trim() };
  }).filter(p => p.front && p.back);

  const res = await api('/api/bulk', { method: 'POST', body: JSON.stringify({ deck_id, pairs }) });
  document.getElementById('bulkText').value = '';
  fb.textContent = `✓ Imported ${res.added} cards into "${deck_id}"`;
  fb.className = 'form-feedback ok';
  setTimeout(() => { fb.textContent = ''; }, 3000);
  showToast(`Imported ${res.added} cards`);
}

// ── Stats ──────────────────────────────────────────────
async function loadStats() {
  const stats = await api('/api/stats');
  document.getElementById('bigTotal').textContent = stats.total;
  document.getElementById('bigDue').textContent = stats.due;
  document.getElementById('bigMastered').textContent = stats.mastered;
  renderBarChart(stats.daily);
  renderDonut(stats.mastered, stats.learning);
}

function renderBarChart(daily) {
  const el = document.getElementById('barChart');
  if (!daily || !daily.length) { el.innerHTML = ''; return; }
  const max = Math.max(...daily.map(d => d.count), 1);
  el.innerHTML = daily.map(d => {
    const h = Math.max(4, Math.round((d.count / max) * 110));
    const dayLabel = new Date(d.date + 'T12:00:00').toLocaleDateString('en', { weekday: 'short' });
    return `
      <div class="bar-wrap">
        <div class="bar-val">${d.count || ''}</div>
        <div class="bar ${d.count > 0 ? 'active-bar' : ''}" style="height:${h}px"></div>
        <div class="bar-label">${dayLabel}</div>
      </div>`;
  }).join('');
}

function renderDonut(mastered, learning) {
  const svg = document.getElementById('donutChart');
  const legend = document.getElementById('donutLegend');
  const total = mastered + learning;
  if (!total) {
    svg.innerHTML = '';
    legend.innerHTML = '<div style="color:var(--text3);font-size:12px">No data</div>';
    return;
  }

  const segments = [
    { label: 'Mastered', value: mastered, color: '#5dba8a' },
    { label: 'Learning', value: learning, color: '#e8a530' },
  ];

  const cx = 60, cy = 60, r = 45, stroke = 18;
  const circ = 2 * Math.PI * r;
  let offset = 0;
  let paths = '';

  for (const seg of segments) {
    const frac = seg.value / total;
    const dash = frac * circ;
    paths += `<circle cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke="${seg.color}" stroke-width="${stroke}"
      stroke-dasharray="${dash} ${circ - dash}" stroke-dashoffset="${-offset}" stroke-linecap="butt"
      transform="rotate(-90 ${cx} ${cy})" />`;
    offset += dash;
  }

  svg.innerHTML = paths + `<text x="${cx}" y="${cy + 5}" text-anchor="middle" fill="var(--text)" font-family="var(--font-serif)" font-size="14">${total}</text>`;
  legend.innerHTML = segments.map(s => `
    <div class="legend-item">
      <div class="legend-dot" style="background:${s.color}"></div>
      <span>${s.label}: <strong>${s.value}</strong></span>
    </div>`).join('');
}

// ── Utilities ──────────────────────────────────────────
function escHtml(str) {
  return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

let toastTimer;
function showToast(msg) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => t.classList.remove('show'), 2500);
}