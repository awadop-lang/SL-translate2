import os
import httpx
import urllib.parse
import json
from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

from nllb_translate import translate_nllb

app = FastAPI()

# ── Fichier de persistance mémoire ──
MEMORY_FILE = "memory.json"

def load_memory():
    """Charge la mémoire depuis le fichier JSON."""
    try:
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"[MEMORY] Erreur chargement: {e}")
    return {}

def save_memory():
    """Sauvegarde la mémoire dans le fichier JSON."""
    try:
        with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(MEMORY, f, indent=2, ensure_ascii=False)
        print(f"[MEMORY] Sauvegardé ({len(MEMORY)} UUIDs)")
    except Exception as e:
        print(f"[MEMORY] Erreur sauvegarde: {e}")

# Charger la mémoire au démarrage
MEMORY = load_memory()
MAX_MEMORY = 5

# ── Clés API ──
GROQ_KEY  = os.environ.get("GROQ_API_KEY")
DEEPL_KEY = os.environ.get("DEEPL_API_KEY")

# ── UUID autorisés ──
ALLOWED_USERS = [
    "d829374a-247a-4aab-abc6-8f4ee14b4fd2",
    "1981874c-b144-42ea-b94f-2a819cd91a82",
    "4b8ad3ce-ddf3-4ac9-949e-11fe91905b57"
]
# ── Mapping des langues supportées ──
SUPPORTED_LANGUAGES = {
    "arabic": "AR", "bulgarian": "BG", "chinese": "ZH",
    "czech": "CS", "danish": "DA", "dutch": "NL",
    "english": "EN", "estonian": "ET", "finnish": "FI",
    "french": "FR", "german": "DE", "greek": "EL",
    "hungarian": "HU", "indonesian": "ID", "italian": "IT",
    "japanese": "JA", "korean": "KO", "latvian": "LV",
    "lithuanian": "LT", "norwegian": "NB", "polish": "PL",
    "portuguese": "PT", "romanian": "RO", "russian": "RU",
    "slovak": "SK", "slovenian": "SL", "spanish": "ES",
    "swedish": "SV", "turkish": "TR", "ukrainian": "UK",
    # Langues supplémentaires pour Groq
    "hindi": "HI", "thai": "TH", "vietnamese": "VI",
    "hebrew": "HE", "arabic": "AR", "persian": "FA",
    "auto": "AUTO"  # Détection automatique
}

# Cartographie pour DeepL (codes spécifiques)
DEEPL_LANG_MAP = SUPPORTED_LANGUAGES.copy()

# ── Phrases de refus à détecter ──
REFUS_TRIGGERS = [
    "ich kann", "i cannot", "i'm unable", "i am unable",
    "je ne peux pas", "this request", "inappropriate",
    "i'm sorry", "i apologize", "stehe ich", "i can't",
    "lo siento", "non posso", "je suis désolé",
    "als ki", "as an ai", "as a language model",
    "unable to fulfill", "cannot fulfill", "cannot assist",
    "wenn sie einen", "si vous avez", "if you have another"
]


# ──────────────────────────────────────────────
# CONSTRUCTION DU PROMPT DE TRADUCTION
# ──────────────────────────────────────────────
def build_translation_prompt(source, target, history=None):
    if source and source.lower() != target.lower():
        direction = f"from {source} to {target}"
    else:
        direction = f"to {target} (detect source)"

    context = ""
    if history:
        context = "\nContext: " + " | ".join(history[-2:]) + "\n"

    prompt = (
        f"Translate {direction}. Rules:\n"
        f"1. Output ONLY translation, no quotes/prefixes\n"
        f"2. Keep emotes in *asterisks*\n"
        f"3. Keep proper nouns, translate common words\n"
        f"4. Preserve tone/slang naturally\n"
        f"5. If already in {target}: return unchanged\n"
        f"6. Single line, no line breaks\n"
        f"{context}Text: "
    )
    return prompt


# ──────────────────────────────────────────────
# APPEL GROQ GÉNÉRIQUE
# ──────────────────────────────────────────────
async def call_groq(model, system_msg, text, timeout=10.0):
    if not GROQ_KEY:
        print("[Groq] ⚠️ GROQ_API_KEY non définie")
        return None
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {GROQ_KEY}"},
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system_msg},
                        {"role": "user",   "content": text}
                    ],
                    "temperature": 0.0,
                    "max_tokens": 256
                },
                timeout=timeout
            )
            data = response.json()

            if "choices" not in data:
                print(f"[Groq {model}] Réponse inattendue: {data}")
                return None

            res = data["choices"][0]["message"]["content"].strip()

            if res.startswith('"') and res.endswith('"'):
                res = res[1:-1].strip()

            if any(t in res.lower() for t in REFUS_TRIGGERS):
                print(f"[Groq {model}] REFUS détecté → None")
                return None

            return res

    except Exception as e:
        print(f"[Groq {model}] Erreur: {e}")
        return None


