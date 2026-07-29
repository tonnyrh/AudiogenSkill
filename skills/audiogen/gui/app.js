const state = { items: [], presets: {}, favoritesOnly: false, poller: null };
const $ = (selector) => document.querySelector(selector);
const escapeHtml = (text) => String(text).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: options.body ? {'Content-Type': 'application/json'} : {},
    ...options,
    body: options.body ? JSON.stringify(options.body) : undefined
  });
  if (!response.ok) {
    let message = `HTTP ${response.status}`;
    try { message = (await response.json()).error || message; } catch {}
    throw new Error(message);
  }
  return response.status === 204 ? null : response.json();
}

function toast(message) {
  const el = $('#toast');
  el.textContent = message;
  el.classList.add('show');
  clearTimeout(el.timer);
  el.timer = setTimeout(() => el.classList.remove('show'), 2600);
}

function formatDate(value) {
  return new Intl.DateTimeFormat('nb-NO', {dateStyle:'medium', timeStyle:'short'}).format(new Date(value));
}

function statusMarkup(item) {
  if (item.status === 'queued') return '<div class="job-state running">Venter i kø…</div>';
  if (item.status === 'running') return '<div class="job-state running">Genererer lyd lokalt…</div>';
  if (item.status === 'error') return `<div class="job-state error" title="${escapeHtml(item.log)}">Generering feilet · hold over for detaljer</div>`;
  return item.files.map((file, i) => `
    <div class="audio-row">
      <span class="variant-label">${String(i + 1).padStart(2, '0')}</span>
      <audio controls preload="metadata" src="/api/audio/${item.id}/${encodeURIComponent(file)}"></audio>
    </div>`).join('');
}

function render() {
  const query = $('#search').value.trim().toLowerCase();
  const shown = state.items.filter(item =>
    (!state.favoritesOnly || item.favorite) &&
    (!query || item.prompt.toLowerCase().includes(query))
  );
  $('#history').innerHTML = shown.map(item => `
    <article class="sound-card" data-id="${item.id}">
      <div class="card-top">
        <div>
          <p>${escapeHtml(item.prompt)}</p>
          <div class="meta">${formatDate(item.created_at)} · ${item.duration.toFixed(1)} s · ${item.variants} variant${item.variants === 1 ? '' : 'er'}</div>
        </div>
        <button class="favorite ${item.favorite ? 'on' : ''}" title="Favoritt">${item.favorite ? '★' : '☆'}</button>
      </div>
      ${statusMarkup(item)}
      <div class="card-actions">
        <button class="refine">↗ Finjuster</button>
        <button class="copy">⧉ Kopier prompt</button>
        <button class="delete" title="Slett">Slett</button>
      </div>
    </article>`).join('');
  $('#empty').classList.toggle('hidden', shown.length > 0);
  bindCards();
  const active = state.items.some(item => ['queued', 'running'].includes(item.status));
  if (active && !state.poller) state.poller = setInterval(loadHistory, 2000);
  if (!active && state.poller) { clearInterval(state.poller); state.poller = null; }
}

function bindCards() {
  document.querySelectorAll('.sound-card').forEach(card => {
    const item = state.items.find(x => x.id === card.dataset.id);
    card.querySelector('.favorite').onclick = async () => {
      await api(`/api/history/${item.id}`, {method:'PATCH', body:{favorite:!item.favorite}});
      item.favorite = !item.favorite; render();
    };
    card.querySelector('.refine').onclick = () => {
      $('#prompt').value = item.prompt;
      $('#duration').value = item.duration;
      $('#variants').value = item.variants;
      $('#parent-id').value = item.id;
      $('#duration-value').textContent = `${item.duration.toFixed(1)} s`;
      $('#char-count').textContent = `${item.prompt.length} / 1000`;
      $('#refine-note').textContent = 'Finjusterer en tidligere generering. Endre prompten og generer på nytt.';
      $('#refine-note').classList.remove('hidden');
      $('#prompt').focus();
      window.scrollTo({top: $('.workspace').offsetTop - 85, behavior:'smooth'});
    };
    card.querySelector('.copy').onclick = async () => {
      await navigator.clipboard.writeText(item.prompt);
      toast('Prompt kopiert');
    };
    card.querySelector('.delete').onclick = async () => {
      if (!confirm('Slette denne genereringen og WAV-filene?')) return;
      try {
        await api(`/api/history/${item.id}`, {method:'DELETE'});
        state.items = state.items.filter(x => x.id !== item.id); render(); toast('Genereringen er slettet');
      } catch (error) { toast(error.message); }
    };
  });
}

