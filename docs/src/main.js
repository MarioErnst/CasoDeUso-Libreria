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

function buildSteps(){
  const steps = [];
  steps.push(TREE.start);
  if(STATE.branch === 'idea') steps.push(...TREE.idea);
  if(STATE.branch === 'discover') steps.push(...TREE.discover);
  STATE.steps = steps;
}

function show(idx){
  STATE.idx = idx;
  const step = STATE.steps[idx];
  if(step && step.when && !step.when(STATE.data)){
    return show(idx+1);
  }
  elSteps.innerHTML = '';
  renderStep(elSteps, step);

  const total = STATE.steps.filter(s => !s.when || s.when(STATE.data)).length;
  const current = Math.min(idx+1, total);
  const pct = Math.round((current-1)/(total-1)*100);
  bar.style.width = pct + '%';
  labelText.textContent = `Paso ${current} de ${total}`;
  labelPct.textContent = pct + '%';

  btnBack.disabled = (idx === 0);
  btnNext.textContent = (current === total) ? 'Buscar' : 'Siguiente';
  btnNext.disabled = !isStepComplete(step);

  elSteps.addEventListener('step:changed', () => {
    btnNext.disabled = !isStepComplete(step);
  }, { once:false });
}

function isStepComplete(step){
  const d = STATE.data;
  switch(step.id){
    case 'modo': return !!STATE.branch;
    case 'tipo': return !!d.tipo;
    case 'ficGenero': return !!d.ficGenero;
    case 'ficRitmo': return !!d.ficRitmo;
    case 'ficLongitud': return !!d.ficLongitud;
    case 'nfTema': return !!d.nfTema;
    case 'nfTono': return !!d.nfTono;
    case 'nfLongitud': return !!d.nfLongitud;
    case 'animo': return !!d.animo;
    case 'temas': return Array.isArray(d.temas) && d.temas.length>0;
    case 'ritmo': return !!d.ritmo;
    case 'extension': return !!d.extension;
    case 'formato': return !!d.formato;
    case 'precio': return true;
    case 'publico': return !!d.publico;
    case 'evitar': return true;
    default: return true;
  }
}

btnNext.addEventListener('click', async () => {
  const step = STATE.steps[STATE.idx];
  if(step.id === 'modo'){
    buildSteps();
    return show(STATE.idx + 1);
  }
  let nextIdx = STATE.idx + 1;
  while(nextIdx < STATE.steps.length && STATE.steps[nextIdx].when && !STATE.steps[nextIdx].when(STATE.data)){
    nextIdx++;
  }
  if(nextIdx < STATE.steps.length){
    show(nextIdx);
  } else {
    results.classList.remove('hidden');
    loading.classList.remove('hidden');
    cards.innerHTML = ''; empty.classList.add('hidden');
    try{
      const payload = toPayload(STATE.branch, STATE.data);
      const data = await recomendar(payload);
      renderResults(data?.recomendaciones || []);
    }catch(e){ console.error(e); empty.classList.remove('hidden'); }
    finally{ loading.classList.add('hidden'); }
  }
});

btnBack.addEventListener('click', () => {
  if(STATE.idx > 0) show(STATE.idx - 1);
});

btnAgain.addEventListener('click', () => {
  results.classList.add('hidden');
  STATE.idx = 0; STATE.branch = null; STATE.steps = []; STATE.data = { precio_max:15000, evitar:[] };
  show(0);
});

btnReset.addEventListener('click', () => location.reload());

function renderResults(list){
  if(!list.length){ empty.classList.remove('hidden'); return; }
  cards.innerHTML = list.map(it => {
    const meta = `${it.tipo} · ${it.genero} · ${it.formato} · ${it.publico}`;
    return `
      <article class="card">
        <div class="row" style="justify-content:space-between;align-items:center;">
          <span class="tag">Match ${it.match_score}/100</span>
          <span class="price">${it.precio_clp.toLocaleString('es-CL',{style:'currency',currency:'CLP'})}</span>
        </div>
        <div class="title">${it.nombre}</div>
        <div class="meta">${meta}</div>
        ${it.sinopsis_1linea ? `<p class="meta">${it.sinopsis_1linea}</p>` : ''}
        <p style="line-height:1.5">${it.motivo}</p>
      </article>`;
  }).join('');
}

// init
STATE.steps = [TREE.start];
show(0);
