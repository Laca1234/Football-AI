// app.js — Footy AI frontend logic

const API = '';
let allTeams = [];
let rowCount = 0;

// ── Theme ─────────────────────────────────────────────────────────────────────
function initTheme() {
  applyTheme(localStorage.getItem('theme') || 'dark');
}
function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem('theme', theme);
  const btn = document.getElementById('themeBtn');
  if (btn) btn.textContent = theme === 'dark' ? '☀️' : '🌙';
}
function toggleTheme() {
  applyTheme(document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark');
}

// ── Boot ──────────────────────────────────────────────────────────────────────
async function boot() {
  initTheme();
  try {
    const res  = await fetch(`${API}/api/teams`);
    const data = await res.json();
    allTeams   = data.teams;
    document.getElementById('seasonBadge').textContent = data.season;
    addMatchRow();
    loadFixtures();
  } catch (e) {
    document.getElementById('matchRows').innerHTML =
      `<div class="error-msg">Could not connect to backend. Make sure controller.py is running.</div>`;
  }
}

// ── Mode switch ───────────────────────────────────────────────────────────────
function setMode(mode) {
  document.querySelectorAll('.mode-btn').forEach(b =>
    b.classList.toggle('active', b.dataset.mode === mode));
  document.querySelectorAll('.panel').forEach(p =>
    p.classList.toggle('active', p.id === mode + 'Panel'));
}

// ── Custom select ─────────────────────────────────────────────────────────────
function createSelect(id, placeholder) {
  const wrap = document.createElement('div');
  wrap.className = 'custom-select';
  wrap.dataset.value = '';
  wrap.id = id;
  wrap.innerHTML = `
    <div class="select-display" onclick="toggleDropdown('${id}')">
      <span class="placeholder">${placeholder}</span>
      <span class="chevron">▼</span>
    </div>
    <div class="select-dropdown" id="${id}_drop">
      <input class="select-search" placeholder="Search team..."
             oninput="filterOptions('${id}', this.value)" autocomplete="off">
      <div class="select-options" id="${id}_opts"></div>
    </div>`;
  renderOptions(id, allTeams, wrap);
  return wrap;
}

function renderOptions(id, teams, wrapEl) {
  const wrap = wrapEl || document.getElementById(id);
  const opts = document.getElementById(`${id}_opts`);
  if (!opts) return;
  opts.innerHTML = '';
  if (!teams.length) {
    opts.innerHTML = '<div class="select-option no-results">No teams found</div>';
    return;
  }
  teams.forEach(t => {
    const div = document.createElement('div');
    div.className = 'select-option' + (wrap.dataset.value === t.name ? ' selected' : '');
    div.innerHTML = (t.badge ? `<img src="${t.badge}" onerror="this.style.display='none'">` : '')
                  + `<span>${t.name}</span>`;
    div.onclick = () => selectTeam(id, t);
    opts.appendChild(div);
  });
}

function toggleDropdown(id) {
  const drop    = document.getElementById(`${id}_drop`);
  const display = drop.previousElementSibling;
  const isOpen  = drop.classList.contains('open');
  document.querySelectorAll('.select-dropdown.open').forEach(d => {
    d.classList.remove('open');
    d.previousElementSibling.classList.remove('open');
  });
  if (!isOpen) {
    drop.classList.add('open');
    display.classList.add('open');
    drop.querySelector('.select-search').focus();
  }
}

function filterOptions(id, query) {
  renderOptions(id, query
    ? allTeams.filter(t => t.name.toLowerCase().includes(query.toLowerCase()))
    : allTeams);
}

function selectTeam(id, team) {
  const wrap    = document.getElementById(id);
  const display = wrap.querySelector('.select-display');
  const drop    = wrap.querySelector('.select-dropdown');
  wrap.dataset.value = team.name;
  display.innerHTML = (team.badge ? `<img src="${team.badge}" onerror="this.style.display='none'">` : '')
                    + `<span class="team-name">${team.name}</span><span class="chevron">▼</span>`;
  display.classList.remove('open');
  drop.classList.remove('open');
  drop.querySelector('.select-search').value = '';
  renderOptions(id, allTeams, wrap);
}

document.addEventListener('click', e => {
  if (!e.target.closest('.custom-select'))
    document.querySelectorAll('.select-dropdown.open').forEach(d => {
      d.classList.remove('open');
      d.previousElementSibling.classList.remove('open');
    });
});

// ── Match rows ────────────────────────────────────────────────────────────────
function addMatchRow() {
  rowCount++;
  const rowId = `row_${rowCount}`;
  const row   = document.createElement('div');
  row.className = 'match-row';
  row.id        = rowId;

  const vs       = document.createElement('div');
  vs.className   = 'vs-label';
  vs.textContent = 'VS';

  const delBtn     = document.createElement('button');
  delBtn.className = 'delete-btn';
  delBtn.title     = 'Remove row';
  delBtn.innerHTML = '🗑';
  delBtn.onclick   = () => removeRow(rowId);

  row.appendChild(createSelect(`home_${rowCount}`, 'Home team'));
  row.appendChild(vs);
  row.appendChild(createSelect(`away_${rowCount}`, 'Away team'));
  row.appendChild(delBtn);

  document.getElementById('matchRows').appendChild(row);
  updateDeleteButtons();
}

function removeRow(rowId) {
  document.getElementById(rowId)?.remove();
  updateDeleteButtons();
}

function updateDeleteButtons() {
  const rows = document.querySelectorAll('#matchRows .match-row');
  rows.forEach(r => { r.querySelector('.delete-btn').disabled = rows.length === 1; });
}

// ── Next fixtures sidebar ─────────────────────────────────────────────────────
async function loadFixtures() {
  const sidebar = document.getElementById('fixturesSidebar');
  if (!sidebar) return;
  sidebar.innerHTML = '<div class="loading" style="padding:20px"><div class="spinner"></div></div>';

  try {
    const res  = await fetch(`${API}/api/fixtures`);
    const data = await res.json();
    renderFixtures(data.gameweeks);
  } catch (e) {
    sidebar.innerHTML = '<div style="padding:14px;font-size:13px;color:var(--muted)">Fixtures unavailable</div>';
  }
}

function renderFixtures(gameweeks) {
  const sidebar = document.getElementById('fixturesSidebar');
  if (!gameweeks || !gameweeks.length) {
    sidebar.innerHTML = '<div style="padding:14px;font-size:13px;color:var(--muted)">No upcoming fixtures found</div>';
    return;
  }

  sidebar.innerHTML = gameweeks.map((gw, gi) => {
    const dateLabel = new Date(gw.date).toLocaleDateString('en-GB', { weekday:'short', day:'numeric', month:'short' });
    const matchRows = gw.matches.map(m => `
      <div class="fixture-item">
        <div class="fixture-team">
          ${m.home_badge ? `<img src="${m.home_badge}" onerror="this.style.display='none'">` : ''}
          <span>${m.home}</span>
        </div>
        <div class="fixture-vs">VS</div>
        <div class="fixture-team" style="justify-content:flex-end;text-align:right">
          ${m.away_badge ? `<img src="${m.away_badge}" onerror="this.style.display='none'">` : ''}
          <span>${m.away}</span>
        </div>
      </div>`).join('');

    return `
      <div class="sidebar-card">
        <div class="gameweek-label">Gameweek ${gi + 1} · ${dateLabel}</div>
        ${matchRows}
      </div>`;
  }).join('');
}

// ── Predict ───────────────────────────────────────────────────────────────────
async function runPrediction() {
  const rows    = document.querySelectorAll('#matchRows .match-row');
  const matches = [];
  rows.forEach(r => {
    const home = r.querySelector('[id^="home_"]')?.dataset.value;
    const away = r.querySelector('[id^="away_"]')?.dataset.value;
    if (home && away) matches.push({ home, away });
  });

  if (!matches.length) {
    document.getElementById('matchResults').innerHTML =
      '<div class="error-msg">Please select at least one full match.</div>';
    return;
  }

  const btn = document.getElementById('predictBtn');
  btn.disabled = true; btn.textContent = 'Predicting...';
  document.getElementById('matchResults').innerHTML =
    '<div class="loading"><div class="spinner"></div> Running predictions…</div>';

  try {
    const res  = await fetch(`${API}/api/predict`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ matches }),
    });
    renderMatchResults((await res.json()).results);
  } catch (e) {
    document.getElementById('matchResults').innerHTML =
      '<div class="error-msg">Prediction failed. Is the backend running?</div>';
  } finally {
    btn.disabled = false; btn.textContent = 'Predict';
  }
}

