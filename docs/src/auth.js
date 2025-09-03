const API = "http://127.0.0.1:8000";

// --- Registro ---
document.getElementById("registroForm").addEventListener("submit", async e => {
  e.preventDefault();
  const data = Object.fromEntries(new FormData(e.target));

  const res = await fetch(`${API}/registro`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data)
  });

  if (res.ok) {
    alert("✅ Cuenta creada, ahora inicia sesión con tu teléfono");
    e.target.reset();
  } else {
    const err = await res.json();
    alert("❌ " + err.detail);
  }
});

// --- Login ---
document.getElementById("loginForm").addEventListener("submit", async e => {
  e.preventDefault();
  const data = Object.fromEntries(new FormData(e.target));

  const res = await fetch(`${API}/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data)
  });

  if (res.ok) {
    const json = await res.json();
    localStorage.setItem("token", json.usuario.token);
    localStorage.setItem("nombre", json.usuario.nombre);
    window.location.href = "index.html"; // ir al wizard
  } else {
    const err = await res.json();
    alert("❌ " + err.detail);
  }
});
