import { STATE } from './state.js';
import { TREE } from './tree.js';
import { renderStep } from './wizard.js';
import { toPayload } from './mapping.js';
import { recomendar } from './api.js';

const elSteps = document.getElementById('steps');
const btnNext = document.getElementById('btnNext');
const btnBack = document.getElementById('btnBack');
const bar = document.getElementById('progressBar');
const labelText = document.getElementById('progressText');
const labelPct = document.getElementById('progressPct');

const results = document.getElementById('results');
const loading = document.getElementById('loading');
const cards = document.getElementById('cards');
const empty = document.getElementById('empty');
const btnAgain = document.getElementById('btnAgain');
const btnReset = document.getElementById('btnReset');

// --- Auth simple ---
const token = localStorage.getItem("token");
if (!token) {
  window.location.href = "login.html";
}
document.getElementById("nombreUsuario").textContent =
  "Hola, " + (localStorage.getItem("nombre") || "Usuario");

document.getElementById("btnLogout").addEventListener("click", () => {
  localStorage.clear();
  window.location.href = "login.html";
});

// --- Construcción de pasos ---
function buildSteps() {
  const steps = [...TREE.start];
  if (STATE.branch === 'idea') steps.push(...TREE.idea);
  if (STATE.branch === 'discover') steps.push(...TREE.discover);
  STATE.steps = steps;
}

// --- Mostrar paso actual ---
function show(idx) {
  STATE.idx = idx;
  const step = STATE.steps[idx];
  if (step && step.when && !step.when(STATE.data)) return show(idx + 1);

  elSteps.innerHTML = '';
  renderStep(elSteps, step);

  const total = STATE.steps.filter(s => !s.when || s.when(STATE.data)).length;
  const current = Math.min(idx + 1, total);
  const pct = Math.round((current - 1) / (total - 1) * 100);
  bar.style.width = pct + '%';
  labelText.textContent = `Paso ${current} de ${total}`;
  labelPct.textContent = pct + '%';

  btnBack.disabled = (idx === 0);
  btnNext.textContent = (current === total) ? 'Buscar' : 'Siguiente';
  btnNext.disabled = !isStepComplete(step);

  elSteps.addEventListener('step:changed', () => {
    btnNext.disabled = !isStepComplete(step);
  }, { once: true });
}

function isStepComplete(step) {
  const d = STATE.data;
  switch (step.id) {
    case 'destino': return !!d.destino;
    case 'modo': return !!STATE.branch;
    case 'tipo': return !!d.tipo;
    case 'ficGenero': return !!d.ficGenero;
    case 'ficLongitud': return !!d.ficLongitud;
    case 'nfTema': return !!d.nfTema;
    case 'nfTono': return !!d.nfTono;
    case 'nfLongitud': return !!d.nfLongitud;
    case 'animo': return !!d.animo;
    case 'temas': return Array.isArray(d.temas) && d.temas.length > 0;
    case 'extension': return !!d.extension;
    case 'formato': return !!d.formato;
    case 'precio': return true;
    case 'publico': return !!d.publico;
    case 'evitar': return true;
    default: return true;
  }
}

// --- Botón siguiente ---
btnNext.addEventListener('click', async () => {
  const step = STATE.steps[STATE.idx];

  if (step.id === 'modo') {
    buildSteps();
    return show(STATE.idx + 1);
  }

  let nextIdx = STATE.idx + 1;
  while (nextIdx < STATE.steps.length && STATE.steps[nextIdx].when && !STATE.steps[nextIdx].when(STATE.data)) {
    nextIdx++;
  }

  if (nextIdx < STATE.steps.length) {
    show(nextIdx);
  } else {
    // Mostrar resultados
    results.classList.remove('hidden');
    loading.classList.remove('hidden');
    cards.innerHTML = '';
    empty.classList.add('hidden');

    try {
      const payload = toPayload(STATE.branch, STATE.data);
      const data = await recomendar(payload);
      renderResults(data?.recomendaciones || []);
    } catch (e) {
      console.error("❌ error al recomendar:", e);
      empty.classList.remove('hidden');
    } finally {
      loading.classList.add('hidden');
    }
  }
});

// --- Botón atrás ---
btnBack.addEventListener('click', () => {
  if (STATE.idx > 0) show(STATE.idx - 1);
});

// --- Nueva búsqueda ---
btnAgain.addEventListener('click', () => {
  results.classList.add('hidden');
  STATE.idx = 0;
  STATE.branch = null;
  STATE.steps = [];
  STATE.data = { precio_max: 15000, evitar: [] };
  show(0);
});

// --- Reset total ---
btnReset.addEventListener('click', () => {
  location.reload();
});

// --- Render de resultados ---
function renderResults(list) {
  if (!list.length) {
    empty.classList.remove('hidden');
    return;
  }

  cards.innerHTML = '';
  list.forEach(it => {
    const article = document.createElement('article');
    article.className = 'card';

    const row = document.createElement('div');
    row.className = 'row';
    row.style.justifyContent = 'space-between';
    row.style.alignItems = 'center';

    const tag = document.createElement('span');
    tag.className = 'tag';
    tag.textContent = `Match ${it.match_score ?? 0}/100`;

    const price = document.createElement('span');
    price.className = 'price';
    if (it.precio_clp && !isNaN(Number(it.precio_clp))) {
      price.textContent = Number(it.precio_clp).toLocaleString('es-CL', {
        style: 'currency', currency: 'CLP'
      });
    }

    row.appendChild(tag);
    row.appendChild(price);

    const title = document.createElement('div');
    title.className = 'title';
    title.textContent = it.nombre || 'Sin título';

    const meta = document.createElement('div');
    meta.className = 'meta';
    meta.textContent = [
      it.tipo || '',
      it.genero || '',
      it.formato || '',
      it.publico || ''
    ].filter(Boolean).join(' · ');

    article.appendChild(row);
    article.appendChild(title);
    article.appendChild(meta);

    if (it.sinopsis_1linea) {
      const sinopsis = document.createElement('p');
      sinopsis.className = 'meta';
      sinopsis.textContent = it.sinopsis_1linea;
      article.appendChild(sinopsis);
    }

    const motivo = document.createElement('p');
    motivo.style.lineHeight = '1.5';
    motivo.textContent = it.motivo || '';
    article.appendChild(motivo);

    cards.appendChild(article);
  });
}

// --- init ---
STATE.steps = [...TREE.start];
show(0);
