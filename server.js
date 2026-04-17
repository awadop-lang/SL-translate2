const express = require('express');
const { GoogleGenerativeAI } = require("@google/generative-ai");

const app = express();
app.use(express.json());

// On vérifie que la clé est présente au démarrage
const apiKey = process.env.GEMINI_API_KEY;
if (!apiKey) {
    console.error("ERREUR : GEMINI_API_KEY manquante dans les variables Railway !");
}

const genAI = new GoogleGenerativeAI(apiKey);

app.post('/translate', async (req, res) => {
    try {
        const { prompt, password } = req.body;

        // Vérification du mot de passe
        if (password !== process.env.HUD_PASSWORD) {
            console.log("Tentative échouée : Mauvais mot de passe");
            return res.status(403).json({ error: "Accès refusé" });
        }

        const model = genAI.getGenerativeModel({ model: "gemini-1.5-flash" });
        
        // Requête simplifiée pour éviter les erreurs 500
        const result = await model.generateContent(prompt);
        const response = await result.response;
        const text = response.text();

        res.json({ text: text });
    } catch (error) {
        console.error("Erreur Gemini:", error);
        res.status(500).json({ error: "L'IA n'a pas pu répondre." });
    }
});

// Railway utilise le port 8080 par défaut, on s'adapte
const PORT = process.env.PORT || 8080;
app.listen(PORT, '0.0.0.0', () => {
    console.log(`Serveur prêt sur port ${PORT}`);
});
