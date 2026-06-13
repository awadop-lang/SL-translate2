# API des Langues Supportées

## Endpoint: `/api/languages`

Retourne la liste complète des langues supportées par le traducteur.

### Exemple de requête:
```bash
curl https://shurat07-tranlator.hf.space/api/languages
```

### Réponse:
```json
{
  "languages": [
    "arabic",
    "bulgarian",
    "chinese",
    "czech",
    "danish",
    "dutch",
    "english",
    "estonian",
    "finnish",
    "french",
    "german",
    "greek",
    "hungarian",
    "indonesian",
    "italian",
    "japanese",
    "korean",
    "latvian",
    "lithuanian",
    "norwegian",
    "polish",
    "portuguese",
    "romanian",
    "russian",
    "slovak",
    "slovenian",
    "spanish",
    "swedish",
    "turkish",
    "ukrainian",
    "hindi",
    "thai",
    "vietnamese",
    "hebrew",
    "persian",
    "auto"
  ],
  "count": 35,
  "mapping": {
    "arabic": "AR",
    "bulgarian": "BG",
    ...
  }
}
```

## Utilisation dans Second Life

### Script LSL pour récupérer les langues:
```lsl
key HTTP_REQUEST_ID;
string API_URL = "https://shurat07-tranlator.hf.space/api/languages";

default {
    touch_start(integer total_number) {
        llSay(0, "Récupération des langues supportées...");
        
        HTTP_REQUEST_ID = llHTTPRequest(
            API_URL,
            [HTTP_METHOD, "GET"],
            ""
        );
    }
    
    http_response(key request_id, integer status, list metadata, string body) {
        if (request_id == HTTP_REQUEST_ID && status == 200) {
            llSay(0, "Langues disponibles: " + body);
            
            // Parser JSON pour extraire la liste des langues
            list languages = llJson2List(body);
            string lang_list = llJsonGetValue(body, ["languages"]);
            llSay(0, "Liste: " + lang_list);
        }
    }
}
```

### Menu de sélection de langue:
```lsl
list MENU_LANGUAGES = [
    "English", "French", "German", "Spanish",
    "Italian", "Portuguese", "Russian", "Chinese",
    "Japanese", "Korean", "Auto"
];

default {
    touch_start(integer total_number) {
        llDialog(llGetOwner(), "Choisissez votre langue:", MENU_LANGUAGES, -1);
    }
    
    touch_end(integer total_number) {
        // Stocker la langue choisie
        // Utiliser cette langue dans les requêtes de traduction
    }
}
```

## Utilisation dans l'endpoint `/sl`

### Format:
```
POST /sl
Headers:
  X-MyLang: french
  X-HisLang: english
  X-Engine: 1
Body:
  text: Bonjour le monde
  mylang: french
  hislang: english
  is_owner: 1
  engine: 1
```

### Codes de langue acceptés:
- Noms en anglais: `french`, `english`, `german`, etc.
- Option `auto` pour détection automatique
- Insensible à la casse: `French` == `french`

## Langues supportées par moteur:

### Groq (Engine 1 - recommandé):
- Toutes les langues listées (35 langues)
- Meilleure qualité de traduction
- Supporte les langues moins courantes

### DeepL (Engine 0):
- Langues européennes principales
- Qualité très élevée pour les langues supportées
- Requiert une clé API DeepL

### NLLB (Engine 2 - désactivé):
- Traduction locale (non disponible actuellement pour économiser les ressources)