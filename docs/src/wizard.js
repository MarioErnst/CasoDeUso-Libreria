import { STATE } from './state.js';

export function renderStep(container, step){
  container.innerHTML = '';
  const section = document.createElement('section');
  section.className = 'step active';

  const h = document.createElement('div');
  h.className = 'section-title';
  h.textContent = step.title;
  section.appendChild(h);

  if(step.type === 'range'){
    const wrap = document.createElement('div');
    wrap.className = 'range';
    wrap.innerHTML = `
      <input type="range" min="6000" max="30000" step="500" value="${STATE.data.precio_max}" id="range-precio">
      <div class="small" id="label-precio"></div>
    `;
    container.appendChild(section);
    container.appendChild(wrap);
    const lab = wrap.querySelector('#label-precio');
    const rng = wrap.querySelector('#range-precio');
    const fmt = n => Number(n).toLocaleString('es-CL',{style:'currency',currency:'CLP',maximumFractionDigits:0});
    lab.textContent = `Presupuesto: ${fmt(rng.value)}`;
    rng.addEventListener('input', e => { STATE.data.precio_max = Number(e.target.value); lab.textContent = `Presupuesto: ${fmt(e.target.value)}`; });
    return;
  }

  const grid = document.createElement('div');
  grid.className = 'grid';

  (step.options || []).forEach(opt => {
    const value = typeof opt === 'string' ? opt : opt.value;
    const label = typeof opt === 'string' ? opt : opt.label;
    const div = document.createElement('div');
    div.className = 'opt';
    div.textContent = label;
    div.dataset.value = value;

    div.addEventListener('click', () => {
      if(step.multi){
        const arr = STEP_VALUE_ARRAY(step.id);
        const idx = arr.indexOf(value);
        if(idx >= 0){ arr.splice(idx,1); div.classList.remove('selected'); }
        else {
          if(step.max && arr.length >= step.max) return;
          arr.push(value); div.classList.add('selected');
        }
      } else {
        SELECT_VALUE(step.id, value);
        [...grid.children].forEach(c => c.classList.remove('selected'));
        div.classList.add('selected');
      }
      container.dispatchEvent(new CustomEvent('step:changed'));
    });

    grid.appendChild(div);
  });

  section.appendChild(grid);
  container.appendChild(section);
}

function STEP_VALUE_ARRAY(stepId){
  if(stepId === 'evitar'){ if(!Array.isArray(STATE.data.evitar)) STATE.data.evitar = []; return STATE.data.evitar; }
  if(stepId === 'temas'){ if(!Array.isArray(STATE.data.temas)) STATE.data.temas = []; return STATE.data.temas; }
  return [];
}

function SELECT_VALUE(stepId, value){
  const d = STATE.data;
  switch(stepId){
    case 'modo': STATE.branch = value; break;
    case 'tipo': d.tipo = value; break;
    case 'ficGenero': d.ficGenero = value; break;
    case 'ficRitmo': d.ficRitmo = value; d.ritmo = value; break;
    case 'ficLongitud': d.ficLongitud = value; d.extension = value; break;
    case 'nfTema': d.nfTema = value; break;
    case 'nfTono': d.nfTono = value; break;
    case 'nfLongitud': d.nfLongitud = value; d.extension = value; break;
    case 'animo': d.animo = value; break;
    case 'ritmo': d.ritmo = value; break;
    case 'extension': d.extension = value; break;
    case 'formato': d.formato = value; break;
    case 'publico': d.publico = value; break;
  }
}
