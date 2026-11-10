// app.js — Footy AI frontend logic with Hungarian Support

const API = '';
let allTeams = [];
let rowCount = 0;
let currentLang = localStorage.getItem('lang') || 'en';

// ── Translations ──────────────────────────────────────────────────────────────
const translations = {
  en: {
    matchPredict: "Match Predict",
    seasonSim: "Season Sim",
    addRow: "Add another match",
    predict: "Predict",
    simSeason: "Simulate Season",
    simulating: "Simulating 380 fixtures…",
    nextGameweeks: "Next 2 Gameweeks",
    homeTeam: "Home team",
    awayTeam: "Away team",
    searchTeam: "Search team...",
    noTeams: "No teams found",
    win: "Win",
    draw: "Draw",
    tableTeam: "Team",
    pts: "Pts",
    championsLeague: "Champions League",
    europaLeague: "Europa League",
    conferenceLeague: "Conference League",
    relegationZone: "Relegation Zone",
    promotedTeams: "Promoted Teams",
    topScorers: "Top Scorers",
    bestGd: "Best Goal Diff",
    simNote: "Simulated season · Run again for a different outcome",
    backendError: "Could not connect to backend. Make sure controller.py is running.",
    predictError: "Prediction failed. Is the backend running?",
    simError: "Simulation failed. Is the backend running?",
    selectMatchError: "Please select at least one full match.",
    noFixtures: "No upcoming fixtures found",
    fixturesUnavailable: "Fixtures unavailable"
  },
  hu: {
    matchPredict: "Mérkőzés Tipp",
    seasonSim: "Szezon Szimuláció",
    addRow: "Új mérkőzés hozzáadása",
    predict: "Elemzés",
    simSeason: "Szezon Szimulációja",
    simulating: "380 mérkőzés szimulációja…",
    nextGameweeks: "Következő 2 Forduló",
    homeTeam: "Hazai csapat",
    awayTeam: "Vendég csapat",
    searchTeam: "Csapat keresése...",
    noTeams: "Nincs találat",
    win: "Győzelem",
    draw: "Döntetlen",
    tableTeam: "Csapat",
    pts: "Pont",
    championsLeague: "Bajnokok Ligája",
    europaLeague: "Európa Liga",
    conferenceLeague: "Konferencia Liga",
    relegationZone: "Kiesőzóna",
    promotedTeams: "Feljutó Csapatok",
    topScorers: "Legjobb Gólszerzők",
    bestGd: "Legjobb Gólkülönbség",
    simNote: "Szimulált szezon · Futtassa újra az eltérő eredményért",
    backendError: "Nem sikerült csatlakozni a szerverhez. Ellenőrizze, hogy fut-e a controller.py.",
    predictError: "Az előrejelzés sikertelen. Fut a szerver?",
    simError: "A szimuláció sikertelen. Fut a szerver?",
    selectMatchError: "Kérjük, válasszon ki legalább egy teljes mérkőzést.",
    noFixtures: "Nincsenek közelgő mérkőzések",
    fixturesUnavailable: "A menetrend nem érhető el"
  }
};

function t(key) {
  return translations[currentLang][key] || translations['en'][key] || key;
}

// ── Language Toggle ───────────────────────────────────────────────────────────
function initLang() {
  applyLang(localStorage.getItem('lang') || 'en');
}

function applyLang(lang) {
  currentLang = lang;
  localStorage.setItem('lang', lang);
  
  // Sync toggle switch state (checked = English, unchecked = Hungarian)
  const checkbox = document.getElementById('langCheckbox');
  if (checkbox) checkbox.checked = (lang === 'en');
  
  // Update static text elements
  document.querySelector('[data-mode="match"]').textContent = t('matchPredict');
  document.querySelector('[data-mode="season"]').textContent = t('seasonSim');
  document.querySelector('.add-row-btn').innerHTML = `<span class="plus">+</span> ${t('addRow')}`;
  document.getElementById('predictBtn').textContent = t('predict');
  document.getElementById('simBtn').textContent = t('simSeason');
  
  const sidebarHeader = document.querySelector('.sidebar-header');
  if (sidebarHeader) sidebarHeader.textContent = t('nextGameweeks');

  // Re-render placeholders for active team selects
  document.querySelectorAll('.custom-select').forEach(wrap => {
    const placeholderEl = wrap.querySelector('.placeholder');
    if (placeholderEl && !wrap.dataset.value) {
      placeholderEl.textContent = wrap.id.startsWith('home_') ? t('homeTeam') : t('awayTeam');
    }
    const searchInput = wrap.querySelector('.select-search');
    if (searchInput) searchInput.placeholder = t('searchTeam');
  });
}

function toggleLanguage() {
  applyLang(currentLang === 'en' ? 'hu' : 'en');
  // Refresh current displays if data is already loaded
  if (allTeams.length > 0) {
    loadFixtures();
  }
}

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
  initLang();
  try {
    const res  = await fetch(`${API}/api/teams`);
    const data = await res.json();
    allTeams   = data.teams;
    document.getElementById('seasonBadge').textContent = data.season;
    addMatchRow();
    loadFixtures();
  } catch (e) {
    document.getElementById('matchRows').innerHTML =
      `<div class="error-msg">${t('backendError')}</div>`;
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
      <input class="select-search" placeholder="${t('searchTeam')}"
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
    opts.innerHTML = `<div class="select-option no-results">${t('noTeams')}</div>`;
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

  row.appendChild(createSelect(`home_${rowCount}`, t('homeTeam')));
  row.appendChild(vs);
  row.appendChild(createSelect(`away_${rowCount}`, t('awayTeam')));
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
    sidebar.innerHTML = `<div style="padding:14px;font-size:13px;color:var(--muted)">${t('fixturesUnavailable')}</div>`;
  }
}

