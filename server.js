const express = require('express');
const { GoogleGenerativeAI } = require("@google/generative-ai");

const app = express();
app.use(express.json());

// Configuration du port pour Railway
const PORT = process.env.PORT || 8080;

app.post('/translate', async (req, res) => {
    try {
        const { prompt, password } = req.body;

        // Vérification de sécurité
        if (password !== process.env.HUD_PASSWORD) {
            return res.status(403).json({ error: "Password Error" });
        }

        // Initialisation de l'IA à l'intérieur de la requête pour éviter les crashs au démarrage
        const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);
        const model = genAI.getGenerativeModel({ model: "gemini-1.5-flash" });

        const result = await model.generateContent(prompt);
        const response = await result.response;
        
        res.json({ text: response.text() });

    } catch (e) {
        console.error("Détail de l'erreur:", e.message);
        res.status(500).json({ text: "Erreur IA: " + e.message });
    }
});

app.listen(PORT, '0.0.0.0', () => {
    console.log("Serveur actif sur le port " + PORT);
});
