export async function recomendar(payload){
  const res = await fetch('http://127.0.0.1:8000/recomendar/', {
    method: 'POST', headers: { 'Content-Type':'application/json' }, body: JSON.stringify(payload)
  });
  if(!res.ok) throw new Error('Error HTTP '+res.status);
  return await res.json();
}