function renderMatchResults(results) {
  const section = document.getElementById('matchResults');
  section.innerHTML = '';
  results.forEach(r => {
    if (r.error) { section.innerHTML += `<div class="error-msg">${r.home} vs ${r.away}: ${r.error}</div>`; return; }
    const H = (r.probs.H * 100).toFixed(1);
    const D = (r.probs.D * 100).toFixed(1);
    const A = (r.probs.A * 100).toFixed(1);
    const card = document.createElement('div');
    card.className = 'result-card';
    card.innerHTML = `
      <div class="result-teams">
        <div class="result-team home">
          ${r.home_badge ? `<img src="${r.home_badge}" onerror="this.style.display='none'">` : ''}
          <span>${r.home}</span>
        </div>
        <div class="result-vs">VS</div>
        <div class="result-team away">
          ${r.away_badge ? `<img src="${r.away_badge}" onerror="this.style.display='none'">` : ''}
          <span>${r.away}</span>
        </div>
      </div>
      <div class="prob-bars">
        <div class="prob-row">
          <div class="prob-label">${r.home} Win</div>
          <div class="prob-track"><div class="prob-fill home" data-pct="${H}"></div></div>
          <div class="prob-pct home">${H}%</div>
        </div>
        <div class="prob-row">
          <div class="prob-label">Draw</div>
          <div class="prob-track"><div class="prob-fill draw" data-pct="${D}"></div></div>
          <div class="prob-pct draw">${D}%</div>
        </div>
        <div class="prob-row">
          <div class="prob-label">${r.away} Win</div>
          <div class="prob-track"><div class="prob-fill away" data-pct="${A}"></div></div>
          <div class="prob-pct away">${A}%</div>
        </div>
      </div>`;
    section.appendChild(card);
  });
  requestAnimationFrame(() => {
    document.querySelectorAll('.prob-fill').forEach(el => { el.style.width = el.dataset.pct + '%'; });
  });
}