# ──────────────────────────────────────────────
# MOTEURS DE TRADUCTION
# ──────────────────────────────────────────────
async def translate_groq_primary(text, source, target, history=None):
    if not GROQ_KEY:
        print("[Groq] ⚠️ Clé API manquante, utilisation du fallback")
        return text
    
    system_msg = build_translation_prompt(source, target, history)
    print(f"[Groq 8B] {source} → {target} | '{text[:60]}'")
    res = await call_groq("llama-3.1-8b-instant", system_msg, text, timeout=12.0)
    if res:
        print(f"[Groq 8B] ✅ '{res[:60]}'")
    return res

async def translate_groq_fallback(text, source, target):
    if not GROQ_KEY:
        print("[Groq] ⚠️ Clé API manquante, retour du texte original")
        return text
    
    system_msg = build_translation_prompt(source, target)
    print(f"[Groq retry] {source} → {target} | '{text[:60]}'")
    res = await call_groq("llama-3.1-8b-instant", system_msg, text, timeout=10.0)
    if res:
        print(f"[Groq retry] ✅ '{res[:60]}'")
    else:
        print(f"[Groq retry] Échec → texte original retourné.")
        res = text
    return res

async def translate_deepl(text, source_lang, target_lang):
    if not DEEPL_KEY:
        print("[DeepL] ⚠️ Clé API manquante !")
        return "[Erreur: clé DeepL manquante]"

    target_code = DEEPL_LANG_MAP.get(target_lang.lower())
    source_code = DEEPL_LANG_MAP.get(source_lang.lower()) if source_lang else None

    print(f"[DeepL DEBUG] source='{source_lang}' ({source_code}) → target='{target_lang}' ({target_code})")

    if not target_code:
        print(f"[DeepL] ⚠️ Langue cible inconnue : '{target_lang}'")
        return "[Erreur: langue cible inconnue]"

    try:
        async with httpx.AsyncClient() as client:
            payload = {
                "text":        [text],
                "target_lang": target_code
            }
            if source_code and source_code != target_code:
                payload["source_lang"] = source_code

            response = await client.post(
                "https://api-free.deepl.com/v2/translate",
                headers={
                    "Authorization": f"DeepL-Auth-Key {DEEPL_KEY}",
                    "Content-Type":  "application/json"
                },
                json=payload,
                timeout=10.0
            )

            data = response.json()
            if "translations" not in data:
                return f"[Erreur DeepL: {data.get('message', response.text[:100])}]"

            result   = data["translations"][0]["text"]
            detected = data["translations"][0].get("detected_source_language", "").upper()

            if detected and detected == target_code.upper() and not source_code:
                return "NO_TRAD_NEEDED"

            return result
    except Exception as e:
        print(f"[DeepL] Erreur: {e}")
        return f"[Erreur DeepL: {e}]"