async function loadHistory() {
  try {
    const data = await api('/api/history');
    state.items = data.items;
    state.presets = data.presets;
    if (!$('#preset-list').children.length) {
      const featured = ['ui_click','ui_confirm','reward','hit','spell','ambient'];
      $('#preset-list').innerHTML = featured.map(name => `<button class="preset" type="button" data-name="${name}">${name.replace('_',' ')}</button>`).join('');
      document.querySelectorAll('.preset').forEach(button => button.onclick = () => {
        $('#prompt').value = state.presets[button.dataset.name];
        $('#prompt').dispatchEvent(new Event('input'));
      });
    }
    render();
  } catch (error) { toast(`Kunne ikke hente historikk: ${error.message}`); }
}

async function checkHealth() {
  const dot = $('#health-dot'), text = $('#health-text');
  dot.className = 'status-dot checking'; text.textContent = 'Sjekker AudioGen…';
  try {
    const data = await api('/api/health');
    dot.className = `status-dot ${data.ok ? '' : 'error'}`;
    text.textContent = data.ok ? 'AudioGen er klar' : 'AudioGen mangler konfigurasjon';
    text.title = data.ok ? `${data.checks.python_version || ''} · ${data.model}` : JSON.stringify(data.checks);
  } catch {
    dot.className = 'status-dot error'; text.textContent = 'Kunne ikke sjekke AudioGen';
  }
}

$('#generator-form').onsubmit = async event => {
  event.preventDefault();
  const button = $('#generate');
  button.disabled = true;
  button.querySelector('span:last-child').textContent = 'Starter…';
  try {
    const item = await api('/api/generate', {method:'POST', body:{
      prompt: $('#prompt').value,
      duration: Number($('#duration').value),
      variants: Number($('#variants').value),
      parent_id: $('#parent-id').value || null
    }});
    state.items.unshift(item);
    $('#parent-id').value = '';
    $('#refine-note').classList.add('hidden');
    render();
    toast('Genereringen er startet');
    window.scrollTo({top: $('.library').offsetTop - 70, behavior:'smooth'});
  } catch (error) { toast(error.message); }
  finally {
    button.disabled = false;
    button.querySelector('span:last-child').textContent = 'Generer lyd';
  }
};

$('#prompt').oninput = event => $('#char-count').textContent = `${event.target.value.length} / 1000`;
$('#duration').oninput = event => $('#duration-value').textContent = `${Number(event.target.value).toFixed(1)} s`;
$('#search').oninput = render;
$('#favorites-filter').onclick = event => {
  state.favoritesOnly = !state.favoritesOnly;
  event.currentTarget.setAttribute('aria-pressed', state.favoritesOnly);
  render();
};
$('#check-health').onclick = checkHealth;
$('#surprise').onclick = () => {
  const ideas = [
    'Kort glassaktig energipuls, lys og futuristisk, sci-fi UI, uten musikk',
    'Tung steindør som låses opp, dyp mekanisk resonans, mørkt fantasyspill',
    'Myk belønningslyd med tre varme klokktoner, vennlig mobilspill',
    'Rask elektrisk magisk gnist som stiger og forsvinner, arkadespill'
  ];
  $('#prompt').value = ideas[Math.floor(Math.random() * ideas.length)];
  $('#prompt').dispatchEvent(new Event('input'));
};

loadHistory();
checkHealth();
