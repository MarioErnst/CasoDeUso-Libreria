# -*- coding: utf-8 -*-
"""
Redactor IA compatible con versiones antiguas del SDK (usa Chat Completions).
Devuelve por libro:
- "motivo": 2–4 oraciones explicables, sin spoilers
- "sinopsis_1linea": logline de 1 oración, prudente

Variables de entorno:
  OPENAI_API_KEY=...
  OPENAI_MODEL=gpt-4o-mini   (por defecto)
  REDACTOR_TONO=neutro|entusiasta|librero  (opcional)
"""

import os
import json
from typing import Dict, List
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from openai import OpenAI

# Cargar .env si está disponible (opcional)
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
TONO = os.getenv("REDACTOR_TONO", "neutro")

def _get_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY no configurada. Revisa tu .env o variables de entorno.")
    return OpenAI(api_key=api_key)

SYSTEM = (
    "Eres un redactor de una librería chilena. Escribe en español de Chile, claro y cálido. "
    "Prohibido inventar hechos específicos (premios, cifras, fechas, lugares, nombres de personajes) "
    "a menos que vengan en los datos. Evita spoilers. Longitud: 2–4 oraciones en 'motivo' y 1 sola oración en 'sinopsis_1linea'."
)

def _build_prompt(preferencias: Dict, explicaciones_motor: List[str], libros: List[Dict]) -> str:
    lines: List[str] = []
    lines.append(
        "Tarea: para cada libro, redacta un 'motivo' (2–4 oraciones) que explique por qué el motor lo recomendó, "
        "y una 'sinopsis_1linea' breve sin spoilers."
    )
    lines.append(f"Tono solicitado: {TONO} (si no aplica, usa tono neutro).")

    lines.append("\nPreferencias del usuario (no inventes nada fuera de esto):")
    lines.append(str(preferencias))

    lines.append("\nLibros en el orden dado (NO reordenar):")
    for i, l in enumerate(libros, 1):
        desc = l.get("descripcion") or ""
        lines.append(
            f"{i}. {l.get('titulo')} — {l.get('autor')} | Tipo: {l.get('tipo')} | Género: {l.get('genero')} | "
            f"Ritmo: {l.get('ritmo')} | Páginas: {l.get('paginas')} | Tono: {l.get('tono')} | Público: {l.get('publico')} | "
            f"Formatos: {', '.join(l.get('formato', []))} | Precio CLP: {l.get('precio_clp')} | "
            f"Descripción opcional: {desc[:240]}"
        )

    lines.append("\nSeñales activadas por el motor (mismo orden):")
    for i, s in enumerate(explicaciones_motor, 1):
        lines.append(f"{i}. {s}")

    # Pedimos salida JSON explícita (sin schema) para compatibilidad
    lines.append(
        "\nInstrucciones estrictas:\n"
        "- El 'motivo' debe referirse a las señales y preferencias (ánimo, ritmo, extensión/páginas, presupuesto, público, formato).\n"
        "- Menciona de forma natural 1–2 rasgos del género/tono sin spoilers.\n"
        "- 'sinopsis_1linea' es un logline prudente: una sola oración basada en género/tono/temas sin inventar nombres propios ni tramas específicas.\n"
        "- No menciones 'según el motor' ni hagas listados; escribe copy natural.\n"
        "- Devuelve SOLO un JSON con esta forma exacta:\n"
        "  {\"items\": [{\"motivo\": \"...\", \"sinopsis_1linea\": \"...\"}, ...]}\n"
        f"- El array 'items' debe tener exactamente {len(libros)} elementos, en el mismo orden."
    )
    return "\n".join(lines)

@retry(
    reraise=True,
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=0.8, min=1, max=8),
    retry=retry_if_exception_type(Exception),
)
def redactar_motivos(preferencias: Dict, explicaciones_motor: List[str], libros: List[Dict]):
    client = _get_client()
    prompt = _build_prompt(preferencias, explicaciones_motor, libros)

    # Compat: Chat Completions con respuesta JSON
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},  # fuerza JSON
        temperature=0.7,
    )

    content = resp.choices[0].message.content
    try:
        data = json.loads(content)
    except Exception:
        # si el modelo no devolvió JSON perfecto, intentamos arreglar
        # última defensa: paquete mínimo válido
        data = {"items": []}

    items = data.get("items", [])
    # Alinear con la cantidad de libros
    if len(items) != len(libros):
        while len(items) < len(libros):
            items.append({
                "motivo": "Recomendación basada en tus preferencias.",
                "sinopsis_1linea": "Historia acorde al género indicado."
            })
        items = items[: len(libros)]

    # saneo básico de tipos
    for it in items:
        if not isinstance(it.get("motivo"), str):
            it["motivo"] = "Recomendación basada en tus preferencias."
        if not isinstance(it.get("sinopsis_1linea"), str):
            it["sinopsis_1linea"] = "Historia acorde al género indicado."

    return items