// ── Season sim ────────────────────────────────────────────────────────────────
async function runSimulation() {
  const btn = document.getElementById('simBtn');
  btn.disabled = true; btn.textContent = 'Simulating…';
  document.getElementById('seasonResults').innerHTML =
    '<div class="loading"><div class="spinner"></div> Simulating 380 fixtures…</div>';
  document.getElementById('seasonInsights').innerHTML = '';

  try {
    const res  = await fetch(`${API}/api/simulate`, { method: 'POST' });
    const data = await res.json();
    renderStandings(data.standings);
    renderInsights(data.insights, data.standings);
  } catch (e) {
    document.getElementById('seasonResults').innerHTML =
      '<div class="error-msg">Simulation failed. Is the backend running?</div>';
  } finally {
    btn.disabled = false; btn.textContent = 'Simulate Season';
  }
}

function renderStandings(standings) {
  const posClass = p => p<=4?'champions':p<=6?'europa':p===7?'conference':p>=18?'relegation':'';
  const rows = standings.map(s => {
    const gdClass = s.gd > 0 ? 'pos' : s.gd < 0 ? 'neg' : '';
    const gdStr   = s.gd > 0 ? `+${s.gd}` : `${s.gd}`;
    return `
      <tr class="${posClass(s.pos)}">
        <td class="pos-cell">${s.pos}</td>
        <td class="left">
          <div class="team-cell">
            ${s.badge ? `<img src="${s.badge}" onerror="this.style.display='none'">` : ''}
            <span>${s.team}</span>
          </div>
        </td>
        <td class="pts-cell">${s.pts}</td>
        <td>${s.w}</td><td>${s.d}</td><td>${s.l}</td>
        <td>${s.gf}</td><td>${s.ga}</td>
        <td class="gd-cell ${gdClass}">${gdStr}</td>
      </tr>`;
  }).join('');

  document.getElementById('seasonResults').innerHTML = `
    <div class="standings-wrap">
      <table class="standings-table">
        <thead><tr>
          <th>#</th><th class="left">Team</th><th>Pts</th>
          <th>W</th><th>D</th><th>L</th><th>GF</th><th>GA</th><th>GD</th>
        </tr></thead>
        <tbody>${rows}</tbody>
      </table>
    </div>
    <div class="legend">
      <div class="legend-item"><div class="legend-dot" style="background:var(--accent)"></div> Champions League</div>
      <div class="legend-item"><div class="legend-dot" style="background:#4da6ff"></div> Europa League</div>
      <div class="legend-item"><div class="legend-dot" style="background:#a0a0b0"></div> Conference League</div>
      <div class="legend-item"><div class="legend-dot" style="background:var(--danger)"></div> Relegation</div>
    </div>
    <p style="margin-top:12px;font-size:12px;color:var(--muted);text-align:center">
      Simulated season · Run again for a different outcome
    </p>`;
}

