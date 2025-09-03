from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, conint
from dotenv import load_dotenv
load_dotenv()
from services.motor import MotorRecomendador, map_extension_range
from services.redactor import redactar_motivos
from typing import List, Literal, Optional, Dict, Any
import json
import os
from services.motor import MotorRecomendador, map_extension_range



# IA redactor (solo para el texto de justificación)
try:
    from services.redactor import redactar_motivos
except Exception:
    # Fallback suave si no está instalado el SDK todavía
    def redactar_motivos(preferencias, explicaciones, libros):
        # Devuelve motivos simples para no romper la UX
        outs = []
        for i, l in enumerate(libros):
            parts = []
            if preferencias.get("animo"):
                parts.append(f"alineado con tu ánimo '{preferencias['animo']}'")
            if preferencias.get("ritmo"):
                parts.append(f"ritmo {preferencias['ritmo'].lower()}")
            if preferencias.get("extension"):
                lo, hi = map_extension_range(preferencias["extension"]) or (None, None)
                if lo or hi:
                    parts.append("extensión acorde")
            outs.append("Recomendación " + ", ".join(parts) + ".")
        return outs

# ======= Modelos de entrada/salida =======

Animo = Literal[
    "Desconectar", "Emoción", "Romántico", "Reflexivo", "Aprender", "Inspirarme", "Sorpréndeme"
]
Tipo = Literal["Ficción", "No ficción", "Me da igual"]
Ritmo = Literal["Tranquilo", "Medio", "Vertiginoso"]
Extension = Literal["Corto", "Medio", "Largo"]
Formato = Literal["Tapa blanda", "Tapa dura", "Cualquiera"]
Publico = Literal["Infantil", "Juvenil", "Adulto"]

class Payload(BaseModel):
    animo: Animo
    tipo: Tipo
    genero_tema: str = Field(..., description="Género (Ficción) o tema (No ficción) o 'No sé'")
    ritmo: Ritmo
    extension: Extension
    formato: Formato
    precio_max: conint(ge=0)  # CLP
    publico: Publico
    evitar: List[str] = Field(default_factory=list)

class Recomendacion(BaseModel):
    nombre: str
    motivo: str
    sinopsis_1linea: Optional[str] = None # <— NUEVO
    precio_clp: int
    tipo: Literal["Ficción", "No ficción"]
    genero: str
    formato: str
    publico: Publico
    match_score: float

class Respuesta(BaseModel):
    recomendaciones: List[Recomendacion]

# ======= App =======

app = FastAPI(title="Recomendador Librería — Demo (Reglas + IA para motivo)")

# CORS para Live Server (front local)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500", "http://localhost:5500"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Carga de catálogo
CATALOGO_PATH = os.getenv("LIBROS_JSON", os.path.join(os.path.dirname(__file__), "data", "libros.json"))
try:
    with open(CATALOGO_PATH, "r", encoding="utf-8") as f:
        CATALOGO = json.load(f)
except Exception as e:
    CATALOGO = []
    print("[WARN] No se pudo cargar el catálogo:", e)

motor = MotorRecomendador(CATALOGO)


@app.get("/health")
async def health():
    return {"ok": True, "items": len(CATALOGO)}


@app.post("/recomendar/", response_model=Respuesta)
async def recomendar(payload: Payload):
    if not CATALOGO:
        raise HTTPException(status_code=500, detail="Catálogo no disponible")

    # 1) Reglas deterministas: filtros + scoring
    tops = motor.recomendar(payload.dict())  # lista de 1–3 dicts con _explicacion_motor
    if not tops:
        return {"recomendaciones": []}

    # 2) IA SOLO para redactar motivo + sinopsis_1linea
    preferencias = payload.dict()
    explicaciones = [t.get("_explicacion_motor", "") for t in tops]

    libros_para_llm = []
    for t in tops:
        libros_para_llm.append({
            "titulo": t["titulo"],
            "autor": t["autor"],
            "tipo": t["tipo"],
            "genero": t["genero"],
            "ritmo": t["ritmo"],
            "paginas": t.get("paginas"),
            "tono": t.get("tono"),
            "publico": t.get("publico"),
            "formato": t.get("formato", []) if isinstance(t.get("formato"), list) else [],
            "precio_clp": t.get("precio_clp", 0),
            # opcional: "descripcion": t.get("descripcion")
        })

    try:
        motivos_items = redactar_motivos(preferencias, explicaciones, libros_para_llm)
        # motivos_items es una lista de objetos: {"motivo": str, "sinopsis_1linea": str}
    except Exception as e:
        print("[WARN] Falla en IA redactor:", e)
        motivos_items = [
            {"motivo": t.get("motivo", "Recomendación basada en tus preferencias."),
             "sinopsis_1linea": None}
            for t in tops
        ]

    # 3) Respuesta final (sin campos internos)
    res: List[Dict[str, Any]] = []
    for t, mi in zip(tops, motivos_items):
        formatos = t.get("formato", [])
        if not isinstance(formatos, list):
            formatos = []
        formato_str = "Tapa dura" if "Tapa dura" in formatos else "Tapa blanda"

        item = {
            "nombre": f"{t['titulo']} — {t['autor']}",
            "motivo": mi.get("motivo", "Recomendación basada en tus preferencias."),
            "sinopsis_1linea": mi.get("sinopsis_1linea"),
            "precio_clp": int(t.get("precio_clp", 0) or 0),
            "tipo": t["tipo"],
            "genero": t["genero"],
            "formato": formato_str,
            "publico": t["publico"],
            "match_score": round(float(t.get("match_score", 0.0)), 2),
        }
        res.append(item)

    return {"recomendaciones": res}