function renderFixtures(gameweeks) {
  const sidebar = document.getElementById('fixturesSidebar');
  if (!gameweeks || !gameweeks.length) {
    sidebar.innerHTML = `<div style="padding:14px;font-size:13px;color:var(--muted)">${t('noFixtures')}</div>`;
    return;
  }

  sidebar.innerHTML = gameweeks.map((gw) => {
    const localeCode = currentLang === 'hu' ? 'hu-HU' : 'en-GB';
    const dateLabel = gw.date ? new Date(gw.date).toLocaleDateString(localeCode, { weekday:'short', day:'numeric', month:'short' }) : '';
    
    // Use the actual round number/title sent from the backend instead of loop index
    const roundNumber = gw.round || gw.round_num || '1';
    const gwText = currentLang === 'hu' ? `${roundNumber}. Forduló` : `Gameweek ${roundNumber}`;
    
    const matchRows = (gw.matches || []).map(m => `
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
        <div class="gameweek-label">${gwText} ${dateLabel ? '· ' + dateLabel : ''}</div>
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
      `<div class="error-msg">${t('selectMatchError')}</div>`;
    return;
  }

  const btn = document.getElementById('predictBtn');
  btn.disabled = true; btn.textContent = currentLang === 'hu' ? 'Elemzés...' : 'Predicting...';
  document.getElementById('matchResults').innerHTML =
    `<div class="loading"><div class="spinner"></div> ${currentLang === 'hu' ? 'Előrejelzés futtatása…' : 'Running predictions…'}</div>`;

  try {
    const res  = await fetch(`${API}/api/predict`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ matches }),
    });
    renderMatchResults((await res.json()).results);
  } catch (e) {
    document.getElementById('matchResults').innerHTML =
      `<div class="error-msg">${t('predictError')}</div>`;
  } finally {
    btn.disabled = false; btn.textContent = t('predict');
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
          <div class="prob-label">${r.home} ${t('win')}</div>
          <div class="prob-track"><div class="prob-fill home" data-pct="${H}"></div></div>
          <div class="prob-pct home">${H}%</div>
        </div>
        <div class="prob-row">
          <div class="prob-label">${t('draw')}</div>
          <div class="prob-track"><div class="prob-fill draw" data-pct="${D}"></div></div>
          <div class="prob-pct draw">${D}%</div>
        </div>
        <div class="prob-row">
          <div class="prob-label">${r.away} ${t('win')}</div>
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

// ── Season sim ────────────────────────────────________________________________
async function runSimulation() {
  const btn = document.getElementById('simBtn');
  btn.disabled = true; btn.textContent = currentLang === 'hu' ? 'Szimuláció…' : 'Simulating…';
  document.getElementById('seasonResults').innerHTML =
    `<div class="loading"><div class="spinner"></div> ${t('simulating')}</div>`;
  document.getElementById('seasonInsights').innerHTML = '';

  try {
    const res  = await fetch(`${API}/api/simulate`, { method: 'POST' });
    const data = await res.json();
    renderStandings(data.standings);
    renderInsights(data.insights, data.standings);
  } catch (e) {
    document.getElementById('seasonResults').innerHTML =
      `<div class="error-msg">${t('simError')}</div>`;
  } finally {
    btn.disabled = false; btn.textContent = t('simSeason');
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
          <th>#</th><th class="left">${t('tableTeam')}</th><th>${t('pts')}</th>
          <th>W</th><th>D</th><th>L</th><th>GF</th><th>GA</th><th>GD</th>
        </tr></thead>
        <tbody>${rows}</tbody>
      </table>
    </div>
    <div class="legend">
      <div class="legend-item"><div class="legend-dot" style="background:var(--accent)"></div> ${t('championsLeague')}</div>
      <div class="legend-item"><div class="legend-dot" style="background:#4da6ff"></div> ${t('europaLeague')}</div>
      <div class="legend-item"><div class="legend-dot" style="background:#a0a0b0"></div> ${t('conferenceLeague')}</div>
      <div class="legend-item"><div class="legend-dot" style="background:var(--danger)"></div> ${t('relegationZone')}</div>
    </div>
    <p style="margin-top:12px;font-size:12px;color:var(--muted);text-align:center">
      ${t('simNote')}
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
    <div class="insight-row" style="display: flex; justify-content: space-between; align-items: center;">
      <span class="insight-team-name">${t.team}</span>
      <div class="insight-stat">${valHtml}</div>
    </div>`;
}

function renderInsights(ins, standings) {
  if (!ins) return;
  const el = document.getElementById('seasonInsights');

  /*const top4Rows     = ins.top4.map(t =>
    teamRow(t, `<span class="insight-val green">${t.pts} pts</span>`)).join('');
  const relegRows    = ins.relegated.map(t =>
    teamRow(t, `<span class="insight-val red">${t.pts} pts</span>`)).join('');*/
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
    /*insightCard(t('championsLeague'), 'var(--accent)', top4Rows) +
    insightCard(t('relegationZone'), 'var(--danger)', relegRows) +*/
    insightCard(t('promotedTeams'), '#a0a0b0', promotedRows) +
    insightCard(t('topScorers'), '#4da6ff', scorerRows) +
    insightCard(t('bestGd'), 'var(--accent)', gdRows);
}

boot();