function insightCard(title, dotColor, rows) {
  return `
    <div class="insight-card">
      <div class="insight-header">
        <div class="dot" style="background:${dotColor}"></div>${title}
      </div>
      ${rows}
    </div>`;
}

function teamRow(t, valHtml) {
  return `
    <div class="insight-row">
      <div class="insight-team">
        ${t.badge ? `<img src="${t.badge}" onerror="this.style.display='none'">` : ''}
        <span>${t.team}</span>
      </div>
      ${valHtml}
    </div>`;
}

function renderInsights(ins, standings) {
  if (!ins) return;
  const el = document.getElementById('seasonInsights');

  const top4Rows     = ins.top4.map(t =>
    teamRow(t, `<span class="insight-val green">${t.pts} pts</span>`)).join('');
  const relegRows    = ins.relegated.map(t =>
    teamRow(t, `<span class="insight-val red">${t.pts} pts</span>`)).join('');
  const promotedRows = ins.promoted.length
    ? ins.promoted.map(t => {
        const cls = t.pos <= 17 ? 'green' : 'red';
        return teamRow(t, `<span class="insight-val ${cls}">P${t.pos} · ${t.pts}pts</span>`);
      }).join('')
    : '<div style="padding:10px 14px;font-size:13px;color:var(--muted)">No data</div>';

  const scorerRows   = ins.top_scorers.map(t =>
    teamRow(t, `<span class="insight-val blue">${t.gf} GF</span>`)).join('');
  const gdRows       = ins.best_gd.map(t =>
    teamRow(t, `<span class="insight-val green">+${t.gd}</span>`)).join('');

  el.innerHTML =
    insightCard('Champions League', 'var(--accent)', top4Rows) +
    insightCard('Relegation Zone', 'var(--danger)', relegRows) +
    insightCard('Promoted Teams', '#a0a0b0', promotedRows) +
    insightCard('Top Scorers', '#4da6ff', scorerRows) +
    insightCard('Best Goal Diff', 'var(--accent)', gdRows);
}

boot();