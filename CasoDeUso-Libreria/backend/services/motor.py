from __future__ import annotations
from typing import List, Dict, Tuple, Optional

# ====== Config de afinamiento por Ánimo ======
ANIMO_A_GENEROS: Dict[str, List[str]] = {
    "Emoción": ["Thriller", "Suspenso", "Policial", "Aventura"],
    "Desconectar": ["Cozy mystery", "Humor", "Fantasía ligera", "Rom-com"],
    "Romántico": ["Romance", "Rom-com"],
    "Reflexivo": ["Realismo contemporáneo", "Literaria", "Memorias", "Filosofía"],
    "Aprender": ["Historia", "Ciencia", "Psicología", "Negocios", "Divulgación científica"],
    "Inspirarme": ["Autoayuda", "Biografías", "Emprendimiento"],
    "Sorpréndeme": [],
}

# Géneros penalizados (disonancia) por cada ánimo
ANIMO_A_EVITAR = {
    "Romántico": {"Horror", "Thriller", "Gore", "Terror"},
    "Reflexivo": {"Horror", "Gore"},
}

# Rangos de páginas por extensión
PAGINAS_RANGO: Dict[str, Tuple[int, int]] = {
    "Corto": (0, 200),
    "Medio": (200, 400),
    "Largo": (400, 10_000),
}


def map_extension_range(ext: str) -> Optional[Tuple[int, int]]:
    return PAGINAS_RANGO.get(ext)