# ──────────────────────────────────────────────
# ENDPOINT PRINCIPAL /sl (CORRIGÉ & ROBUSTE)
# ──────────────────────────────────────────────
@app.post("/sl")
async def sl(request: Request):
    
    # Extraction des données du formulaire POST (Méthode moderne & sécurisée)
    form_data = await request.form()
    
    # Récupération de l'ID propriétaire (priorité au Body, sinon fallback sur les Headers)
    owner_id = form_data.get("owner_key", request.headers.get("X-SecondLife-Owner-Key", "Unknown"))
    
    # Vérification de sécurité
    if owner_id not in ALLOWED_USERS:
        return Response(content="Accès refusé.")

    try:
        # Lecture intelligente : Si présent dans le Body, on prend, sinon on check les Headers
        text = form_data.get("text", "")
        if not text: # Rétrocompatibilité HUD avec X-Text si besoin
            text = urllib.parse.unquote(request.headers.get("X-Text", ""))
            
        my_lang   = form_data.get("mylang", request.headers.get("X-MyLang", "French"))
        his_lang  = form_data.get("hislang", request.headers.get("X-HisLang", "English"))
        
        # Gestion des booléens et chaînes provenant de SL
        is_owner_raw = form_data.get("is_owner", request.headers.get("X-IsOwner", "1"))
        is_owner = is_owner_raw == "1" or is_owner_raw == "True"
        
        engine = form_data.get("engine", request.headers.get("X-Engine", "1"))
        uuid   = form_data.get("sl_key", request.headers.get("X-SecondLife-Key", ""))

        print(f"[ENDPOINT] engine='{engine}' is_owner={is_owner} my_lang='{my_lang}' his_lang='{his_lang}' text='{text[:60]}'")

        if not text:
            return Response(content="")

        # ── Calcul source / cible selon qui parle ──
        if is_owner:
            source = my_lang
            target = his_lang if his_lang != "Auto" else "English"
        else:
            source = his_lang if his_lang != "Auto" else None
            target = my_lang

        print(f"[ENDPOINT] source='{source}' → target='{target}'")

        # ── Mémoire ──
        history = MEMORY.get(uuid, []) if uuid else []

        # ── Aiguillage moteur ──
        if engine == "0":
            res = await translate_deepl(text, source, target)
        elif engine == "2":
            print(f"[ENDPOINT] NLLB translate: {source} → {target}")
            res = await translate_nllb(text, source, target)
        else:
            res = await translate_groq_primary(text, source, target, history)
            if res is None:
                res = await translate_groq_fallback(text, source, target)

        print(f"[ENDPOINT] résultat brut → '{str(res)[:80]}'")

        if not res:
            print("[ENDPOINT] ⚠️ Résultat vide.")
            return Response(content="")

        # ── NO_TRAD_NEEDED ──
        if res.strip() == "NO_TRAD_NEEDED":
            return Response(content="NO_TRAD_NEEDED")
        if res.lower().strip() == text.lower().strip():
            return Response(content="NO_TRAD_NEEDED")

        # ── Nettoyage parenthèses en fin de chaîne ──
        if "(" in res:
            idx = res.rfind("(")
            if idx >= len(res) - 20:
                res = res[:idx].strip()

        # ── Mise à jour mémoire (Groq uniquement) ──
        if uuid and engine == "1" and not res.startswith("[Erreur"):
            if uuid not in MEMORY:
                MEMORY[uuid] = []
            MEMORY[uuid].append(f"[{source}→{target}] {text[:60]} → {res[:60]}")
            if len(MEMORY[uuid]) > MAX_MEMORY:
                MEMORY[uuid] = MEMORY[uuid][-MAX_MEMORY:]
            save_memory()

        print(f"[ENDPOINT] ✅ Envoyé au HUD : '{res[:80]}'")
        return Response(content=res)

    except Exception as e:
        print(f"[ENDPOINT] Erreur: {e}")
        return Response(content="Erreur serveur")


# ──────────────────────────────────────────────
# ENDPOINT SANTÉ & SERVICES STATIQUES
# ──────────────────────────────────────────────
@app.get("/")
async def index():
    index_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    if os.path.exists(index_path):
        with open(index_path, encoding="utf-8") as f:
            return HTMLResponse(content=f.read(), status_code=200)
    return {
        "status": "✅ Serveur traducteur SL actif",
        "api_keys": {"groq": bool(GROQ_KEY), "deepl": bool(DEEPL_KEY)},
        "endpoints": {
            "languages": "/api/languages",
            "status": "/api/status",
            "memory": "/api/memory",
            "translate": "/sl (POST)"
        }
    }

@app.get("/api/memory")
async def get_memory():
    return MEMORY

@app.delete("/api/memory/{uuid}")
async def delete_memory(uuid: str):
    if uuid in MEMORY:
        del MEMORY[uuid]
        save_memory()
        return {"status": "deleted", "uuid": uuid}
    return {"status": "not_found", "uuid": uuid}

@app.delete("/api/memory")
async def clear_all_memory():
    MEMORY.clear()
    save_memory()
    return {"status": "cleared"}

@app.get("/api/status")
async def get_status():
    return {
        "status": "running",
        "groq_configured": bool(GROQ_KEY),
        "deepl_configured": bool(DEEPL_KEY),
        "memory_entries": len(MEMORY)
    }

@app.get("/api/languages")
async def get_languages():
    """Retourne la liste des langues supportées par le traducteur"""
    return {
        "languages": list(SUPPORTED_LANGUAGES.keys()),
        "count": len(SUPPORTED_LANGUAGES),
        "mapping": SUPPORTED_LANGUAGES
    }

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/admin")
async def admin_interface():
    try:
        with open("static/index.html", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Interface non trouvée</h1><p>Le fichier static/index.html n'existe pas.</p>", status_code=404)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)