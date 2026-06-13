// Script LSL pour Second Life - Menu de sélection de langue
// Intégration avec l'API de traduction

string TRANSLATOR_URL = "https://shurat07-tranlator.hf.space";
string API_LANGUAGES = "/api/languages";
string API_TRANSLATE = "/sl";

key owner;
key http_request_id;
string user_language = "english";  // Langue par défaut
string target_language = "french";  // Langue cible par défaut
integer engine = 1;  // 1 = Groq (recommandé), 0 = DeepL, 2 = NLLB

// Menu des langues les plus courantes
list MAIN_MENU = [
    "English", "French", "German", "Spanish",
    "Italian", "Portuguese", "Russian", "Chinese",
    "Japanese", "Korean", "Auto Detect", "Settings"
];

list SETTINGS_MENU = [
    "Engine: Groq", "Target Language", "Test Translation",
    "Show All Languages", "Back"
];

default {
    state_entry() {
        owner = llGetOwner();
        llListen(0, "", owner, "");
    }
    
    touch_start(integer total_number) {
        llDialog(owner, "=== Traducteur Second Life ===\n\nLangue actuelle: " + llToUpper(user_language) + 
            "\nLangue cible: " + llToUpper(target_language) +
            "\nMoteur: " + (engine == 1 ? "Groq" : (engine == 0 ? "DeepL" : "NLLB")),
            MAIN_MENU, -1);
    }
    
    listen(integer channel, string name, key id, string message) {
        // Traduire le message entrant
        if (message != "") {
            translate_message(message);
        }
    }
    
    dialog_response(key id, integer channel, integer button_index, string button) {
        if (id != owner) return;
        
        if (button == "Auto Detect") {
            target_language = "auto";
            llOwnerSay("Langue cible définie sur: Détection automatique");
            llDialog(owner, "Langue cible: AUTO", MAIN_MENU, -1);
        }
        else if (button == "Settings") {
            update_settings_menu();
            llDialog(owner, "=== Paramètres ===", SETTINGS_MENU, -1);
        }
        else if (button == "Engine: Groq") {
            engine = 1;
            update_settings_menu();
            llDialog(owner, "Moteur changé: Groq", SETTINGS_MENU, -1);
        }
        else if (button == "Target Language") {
            llDialog(owner, "Choisissez la langue cible:", MAIN_MENU, -1);
        }
        else if (button == "Show All Languages") {
            get_all_languages();
        }
        else if (button == "Test Translation") {
            translate_message("Hello, this is a test message.");
        }
        else if (button == "Back") {
            llDialog(owner, "=== Traducteur Second Life ===", MAIN_MENU, -1);
        }
        else {
            // Sélection de langue
            string lang = llToLower(button);
            user_language = lang;
            llOwnerSay("Votre langue: " + button);
            llDialog(owner, "Langue définie: " + button, MAIN_MENU, -1);
        }
    }
    
    update_settings_menu() {
        SETTINGS_MENU = [
            "Engine: " + (engine == 1 ? "Groq" : (engine == 0 ? "DeepL" : "NLLB")),
            "Target Language: " + llToUpper(target_language),
            "Test Translation",
            "Show All Languages",
            "Back"
        ];
    }
    
    translate_message(string text) {
        llOwnerSay("Traduction de: " + text);
        
        http_request_id = llHTTPRequest(
            TRANSLATOR_URL + API_TRANSLATE,
            [
                HTTP_METHOD, "POST",
                HTTP_MIMETYPE, "application/x-www-form-urlencoded",
                HTTP_BODY, "text=" + llEscapeURL(text) + 
                          "&mylang=" + user_language + 
                          "&hislang=" + target_language + 
                          "&is_owner=1" +
                          "&engine=" + (string)engine,
                HTTP_HEADERS, [
                    "X-SecondLife-Owner-Key", (string)llGetOwner(),
                    "X-SecondLife-Key", llGenerateKey(),
                    "X-MyLang", user_language,
                    "X-HisLang", target_language,
                    "X-IsOwner", "1",
                    "X-Engine", (string)engine
                ]
            ],
            ""
        );
    }
    
    get_all_languages() {
        llOwnerSay("Récupération de la liste complète des langues...");
        
        http_request_id = llHTTPRequest(
            TRANSLATOR_URL + API_LANGUAGES,
            [HTTP_METHOD, "GET"],
            ""
        );
    }
    
    http_response(key request_id, integer status, list metadata, string body) {
        if (request_id == http_request_id) {
            if (status == 200) {
                if (llSubStringIndex(body, "languages") != -1) {
                    // Réponse de l'API des langues
                    string lang_list = llJsonGetValue(body, ["languages"]);
                    llOwnerSay("Langues disponibles: " + lang_list);
                    
                    // Afficher le nombre de langues
                    integer count = (integer)llJsonGetValue(body, ["count"]);
                    llOwnerSay("Total: " + (string)count + " langues supportées");
                }
                else {
                    // Réponse de traduction
                    if (body == "NO_TRAD_NEEDED") {
                        llOwnerSay("Pas de traduction nécessaire (texte déjà dans la langue cible)");
                    }
                    else if (llSubStringIndex(body, "[Erreur") == 0) {
                        llOwnerSay("Erreur de traduction: " + body);
                    }
                    else {
                        llOwnerSay("Traduction: " + body);
                    }
                }
            }
            else {
                llOwnerSay("Erreur HTTP: " + (string)status);
            }
        }
    }
}