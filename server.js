const express = require('express');
const { GoogleGenerativeAI } = require("@google/generative-ai");

const app = express();
app.use(express.json());

app.post('/translate', async (req, res) => {
    try {
        const { prompt, password } = req.body;

        // 1. Test du mot de passe
        if (password !== process.env.HUD_PASSWORD) {
            return res.status(403).json({ text: "Erreur: Mot de passe Railway incorrect." });
        }

        // 2. Test de la présence de la clé
        const key = process.env.GEMINI_API_KEY;
        if (!key) {
            return res.status(500).json({ text: "Erreur: La variable GEMINI_API_KEY est vide sur Railway." });
        }

        const genAI = new GoogleGenerativeAI(key);
        const model = genAI.getGenerativeModel({ model: "gemini-1.5-flash" });

        // 3. Tentative d'appel à Google
        const result = await model.generateContent(prompt);
        const response = await result.response;
        const out = response.text();

        res.json({ text: out });

    } catch (err) {
        // Renvoie l'erreur précise de Google au HUD
        console.error(err);
        res.status(500).json({ text: "DEBUG GOOGLE: " + err.message });
    }
});

const PORT = process.env.PORT || 8080;
app.listen(PORT, '0.0.0.0', () => {
    console.log("Serveur de diagnostic prêt sur port " + PORT);
});