class MotorRecomendador:
    def __init__(self, catalogo: List[Dict]):
        self.catalogo = catalogo or []

    # =============== Utilidades ===============
    @staticmethod
    def _publico_match(user_publico: str, book_publico: str) -> bool:
        if user_publico in ("Infantil", "Juvenil"):
            return user_publico == book_publico
        return book_publico == "Adulto"

    # =============== Filtros duros ===============
    def _filtrar(self, p: Dict) -> List[Dict]:
        out = []
        formato_user = p.get("formato")
        precio_max = p.get("precio_max")
        tipo_user = p.get("tipo")
        publico_user = p.get("publico")
        evitar_flags = set(map(str.lower, p.get("evitar", [])))

        for b in self.catalogo:
            # tipo
            if tipo_user != "Me da igual" and b.get("tipo") != tipo_user:
                continue
            # formato
            if formato_user != "Cualquiera":
                if formato_user not in set(b.get("formato", [])):
                    continue
            # flags de contenido
            flags = set(map(str.lower, b.get("content_flags", [])))
            if evitar_flags & flags:
                continue
            # público
            if not self._publico_match(publico_user, b.get("publico")):
                continue
            # precio con tolerancia (descartamos solo si supera +10%)
            if isinstance(precio_max, (int, float)) and isinstance(b.get("precio_clp"), (int, float)):
                if b["precio_clp"] > precio_max * 1.1:
                    continue

            out.append(b)
        return out

    # =============== Scoring determinista ===============
    def _score(self, b: Dict, p: Dict) -> Tuple[float, str, Dict[str, bool]]:
        """Devuelve (score_total 0–100, explicacion_str, flags_dict)."""
        S_tipo_genero = 0.0   # /35
        S_animo = 0.0         # /25
        S_ritmo_ext = 0.0     # /20
        S_form_precio = 0.0   # /15
        S_publico_social = 0.0  # /5

        flags = {
            "genero_match": False,
            "animo_bucket": False,
            "ritmo_match": False,
            "rango_paginas": False,
            "dentro_presupuesto": False,
            "por_tolerancia": False,
            "publico_match": False,
            "bestseller": bool(b.get("bestseller")),
            "premios": bool(b.get("premios")),
        }

        genero_user = p.get("genero_tema")
        animo = p.get("animo")
        ritmo_user = p.get("ritmo")
        ext_user = p.get("extension")
        formato_user = p.get("formato")
        precio_max = p.get("precio_max") or 0

        # Tipo+género/tema (35)
        if genero_user and str(genero_user).lower() not in {"no sé", "nose", "no se"}:
            if b.get("genero") == genero_user:
                S_tipo_genero = 35.0
                flags["genero_match"] = True
            else:
                if p.get("tipo") == b.get("tipo") or p.get("tipo") == "Me da igual":
                    S_tipo_genero = 18.0
        else:
            bucket = ANIMO_A_GENEROS.get(animo, [])
            if b.get("genero") in bucket:
                S_tipo_genero = 28.0
                flags["animo_bucket"] = True
            elif p.get("tipo") == b.get("tipo") or p.get("tipo") == "Me da igual":
                S_tipo_genero = 16.0

        # Ánimo (25) + ajuste por tono
        bucket = ANIMO_A_GENEROS.get(animo, [])
        if b.get("genero") in bucket:
            S_animo += 20.0
            flags["animo_bucket"] = True
        tono = (b.get("tono") or "").lower()
        if animo == "Emoción" and tono in {"oscuro", "agridulce"}:
            S_animo += 3
        if animo == "Desconectar" and tono in {"luminoso", "esperanzador"}:
            S_animo += 4
        if animo == "Reflexivo" and tono in {"reflexivo", "agridulce"}:
            S_animo += 4
        S_animo = min(S_animo, 25.0)

        # Ritmo + extensión (20)
        if b.get("ritmo") == ritmo_user:
            S_ritmo_ext += 12.0
            flags["ritmo_match"] = True
        rng = map_extension_range(ext_user)
        if rng and isinstance(b.get("paginas"), int):
            lo, hi = rng
            if lo <= b["paginas"] <= hi:
                S_ritmo_ext += 8.0
                flags["rango_paginas"] = True
        S_ritmo_ext = min(S_ritmo_ext, 20.0)

        # Formato + precio (15)
        if formato_user == "Cualquiera" or (formato_user in set(b.get("formato", []))):
            S_form_precio += 5.0
        precio = b.get("precio_clp") or 0
        if precio <= precio_max:
            S_form_precio += 10.0
            flags["dentro_presupuesto"] = True
        elif precio <= precio_max * 1.1:
            S_form_precio += 6.0
            flags["por_tolerancia"] = True

        # Público + señales sociales (5)
        if b.get("publico") == p.get("publico") or (p.get("publico") == "Adulto" and b.get("publico") == "Adulto"):
            S_publico_social += 3.0
            flags["publico_match"] = True
        if b.get("bestseller"):
            S_publico_social += 1.0
        if b.get("premios"):
            S_publico_social += 1.0
        S_publico_social = min(S_publico_social, 5.0)

        # ===== Afinamiento por disonancia de Ánimo =====
        penalty = 0.0
        evitar = ANIMO_A_EVITAR.get(animo, set())
        if b.get("genero") in evitar:
            penalty += 10.0  # evita que Horror/Thriller dominen cuando el ánimo es Romántico

        # Si género no pertenece al bucket del ánimo, limitar el impacto de ritmo/extensión
        if ANIMO_A_GENEROS.get(animo) and b.get("genero") not in ANIMO_A_GENEROS[animo]:
            S_ritmo_ext = min(S_ritmo_ext, 6.0)

        total = S_tipo_genero + S_animo + S_ritmo_ext + S_form_precio + S_publico_social - penalty
        total = max(0.0, min(100.0, total))

        # Explicación breve (para alimentar al redactor IA)
        exp_parts = []
        if flags["genero_match"]:
            exp_parts.append("Coincidencia de género/tema")
        if flags["animo_bucket"]:
            exp_parts.append("Alineado con el ánimo declarado")
        if flags["ritmo_match"]:
            exp_parts.append(f"Ritmo {ritmo_user} coincide")
        if flags["rango_paginas"]:
            exp_parts.append(f"Extensión {ext_user} acorde")
        if flags["dentro_presupuesto"]:
            exp_parts.append("Dentro de presupuesto")
        elif flags["por_tolerancia"]:
            exp_parts.append("Precio en tolerancia +10%")
        if flags["publico_match"]:
            exp_parts.append(f"Público {p.get('publico')}")
        if b.get("bestseller"):
            exp_parts.append("Bestseller")
        if b.get("premios"):
            exp_parts.append("Premiado")
        explicacion = "; ".join(exp_parts)

        return total, explicacion, flags

    # =============== Ranqueo + Top N ===============
    def recomendar(self, payload: Dict, top_n: int = 3) -> List[Dict]:
        candidatos = self._filtrar(payload)
        if not candidatos:
            candidatos = [b for b in self.catalogo if self._publico_match(payload.get("publico"), b.get("publico"))]

        # Prefiltro por Ánimo si el usuario no sabe el género
        gen = (payload.get("genero_tema") or "").lower()
        if gen in ("no sé", "nose", "no se"):
            bucket = ANIMO_A_GENEROS.get(payload.get("animo"), [])
            if bucket:
                preferidos = [b for b in candidatos if b.get("genero") in bucket]
                if preferidos:
                    candidatos = preferidos
                else:
                    # si no hay del bucket, al menos evita géneros claramente disonantes
                    evitar = ANIMO_A_EVITAR.get(payload.get("animo"), set())
                    filtrados = [b for b in candidatos if b.get("genero") not in evitar]
                    candidatos = filtrados or candidatos

        # ⚠️ Nuevo bloque: detectar si no hay match exacto del género pedido
        genero_busq = payload.get("genero_tema")
        if genero_busq and genero_busq.lower() not in ("no sé", "nose", "no se"):
            if not any(genero_busq.lower() == (b.get("genero", "").lower()) for b in candidatos):
                for b in candidatos:
                    b["_explicacion_motor"] = b.get("_explicacion_motor", "")
                    b["_explicacion_motor"] += f" ⚠️ No hay match exacto con '{genero_busq}', mostrando cercanos."

        scored = []
        for b in candidatos:
            score, explicacion, flags = self._score(b, payload)
            scored.append((score, explicacion, flags, b))

        # Orden: score desc, luego precio asc
        scored.sort(key=lambda x: (-x[0], x[3].get("precio_clp", 10**9)))

        out: List[Dict] = []
        for score, explicacion, flags, b in scored[:top_n]:
            item = {
                "titulo": b.get("titulo"),
                "autor": b.get("autor"),
                "tipo": b.get("tipo"),
                "genero": b.get("genero"),
                "subgenero": b.get("subgenero"),
                "paginas": b.get("paginas"),
                "ritmo": b.get("ritmo"),
                "tono": b.get("tono"),
                "publico": b.get("publico"),
                "formato": b.get("formato", []),
                "precio_clp": b.get("precio_clp", 0),
                "bestseller": b.get("bestseller", False),
                "premios": b.get("premios", []),
                "content_flags": b.get("content_flags", []),
                "match_score": float(score),
                "_explicacion_motor": explicacion,
            }
            out.append(item)

        return out
