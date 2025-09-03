import json, uuid, os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USUARIOS_FILE = os.path.join("data", "usuarios.json")

def _load_users():
    if not os.path.exists(USUARIOS_FILE):
        return []
    with open(USUARIOS_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def _save_users(data):
    with open(USUARIOS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def registrar(nombre: str, telefono: str):
    usuarios = _load_users()

    # normalizamos el teléfono
    telefono = telefono.strip()

    # no permitir duplicados
    if any(u["telefono"] == telefono for u in usuarios):
        return None

    user = {
        "id": str(uuid.uuid4()),
        "nombre": nombre.strip(),
        "telefono": telefono,
        "token": None
    }
    usuarios.append(user)
    _save_users(usuarios)
    return user

def login(telefono: str):
    usuarios = _load_users()
    telefono = telefono.strip()
    user = next((u for u in usuarios if u["telefono"] == telefono), None)
    if not user:
        return None
    token = str(uuid.uuid4())
    user["token"] = token
    _save_users(usuarios)
    return {"id": user["id"], "nombre": user["nombre"], "token": token}

def validar_token(token: str):
    usuarios = _load_users()
    return next((u for u in usuarios if u.get("token") == token), None)
