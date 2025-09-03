const API = "http://127.0.0.1:8000";

export async function recomendar(payload) {
  const token = localStorage.getItem("token");
  if (!token) {
    alert("⚠️ No tienes sesión activa");
    window.location.href = "login.html";
    return;
  }

  const res = await fetch(`${API}/recomendar/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "token": token
    },
    body: JSON.stringify(payload)
  });

  if (res.status === 401) {
    alert("⚠️ Sesión expirada, vuelve a ingresar");
    localStorage.clear();
    window.location.href = "login.html";
    return;
  }

  if (!res.ok) throw new Error("Error HTTP " + res.status);
  return await res.json();
}
