const API = '';   // same origin — Flask serves both frontend and API
let allTeams = [];
let rowCount = 0;

// ── Boot ──────────────────────────────────────────────────────────────────────
async function boot() {
  try {
    const res  = await fetch(`${API}/api/teams`);
    const data = await res.json();
    allTeams   = data.teams;
    document.getElementById('seasonBadge').textContent = data.season;
    addMatchRow();   // first permanent row
  } catch(e) {
    document.getElementById('matchRows').innerHTML =
      `<div class="error-msg">Could not connect to backend. Make sure controller.py is running.</div>`;
  }
}

// ── Mode switch ───────────────────────────────────────────────────────────────
function setMode(mode) {
  document.querySelectorAll('.mode-btn').forEach(b => b.classList.toggle('active', b.dataset.mode === mode));
  document.querySelectorAll('.panel').forEach(p => p.classList.toggle('active', p.id === mode + 'Panel'));
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
      <input class="select-search" placeholder="Search team..." oninput="filterOptions('${id}', this.value)" autocomplete="off">
      <div class="select-options" id="${id}_opts"></div>
    </div>
  `;

  renderOptions(id, allTeams, wrap);
  return wrap;
}

function renderOptions(id, teams, wrapEl) {
  const wrap = wrapEl || document.getElementById(id);
  const opts = document.getElementById(`${id}_opts`);
  if (!opts) return;

  opts.innerHTML = '';
  if (teams.length === 0) {
    opts.innerHTML = '<div class="select-option no-results">No teams found</div>';
    return;
  }
  teams.forEach(t => {
    const div = document.createElement('div');
    div.className = 'select-option' + (wrap.dataset.value === t.name ? ' selected' : '');
    div.innerHTML = t.badge
      ? `<img src="${t.badge}" onerror="this.style.display='none'">`
      : '';
    div.innerHTML += `<span>${t.name}</span>`;
    div.onclick = () => selectTeam(id, t);
    opts.appendChild(div);
  });
}

function toggleDropdown(id) {
  const drop    = document.getElementById(`${id}_drop`);
  const display = drop.previousElementSibling;
  const isOpen  = drop.classList.contains('open');

  // close all others
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
  const filtered = query
    ? allTeams.filter(t => t.name.toLowerCase().includes(query.toLowerCase()))
    : allTeams;
  renderOptions(id, filtered);
}

function selectTeam(id, team) {
  const wrap    = document.getElementById(id);
  const display = wrap.querySelector('.select-display');
  const drop    = wrap.querySelector('.select-dropdown');

  wrap.dataset.value = team.name;

  display.innerHTML = team.badge
    ? `<img src="${team.badge}" onerror="this.style.display='none'">`
    : '';
  display.innerHTML += `<span class="team-name">${team.name}</span><span class="chevron">▼</span>`;
  display.classList.remove('open');
  drop.classList.remove('open');

  // reset search
  drop.querySelector('.select-search').value = '';
  renderOptions(id, allTeams, wrap);
}

// close dropdowns on outside click
document.addEventListener('click', e => {
  if (!e.target.closest('.custom-select')) {
    document.querySelectorAll('.select-dropdown.open').forEach(d => {
      d.classList.remove('open');
      d.previousElementSibling.classList.remove('open');
    });
  }
});

// ── Match rows ────────────────────────────────────────────────────────────────
function addMatchRow() {
  rowCount++;
  const rowId  = `row_${rowCount}`;
  const homeId = `home_${rowCount}`;
  const awayId = `away_${rowCount}`;

  const row = document.createElement('div');
  row.className = 'match-row';
  row.id        = rowId;

  const homeSelect = createSelect(homeId, 'Home team');
  const awaySelect = createSelect(awayId, 'Away team');

  const vs  = document.createElement('div');
  vs.className = 'vs-label';
  vs.textContent = 'VS';

  const delBtn = document.createElement('button');
  delBtn.className = 'delete-btn';
  delBtn.title     = 'Remove row';
  delBtn.innerHTML = '🗑';
  delBtn.onclick   = () => removeRow(rowId);

  row.appendChild(homeSelect);
  row.appendChild(vs);
  row.appendChild(awaySelect);
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
  rows.forEach((r, i) => {
    const btn = r.querySelector('.delete-btn');
    btn.disabled = (rows.length === 1);
  });
}

// ── Predict ───────────────────────────────────────────────────────────────────
async function runPrediction() {
  const rows   = document.querySelectorAll('#matchRows .match-row');
  const matches = [];

  rows.forEach(r => {
    const homeEl = r.querySelector('[id^="home_"]');
    const awayEl = r.querySelector('[id^="away_"]');
    const home   = homeEl?.dataset.value;
    const away   = awayEl?.dataset.value;
    if (home && away) matches.push({ home, away });
  });

  if (matches.length === 0) {
    document.getElementById('matchResults').innerHTML =
      '<div class="error-msg">Please select at least one full match.</div>';
    return;
  }

  const btn = document.getElementById('predictBtn');
  btn.disabled  = true;
  btn.textContent = 'Predicting...';
  document.getElementById('matchResults').innerHTML =
    '<div class="loading"><div class="spinner"></div> Running predictions…</div>';

  try {
    const res  = await fetch(`${API}/api/predict`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ matches }),
    });
    const data = await res.json();
    renderMatchResults(data.results);
  } catch(e) {
    document.getElementById('matchResults').innerHTML =
      '<div class="error-msg">Prediction failed. Is the backend running?</div>';
  } finally {
    btn.disabled    = false;
    btn.textContent = 'Predict';
  }
}

function renderMatchResults(results) {
  const section = document.getElementById('matchResults');
  section.innerHTML = '';

  results.forEach(r => {
    if (r.error) {
      section.innerHTML += `<div class="error-msg">${r.home} vs ${r.away}: ${r.error}</div>`;
      return;
    }

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
      </div>
    `;
    section.appendChild(card);
  });

  // animate bars after DOM insertion
  requestAnimationFrame(() => {
    document.querySelectorAll('.prob-fill').forEach(el => {
      el.style.width = el.dataset.pct + '%';
    });
  });
}

