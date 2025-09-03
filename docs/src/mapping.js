export function toPayload(branch, data){
  const out = {
    animo: data.animo || inferAnimo(branch, data),
    tipo: data.tipo || 'Me da igual',
    genero_tema: inferGeneroTema(branch, data),
    ritmo: data.ritmo || data.ficRitmo || 'Medio',
    extension: data.extension || data.ficLongitud || data.nfLongitud || 'Medio',
    formato: data.formato || 'Cualquiera',
    precio_max: Number(data.precio_max || 15000),
    publico: data.publico || 'Adulto',
    evitar: Array.isArray(data.evitar) ? data.evitar : [],
  };
  return out;
}

function inferAnimo(branch, d){
  if(branch === 'idea'){
    if(d.tipo === 'No ficción' && d.nfTono){
      const map = { 'Reflexivo':'Reflexivo','Inspirador':'Inspirarme','Agridulce':'Reflexivo','Esperanzador':'Desconectar' };
      return map[d.nfTono] || 'Sorpréndeme';
    }
    if(d.ficRitmo){
      const r = d.ficRitmo; return r === 'Vertiginoso' ? 'Emoción' : (r === 'Tranquilo' ? 'Desconectar' : 'Sorpréndeme');
    }
  }
  return 'Sorpréndeme';
}

function inferGeneroTema(branch, d){
  if(branch === 'idea'){
    if(d.tipo === 'Ficción') return d.ficGenero || 'No sé';
    if(d.tipo === 'No ficción') return d.nfTema || 'No sé';
    return 'No sé';
  }
  if(Array.isArray(d.temas) && d.temas.length) return d.temas[0];
  return 'No sé';
}