// ── Season sim ────────────────────────────────────────────────────────────────
async function runSimulation() {
  const btn = document.getElementById('simBtn');
  btn.disabled    = true;
  btn.textContent = 'Simulating…';
  document.getElementById('seasonResults').innerHTML =
    '<div class="loading"><div class="spinner"></div> Simulating 380 fixtures…</div>';

  try {
    const res  = await fetch(`${API}/api/simulate`, { method: 'POST' });
    const data = await res.json();
    renderStandings(data.standings, data.season);
  } catch(e) {
    document.getElementById('seasonResults').innerHTML =
      '<div class="error-msg">Simulation failed. Is the backend running?</div>';
  } finally {
    btn.disabled    = false;
    btn.textContent = 'Simulate Season';
  }
}

function renderStandings(standings, season) {
  const posClass = pos => {
    if (pos <= 4)  return 'champions';
    if (pos <= 6)  return 'europa';
    if (pos === 7) return 'conference';
    if (pos >= 18) return 'relegation';
    return '';
  };

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
        <td>${s.w}</td>
        <td>${s.d}</td>
        <td>${s.l}</td>
        <td>${s.gf}</td>
        <td>${s.ga}</td>
        <td class="gd-cell ${gdClass}">${gdStr}</td>
      </tr>
    `;
  }).join('');

  document.getElementById('seasonResults').innerHTML = `
    <div class="standings-wrap">
      <table class="standings-table">
        <thead>
          <tr>
            <th>#</th>
            <th class="left">Team</th>
            <th>Pts</th>
            <th>W</th>
            <th>D</th>
            <th>L</th>
            <th>GF</th>
            <th>GA</th>
            <th>GD</th>
          </tr>
        </thead>
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
    </p>
  `;
}

boot();